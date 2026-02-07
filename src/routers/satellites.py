import sqlite3
from fastapi import APIRouter, HTTPException, Response

import db.satellites_db as sat_db

from src.schemas import Satellite, SatelliteUpdate


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

@router.patch("/satellites/{norad_id}/")
def update_satellite(norad_id: int, sat_updates: SatelliteUpdate):
    satellite = sat_db.get_satellite_by_norad_id(norad_id)
    if satellite is None:
        raise HTTPException(status_code=404, detail="Satellite not found.")

    updates = {k: v for k, v in sat_updates.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No updatable fields provided.")
    if set(updates) - {"s_name"}:
        raise HTTPException(
            status_code=400,
            detail="Only s_name can be updated. Create a new satellite to change other fields."
        )

    try:
        sat_db.update_satellite(satellite["s_id"], updates)
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Satellite update already exists.")
    except sqlite3.Error:
        raise HTTPException(status_code=500, detail="Unable to update satellite.")

    return {
        "msg": "Satellite updated",
        "satellite": dict(sat_db.get_satellite_by_id(satellite["s_id"]))
    }

@router.delete("/satellites/{norad_id}")
def delete_satellite(norad_id: int, response: Response, force: bool = False):
    satellite = sat_db.get_satellite_by_norad_id(norad_id)

    if satellite is None:
        raise HTTPException(status_code=404, detail= "Satellite not found.")
    
    s_id = satellite["s_id"]
    if not force:
        # check if satellite has non-cancelled, uncompleted reservation 
        if sat_db.sat_has_active_reservations(s_id):
            raise HTTPException(status_code=409, detail="Please cancel reservations associated with this satellite first.")
    
    try:
        reservations_deleted, deleted = sat_db.delete_satellite_and_reservations(s_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Satellite not found.")
        response.headers["Warning"] = (
            "Deletion removes predicted passes and reservations."
        )
        return {
            "msg": "Satellite deleted. All corresponding reservations deleted",
            "norad_id": norad_id,
            "deleted_reservations": reservations_deleted,
        }
    except sqlite3.Error:
        raise HTTPException(status_code=500, detail="Failed to delete satellite")
