import httpx
from fastapi import APIRouter, HTTPException
import sqlite3
import logging

import db.gs_db as gs_db
import db.satellites_db as sat_db
import db.passes_db as p_db
from src.services.n2yo_client import get_passes_from_n2yo

router = APIRouter()
logger = logging.getLogger("pass_routing")

@router.get("/passes")
def view_pass(norad_id: int, gs_id: int):
    # ----get satellite and ground station information----
    satellite = sat_db.get_satellite_by_norad_id(norad_id)
    gs = gs_db.get_gs_by_id(gs_id)

    if not gs:
        raise HTTPException(status_code=404, detail="Ground station not found.")
    if not satellite:
        raise HTTPException(status_code=404, detail="Satellite not found.")

    # ---- get passes fron n2yo api and add it to database (caches)-----
    try:
        n2yo_passes =  get_passes_from_n2yo(
            norad_id=norad_id,
            gs_lon=gs["lon"],
            gs_lat=gs["lat"],
            alt=gs["alt"],
            min_visibility=30,
            days=1,
            )
    # Error handling for NY20 API response erros using HTTPX
    except httpx.HTTPStatusError:
        raise HTTPException(status_code=502, detail="N2YO API request failed.")
    

    total_passes = len(n2yo_passes)
    passes_cached_count = 0 
    pass_ids = []
    
    # add new passes to the cache table, tracking passes cached and their pass_ids
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
        
        #log caching information
        logger.info(f"{passes_cached_count} new passes cached out of {total_passes} passes recieved by N2YO API. pass_ids: {pass_ids}")
    except sqlite3.Error:
        raise HTTPException (status_code = 502, detail = "Passes could not be added")
        
    # --- Delete expired passes from database (cache) ----------
    expired_passes= p_db.get_all_expired_passes()
    try:
        delete_count =p_db.delete_expired_passes()
    except sqlite3.Error:
        raise HTTPException (status_code = 500, detail = "Expired passes could not be deleted")

    logger.info(f"{delete_count} expired passes deleted from database/cache.")

    # ----- Return predicted passes to client ------
    rows = p_db.get_passes_by_gs_and_sat(satellite["s_id"], gs["gs_id"])
    final_passes = [dict(p) for p in rows]


    return{
        "passes": final_passes
    }
    
