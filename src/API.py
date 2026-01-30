
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import sqlite3
#database querying 
import db.satellites_db as sat_db
import db.gs_db as gs_db

GS_CODE_REGEX = r"^[A-Z][A-Z0-9_]{2,49}$"  # 3–50 chars, all caps, with numbers or underscores allowed.

app = FastAPI()

# Pydantic Model for API
class Satellite(BaseModel):
    norad_id: int = Field(..., ge = 1)  # must be >= 1
    s_name: str = Field(..., min_length = 1)

class GroundStation(BaseModel):
    gs_code: str = Field(min_length=3, max_length=50, pattern=GS_CODE_REGEX)
    lon: float
    lat: float
    
#TODO: Implement list of satellite view 
@app.get("/satellites")
def list_satellites():
    pass

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
@app.get("/groundstations/view")
def list_gs():
    try:
        rows = gs_db.get_all_gs()
                
        #convert rows to list of dictionaries (for json formatting)
        list_of_rows = [dict(row) for row in rows]
        return {
            "ground stations": list_of_rows
            }
    except sqlite3.Error as e:
        raise
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
    
