from aiogram import Bot, Dispatcher, executor, types  # pip install aiogram
from CONFIG import TOKEN, NAME_DB
from datetime import datetime
import logging
import parser_nm
import os.path
import sql_db

"""Записываем логи папку logs"""
if not os.path.isdir("logs"):
    os.mkdir("logs")

"""Подключаем базу данных"""
db = sql_db.SQLLite(NAME_DB)

"""Определяем название лога. Форматируем название по дате и времени"""
path_log = f"log_bot_{datetime.now().date()}_{datetime.now().strftime('%H.%M')}.log"

"""Для записи логов меняем деректорию"""
os.chdir('logs')

"""Инициализируем уровень логов
Бота требуется иногда перезапускать:
логи пишутся без остановки в 1 файл. Каждый перезапуск создает новый файл
Проблема в данный момент не решена."""
logging.basicConfig(filename=path_log, level=logging.INFO)

"""Инициализирем бота"""
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(commands=['status'])
async def status(message: types.Message):
    """Бот реагирует на команду /status"""
    logging.info(f'{message.from_user.id} выполнил команду "/status"')
    if not db.user_exists(message.from_user.id):
        # если юзера нет в базе - добавляем его
        information = dict(message.chat)
        db.add_user(message.from_user.id, information.get('first_name', 'Не указано'),
                    information.get('last_name', 'Не указано'))
    number_of_request = db.get_status(message.from_user.id)
    await message.answer(f'Количество запросов к боту: {number_of_request}')


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    logging.info(f'{message.from_user.id} выполнил команду "/start"')
    """Бот реагирует на команду /start"""
    await message.answer("""Здравствуйте!
Для использования данного бота Вам необходимо знать номер обращения в Service Desk компании Пилот. 
Номер запроса был направлен на почту ранее (при его регистрации)
Как же узнать информцию по Вашему запросу? Очень просто: необходимо просто отправить боту сообщение с номером

Доступные команды:
/start - вновь запросить данное сообщение
/status - узнать Ваше количество обращений к боту""")


@dp.message_handler()
async def answer(message: types.Message):
    """Функция, принимающая любое НЕ командное сообщение
    Информация вносится в базу данных"""
    information = dict(message.chat)
    if not db.user_exists(message.from_user.id):
        db.add_user(message.from_user.id, information.get('first_name', 'Не указано'),
                    information.get('last_name', 'Не указано'))
    await message.answer(naumen(message))


def naumen(message):
    """Обработка запроса.
    Обрабатываются только числовые значния в диапазоне [800.000 : последняя заявка]
    Отсекаются служебные заявки, переписки, проводимая профилактика"""
    a = parser_nm.Parser_NM()
    request = str(message.text).encode('UTF-8')
    logging.info(f'{message.from_user.id} выполнил запрос {request}')
    if message.text.isdigit():
        db.update_status(message.from_user.id)
        if int(message.text) > 799999:
            try:
                return a.get_content(message.text)
            except AttributeError:
                return 'Заявка имеет слишком большой номер. Вероятно была допущена ошибка'

        else:
            return 'Бот обрабатывает заявки, начиная с 800.000'
    return 'Ошибка команды'


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
