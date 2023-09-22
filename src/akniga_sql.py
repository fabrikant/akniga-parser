from sqlalchemy import Column, Integer, String, Boolean, Float, create_engine, ForeignKey
from sqlalchemy.orm import Session, declarative_base, relationship
import logging

logger = logging.getLogger()
Base = declarative_base()


class FilterType(Base):
    __tablename__ = 'filter_types'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False, unique=True)
    values = relationship('Filter', order_by='Filter.name', back_populates='type')

    def __str__(self):
        return f'name: {self.name}; id: {self.id}; url: {self.url}'


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

    def __str__(self):
        return f'name: {self.name}; id: {self.id}; url: {self.url}'


class BookFilter(Base):
    __tablename__ = 'books_filters'
    book_id = Column(Integer, ForeignKey('books.id'), primary_key=True)
    filter_id = Column(Integer, ForeignKey('filters.id'), primary_key=True)
    books = relationship('Book', back_populates='filters')
    filters = relationship('Filter', order_by='Book.title', back_populates='books')


class Section(Base):
    __tablename__ = 'sections'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False, unique=True)
    books = relationship('BookSection', back_populates='sections')

    def __str__(self):
        return f'name: {self.name}; id: {self.id}; url: {self.url}'


class BookSection(Base):
    __tablename__ = 'books_sections'
    book_id = Column(Integer, ForeignKey('books.id'), primary_key=True)
    section_id = Column(Integer, ForeignKey('sections.id'), primary_key=True)
    books = relationship('Book', back_populates='sections')
    sections = relationship('Section', order_by='Book.title', back_populates='books')

class Author(Base):
    __tablename__ = 'authors'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False, unique=True)
    books = relationship('Book', order_by='Book.title', back_populates='author')

    def __str__(self):
        return f'name: {self.name}; id: {self.id}; url: {self.url}'


class Performer(Base):
    __tablename__ = 'performers'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False, unique=True)
    books = relationship('Book', order_by='Book.title', back_populates='performer')

    def __str__(self):
        return f'name: {self.name}; id: {self.id}; url: {self.url}'


class Seria(Base):
    __tablename__ = 'serias'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False, unique=True)
    books = relationship('Book', order_by='Book.title', back_populates='seria')

    def __str__(self):
        return f'name: {self.name}; id: {self.id}; url: {self.url}'


class Book(Base):
    __tablename__ = 'books'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String)
    description = Column(String)
    duration = Column(Integer, nullable=False)
    duration_hours = Column(Integer, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
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
    sections = relationship("BookSection", back_populates="books")

    def __str__(self):
        return f'title: {self.title}; id: {self.id}; url: {self.url}'


def create_database(connection_string):
    engine = create_engine(connection_string, echo=True)
    Base.metadata.create_all(engine)


def get_session(connection_string):
    engine = create_engine(connection_string)
    return Session(bind=engine)


def get_or_create(session, model, update, **kwargs):
    instance = session.query(model).filter_by(url=kwargs['url']).first()

    if instance:
        logger.debug(f'FOUND in the database - type: {model}; {instance}')
        if update:
            for key, value in kwargs.items():
                setattr(instance, key, value)
            session.add(instance)
            session.commit()
            logger.debug(f'UPDATE - type: {model}; {instance}')
    else:
        instance = model(**kwargs)
        session.add(instance)
        session.commit()
        logger.debug(f'CREATED - type: {model}; {instance}')

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


def create_book_section_if_not_exists(session, book_id, section_id):
    instance = session.query(BookSection).filter_by(book_id=book_id,  section_id=section_id).first()
    if instance:
        return instance
    else:
        instance = BookSection(book_id=book_id,  section_id=section_id)
        session.add(instance)
        session.commit()
        return instance

def book_exists(book_url, session):
    if session.query(Book).filter_by(url=book_url).first():
        return True
    else:
        return False
