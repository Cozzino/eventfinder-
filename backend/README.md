# Backend

FastAPI service for EventFinder, backed by PostgreSQL with PostGIS.

## 1. Install dependencies

Requirements: Python 3.10 or newer, Docker and Docker Compose.

```bash
python -m pip install -r requirements.txt
cp backend/.env.example backend/.env
```

On Windows PowerShell, use `Copy-Item backend/.env.example backend/.env` instead of `cp`.

## 2. Start PostgreSQL/PostGIS

```bash
docker compose up -d
docker compose ps
```

The `postgres` service uses the PostGIS image and persists data in the `eventfinder_postgres_data` volume.

## 3. Initialize and import

```bash
python backend/scripts/init_db.py
python backend/scripts/import_sqlite_events.py --sqlite-path ./event_platform_v16.db
```

The SQLite file is read without being modified. Import is idempotent by source URL or source plus external ID.

## 4. Start the API

```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive documentation is available at `http://localhost:8000/docs`.

## 5. Manual endpoint tests

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/stats
curl "http://127.0.0.1:8000/events?limit=5"
curl http://127.0.0.1:8000/categories
curl "http://127.0.0.1:8000/search?q=festival&limit=5"
curl "http://127.0.0.1:8000/events/nearby?lat=44.4949&lon=11.3426&radius_km=50&limit=5"
```

`/search` searches title, description, city, and province and supports category, location, date, limit, and offset filters. `/events/nearby` uses PostGIS distance calculations, returns `distance_km`, and supports category/date filters plus pagination.

## Shutdown

```bash
docker compose down
```

Data remains in the named volume. Use `docker compose down -v` only when the database should be deleted.
