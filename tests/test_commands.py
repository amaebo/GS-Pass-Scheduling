import sqlite3

import db.commands_db as c_db


def test_commands_db_error_returns_500(client, monkeypatch):
    def raise_db_error():
        raise sqlite3.Error("db down")

    monkeypatch.setattr(c_db, "get_all_commands", raise_db_error)

    response = client.get("/commands/")
    assert response.status_code == 500
