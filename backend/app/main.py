from datetime import datetime
import uuid

from fastapi import Depends, FastAPI, Query
from geoalchemy2 import Geography
from sqlalchemy import cast, func, or_, select
from sqlalchemy.orm import Session

from . import models, schemas
from .database import get_db

app = FastAPI(
    title="EventFinder API",
    description="Core API for EventFinder event discovery.",
    version="1.0.0",
)


def _apply_event_filters(
    statement: object,
    *,
    category_id: uuid.UUID | None = None,
    city: str | None = None,
    province: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> object:
    if category_id is not None:
        statement = statement.where(models.Event.category_id == category_id)
    if city:
        statement = statement.where(func.lower(models.Event.city) == city.strip().lower())
    if province:
        statement = statement.where(func.lower(models.Event.province) == province.strip().lower())
    if date_from is not None:
        statement = statement.where(models.Event.start_date >= date_from)
    if date_to is not None:
        statement = statement.where(models.Event.start_date <= date_to)
    return statement


@app.get("/health", response_model=schemas.HealthResponse, tags=["system"])
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "eventfinder-api",
        "version": "1.0.0",
    }


@app.get("/stats", response_model=schemas.StatsResponse, tags=["system"])
def stats(db: Session = Depends(get_db)) -> schemas.StatsResponse:
    def count(model: type[models.Base], *conditions: object) -> int:
        statement = select(func.count()).select_from(model)
        if conditions:
            statement = statement.where(*conditions)
        return int(db.scalar(statement) or 0)

    return schemas.StatsResponse(
        events=count(models.Event),
        categories=count(models.Category),
        sources=count(models.Source),
        high_quality_events=count(models.Event, models.Event.quality_class == "HIGH"),
        medium_quality_events=count(models.Event, models.Event.quality_class == "MEDIUM"),
        low_quality_events=count(models.Event, models.Event.quality_class == "LOW"),
    )


@app.get("/events/nearby", response_model=schemas.NearbyEventsResponse, tags=["events"])
def nearby_events(
    lat: float = Query(ge=-90, le=90),
    lon: float = Query(ge=-180, le=180),
    radius_km: float = Query(default=10, gt=0, le=500),
    category_id: uuid.UUID | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int = Query(default=20, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> schemas.NearbyEventsResponse:
    event_point = cast(
        func.ST_SetSRID(func.ST_MakePoint(models.Event.longitude, models.Event.latitude), 4326),
        Geography(geometry_type="POINT", srid=4326),
    )
    center_point = cast(
        func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326),
        Geography(geometry_type="POINT", srid=4326),
    )
    distance_km = (func.ST_Distance(event_point, center_point) / 1000.0).label("distance_km")
    radius_meters = radius_km * 1000.0

    filters = [
        models.Event.latitude.is_not(None),
        models.Event.longitude.is_not(None),
        func.ST_DWithin(event_point, center_point, radius_meters),
    ]
    if category_id is not None:
        filters.append(models.Event.category_id == category_id)
    if date_from is not None:
        filters.append(models.Event.start_date >= date_from)
    if date_to is not None:
        filters.append(models.Event.start_date <= date_to)

    total_statement = select(func.count()).select_from(models.Event).where(*filters)
    total = int(db.scalar(total_statement) or 0)
    statement = (
        select(models.Event, distance_km)
        .where(*filters)
        .order_by(distance_km, models.Event.start_date.asc().nulls_last())
        .limit(limit)
        .offset(offset)
    )
    rows = db.execute(statement).all()
    items = [
        schemas.NearbyEventRead(
            **schemas.EventRead.model_validate(event).model_dump(),
            distance_km=round(float(distance), 3),
        )
        for event, distance in rows
    ]
    return schemas.NearbyEventsResponse(
        items=items,
        center={"lat": lat, "lon": lon},
        radius_km=radius_km,
        limit=limit,
        offset=offset,
        total=total,
    )


@app.get("/events", response_model=list[schemas.EventRead], tags=["events"])
def list_events(
    category_id: uuid.UUID | None = None,
    city: str | None = None,
    province: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int = Query(default=20, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[models.Event]:
    statement = _apply_event_filters(
        select(models.Event),
        category_id=category_id,
        city=city,
        province=province,
        date_from=date_from,
        date_to=date_to,
    )
    statement = statement.order_by(
        models.Event.start_date.asc().nulls_last(),
        models.Event.title,
    ).limit(limit).offset(offset)
    return list(db.scalars(statement).all())


@app.get("/categories", response_model=list[schemas.CategoryRead], tags=["categories"])
def list_categories(db: Session = Depends(get_db)) -> list[models.Category]:
    statement = select(models.Category).order_by(models.Category.name)
    return list(db.scalars(statement).all())


@app.get("/search", response_model=schemas.SearchResponse, tags=["events"])
def search_events(
    q: str = Query(min_length=1, max_length=200),
    category_id: uuid.UUID | None = None,
    city: str | None = None,
    province: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int = Query(default=20, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> schemas.SearchResponse:
    search_term = f"%{q.strip()}%"
    search_filter = or_(
        models.Event.title.ilike(search_term),
        models.Event.description.ilike(search_term),
        models.Event.city.ilike(search_term),
        models.Event.province.ilike(search_term),
    )
    filtered = _apply_event_filters(
        select(models.Event).where(search_filter),
        category_id=category_id,
        city=city,
        province=province,
        date_from=date_from,
        date_to=date_to,
    )
    count_statement = _apply_event_filters(
        select(func.count()).select_from(models.Event).where(search_filter),
        category_id=category_id,
        city=city,
        province=province,
        date_from=date_from,
        date_to=date_to,
    )
    total = int(db.scalar(count_statement) or 0)
    statement = filtered.order_by(
        models.Event.start_date.asc().nulls_last(),
        models.Event.title,
    ).limit(limit).offset(offset)
    items = list(db.scalars(statement).all())
    return schemas.SearchResponse(
        query=q.strip(),
        items=items,
        limit=limit,
        offset=offset,
        total=total,
    )
