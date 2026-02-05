from fastapi import APIRouter, HTTPException
import sqlite3
from src.schemas import ReservationCreate
import db.passes_db as p_db
import db.missions_db as m_db
import db.satellites_db as sat_db
import db.reservations_db as r_db
router = APIRouter()

@router.post("/reservations")
def create_reservation(reservation:ReservationCreate):
    pass_id = reservation.pass_id
    mission_id = reservation.mission_id
    commands = reservation.commands
    
    # check if pass_id exists and is claimable
    if not p_db.check_claimable_pass(pass_id):
        raise HTTPException(status_code= 404, details= "Pass ID not found")
    
    pass_info = p_db.get_pass_from_pass_id(pass_id)
    gs_id = pass_info["gs_id"]
    s_id = pass_info["s_id"]

    # if client gives mission, check if satellite in pass is part of the misison 
    
    if mission_id:
        #check if mission exists
        if not m_db.check_mission_exists(mission_id):
            raise HTTPException(status_code=404, detail= f"Mission ({mission_id}) not be found")
        
        #check if satellite in pass is part of mission 
        sat = sat_db.get_satellite_by_id(s_id)

        if not m_db.check_sat_exist_in_mission(s_id,mission_id):
            raise HTTPException(status_code= 404, detail= f"Satellite ({sat["norad_id"]}) not found in mission. Add satellite to misison to reserve this pass to mission.")

    r_id = r_db.insert_reservation(pass_id, gs_id, s_id, mission_id)

    #add commands
    if commands:
            for command in reservation.commands:
                try:
                    r_db.add_command_to_reservation(r_id, command)
                except sqlite3.Error:
                     raise HTTPException (status_code=500, detail= f"Failed to add '{command}' command to reservation. Please make you choose commands from the catalog. ")

            

