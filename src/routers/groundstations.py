import sqlite3
from fastapi import APIRouter, HTTPException

import db.gs_db as gs_db
from src.schemas import GroundStation


router = APIRouter()


@router.get("/groundstations")
def list_gs():
    try:
        rows = gs_db.get_all_gs()
        return {"ground stations": [dict(row) for row in rows]}
    except sqlite3.Error:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve ground stations."
        )


@router.post("/groundstations/register", status_code=201)
def register_gs(gs: GroundStation):
    try:
        lon = round(gs.lon, 5)
        lat = round(gs.lat, 5)

        gs_db.insert_gs_manual(gs.gs_code, lon, lat)
        return {
            "msg": "Ground station registered",
            "Ground Station": {"gs_code": gs.gs_code, "lon": lon, "lat": lat},
        }
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Ground Station already registered (duplicate gs_code or coordinates)."
        )
