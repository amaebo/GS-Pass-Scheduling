import requests
from fastapi import APIRouter

from src.core.config import N2YO_API_BASE_URL, N2YO_API_KEY


router = APIRouter()


@router.get("/passes")
def view_pass(s_id: int, gs_id: int):
    pass
    # Check API for new passes

    # Check cache for passes

    # Check api


def get_passes_from_n2yo(
    norad_id: int,
    gs_lon: float,
    gs_lat: float,
    alt: float,
    min_visibility: int,
    days: int = 1,
):
    """Send api requests to get passes form n2yo API."""
    res = requests.get(
        f"{N2YO_API_BASE_URL}visualpasses/{norad_id}/{gs_lat}/{gs_lon}/{alt}/{days}/{min_visibility}",
        params={"apiKey": N2YO_API_KEY} if N2YO_API_KEY else None,
    )
    return res


def cache_passes():
    """Get satellite-groundstation passes from API."""
