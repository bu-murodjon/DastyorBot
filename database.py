import sqlite3

# =========================
# DATABASE ULASH
# =========================

db = sqlite3.connect("dastyor.db")

cursor = db.cursor()

# =========================
# BUYURTMALAR
# =========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    full_name TEXT,
    username TEXT,
    phone TEXT,
    order_text TEXT,
    location TEXT,           
    latitude TEXT,
    longitude TEXT,
    status TEXT,
    courier TEXT
)
""")

# =========================
# SAVOLLAR
# =========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    full_name TEXT,
    username TEXT,
    question TEXT
)
""")

db.commit()