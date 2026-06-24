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
{"events":553,"categories":2,"sources":9,"high_quality_events":120,"medium_quality_events":300,"low_quality_events":133}
```

## GET /events

Returns PostgreSQL events ordered by start date and title. Optional parameters: `category_id`, `city`, `province`, `date_from`, `date_to`, `limit`, and `offset`.

```http
GET /events?city=Roma&limit=5
```

## GET /events/nearby

Finds events within a radius using PostGIS `ST_DWithin` and orders them by `ST_Distance`.

Parameters:

- `lat`, `lon`: required center coordinates.
- `radius_km`: optional radius, default 10, maximum 500.
- `category_id`, `date_from`, `date_to`: optional filters.
- `limit`: 1-200, default 20.
- `offset`: non-negative, default 0.

```http
GET /events/nearby?lat=44.4949&lon=11.3426&radius_km=50&limit=5
```

```json
{
  "items": [
    {
      "id": "7ad3a0f1-4f93-4d7b-9e8e-f4af8cf079d3",
      "source_id": "349c4ba9-1341-4328-8527-3e0f8d3dfc21",
      "category_id": "49b5697e-6460-42bb-a089-a58274a8d1d3",
      "external_id": "collector-event-42",
      "fingerprint": "a9d9ad91f12d",
      "title": "Festival di Bologna",
      "description": "Festival nel centro storico.",
      "region": "Emilia-Romagna",
      "province": "Bologna",
      "city": "Bologna",
      "address": null,
      "latitude": 44.4949,
      "longitude": 11.3426,
      "start_date": "2026-07-10T20:30:00",
      "end_date": null,
      "source_url": "https://example.com/festival-bologna",
      "quality_score": 100,
      "quality_class": "HIGH",
      "distance_km": 0.0
    }
  ],
  "center": {"lat": 44.4949, "lon": 11.3426},
  "radius_km": 50.0,
  "limit": 5,
  "offset": 0,
  "total": 1
}
```

## GET /categories

Returns categories from PostgreSQL ordered by name, or `[]` when empty.

```http
GET /categories
```

## GET /search

Searches case-insensitively in `title`, `description`, `city`, and `province`.

Parameters:

- `q`: required search text.
- `category_id`, `city`, `province`, `date_from`, `date_to`: optional filters.
- `limit`: 1-200, default 20.
- `offset`: non-negative, default 0.

```http
GET /search?q=festival&limit=5
```

```json
{
  "query": "festival",
  "items": [
    {
      "id": "7ad3a0f1-4f93-4d7b-9e8e-f4af8cf079d3",
      "source_id": "349c4ba9-1341-4328-8527-3e0f8d3dfc21",
      "category_id": "49b5697e-6460-42bb-a089-a58274a8d1d3",
      "external_id": "collector-event-42",
      "fingerprint": "a9d9ad91f12d",
      "title": "Festival di Bologna",
      "description": "Festival nel centro storico.",
      "region": "Emilia-Romagna",
      "province": "Bologna",
      "city": "Bologna",
      "address": null,
      "latitude": 44.4949,
      "longitude": 11.3426,
      "start_date": "2026-07-10T20:30:00",
      "end_date": null,
      "source_url": "https://example.com/festival-bologna",
      "quality_score": 100,
      "quality_class": "HIGH"
    }
  ],
  "limit": 5,
  "offset": 0,
  "total": 1
}
```

## Planned endpoints

`GET /events/{id}` remains planned for a later milestone.
