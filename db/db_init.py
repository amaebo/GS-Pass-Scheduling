import sqlite3
import os

# simple paths so its easy to read
BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "ground_system.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "schema.sql")


def get_db(db_path=None):
    """
    Returns a conn object to database
    
    :param db_path: Path to database file
    """
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path=None, schema_path=None):
    """
    Initializes Database

    :param db_path: Path to database file
    :param schema_path: Path to database schema creation file
    """
    path = schema_path or SCHEMA_PATH
    with open(path, "r") as f:
        schema_sql = f.read()
    conn = get_db(db_path)
    conn.executescript(schema_sql)
    conn.commit()
    conn.close()
