# EventFinder

EventFinder collects events into SQLite and serves imported data through a FastAPI backend backed by PostgreSQL/PostGIS.

## Runtime quick start

From the repository root:

```bash
python -m pip install -r requirements.txt
cp backend/.env.example backend/.env
docker compose up -d
python backend/scripts/init_db.py
python backend/scripts/import_sqlite_events.py --sqlite-path ./event_platform_v16.db
uvicorn backend.app.main:app --reload
```

The collector SQLite database is read without being modified. See `backend/README.md` for database checks, endpoint tests, and troubleshooting.
