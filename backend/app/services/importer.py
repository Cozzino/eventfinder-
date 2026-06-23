from __future__ import annotations

import hashlib
import re
import sqlite3
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from ..models import Category, Event, Source

SOURCE_COLUMNS = (
    "event_id",
    "source_name",
    "title",
    "excerpt",
    "description_text",
    "city",
    "province",
    "latitude",
    "longitude",
    "start_date",
    "end_date",
    "source_url",
    "fingerprint",
    "updated_at",
)


@dataclass
class ImportResult:
    read: int = 0
    imported: int = 0
    duplicates: int = 0
    invalid: int = 0


def calculate_quality_score(
    *,
    title: str | None,
    description: str | None,
    start_date: datetime | None,
    end_date: datetime | None,
    city: str | None,
    province: str | None,
    latitude: float | None,
    longitude: float | None,
    category: Category | None,
) -> tuple[int, str]:
    score = 0
    score += 10 if title else 0
    score += 20 if description else 0
    score += 25 if start_date or end_date else 0
    score += 20 if city or province else 0
    score += 15 if latitude is not None and longitude is not None else 0
    score += 10 if category is not None else 0

    if score >= 80:
        quality_class = "HIGH"
    elif score >= 60:
        quality_class = "MEDIUM"
    else:
        quality_class = "LOW"
    return score, quality_class


class SqliteEventImporter:
    def __init__(self, db: Session) -> None:
        self.db = db
        self._sources: dict[str, Source] = {}
        self._categories: dict[str, Category] = {}
        self._seen_urls: set[str] = set()
        self._seen_external_ids: set[tuple[object, str]] = set()

    def import_file(self, sqlite_path: str | Path) -> ImportResult:
        path = Path(sqlite_path).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"SQLite database not found: {path}")

        connection = sqlite3.connect(path)
        connection.row_factory = sqlite3.Row
        try:
            columns = self._validate_source(connection)
            selected_columns = [column for column in SOURCE_COLUMNS if column in columns]
            quoted_columns = ", ".join(f'"{column}"' for column in selected_columns)
            cursor = connection.execute(f"SELECT {quoted_columns} FROM events")

            result = ImportResult()
            for row in cursor:
                result.read += 1
                outcome = self._import_row(dict(row))
                if outcome == "imported":
                    result.imported += 1
                elif outcome == "duplicate":
                    result.duplicates += 1
                else:
                    result.invalid += 1

            self.db.commit()
            return result
        except Exception:
            self.db.rollback()
            raise
        finally:
            connection.close()

    @staticmethod
    def _validate_source(connection: sqlite3.Connection) -> set[str]:
        table = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'events'"
        ).fetchone()
        if table is None:
            raise ValueError("SQLite database does not contain an events table")

        columns = {row[1] for row in connection.execute("PRAGMA table_info(events)")}
        missing = {"event_id", "source_name", "title"} - columns
        if missing:
            missing_list = ", ".join(sorted(missing))
            raise ValueError(f"SQLite events table is missing required columns: {missing_list}")
        return columns

    def _import_row(self, row: dict[str, Any]) -> str:
        title = _clean_text(row.get("title"))
        source_name = _clean_text(row.get("source_name"))
        external_id = _clean_text(row.get("event_id"))
        if not title or not source_name or not external_id:
            return "invalid"

        source_name = source_name[:200]
        external_id = external_id[:255]
        source = self._get_or_create_source(source_name)
        source_url = _clean_text(row.get("source_url"))
        if self._is_duplicate(source, external_id, source_url):
            return "duplicate"

        excerpt = _clean_text(row.get("excerpt"))
        description = _clean_text(row.get("description_text")) or excerpt
        city = _clean_text(row.get("city"))
        province = _clean_text(row.get("province"))
        start_date = _parse_datetime(row.get("start_date"))
        end_date = _parse_datetime(row.get("end_date"))
        latitude = _parse_coordinate(row.get("latitude"), -90, 90)
        longitude = _parse_coordinate(row.get("longitude"), -180, 180)
        category = self._get_or_create_category(title, description)
        quality_score, quality_class = calculate_quality_score(
            title=title,
            description=description,
            start_date=start_date,
            end_date=end_date,
            city=city,
            province=province,
            latitude=latitude,
            longitude=longitude,
            category=category,
        )

        fingerprint = _clean_text(row.get("fingerprint"))
        values: dict[str, Any] = {
            "source_id": source.id,
            "category_id": category.id,
            "external_id": external_id,
            "fingerprint": fingerprint[:255] if fingerprint else None,
            "title": title[:500],
            "description": description,
            "province": province,
            "city": city,
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date,
            "end_date": end_date,
            "source_url": source_url,
            "quality_score": quality_score,
            "quality_class": quality_class,
        }
        updated_at = _parse_datetime(row.get("updated_at"))
        if updated_at is not None:
            values["updated_at"] = updated_at

        self.db.add(Event(**values))
        if source_url:
            self._seen_urls.add(source_url)
        self._seen_external_ids.add((source.id, external_id))
        return "imported"

    def _get_or_create_source(self, name: str) -> Source:
        cache_key = name.casefold()
        if cache_key in self._sources:
            return self._sources[cache_key]

        source = self.db.scalar(select(Source).where(func.lower(Source.name) == name.lower()))
        if source is None:
            slug = _slugify(name)
            slug_owner = self.db.scalar(select(Source).where(Source.slug == slug))
            if slug_owner is not None:
                suffix = hashlib.sha1(name.encode("utf-8")).hexdigest()[:8]
                slug = f"{slug[:190]}-{suffix}"
            source = Source(
                name=name,
                slug=slug[:200],
                source_type="collector-sqlite",
                base_url=None,
            )
            self.db.add(source)
            self.db.flush()

        self._sources[cache_key] = source
        return source

    def _get_or_create_category(self, title: str, description: str | None) -> Category:
        searchable = f"{title} {description or ''}".casefold()
        category_name = "Sagre e Feste" if re.search(r"\b(sagra|sagre|festa|feste)\b", searchable) else "Festival"
        if category_name in self._categories:
            return self._categories[category_name]

        category = self.db.scalar(select(Category).where(Category.name == category_name))
        if category is None:
            category = Category(
                name=category_name,
                slug=_slugify(category_name),
                description="Categoria creata automaticamente durante l'importazione SQLite.",
            )
            self.db.add(category)
            self.db.flush()

        self._categories[category_name] = category
        return category

    def _is_duplicate(self, source: Source, external_id: str, source_url: str | None) -> bool:
        if source_url and source_url in self._seen_urls:
            return True
        if (source.id, external_id) in self._seen_external_ids:
            return True

        conditions = [
            and_(Event.source_id == source.id, Event.external_id == external_id),
        ]
        if source_url:
            conditions.append(Event.source_url == source_url)

        statement = select(Event.id).where(or_(*conditions)).limit(1)
        return self.db.scalar(statement) is not None


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _parse_datetime(value: Any) -> datetime | None:
    text = _clean_text(value)
    if text is None:
        return None
    normalized = text.replace("Z", "+00:00")
    parsed: datetime | None = None
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        for date_format in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y"):
            try:
                parsed = datetime.strptime(text, date_format)
                break
            except ValueError:
                continue
    if parsed is not None and parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed


def _parse_coordinate(value: Any, minimum: float, maximum: float) -> float | None:
    text = _clean_text(value)
    if text is None:
        return None
    try:
        coordinate = float(text.replace(",", "."))
    except ValueError:
        return None
    return coordinate if minimum <= coordinate <= maximum else None


def _slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_value).strip("-")
    return slug or "source"
