import sqlite3
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

import db.gs_db as gs_db


router = APIRouter()

GS_CODE_REGEX = r"^[A-Z][A-Z0-9_]{2,49}$"  # 3–50 chars, all caps, with numbers or underscores allowed.


class GroundStation(BaseModel):
    gs_code: str = Field(min_length=3, max_length=50, pattern=GS_CODE_REGEX)
    lon: float
    lat: float


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
