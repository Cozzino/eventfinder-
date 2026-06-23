import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "eventfinder-api"
    version: str = "1.0.0"


class StatsResponse(BaseModel):
    events: int
    categories: int
    sources: int
    high_quality_events: int
    medium_quality_events: int
    low_quality_events: int


class CategoryBase(BaseModel):
    name: str
    slug: str
    description: str | None = None


class CategoryRead(CategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID


class SourceBase(BaseModel):
    name: str
    slug: str
    base_url: str | None = None
    source_type: str | None = None
    is_active: bool = True


class SourceRead(SourceBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID


class EventBase(BaseModel):
    source_id: uuid.UUID | None = None
    category_id: uuid.UUID | None = None
    external_id: str | None = None
    fingerprint: str | None = None
    title: str = Field(max_length=500)
    description: str | None = None
    region: str | None = None
    province: str | None = None
    city: str | None = None
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    source_url: str | None = None
    quality_score: int | None = 0
    quality_class: str | None = None


class EventRead(EventBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID


class EventListResponse(BaseModel):
    items: list[EventRead]
    limit: int
    offset: int
    total: int


class NearbyEventRead(BaseModel):
    id: uuid.UUID
    title: str
    city: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    distance_km: float
    start_date: datetime | None = None


class NearbyEventsResponse(BaseModel):
    items: list[NearbyEventRead]
    center: dict[str, float]
    radius_km: float


class SearchResponse(BaseModel):
    query: str
    items: list[EventRead]
    limit: int
    offset: int
    total: int
