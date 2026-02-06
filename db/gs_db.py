
import sqlite3
from db.db_query import execute_row_id, execute_rowcount, fetch_all, fetch_one


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
def get_gs_by_id(gs_id: int):
    query = """
            SELECT *
            FROM ground_stations
            WHERE gs_id = ?
        """
    try:
        return fetch_one(query, (gs_id,))
    except sqlite3.Error:
        raise
    
def gs_has_active_reservations(gs_id: int) -> bool:
    query = """
            SELECT 1
            FROM reservations r
            INNER JOIN predicted_passes p ON p.pass_id = r.pass_id
            WHERE r.gs_id = ?
              AND r.cancelled_at IS NULL
              AND p.end_time >= CURRENT_TIMESTAMP
            LIMIT 1
        """
    return True if fetch_one(query, (gs_id,)) else False
    

def delete_gs_by_id(gs_id: int) -> int:
    query = """
            DELETE FROM ground_stations
            WHERE gs_id = ?
        """
    try:
        return execute_rowcount(query, (gs_id,))
    except sqlite3.Error:
        raise
