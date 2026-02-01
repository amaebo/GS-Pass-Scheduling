
from fastapi import FastAPI
from src.routers import groundstations, missions, passes, satellites


app = FastAPI()
app.include_router(satellites)
app.include_router(groundstations)
app.include_router(missions)
app.include_router(passes)
