from datetime import datetime, timedelta, timezone

import db.passes_db as p_db
from db import db_init


def _utc_ts(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _clear_reservation_data():
    conn = db_init.db_connect()
    try:
        conn.execute("DELETE FROM reservation_commands;")
        conn.execute("DELETE FROM reservations;")
        conn.execute("DELETE FROM predicted_passes;")
        conn.commit()
    finally:
        conn.close()


def _create_future_pass() -> int:
    now = datetime.now(timezone.utc)
    start_time = _utc_ts(now + timedelta(hours=1))
    end_time = _utc_ts(now + timedelta(hours=2))
    pass_id = p_db.insert_n2yo_pass_return_id(
        s_id=1,
        gs_id=1,
        max_elevation=45.0,
        duration=600,
        start_time=start_time,
        end_time=end_time,
    )
    assert pass_id is not None
    return pass_id


def test_create_reservation_no_mission_no_commands(client):
    _clear_reservation_data()
    pass_id = _create_future_pass()

    response = client.post("/reservations", json={"pass_id": pass_id})
    assert response.status_code == 200

    data = response.json()["Reservation"]
    assert data["mission_id"] is None
    assert data["commands"] == []


def test_create_reservation_no_mission_with_commands(client):
    _clear_reservation_data()
    pass_id = _create_future_pass()

    response = client.post(
        "/reservations",
        json={"pass_id": pass_id, "commands": ["PING"]},
    )
    assert response.status_code == 200

    data = response.json()["Reservation"]
    assert data["mission_id"] is None
    assert "PING" in data["commands"]


def test_create_reservation_mission_not_connected(client):
    _clear_reservation_data()
    pass_id = _create_future_pass()

    response = client.post(
        "/reservations",
        json={"pass_id": pass_id, "mission_id": 2},
    )
    assert response.status_code == 404


def test_create_reservation_with_mission_connected(client):
    _clear_reservation_data()
    pass_id = _create_future_pass()

    response = client.post(
        "/reservations",
        json={"pass_id": pass_id, "mission_id": 1},
    )
    assert response.status_code == 200
    assert response.json()["Reservation"]["mission_id"] == 1


def test_create_reservation_command_not_in_catalog(client):
    _clear_reservation_data()
    pass_id = _create_future_pass()

    response = client.post(
        "/reservations",
        json={"pass_id": pass_id, "commands": ["NOT_A_CMD"]},
    )
    assert response.status_code == 400


def test_create_reservation_duplicate_commands(client):
    _clear_reservation_data()
    pass_id = _create_future_pass()

    response = client.post(
        "/reservations",
        json={"pass_id": pass_id, "commands": ["PING", "PING"]},
    )
    assert response.status_code == 400


def test_create_reservation_already_reserved(client):
    _clear_reservation_data()
    pass_id = _create_future_pass()

    first = client.post("/reservations", json={"pass_id": pass_id})
    assert first.status_code == 200

    second = client.post("/reservations", json={"pass_id": pass_id})
    assert second.status_code == 409


def test_create_reservation_pass_expired(client):
    _clear_reservation_data()
    now = datetime.now(timezone.utc)
    pass_id = p_db.insert_n2yo_pass_return_id(
        s_id=1,
        gs_id=1,
        max_elevation=10.0,
        duration=300,
        start_time=_utc_ts(now - timedelta(hours=2)),
        end_time=_utc_ts(now - timedelta(hours=1)),
    )
    assert pass_id is not None

    response = client.post("/reservations", json={"pass_id": pass_id})
    assert response.status_code == 400


def test_create_reservation_pass_not_found(client):
    _clear_reservation_data()
    response = client.post("/reservations", json={"pass_id": 999999})
    assert response.status_code == 404


def test_create_reservation_mission_not_found(client):
    _clear_reservation_data()
    pass_id = _create_future_pass()
    response = client.post(
        "/reservations",
        json={"pass_id": pass_id, "mission_id": 999999},
    )
    assert response.status_code == 404


def test_create_reservation_invalid_pass_id_type(client):
    _clear_reservation_data()
    response = client.post("/reservations", json={"pass_id": "abc"})
    assert response.status_code == 422


def test_create_reservation_invalid_pass_id_negative(client):
    _clear_reservation_data()
    response = client.post("/reservations", json={"pass_id": -1})
    assert response.status_code == 422


def test_create_reservation_with_commands_returns_commands(client):
    _clear_reservation_data()
    pass_id = _create_future_pass()

    response = client.post(
        "/reservations",
        json={"pass_id": pass_id, "commands": ["PING", "DOWNLINK"]},
    )
    assert response.status_code == 200

    data = response.json()["Reservation"]
    assert set(data["commands"]) == {"PING", "DOWNLINK"}
