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

def update_database():
    try:
        # Подключение к базе данных
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # Выполнение ALTER TABLE
        cursor.execute("""
            ALTER TABLE ad_users 
            ADD COLUMN interface_version TEXT DEFAULT '1.0';
        """)
        conn.commit()
        print("Столбец interface_version успешно добавлен.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Столбец interface_version уже существует.")
        else:
            print(f"Ошибка при обновлении базы данных: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    update_database()