from datetime import datetime
import uuid

from fastapi import Depends, FastAPI, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from . import models, schemas
from .database import get_db

app = FastAPI(
    title="EventFinder API",
    description="Core API for EventFinder event discovery.",
    version="1.0.0",
)


@app.get("/health", response_model=schemas.HealthResponse, tags=["system"])
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "eventfinder-api",
        "version": "1.0.0",
    }


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
    statement = select(models.Event)
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

    statement = statement.order_by(
        models.Event.start_date.asc().nulls_last(),
        models.Event.title,
    ).limit(limit).offset(offset)
    return list(db.scalars(statement).all())


@app.get("/categories", response_model=list[schemas.CategoryRead], tags=["categories"])
def list_categories(db: Session = Depends(get_db)) -> list[models.Category]:
    statement = select(models.Category).order_by(models.Category.name)
    return list(db.scalars(statement).all())
