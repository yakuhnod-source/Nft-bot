import sqlite3

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY
        )
    ''')
    conn.commit()
    conn.close()

def upsert_user(user_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO users (user_id) VALUES (?)
    ''', (user_id,))
    conn.commit()
    conn.close()

def create_order(*args, **kwargs):
    # Функция для создания заказа (если аргументы специфичны, можно дополнить)
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    # Базовая заглушка, чтобы бот не падал при импорте
    conn.commit()
    conn.close()
    
    
  
