import sqlite3
from fastapi import APIRouter, HTTPException

import db.gs_db as gs_db
import db.reservations_db as r_db
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
        alt = round(gs.alt, 2)

        gs_db.insert_gs_manual(gs.gs_code, lon, lat, alt)
        return {
            "msg": "Ground station registered",
            "Ground Station": {"gs_code": gs.gs_code, "lon": lon, "lat": lat, "alt": alt},
        }
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Ground Station already registered (duplicate gs_code or coordinates)."
        )

#delete groundstation along with history of all gs reservations 
@router.delete("/groundstations/{gs_id}")
def delete_gs(gs_id: int, force: bool = False):
    gs = gs_db.get_gs_by_id(gs_id)
    if not gs:
        raise HTTPException(status_code=404, detail="Ground station not found.")
    
    if not force:
        if gs_db.gs_has_active_reservations(gs_id):
            raise HTTPException(status_code=500, detail="Please cancel reservations associated with groundstations first.")
    
    
    try:
        #delete all reservations, cancelled or otherwise
        r_db.delete_reservations_by_gs_id(gs_id) #reservations must be deleted for associated passes to be deleted
        deleted = gs_db.delete_gs_by_id(gs_id) # deletions should cascade to passes database/cache
        if not deleted:
            raise HTTPException(status_code=404, detail="Ground station not found.")
        return {"msg": "Ground station deleted. Corresponding reservations deleted", "gs_id": gs_id}
    except sqlite3.Error:
        raise HTTPException(status_code=500, detail="Failed to delete ground station.")
