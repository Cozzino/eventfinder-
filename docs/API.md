# EventFinder API

All paginated endpoints return `items`, `total`, `limit`, and `offset`. The default limit is 20 and the maximum is 100.

## GET /health

```http
GET /health
```

```json
{"status":"ok","service":"eventfinder-api","version":"1.0.0"}
```

## GET /stats

```http
GET /stats
```

## GET /events

Filters: `category_id`, `city`, `province`, `date_from`, and `date_to`.

Ordering:

- `sort_by=start_date` is the default and sorts ascending, with missing dates last.
- `sort_by=quality_score` sorts descending, then by start date.

```http
GET /events?limit=5&offset=0&sort_by=start_date
```

```json
{
  "items": [{"id":"7ad3a0f1-4f93-4d7b-9e8e-f4af8cf079d3","title":"Festival di Bologna"}],
  "total": 553,
  "limit": 5,
  "offset": 0
}
```

## GET /search

Requires `q` and searches case-insensitively in title, description, city, and province. Results sort by `quality_score` descending. Optional filters: `category_id`, `city`, `province`, `date_from`, and `date_to`.

```http
GET /search?q=festival&limit=5
```

```json
{
  "query": "festival",
  "items": [{"id":"67bcd26f-bb6c-4680-aa3c-f9b9533c5734","title":"Biografilm Festival","quality_score":100}],
  "total": 56,
  "limit": 5,
  "offset": 0
}
```

## GET /events/nearby

Requires `lat` and `lon`. Uses PostGIS `ST_DWithin` and `ST_Distance`, sorted by distance ascending.

- `radius_km`: default 25, greater than 0, maximum 200.
- Optional filters: `category_id`, `date_from`, and `date_to`.
- Invalid or missing coordinates and out-of-range values return HTTP 422 with the offending parameter in `detail`.

```http
GET /events/nearby?lat=44.4949&lon=11.3426&radius_km=50&limit=5
```

```json
{
  "items": [{"id":"eff7395f-1643-437e-bd25-9bacbdb9931c","title":"Viva Varda!","distance_km":0.098}],
  "total": 59,
  "limit": 5,
  "offset": 0,
  "center": {"lat":44.4949,"lon":11.3426},
  "radius_km": 50.0
}
```

## GET /categories

```http
GET /categories
```

## CORS

CORS is enabled for all origins, methods, and headers for Flutter development clients. Credentials are disabled.
