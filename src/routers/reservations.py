from fastapi import APIRouter, HTTPException
import sqlite3
from datetime import datetime, timezone

from src.schemas import ReservationCreate
import db.passes_db as p_db
import db.missions_db as m_db
import db.satellites_db as sat_db
import db.reservations_db as r_db

router = APIRouter()

def compute_reservation_status(r_id: int):
    pass_id = p_db.get_pass_id_from_r_id
    p = p_db.get_pass_from_pass_id(pass_id)
    reservation = r_db.get_reservation_by_r_id(r_id)
    start_time = datetime.strptime(p["start_time"],"%Y-%m-%d %H:%M:%S")
    end_time = datetime.strptime(p["end_time"],"%Y-%m-%d %H:%M:%S")
    cur_time = datetime.now(timezone.utc)
    
    if reservation["cancelled_at"]:
        status = "CANCELLED"
    elif start_time > cur_time:
        status = "RESERVED"
    elif start_time < cur_time and end_time > cur_time:
        status = "ACTIVE"
    elif end_time < cur_time:
        status = "COMPLETE"
    
    return status

@router.post("/reservations")
def create_reservation(reservation:ReservationCreate):
    pass_id = reservation.pass_id
    mission_id = reservation.mission_id
    commands = reservation.commands
    
    if not p_db.pass_exists(pass_id):
        raise HTTPException(status_code=404, detail="Pass ID not found")
    if p_db.pass_has_active_reservation(pass_id):
        raise HTTPException(status_code=409, detail="Pass is already reserved")
    if not p_db.pass_is_future(pass_id):
        raise HTTPException(status_code=400, detail="Pass is no longer claimable")
    
    pass_info = p_db.get_pass_from_pass_id(pass_id)
    gs_id = pass_info["gs_id"]
    s_id = pass_info["s_id"]
    sat = sat_db.get_satellite_by_id(s_id)
    # if client gives mission, check if mission exists and if satellite is in mission
    if mission_id is not None:
        #check if mission exists
        if not m_db.check_mission_exists(mission_id):
            raise HTTPException(status_code=404, detail=f"Mission ({mission_id}) not found")
        
        #check if satellite is in mission 
        if not m_db.check_sat_exist_in_mission(s_id, mission_id):
            norad_id = sat["norad_id"]
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Satellite ({norad_id}) not found in mission. "
                    "Add satellite to mission to reserve this pass to mission."
                ),
            )
    
    # Check if commands are valid
    if commands:
        allowed = c_db.get_command_types()
        invalid = [cmd for cmd in commands if cmd not in allowed]
        if invalid:
            invalid_list = ", ".join(invalid)
            raise HTTPException(
                status_code=400,
                detail=f"Invalid command(s): {invalid_list}",
            )
        if len(commands) != len(set(commands)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate commands are not allowed",
            )
    #Create reservaion with commands
    try:
        r_id = r_db.create_reservation_with_commands(
            pass_id=pass_id,
            gs_id=gs_id,
            s_id=s_id,
            mission_id=mission_id,
            commands=commands,
        )
    except sqlite3.Error:
        raise HTTPException(status_code=500, detail="Reservation could not be made.")

    reservation_info = r_db.get_reservation_with_details_by_r_id(r_id)
    command_list = (
        reservation_info["commands"].split(",")
        if reservation_info and reservation_info["commands"]
        else []
    )
    
    return{
        "msg": "Pass has been reserved.",
        "Reservation": {"r_id": r_id,
                       "mission_id": mission_id,
                       "pass_id": pass_id,
                       "gs_id": reservation_info["gs_id"],
                       "norad_id": reservation_info["norad_id"],
                       "start_time": reservation_info["start_time"],
                       "end_time": reservation_info["end_time"],
                        "commands": command_list,
                        "created_at":reservation_info["created_at"]} }

#view all registrations 
@router.get("/reservations")
def view_reservations(include_cancelled: bool = False):
    #get reservations and commands
    try:
        reservations = r_db.get_reservations_with_details(include_cancelled=include_cancelled)
        commands_rows = r_db.get_reservation_commands_grouped()
    except sqlite3.Error:
        raise HTTPException(status_code=500, detail="Unable to get reservations")

    #create a dictionary of commands by r_id
    commands_by_rid: dict[int, list[str]] = {}
    for row in commands_rows:
        commands = row["commands"].split(",") if row["commands"] else []
        commands_by_rid[row["r_id"]] = commands

    #build reservations info to send to client
    reservation_list = []
    for reservation in reservations:
        r_id = reservation["r_id"]
        reservation_list.append(
            {
                "r_id": r_id,
                "mission_id": reservation["mission_id"],
                "pass_id": reservation["pass_id"],
                "gs_id": reservation["gs_id"],
                "norad_id": reservation["norad_id"],
                "start_time": reservation["start_time"],
                "end_time": reservation["end_time"],
                "commands": commands_by_rid.get(r_id, []),
                "status": reservation["status"],
                "created_at": reservation["created_at"],
            }
        )

    return {
        "reservations": reservation_list
    }
    return {
        "reservations": reservation_list
    }
