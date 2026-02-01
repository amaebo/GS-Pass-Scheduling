import sqlite3
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

import db.satellites_db as sat_db


router = APIRouter()


class Satellite(BaseModel):
    norad_id: int = Field(..., ge=1)  # must be >= 1
    s_name: str = Field(..., min_length=1)


@router.get("/satellites")
def list_satellites():
    try:
        rows = sat_db.get_all_satellites(True)
        return {"satellites": [dict(row) for row in rows]}
    except sqlite3.Error:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve satellites."
        )


@router.post("/satellites/register", status_code=201)
def register_satellite(satellite: Satellite):
    try:
        sat_db.insert_new_satellite(satellite.norad_id, satellite.s_name)
        return {
            "msg": "Satellite registered",
            "satellite": satellite.model_dump(),
        }
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Satellite already registered (duplicate NORAD ID)."
        )
