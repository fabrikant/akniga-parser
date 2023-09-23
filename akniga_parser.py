import argparse
import logging
import akniga_sql as sql
import requests
from bs4 import BeautifulSoup
import re
from akniga_global import request_heders

logger = logging.getLogger(__name__)
akniga_url = 'https://akniga.org'


def convert_to_number(number_string):
    res = 0
    try:
        res = int(f'0{number_string.split(" ")[0]}')
    except ValueError as message:
        logger.error(message)
    return res


def books_url_iter(soup_page):
    soup_books = soup_page.findAll('div', {'class': 'content__main__articles--item'})
    if not soup_books is None:
        for soup_book in soup_books:
            book_url = soup_book.find('a')
            if not book_url is None:
                book_url = book_url['href']
                logger.debug(f'find book url: {book_url}')
                yield book_url


def get_next_page_url(soup_page, stop_page_number=None ):
    result = None
    soup_next_page = (soup_page.find('div', {'class': 'page__nav'}).
                      find('a', {'class': 'page__nav--next'}))
    if not soup_next_page is None:
        result = soup_next_page['href']
        if stop_page_number:
            next_page_number = result.replace('/', '').split('page')
            if len(next_page_number):
                next_page_number = convert_to_number(next_page_number[-1])
                if stop_page_number < next_page_number > 0:
                    result = None
    return result


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
            hours = 0
        else:
            hours = convert_to_number(hours.get_text())

        minutes = book_soup.find('span', {'class': 'minutes'})
        if minutes is None:
            minutes = 0
        else:
            minutes = convert_to_number(minutes.get_text())

        duration = hours * 60 + minutes
        book_db = sql.get_or_create(session, sql.Book, update,
                                    url=book_url,
                                    title=title,
                                    description=description,
                                    duration=duration,
                                    duration_hours=hours,
                                    duration_minutes=minutes,
                                    free=free_book)

        # Автор
        author_soup = book_soup.find('a', {'rel': 'author'})
        if not author_soup is None:
            author_url = author_soup['href']
            author = author_soup.get_text().replace('\n', '')
            book_db.author_id = sql.get_or_create(session, sql.Author, update,
                                                         url=author_url, name=author).id
            session.add(book_db)

        # Исполнитель
        performer_soup = book_soup.find('a', {'rel': 'performer'})
        if not performer_soup is None:
            performer_url = performer_soup['href']
            performer = performer_soup.get_text().replace('\n', '')
            book_db.performer_id = sql.get_or_create(session, sql.Performer, update,
                                                            url=performer_url, name=performer).id
            session.add(book_db)

        # Серия
        series_soup = book_soup.find('div', {'class': 'about--series'})
        if not series_soup is None:
            series_soup = series_soup.find('a')
            seria_url = series_soup['href']
            seria = series_soup.get_text().split('(')[0].replace('\n', '')
            book_db.seria_id = sql.get_or_create(session, sql.Seria, update,
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
                    filter_type_db = sql.get_or_create(session, sql.FilterType, update,
                                                              url=filter_type_url, name=type_of_filters)

                    filter_db = sql.get_or_create_filter(session, sql.Filter, update,
                                                                url=filter_url, name=filter_name,
                                                                types_id=filter_type_db.id)

                    sql.create_book_filter_if_not_exists(session, book_id=book_db.id, filter_id=filter_db.id)
        session.commit()
        logger.info(f'BOOK complete - {book_db}')
        return book_db
    else:
        logger.error(f'code: {res.status_code} while get: {book_url}')
        return None


def start_parsing(connection_string, update, full_scan, start_page, stop_page):
    session = sql.get_session(connection_string)
    processed_urls = []
    get_url = f'{akniga_url}/index/page{start_page}/'
    while not get_url is None:
        logger.info(f'get new books page: {get_url}')
        res = requests.get(get_url, headers=request_heders())
        if res.status_code == 200:
            soup_page = BeautifulSoup(res.text, 'html.parser')
            for book_url in books_url_iter(soup_page):
                if not full_scan:
                    if not book_url in processed_urls:
                        if sql.book_exists(book_url, session):
                            logger.info(f'book already exists in database url: {book_url}')
                            return
                add_book_to_database(book_url, session, update)
                if not full_scan:
                    processed_urls.append(book_url)

            get_url = get_next_page_url(soup_page, stop_page)
        else:
            logger.error(f'code: {res.status_code} while get: {get_url}')
            return


def get_sections(session):
    result = []
    get_url = f'{akniga_url}/sections/'
    logger.info(f'get sections urls: {get_url}')
    res = requests.get(get_url, headers=request_heders())
    if res.status_code == 200:
        soup_page = BeautifulSoup(res.text, 'html.parser')
        sections = soup_page.findAll('h4')
        for section_soup in sections:
            section_soup = section_soup.find('a')
            if not section_soup is None:
                section_url = section_soup['href']
                section_name = section_soup.get_text().strip()
                if akniga_url in section_url:
                    section_db = sql.get_or_create(session, sql.Section, True,
                                             url=section_url, name=section_name)
                    result.append(section_db)
        return result
    else:
        logger.error(f'code: {res.status_code} while get: {get_url}')
        return


def parse_section(session, update, section_db):
    get_url = section_db.url
    logger.info(f'get section {section_db.name} urls: {get_url}')
    while not get_url is None:
        logger.info(f'get new books page {section_db.name}: {get_url}')
        res = requests.get(get_url, headers=request_heders())
        if res.status_code == 200:
            soup_page = BeautifulSoup(res.text, 'html.parser')

            for book_url in books_url_iter(soup_page):
                book_db = session.query(sql.Book).filter_by(url=book_url).first()
                if not book_db:
                    book_db = add_book_to_database(book_url, session, update)

                sql.create_book_section_if_not_exists(session, book_id=book_db.id, section_id=section_db.id)

            get_url = get_next_page_url(soup_page)
        else:
            logger.error(f'code: {res.status_code} while get: {get_url}')
            return


def start_parsing_sections(connection_string, update):
    session = sql.get_session(connection_string)
    sections_db = get_sections(session)
    for section_db in sections_db:
        parse_section(session, update, section_db)


if __name__ == '__main__':
    database_connection_string = 'sqlite:///akniga.sqlite'
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
    )
    parser = argparse.ArgumentParser(description='Парсинг сайта akniga.org и создание базы данных')
    parser.add_argument('-db', '--database', type=str, default=f'{database_connection_string}',
                        help='Строка подключения к базе данных. '
                        f'Например (по умолчанию): [{database_connection_string}]. '
                        'Узнать больше: https://docs.sqlalchemy.org/en/20/core/engines.html')
    parser.add_argument('-u', '--update', default=False, action='store_true',
                        help='Обновлять найденные объекты свежими данными.')
    parser.add_argument('-f', '--full-scan',  default=False, action='store_true',
                        help='Без этого параметра сканирование прервется, как только следующая книга будет найдена в '
                             'базе. Если нужно просто привести в актуальное состояние базу (добавить новые книги), '
                             'то опцию не активировать.')
    parser.add_argument('--start-page', type=int, default=1,
                        help='Страница с которой начинается сканирование. Если параметр не указан, то с первой. '
                             'Полезно, если необходимо продолжить после сбоя. '
                             'Рекомендуется использовать с параметром -f')
    parser.add_argument('--stop-page', type=int, default=0,
                        help='Последняя сканируемая страница. Полезно, если необходимо просканировать определенный '
                             'диапазон страниц. Если параметр не указан, то ограничивать сканирование будет параметр -f')
    parser.add_argument('-g', '--genres',  default=False, action='store_true',
                        help=f'Дополнительно просканировать книги по жанрам. Адреса: {akniga_url}/sections/'
                             'При обычном сканировании невозможно определить к каким жанрам относится книга, поэтому'
                             'требуется еще один проход. Если не планируется осуществлять отбор по жанрам, можно не'
                             'выполнять')

    args = parser.parse_args()
    logger.debug(args)
    sql.create_database(args.database)
    start_parsing(args.database, args.update, args.full_scan, args.start_page, args.stop_page)
    if args.genres:
        start_parsing_sections(args.database, args.update)
