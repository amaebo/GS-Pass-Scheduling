from datetime import datetime, timedelta, timezone

import db.passes_db as p_db
import db.reservations_db as r_db
from db import db_init


def _utc_ts(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def test_delete_groundstation_response_shape(client):
    response = client.delete("/groundstations/3")
    assert response.status_code == 200
    data = response.json()
    assert "deleted_reservations" in data
    assert "deleted_reservations_count" not in data


def test_deactivate_groundstation_cancels_and_deletes(client):
    now = datetime.now(timezone.utc)
    reserved_pass_id = p_db.insert_n2yo_pass_return_id(
        s_id=1,
        gs_id=1,
        max_elevation=20.0,
        duration=600,
        start_time=_utc_ts(now + timedelta(hours=1)),
        end_time=_utc_ts(now + timedelta(hours=2)),
    )
    unreserved_pass_id = p_db.insert_n2yo_pass_return_id(
        s_id=1,
        gs_id=1,
        max_elevation=25.0,
        duration=300,
        start_time=_utc_ts(now + timedelta(hours=3)),
        end_time=_utc_ts(now + timedelta(hours=4)),
    )
    assert reserved_pass_id is not None
    assert unreserved_pass_id is not None

    r_id = r_db.create_reservation_with_commands(
        pass_id=reserved_pass_id,
        gs_id=1,
        s_id=1,
        mission_id=None,
        commands=[],
    )

    response = client.patch("/groundstations/1/", json={"status": "INACTIVE"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["ground station"]["status"] == "INACTIVE"
    assert payload["reservations_cancelled"] >= 1
    assert payload["passes_deleted"] >= 1

    conn = db_init.db_connect()
    try:
        row = conn.execute(
            "SELECT cancelled_at FROM reservations WHERE r_id = ?",
            (r_id,),
        ).fetchone()
    finally:
        conn.close()
    assert row is not None
    assert row["cancelled_at"] is not None
    assert p_db.get_pass_from_pass_id(unreserved_pass_id) is None
