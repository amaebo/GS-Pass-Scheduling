
from fastapi import FastAPI

from src.core.logging import setup_logging
from src.routers import groundstations, missions, passes, satellites, commands, reservations


app = FastAPI()
setup_logging()
app.include_router(satellites)
app.include_router(groundstations)
app.include_router(missions)
app.include_router(passes)
app.include_router(commands)
app.include_router(reservations)