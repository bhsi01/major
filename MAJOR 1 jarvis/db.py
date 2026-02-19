import sqlite3
from datetime import datetime

conn = sqlite3.connect("chats.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS chats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_number INTEGER,
    created_at TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER,
    role TEXT,
    content TEXT
)
""")

conn.commit()

def get_next_chat_number():
    cur.execute("SELECT MAX(chat_number) FROM chats")
    res = cur.fetchone()[0]
    return (res or 0) + 1

def create_chat():
    num = get_next_chat_number()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("INSERT INTO chats (chat_number, created_at) VALUES (?, ?)", (num, ts))
    conn.commit()
    return cur.lastrowid, num, ts

def get_chats():
    cur.execute("SELECT id, chat_number, created_at FROM chats ORDER BY id DESC")
    return cur.fetchall()

def save_message(chat_id, role, content):
    cur.execute(
        "INSERT INTO messages (chat_id, role, content) VALUES (?, ?, ?)",
        (chat_id, role, content)
    )
    conn.commit()

def load_messages(chat_id):
    cur.execute(
        "SELECT role, content FROM messages WHERE chat_id=? ORDER BY id",
        (chat_id,)
    )
    return cur.fetchall()
