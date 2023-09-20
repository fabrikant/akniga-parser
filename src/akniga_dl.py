import argparse
import os
import subprocess
import json
import brotli
import shutil
import requests
import logging
from pathlib import Path
from pathvalidate import sanitize_filename
from selenium.webdriver.chrome.service import Service as ChromeService
from seleniumwire import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import urllib.parse
from Crypto.Cipher import AES
import m3u8  # type:ignore
import tqdm
from akniga_parser import request_heders
from akniga_global import NAMING_DEEP, NAMING_WIDE, NAMING_ID, DOWNLOAD_REQUESTS, DOWNLOAD_FFMPEG

logger = logging.getLogger(__name__)


def ffmpeg_common_command():
    ffmpeg_log_level = 'fatal'
    if logger.root.level == logging.DEBUG:
        ffmpeg_log_level = '‘debug'
    elif logger.root.level == logging.INFO:
        ffmpeg_log_level = 'info'
    elif logger.root.level == logging.WARNING:
        ffmpeg_log_level = 'warning'
    elif logger.root.level == logging.ERROR:
        ffmpeg_log_level = 'error'
    return ['ffmpeg', '-y', '-hide_banner', '-loglevel', ffmpeg_log_level]


def get_cover_filename(dir_path):
    return dir_path / 'cover.jpg'


def download_cover(book_json, tmp_folder):
    cover_url = book_json['preview']
    cover_filename = get_cover_filename(tmp_folder)
    big_picture_url = cover_url.replace("100x100crop", "400x")
    # try to download big picture
    res = requests.get(big_picture_url, stream=True, headers=request_heders())
    if res.status_code == 200:
        with open(cover_filename, 'wb') as f:
            shutil.copyfileobj(res.raw, f)
    else:
        # big picture not found, try to download preview
        res = requests.get(cover_url, stream=True, headers=request_heders())
        if res.status_code == 200:
            with open(cover_filename, 'wb') as f:
                shutil.copyfileobj(res.raw, f)
    return cover_filename


def find_mp3_url(book_soup):
    url_mp3 = None
    logger.debug('try to parse html')
    attr_name = 'src'
    for audio_tag in book_soup.findAll('audio'):
        if 'src' in audio_tag.attrs:
            url_mp3 = audio_tag.attrs[attr_name]
            logger.warning(f'find mp3 url: {url_mp3}')
            break
    return url_mp3


def get_book_requests(book_url: str) -> list:
    logger.warning("Getting book requests. Please wait...")
    service = ChromeService(executable_path=ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    with webdriver.Chrome(service=service, options=options) as driver:
        driver.get(book_url)
        book_requests = driver.requests
        html = driver.page_source
        driver.close()
        return book_requests, html


def analyse_book_requests(book_requests: list) -> tuple:
    logger.debug('Analysing book requests...')
    try:
        # find request with book json data
        book_json_requests = [r for r in book_requests if r.method == 'POST' and r.path.startswith('/ajax/b/')]
        # assert that we have only 1 request for book data found
        assert len(book_json_requests) == 1, 'Error: Book data not found. Exiting.'
        logger.warning('Book data found')
        book_json = json.loads(brotli.decompress(book_json_requests[0].response.body))
        # find request with m3u8 file
        m3u8_file_requests = [r for r in book_requests if 'm3u8' in r.url]
        m3u8url = None
        if len(m3u8_file_requests) == 1:
            logger.warning('m3u8 file found')
            m3u8url = m3u8_file_requests[0].url
        else:
            logger.warning('m3u8 file NOT found')
        return book_json, m3u8url
    except AssertionError as message:
        logger.error(message)
        exit(1)


def cut_the_chapter(chapter, input_file, output_folder):
    output_file = output_folder / sanitize_filename(f'no_meta_{chapter["title"]}.mp3')
    logger.debug(f'cut the chapter {chapter["title"]} from file {input_file} time from '
                f'start {str(chapter["time_from_start"])} time finish {str(chapter["time_finish"])}')
    command_cut = (ffmpeg_common_command() + ['-i', input_file, '-codec', 'copy',
                    '-ss', str(chapter['time_from_start']), '-to', str(chapter['time_finish']), output_file])
    subprocess.run(command_cut)
    return output_file


def create_mp3_with_metadata(chapter, no_meta_filename, book_folder, tmp_folder, book_json):
    cover_filename = get_cover_filename(tmp_folder)
    chapter_path = book_folder / sanitize_filename(f'{chapter["title"]}.mp3')
    logger.debug(f'create mp3 with metadata: {chapter_path}')
    command_metadata = ffmpeg_common_command() + ['-i', no_meta_filename]
    book_performer = ''
    if 'sTextPerformer' in book_json.keys():
        book_performer = BeautifulSoup(book_json['sTextPerformer'], 'html.parser').find('a')
        if book_performer is None:
            book_performer = ''
        else:
            book_performer = book_performer.find('span')
            if book_performer is None:
                book_performer = ''
            else:
                book_performer = book_performer.get_text()
    if Path(cover_filename).exists():
        command_metadata = command_metadata + ['-i', cover_filename, '-map', '0:0', '-map', '1:0']
    command_metadata = command_metadata + ['-codec', 'copy', '-id3v2_version', '3',
                                           '-metadata', f'title={chapter["title"]}',
                                           '-metadata', f'album={book_json["titleonly"]}',
                                           '-metadata', f'artist={book_json["author"]}',
                                           '-metadata', f'composer={book_json["author"]}',
                                           '-metadata', f'album_artist={book_performer}',
                                           '-metadata', 'comment=',
                                           '-metadata', 'encoded_by=',
                                           '-metadata', f'TOPE={book_performer}',
                                           '-metadata', 'track={0:0>3}/{1:0>3}'.
                                           format(chapter['chapter_number'], chapter['number_of_chapters']),
                                           chapter_path]
    subprocess.run(command_metadata)
    # remove no_meta file
    os.remove(no_meta_filename)


def download_book_by_mp3_url(mp3_url, book_folder, tmp_folder, book_json):
    mp3_filename = mp3_url.split('/')[-1]
    url_pattern_path = '{0}/'.format('/'.join(mp3_url.split('/')[0:-1]))
    url_pattern_filename = '.'+'.'.join(mp3_filename.split('.')[1:])
    filename = None
    count = 0
    chapter_count = 0
    chapters = json.loads(book_json['items'])
    for chapter in chapters:
        chapter_count += 1
        chapter['chapter_number'] = chapter_count
        chapter['number_of_chapters'] = len(chapters)
        # download new file
        if count != chapter['file']:
            count = chapter['file']
            # calculate filename
            str_count = '{}'.format(count)
            if count < 10:
                str_count = '{:0>2}'.format(count)
            filename = tmp_folder / (str_count + url_pattern_filename)
            url_string = url_pattern_path+urllib.parse.quote(str_count+url_pattern_filename)
            logger.debug('try to download file: '+url_string)
            res = requests.get(url_string, stream=True, headers=request_heders())
            if res.status_code == 200:
                with open(filename, 'wb') as f:
                    shutil.copyfileobj(res.raw, f)
                logger.warning(f'file has been downloaded and saved as: {filename}')
            else:
                logger.error(f'code: {res.status_code} while downloading: {url_string}')
                exit(1)
        no_meta_filename = cut_the_chapter(chapter, filename, tmp_folder)
        create_mp3_with_metadata(chapter, no_meta_filename, book_folder, tmp_folder, book_json)


def full_book_tmp_filename(tmp_folder):
    return tmp_folder / 'full_book.mp3'


def post_processing(book_folder, tmp_folder, book_json):
    chapter_count = 0
    # separate audio file into chapters
    items = json.loads(book_json['items'])
    for chapter in items:
        chapter_count += 1
        chapter['chapter_number'] = chapter_count
        chapter['number_of_chapters'] = len(items)
        no_meta_filename = cut_the_chapter(chapter, full_book_tmp_filename(tmp_folder), book_folder)
        create_mp3_with_metadata(chapter, no_meta_filename, book_folder, tmp_folder, book_json)


def download_book_by_m3u8_with_requests(m3u8_url, book_folder, tmp_folder, book_json):
    def get_key(url: str) -> bytes:
        resp = requests.get(url, headers=request_heders())
        assert resp.status_code == 200, 'Could not fetch decryption key.'
        return resp.content

    def make_cipher_for_segment(segment):
        key = get_key(segment.key.absolute_uri)
        iv = bytes.fromhex(segment.key.iv.lstrip('0x'))
        return AES.new(key, AES.MODE_CBC, IV=iv)

    segments = m3u8.load(m3u8_url).segments
    stream_path = (tmp_folder / 'stream.ts')
    with open(stream_path, mode='wb') as file:
        bar_format = 'Downloading segment {n}/{total} [{elapsed}]'
        for segment in tqdm.tqdm(segments, bar_format=bar_format):
            cipher = make_cipher_for_segment(segment)
            for chunk in requests.get(segment.absolute_uri, stream=True, headers=request_heders()):
                file.write(cipher.decrypt(chunk))

    ffmpeg_command = ffmpeg_common_command() + ['-i', stream_path, full_book_tmp_filename(tmp_folder)]
    subprocess.run(ffmpeg_command)
    post_processing(book_folder, tmp_folder, book_json)


def download_book_by_m3u8_with_ffmpeg(m3u8_url, book_folder, tmp_folder, book_json):
    ffmpeg_command = ffmpeg_common_command() + ['-i', m3u8_url, full_book_tmp_filename(tmp_folder)]
    subprocess.run(ffmpeg_command)
    post_processing(book_folder, tmp_folder, book_json)


def create_work_dirs(output_folder, book_json, book_soup, book_url, naming):
    if naming == NAMING_ID:
        book_folder = Path(output_folder) / sanitize_filename(book_url.strip('/').split('/')[-1])
    else:
        # sanitize (make valid) book title
        book_json['title'] = sanitize_filename(book_json['title'])
        book_json['titleonly'] = sanitize_filename(book_json['titleonly'])
        book_json['author'] = sanitize_filename(book_json['author'])
        if naming == NAMING_DEEP:
            book_folder = Path(output_folder) / book_json['author'] / book_json['titleonly']
        else:
            book_folder = Path(output_folder) / f'{book_json["author"]} - {book_json["titleonly"]}'

        bs_series = book_soup.findAll('div', {'class': 'caption__article--about-block about--series'})
        if len(bs_series) == 1:
            series_name = bs_series[0].find('a').find('span').get_text().split('(')
            if len(series_name) == 2:
                book_json['series_name'] = sanitize_filename(series_name[0].strip(' '))
                book_json['series_number'] = series_name[1].split(')')[0].strip(' ')
                if len(book_json['series_name']) > 0:
                    if naming == NAMING_DEEP:
                        book_folder = (Path(output_folder) / book_json['author'] / book_json['series_name'] /
                                       book_json['titleonly'])
                    else:
                        book_folder = Path(output_folder) / (f'{book_json["author"]} - {book_json["series_name"]} '
                                                             f'- {book_json["titleonly"]}')

    # create new folder with book title
    Path(book_folder).mkdir(exist_ok=True, parents=True)

    # create tmp folder. It will be removed
    tmp_folder = book_folder / 'tmp'
    Path(tmp_folder).mkdir(exist_ok=True)

    return book_folder, tmp_folder


def download_book(book_url, output_folder, download_method=download_book_by_m3u8_with_requests, naming=NAMING_DEEP):

    logger.debug(f'start downloading book: {book_url}')
    # create output folder
    Path(output_folder).mkdir(exist_ok=True)

    book_requests, book_html = get_book_requests(book_url)
    book_json, m3u8_url = analyse_book_requests(book_requests)
    book_soup = BeautifulSoup(book_html, 'html.parser')
    book_folder, tmp_folder = create_work_dirs(output_folder, book_json, book_soup, book_url, naming)

    # download cover picture
    download_cover(book_json, tmp_folder)

    if m3u8_url is None: # playlist not found.
        # try to parse html
        mp3_url = find_mp3_url(book_soup)
        if mp3_url is None:
            logger.error('mp3 url not found')
            exit(1)
        else:
            download_book_by_mp3_url(mp3_url, book_folder, tmp_folder, book_json)
    else: # it's ordinary case
        # download_book_by_m3u8_with_ffmpeg(m3u8_url, book_folder, tmp_folder, book_json)
        download_method(m3u8_url, book_folder, tmp_folder, book_json)

    logger.warning(f'The book has been downloaded: {book_folder}')
    # remove full book folder
    shutil.rmtree(tmp_folder, ignore_errors=True)
    return book_folder


def parse_series(series_url, output_folder, download_method=download_book_by_m3u8_with_requests, naming=NAMING_DEEP):
    logger.warning('the series has been discovered')
    res = requests.get(series_url, headers=request_heders())
    if res.status_code == 200:
        series_soup = BeautifulSoup(res.text, 'html.parser')
        bs_links_soup = (series_soup.find('div', {'class':'content__main__articles'}).
                findAll('a', {'class': 'content__article-main-link tap-link'}))
        for bs_link_soup in bs_links_soup:
            download_book(bs_link_soup['href'], output_folder, download_method, naming)
    else:
        logger.error(f'code: {res.status_code} while downloading: {series_url}')


if __name__ == '__main__':
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.WARNING
    )
    parser = argparse.ArgumentParser(description='Загрузчик книг с сайта akniga.org')
    parser.add_argument('-d','--download-method', default=DOWNLOAD_REQUESTS,
                        choices=[DOWNLOAD_REQUESTS, DOWNLOAD_FFMPEG],
                        help='Способ загрузки контента: с помощью отдельных запросов или ffmpeg')
    parser.add_argument('-n','--naming', default=NAMING_DEEP, choices=[NAMING_DEEP, NAMING_WIDE, NAMING_ID],
                        help=f'Имена для выходных каталогов: [{NAMING_DEEP}] - путь Автор/Серия/Название; '
                             f'[{NAMING_WIDE}] - каталог Автор-Серия-Название; '
                             f'[{NAMING_ID}] - каталог с идентификатором из url')
    parser.add_argument('url', help='Адрес (url) страницы с книгой или серией книг')
    parser.add_argument('output', help='Путь к папке загрузки')
    args = parser.parse_args()
    logger.info(args)

    download_method = download_book_by_m3u8_with_ffmpeg if args.download_method == DOWNLOAD_FFMPEG \
        else download_book_by_m3u8_with_requests
    if '/series/' in args.url:
        parse_series(args.url, args.output, download_method, args.naming)
    else:
        download_book(args.url, args.output, download_method, args.naming)
