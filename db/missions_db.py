

import sqlite3
from db.db_init import db_connect


def add_mission(mission_name: str, owner: str | None = None, priority: str | None = None) -> int:
    query = """
            INSERT INTO missions(mission_name, owner, priority) 
            VALUES (?, ?, ?);
        """
    conn = db_connect()
    try:
        cur = conn.execute(query, (mission_name, owner, priority))
        conn.commit()
        return cur.lastrowid
    except sqlite3.Error:
        conn.rollback()
        raise
    finally:
        conn.close()

def get_missions():
    query = """
            SELECT *
            FROM missions;
        """
    conn = db_connect()
    
    try:
        cur = conn.execute(query)
        conn.commit()
        return cur.fetchall()
    except sqlite3.Error:
        conn.rollback()
        raise
    finally:
        conn.close()