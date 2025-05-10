import sqlite3
import os
import logging
from db_config import DB_NAME

# Настройка логгера
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/init.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def check_and_create_tables():
    logging.info("Проверка базы данных: %s", DB_NAME)

    if not os.path.exists(DB_NAME):
        logging.info("Файл базы данных не найден. Создаю: %s", DB_NAME)
        conn = sqlite3.connect(DB_NAME)
        conn.close()

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # ad_users
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ad_users';")
    if cursor.fetchone() is None:
        logging.info("Создаю таблицу ad_users")
        cursor.execute("""
            CREATE TABLE ad_users (
                user_id INTEGER PRIMARY KEY,
                phone TEXT NOT NULL,
                interface_version TEXT DEFAULT '1.0',
                created_dt TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)

    # ad_pressure_measurements
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ad_pressure_measurements';")
    if cursor.fetchone() is None:
        logging.info("Создаю таблицу ad_pressure_measurements")
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
    logging.info("Проверка завершена. База данных готова.")
