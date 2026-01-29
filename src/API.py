
from fastapi import FastAPI
from pydantic import BaseModel, Field
from db.satellites_db import insert_new_satellite

app = FastAPI()

class Satellite(BaseModel):
    norad_id: int = Field(..., ge = 1)  # must be >= 1
    s_name: str = Field(..., min_length = 1)

# Satellite Registraion 
@app.post("/satellites/register")
def register_satellite(satellite: Satellite ):

    satellite_dict = satellite.model_dump()
    res = insert_new_satellite(satellite_dict["norad_id"], satellite_dict["s_name"])

    message = "Satellite registered" if res else "Failed to register satellite"

    return {
        "msg": message,
        "satellite": satellite_dict
    }