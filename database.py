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

def upsert_user(user_id, username=""):
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO users (user_id) VALUES (?)
    ''', (user_id,))
    conn.commit()
    conn.close()

def create_order(owner_id, recipient_id, nft_link, price):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER,
            recipient_id INTEGER,
            nft_link TEXT,
            price INTEGER,
            status TEXT DEFAULT 'pending'
        )
    ''')
    cursor.execute('''
        INSERT INTO orders (owner_id, recipient_id, nft_link, price)
        VALUES (?, ?, ?, ?)
    ''', (owner_id, recipient_id, nft_link, price))
    conn.commit()
    order_id = cursor.lastrowid
    conn.close()
    return order_id
    

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

def list_users(*args, **kwargs):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    conn.close()
    return []
    
