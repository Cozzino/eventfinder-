from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPOSITORY_ROOT / "backend"
SCHEMA_PATH = REPOSITORY_ROOT / "database" / "schema" / "eventfinder_schema.sql"

if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))


def main() -> int:
    load_dotenv(BACKEND_DIR / ".env")
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://eventfinder:eventfinder@localhost:5432/eventfinder",
    )

    if not SCHEMA_PATH.is_file():
        print(f"Schema file not found: {SCHEMA_PATH}", file=sys.stderr)
        return 1

    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    try:
        with psycopg2.connect(database_url) as connection:
            connection.autocommit = True
            with connection.cursor() as cursor:
                cursor.execute(schema_sql)
                cursor.execute("SELECT PostGIS_Version()")
                postgis_version = cursor.fetchone()[0]
    except psycopg2.Error as exc:
        print(f"Database initialization failed: {exc}", file=sys.stderr)
        return 1

    print(f"Database initialized successfully (PostGIS {postgis_version}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
