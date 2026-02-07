from datetime import datetime, timedelta, timezone
import time

import db.passes_db as p_db
from db import db_init


def _utc_ts(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _clear_passes_and_reservations_for_gs(gs_id: int):
    conn = db_init.db_connect()
    try:
        conn.execute("DELETE FROM reservations WHERE gs_id = ?", (gs_id,))
        conn.execute("DELETE FROM predicted_passes WHERE gs_id = ?", (gs_id,))
        conn.commit()
    finally:
        conn.close()


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
    rows = listing.json()["ground stations"]
    match = next((gs for gs in rows if gs["gs_code"] == gs_code), None)
    assert match is not None
    return match["gs_id"]


def _create_groundstation(client) -> int:
    return _create_groundstation_no_status(client)


def _create_groundstation_invalid_status(client) -> int | None:
    ms = int(time.time() * 1000)
    gs_code = f"TEST_GS_{ms}"
    lat = 39.0 + (ms % 1000) / 10000
    lon = -105.0 - (ms % 1000) / 10000
    alt = 1600.0 + (ms % 100) / 10
    status = "INVALID_STATUS"
    response = client.post(
        "/groundstations",
        json={"gs_code": gs_code, "lat": lat, "lon": lon, "alt": alt, "status": status},
    )
    assert response.status_code == 409

    listing = client.get("/groundstations")
    assert listing.status_code == 200
    rows = listing.json()["ground stations"]
    match = next((gs for gs in rows if gs["gs_code"] == gs_code), None)
    assert match is None
    return None


def _create_groundstation_active_status(client) -> int:
    ms = int(time.time() * 1000)
    gs_code = f"TEST_GS_{ms}"
    lat = 39.0 + (ms % 1000) / 10000
    lon = -105.0 - (ms % 1000) / 10000
    alt = 1600.0 + (ms % 100) / 10
    status = "ACTIVE"
    response = client.post(
        "/groundstations",
        json={"gs_code": gs_code, "lat": lat, "lon": lon, "alt": alt, "status": status},
    )
    assert response.status_code == 201

    listing = client.get("/groundstations")
    assert listing.status_code == 200
    rows = listing.json()["ground stations"]
    match = next((gs for gs in rows if gs["gs_code"] == gs_code), None)
    assert match is not None
    return match["gs_id"]


def _delete_groundstation_force(client, gs_id: int):
    client.delete(f"/groundstations/{gs_id}", params={"force": True})


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


def test_create_groundstation_defaults_active_status(client):
    gs_id = _create_groundstation_no_status(client)
    listing = client.get("/groundstations")
    assert listing.status_code == 200
    rows = listing.json()["ground stations"]
    match = next((gs for gs in rows if gs["gs_id"] == gs_id), None)
    assert match is not None
    assert match["status"] == "ACTIVE"


def test_create_groundstation_with_active_status(client):
    gs_id = _create_groundstation_active_status(client)
    listing = client.get("/groundstations")
    assert listing.status_code == 200
    rows = listing.json()["ground stations"]
    match = next((gs for gs in rows if gs["gs_id"] == gs_id), None)
    assert match is not None
    assert match["status"] == "ACTIVE"


def test_create_groundstation_invalid_status_rejected(client):
    gs_id = _create_groundstation_invalid_status(client)
    assert gs_id is None


def test_delete_groundstation_blocked_by_active_reservation(client):
    gs_id = _create_groundstation(client)
    r_id = None
    try:
        now = datetime.now(timezone.utc)
        pass_id = p_db.insert_n2yo_pass_return_id(
            s_id=1,
            gs_id=gs_id,
            max_elevation=45.0,
            duration=600,
            start_time=_utc_ts(now + timedelta(hours=1)),
            end_time=_utc_ts(now + timedelta(hours=2)),
        )
        assert pass_id is not None

        reserve = client.post("/reservations", json={"pass_id": pass_id})
        assert reserve.status_code == 200
        r_id = reserve.json()["Reservation"]["r_id"]

        response = client.delete(f"/groundstations/{gs_id}")
        assert response.status_code == 409
    finally:
        if r_id is not None:
            client.post(f"/reservations/{r_id}/cancel")
        _delete_groundstation_force(client, gs_id)


def test_delete_groundstation_no_reservations(client):
    gs_id = _create_groundstation(client)
    response = client.delete(f"/groundstations/{gs_id}")
    assert response.status_code == 200

    listing = client.get("/groundstations")
    assert listing.status_code == 200
    rows = listing.json()["ground stations"]
    assert all(gs["gs_id"] != gs_id for gs in rows)


def test_delete_groundstation_cancelled_reservation_allows_delete(client):
    gs_id = _create_groundstation(client)
    now = datetime.now(timezone.utc)
    pass_id = p_db.insert_n2yo_pass_return_id(
        s_id=1,
        gs_id=gs_id,
        max_elevation=45.0,
        duration=600,
        start_time=_utc_ts(now + timedelta(hours=1)),
        end_time=_utc_ts(now + timedelta(hours=2)),
    )
    assert pass_id is not None

    reserve = client.post("/reservations", json={"pass_id": pass_id})
    assert reserve.status_code == 200
    r_id = reserve.json()["Reservation"]["r_id"]

    cancel = client.post(f"/reservations/{r_id}/cancel")
    assert cancel.status_code == 200

    response = client.delete(f"/groundstations/{gs_id}")
    assert response.status_code == 200

    listing = client.get("/groundstations")
    assert listing.status_code == 200
    rows = listing.json()["ground stations"]
    assert all(gs["gs_id"] != gs_id for gs in rows)


def test_delete_groundstation_force_with_active_reservation(client):
    gs_id = _create_groundstation(client)
    now = datetime.now(timezone.utc)
    pass_id = p_db.insert_n2yo_pass_return_id(
        s_id=1,
        gs_id=gs_id,
        max_elevation=45.0,
        duration=600,
        start_time=_utc_ts(now + timedelta(hours=1)),
        end_time=_utc_ts(now + timedelta(hours=2)),
    )
    assert pass_id is not None

    reserve = client.post("/reservations", json={"pass_id": pass_id})
    assert reserve.status_code == 200

    response = client.delete(f"/groundstations/{gs_id}", params={"force": True})
    assert response.status_code == 200

    listing = client.get("/groundstations")
    assert listing.status_code == 200
    rows = listing.json()["ground stations"]
    assert all(gs["gs_id"] != gs_id for gs in rows)
