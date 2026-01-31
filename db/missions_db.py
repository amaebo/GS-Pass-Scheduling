

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

def get_all_missions():
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

def get_mission_by_id(mission_id: int):
    query= """
            SELECT *
            FROM missions
            WHERE mission_id = ?
        """
    conn = db_connect()
    
    try:
        cur = conn.execute(query, (mission_id,))
        conn.commit()
        return cur.fetchone()
    except sqlite3.Error:
        conn.rollback()
        raise
    finally:
        conn.close()

def update_mission(mission_id: int, updates: dict) -> int:
    if not updates:
        return 0

    set_clauses = []
    params = []

    for field, value in updates.items():
        set_clauses.append(f"{field} = ?")
        params.append(value)
    
    params.append(mission_id)


    query = f"""
            UPDATE missions
            SET {", ".join(set_clauses)}
            WHERE mission_id = ?;
        """
    conn = db_connect()
    try:
        cur = conn.execute(query, params)
        conn.commit()
        return cur.rowcount
    except sqlite3.Error:
        conn.rollback()
        raise
    finally:
        conn.close()
    
