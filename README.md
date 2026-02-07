# GS-Pass-Scheduling

FastAPI service for managing ground stations, satellites, missions, predicted passes, and pass reservations. Pass predictions are cached in SQLite and refreshed from the N2YO API when stale.

## Highlights
- Register and manage ground stations and satellites.
- Create missions and attach satellites to missions.
- Fetch and cache predicted passes (N2YO-backed) and claim them via reservations.
- Schedule command sets per reservation.
- Cleanup script to remove cancelled reservations tied to expired passes.

## Tech Stack
- Language: Python
- API framework: FastAPI
- Data store: SQLite
- External API: N2YO (pass prediction source)
- HTTP client: httpx
- Validation: Pydantic
- Testing: pytest

## Project layout
- `src/main.py` FastAPI app entrypoint.
- `src/routers/` API routes (groundstations, satellites, missions, passes, reservations, commands).
- `db/schema.sql` SQLite schema.
- `db/seed.sql` dev seed data.
- `data/ground_system.db` default SQLite DB path.
- `scripts/cleanup_reservations.py` cleanup job.
- `tests/` pytest test suite.

## Quick start
1. Create a virtual environment and install dependencies.
   - Recommended: `pip install "fastapi[standard]"`
     - Includes Uvicorn for running the API.
   - Additional requirements used by this project: `httpx`, `python-dotenv` (for `.env`), `pytest` (tests).

2. Configure environment variables in `.env` (see the next section).

3. Initialize the SQLite database (required), and optionally seed it (recommended for local dev):

```bash
python -c "from db.db_init import init_db; init_db()"
```

Optional seed:

```bash
python -c "from db.db_init import init_db, seed_db; init_db(); seed_db()"
```

Seed only (assumes schema already initialized):

```bash
python - <<'PY'
from pathlib import Path
from db import db_init

seed_sql = (Path(__file__).resolve().parents[0] / 'db' / 'seed.sql').read_text(encoding='utf-8')
conn = db_init.db_connect()
try:
    conn.executescript(seed_sql)
    conn.commit()
finally:
    conn.close()
PY
```

4. Run the API:

```bash
fastapi dev src.main:app
```

The server will be available at `http://localhost:8000`.

## Environment
Configuration is loaded from `.env` at the repo root.

Required:
- `N2YO_API_KEY` N2YO API key.
- `N2YO_API_BASE_URL` N2YO base URL, for example `https://api.n2yo.com/rest/v1/satellite/`.

Optional:
- `LOG_LEVEL` (default: `INFO`).

## API overview

Base URL depends on where the FastAPI server is running. In local dev, it usually runs at `http://localhost:8000`.

### Ground stations
- `GET /groundstations` List all ground stations.
- `POST /groundstations` Register a ground station.
- `PATCH /groundstations/{gs_id}/` Update `gs_code` or `status`.
- `DELETE /groundstations/{gs_id}` Delete a ground station. Use `?force=true` to bypass active-reservation checks.

Example:
```bash
curl -X POST http://localhost:8000/groundstations \
  -H 'Content-Type: application/json' \
  -d '{"gs_code":"DEN_CO","lon":-104.9903,"lat":39.7392,"alt":1609,"status":"ACTIVE"}'
```

### Satellites
- `GET /satellites` List all satellites.
- `POST /satellites` Register a satellite.
- `PATCH /satellites/{norad_id}/` Update `s_name`.
- `DELETE /satellites/{norad_id}` Delete a satellite. Use `?force=true` to bypass active-reservation checks.

Example:
```bash
curl -X POST http://localhost:8000/satellites \
  -H 'Content-Type: application/json' \
  -d '{"norad_id":25544,"s_name":"ISS (ZARYA)"}'
```

### Missions
- `POST /missions/create` Create a mission.
- `GET /missions` List missions.
- `PATCH /missions/update/{mission_id}` Update a mission.
- `DELETE /missions/delete/{mission_id}` Delete a mission.
- `POST /missions/{mission_id}/satellites/{norad_id}` Add satellite to mission.
- `GET /missions/{mission_id}/satellites` List mission satellites.
- `DELETE /missions/{mission_id}/satellites/{norad_id}` Remove satellite from mission.

Example:
```bash
curl -X POST http://localhost:8000/missions/create \
  -H 'Content-Type: application/json' \
  -d '{"mission_name":"ISS Ops Demo","owner":"Ama","priority":"medium"}'
```

### Passes
- `GET /passes?norad_id={norad_id}&gs_id={gs_id}`
  - Fetches predicted passes from cache, refreshes from N2YO if stale, and returns claimable future passes.

Example:
```bash
curl "http://localhost:8000/passes?norad_id=25544&gs_id=1"
```

### Reservations
- `POST /reservations` Create a reservation for a pass (optionally tied to a mission and with commands).
- `GET /reservations` List reservations. Use `?include_cancelled=true` to include cancelled ones.
- `GET /reservations/{mission_id}` List reservations for a mission. Use `?include_cancelled=true`.
- `POST /reservations/{r_id}/cancel` Cancel a reservation.

Example:
```bash
curl -X POST http://localhost:8000/reservations \
  -H 'Content-Type: application/json' \
  -d '{"pass_id":1,"mission_id":1,"commands":["PING","GET_TELEMETRY"]}'
```

### Commands
- `GET /commands/` List available command types.

Example:
```bash
curl http://localhost:8000/commands/
```

## Maintenance
Scheduled cleanup (recommended via cron):

```bash
python scripts/cleanup_reservations.py
```

Example cron entry (runs every 48 hours at 2am):

```cron
0 2 */2 * * cd /Users/amaebong/Documents/Git/GS-Pass-Scheduling && /usr/bin/python3 scripts/cleanup_reservations.py
```

## Tests
Run the test suite:

```bash
pytest
```

The tests create a temporary SQLite DB and seed it using `db/seed.sql`.
