
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import sqlite3
#database querying 
import db.satellites_db as sat_db
import db.gs_db as gs_db
import db.missions_db as miss_db

GS_CODE_REGEX = r"^[A-Z][A-Z0-9_]{2,49}$"  # 3–50 chars, all caps, with numbers or underscores allowed.

app = FastAPI()

# Pydantic models for API data modification
class Satellite(BaseModel):
    norad_id: int = Field(..., ge = 1)  # must be >= 1
    s_name: str = Field(..., min_length = 1)

class GroundStation(BaseModel):
    gs_code: str = Field(min_length=3, max_length=50, pattern=GS_CODE_REGEX)
    lon: float
    lat: float

class Mission(BaseModel):
    mission_name: str = Field(..., min_length = 1)
    owner: str | None = None
    priority: str | None = None

class MissionUpdate(BaseModel):
    mission_name: str | None = Field(None, min_length = 1)
    owner: str | None = None
    priority: str | None = None

# View all registered satellites
@app.get("/satellites")
def list_satellites():
    try:
        rows = sat_db.get_all_satellites()
                
        #convert rows to list of dictionaries (for json formatting)
        list_of_rows = [dict(row) for row in rows]
        return {
            "satellites": list_of_rows
            }
    except sqlite3.Error:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve satellites."
        )

# Satellite Registraion 
@app.post("/satellites/register", status_code=201)
def register_satellite(satellite: Satellite ):
    try:
        s_id = sat_db.insert_new_satellite(satellite.norad_id, satellite.s_name)
        message = "Satellite registered"
        return {
        "msg": message,
        "satellite": satellite.model_dump()
        }
    # handle duplicate entries 
    except sqlite3.IntegrityError:
        # UNIQUE constraint hit
        raise HTTPException(
            status_code=409,
            detail= "Satellite already registered (duplicate NORAD ID)."
        )
# View ground stations list
@app.get("/groundstations")
def list_gs():
    try:
        rows = gs_db.get_all_gs()
                
        #convert rows to list of dictionaries (for json formatting)
        list_of_rows = [dict(row) for row in rows]
        return {
            "ground stations": list_of_rows
            }
    except sqlite3.Error:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve ground stations."
        )
# Ground Station Registration 
@app.post("/groundstations/register", status_code = 201)
def register_gs(gs: GroundStation):
    try:
        #round to the nearest 
        lon = round(gs.lon,5)
        lat = round(gs.lat, 5)
        
        gs_id = gs_db.insert_gs_manual(gs.gs_code, lon, lat)
        message = "Ground station registered"
        return{
        "msg": message,
        "Ground Station": {"gs_code": gs.gs_code,
                        "lon": lon,
                        "lat": lat}
        }
    # handle duplicate entries 
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code = 409,
            detail = "Ground Station already registered (duplicate gs_code or coordinates)."
        )
    
# Create Misison
@app.post("/missions/create", status_code = 201)
def create_mission (mission: Mission):
    try:
        mission_id = miss_db.add_mission(mission.mission_name, mission.owner, mission.priority)
        mission_data = miss_db.get_mission_by_id(mission_id)
        return {
            "msg": "Mission created",
            "mission": mission_data
        }
    except sqlite3.Error:
        raise HTTPException(
            status_code=500,
            detail="Failed to create mission."
        )
# View the missions
@app.get("/missions")
def view_missions():
    try:
        rows = miss_db.get_all_missions()

        missions = [dict(row) for row in rows]
        return{
            "missions" : missions
        }
    except sqlite3.Error:
        raise HTTPException( 
            status_code = 500,
            details = "Failed to view mission"
            )
# Update this mission
@app.patch("/mission/update/{mission_id}")
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
            "mission": dict(updated) if updated else None
        }
    except sqlite3.Error:
        raise HTTPException(
            status_code=500,
            detail="Failed to update mission."
        )
    
# Delete misssion
@app.delete("/missions/delete/{mission_id}")
def delete_mission(mission_id: int):
    try:
        #check if mission exists
        mission = miss_db.get_mission_by_id(mission_id)

        if mission:
            miss_db.delete_mission(mission_id)
            return{
                "msg": "Mission deleted",
                "Mission": dict(mission)
            }
        else:
            raise HTTPException(
            status_code=404,
            detail= "Mission (mission_id) not found"
        )        
    except sqlite3.Error as e:
        print(type(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to delete mission."
        )
    #TODO: Handle foreign key constraint exception for satellites connected to mission

# Add satellite to mission.
@app.post("/mission/{mission_id}/satellites/{s_id}")
def add_sat_to_mission(mission_id: int, s_id: int):
    #check if mission and satellite exists 
    mission = miss_db.get_mission_by_id(mission_id)
    satellite = sat_db.get_satellite_by_id(s_id)

    if mission:
        if satellite:
            try:
                miss_db.add_sat_mission(mission_id, s_id)
                mission_satellites = miss_db.get_all_sats_in_mission(mission_id)

                return{
                    "msg": f"Satellite added to mission",
                    "mission_id": mission_id, 
                    "mission_name": mission["mission_name"],
                    "mission_satellites": [dict(row) for row in mission_satellites]
                }
            
            except sqlite3.IntegrityError as e:
                print(e)
                raise HTTPException(
                    status_code = 500,
                    detail = "Satellite already added to mission"
                )
        else:
            raise HTTPException(
            status_code=404,
            detail="Satellite not found"
            )
    
    else:
        raise HTTPException(
            status_code=404,
            detail="Mission not found"
            )

#View all satellites part of a misison 
@app.get("/mission/{mission_id}/satellites")
def view_mission_satellites(mission_id: int):
    #check if mission exists 
    mission = miss_db.get_mission_by_id(mission_id)

    if mission:
        satellites = miss_db.get_all_sats_in_mission(mission_id)
        return {
            "satellites" : [dict(row) for row in satellites]
        }
    else:
        raise HTTPException(
            status_code=404,
            detail="Mission not found"
            )
