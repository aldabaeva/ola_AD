import sqlite3
import sys
import os

# Добавляем путь к корневой директории проекта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Импортируем конфигурацию из корня проекта
try:
    from config import DB_NAME
except ImportError:
    print("Ошибка: файл config.py не найден или не содержит DB_NAME.")
    sys.exit(1)

# Проверка существования файла базы данных
if not os.path.exists(DB_NAME):
    print(f"База данных {DB_NAME} не найдена. Создаю новую...")
    conn = sqlite3.connect(DB_NAME)  # Создаем файл в корне проекта
    conn.close()

# Проверка существования таблиц
def check_and_create_tables():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Проверка таблицы ad_users
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ad_users';")
    users_table_exists = cursor.fetchone() is not None

    if not users_table_exists:
        print("Создаю таблицу ad_users...")
        cursor.execute("""
            CREATE TABLE ad_users (
                user_id INTEGER PRIMARY KEY,
                phone TEXT NOT NULL,
                interface_version TEXT DEFAULT '1.0',
                created_dt TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)

    # Проверка таблицы ad_pressure_measurements
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ad_pressure_measurements';")
    measurements_table_exists = cursor.fetchone() is not None

    if not measurements_table_exists:
        print("Создаю таблицу ad_pressure_measurements...")
        cursor.execute("""
            CREATE TABLE ad_pressure_measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                systolic INTEGER NOT NULL,
                diastolic INTEGER NOT NULL,
                pulse INTEGER NOT NULL,
                comment1 TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)

    conn.commit()
    conn.close()

# Вызов функции проверки и создания таблиц
check_and_create_tables()
print("Проверка завершена. База данных готова к работе.")