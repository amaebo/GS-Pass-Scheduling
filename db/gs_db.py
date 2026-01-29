
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
    except sqlite3.Error as e:
        raise RuntimeError(f"Insert ground station failed: {e}")

