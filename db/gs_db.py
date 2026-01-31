
import sqlite3
from db.db_init import db_connect


def insert_gs_manual(gs_code: str, lon: float, lat: float) -> int:
    query= """
            INSERT INTO ground_stations(gs_code, lon, lat, source, status) 
            VALUES (?,?,?,?,?);
        """
    conn = db_connect()
    try:
        cur = conn.execute(query, (gs_code, lon, lat, "manual", "ACTIVE"))
        conn.commit()
        return cur.lastrowid # return primary key of new row (gs_id)
    except sqlite3.Error:
        conn.rollback()
        raise
    finally:
        conn.close()

def get_all_gs() -> sqlite3.Row:
    query= """
            SELECT *
            FROM ground_stations;
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