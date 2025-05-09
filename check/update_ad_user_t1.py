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

        # Сначала добавляем столбец без DEFAULT
        cursor.execute("""
            ALTER TABLE ad_users 
            ADD COLUMN created_dt TIMESTAMP;
        """)
        
        # Затем обновляем существующие записи
        cursor.execute("""
            UPDATE ad_users 
            SET created_dt = CURRENT_TIMESTAMP 
            WHERE created_dt IS NULL;
        """)
        
        # Для новых записей можно установить DEFAULT через триггер
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS set_ad_users_created_dt
            AFTER INSERT ON ad_users
            FOR EACH ROW
            BEGIN
                UPDATE ad_users 
                SET created_dt = CURRENT_TIMESTAMP 
                WHERE rowid = NEW.rowid;
            END;
        """)
        
        conn.commit()
        print("Столбец created_dt успешно добавлен и настроен.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Столбец created_dt уже существует.")
        else:
            print(f"Ошибка при обновлении базы данных: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    update_database()