import sqlite3
from fastapi import APIRouter, HTTPException

import db.missions_db as miss_db
import db.satellites_db as sat_db
from src.schemas import Mission, MissionUpdate


router = APIRouter()


@router.post("/missions/create", status_code=201)
def create_mission(mission: Mission):
    try:
        mission_id = miss_db.add_mission(mission.mission_name, mission.owner, mission.priority)
        mission_data = miss_db.get_mission_by_id(mission_id)
        return {"msg": "Mission created", "mission": mission_data}
    except sqlite3.Error:
        raise HTTPException(
            status_code=500,
            detail="Failed to create mission."
        )


@router.get("/missions")
def view_missions():
    try:
        rows = miss_db.get_all_missions()
        missions = [dict(row) for row in rows]
        return {"missions": missions}
    except sqlite3.Error:
        raise HTTPException(
            status_code=500,
            detail="Failed to view mission"
        )


@router.patch("/missions/update/{mission_id}")
def update_mission(mission_id: int, mission: MissionUpdate):
    updates = mission.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(
            status_code=400,
            detail="No fields provided to update."
        )

    try:
        existing = miss_db.get_mission_by_id(mission_id)
        if existing is None:
            raise HTTPException(
                status_code=404,
                detail="Mission not found."
            )

        miss_db.update_mission(mission_id, updates)
        updated = miss_db.get_mission_by_id(mission_id)
        return {
            "msg": "Mission updated",
            "mission": dict(updated) if updated else None,
        }
    except sqlite3.Error:
        raise HTTPException(
            status_code=500,
            detail="Failed to update mission."
        )


@router.delete("/missions/delete/{mission_id}")
def delete_mission(mission_id: int):
    try:
        mission = miss_db.get_mission_by_id(mission_id)
        if mission:
            miss_db.delete_mission(mission_id)
            return {"msg": "Mission deleted", "Mission": dict(mission)}
        raise HTTPException(
            status_code=404,
            detail="Mission (mission_id) not found"
        )
    except sqlite3.Error:
        raise HTTPException(
            status_code=500,
            detail="Failed to delete mission."
        )


@router.post("/missions/{mission_id}/satellites/{norad_id}")
def add_sat_to_mission(mission_id: int, norad_id: int):
    mission = miss_db.get_mission_by_id(mission_id)
    satellite = sat_db.get_satellite_by_norad_id(norad_id)

    if mission:
        if satellite:
            try:
                miss_db.add_sat_mission(mission_id, satellite["s_id"])
                mission_satellites = miss_db.get_all_sats_in_mission(mission_id)

                return {
                    "msg": "Satellite added to mission",
                    "mission_id": mission_id,
                    "mission_name": mission["mission_name"],
                    "mission_satellites": [dict(row) for row in mission_satellites],
                }
            except sqlite3.IntegrityError as e:
                print(e)
                raise HTTPException(
                    status_code=500,
                    detail="Satellite already added to mission"
                )
        raise HTTPException(
            status_code=404,
            detail="Satellite not found"
        )

    raise HTTPException(
        status_code=404,
        detail="Mission not found"
    )


@router.get("/missions/{mission_id}/satellites")
def view_mission_satellites(mission_id: int):
    mission = miss_db.get_mission_by_id(mission_id)

    if mission:
        satellites = miss_db.get_all_sats_in_mission(mission_id)
        return {"satellites": [dict(row) for row in satellites]}

    raise HTTPException(
        status_code=404,
        detail="Mission not found"
    )


@router.delete("/missions/{mission_id}/satellites/{norad_id}")
def remove_sat_from_mission(mission_id: int, norad_id: int):
    mission = miss_db.get_mission_by_id(mission_id)
    satellite = sat_db.get_satellite_by_norad_id(norad_id)

    if mission:
        if satellite:
            res = miss_db.delete_sat_from_mission(mission_id, satellite["s_id"])

            if not res:
                raise HTTPException(
                    status_code=404,
                    detail=f"Statellite ({norad_id}) not part of mission ({mission_id})"
                )

            return {
                "msg": f"Satellite ({norad_id}) was removed from mission ({mission_id}).",
                "Mission satellites": [dict(row) for row in miss_db.get_all_sats_in_mission(mission_id)],
            }

    raise HTTPException(status_code=404, detail="Mission not found.")
