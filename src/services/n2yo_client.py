import httpx
from fastapi import HTTPException

from src.core.config import N2YO_BASE_URL, N2YO_API_KEY


def get_passes_from_n2yo(
    norad_id: int,
    gs_lon: float,
    gs_lat: float,
    alt: float,
    min_visibility: int,
    days: int = 1,
) -> dict[str, object]:
    """Send N2YO API request to get passes.

    Returns parsed JSON response from NY2O API.
    """
    if not N2YO_API_KEY:
        raise HTTPException(status_code=500, detail="N2YO API key is not configured.")
    if not N2YO_BASE_URL:
        raise HTTPException(status_code=500, detail="N2YO API base url is not configured.")
    res = httpx.get(
        f"{N2YO_BASE_URL}visualpasses/{norad_id}/{gs_lat}/{gs_lon}/{alt}/{days}/{min_visibility}",
        params={"apiKey": N2YO_API_KEY}
    )
    return res.json()
