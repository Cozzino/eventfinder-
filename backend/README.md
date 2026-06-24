# Backend

FastAPI service for EventFinder, backed by PostgreSQL with PostGIS.

## Setup and run

```bash
python -m pip install -r requirements.txt
cp backend/.env.example backend/.env
docker compose up -d
docker compose ps
python backend/scripts/init_db.py
python backend/scripts/import_sqlite_events.py --sqlite-path ./event_platform_v16.db
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

On Windows PowerShell, use `Copy-Item backend/.env.example backend/.env` instead of `cp`.

## API behavior

`/events`, `/search`, and `/events/nearby` use a common pagination envelope containing `items`, `total`, `limit`, and `offset`. Limits default to 20 and cannot exceed 100.

- `/events` defaults to ascending start date and supports `sort_by=quality_score`.
- `/search` sorts matching events by quality score descending.
- `/events/nearby` sorts by distance ascending, requires valid coordinates, and accepts a radius from above 0 through 200 km (default 25).
- CORS allows development requests from future Flutter clients.

## Runtime tests

```bash
curl "http://127.0.0.1:8001/events?limit=5"
curl "http://127.0.0.1:8001/events?limit=5&sort_by=quality_score"
curl "http://127.0.0.1:8001/search?q=festival&limit=5"
curl "http://127.0.0.1:8001/events/nearby?lat=44.4949&lon=11.3426&radius_km=50&limit=5"
```

Validation examples:

```bash
curl "http://127.0.0.1:8001/events/nearby?lon=11.3426"
curl "http://127.0.0.1:8001/events/nearby?lat=44.4949&lon=11.3426&radius_km=201"
curl "http://127.0.0.1:8001/events?limit=101"
```

These invalid requests return HTTP 422 and identify the invalid or missing query parameter.

Interactive documentation is available at `/docs`. Stop the database with `docker compose down`; the named volume is preserved.
