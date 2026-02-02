import httpx
import logging
import sqlite3
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException

import db.gs_db as gs_db
import db.satellites_db as sat_db
import db.passes_db as p_db
from src.services.n2yo_client import get_passes_from_n2yo

router = APIRouter()
logger = logging.getLogger("pass_routing")


def _parse_db_time(value: str) -> datetime:
    dt = datetime.fromisoformat(value)
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


@router.get("/passes")
def view_pass(norad_id: int, gs_id: int):
    # ----get satellite and ground station information----
    satellite = sat_db.get_satellite_by_norad_id(norad_id)
    gs = gs_db.get_gs_by_id(gs_id)

    if not gs:
        raise HTTPException(status_code=404, detail="Ground station not found.")
    if not satellite:
        raise HTTPException(status_code=404, detail="Satellite not found.")

    now_utc = datetime.now(timezone.utc)
    refresh_threshold = now_utc + timedelta(hours=12)

    latest_row = p_db.get_latest_pass_end_time(gs["gs_id"], satellite["s_id"])
    latest_end_time = _parse_db_time(latest_row["end_time"]) if latest_row else None #convert current time zone time
    
    # -----Refresh cache if latest gs-sat pass is greater than 12 hours or no passes have been cached yet.--------
    if latest_end_time is None or latest_end_time < refresh_threshold:
        try:
            n2yo_passes = get_passes_from_n2yo(
                norad_id=norad_id,
                gs_lon=gs["lon"],
                gs_lat=gs["lat"],
                alt=gs["alt"],
                min_visibility=30,
                days=1,
            )
        except httpx.HTTPStatusError:
            raise HTTPException(status_code=502, detail="N2YO API request failed.")

        total_passes = len(n2yo_passes)
        passes_cached_count = 0
        pass_ids = []
        
        #add only new passes to cache
        try:
            for p in n2yo_passes:
                pass_id = p_db.insert_n2yo_pass_return_id(
                    satellite["s_id"],
                    gs["gs_id"],
                    p["start_time"],
                    p["end_time"],
                )
                if pass_id:
                    pass_ids.append(pass_id)
                    passes_cached_count += 1

            logger.info(
                f"{passes_cached_count} new passes cached out of {total_passes} passes received by N2YO API. "
                f"pass_ids: {pass_ids}"
            )
        except sqlite3.Error:
            raise HTTPException(status_code=502, detail="Passes could not be added")
        
    # Always remove expired passes to avoid unbounded cache growth.
    try:
        exp_delete_count = p_db.delete_expired_passes()
    except sqlite3.Error:
        raise HTTPException(status_code=500, detail="Expired passes could not be deleted")

    logger.info(f"{exp_delete_count} expired passes deleted from database/cache.")

    rows = p_db.get_all_future_passes(
        satellite["s_id"],
        gs["gs_id"],
    )
    final_passes = [dict(p) for p in rows]


    return{
        "passes": final_passes
    }
    
