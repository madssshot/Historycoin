import sqlite3
import os

DB_PATH = "numizmat.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        tg_id INTEGER UNIQUE NOT NULL,
        username TEXT,
        full_name TEXT,
        score INTEGER DEFAULT 0,
        rank TEXT DEFAULT "Новичок",
        collection TEXT DEFAULT "[]",
        registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS auction_lots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        seller_tg_id INTEGER NOT NULL,
        seller_name TEXT,
        title TEXT NOT NULL,
        description TEXT,
        period TEXT,
        year TEXT,
        material TEXT,
        price TEXT,
        photo_path TEXT,
        status TEXT DEFAULT "active",
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS period_texts (
        id INTEGER PRIMARY KEY,
        period_key TEXT UNIQUE NOT NULL,
        overview TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    conn.commit()
    conn.close()


def upsert_user(tg_id, username, full_name):
    conn = get_conn()
    c = conn.cursor()
    c.execute('''INSERT INTO users (tg_id, username, full_name)
                 VALUES (?, ?, ?)
                 ON CONFLICT(tg_id) DO UPDATE SET
                   username=excluded.username,
                   full_name=excluded.full_name''',
              (tg_id, username, full_name))
    conn.commit()
    conn.close()


def get_user(tg_id):
    conn = get_conn()
    c = conn.cursor()
    row = c.execute('SELECT * FROM users WHERE tg_id=?', (tg_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_user_score(tg_id, delta):
    conn = get_conn()
    c = conn.cursor()
    c.execute('UPDATE users SET score = score + ? WHERE tg_id=?', (delta, tg_id))
    conn.commit()
    conn.close()


def get_auction_lots(status="active"):
    conn = get_conn()
    c = conn.cursor()
    rows = c.execute('SELECT * FROM auction_lots WHERE status=? ORDER BY created_at DESC', (status,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_auction_lot(seller_tg_id, seller_name, title, description, period, year, material, price, photo_path):
    conn = get_conn()
    c = conn.cursor()
    c.execute('''INSERT INTO auction_lots
                 (seller_tg_id, seller_name, title, description, period, year, material, price, photo_path)
                 VALUES (?,?,?,?,?,?,?,?,?)''',
              (seller_tg_id, seller_name, title, description, period, year, material, price, photo_path))
    lot_id = c.lastrowid
    conn.commit()
    conn.close()
    return lot_id


def delete_lot(lot_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute('UPDATE auction_lots SET status="deleted" WHERE id=?', (lot_id,))
    conn.commit()
    conn.close()


def get_all_users():
    conn = get_conn()
    c = conn.cursor()
    rows = c.execute('SELECT * FROM users ORDER BY score DESC').fetchall()
    conn.close()
    return [dict(r) for r in rows]


init_db()