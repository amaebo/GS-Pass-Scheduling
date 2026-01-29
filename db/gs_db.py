
import sqlite3
from db.db_init import db_connect


def insert_gs_manual(gs_name: str, lon: float, lat: float):
    query= """
            INSERT INTO ground_stations(gs_name, lon, lat, source) VALUES (?,?,?, manual)
        """
    conn = db_connect()
    try:
        cur = conn.execute(query, gs_name, lon, lat)
        conn.commit()
        return cur.lastrowid # return primary key of new row (s_id)
    except sqlite3.Error:
        conn.rollback()
        raise
    finally:
        conn.close()