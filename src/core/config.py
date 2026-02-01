import os
from pathlib import Path

from dotenv import load_dotenv


_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(_ENV_PATH)

N2YO_API_KEY = os.getenv("N2YO_API_KEY")
N2YO_BASE_URL = os.getenv("N2YO_API_BASE_URL")
