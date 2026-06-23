# EventFinder API

Base service: `eventfinder-api`
Version: `1.0.0`

## GET /health

Returns service health information.

Parameters: none.

Example request:

```http
GET /health
```

Example response:

```json
{
  "status": "ok",
  "service": "eventfinder-api",
  "version": "1.0.0"
}
```

## GET /events

Returns a paginated list of events, optionally filtered by location, category, and date.

Parameters:

- `limit` integer, optional, default `20`.
- `offset` integer, optional, default `0`.
- `category_id` UUID, optional.
- `region` string, optional.
- `province` string, optional.
- `city` string, optional.
- `start_date` ISO datetime, optional.
- `end_date` ISO datetime, optional.

Example request:

```http
GET /events?city=Roma&limit=2&offset=0
```

Example response:

```json
{
  "items": [
    {
      "id": "7ad3a0f1-4f93-4d7b-9e8e-f4af8cf079d3",
      "source_id": "349c4ba9-1341-4328-8527-3e0f8d3dfc21",
      "category_id": "49b5697e-6460-42bb-a089-a58274a8d1d3",
      "title": "Concerto al parco",
      "description": "Evento musicale all'aperto.",
      "region": "Lazio",
      "province": "Roma",
      "city": "Roma",
      "address": "Via del Parco 1",
      "latitude": 41.9028,
      "longitude": 12.4964,
      "start_date": "2026-07-10T20:30:00",
      "end_date": "2026-07-10T23:00:00",
      "source_url": "https://example.com/events/concerto",
      "quality_score": 85,
      "quality_class": "high"
    }
  ],
  "limit": 2,
  "offset": 0,
  "total": 1
}
```

## GET /events/{id}

Returns one event by UUID.

Parameters:

- `id` UUID, required path parameter.

Example request:

```http
GET /events/7ad3a0f1-4f93-4d7b-9e8e-f4af8cf079d3
```

Example response:

```json
{
  "id": "7ad3a0f1-4f93-4d7b-9e8e-f4af8cf079d3",
  "source_id": "349c4ba9-1341-4328-8527-3e0f8d3dfc21",
  "category_id": "49b5697e-6460-42bb-a089-a58274a8d1d3",
  "title": "Concerto al parco",
  "description": "Evento musicale all'aperto.",
  "region": "Lazio",
  "province": "Roma",
  "city": "Roma",
  "address": "Via del Parco 1",
  "latitude": 41.9028,
  "longitude": 12.4964,
  "start_date": "2026-07-10T20:30:00",
  "end_date": "2026-07-10T23:00:00",
  "source_url": "https://example.com/events/concerto",
  "quality_score": 85,
  "quality_class": "high"
}
```

## GET /events/nearby

Returns events near a geographic point.

Parameters:

- `latitude` number, required.
- `longitude` number, required.
- `radius_km` number, optional, default `10`.
- `limit` integer, optional, default `20`.

Example request:

```http
GET /events/nearby?latitude=41.9028&longitude=12.4964&radius_km=5
```

Example response:

```json
{
  "items": [
    {
      "id": "7ad3a0f1-4f93-4d7b-9e8e-f4af8cf079d3",
      "title": "Concerto al parco",
      "city": "Roma",
      "latitude": 41.9028,
      "longitude": 12.4964,
      "distance_km": 1.4,
      "start_date": "2026-07-10T20:30:00"
    }
  ],
  "center": {
    "latitude": 41.9028,
    "longitude": 12.4964
  },
  "radius_km": 5
}
```

## GET /categories

Returns available event categories.

Parameters: none.

Example request:

```http
GET /categories
```

Example response:

```json
{
  "items": [
    {
      "id": "49b5697e-6460-42bb-a089-a58274a8d1d3",
      "name": "Musica",
      "slug": "musica",
      "description": "Concerti e spettacoli musicali"
    }
  ]
}
```

## GET /search

Searches events by keyword and optional filters.

Parameters:

- `q` string, required.
- `city` string, optional.
- `category_id` UUID, optional.
- `limit` integer, optional, default `20`.
- `offset` integer, optional, default `0`.

Example request:

```http
GET /search?q=concerto&city=Roma
```

Example response:

```json
{
  "query": "concerto",
  "items": [
    {
      "id": "7ad3a0f1-4f93-4d7b-9e8e-f4af8cf079d3",
      "title": "Concerto al parco",
      "city": "Roma",
      "start_date": "2026-07-10T20:30:00",
      "source_url": "https://example.com/events/concerto"
    }
  ],
  "limit": 20,
  "offset": 0,
  "total": 1
}
```
