import sqlite3
from db.db_query import execute_row_id, fetch_all


def insert_new_satellite(norad_id: int, s_name: str) -> int:
    query = """
        INSERT INTO satellites (s_name, norad_id)
        VALUES (?, ?);
    """

    try:
        return execute_row_id(query, (s_name, norad_id))
    except sqlite3.Error:
        raise

def get_all_satellites():
    query= """
            SELECT *
            FROM satellites
    """
    try:
        return fetch_all(query)
    except sqlite3.Error:
        raise
