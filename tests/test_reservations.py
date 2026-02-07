from datetime import datetime, timedelta, timezone
import sqlite3

import db.passes_db as p_db
import db.reservations_db as r_db
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

    data = response.json()["reservation"]
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

    data = response.json()["reservation"]
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
    assert response.json()["reservation"]["mission_id"] == 1


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


def test_create_reservation_handles_integrity_error(client, monkeypatch):
    _clear_reservation_data()
    pass_id = _create_future_pass()

    def raise_integrity(*args, **kwargs):
        raise sqlite3.IntegrityError("duplicate")

    monkeypatch.setattr(r_db, "create_reservation_with_commands", raise_integrity)

    response = client.post("/reservations", json={"pass_id": pass_id})
    assert response.status_code == 409


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

    data = response.json()["reservation"]
    assert set(data["commands"]) == {"PING", "DOWNLINK"}


def test_get_reservations_excludes_cancelled(client):
    response = client.get("/reservations")
    assert response.status_code == 200
    reservations = response.json()["reservations"]
    assert all(r["status"] != "CANCELLED" for r in reservations)


def test_get_reservations_include_cancelled(client):
    response = client.get("/reservations", params={"include_cancelled": True})
    assert response.status_code == 200
    reservations = response.json()["reservations"]
    assert any(r["status"] == "CANCELLED" for r in reservations)


def test_get_reservations_by_mission(client):
    response = client.get("/reservations/1")
    assert response.status_code == 200
    reservations = response.json()["reservations"]
    assert len(reservations) >= 1
    assert all(r["mission_id"] == 1 for r in reservations)


def test_cancel_reservation(client):
    response = client.post("/reservations/1/cancel")
    assert response.status_code == 200

    follow_up = client.get("/reservations", params={"include_cancelled": True})
    assert follow_up.status_code == 200
    reservations = follow_up.json()["reservations"]
    cancelled = [r for r in reservations if r["r_id"] == 1]
    assert cancelled and cancelled[0]["status"] == "CANCELLED"


def test_cancel_reservation_not_found(client):
    response = client.post("/reservations/999999/cancel")
    assert response.status_code == 404


def test_cancel_then_reserve_same_pass_again(client):
    _clear_reservation_data()
    pass_id = _create_future_pass()

    first = client.post("/reservations", json={"pass_id": pass_id})
    assert first.status_code == 200
    r_id = first.json()["reservation"]["r_id"]

    cancel = client.post(f"/reservations/{r_id}/cancel")
    assert cancel.status_code == 200

    second = client.post("/reservations", json={"pass_id": pass_id})
    assert second.status_code == 200


def test_pass_removed_and_restored_in_passes_list_on_cancel(client):
    _clear_reservation_data()
    pass_id = _create_future_pass()

    before = client.get("/passes", params={"norad_id": 25544, "gs_id": 1})
    assert before.status_code == 200
    before_ids = {p["pass_id"] for p in before.json()["passes"]}
    assert pass_id in before_ids

    reserve = client.post("/reservations", json={"pass_id": pass_id})
    assert reserve.status_code == 200
    r_id = reserve.json()["reservation"]["r_id"]

    during = client.get("/passes", params={"norad_id": 25544, "gs_id": 1})
    assert during.status_code == 200
    during_ids = {p["pass_id"] for p in during.json()["passes"]}
    assert pass_id not in during_ids

    cancel = client.post(f"/reservations/{r_id}/cancel")
    assert cancel.status_code == 200

    after = client.get("/passes", params={"norad_id": 25544, "gs_id": 1})
    assert after.status_code == 200
    after_ids = {p["pass_id"] for p in after.json()["passes"]}
    assert pass_id in after_ids


def test_multiple_cancelled_reservations_allowed_one_active(client):
    _clear_reservation_data()
    pass_id = _create_future_pass()

    first = client.post("/reservations", json={"pass_id": pass_id})
    assert first.status_code == 200
    r_id_1 = first.json()["reservation"]["r_id"]

    cancel_1 = client.post(f"/reservations/{r_id_1}/cancel")
    assert cancel_1.status_code == 200

    second = client.post("/reservations", json={"pass_id": pass_id})
    assert second.status_code == 200
    r_id_2 = second.json()["reservation"]["r_id"]
    assert r_id_2 != r_id_1

    cancel_2 = client.post(f"/reservations/{r_id_2}/cancel")
    assert cancel_2.status_code == 200

    third = client.post("/reservations", json={"pass_id": pass_id})
    assert third.status_code == 200
    r_id_3 = third.json()["reservation"]["r_id"]
    assert r_id_3 not in {r_id_1, r_id_2}

    # A second active reservation should be blocked.
    blocked = client.post("/reservations", json={"pass_id": pass_id})
    assert blocked.status_code == 409
