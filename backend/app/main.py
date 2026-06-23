from fastapi import Depends, FastAPI
from sqlalchemy import select
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
def list_events(db: Session = Depends(get_db)) -> list[models.Event]:
    statement = select(models.Event).order_by(models.Event.start_date, models.Event.title)
    return list(db.scalars(statement).all())


@app.get("/categories", response_model=list[schemas.CategoryRead], tags=["categories"])
def list_categories(db: Session = Depends(get_db)) -> list[models.Category]:
    statement = select(models.Category).order_by(models.Category.name)
    return list(db.scalars(statement).all())
