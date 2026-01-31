import sqlite3
from db.db_init import db_connect


def fetch_one(query: str, params: tuple | None = None) -> sqlite3.Row | None:
    """Fetch a single row or None, handling connection lifecycle safely."""
    conn = db_connect()
    try:
        cur = conn.execute(query, params or ())
        row = cur.fetchone()
        conn.commit()
        return row
    except sqlite3.Error:
        conn.rollback()
        raise
    finally:
        conn.close()


def fetch_all(query: str, params: tuple | None = None):
    """Fetch all rows as a list of sqlite3.Row."""
    conn = db_connect()
    try:
        cur = conn.execute(query, params or ())
        rows = cur.fetchall()
        conn.commit()
        return rows
    except sqlite3.Error:
        conn.rollback()
        raise
    finally:
        conn.close()


def execute_row_id(query: str, params: tuple | None = None) -> int:
    """Run a write query and return the last inserted row id."""
    conn = db_connect()
    try:
        cur = conn.execute(query, params or ())
        conn.commit()
        return cur.lastrowid
    except sqlite3.Error:
        conn.rollback()
        raise
    finally:
        conn.close()

def execute(query: str, params: tuple | None = None) -> None:
    """Run a write query ."""
    conn = db_connect()
    try:
        conn.execute(query, params or ())
        conn.commit()
    except sqlite3.Error as e:
        print("execution",type(e))
        conn.rollback()
        raise
    finally:
        conn.close()

def execute_rowcount(query: str, params: tuple | None = None) -> int:
    """Run a write query and return affected row count."""
    conn = db_connect()
    try:
        cur = conn.execute(query, params or ())
        conn.commit()
        return cur.rowcount
    except sqlite3.Error:
        conn.rollback()
        raise
    finally:
        conn.close()
