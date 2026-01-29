import sqlite3
from pathlib import Path

# Project root: GS-PASS-SCHEDULING/
PROJECT_ROOT = Path(__file__).resolve().parents[1]

DB_PATH = PROJECT_ROOT / "data" / "ground_system.db"
SCHEMA_PATH = PROJECT_ROOT / "db" / "schema.sql"


def db_connect(db_path: str | None = None) -> sqlite3.Connection:
    """
    Create and return a SQLite database connection.
    """
    path = Path(db_path) if db_path else DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(
    db_path: str | None = None,
    schema_path: str | None = None
) -> None:
    """
    Initialize the database schema.
    """
    db_file = Path(db_path) if db_path else DB_PATH
    schema_file = Path(schema_path) if schema_path else SCHEMA_PATH

    schema_sql = schema_file.read_text(encoding="utf-8")

    conn = db_connect(str(db_file))
    try:
        conn.executescript(schema_sql)
        conn.commit()
    except sqlite3.Error:
        conn.rollback()
        raise
    finally:
        conn.close()