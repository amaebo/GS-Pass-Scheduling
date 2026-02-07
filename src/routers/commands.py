from fastapi import APIRouter, HTTPException
import db.commands_db as c_db
import sqlite3

router = APIRouter(prefix="/commands")


@router.get("/")
def view_commands():
    try:
        rows = c_db.get_all_commands()

        return {"commands": [dict(command) for command in rows]}
    except sqlite3.Error:
        raise HTTPException(status_code=500, detail="Failed to retrieve commands")
