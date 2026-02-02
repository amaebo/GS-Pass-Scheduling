import httpx
from datetime import datetime, timezone

from fastapi import HTTPException

from src.core.config import N2YO_BASE_URL, N2YO_API_KEY


def get_passes_from_n2yo(
    norad_id: int,
    gs_lon: float,
    gs_lat: float,
    alt: float,
    min_visibility: int,
    days: int = 1,
) -> list[dict]:
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
    # raise 404 error if item not found
    res.raise_for_status()
    return normalize_n2yo_passes(res)

def normalize_n2yo_passes(res: httpx.Response) -> list[dict]:
    """Convert N2YO pass times from Unix seconds to UTC ISO timestamps.
        Expected API keys: `passes`- list of passes with `satid`,`startUTC`, `endUTC` 
        
        Returns:
            list[dict]: A list of passes with `norad_id`, `start_time` and `end_time` keys"""
    data = res.json()
    passes: list[dict] = []

    # 
    for p in data.get("passes", []):
        try:
            start_unix_time = p["startUTC"]
            end_unix_time = p["endUTC"]
            norad_id = p["satid"]
        except KeyError as e:
          missing = e.args[0]
          raise HTTPException(status_code=502, detail=f"N2YO API service response missing '{missing}'")

        passes.append({
            "norad_id": norad_id,
            "start_time": datetime.fromtimestamp(start_unix_time, tz=timezone.utc).isoformat(sep=" "),
            "end_time": datetime.fromtimestamp(end_unix_time, tz=timezone.utc).isoformat(sep=" "),
            })

    return passes
    
