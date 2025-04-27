import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime
import asyncio
import logging
from aiogram.exceptions import TelegramConflictError
from io import BytesIO
from aiogram.types import BufferedInputFile
from importlib.metadata import version as package_version, PackageNotFoundError
import sys

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# Конфигурация
from config import BOT_TOKEN, DB_NAME

# Вывод версий пакетов
def print_versions():
    packages = ['aiogram', 'pandas', 'matplotlib', 'sqlite3']
    print("====================================")
    print("\n--- Версии используемых пакетов ---")
    
    for pkg in packages:
        try:
            if pkg == 'sqlite3':
                print(f"sqlite3: {sqlite3.sqlite_version} (системная)")
            else:
                ver = package_version(pkg)
                print(f"{pkg}: {ver}")
        except PackageNotFoundError:
            print(f"{pkg}: не установлен")
    
    print(f"Python: {sys.version.split()[0]}")
    print("====================================\n")

print_versions()

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
    builder.row(KeyboardButton(text="💚 Добавить запись"))
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
@dp.message(F.text == "💚 Добавить запись")
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

# Переход к шагу ввода комментария
@dp.message(PressureStates.waiting_for_pulse)
async def process_pulse(message: Message, state: FSMContext):
    try:
        pulse = int(message.text)
        await state.update_data(pulse=pulse)

        # Создаем клавиатуру с кнопкой "Не заполнять комментарий"
        builder = ReplyKeyboardBuilder()
        builder.add(KeyboardButton(text="Не заполнять комментарий"))
        builder.adjust(1)  # Кнопка будет одна в строке

        await state.set_state(PressureStates.waiting_for_comment)
        await message.answer(
            "Добавьте комментарий (или нажмите кнопку ниже):",
            reply_markup=builder.as_markup(resize_keyboard=True)
        )
    except ValueError:
        await message.answer("❌ Введите число!")

@dp.message(PressureStates.waiting_for_comment)
async def process_comment(message: Message, state: FSMContext):
    # Создаем клавиатуру с кнопкой "Не заполнять комментарий"
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="Не заполнять комментарий"))
    builder.adjust(1)  # Кнопка будет одна в строке

    # Если пользователь нажал кнопку "Не заполнять комментарий"
    if message.text == "Не заполнять комментарий":
        comment = None
    else:
        comment = message.text

    # Получаем данные из FSM
    data = await state.get_data()

    # Сохраняем данные в базу данных
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO ad_pressure_measurements (user_id, systolic, diastolic, pulse, comment1) VALUES (?, ?, ?, ?, ?)",
        (message.from_user.id, data['systolic'], data['diastolic'], data['pulse'], comment)
    )
    conn.commit()
    conn.close()

    # Очищаем состояние и показываем главное меню
    await state.clear()
    await message.answer(
        "✅ Запись успешно сохранена!",
        reply_markup=ReplyKeyboardRemove()  # Убираем клавиатуру
    )
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
            f"{systolic} / {diastolic}\n"
            f"Пульс: {pulse}\n"
            f"Комментарий: {comment if comment else '—'}\n\n"
        )

    await message.answer(response)

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

    # Форматируем даты для графика
    dates = [datetime.strptime(record[0], "%Y-%m-%d %H:%M:%S") for record in records]
    formatted_dates = [dt.strftime("%d.%m.%Y %H:%M") for dt in dates]
    
    systolic = [record[1] for record in records]
    diastolic = [record[2] for record in records]
    pulse = [record[3] for record in records]

    plt.figure(figsize=(12, 7))
    plt.plot(formatted_dates, systolic, label="Верхнее (сист.)", marker="o")
    plt.plot(formatted_dates, diastolic, label="Нижнее (диаст.)", marker="o")
    plt.plot(formatted_dates, pulse, label="Пульс", linestyle="--", marker="x")
    plt.xlabel("Дата и время", fontsize=12)
    plt.ylabel("Значение", fontsize=12)
    plt.title("Динамика давления и пульса", fontsize=14)
    plt.legend(fontsize=10)
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()

    img_buffer = BytesIO()
    plt.savefig(img_buffer, format="png", dpi=300, bbox_inches="tight")
    img_buffer.seek(0)
    plt.close()

    photo = BufferedInputFile(img_buffer.getvalue(), filename="pressure_graph.png")
    await message.answer_photo(photo, caption="📈 Ваша динамика давления и пульса")

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

    # Форматируем даты для Excel
    formatted_records = []
    for record in records:
        dt = datetime.strptime(record[0], "%Y-%m-%d %H:%M:%S")
        formatted_date = dt.strftime("%d.%m.%Y %H:%M")
        formatted_records.append((formatted_date, *record[1:]))

    df = pd.DataFrame(
        formatted_records,
        columns=["Дата и время", "Верхнее", "Нижнее", "Пульс", "Комментарий"]
    )

    # Создаем имя файла с текущей датой и временем
    current_time = datetime.now().strftime("%d_%m_%Y_%H_%M")
    filename = f"pressure_data_{current_time}.xlsx"
    
    bio = BytesIO()
    with pd.ExcelWriter(bio, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
        
        # Получаем объект листа для настройки
        worksheet = writer.sheets['Sheet1']
        
        # Устанавливаем ширину столбцов
        worksheet.column_dimensions['A'].width = 20  # Дата и время
        worksheet.column_dimensions['B'].width = 10  # Верхнее
        worksheet.column_dimensions['C'].width = 10  # Нижнее
        worksheet.column_dimensions['D'].width = 10  # Пульс
        worksheet.column_dimensions['E'].width = 30  # Комментарий
    
    bio.seek(0)

    document = BufferedInputFile(bio.getvalue(), filename=filename)
    await message.answer_document(document, caption=f"📊 Ваши данные в Excel ({current_time.replace('_', '.')})")

# Выход
@dp.message(F.text == "🔒 Выход")
async def cmd_logout(message: Message):
    await message.answer("🔒 Вы вышли из аккаунта.")

# Включаем логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

async def main():
    try:
        logging.info("Бот запускается...")
        await dp.start_polling(bot)
    except TelegramConflictError:
        logging.error("❌ Конфликт с другим экземпляром бота! Завершите другие процессы.")
    except Exception as e:
        logging.exception(f"❌ Неожиданная ошибка: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("🛑 Бот остановлен вручную.")