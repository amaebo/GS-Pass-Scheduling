
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import sqlite3
#database querying 
import db.satellites_db as sat_db
import db.gs_db as gs_db


app = FastAPI()

# Pydantic Model for API
class Satellite(BaseModel):
    norad_id: int = Field(..., ge = 1)  # must be >= 1
    s_name: str = Field(..., min_length = 1)

class GroundStation(BaseModel):
    gs_name: str = Field(..., min_length = 1)
    lon: float
    lat: float
    

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
