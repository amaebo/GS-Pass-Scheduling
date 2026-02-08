# Change Notes

## 2026-02-08
- Replaced two unused pass indexes with a composite index matching pass lookup patterns. `db/schema.sql`

## 2026-01-24
- Added basic API tests with FastAPI `TestClient`. `tests/test_api.py`
- Added `src/__init__.py` so `src` is a package. `src/__init__.py`
- Added a pytest helper that fixes `ModuleNotFoundError: No module named 'src'`. `tests/conftest.py`
- Reworked DB init and satellite insert to use safer SQL, correct table names, and proper commits. `db/db_init.py`, `db/satellites_db.py`
- Fixed missing DB function imports and a wrong helper name in DB init. `src/API.py`, `db/db_init.py`
- Fixed pytest fixture usage and mocked DB insert in tests to avoid touching real SQLite. `tests/test_api.py`

What was tricky:
- The `src` package existed but Python couldn't find it because the repo root wasn’t on `sys.path`.
- The SQL insert used string formatting and the wrong table name, which breaks inserts and can be unsafe.
