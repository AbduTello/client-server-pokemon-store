import sqlite3
from constants import DB_PATH, INITIAL_BALANCE

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor() # cursor to run cmds

  # Create Users table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Users (
        ID INTEGER PRIMARY KEY,
        first_name TEXT,
        last_name TEXT,
        user_name TEXT NOT NULL,
        password TEXT,
        email TEXT NOT NULL,
        usd_balance DOUBLE NOT NULL,
        is_root INTEGER NOT NULL DEFAULT 0
    )
    """)

    # Create Pokemon_cards table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Pokemon_cards (
        ID INTEGER PRIMARY KEY,
        card_name TEXT NOT NULL,
        card_type TEXT NOT NULL,
        rarity TEXT NOT NULL,
        count INTEGER,
        owner_id INTEGER,
        FOREIGN KEY(owner_id) REFERENCES Users(ID)
    )
    """)
    
    conn.commit() # save changes
    return conn

def ensure_seed_user(conn):
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM Users")
    count = cur.fetchone()[0]
    if count == 0:
        cur.execute(
            "INSERT INTO Users (user_name, usd_balance, is_root) VALUES (?, ?, ?)",
            ("default_user", INITIAL_BALANCE, 1)
        )
        conn.commit()
