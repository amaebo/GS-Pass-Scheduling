import sqlite3
from fastapi import APIRouter, HTTPException, Response
from src.schemas import GSUpdate

import db.gs_db as gs_db
from src.schemas import GroundStation


router = APIRouter()


@router.get("/groundstations")
def list_gs():
    try:
        rows = gs_db.get_all_gs()
        return {"ground_stations": [dict(row) for row in rows]}
    except sqlite3.Error:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve ground stations."
        )

#add a groundstation
@router.post("/groundstations", status_code=201)
def register_gs(gs: GroundStation):
    try:
        lon = round(gs.lon, 5)
        lat = round(gs.lat, 5)
        alt = round(gs.alt, 2)
        status = gs.status.upper()

        if status not in ("ACTIVE","INACTIVE"):
            raise HTTPException(status_code=409, detail="Status must be 'ACTIVE' or 'INACTIVE'")

        gs_db.insert_gs_manual(gs.gs_code, lon, lat, alt, status)
        return {
            "msg": "Ground station registered",
            "ground_station": {"gs_code": gs.gs_code, "lon": lon, "lat": lat, "alt": alt, "status": gs.status},
        }
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Ground Station already registered (duplicate gs_code or coordinates)."
        )

# Update ground stations
@router.patch("/groundstations/{gs_id}/")
def update_gs(gs_id:int,gs_updates: GSUpdate):
    gs = gs_db.get_gs_by_id(gs_id)
    if not gs:
        raise HTTPException(status_code= 404, detail="Ground station not found")
    
    updates = {key: value for key, value in gs_updates.model_dump().items() if value is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No updatable fields provided.")

    if set(updates) - {"gs_code", "status"}:
        raise HTTPException(status_code=400, detail="Only gs_code and status can be updated.")

    if "status" in updates:
        status = updates["status"].upper()
        if status not in ("ACTIVE", "INACTIVE"):
            raise HTTPException(status_code=400, detail="Status must be 'ACTIVE' or 'INACTIVE'.")
        updates["status"] = status
    deactivating = (
        updates.get("status") == "INACTIVE" and gs["status"] != "INACTIVE"
    )
    try:
        cancelled = 0
        deleted_passes = 0
        if deactivating:
            _, cancelled, deleted_passes = gs_db.update_gs_with_deactivation(gs_id, updates)
        else:
            gs_db.update_gs(gs_id, updates)
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="gs_code or (lat,lon) coordinates already exist.")
    except sqlite3.Error:
        raise HTTPException(status_code=500, detail="Unable to update ground station.")
    payload = {
        "msg": "Ground stations updated",
        "ground_station": dict(gs_db.get_gs_by_id(gs_id))
    }
    if deactivating:
        payload["reservations_cancelled"] = cancelled
        payload["passes_deleted"] = deleted_passes
    return payload
#delete groundstation along with history of all gs reservations 
@router.delete("/groundstations/{gs_id}")
def delete_gs(gs_id: int, response: Response, force: bool = False):
    gs = gs_db.get_gs_by_id(gs_id)
    if not gs:
        raise HTTPException(status_code=404, detail="Ground station not found.")
    
    if not force:
        if gs_db.gs_has_active_reservations(gs_id):
            raise HTTPException(status_code=409, detail="Please cancel reservations associated with groundstations first.")
    
    try:
        reservations_deleted, deleted = gs_db.delete_gs_and_reservations(gs_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Ground station not found.")
        response.headers["Warning"] = (
            "Deletion removes predicted passes and reservations."
        )
        return {
            "msg": "Ground station deleted. All corresponding reservations deleted",
            "gs_id": gs_id,
            "deleted_reservations": reservations_deleted,
        }
    except sqlite3.Error:
        raise HTTPException(status_code=500, detail="Failed to delete ground station.")
