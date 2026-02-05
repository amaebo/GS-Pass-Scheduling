from src.routers.groundstations import router as groundstations
from src.routers.missions import router as missions
from src.routers.passes import router as passes
from src.routers.satellites import router as satellites
from src.routers.commands import router as commands 
from src.routers.reservations import router as reservations
__all__ = ["groundstations", "missions", "passes", "satellites", "commands", "reservations"]
