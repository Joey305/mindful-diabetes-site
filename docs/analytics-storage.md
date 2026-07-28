# Mindful Diabetes Analytics Storage

The current first-party analytics system uses `ANALYTICS_STORAGE_BACKEND=local`.

Local analytics are stored in SQLite at `ANALYTICS_LOCAL_PATH`, which defaults to `instance/analytics.sqlite3`. On Heroku this is temporary dyno storage, so analytics can reset after a restart, deployment, or dyno replacement.

## Current Environment Variables

- `ANALYTICS_STORAGE_BACKEND=local`
- `ANALYTICS_LOCAL_PATH=/path/to/analytics.sqlite3`
- `ANALYTICS_RETENTION_DAYS=180`
- `ANALYTICS_ENABLE_LOCAL_TESTING=1` to allow local/test event collection
- `ANALYTICS_REPORT_RECIPIENTS=admin@example.org,other-admin@example.org`

## Randy Adapter

The Randy adapter is available through:

- `ANALYTICS_STORAGE_BACKEND=remote`
- `ANALYTICS_REMOTE_BASE_URL=https://randy.rove-vernier.ts.net/mindful-diabetes/analytics`
- `ANALYTICS_REMOTE_API_TOKEN`
- `ANALYTICS_REMOTE_TIMEOUT_SECONDS`

The browser must continue sending analytics only to the Mindful Diabetes Flask app. The Randy API token must never be exposed in public JavaScript.

The Flask app communicates with Randy server-to-server using the same storage interface:

- `store_event(event)`
- `store_events(events)`
- `query_summary(start, end, filters)`
- `query_events(start, end, filters, page, page_size)`
- `export_events(start, end, filters)`
- `cleanup(before_date)`
- `health_check()`

Private Randy API operations:

- `POST /analytics/events` to submit one event
- `POST /analytics/events/batch` to submit a small event batch
- `GET /analytics/summary` to query aggregated metrics by date range
- `GET /analytics/events` to query filtered events
- `GET /analytics/events/export` to export filtered events
- `POST /analytics/cleanup` to delete or aggregate old events
- `GET /analytics/health` for health checks

Remote responses avoid returning personal information and preserve event IDs for idempotency.

## Weekly Report

Run the weekly report manually with:

```bash
flask analytics-send-weekly-summary
```

This does not activate automatic weekly delivery. Later scheduling can be added with Heroku Scheduler, a cron job on Randy, or another existing scheduler.

## Cleanup

Run cleanup with:

```bash
flask analytics-cleanup
```

Cleanup uses `ANALYTICS_RETENTION_DAYS`.
