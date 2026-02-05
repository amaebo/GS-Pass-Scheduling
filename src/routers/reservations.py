from fastapi import APIRouter
from src.schemas import ReservationCreate
import db.passes_db as p_db

router = APIRouter()
