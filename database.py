# database.py
import sqlite3
import os

DB_PATH = os.path.join('data', 'orders.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Таблицы, которые уже существовали
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT UNIQUE NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            total_price REAL,
            status TEXT DEFAULT 'Ожидание принятия',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            cooking_started_at DATETIME,
            cooking_ends_at DATETIME,
            cancel_reason TEXT,
            details TEXT,
            FOREIGN KEY(client_id) REFERENCES clients(id)
        )
    ''')
    
    # Новые таблицы для управления ингредиентами
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            quantity INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pizza_ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pizza_name TEXT NOT NULL,
            ingredient_id INTEGER,
            required_quantity INTEGER NOT NULL,
            FOREIGN KEY(ingredient_id) REFERENCES ingredients(id)
        )
    ''')

    conn.commit()
    conn.close()

def get_connection():
    return sqlite3.connect(DB_PATH)