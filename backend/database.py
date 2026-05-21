import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'medical_leave.db')

def get_db():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            full_name TEXT,
            points INTEGER DEFAULT 5,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leaves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name_ar TEXT,
            name_en TEXT,
            national_id TEXT,
            hospital TEXT,
            doctor_ar TEXT,
            doctor_en TEXT,
            date_g TEXT,
            date_h TEXT,
            pdf_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ قاعدة البيانات جاهزة")

def get_user(telegram_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return {"id": user[0], "telegram_id": user[1], "full_name": user[2], "points": user[3]}
    return None

def create_user(telegram_id, full_name):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (telegram_id, full_name) VALUES (?, ?)", (telegram_id, full_name))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return {"id": user_id, "telegram_id": telegram_id, "full_name": full_name, "points": 5}
    except:
        conn.close()
        return None

def deduct_points(telegram_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET points = points - 1 WHERE telegram_id = ? AND points > 0", (telegram_id,))
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0

def get_points(telegram_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT points FROM users WHERE telegram_id = ?", (telegram_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

def save_leave(user_id, data, pdf_path):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO leaves (user_id, name_ar, name_en, national_id, hospital, doctor_ar, doctor_en, date_g, date_h, pdf_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, data['name_ar'], data['name_en'], data['national_id'], data['hospital'], 
          data['doctor_ar'], data['doctor_en'], data['date_g'], data['date_h'], pdf_path))
    conn.commit()
    conn.close()

init_db()