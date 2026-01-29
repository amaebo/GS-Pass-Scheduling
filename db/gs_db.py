
import sqlite3
from db.db_init import db_connect


def insert_gs_manual(gs_name: str, lon: float, lat: float) -> int:
    query= """
            INSERT INTO ground_stations(gs_name, lon, lat, source, status) 
            VALUES (?,?,?,?,?);
        """
    conn = db_connect()
    try:
        cur = conn.execute(query, (gs_name, lon, lat, "manual", "ACTIVE"))
        conn.commit()
        return cur.lastrowid # return primary key of new row (gs_id)
    except sqlite3.Error:
        conn.rollback()
        raise
    finally:
        conn.close()