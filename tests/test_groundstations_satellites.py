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
    rows = listing.json()["ground_stations"]
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
    rows = listing.json()["ground_stations"]
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
    rows = listing.json()["ground_stations"]
    match = next((gs for gs in rows if gs["gs_code"] == gs_code), None)
    assert match is not None
    return match["gs_id"]


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


def test_create_groundstation_defaults_active_status(client):
    gs_id = _create_groundstation_no_status(client)
    listing = client.get("/groundstations")
    assert listing.status_code == 200
    rows = listing.json()["ground_stations"]
    match = next((gs for gs in rows if gs["gs_id"] == gs_id), None)
    assert match is not None
    assert match["status"] == "ACTIVE"


def test_create_groundstation_with_active_status(client):
    gs_id = _create_groundstation_active_status(client)
    listing = client.get("/groundstations")
    assert listing.status_code == 200
    rows = listing.json()["ground_stations"]
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
        r_id = reserve.json()["reservation"]["r_id"]

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
    assert "Warning" in response.headers
    assert response.json()["deleted_reservations"] == 0

    listing = client.get("/groundstations")
    assert listing.status_code == 200
    rows = listing.json()["ground_stations"]
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
    r_id = reserve.json()["reservation"]["r_id"]

    cancel = client.post(f"/reservations/{r_id}/cancel")
    assert cancel.status_code == 200

    response = client.delete(f"/groundstations/{gs_id}")
    assert response.status_code == 200
    assert "Warning" in response.headers

    listing = client.get("/groundstations")
    assert listing.status_code == 200
    rows = listing.json()["ground_stations"]
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
    assert "Warning" in response.headers
    assert response.json()["deleted_reservations"] == 1

    listing = client.get("/groundstations")
    assert listing.status_code == 200
    rows = listing.json()["ground_stations"]
    assert all(gs["gs_id"] != gs_id for gs in rows)


def test_update_groundstation_allows_code_and_status_only(client):
    gs_id = _create_groundstation(client)
    response = client.patch(
        f"/groundstations/{gs_id}/",
        json={"gs_code": f"UPDATED_{gs_id}", "status": "INACTIVE"},
    )
    assert response.status_code == 200
    updated = response.json()["ground_station"]
    assert updated["gs_code"] == f"UPDATED_{gs_id}"
    assert updated["status"] == "INACTIVE"


def test_update_groundstation_status_normalized(client):
    gs_id = _create_groundstation(client)
    response = client.patch(
        f"/groundstations/{gs_id}/",
        json={"status": "inactive"},
    )
    assert response.status_code == 200
    updated = response.json()["ground_station"]
    assert updated["status"] == "INACTIVE"

def test_update_groundstation_inactive_cancels_reservations_and_deletes_passes(client):
    gs_id = _create_groundstation(client)
    now = datetime.now(timezone.utc)
    reserved_pass_id = p_db.insert_n2yo_pass_return_id(
        s_id=1,
        gs_id=gs_id,
        max_elevation=45.0,
        duration=600,
        start_time=_utc_ts(now + timedelta(hours=1)),
        end_time=_utc_ts(now + timedelta(hours=2)),
    )
    assert reserved_pass_id is not None
    unreserved_pass_id = p_db.insert_n2yo_pass_return_id(
        s_id=1,
        gs_id=gs_id,
        max_elevation=35.0,
        duration=500,
        start_time=_utc_ts(now + timedelta(hours=3)),
        end_time=_utc_ts(now + timedelta(hours=4)),
    )
    assert unreserved_pass_id is not None

    reserve = client.post("/reservations", json={"pass_id": reserved_pass_id})
    assert reserve.status_code == 200
    r_id = reserve.json()["reservation"]["r_id"]

    response = client.patch(
        f"/groundstations/{gs_id}/",
        json={"status": "INACTIVE"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload.get("reservations_cancelled") == 1
    assert payload.get("passes_deleted") == 1

    reservations = client.get("/reservations", params={"include_cancelled": True})
    assert reservations.status_code == 200
    rows = reservations.json()["reservations"]
    match = next((r for r in rows if r["r_id"] == r_id), None)
    assert match is not None
    assert match["status"] == "CANCELLED"

    conn = db_init.db_connect()
    try:
        remaining = conn.execute(
            "SELECT pass_id FROM predicted_passes WHERE gs_id = ?",
            (gs_id,),
        ).fetchall()
        remaining_ids = {row["pass_id"] for row in remaining}
        assert remaining_ids == {reserved_pass_id}
    finally:
        conn.close()


def test_reservation_blocked_for_inactive_groundstation(client):
    gs_id = _create_groundstation(client)
    response = client.patch(
        f"/groundstations/{gs_id}/",
        json={"status": "INACTIVE"},
    )
    assert response.status_code == 200

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
    assert reserve.status_code == 409


def test_update_groundstation_rejects_location_changes(client):
    gs_id = _create_groundstation(client)
    response = client.patch(f"/groundstations/{gs_id}/", json={"lat": 40.0})
    assert response.status_code == 422


def test_update_groundstation_rejects_empty_payload(client):
    gs_id = _create_groundstation(client)
    response = client.patch(f"/groundstations/{gs_id}/", json={})
    assert response.status_code == 400


def test_update_groundstation_not_found(client):
    response = client.patch("/groundstations/999999/", json={"gs_code": "NOT_FOUND"})
    assert response.status_code == 404


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


def test_delete_groundstation_not_found(client):
    response = client.delete("/groundstations/999999")
    assert response.status_code == 404


def test_delete_satellite_not_found(client):
    response = client.delete("/satellites/999999")
    assert response.status_code == 404
