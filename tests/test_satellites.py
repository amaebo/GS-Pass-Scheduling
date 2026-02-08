from datetime import datetime, timedelta, timezone
import time

import db.passes_db as p_db
from db import db_init


def _utc_ts(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _create_groundstation_no_status(client) -> int:
    ms = int(time.time() * 1000)
    gs_code = f"TEST_GS_{ms}"
    lat = 39.0 + (ms % 1000) / 10000
    lon = -105.0 - (ms % 1000) / 10000
    alt = 1600.0 + (ms % 100) / 10

    response = client.post(
        "/groundstations",
        json={"gs_code": gs_code, "lat": lat, "lon": lon, "alt": alt},
    )
    assert response.status_code == 201

    listing = client.get("/groundstations")
    assert listing.status_code == 200
    rows = listing.json()["ground_stations"]
    match = next((gs for gs in rows if gs["gs_code"] == gs_code), None)
    assert match is not None
    return match["gs_id"]


def _create_groundstation(client) -> int:
    return _create_groundstation_no_status(client)


def _delete_groundstation_force(client, gs_id: int):
    client.delete(f"/groundstations/{gs_id}", params={"force": True})


def _create_satellite(client) -> int:
    ms = int(time.time() * 1000)
    norad_id = 70000 + (ms % 20000)
    payload = {"norad_id": norad_id, "s_name": f"TEST SAT {ms}"}
    response = client.post("/satellites", json=payload)
    assert response.status_code == 201
    return norad_id


def _get_satellite_s_id(norad_id: int) -> int:
    conn = db_init.db_connect()
    try:
        row = conn.execute(
            "SELECT s_id FROM satellites WHERE norad_id = ?",
            (norad_id,),
        ).fetchone()
        assert row is not None
        return row["s_id"]
    finally:
        conn.close()


def test_list_satellites_seeded(client):
    response = client.get("/satellites")
    assert response.status_code == 200
    satellites = response.json()["satellites"]
    assert len(satellites) >= 1


def test_register_satellite_then_list(client):
    payload = {"norad_id": 99999, "s_name": "TEST SAT"}
    response = client.post("/satellites", json=payload)
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
    first = client.post("/satellites", json=payload)
    assert first.status_code == 201

    second = client.post("/satellites", json=payload)
    assert second.status_code == 409


def test_update_satellite_allows_name_only(client):
    norad_id = _create_satellite(client)
    response = client.patch(f"/satellites/{norad_id}/", json={"s_name": "NEW SAT NAME"})
    assert response.status_code == 200
    sat = response.json()["satellite"]
    assert sat["norad_id"] == norad_id
    assert sat["s_name"] == "NEW SAT NAME"


def test_update_satellite_rejects_non_name_fields(client):
    norad_id = _create_satellite(client)
    response = client.patch(f"/satellites/{norad_id}/", json={"tle_line1": "X"})
    assert response.status_code == 422


def test_update_satellite_rejects_empty_payload(client):
    norad_id = _create_satellite(client)
    response = client.patch(f"/satellites/{norad_id}/", json={})
    assert response.status_code == 400


def test_update_satellite_not_found(client):
    response = client.patch("/satellites/999999/", json={"s_name": "MISSING"})
    assert response.status_code == 404


def test_delete_satellite_returns_warning_header(client):
    norad_id = _create_satellite(client)
    response = client.delete(f"/satellites/{norad_id}")
    assert response.status_code == 200
    assert "Warning" in response.headers


def test_delete_satellite_blocked_by_active_reservation(client):
    norad_id = _create_satellite(client)
    s_id = _get_satellite_s_id(norad_id)
    gs_id = _create_groundstation(client)

    now = datetime.now(timezone.utc)
    pass_id = p_db.insert_n2yo_pass_return_id(
        s_id=s_id,
        gs_id=gs_id,
        max_elevation=45.0,
        duration=600,
        start_time=_utc_ts(now + timedelta(hours=1)),
        end_time=_utc_ts(now + timedelta(hours=2)),
    )
    assert pass_id is not None

    reserve = client.post("/reservations", json={"pass_id": pass_id})
    assert reserve.status_code == 200

    response = client.delete(f"/satellites/{norad_id}")
    assert response.status_code == 409

    _delete_groundstation_force(client, gs_id)


def test_delete_satellite_force_with_active_reservation(client):
    norad_id = _create_satellite(client)
    s_id = _get_satellite_s_id(norad_id)
    gs_id = _create_groundstation(client)

    now = datetime.now(timezone.utc)
    pass_id = p_db.insert_n2yo_pass_return_id(
        s_id=s_id,
        gs_id=gs_id,
        max_elevation=45.0,
        duration=600,
        start_time=_utc_ts(now + timedelta(hours=1)),
        end_time=_utc_ts(now + timedelta(hours=2)),
    )
    assert pass_id is not None

    reserve = client.post("/reservations", json={"pass_id": pass_id})
    assert reserve.status_code == 200

    response = client.delete(f"/satellites/{norad_id}", params={"force": True})
    assert response.status_code == 200
    assert "Warning" in response.headers
    assert response.json()["deleted_reservations"] == 1

    _delete_groundstation_force(client, gs_id)


def test_delete_satellite_not_found(client):
    response = client.delete("/satellites/999999")
    assert response.status_code == 404
