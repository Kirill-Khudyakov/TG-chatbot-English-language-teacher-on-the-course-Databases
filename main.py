import configparser
import time
import sqlalchemy
import telebot
import logging
import random
from telebot.storage import StateMemoryStorage
from telebot import types, custom_filters
from telebot.handler_backends import State, StatesGroup
from sqlalchemy.orm import sessionmaker
from models import create_tables, Word, User, UserWord


# Настройка логирования
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        # Логирование в файл
                        logging.FileHandler("user_states.log"),
                        # logging.StreamHandler()  # Логирование в консоль
                    ])
logger = logging.getLogger(__name__)


def user_list(engine):
    """Получение списка пользователей из базы данных."""
    try:
        session = sessionmaker(bind=engine)()
        users = session.query(User).all()
        users = [user.chat_id for user in users]
    except Exception as e:
        logger.error(f"Ошибка при получении списка пользователей: {e}")
        return []
    finally:
        session.close()
    return users


def add_users(engine, new_user_id, user_name):
    """Добавление нового пользователя в базу данных."""
    try:
        session = sessionmaker(bind=engine)()
        session.add(User(chat_id=new_user_id, first_name=user_name))
        session.commit()
        logger.info(f'Пользователь {user_name} (ID: {new_user_id}) добавлен.')
    except Exception as e:
        logger.error(
            f'Ошибка при добавлении пользователя {user_name} (ID: {new_user_id}): {e}')
    finally:
        session.close()


def get_words(engine, new_user_id):
    """Получение слов пользователя из базы данных."""
    try:
        session = sessionmaker(bind=engine)()
        words = session.query(UserWord.word, UserWord.translate).join(
            User, User.id == UserWord.user_id).filter(User.chat_id == new_user_id).all()
        all_words = session.query(Word.word, Word.translate).all()
        result = all_words + words
    except Exception as e:
        logger.error(
            f'Ошибка при получении слов пользователя {new_user_id}: {e}')
        return []
    finally:
        session.close()
    return result


def add_words(engine, chat_id, word, translate):
    """Добавление слова в базу данных для пользователя."""
    try:
        session = sessionmaker(bind=engine)()
        user_id = session.query(User.id).filter(
            User.chat_id == chat_id).first()[0]
        session.add(UserWord(word=word, translate=translate, user_id=user_id))
        session.commit()
        user_name = session.query(User).filter(
            User.chat_id == chat_id).first().name
        logger.info(
            f'Слово "{word}" добавлено для пользователя {user_name} (ID: {chat_id}).')
    except Exception as e:
        logger.error(
            f'Ошибка при добавлении слова "{word}" для пользователя {chat_id}: {e}')
    finally:
        session.close()


def delete_words(engine, chat_id, word):
    """Удаление слова из базы данных для пользователя."""
    try:
        session = sessionmaker(bind=engine)()
        user_id = session.query(User.id).filter(
            User.chat_id == chat_id).first()[0]
        session.query(UserWord).filter(UserWord.user_id ==
                                       user_id, UserWord.word == word).delete()
        session.commit()
        user_name = session.query(User).filter(User.chat_id == chat_id).first()
        user_display_name = user_name.first_name if user_name else 'Неизвестный пользователь'

        logger.info(
            f'Слово "{word}" удалено для пользователя {user_display_name} (ID: {chat_id}).')
    except Exception as e:
        logger.error(
            f'Ошибка при удалении слова "{word}" для пользователя {chat_id}: {e}')
    finally:
        session.close()


# Чтение конфигурации из файла
config = configparser.ConfigParser()
config.read('config.ini')


# Установка соединения с базой данных
DSN = config['database']['dsn']
engine = sqlalchemy.create_engine(DSN)


Session = sessionmaker(bind=engine)
session = Session()
create_tables(engine)


# Токен вашего бота
state_storage = StateMemoryStorage()
TOKEN = config['token']['tg_bot']
bot = telebot.TeleBot(TOKEN, state_storage=state_storage)

known_users = user_list(engine)
print(f'Добавлено {len(known_users)} пользователей')
userStep = {}
buttons = []


def show_hint(*lines):
    """Формирование подсказки для пользователя."""
    return '\n'.join(lines)


def show_target(data):
    """Формирование строки с целевым словом и переводом."""
    return f"{data['translate_word']} -> {data['target_word']}"


class Command:
    ADD_WORD = 'Добавить слово ✏️'
    DELETE_WORD = 'Удалить слово 🗑️'
    NEXT = 'Дальше ➡️'


class MyStates(StatesGroup):
    target_word = State()
    translate_word = State()
    another_word = State()


def get_user_id(user_id):
    if user_id in userStep:
        return userStep[user_id]
    else:
        known_users.append(user_id)
        userStep[user_id] = 0
        print(f'Новый пользователь: {user_id}')
        return 0


@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    user_name = message.from_user.first_name

    if chat_id not in known_users:
        known_users.append(chat_id)
        add_users(engine, chat_id, user_name)
        userStep[chat_id] = 0
        bot.send_message(
            message.chat.id,
            f'👋 Привет, {user_name}! Добро пожаловать в *EnglishQuest*! 🌟\n\n'
            'Я ваш персональный бот для изучения английских слов. 📚\n'
            'С помощью меня вы сможете:\n'
            '✅ Изучать новые слова\n'
            '✅ Проверять свои знания\n'
            '✅ Отслеживать прогресс\n\n'
            'Чтобы начать, просто напишите или нажмите /help, чтобы получить список доступных команд. 🚀'
        )
        logger.info(
            f'Пользователь {user_name} (ID: {chat_id}) начал взаимодействие с ботом.')
    else:
        bot.send_message(
            message.chat.id, f'{user_name}!\n'
            'Чтобы продолжить, воспользуйтесь кнопками на клавиатуре.📲\n'
            'Если вам нужна помощь, просто введите или нажмите /help, чтобы увидеть все команды. 🚀')
        logger.info(f'Пользователь {user_name} (ID: {chat_id}) уже в системе.')


@bot.message_handler(commands=['help'])
def send_help(message):
    bot.send_message(
        message.chat.id,
        '🔍 **Доступные команды:**\n\n'
        '/learn - начать изучение слов 📚\n'
        '/list - список изучаемых слов 📜\n'
        'Используйте команды выше, чтобы начать изучение и отслеживать прогресс!'
    )


@bot.message_handler(commands=['list'])
def list_words(message):
    chat_id = message.chat.id
    user_name = message.from_user.first_name
    words = get_words(engine, chat_id)

    if not words:
        bot.send_message(
            chat_id, 'У вас нет изученных слов. Добавьте слова с помощью команды /learn или /add.')
        logger.info(
            f'Пользователь {user_name} (ID: {chat_id}) запросил список слов, но у него их нет.')
        return

    # Формируем список слов для отправки
    word_list = '\n'.join([f"{word[0]} -> {word[1]}" for word in words])
    bot.send_message(chat_id, f'📜 Ваши изучаемые слова:\n{word_list}')
    logger.info(
        f'Пользователь {user_name} (ID: {chat_id}) запросил список слов: {word_list}')


@bot.message_handler(commands=['learn'])
def learn_words(message):
    global buttons
    buttons = []

    chat_id = message.chat.id
    user_name = message.from_user.first_name
    words = get_words(engine, chat_id)

    if len(words) < 4:
        bot.send_message(
            chat_id, '❌ Недостаточно слов для обучения. Пожалуйста, добавьте больше слов.')
        logger.info(
            f'Пользователь {user_name} (ID: {chat_id}) попытался начать обучение, но недостаточно слов.')
        return

    get_word = random.sample(words, 4)
    word = get_word[0]
    target_word = word[1]
    translate = word[0]

    target_word_btn = types.KeyboardButton(target_word)
    buttons.append(target_word_btn)
    others = [word[1] for word in get_word[1:]]
    other_words_btns = [types.KeyboardButton(word) for word in others]
    buttons.extend(other_words_btns)
    random.shuffle(buttons)

    markup = types.ReplyKeyboardMarkup(row_width=2)
    next_btn = types.KeyboardButton(Command.NEXT)
    add_word_btn = types.KeyboardButton(Command.ADD_WORD)
    delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
    buttons.extend([next_btn, add_word_btn, delete_word_btn])
    markup.add(*buttons)

    bot.send_message(
        message.chat.id,
        f'🗣️ Выберите перевод слова: 🇷🇺 *{word[0]}* \n\n'
        'Вот ваши варианты:\n',
        reply_markup=markup
    )
    bot.set_state(message.from_user.id, MyStates.target_word, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['target_word'] = target_word
        data['translate_word'] = translate
        data['other_words'] = others
    logger.info(
        f'Пользователь {user_name} (ID: {chat_id}) начал обучение со словом: {word[0]}.')


@bot.message_handler(func=lambda message: message.text == Command.NEXT)
def next_cards(message):
    learn_words(message)


@bot.message_handler(func=lambda message: message.text == Command.DELETE_WORD)
def delete_word(message):
    user_name = message.from_user.first_name if message.from_user.first_name else 'Неизвестный пользователь'
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        try:
            logger.info(
                f'Пользователь {user_name} (ID: {message.chat.id}) запросил удаление слова: {data["translate_word"]}.')
            delete_words(engine, message.chat.id, data['translate_word'])
            bot.send_message(message.chat.id, '✅ Слово успешно удалено!')
        except Exception as e:
            logger.error(f"Ошибка при удалении слова: {e}")
            bot.send_message(
                message.chat.id, '❌ Произошла ошибка при удалении слова. Попробуйте еще раз.')


@bot.message_handler(func=lambda message: message.text == Command.ADD_WORD)
def add_word(message):
    chat_id = message.chat.id
    user_name = message.from_user.first_name
    userStep[chat_id] = 1
    bot.send_message(chat_id, '✏️ Введите слово на Русском 🇷🇺:')
    bot.set_state(message.from_user.id, MyStates.target_word, message.chat.id)
    logger.info(
        f'Пользователь {user_name} (ID: {chat_id}) начал процесс добавления слова.')


@bot.message_handler(func=lambda message: True, content_types=['text'])
def message_reply(message):
    text = message.text
    markup = types.ReplyKeyboardMarkup(row_width=2)
    chat_id = message.chat.id
    user_name = message.from_user.first_name

    # Проверяем, существует ли chat_id в userStep
    if chat_id not in userStep:
        userStep[chat_id] = 0

    # Проверка состояния пользователя
    if userStep[chat_id] == 0:
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            target_word = data.get('target_word')
            if text.strip().lower() == target_word.strip().lower():
                hint = show_target(data)
                hint_text = ['✅ Правильно! Отличная работа!', hint]
                next_btn = types.KeyboardButton(Command.NEXT)
                add_word_btn = types.KeyboardButton(Command.ADD_WORD)
                delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
                markup.add(next_btn, add_word_btn, delete_word_btn)
                bot.send_message(message.chat.id, '\n'.join(
                    hint_text), reply_markup=markup)
            else:
                bot.send_message(
                    message.chat.id, '❌ Неправильно. Попробуйте еще раз!')

    elif userStep[chat_id] == 1:
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['target_word'] = text
            bot.send_message(
                chat_id, 'Enter the English translation of the word 🇺🇸: ')
            bot.set_state(message.from_user.id,
                          MyStates.translate_word, message.chat.id)
            userStep[chat_id] = 2

    elif userStep[chat_id] == 2:
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['translate_word'] = text
        add_words(engine, chat_id, data['target_word'], data['translate_word'])
        bot.send_message(chat_id, '✅ Слово успешно добавлено!')
        userStep[chat_id] = 0  # Сброс состояния
        logger.info(
            f'Пользователь {user_name} (ID: {chat_id}) добавил слово: {data["target_word"]} с переводом: {data["translate_word"]}.')
        learn_words(message)


bot.add_custom_filter(custom_filters.StateFilter(bot))

if __name__ == "__main__":
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        time.sleep(15)
