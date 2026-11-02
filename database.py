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
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    conn.commit()
    conn.close()

def get_order(*args, **kwargs):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    conn.close()
    return None

def set_order_status(*args, **kwargs):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    conn.commit()
    conn.close()

def set_subscription(*args, **kwargs):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    conn.commit()
    conn.close()

def get_subscription(*args, **kwargs):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    conn.close()
    return None
    
