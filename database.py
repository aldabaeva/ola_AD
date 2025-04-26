import sqlite3

def init_db():
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()

    # Таблица пользователей
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ad_users (
        user_id INTEGER PRIMARY KEY,
        phone TEXT UNIQUE,
        registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Таблица измерений давления
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ad_pressure_measurements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        systolic INTEGER,
        diastolic INTEGER,
        pulse INTEGER,
        comment1 TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES ad_users(user_id)
    )
    ''')

    conn.commit()
    conn.close()

# Проверяем, что БД создана
init_db()