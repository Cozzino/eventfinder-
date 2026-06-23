# Backend

FastAPI service for the EventFinder Core API.

## M1 scope

- Application package under `backend/app/`.
- Health endpoint at `GET /health`.
- Database session setup for PostgreSQL.
- SQLAlchemy models aligned with the M1 schema.
- Pydantic schemas for events, categories, nearby search, and search responses.

## Run locally

```bash
uvicorn backend.app.main:app --reload
```

The API exposes service metadata at `/health`.
