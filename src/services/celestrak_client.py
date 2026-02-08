import httpx
from fastapi import HTTPException
import logging

logger = logging.getLogger("celestrak_client")

CELESTRAK_BASE_URL = "https://celestrak.org/NORAD/elements/gp.php"

def get_tle(norad_id: int):
    try:
        response = httpx.get(f"{CELESTRAK_BASE_URL}?CATNR={norad_id}&FORMAT=2LE")
        response.raise_for_status()
    except httpx.RequestError as exc:
        logger.error(f"CelesTrak API request failed: {exc}")
        raise HTTPException(status_code=502, detail="CelesTrak API request failed.")
    
    res_str = response.text

    tle_list = [line.strip() for line in res_str.splitlines() if line.strip()]

    if len(tle_list) < 2:
        logger.error(f"CelesTrak returned no TLE for NORAD {norad_id}")
        raise HTTPException(status_code=404, detail="TLE not found for satellite.")

    # tle_dict = {"tle_line_1": tle_list[0], "tle_line_2": tle_list[1]}

    return tle_list[:2]
