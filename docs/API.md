# EventFinder API

Base service: `eventfinder-api`  
Version: `1.0.0`

## GET /health

Returns service health information. It has no parameters.

```http
GET /health
```

```json
{
  "status": "ok",
  "service": "eventfinder-api",
  "version": "1.0.0"
}
```

## GET /events

Returns real events stored in PostgreSQL, ordered by start date and title. An empty database returns `[]`.

Parameters:

- `category_id`: optional category UUID.
- `city`: optional case-insensitive exact city.
- `province`: optional case-insensitive exact province.
- `date_from`: optional minimum start date in ISO 8601 format.
- `date_to`: optional maximum start date in ISO 8601 format.
- `limit`: optional integer from 1 to 200, default 20.
- `offset`: optional non-negative integer, default 0.

```http
GET /events?city=Roma&date_from=2026-07-01T00:00:00&limit=2&offset=0
```

```json
[
  {
    "id": "7ad3a0f1-4f93-4d7b-9e8e-f4af8cf079d3",
    "source_id": "349c4ba9-1341-4328-8527-3e0f8d3dfc21",
    "category_id": "49b5697e-6460-42bb-a089-a58274a8d1d3",
    "external_id": "collector-event-42",
    "fingerprint": "a9d9ad91f12d",
    "title": "Festival al parco",
    "description": "Evento musicale all'aperto.",
    "region": null,
    "province": "Roma",
    "city": "Roma",
    "address": null,
    "latitude": 41.9028,
    "longitude": 12.4964,
    "start_date": "2026-07-10T20:30:00",
    "end_date": "2026-07-10T23:00:00",
    "source_url": "https://example.com/events/festival",
    "quality_score": 100,
    "quality_class": "HIGH"
  }
]
```

## GET /events/{id}

Planned endpoint returning one event by UUID.

```http
GET /events/7ad3a0f1-4f93-4d7b-9e8e-f4af8cf079d3
```

```json
{
  "id": "7ad3a0f1-4f93-4d7b-9e8e-f4af8cf079d3",
  "title": "Festival al parco"
}
```

## GET /events/nearby

Planned endpoint for events near a geographic point. Parameters are `latitude`, `longitude`, optional `radius_km` (default 10), and optional `limit` (default 20).

```http
GET /events/nearby?latitude=41.9028&longitude=12.4964&radius_km=5
```

```json
{
  "items": [],
  "center": {"latitude": 41.9028, "longitude": 12.4964},
  "radius_km": 5
}
```

## GET /categories

Returns categories from PostgreSQL, ordered by name. It has no parameters and returns `[]` when empty.

```http
GET /categories
```

```json
[
  {
    "id": "49b5697e-6460-42bb-a089-a58274a8d1d3",
    "name": "Festival",
    "slug": "festival",
    "description": "Categoria creata automaticamente durante l'importazione SQLite."
  }
]
```

## GET /search

Planned keyword search endpoint. Parameters are `q`, optional `city`, optional `category_id`, `limit`, and `offset`.

```http
GET /search?q=festival&city=Roma
```

```json
{
  "query": "festival",
  "items": [],
  "limit": 20,
  "offset": 0,
  "total": 0
}
```
