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
```

Wait until the database is healthy:

```bash
docker compose ps
```

The `postgres` service uses the PostGIS image and persists data in the `eventfinder_postgres_data` volume.

## 3. Apply the database schema

Run the idempotent initializer after PostgreSQL is ready:

```bash
python backend/scripts/init_db.py
```

It connects using `DATABASE_URL`, enables PostGIS, and creates or upgrades the tables from `database/schema/eventfinder_schema.sql`.

## 4. Import SQLite events

Place the collector database at the repository root or provide its absolute path:

```bash
python backend/scripts/import_sqlite_events.py --sqlite-path ./event_platform_v16.db
```

The SQLite file is opened for reading and is not modified. The importer creates missing sources and fallback categories, copies coordinates and dates, calculates quality scores, and skips duplicates matched by `source_url` or source plus `external_id`.

Quality scoring totals 100 points: title 10, description 20, date 25, location 20, coordinates 15, and category 10. Classes are `HIGH` for 80-100, `MEDIUM` for 60-79, and `LOW` for 0-59.

## 5. Start the API

```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive documentation is available at `http://localhost:8000/docs`.

## 6. Manual endpoint test

With the API running, execute:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/stats
curl "http://localhost:8000/events?limit=5&offset=0"
curl http://localhost:8000/categories
```

Expected behavior:

- `/health` returns service status without querying PostgreSQL.
- `/stats` returns totals for events, categories, sources, and quality classes.
- `/events` returns imported PostgreSQL events or `[]` when empty.
- `/categories` returns database categories or `[]` when empty.

## Shutdown

```bash
docker compose down
```

Data remains in the named volume. Use `docker compose down -v` only when the database should be deleted.
