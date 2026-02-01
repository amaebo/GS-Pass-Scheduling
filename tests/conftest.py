from pathlib import Path
import sys
import pytest
from fastapi.testclient import TestClient


# Ensure project root is on sys.path for local imports.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from db import db_init
from src.main import app


@pytest.fixture()
def test_db(tmp_path):
    db_path = tmp_path / "test.db"
    old_path = db_init.DB_PATH
    db_init.DB_PATH = db_path
    try:
        db_init.init_db(str(db_path))
        seed_sql = (Path(__file__).resolve().parents[1] / "db" / "seed.sql").read_text(encoding="utf-8")
        conn = db_init.db_connect(str(db_path))
        try:
            conn.executescript(seed_sql)
            conn.commit()
        finally:
            conn.close()
        yield db_path
    finally:
        db_init.DB_PATH = old_path


@pytest.fixture()
def client(test_db):
    return TestClient(app)
