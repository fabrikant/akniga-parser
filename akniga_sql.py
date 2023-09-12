from sqlalchemy import Column, Integer, String, Boolean, create_engine, ForeignKey
from sqlalchemy.orm import Session, declarative_base, relationship

Base = declarative_base()



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
    url = Column(String, nullable=False, unique=True)
    author = relationship("Author", back_populates="books")
    performer = relationship("Performer", back_populates="books")
    seria = relationship("Seria", back_populates="books")

def crate_database(connection_string):
    engine = create_engine(connection_string, echo=True)
    Base.metadata.create_all(engine)


def get_session(connection_string):
    engine = create_engine(connection_string)
    return Session(bind=engine)


def get_or_create(session, model, **kwargs):
    instance = session.query(model).filter_by(url=kwargs['url']).first()
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        session.add(instance)
        session.commit()
        return instance