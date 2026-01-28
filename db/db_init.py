import os
import sqlite3

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "ground_system.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "schema.sql")


def get_db(db_path: str | None = None) -> sqlite3.Connection:
    """
    Create and return a SQLite database connection.
    """
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row  # allows abiltity to access columns by name 
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(
    db_path: str | None = None,
    schema_path: str | None = None
) -> None:
    """
    Initialize the database schema.
    """
    db_file = db_path or DB_PATH
    schema_file = schema_path or SCHEMA_PATH

    with open(schema_file, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    conn = get_db(db_file)
    try:
        conn.executescript(schema_sql)
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise RuntimeError(f"Database initialization failed: {e}")
    finally:
        conn.close()