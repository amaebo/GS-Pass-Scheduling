import httpx
import logging
from datetime import datetime, timezone

from fastapi import HTTPException

from src.core.config import N2YO_BASE_URL, N2YO_API_KEY

logger = logging.getLogger("n2yo_service")

def get_passes_from_n2yo(
    norad_id: int,
    gs_lon: float,
    gs_lat: float,
    alt: float,
    min_visibility: int = 30,
    days: int = 1,
) -> list[dict]:
    """Send N2YO API request to get passes.
    """
    if not N2YO_API_KEY:
        raise HTTPException(status_code=500, detail="N2YO API key is not configured.")
    if not N2YO_BASE_URL:
        raise HTTPException(status_code=500, detail="N2YO API base url is not configured.")
    
    try:
        res = httpx.get(
            f"{N2YO_BASE_URL}visualpasses/{norad_id}/{gs_lat}/{gs_lon}/{alt}/{days}/{min_visibility}",
            params={"apiKey": N2YO_API_KEY},
            timeout=10.0,
        )
    except httpx.RequestError as exc:
        logger.error(f"N2YO API request failed: {exc}")
        raise HTTPException(status_code=502, detail="N2YO API request failed.")
    # raise HTTPStatusError if response is not 2xx status
    res.raise_for_status()
    
    # Log API requests sent and responses recieved.
    if res.status_code == httpx.codes.OK:
        transaction_count = res.json().get("info")["transactionscount"]
        logger.info(f"N2YO API request sent. {N2YO_BASE_URL}visualpasses/{norad_id}/{gs_lat}/{gs_lon}/{alt}/{days}/{min_visibility}")
        logger.info(f"N2YO API response received. Transaction count in the last hour: {transaction_count}")
        
    
    #normalize passes
    normalized_passes = normalize_n2yo_passes(res)

    return normalized_passes

def normalize_n2yo_passes(res: httpx.Response) -> list[dict]:
    """
    Extracts key information from N2YO API response passes, including time conversion.
        
        Expected API keys:

        'info' - JSON of satellite info including 'satid'
        
        'passes'- list of passes JSON with 'startUTC', 'endUTC', `duration` and `maxEl`
        
        Returns:
            list[dict]: A list of passes with `norad_id`, `start_time`, `end_time`, `max_elavation` and `duration` keys"""
    data = res.json()
    raw_passes = data.get("passes", [])
    norad_id = data.get("info")["satid"]

    normalized_passes: list[dict] = []

    for p in raw_passes:
        try:
            start_unix_time = p["startUTC"]
            end_unix_time = p["endUTC"]
            max_el = p["maxEl"]
            duration = p["duration"]

        except KeyError as e:
          missing = e.args[0]
          raise HTTPException(status_code=502, detail=f"N2YO API service response missing '{missing}'")

        start_ts = datetime.fromtimestamp(start_unix_time, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        end_ts = datetime.fromtimestamp(end_unix_time, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        normalized_passes.append({
            "norad_id": norad_id,
            "max_elevation": max_el,
            "duration": duration,
            "start_time": start_ts,
            "end_time": end_ts
            })

    return normalized_passes
    
