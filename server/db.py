import sqlite3
from constants import DB_PATH, INITIAL_BALANCE

def init_db(path: str = DB_PATH) -> sqlite3.Connection:
    """
    Open/create the DB, ensure schema exists, and seed one default user if none.
    """
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    with conn:
        conn.execute("PRAGMA foreign_keys = ON;")

        # Users table
        conn.execute("""
        CREATE TABLE IF NOT EXISTS Users (
            ID INTEGER PRIMARY KEY,
            first_name  TEXT,
            last_name   TEXT,
            user_name   TEXT NOT NULL,
            password    TEXT,
            usd_balance DOUBLE NOT NULL,
            is_root     INTEGER NOT NULL DEFAULT 0
        );
        """)

        # Pokemon cards table
        conn.execute("""
        CREATE TABLE IF NOT EXISTS Pokemon_cards (
            ID        INTEGER PRIMARY KEY,
            card_name TEXT NOT NULL,
            card_type TEXT NOT NULL,
            rarity    TEXT NOT NULL,
            count     INTEGER,
            owner_id  INTEGER,
            FOREIGN KEY (owner_id) REFERENCES Users(ID)
        );
        """)

        # Seed a single default user if table is empty
        cur = conn.execute("SELECT COUNT(*) AS c FROM Users;")
        if cur.fetchone()["c"] == 0:
            conn.execute(
                "INSERT INTO Users (first_name,last_name,user_name,password,usd_balance,is_root) "
                "VALUES (?,?,?,?,?,?)",
                (None, None, "seed_user", None, float(INITIAL_BALANCE), 1),
            )
    return conn

# READ HELPER FUNCTIONS

def get_user_balance(conn: sqlite3.Connection, owner_id: int):
    """
    Returns (balance, first_name, last_name, user_name). Raises ValueError if user not found.
    """
    row = conn.execute(
        "SELECT usd_balance, first_name, last_name, user_name FROM Users WHERE ID=?;",
        (owner_id,),
    ).fetchone()
    if not row:
        raise ValueError(f"user {owner_id} doesn't exist")
    return float(row["usd_balance"]), row["first_name"], row["last_name"], row["user_name"]

def list_user_cards(conn: sqlite3.Connection, owner_id: int):
    """
    Returns a list of dicts with keys: ID, card_name, card_type, rarity, count, owner_id.
    """
    cur = conn.execute(
        "SELECT ID, card_name, card_type, rarity, count, owner_id "
        "FROM Pokemon_cards WHERE owner_id=? ORDER BY ID;",
        (owner_id,),
    )
    return [dict(r) for r in cur.fetchall()]