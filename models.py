import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'
    id = sq.Column(sq.Integer, primary_key=True)
    chat_id = sq.Column(sq.BigInteger, unique=True)
    first_name = sq.Column(sq.String(length=40))


class UserWord(Base):
    __tablename__ = 'user_word'
    id = sq.Column(sq.Integer, primary_key=True)
    word = sq.Column(sq.String(length=40), unique=True)
    translate = sq.Column(sq.String(length=40), unique=True)
    user_id = sq.Column(sq.Integer, sq.ForeignKey('user.id'), nullable=False)

    user = relationship(User, backref='word')

class Word(Base):
    __tablename__ = 'word'
    id = sq.Column(sq.Integer, primary_key=True)
    word = sq.Column(sq.String(length=40), unique=True)
    translate = sq.Column(sq.String(length=40), unique=True)


# Функция создания таблиц из классов.
def create_tables(engine):
    # Base.metadata.drop_all(engine)  # Использовать если необходимо удалить данные из БД
    Base.metadata.create_all(engine)