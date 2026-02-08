import logging
import sqlite3

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException

import db.gs_db as gs_db
import db.satellites_db as sat_db
import db.passes_db as p_db
from src.services.celestrak_client import get_tle
from src.services.predict_passes import get_pass_predictions
router = APIRouter()
logger = logging.getLogger("pass_routing")


def _parse_db_time(value: str) -> datetime:
    dt = datetime.fromisoformat(value)
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

def _format_db_time(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

def _tle_is_stale(satellite: sqlite3.Row, now_utc: datetime) -> bool:
    if not satellite["tle_line1"] or not satellite["tle_line2"]:
        return True
    updated_at = satellite["tle_updated_at"]
    if not updated_at:
        return True
    updated_dt = _parse_db_time(updated_at)
    return updated_dt < (now_utc - timedelta(hours=24))


@router.get("/passes")
def view_pass(norad_id: int, gs_id: int):
    # Fetch required entities
    satellite = sat_db.get_satellite_by_norad_id(norad_id)
    gs = gs_db.get_gs_by_id(gs_id)

    if not gs:
        raise HTTPException(status_code=404, detail="Ground station not found.")
    if gs["status"] != "ACTIVE":
        raise HTTPException(status_code=409, detail="Ground station is inactive.")
    if not satellite:
        raise HTTPException(status_code=404, detail="Satellite not found.")

    now_utc = datetime.now(timezone.utc)

    # Refresh TLE if older than 24 hours
    if _tle_is_stale(satellite, now_utc):
        logger.info(f"TLE stale for NORAD {norad_id}; refreshing from CelesTrak.")
        tle_line1, tle_line2 = get_tle(norad_id)
        tle_updated_at = _format_db_time(now_utc)
        try:
            sat_db.update_satellite_tle(
                satellite["s_id"],
                tle_line1,
                tle_line2,
                tle_updated_at,
            )
        except sqlite3.Error:
            raise HTTPException(status_code=500, detail="Failed to update TLE data.")
        satellite = sat_db.get_satellite_by_norad_id(norad_id)

    # Determine whether pass cache/database is stale
    refresh_threshold = now_utc + timedelta(hours=24)

    latest_row = p_db.get_latest_pass_end_time(gs["gs_id"], satellite["s_id"])
    latest_end_time = _parse_db_time(latest_row["end_time"]) if latest_row else None

    # Refresh cache from local prediction if needed
    if latest_end_time is None or latest_end_time < refresh_threshold:
        try:
            predicted_passes = get_pass_predictions(
                sat_name=satellite["s_name"],
                tle_line1=satellite["tle_line1"],
                tle_line2=satellite["tle_line2"],
                utc_time=now_utc,
                hours=24,
                gs_lon=gs["lon"],
                gs_lat=gs["lat"],
                gs_alt=gs["alt"],
            )
        except Exception:
            logger.exception("Pass prediction failed.")
            raise HTTPException(status_code=500, detail="Pass prediction failed.")

        total_passes = len(predicted_passes)
        passes_cached_count = 0
        pass_ids = []

        # Insert only new passes into cache
        try:
            for p in predicted_passes:
                pass_id = p_db.insert_predicted_pass_return_id(
                    satellite["s_id"],
                    gs["gs_id"],
                    p["max_elevation"],
                    p["duration"],
                    p["start_time"],
                    p["end_time"],
                    "pyorbital",
                )
                if pass_id:
                    pass_ids.append(pass_id)
                    passes_cached_count += 1

            logger.info(
                f"{passes_cached_count} new passes cached out of {total_passes} from local prediction. "
                f"pass_ids: {pass_ids}"
            )
        except sqlite3.Error:
            raise HTTPException(status_code=502, detail="Passes could not be added")

    # Housekeeping: remove expired passes
    try:
        exp_delete_count = p_db.delete_unreserved_expired_passes()
        logger.info(f"{exp_delete_count} expired passes deleted from cache.")
    except sqlite3.Error:
        raise HTTPException(status_code=500, detail="Expired passes could not be deleted")

    # Fetch final list of valid future passes
    rows = p_db.get_claimable_passes(
        satellite["s_id"],
        gs["gs_id"],
    )

    return {"passes": [dict(p) for p in rows]}
    
