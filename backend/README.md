# Backend

FastAPI service for the EventFinder API, backed by PostgreSQL with PostGIS.

## Requirements

- Python 3.10 or newer
- Docker with Docker Compose

## Local setup

Create the backend environment file from the provided example:

```bash
cp backend/.env.example backend/.env
```

Install the Python dependencies from the repository root:

```bash
python -m pip install -r requirements.txt
```

Start PostgreSQL/PostGIS:

```bash
docker compose up -d postgres
```

The `postgres` service uses the PostGIS image, persists data in the `eventfinder_postgres_data` volume, and initializes a new database with `database/schema/eventfinder_schema.sql`.

Start the API from the repository root:

```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Endpoints

- `GET /health` returns API service metadata.
- `GET /events` returns all events ordered by start date and title.
- `GET /categories` returns all categories ordered by name.

When their database tables contain no rows, `GET /events` and `GET /categories` return an empty JSON list (`[]`). Interactive API documentation is available at `http://localhost:8000/docs`.
