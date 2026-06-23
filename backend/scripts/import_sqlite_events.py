from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from backend.app.database import SessionLocal
from backend.app.services.importer import SqliteEventImporter


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import EventFinder collector events from SQLite into PostgreSQL."
    )
    parser.add_argument(
        "--sqlite-path",
        required=True,
        type=Path,
        help="Path to event_platform_v16.db or another compatible collector database.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    with SessionLocal() as db:
        try:
            result = SqliteEventImporter(db).import_file(args.sqlite_path)
        except (FileNotFoundError, ValueError) as exc:
            print(f"Import failed: {exc}", file=sys.stderr)
            return 1
        except Exception as exc:
            print(f"Import failed with an unexpected error: {exc}", file=sys.stderr)
            return 1

    print(
        "Import completed: "
        f"read={result.read}, imported={result.imported}, "
        f"duplicates={result.duplicates}, invalid={result.invalid}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
