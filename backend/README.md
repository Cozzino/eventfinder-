# Backend

FastAPI service for EventFinder, backed by PostgreSQL with PostGIS.

## Setup

Requirements: Python 3.10 or newer, Docker and Docker Compose.

```bash
cp backend/.env.example backend/.env
python -m pip install -r requirements.txt
docker compose up -d postgres
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

The `postgres` service uses the PostGIS image, persists data in the `eventfinder_postgres_data` volume, and initializes new volumes with `database/schema/eventfinder_schema.sql`.

For a database volume created before M3, apply the updated schema once:

```bash
psql postgresql://eventfinder:eventfinder@localhost:5432/eventfinder -f database/schema/eventfinder_schema.sql
```

## SQLite import

Import the collector database without modifying it:

```bash
python backend/scripts/import_sqlite_events.py --sqlite-path ./event_platform_v16.db
```

The importer creates missing sources and fallback categories, transfers coordinates and dates, and skips duplicates matched by `source_url` or by source plus `external_id`. It prints counts for read, imported, duplicate, and invalid rows.

Quality scoring totals 100 points: title 10, description 20, date 25, location 20, coordinates 15, and category 10. Classes are `HIGH` for 80-100, `MEDIUM` for 60-79, and `LOW` for 0-59.

## Endpoints

- `GET /health` returns API service metadata.
- `GET /events` reads PostgreSQL events and supports `category_id`, `city`, `province`, `date_from`, `date_to`, `limit`, and `offset`.
- `GET /categories` returns categories ordered by name.

Empty event or category tables return `[]`. Interactive documentation is available at `http://localhost:8000/docs`.
