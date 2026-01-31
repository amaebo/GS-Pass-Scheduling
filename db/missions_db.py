

import sqlite3
from db.db_query import execute, execute_row_id, execute_rowcount, fetch_all, fetch_one


def add_mission(mission_name: str, owner: str | None = None, priority: str | None = None) -> int:
    query = """
            INSERT INTO missions(mission_name, owner, priority) 
            VALUES (?, ?, ?);
        """
    try:
        return execute_row_id(query, (mission_name, owner, priority))
    except sqlite3.Error:
        raise

def get_all_missions():
    query = """
            SELECT *
            FROM missions;
        """
    try:
        return fetch_all(query)
    except sqlite3.Error:
        raise

def get_mission_by_id(mission_id: int):
    query= """
            SELECT *
            FROM missions
            WHERE mission_id = ?
        """
    try:
        return fetch_one(query, (mission_id,))
    except sqlite3.Error:
        raise

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
    try:
        return execute_rowcount(query, tuple(params))
    except sqlite3.Error:
        raise
    
def delete_mission(mission_id: int):
    query = """
            DELETE FROM missions
            WHERE mission_id = ?;
        """
    
    try:
        return execute(query, (mission_id,))
    except sqlite3.Error:
        raise
