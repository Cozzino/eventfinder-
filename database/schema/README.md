# Database Schema

M1 defines the PostgreSQL + PostGIS schema for EventFinder Core.

## Files

- `eventfinder_schema.sql`: creates PostGIS support, core tables, future user-facing tables, and indexes.

## Core tables

- `categories`
- `sources`
- `events`
- `sync_logs`

## Future-ready tables

- `users`
- `favorites`
- `saved_searches`

The `events` table stores latitude and longitude and includes a PostGIS GiST expression index for geographic queries.
