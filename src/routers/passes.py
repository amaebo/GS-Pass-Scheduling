import os
from pathlib import Path

import requests
from dotenv import load_dotenv
from fastapi import APIRouter


router = APIRouter()

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
N2YO_API_KEY = os.getenv("N2YO_API_KEY")
N2YO_BASE_URL = os.getenv("N2YO_API_BASE_URL")
