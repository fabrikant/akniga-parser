import argparse
import logging
import akniga_sql
import requests
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)
akniga_url = 'https://akniga.org'


def request_heders():
    return {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 '
                         'Safari/537.36'}


def convert_to_number(number_string):
    res = 0
    try:
        res = int(f'0{number_string.split(" ")[0]}')
    except ValueError as message:
        logger.error(message)
    return res


def convert_to_float(float_string):
    res = 0.0
    try:
        res = float(f'0{float_string.split(" ")[0]}')
    except ValueError as message:
        logger.error(message)
    return res


def find_book_property(book_soup, pattern_string):
    res = None
    field_soup = book_soup.find('div', string=re.compile(pattern_string))
    if not field_soup is None:
        field_soup = field_soup.parent.find('span')
        if not field_soup is None:
            res = field_soup.get_text().replace('\n', '').strip().split(' ')[0]
    return res


def add_book_to_database(book_url, session, update):
    logger.debug(f'start getting: {book_url}')
    res = requests.get(book_url, headers=request_heders())
    if res.status_code == 200:
        book_soup = BeautifulSoup(res.text, 'html.parser')

        # Книга
        title = book_soup.find('div', {'itemprop': 'name'})
        if title is None:
            title = ''
        else:
            title = title.get_text().strip()

        description = book_soup.find('div', {'itemprop': 'description'})
        if description is None:
            description = ''
        else:
            description = description.get_text().replace('Описание', '').replace('\n', '').strip()

        free_book = book_soup.find('a', {'href': 'https://akniga.org/paid/'}) is None
        # Продолжительность
        hours = book_soup.find('span', {'class': 'hours'})
        if hours is None:
            hours = '0'
        else:
            hours = hours.get_text()

        minutes = book_soup.find('span', {'class': 'minutes'})
        if minutes is None:
            minutes = '0'
        else:
            minutes = minutes.get_text()

        duration = convert_to_number(hours) * 60 + convert_to_number(minutes)
        book_db = akniga_sql.get_or_create(session, akniga_sql.Book, update,
                                 url=book_url,
                                 title=title,
                                 description=description,
                                 duration=duration,
                                 free=free_book)

        # Автор
        author_soup = book_soup.find('a', {'rel': 'author'})
        if not author_soup is None:
            author_url = author_soup['href']
            author = author_soup.get_text().replace('\n', '')
            book_db.author_id = akniga_sql.get_or_create(session, akniga_sql.Author, update,
                                                         url=author_url, name=author).id
            session.add(book_db)

        # Исполнитель
        performer_soup = book_soup.find('a', {'rel': 'performer'})
        if not performer_soup is None:
            performer_url = performer_soup['href']
            performer = performer_soup.get_text().replace('\n', '')
            book_db.performer_id = akniga_sql.get_or_create(session, akniga_sql.Performer, update,
                                                            url=performer_url, name=performer).id
            session.add(book_db)

        # Серия
        series_soup = book_soup.find('div', {'class': 'about--series'})
        if not series_soup is None:
            series_soup = series_soup.find('a')
            seria_url = series_soup['href']
            seria = series_soup.get_text().split('(')[0].replace('\n', '')
            book_db.seria_id = akniga_sql.get_or_create(session, akniga_sql.Seria, update,
                                                        url=seria_url, name=seria).id
            session.add(book_db)

        # Рейтинг
        rating = find_book_property(book_soup, 'Рейтинг')
        if not rating is None:
           book_db.rating = convert_to_float(rating)
           session.add(book_db)

        # Год
        year = find_book_property(book_soup, 'Год')
        if not year is None:
           book_db.year = convert_to_number(year)
           session.add(book_db)

        #Фильтры
        filers_url_prefix = f'{akniga_url}/label/'
        filters_soup = book_soup.find('article', {'itemtype': 'http://schema.org/Book'})
        if not filters_soup is None:
            filters_soup = filters_soup.find('div', {'class': 'classifiers__article-main'})
        if not filters_soup is None:
            filters_soup = filters_soup.findAll('div')
        if not filters_soup is None:
            for filter_types_soup in filters_soup:
                type_of_filters = (filter_types_soup.next.get_text().replace('\n', '').
                                   replace(':', '').strip())
                links_soup = filter_types_soup.findAll('a')
                for link_soup in links_soup:
                    filter_url = link_soup['href']
                    if not filers_url_prefix in filter_url:
                        continue
                    filter_name = link_soup.get_text()

                    filter_type_url = f'{filers_url_prefix}{filter_url.replace(filers_url_prefix,"").split("/")[0]}/'
                    filter_type_db = akniga_sql.get_or_create(session, akniga_sql.FilterType, update,
                                                              url=filter_type_url, name=type_of_filters)

                    filter_db = akniga_sql.get_or_create_filter(session, akniga_sql.Filter, update,
                                                                url=filter_url, name=filter_name,
                                                                types_id=filter_type_db.id)

                    akniga_sql.create_book_filter_if_not_exists(session, book_id=book_db.id, filter_id=filter_db.id)
        session.commit()
        logger.info(f'BOOK processing completed - {book_db}')
    else:
        logger.error(f'code: {res.status_code} while get: {book_url}')
        exit(1)


def start_parsing(connection_string, update, full_scan, start_page):
    akniga_sql.crate_database(connection_string)
    session = akniga_sql.get_session(connection_string)
    processed_urls = []
    get_url = f'{akniga_url}/index/page{start_page}/'
    while True:
        logger.info(f'get new books page: {get_url}')
        res = requests.get(get_url, headers=request_heders())
        if res.status_code == 200:
            soup_page = BeautifulSoup(res.text, 'html.parser')
            soup_books = soup_page.findAll('div', {'class': 'content__main__articles--item'})
            for soup_book in soup_books:
                book_url = soup_book.find('a')['href']
                logger.info(f'find book url: {book_url}')
                if not full_scan:
                    if not book_url in processed_urls:
                        if akniga_sql.book_exists(book_url, session):
                            logger.info(f'book already exists in database url: {book_url}')
                            exit(0)
                add_book_to_database(book_url, session, update)
                if not full_scan:
                    processed_urls.append(book_url)
            soup_next_page = (soup_page.find('div', {'class': 'page__nav'}).
                              find('a', {'class': 'page__nav--next'}))
            if soup_next_page is None:
                break
            else:
                get_url = soup_next_page['href']
        else:
            logger.error(f'code: {res.status_code} while get: {get_url}')
            exit(1)


if __name__ == '__main__':
    database_connection_string = 'sqlite:///akniga.db'
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
    )
    parser = argparse.ArgumentParser(description='Парсинг сайта akniga.org и создание базы данных')
    parser.add_argument('-db', '--database', type=str, default=f'{database_connection_string}',
                        help='Строка подключения к базе данных. '
                        f'Например (по умолчанию): [{database_connection_string}]. '
                        'Узнать больше: https://docs.sqlalchemy.org/en/20/core/engines.html')
    parser.add_argument('-u', '--update', default=False, action='store_true',
                        help='Обновлять  найденные в базе данные.')
    parser.add_argument('-f', '--full-scan',  default=False, action='store_true',
                        help='Продолжить сканирование, даже после обнаружения книги в базе данных. '
                        'Если нужно просто добавить в базу новые книги, то опцию лучше не активировать.')
    parser.add_argument('-s', '--start-page', type=int, default=1,
                        help='Страница с которой начинается сканирование. По умолчанию 1. Полезно если нужно '
                             'продолжить после сбоя. Рекомендуется использовать с параметром -f')

    args = parser.parse_args()
    logger.debug(args)
    start_parsing(args.database, args.update, args.full_scan, args.start_page)