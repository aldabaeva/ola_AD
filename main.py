import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime
import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# Конфигурация
from config import BOT_TOKEN, DB_NAME

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Класс для хранения состояния FSM
class PressureStates(StatesGroup):
    waiting_for_systolic = State()
    waiting_for_diastolic = State()
    waiting_for_pulse = State()
    waiting_for_comment = State()

# Старт / регистрация
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM ad_users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        builder = ReplyKeyboardBuilder()
        builder.add(KeyboardButton(text="📱 Отправить номер", request_contact=True))
        await message.answer(
            "👋 Добро пожаловать! Для регистрации отправьте ваш номер телефона:",
            reply_markup=builder.as_markup(resize_keyboard=True)
        )
    else:
        await show_main_menu(message)

    conn.close()

# Приём контакта
@dp.message(F.contact)
async def handle_contact(message: Message):
    user_id = message.from_user.id
    phone = message.contact.phone_number

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT OR IGNORE INTO ad_users (user_id, phone) VALUES (?, ?)",
        (user_id, phone)
    )
    conn.commit()
    conn.close()

    await message.answer("✅ Регистрация прошла успешно!")
    await show_main_menu(message)

# Главное меню
async def show_main_menu(message: Message):
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="➕ Добавить запись"))
    builder.row(
        KeyboardButton(text="📋 Последние записи"),
        KeyboardButton(text="📈 График давления")
    )
    builder.row(
        KeyboardButton(text="📤 Экспорт в Excel"),
        KeyboardButton(text="🔒 Выход")
    )

    await message.answer("📊 Выберите действие:", reply_markup=builder.as_markup(resize_keyboard=True))

# Добавление записи
@dp.message(F.text == "➕ Добавить запись")
async def cmd_add_record(message: Message, state: FSMContext):
    await state.set_state(PressureStates.waiting_for_systolic)
    await message.answer("Введите верхнее давление (систолическое):")

@dp.message(PressureStates.waiting_for_systolic)
async def process_systolic(message: Message, state: FSMContext):
    try:
        systolic = int(message.text)
        await state.update_data(systolic=systolic)
        await state.set_state(PressureStates.waiting_for_diastolic)
        await message.answer("Введите нижнее давление (диастолическое):")
    except ValueError:
        await message.answer("❌ Введите число!")

@dp.message(PressureStates.waiting_for_diastolic)
async def process_diastolic(message: Message, state: FSMContext):
    try:
        diastolic = int(message.text)
        await state.update_data(diastolic=diastolic)
        await state.set_state(PressureStates.waiting_for_pulse)
        await message.answer("Введите пульс:")
    except ValueError:
        await message.answer("❌ Введите число!")

@dp.message(PressureStates.waiting_for_pulse)
async def process_pulse(message: Message, state: FSMContext):
    try:
        pulse = int(message.text)
        await state.update_data(pulse=pulse)
        await state.set_state(PressureStates.waiting_for_comment)
        await message.answer("Добавьте комментарий (или напишите /skip):")
    except ValueError:
        await message.answer("❌ Введите число!")

@dp.message(PressureStates.waiting_for_comment)
async def process_comment(message: Message, state: FSMContext):
    data = await state.get_data()
    comment = message.text if message.text != "/skip" else None

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO ad_pressure_measurements (user_id, systolic, diastolic, pulse, comment1) VALUES (?, ?, ?, ?, ?)",
        (message.from_user.id, data['systolic'], data['diastolic'], data['pulse'], comment)
    )
    conn.commit()
    conn.close()

    await state.clear()
    await message.answer("✅ Запись успешно сохранена!")
    await show_main_menu(message)

# Последние записи
@dp.message(F.text == "📋 Последние записи")
async def cmd_list_records(message: Message):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT systolic, diastolic, pulse, comment1, timestamp FROM ad_pressure_measurements WHERE user_id = ? ORDER BY timestamp DESC LIMIT 10",
        (message.from_user.id,)
    )
    records = cursor.fetchall()
    conn.close()

    if not records:
        await message.answer("📭 У вас пока нет записей.")
        return

    response = "📋 Последние 10 записей:\n\n"
    for record in records:
        systolic, diastolic, pulse, comment, timestamp = record
        response += (
            f"🕒 {timestamp}\n"
            f"🔺 {systolic} / 🔻 {diastolic}\n"
            f"💓 Пульс: {pulse}\n"
            f"📝 Комментарий: {comment if comment else '—'}\n\n"
        )

    await message.answer(response)

# График давления
@dp.message(F.text == "📈 График давления")
async def cmd_graph(message: Message):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT timestamp, systolic, diastolic, pulse FROM ad_pressure_measurements WHERE user_id = ? ORDER BY timestamp",
        (message.from_user.id,)
    )
    records = cursor.fetchall()
    conn.close()

    if not records:
        await message.answer("📭 У вас пока нет записей.")
        return

    dates = [datetime.strptime(record[0], "%Y-%m-%d %H:%M:%S") for record in records]
    systolic = [record[1] for record in records]
    diastolic = [record[2] for record in records]
    pulse = [record[3] for record in records]

    plt.figure(figsize=(10, 6))
    plt.plot(dates, systolic, label="Верхнее (сист.)", marker="o")
    plt.plot(dates, diastolic, label="Нижнее (диаст.)", marker="o")
    plt.plot(dates, pulse, label="Пульс", linestyle="--", marker="x")
    plt.xlabel("Дата")
    plt.ylabel("Значение")
    plt.title("Динамика давления и пульса")
    plt.legend()
    plt.grid(True)

    graph_file = "pressure_graph.png"
    plt.savefig(graph_file)
    await message.answer_photo(photo=open(graph_file, "rb"), caption="📈 Ваша динамика давления и пульса")
    os.remove(graph_file)

# Экспорт в Excel
@dp.message(F.text == "📤 Экспорт в Excel")
async def cmd_export_excel(message: Message):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT timestamp, systolic, diastolic, pulse, comment1 FROM ad_pressure_measurements WHERE user_id = ?",
        (message.from_user.id,)
    )
    records = cursor.fetchall()
    conn.close()

    if not records:
        await message.answer("📭 У вас пока нет записей.")
        return

    df = pd.DataFrame(
        records,
        columns=["Дата", "Верхнее", "Нижнее", "Пульс", "Комментарий"]
    )
    excel_file = "pressure_data.xlsx"
    df.to_excel(excel_file, index=False)

    await message.answer_document(open(excel_file, "rb"), caption="📊 Ваши данные в Excel")
    os.remove(excel_file)

# Выход
@dp.message(F.text == "🔒 Выход")
async def cmd_logout(message: Message):
    await message.answer("🔒 Вы вышли из аккаунта.")

# Запуск бота
async def main():
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
