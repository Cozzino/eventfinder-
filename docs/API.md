# EventFinder API

Base service: `eventfinder-api`  
Version: `1.0.0`

## GET /health

Returns service health information without querying the database.

```http
GET /health
```

```json
{"status":"ok","service":"eventfinder-api","version":"1.0.0"}
```

## GET /stats

Returns PostgreSQL row totals and the distribution of event quality classes.

```http
GET /stats
```

```json
{
  "events": 553,
  "categories": 8,
  "sources": 9,
  "high_quality_events": 120,
  "medium_quality_events": 300,
  "low_quality_events": 133
}
```

## GET /events

Returns PostgreSQL events ordered by start date and title. Optional parameters are `category_id`, `city`, `province`, `date_from`, `date_to`, `limit` (1-200, default 20), and `offset` (default 0).

```http
GET /events?city=Roma&date_from=2026-07-01T00:00:00&limit=5
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

## GET /categories

Returns categories from PostgreSQL ordered by name, or `[]` when empty.

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

## Planned endpoints

`GET /events/{id}`, `GET /events/nearby`, and `GET /search` remain planned for later milestones.
