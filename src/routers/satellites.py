import sqlite3
from fastapi import APIRouter, HTTPException

import db.satellites_db as sat_db
import db.reservations_db as r_db

from src.schemas import Satellite


router = APIRouter()


@router.get("/satellites")
def list_satellites():
    try:
        rows = sat_db.get_all_satellites()
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

@router.delete("/satellites/{norad_id}")
def delete_satellite(norad_id: int, force: bool = False):
    satellite = sat_db.get_satellite_by_norad_id(norad_id)

    if satellite is None:
        raise HTTPException(status_code=404, detail= "Satellite not found.")
    
    s_id = satellite["s_id"]
    if not force:
        # check if satellite has non-cancelled, uncompleted reservation 
        if sat_db.sat_has_active_reservations(s_id):
            raise HTTPException(status_code=409, detail="Please cancel reservations associated with groundstations first.")
    
    try:
        #delete reservations
        r_db.delete_reservations_by_s_id(s_id)
        #delete satellites
        deleted = sat_db.delete_satellite_by_s_id(s_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Satellite not found.")
        return {"msg": "Satellite deleted. All corresponding reservations deleted", "norad_id": norad_id}
    except sqlite3.Error:
        raise HTTPException(status_code=500, detail="Failed to delete satellite")
