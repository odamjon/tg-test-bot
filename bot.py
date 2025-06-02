import asyncio
import random
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.enums import ParseMode
from aiogram.utils.keyboard import ReplyKeyboardBuilder
import os

API_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# Хранилище тестов и ответов
tests = {}  # test_code -> correct_answers
submissions = {}  # test_code -> list of (user_id, name, user_answers, correct_count)
participants = {}  # user_id -> name

OWNER_ID = os.getenv("OWNER_ID")

# Кнопки
start_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Проверить тест")],
        [KeyboardButton(text="Связаться с админом")]
    ],
    resize_keyboard=True
)

@dp.message(commands=["start"])
async def start(message: types.Message):
    await message.answer("Добро пожаловать! Введите своё имя:", reply_markup=types.ReplyKeyboardRemove())

@dp.message(lambda m: m.text and m.text.lower() not in ["проверить тест", "связаться с админом"])
async def set_name_or_check(message: types.Message):
    if message.from_user.id not in participants:
        participants[message.from_user.id] = message.text.strip()
        await message.answer("Имя сохранено. Выберите действие:", reply_markup=start_keyboard)
        return

    # Проверка теста
    if '+' not in message.text:
        await message.answer("Пожалуйста, используйте формат: КОД+ответы (например: 123456+1a2b3c...)")
        return

    code, user_answers = message.text.strip().split("+", 1)
    correct_answers = tests.get(code)

    if not correct_answers:
        await message.answer("Такого кода не существует.")
        return

    correct = sum(1 for a, b in zip(correct_answers.lower(), user_answers.lower()) if a == b)
    total = len(correct_answers)

    submissions.setdefault(code, []).append((
        message.from_user.id,
        participants[message.from_user.id],
        user_answers,
        correct
    ))

    await message.answer(f"Результат: {correct}/{total} правильных ответов.")

@dp.message(lambda m: m.text == "Связаться с админом")
async def contact_admin(message: types.Message):
    await message.answer("Напишите администратору напрямую: @your_username")

@dp.message(lambda m: m.text == "Проверить тест")
async def prompt_test(message: types.Message):
    await message.answer("Введите код и ваши ответы в формате:\n<код>+<ответы>")

@dp.message(commands=["create_test"])
async def create_test(message: types.Message):
    if str(message.from_user.id) != OWNER_ID:
        await message.answer("Эта команда только для владельца.")
        return
    await message.answer("Отправьте правильные ответы в одном сообщении:")

@dp.message(lambda m: str(m.from_user.id) == OWNER_ID and m.text and len(m.text) >= 3)
async def receive_answers(message: types.Message):
    correct_answers = ''.join(message.text.strip().split()).lower()
    code = str(random.randint(100000, 999999))
    while code in tests:
        code = str(random.randint(100000, 999999))
    tests[code] = correct_answers
    await message.answer(f"Тест сохранён. Код для участников: <b>{code}</b>")

@dp.message(commands=["results"])
async def show_results(message: types.Message):
    if str(message.from_user.id) != OWNER_ID:
        await message.answer("Эта команда только для владельца.")
        return
    text = ""
    for code, results in submissions.items():
        text += f"\nКод: {code}\n"
        for uid, name, ans, correct in results:
            text += f"{name}: {correct} правильных\n"
    await message.answer(text or "Нет данных.")

@dp.message(commands=["participants"])
async def list_participants(message: types.Message):
    if str(message.from_user.id) != OWNER_ID:
        await message.answer("Эта команда только для владельца.")
        return
    text = "\n".join(participants.values()) or "Нет участников."
    await message.answer(text)
@dp.message(commands=["end_test"])
async def end_test(message: types.Message):
    if str(message.from_user.id) != OWNER_ID:
        await message.answer("Эта команда только для владельца.")
        return
    tests.clear()
    submissions.clear()
    await message.answer("Все тесты сброшены.")

async def main():
    await dp.start_polling(bot)

if name == "main":
    asyncio.run(main())
