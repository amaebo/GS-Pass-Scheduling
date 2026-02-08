import sqlite3
from db.db_init import db_connect
from db.db_query import execute_row_id, fetch_all, fetch_one, execute_rowcount


def insert_new_satellite(norad_id: int, s_name: str) -> int:
    query = """
        INSERT INTO satellites (s_name, norad_id)
        VALUES (?, ?);
    """

    try:
        return execute_row_id(query, (s_name, norad_id))
    except sqlite3.Error:
        raise

def get_all_satellites(include_s_id: bool = False):
    if include_s_id:
        query = """
                SELECT s_id, s_name, norad_id, date_added
                FROM satellites
            """
        
    else:
        query= """
                SELECT s_name, norad_id, date_added
                FROM satellites
            """
        
    try:
        return fetch_all(query)
    except sqlite3.Error:
        raise

def get_satellite_by_id(s_id: int):
    query = """
            SELECT *
            FROM satellites
            WHERE s_id = ?
        """
    try:
        return fetch_one(query,(s_id,))
    except sqlite3.Error:
        raise

def get_satellite_by_norad_id(norad_id: int):
    query = """
            SELECT *
            FROM satellites
            WHERE norad_id = ?
        """
    try:
        return fetch_one(query, (norad_id,))
    except sqlite3.Error:
        raise

def sat_has_active_reservations(s_id: int):
    query = """
            SELECT 1
            FROM reservations r
            INNER JOIN predicted_passes p ON p.pass_id = r.pass_id
            WHERE r.s_id = ?
              AND r.cancelled_at IS NULL
              AND p.end_time >= CURRENT_TIMESTAMP
            LIMIT 1
        """
    return True if fetch_one(query, (s_id,)) else False

def delete_satellite_by_s_id(s_id: int):
    query = """
            DELETE FROM satellites
            WHERE s_id = ? """
    return execute_rowcount(query,(s_id,))

def delete_satellite_and_reservations(s_id: int) -> tuple[int, int]:
    conn = db_connect()
    try:
        reservations_cur = conn.execute(
            "DELETE FROM reservations WHERE s_id = ?",
            (s_id,),
        )
        satellite_cur = conn.execute(
            "DELETE FROM satellites WHERE s_id = ?",
            (s_id,),
        )
        conn.commit()
        return reservations_cur.rowcount, satellite_cur.rowcount
    except sqlite3.Error:
        conn.rollback()
        raise
    finally:
        conn.close()

def update_satellite(s_id: int, updates: dict):
    if not updates:
        return 0

    set_clauses = []
    params = []

    for col, value in updates.items():
        set_clauses.append(f"{col} = ?")
        params.append(value)

    params.append(s_id)
    query = f"""
            UPDATE satellites
            SET {", ".join(set_clauses)}
            WHERE s_id = ?
        """
    return execute_rowcount(query, tuple(params))


def update_satellite_tle(s_id: int, tle_line1: str, tle_line2: str, tle_updated_at: str) -> int:
    query = """
            UPDATE satellites
            SET tle_line1 = ?, tle_line2 = ?, tle_updated_at = ?
            WHERE s_id = ?
        """
    return execute_rowcount(query, (tle_line1, tle_line2, tle_updated_at, s_id))
