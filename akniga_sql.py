from sqlalchemy import Column, Integer, String, Boolean, Float, create_engine, ForeignKey
from sqlalchemy.orm import Session, declarative_base, relationship
from sqlalchemy.sql import text
import logging
import akniga_sql_requests

logger = logging.getLogger()
Base = declarative_base()


class FilterType(Base):
    __tablename__ = 'filter_types'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False, unique=True)
    values = relationship('Filter', order_by='Filter.name', back_populates='type')


class Filter(Base):
    __tablename__ = 'filters'
    id = Column(Integer, primary_key=True, autoincrement=True)
    types_id = Column(Integer, ForeignKey('filter_types.id'))
    parent_id = Column(Integer, ForeignKey('filters.id'))
    name = Column(String, nullable=False)
    url = Column(String, nullable=False, unique=True)
    type = relationship('FilterType', back_populates='values')
    books = relationship('BookFilter', back_populates='filters')
    parent = relationship('Filter', remote_side=[id], back_populates='children')
    children = relationship('Filter', back_populates='parent')


class BookFilter(Base):
    __tablename__ = 'books_filters'
    book_id = Column(Integer, ForeignKey('books.id'), primary_key=True)
    filter_id = Column(Integer, ForeignKey('filters.id'), primary_key=True)
    books = relationship('Book', back_populates='filters')
    filters = relationship('Filter', order_by='Book.title', back_populates='books')


class Author(Base):
    __tablename__ = 'authors'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False, unique=True)
    books = relationship('Book', order_by='Book.title', back_populates='author')


class Performer(Base):
    __tablename__ = 'performers'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False, unique=True)
    books = relationship('Book', order_by='Book.title', back_populates='performer')


class Seria(Base):
    __tablename__ = 'serias'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False, unique=True)
    books = relationship('Book', order_by='Book.title', back_populates='seria')


class Book(Base):
    __tablename__ = 'books'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String)
    description = Column(String)
    duration = Column(Integer)
    free = Column(Boolean)
    author_id = Column(Integer, ForeignKey('authors.id'))
    performer_id = Column(Integer, ForeignKey('performers.id'), nullable=True)
    seria_id = Column(Integer, ForeignKey('serias.id'), nullable=True)
    year = Column(Integer, nullable=True)
    rating = Column(Float, nullable=True)
    url = Column(String, nullable=False, unique=True)
    author = relationship("Author", back_populates="books")
    performer = relationship("Performer", back_populates="books")
    seria = relationship("Seria", back_populates="books")
    filters = relationship("BookFilter", back_populates="books")


def crate_database(connection_string):
    engine = create_engine(connection_string, echo=True)
    Base.metadata.create_all(engine)
    for sql_req in akniga_sql_requests.get_on_base_create_requests():
        get_session(connection_string).execute(text(sql_req))


def get_session(connection_string):
    engine = create_engine(connection_string)
    return Session(bind=engine)


def get_or_create(session, model, update, **kwargs):
    instance = session.query(model).filter_by(url=kwargs['url']).first()
    caption =''
    if 'name' in kwargs.keys():
        caption = kwargs['name']
    elif 'title' in kwargs.keys():
        caption = kwargs['title']

    if instance:
        logger.debug(f'FOUND {caption} type: {model} url: {kwargs["url"]}')
        if update:
            for key, value in kwargs.items():
                setattr(instance, key, value)
            session.add(instance)
            session.commit()
            logger.debug(f'UPDATE {caption} type: {model} url: {kwargs["url"]}')
    else:
        instance = model(**kwargs)
        session.add(instance)
        session.commit()
        logger.debug(f'CREATED {caption} type: {model} url: {kwargs["url"]}')

    return instance


def get_or_create_filter(session, model, update, **kwargs):
    instance = get_or_create(session, model, update, **kwargs)
    parent_url = '{0}'.format('/'.join(instance.url.split('/')[0:-1]))
    parent = session.query(model).filter_by(url=parent_url).first()
    if parent:
        if not instance.parent_id == parent.id:
            logger.debug(f'set parent {parent.name} for filter {instance.name} url: {kwargs["url"]}')
            instance.parent_id = parent.id
            session.add(instance)
            session.commit()
    return instance


def create_book_filter_if_not_exists(session, book_id, filter_id):
    instance = session.query(BookFilter).filter_by(book_id=book_id,  filter_id=filter_id).first()
    if instance:
        return instance
    else:
        instance = BookFilter(book_id=book_id,  filter_id=filter_id)
        session.add(instance)
        session.commit()
        return instance


def book_exists(book_url, session):
    if session.query(Book).filter_by(url=book_url).first():
        return True
    else:
        return False