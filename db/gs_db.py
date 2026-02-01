
import sqlite3
from db.db_query import execute_row_id, fetch_all


def insert_gs_manual(gs_code: str, lon: float, lat: float, alt: float) -> int:
    query= """
            INSERT INTO ground_stations(gs_code, lon, lat, alt, source, status) 
            VALUES (?,?,?,?,?,?);
        """
    try:
        return execute_row_id(query, (gs_code, lon, lat, alt, "manual", "ACTIVE"))
    except sqlite3.Error:
        raise

def get_all_gs() -> sqlite3.Row:
    query= """
            SELECT *
            FROM ground_stations;
    """
    try:
        return fetch_all(query)
    except sqlite3.Error:
        raise
