import sqlite3
from db.db_init import db_connect


def insert_new_satellite(norad_id: int, s_name: str) -> int:
    query = """
        INSERT INTO satellites (s_name, norad_id)
        VALUES (?, ?)
    """

    conn = db_connect()
    try:
        cur = conn.execute(query, (s_name, norad_id))
        conn.commit()
        return cur.lastrowid # primary key of new row
    except sqlite3.Error:
        conn.rollback()
        raise
    finally:
        conn.close()