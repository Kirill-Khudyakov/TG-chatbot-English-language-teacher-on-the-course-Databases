import configparser
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from models import create_tables, Word


def create_db(engine):
    words = (
        ('Здравствуйте', 'Hello'),
        ('До свидания', 'Goodbye'),
        ('Красный', 'Red'),
        ('Синий', 'Blue'),
        ('Зеленый', 'Green'),
        ('Желтый', 'Yellow'),
        ('Черный', 'Black'),
        ('Белый', 'White'),
        ('Я', 'I'),
        ('Ты', 'You'),
        ('Он', 'He'),
        ('Она', 'She'),
        ('Яблоко', 'Apple'),        
        ('Книга', 'Book'),
        ('Кот', 'Cat'),
        ('Собака', 'Dog'),
        ('Цветок', 'Flower'),
        ('Слон', 'Elephant'),
        ('Дом', 'House'),
        ('Мороженое', 'Ice cream'),
        ('Сок', 'Juice'),
        ('Ключ', 'Key'),
        ('Лев', 'Lion'),
        ('Гора', 'Mountain'),
        ('Блокнот', 'Notebook'),
        ('Апельсин', 'Orange'),
        ('Карандаш', 'Pencil'),
        ('Королева', 'Queen'),
        ('Река', 'River'),
        ('Солнце', 'Sun'),
        ('Дерево', 'Tree'),
        ('Зонт', 'Umbrella'),
        ('Скрипка', 'Violin'),
        ('Окно', 'Window'),
        ('Двор', 'Yard'),
        ('Зебра', 'Zebra'),
        ('Друг', 'Friend'),
        ('Счастливый', 'Happy'),
        ('Любовь', 'Lowe'),
        ('Музыка', 'Music'),
        ('Вода', 'Water')
    )
    create_tables(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        for pair in words:
            session.add(Word(word=pair[0], translate=pair[1]))
        session.commit()
    except Exception as e:
        session.rollback()  # Откат транзакции в случае ошибки
        print(f"Произошла ошибка: {e}")
    finally:
        session.close()  # Закрываем сессию
    

# Чтение конфигурации из файла
config = configparser.ConfigParser()
config.read('config.ini')

# Установка соединения с базой данных
DSN = config['database']['dsn']
engine = sqlalchemy.create_engine(DSN)

create_db(engine)    

# Проверка добавленных слов
def check_words(engine):
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        words = session.query(Word).all()
        for word in words:
            print(f"{word.word} -> {word.translate}")
    finally:
        session.close()

check_words(engine)  # Вызов функции для проверки



