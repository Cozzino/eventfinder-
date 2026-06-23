# EventFinder Architecture

## System overview

EventFinder is organized as a data pipeline and API platform for discovering local events. The core system ingests event data from configured sources, normalizes and enriches it, stores it in a geospatial database, and exposes it to client applications through a backend API.

## Collector / Backend / Mobile separation

The Collector is responsible for data acquisition and normalization. It reads configured sources, imports event records, and prepares data for persistence. Collector code and source definitions are isolated from the application layer so ingestion can evolve independently.

The Backend exposes the EventFinder API. It owns validation, query behavior, health checks, search, category listing, event retrieval, and geospatial lookup endpoints.

The Mobile application consumes the backend API. It focuses on discovery flows such as browsing events, searching by keyword, filtering by category, and finding nearby events.

## Technology stack

- Collector: Python ingestion utilities.
- Database: PostgreSQL with PostGIS for geospatial indexing and proximity queries.
- Backend: FastAPI for HTTP APIs and typed Python services.
- Mobile: Flutter for cross-platform iOS and Android clients.
- Geocoding: OpenStreetMap/Nominatim for address-to-coordinate enrichment.

## Data flow

1. Sources are configured and processed by the Collector.
2. Raw event details are normalized into shared EventFinder fields.
3. Addresses can be geocoded with OpenStreetMap/Nominatim to produce latitude and longitude.
4. Normalized events are stored in PostgreSQL.
5. PostGIS indexes enable efficient nearby and map-based queries.
6. FastAPI serves events, categories, search results, and health status.
7. Flutter clients call the API and render event discovery experiences.

## Geocoding with OpenStreetMap/Nominatim

EventFinder uses OpenStreetMap/Nominatim as the planned geocoding provider. The backend and ingestion layers should treat geocoding as an enrichment step: textual location fields remain stored even when coordinates are unavailable, while coordinates enable nearby search and map features when present.

Nominatim usage must respect provider rate limits, attribution requirements, and caching expectations. Production deployments should use throttling and persistent geocoding results to avoid repeated requests for the same address.

## PostgreSQL + PostGIS

PostgreSQL is the source of truth for EventFinder Core data. PostGIS adds geographic indexing so events with latitude and longitude can be queried by distance. The M1 schema stores normalized event records, categories, sources, synchronization logs, and future-ready user tables.

## FastAPI

FastAPI provides the HTTP boundary for EventFinder. The M1 backend starts with a health endpoint and defines the structure for future event, category, nearby, and search endpoints. Pydantic schemas document the response contracts and keep request/response validation explicit.

## Flutter

Flutter is the target mobile client technology. The mobile app should consume the FastAPI endpoints, display event lists and details, and later add map, favorites, saved searches, and personalized discovery features.
