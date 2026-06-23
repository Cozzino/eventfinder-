# Database

EventFinder uses PostgreSQL with PostGIS. The canonical schema is `schema/eventfinder_schema.sql`.

## Startup

`docker compose up -d postgres` creates the `eventfinder` database, enables PostGIS, applies the schema to new volumes, and persists data in `eventfinder_postgres_data`.

Existing volumes are not reinitialized automatically. Apply schema updates manually when upgrading:

```bash
psql postgresql://eventfinder:eventfinder@localhost:5432/eventfinder -f database/schema/eventfinder_schema.sql
```

## M3 import fields

The `events` table includes `external_id` and `fingerprint` from the collector SQLite database. Partial unique indexes prevent duplicates by source plus external ID and by source URL. Existing installations are upgraded idempotently with `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`.

The SQLite source remains read-only from the importer's point of view; imported records are written only to PostgreSQL.
