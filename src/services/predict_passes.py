from datetime import datetime, timezone
from pyorbital.orbital import Orbital


def _to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _format_db_time(dt: datetime) -> str:
    dt = _to_utc(dt)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def get_pass_predictions(
    sat_name: str,
    tle_line1: str,
    tle_line2: str,
    utc_time: datetime,
    hours: int,
    gs_lon: float,
    gs_lat: float,
    gs_alt: float,
    tol: float = 0.001,
    horizon: float = 0,
) -> list[dict]:
    orbital = Orbital(sat_name, line1=tle_line1, line2=tle_line2)
    raw_passes = orbital.get_next_passes(
        _to_utc(utc_time),
        hours,
        gs_lon,
        gs_lat,
        gs_alt,
        tol,
        horizon,
    )

    predictions: list[dict] = []
    for rise_time, set_time, max_time in raw_passes:
        rise_time = _to_utc(rise_time)
        set_time = _to_utc(set_time)
        max_time = _to_utc(max_time)
        _, max_elevation = orbital.get_observer_look(max_time, gs_lon, gs_lat, gs_alt)
        predictions.append(
            {
                "start_time": _format_db_time(rise_time),
                "end_time": _format_db_time(set_time),
                "max_elevation": float(max_elevation),
                "duration": int((set_time - rise_time).total_seconds()),
            }
        )

    return predictions
