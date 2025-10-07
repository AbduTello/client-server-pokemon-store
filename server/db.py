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

# WRITE HELPER FUNCTIONS

def buy(conn: sqlite3.Connection, owner_id: int, card_name: str,
        card_type: str, rarity: str, price_per_card: float, count: int):
    """
    Implements BUY:
      - verify user + balance
      - deduct USD
      - upsert card variant (name+type+rarity)
    Returns (new_user_balance, new_variant_count).
    Raises ValueError with a short message for any failure.
    """
    if count <= 0 or price_per_card < 0:
        raise ValueError("count and price must be positive")

    total = float(price_per_card) * int(count)
    with conn:
        user = conn.execute(
            "SELECT ID, usd_balance FROM Users WHERE ID=?;", (owner_id,)
        ).fetchone()
        if not user:
            raise ValueError(f"user {owner_id} doesn't exist")
        if float(user["usd_balance"]) < total:
            raise ValueError("Not enough balance")

        new_balance = float(user["usd_balance"]) - total
        conn.execute("UPDATE Users SET usd_balance=? WHERE ID=?;", (new_balance, owner_id))

        # upsert exact variant
        row = conn.execute(
            "SELECT ID, count FROM Pokemon_cards "
            "WHERE owner_id=? AND card_name=? AND card_type=? AND rarity=?;",
            (owner_id, card_name, card_type, rarity),
        ).fetchone()

        if row:
            new_count = int(row["count"]) + int(count)
            conn.execute("UPDATE Pokemon_cards SET count=? WHERE ID=?;", (new_count, row["ID"]))
        else:
            conn.execute(
                "INSERT INTO Pokemon_cards (card_name, card_type, rarity, count, owner_id) "
                "VALUES (?,?,?,?,?);",
                (card_name, card_type, rarity, int(count), owner_id),
            )
            new_count = int(count)

    return new_balance, new_count

def sell(conn: sqlite3.Connection, owner_id: int, card_name: str,
         price_per_card: float, count: int):
    """
    Implements SELL (the spec's SELL doesn't include type/rarity):
      - verify user
      - ensure total cards of that name across variants >= count
      - decrement counts across rows by ID until satisfied (delete rows that hit 0)
      - credit USD
    Returns (new_user_balance, remaining_total_for_that_name).
    Raises ValueError with a short message for any failure.
    """
    if count <= 0 or price_per_card < 0:
        raise ValueError("count and price must be positive")

    with conn:
        user = conn.execute(
            "SELECT ID, usd_balance FROM Users WHERE ID=?;", (owner_id,)
        ).fetchone()
        if not user:
            raise ValueError(f"user {owner_id} doesn't exist")

        rows = conn.execute(
            "SELECT ID, count FROM Pokemon_cards "
            "WHERE owner_id=? AND card_name=? ORDER BY ID;",
            (owner_id, card_name),
        ).fetchall()

        total_have = sum(int(r["count"]) for r in rows)
        need = int(count)
        if total_have < need:
            raise ValueError(f"Not enough {card_name} cards")

        # decrement across rows
        remaining_to_remove = need
        for r in rows:
            if remaining_to_remove == 0:
                break
            have = int(r["count"])
            take = min(have, remaining_to_remove)
            newc = have - take
            remaining_to_remove -= take
            if newc > 0:
                conn.execute("UPDATE Pokemon_cards SET count=? WHERE ID=?;", (newc, r["ID"]))
            else:
                conn.execute("DELETE FROM Pokemon_cards WHERE ID=?;", (r["ID"],))

        credit = float(price_per_card) * need
        new_balance = float(user["usd_balance"]) + credit
        conn.execute("UPDATE Users SET usd_balance=? WHERE ID=?;", (new_balance, owner_id))

        remain_total = conn.execute(
            "SELECT COALESCE(SUM(count),0) AS c FROM Pokemon_cards "
            "WHERE owner_id=? AND card_name=?;",
            (owner_id, card_name),
        ).fetchone()["c"]

    return new_balance, int(remain_total)