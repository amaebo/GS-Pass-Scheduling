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


def test_list_satellites_seeded(client):
    response = client.get("/satellites")
    assert response.status_code == 200
    satellites = response.json()["satellites"]
    assert len(satellites) >= 1


def test_register_satellite_then_list(client):
    payload = {"norad_id": 99999, "s_name": "TEST SAT"}
    response = client.post("/satellites/register", json=payload)
    assert response.status_code == 201

    response = client.get("/satellites")
    assert response.status_code == 200
    satellites = response.json()["satellites"]
    assert any(
        sat["norad_id"] == 99999 and sat["s_name"] == "TEST SAT" for sat in satellites
    )
    assert all("s_id" not in sat for sat in satellites)


def test_register_satellite_duplicate_norad_id(client):
    payload = {"norad_id": 88888, "s_name": "DUP TEST SAT"}
    first = client.post("/satellites/register", json=payload)
    assert first.status_code == 201

    second = client.post("/satellites/register", json=payload)
    assert second.status_code == 409

# ===================== Passes =====================

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


def test_passes_n2yo_failure(client, monkeypatch):
    _clear_predicted_passes()

    def raise_httpx(*args, **kwargs):
        request = httpx.Request("GET", "https://example.com")
        response = httpx.Response(502, request=request)
        raise httpx.HTTPStatusError("Bad gateway", request=request, response=response)

    monkeypatch.setattr(passes_module, "get_passes_from_n2yo", raise_httpx)

    response = client.get("/passes", params={"norad_id": 25544, "gs_id": 1})
    assert response.status_code == 502
