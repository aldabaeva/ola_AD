# database/db_operations.py

import sqlite3
from datetime import datetime

DB_NAME = "data.db"

def get_user(user_id):
    """
    Получает данные пользователя из базы данных.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ad_users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user


def register_user(user_id, phone=None):
    """
    Регистрирует нового пользователя в базе данных.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO ad_users (user_id, phone) VALUES (?, ?)",
        (user_id, phone)
    )
    conn.commit()
    conn.close()


def save_pressure_record(user_id, systolic, diastolic, pulse, comment=None):
    """
    Сохраняет новую запись давления в базу данных.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO ad_pressure_measurements (user_id, systolic, diastolic, pulse, comment1, timestamp) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, systolic, diastolic, pulse, comment, timestamp)
    )
    conn.commit()
    conn.close()


def get_user_records(user_id, limit=10):
    """
    Получает последние записи пользователя из базы данных.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT systolic, diastolic, pulse, comment1, timestamp FROM ad_pressure_measurements "
        "WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
        (user_id, limit)
    )
    records = cursor.fetchall()
    conn.close()
    return records


def update_user_data(user_id, **kwargs):
    """
    Обновляет данные пользователя в базе данных.
    Пример: update_user_data(user_id, interface_version="1.1.1")
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    for key, value in kwargs.items():
        cursor.execute(f"UPDATE ad_users SET {key} = ? WHERE user_id = ?", (value, user_id))
    conn.commit()
    conn.close()