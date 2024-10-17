import sqlite3
import logging
from aiogram import Bot, types
from aiogram import Dispatcher
from aiogram.filters import Command  # Імпортуйте Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import asyncio

# Налаштування логування
logging.basicConfig(level=logging.INFO)

API_TOKEN = '8054215916:AAH6yu5PolWIqAX6c8DQ0bXFzby2WZnvF0M'  # Вставте ваш токен бота

# Підключення до бази даних
conn = sqlite3.connect('user_data.db')
cursor = conn.cursor()

# Створення таблиці для збереження відповідей
cursor.execute('''
    CREATE TABLE IF NOT EXISTS answers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        question_type TEXT,
        question TEXT,
        answer TEXT,
        answer_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

# Закриття з'єднання
conn.commit()
conn.close()

# Створіть екземпляр бота
bot = Bot(token=API_TOKEN)
dp = Dispatcher()  # Використовуйте Dispatcher

# Налаштування планувальника APScheduler
scheduler = AsyncIOScheduler()

# Функція, яка виконується за розкладом
async def send_reminder(chat_id):
    logging.info("Надсилаємо нагадування")
    await bot.send_message(chat_id, "Це ваше нагадування!")

# Команда для зміни часу нагадувань
@dp.message(Command("settime"))  # Використовуйте Command для фільтрації
async def set_time(message: types.Message):
    user_id = message.from_user.id
    await message.answer("Введіть новий час для ранкових та вечірніх нагадувань у форматі HH:MM для кожного.")
    # Додайте логіку для збереження нового часу у user_reminders

# Запитання для ранкових та вечірніх нагадувань
async def send_morning_question(user_id):
    questions = [
        "Що в моєму нинішньому житті дає мені відчуття радості?",
        "Що в моєму житті приємно розбурхує мене?",
        "Чим я пишаюся?"
    ]
    await bot.send_message(user_id, questions[0])  # Можна рандомізувати запитання

async def send_evening_question(user_id):
    questions = [
        "Що в цьому дні було добре?",
        "Чому я сьогодні навчився?",
        "Як я можу використати уроки сьогодні?"
    ]
    await bot.send_message(user_id, questions[0])  # Можна рандомізувати запитання

# Функція для збереження відповідей у базі даних
def save_answer(user_id, question_type, question, answer):
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO answers (user_id, question_type, question, answer) VALUES (?, ?, ?, ?)', 
                   (user_id, question_type, question, answer))
    conn.commit()
    conn.close()

@dp.message(Command("start"))  # Використовуйте Command для фільтрації
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    await message.answer(
        "Привіт! Налаштуйте час для отримання ранкових та вечірніх питань.\n"
        "Поточний час: Ранкові — 09:00, Вечірні — 21:00. "
        "Використовуйте команду /settime для зміни."
    )
    # Налаштування початкових нагадувань
    set_reminders(user_id, '09:00', '21:00')

# Функція для налаштування нагадувань
# def set_reminders(user_id, morning_time, evening_time):
#     # Видалити попередні нагадування для цього користувача
#     scheduler.remove_job(f'morning_{user_id}', jobstore='default')
#     scheduler.remove_job(f'evening_{user_id}', jobstore='default')

#     # Налаштування ранкового нагадування
#     scheduler.add_job(
#         lambda: send_morning_question(user_id),
#         CronTrigger.from_crontab(morning_time),
#         id=f'morning_{user_id}',
#         replace_existing=True
#     )

#     # Налаштування вечірнього нагадування
#     scheduler.add_job(
#         lambda: send_evening_question(user_id),
#         CronTrigger.from_crontab(evening_time),
#         id=f'evening_{user_id}',
#         replace_existing=True
#     )
def set_reminders(user_id, morning_time, evening_time):
    try:
        scheduler.remove_job(f'morning_{user_id}', jobstore='default')
    except JobLookupError:
        logging.info(f"Завдання з ID morning_{user_id} не існує, пропускаємо видалення.")
    
    try:
        scheduler.remove_job(f'evening_{user_id}', jobstore='default')
    except JobLookupError:
        logging.info(f"Завдання з ID evening_{user_id} не існує, пропускаємо видалення.")

        # Хендлер для команди /start
@router.message(commands=['start'])
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    await message.answer("Привіт! Я ваш бот для нагадувань.")
    set_reminders(user_id, '09:00', '21:00')

# Хендлер для команди /settime
@router.message(commands=['settime'])
async def set_time_handler(message: types.Message):
    await message.answer("Будь ласка, введіть час для нагадувань у форматі HH:MM для ранкових і вечірніх запитів.")

# Хендлер для команди /summary
@router.message(commands=['summary'])
async def summary_handler(message: types.Message):
    # Вставте тут код для зведення відповідей користувача
    await message.answer("Ось ваш підсумок відповідей за сьогодні.")

# Хендлер для команди /viewanswers
@router.message(commands=['viewanswers'])
async def view_answers_handler(message: types.Message):
    # Вставте логіку для перегляду відповідей
    await message.answer("Ось ваші відповіді на запитання.")

    
    # Додаємо нові завдання
    scheduler.add_job(
        send_morning_question, 
        trigger='cron', 
        hour=morning_time.split(':')[0], 
        minute=morning_time.split(':')[1], 
        id=f'morning_{user_id}',
        replace_existing=True, 
        args=[user_id]
    )

    scheduler.add_job(
        send_evening_question, 
        trigger='cron', 
        hour=evening_time.split(':')[0], 
        minute=evening_time.split(':')[1], 
        id=f'evening_{user_id}',
        replace_existing=True, 
        args=[user_id]
    )
    logging.info(f"Нагадування для користувача {user_id} оновлено: Ранок — {morning_time}, Вечір — {evening_time}")


@dp.message()  # Усі повідомлення
async def handle_answer(message: types.Message):
    user_id = message.from_user.id
    text = message.text
    # Збереження відповіді
    save_answer(user_id, 'morning', 'Що в моєму нинішньому житті дає мені відчуття радості?', text)
    await message.answer("Ваша відповідь збережена!")

@dp.message(Command("summary"))  # Використовуйте Command для фільтрації
async def send_summary(message: types.Message):
    user_id = message.from_user.id
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT question, answer, answer_time FROM answers WHERE user_id = ? AND answer_time >= datetime("now", "-7 days")', (user_id,))
    results = cursor.fetchall()
    
    summary = "Ваші відповіді за останні 7 днів:\n\n"
    for question, answer, answer_time in results:
        summary += f"Дата: {answer_time}\nПитання: {question}\nВідповідь: {answer}\n\n"
    
    await message.answer(summary)
    conn.close()

# Функція для запуску планувальника
async def scheduler_task():
    scheduler.start()
    logging.info("Планувальник запущено")

# Функція для запуску бота
async def main():
    asyncio.create_task(scheduler_task())  # Запуск планувальника
    await dp.start_polling(bot)  # Запуск хендлерів

if __name__ == '__main__':
    logging.info("Запуск бота...")
    asyncio.run(main())
