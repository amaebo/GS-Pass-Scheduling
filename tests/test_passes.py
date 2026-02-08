from datetime import datetime, timedelta, timezone

import pytest

import db.passes_db as p_db
from db import db_init
import importlib

passes_module = importlib.import_module("src.routers.passes")


def _utc_ts(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _clear_predicted_passes():
    conn = db_init.db_connect()
    try:
        conn.execute("DELETE FROM reservations")
        conn.execute("DELETE FROM predicted_passes;")
        conn.commit()
    finally:
        conn.close()

def _update_satellite_tle(s_id: int, line1: str, line2: str, updated_at: str):
    conn = db_init.db_connect()
    try:
        conn.execute(
            "UPDATE satellites SET tle_line1 = ?, tle_line2 = ?, tle_updated_at = ? WHERE s_id = ?",
            (line1, line2, updated_at, s_id),
        )
        conn.commit()
    finally:
        conn.close()

def _insert_reservation(pass_id: int, gs_id: int, s_id: int):
    conn = db_init.db_connect()
    try:
        conn.execute(
            "INSERT INTO reservations (pass_id, gs_id, s_id) VALUES (?, ?, ?)",
            (pass_id, gs_id, s_id),
        )
        conn.commit()
    finally:
        conn.close()


def test_passes_refresh_when_no_cache(client, monkeypatch):
    _clear_predicted_passes()
    calls = {"count": 0}

    now = datetime.now(timezone.utc)
    _update_satellite_tle(
        s_id=1,
        line1="1 25544U 98067A   26029.50000000  .00010000  00000-0  18000-3 0  9991",
        line2="2 25544  51.6400 120.0000 0005000  20.0000  40.0000 15.50000000    10",
        updated_at=_utc_ts(now),
    )
    fake_passes = [
        {
            "norad_id": 25544,
            "start_time": _utc_ts(now + timedelta(hours=1)),
            "end_time": _utc_ts(now + timedelta(hours=2)),
            "max_elevation": 45.0,
            "duration": 600,
        },
    ]

    def fake_get_passes(*args, **kwargs):
        calls["count"] += 1
        return fake_passes

    monkeypatch.setattr(passes_module, "get_pass_predictions", fake_get_passes)

    response = client.get("/passes", params={"norad_id": 25544, "gs_id": 1})
    assert response.status_code == 200
    assert calls["count"] == 1
    assert len(response.json()["passes"]) >= 1


def test_passes_no_refresh_when_cache_fresh(client, monkeypatch):
    _clear_predicted_passes()
    now = datetime.now(timezone.utc)
    _update_satellite_tle(
        s_id=1,
        line1="1 25544U 98067A   26029.50000000  .00010000  00000-0  18000-3 0  9991",
        line2="2 25544  51.6400 120.0000 0005000  20.0000  40.0000 15.50000000    10",
        updated_at=_utc_ts(now),
    )
    p_db.insert_n2yo_pass_return_id(
        s_id=1,
        gs_id=1,
        max_elevation=45.0,
        duration=600,
        start_time=_utc_ts(now + timedelta(hours=1)),
        end_time=_utc_ts(now + timedelta(hours=26)),
    )

    def fail_get_passes(*args, **kwargs):
        pytest.fail("Predictions should not be called when cache is fresh")

    monkeypatch.setattr(passes_module, "get_pass_predictions", fail_get_passes)

    response = client.get("/passes", params={"norad_id": 25544, "gs_id": 1})
    assert response.status_code == 200


def test_passes_return_only_future(client, monkeypatch):
    _clear_predicted_passes()
    now = datetime.now(timezone.utc)
    _update_satellite_tle(
        s_id=1,
        line1="1 25544U 98067A   26029.50000000  .00010000  00000-0  18000-3 0  9991",
        line2="2 25544  51.6400 120.0000 0005000  20.0000  40.0000 15.50000000    10",
        updated_at=_utc_ts(now),
    )
    p_db.insert_n2yo_pass_return_id(
        s_id=1,
        gs_id=1,
        max_elevation=10.0,
        duration=300,
        start_time=_utc_ts(now - timedelta(hours=2)),
        end_time=_utc_ts(now - timedelta(hours=1)),
    )
    p_db.insert_n2yo_pass_return_id(
        s_id=1,
        gs_id=1,
        max_elevation=45.0,
        duration=600,
        start_time=_utc_ts(now + timedelta(hours=1)),
        end_time=_utc_ts(now + timedelta(hours=26)),
    )

    def fail_get_passes(*args, **kwargs):
        pytest.fail("Predictions should not be called for this test")

    monkeypatch.setattr(passes_module, "get_pass_predictions", fail_get_passes)

    response = client.get("/passes", params={"norad_id": 25544, "gs_id": 1})
    assert response.status_code == 200
    passes = response.json()["passes"]
    assert all(p["start_time"] >= _utc_ts(now) for p in passes)


def test_passes_response_fields(client, monkeypatch):
    _clear_predicted_passes()
    now = datetime.now(timezone.utc)
    _update_satellite_tle(
        s_id=1,
        line1="1 25544U 98067A   26029.50000000  .00010000  00000-0  18000-3 0  9991",
        line2="2 25544  51.6400 120.0000 0005000  20.0000  40.0000 15.50000000    10",
        updated_at=_utc_ts(now),
    )
    p_db.insert_n2yo_pass_return_id(
        s_id=1,
        gs_id=1,
        max_elevation=45.0,
        duration=600,
        start_time=_utc_ts(now + timedelta(hours=1)),
        end_time=_utc_ts(now + timedelta(hours=26)),
    )

    def fail_get_passes(*args, **kwargs):
        pytest.fail("Predictions should not be called for this test")

    monkeypatch.setattr(passes_module, "get_pass_predictions", fail_get_passes)

    response = client.get("/passes", params={"norad_id": 25544, "gs_id": 1})
    assert response.status_code == 200
    passes = response.json()["passes"]
    assert len(passes) >= 1
    required = {"pass_id", "gs_id", "norad_id", "start_time", "end_time", "source"}
    assert required.issubset(passes[0].keys())


def test_passes_missing_gs(client):
    response = client.get("/passes", params={"norad_id": 25544, "gs_id": 9999})
    assert response.status_code == 404


def test_passes_missing_satellite(client):
    response = client.get("/passes", params={"norad_id": 999999, "gs_id": 1})
    assert response.status_code == 404


def test_passes_blocked_for_inactive_groundstation(client):
    response = client.patch("/groundstations/1/", json={"status": "INACTIVE"})
    assert response.status_code == 200

    response = client.get("/passes", params={"norad_id": 25544, "gs_id": 1})
    assert response.status_code == 409


def test_tle_refresh_when_stale(client, monkeypatch):
    _clear_predicted_passes()
    now = datetime.now(timezone.utc)
    stale_time = _utc_ts(now - timedelta(days=2))
    _update_satellite_tle(
        s_id=1,
        line1="OLD1",
        line2="OLD2",
        updated_at=stale_time,
    )

    calls = {"count": 0}

    def fake_get_tle(*args, **kwargs):
        calls["count"] += 1
        return [
            "1 25544U 98067A   26029.50000000  .00010000  00000-0  18000-3 0  9991",
            "2 25544  51.6400 120.0000 0005000  20.0000  40.0000 15.50000000    10",
        ]

    def fake_get_passes(*args, **kwargs):
        return []

    monkeypatch.setattr(passes_module, "get_tle", fake_get_tle)
    monkeypatch.setattr(passes_module, "get_pass_predictions", fake_get_passes)

    response = client.get("/passes", params={"norad_id": 25544, "gs_id": 1})
    assert response.status_code == 200
    assert calls["count"] == 1


def test_tle_no_refresh_when_fresh(client, monkeypatch):
    _clear_predicted_passes()
    now = datetime.now(timezone.utc)
    _update_satellite_tle(
        s_id=1,
        line1="1 25544U 98067A   26029.50000000  .00010000  00000-0  18000-3 0  9991",
        line2="2 25544  51.6400 120.0000 0005000  20.0000  40.0000 15.50000000    10",
        updated_at=_utc_ts(now),
    )
    p_db.insert_n2yo_pass_return_id(
        s_id=1,
        gs_id=1,
        max_elevation=45.0,
        duration=600,
        start_time=_utc_ts(now + timedelta(hours=1)),
        end_time=_utc_ts(now + timedelta(hours=26)),
    )

    def fail_get_tle(*args, **kwargs):
        pytest.fail("CelesTrak should not be called when TLE is fresh")

    def fail_get_passes(*args, **kwargs):
        pytest.fail("Predictions should not be called when cache is fresh")

    monkeypatch.setattr(passes_module, "get_tle", fail_get_tle)
    monkeypatch.setattr(passes_module, "get_pass_predictions", fail_get_passes)

    response = client.get("/passes", params={"norad_id": 25544, "gs_id": 1})
    assert response.status_code == 200


def test_claimable_filtering_excludes_active_reservations(client, monkeypatch):
    _clear_predicted_passes()
    now = datetime.now(timezone.utc)
    _update_satellite_tle(
        s_id=1,
        line1="1 25544U 98067A   26029.50000000  .00010000  00000-0  18000-3 0  9991",
        line2="2 25544  51.6400 120.0000 0005000  20.0000  40.0000 15.50000000    10",
        updated_at=_utc_ts(now),
    )
    reserved_id = p_db.insert_n2yo_pass_return_id(
        s_id=1,
        gs_id=1,
        max_elevation=45.0,
        duration=600,
        start_time=_utc_ts(now + timedelta(hours=1)),
        end_time=_utc_ts(now + timedelta(hours=25)),
    )
    open_id = p_db.insert_n2yo_pass_return_id(
        s_id=1,
        gs_id=1,
        max_elevation=30.0,
        duration=400,
        start_time=_utc_ts(now + timedelta(hours=3)),
        end_time=_utc_ts(now + timedelta(hours=26)),
    )
    _insert_reservation(reserved_id, gs_id=1, s_id=1)

    def fail_get_passes(*args, **kwargs):
        pytest.fail("Predictions should not be called for this test")

    monkeypatch.setattr(passes_module, "get_pass_predictions", fail_get_passes)

    response = client.get("/passes", params={"norad_id": 25544, "gs_id": 1})
    assert response.status_code == 200
    ids = {p["pass_id"] for p in response.json()["passes"]}
    assert reserved_id not in ids
    assert open_id in ids


def test_delete_unreserved_expired_passes_keeps_active():
    _clear_predicted_passes()
    now = datetime.now(timezone.utc)
    active_id = p_db.insert_n2yo_pass_return_id(
        s_id=1,
        gs_id=1,
        max_elevation=20.0,
        duration=600,
        start_time=_utc_ts(now - timedelta(minutes=20)),
        end_time=_utc_ts(now + timedelta(minutes=20)),
    )
    expired_id = p_db.insert_n2yo_pass_return_id(
        s_id=1,
        gs_id=1,
        max_elevation=10.0,
        duration=300,
        start_time=_utc_ts(now - timedelta(hours=2)),
        end_time=_utc_ts(now - timedelta(hours=1)),
    )
    assert active_id is not None
    assert expired_id is not None

    p_db.delete_unreserved_expired_passes()

    assert p_db.get_pass_from_pass_id(active_id) is not None
    assert p_db.get_pass_from_pass_id(expired_id) is None
