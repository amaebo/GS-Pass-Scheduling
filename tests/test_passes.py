from datetime import datetime, timedelta, timezone

import httpx
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


def test_passes_refresh_when_no_cache(client, monkeypatch):
    _clear_predicted_passes()
    calls = {"count": 0}

    now = datetime.now(timezone.utc)
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

    monkeypatch.setattr(passes_module, "get_passes_from_n2yo", fake_get_passes)

    response = client.get("/passes", params={"norad_id": 25544, "gs_id": 1})
    assert response.status_code == 200
    assert calls["count"] == 1
    assert len(response.json()["passes"]) >= 1


def test_passes_no_refresh_when_cache_fresh(client, monkeypatch):
    _clear_predicted_passes()
    now = datetime.now(timezone.utc)
    p_db.insert_n2yo_pass_return_id(
        s_id=1,
        gs_id=1,
        max_elevation=45.0,
        duration=600,
        start_time=_utc_ts(now + timedelta(hours=1)),
        end_time=_utc_ts(now + timedelta(hours=13)),
    )

    def fail_get_passes(*args, **kwargs):
        pytest.fail("N2YO should not be called when cache is fresh")

    monkeypatch.setattr(passes_module, "get_passes_from_n2yo", fail_get_passes)

    response = client.get("/passes", params={"norad_id": 25544, "gs_id": 1})
    assert response.status_code == 200


def test_passes_return_only_future(client, monkeypatch):
    _clear_predicted_passes()
    now = datetime.now(timezone.utc)
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
        end_time=_utc_ts(now + timedelta(hours=13)),
    )

    def fail_get_passes(*args, **kwargs):
        pytest.fail("N2YO should not be called for this test")

    monkeypatch.setattr(passes_module, "get_passes_from_n2yo", fail_get_passes)

    response = client.get("/passes", params={"norad_id": 25544, "gs_id": 1})
    assert response.status_code == 200
    passes = response.json()["passes"]
    assert all(p["start_time"] >= _utc_ts(now) for p in passes)


def test_passes_response_fields(client, monkeypatch):
    _clear_predicted_passes()
    now = datetime.now(timezone.utc)
    p_db.insert_n2yo_pass_return_id(
        s_id=1,
        gs_id=1,
        max_elevation=45.0,
        duration=600,
        start_time=_utc_ts(now + timedelta(hours=1)),
        end_time=_utc_ts(now + timedelta(hours=13)),
    )

    def fail_get_passes(*args, **kwargs):
        pytest.fail("N2YO should not be called for this test")

    monkeypatch.setattr(passes_module, "get_passes_from_n2yo", fail_get_passes)

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


def test_passes_n2yo_failure(client, monkeypatch):
    _clear_predicted_passes()

    def raise_httpx(*args, **kwargs):
        request = httpx.Request("GET", "https://example.com")
        response = httpx.Response(502, request=request)
        raise httpx.HTTPStatusError("Bad gateway", request=request, response=response)

    monkeypatch.setattr(passes_module, "get_passes_from_n2yo", raise_httpx)

    response = client.get("/passes", params={"norad_id": 25544, "gs_id": 1})
    assert response.status_code == 502


def test_passes_n2yo_request_error(client, monkeypatch):
    _clear_predicted_passes()

    def raise_request_error(*args, **kwargs):
        request = httpx.Request("GET", "https://example.com")
        raise httpx.RequestError("boom", request=request)

    monkeypatch.setattr(passes_module, "get_passes_from_n2yo", raise_request_error)

    response = client.get("/passes", params={"norad_id": 25544, "gs_id": 1})
    assert response.status_code == 502


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
