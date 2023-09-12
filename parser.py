import logging
import akniga_sql
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def convert_to_number(number_string):
    return int(f'0{number_string.split(" ")[0]}')

def add_book_to_database(book_url, connection_string):
    logger.info(f'get: {book_url}')
    res = requests.get(book_url)
    if res.status_code == 200:
        book_soup = BeautifulSoup(res.text, 'html.parser')
        session = akniga_sql.get_session(connection_string)

        # Книга
        title = book_soup.find('div', {'itemprop': 'name'}).get_text().strip()
        description = (book_soup.find('div', {'itemprop': 'description'}).get_text().
                       replace('Описание', '').replace('\n', '')).strip()

        free_book = book_soup.find('a', {'href': 'https://akniga.org/paid/'}) is None
        # Продолжительность
        hours = book_soup.find('span', {'class': 'hours'}).get_text()
        minutes = book_soup.find('span', {'class': 'minutes'}).get_text()
        duration = convert_to_number(hours)*60+convert_to_number(minutes)
        book_db = akniga_sql.get_or_create(session, akniga_sql.Book,
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
            book_db.author_id = akniga_sql.get_or_create(session, akniga_sql.Author, url=author_url, name=author).id
            session.add(book_db)

        # Исполнитель
        performer_soup = book_soup.find('a', {'rel': 'performer'})
        if not performer_soup is None:
            performer_url = performer_soup['href']
            performer = performer_soup.get_text().replace('\n', '')
            book_db.performer_id = akniga_sql.get_or_create(session,
                                                         akniga_sql.Performer, url=performer_url, name=performer).id
            session.add(book_db)

        # Серия
        series_soup = book_soup.find('div', {'class': 'about--series'})
        if not series_soup is None:
            series_soup = series_soup.find('a')
            seria_url = series_soup['href']
            seria = series_soup.get_text().split('(')[0].replace('\n', '')
            book_db.seria_id = akniga_sql.get_or_create(session, akniga_sql.Seria, url=seria_url, name=seria).id
            session.add(book_db)

        session.commit()

    else:
        logger.error(f'code: {res.status_code} while get: {book_url}')


def start_parsing(database_connection_string, site_url):
    akniga_sql.crate_database(database_connection_string)
    for page_number in range(1, 2):
        get_url = f'{site_url}/index/page{page_number}/'
        logger.info(f'get: {get_url}')
        res = requests.get(get_url)
        if res.status_code == 200:
            soup_books = BeautifulSoup(res.text, 'html.parser').findAll('div', {'class':'content__main__articles--item'})
            for soup_book in soup_books:
                book_url = soup_book.find('a')['href']
                logger.info(f'find book url: {book_url}')
                add_book_to_database(book_url, database_connection_string)
        else:
            logger.error(f'code: {res.status_code} while get: {get_url}')


if __name__ == '__main__':
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
    )
    database_connection_string = 'sqlite:///akniga.db'
    site_url = 'https://akniga.org'
    start_parsing(database_connection_string, site_url)