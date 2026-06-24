from datetime import datetime
from typing import Literal
import uuid

from fastapi import Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
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


def _pagination_count(statement: object, db: Session) -> int:
    return int(db.scalar(statement) or 0)


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
    lat: float = Query(..., ge=-90, le=90, description="Required latitude between -90 and 90."),
    lon: float = Query(..., ge=-180, le=180, description="Required longitude between -180 and 180."),
    radius_km: float = Query(default=25, gt=0, le=200, description="Search radius in kilometers, from 0 to 200."),
    category_id: uuid.UUID | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int = Query(default=20, ge=1, le=100),
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
    filters = [
        models.Event.latitude.is_not(None),
        models.Event.longitude.is_not(None),
        func.ST_DWithin(event_point, center_point, radius_km * 1000.0),
    ]
    if category_id is not None:
        filters.append(models.Event.category_id == category_id)
    if date_from is not None:
        filters.append(models.Event.start_date >= date_from)
    if date_to is not None:
        filters.append(models.Event.start_date <= date_to)

    total = _pagination_count(
        select(func.count()).select_from(models.Event).where(*filters),
        db,
    )
    statement = (
        select(models.Event, distance_km)
        .where(*filters)
        .order_by(distance_km, models.Event.start_date.asc().nulls_last())
        .limit(limit)
        .offset(offset)
    )
    items = [
        schemas.NearbyEventRead(
            **schemas.EventRead.model_validate(event).model_dump(),
            distance_km=round(float(distance), 3),
        )
        for event, distance in db.execute(statement).all()
    ]
    return schemas.NearbyEventsResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        center={"lat": lat, "lon": lon},
        radius_km=radius_km,
    )


@app.get("/events", response_model=schemas.EventListResponse, tags=["events"])
def list_events(
    category_id: uuid.UUID | None = None,
    city: str | None = None,
    province: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    sort_by: Literal["start_date", "quality_score"] = "start_date",
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> schemas.EventListResponse:
    statement = _apply_event_filters(
        select(models.Event),
        category_id=category_id,
        city=city,
        province=province,
        date_from=date_from,
        date_to=date_to,
    )
    count_statement = _apply_event_filters(
        select(func.count()).select_from(models.Event),
        category_id=category_id,
        city=city,
        province=province,
        date_from=date_from,
        date_to=date_to,
    )
    if sort_by == "quality_score":
        order_by = (
            models.Event.quality_score.desc().nulls_last(),
            models.Event.start_date.asc().nulls_last(),
            models.Event.title,
        )
    else:
        order_by = (
            models.Event.start_date.asc().nulls_last(),
            models.Event.title,
        )

    items = list(db.scalars(statement.order_by(*order_by).limit(limit).offset(offset)).all())
    return schemas.EventListResponse(
        items=items,
        total=_pagination_count(count_statement, db),
        limit=limit,
        offset=offset,
    )


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
    limit: int = Query(default=20, ge=1, le=100),
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
    statement = filtered.order_by(
        models.Event.quality_score.desc().nulls_last(),
        models.Event.start_date.asc().nulls_last(),
        models.Event.title,
    ).limit(limit).offset(offset)
    return schemas.SearchResponse(
        query=q.strip(),
        items=list(db.scalars(statement).all()),
        total=_pagination_count(count_statement, db),
        limit=limit,
        offset=offset,
    )
