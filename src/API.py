
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Satellite(BaseModel):
    norad_id: int
    s_name: str
    
# Satellite Registraion 
@app.post("/satellites/register")
def register_satellite(satellite: Satellite ):
    satellite_dict = satellite.model_dump()
    message = ""

    if satellite_dict["norad_id"] and satellite_dict["s_name"]:
        message = "Satellite registered"
    else:
        message = "Error: missing variables" 

    return {
        "message" : message,
        "satellite" : satellite_dict
    }