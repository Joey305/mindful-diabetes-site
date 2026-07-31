# Admin Analytics Upgrade Implementation Note

## What was found

- The Flask app owns admin authentication in `mindful_diabetes/app.py` using one-time email codes and the configured `ADMIN_EMAIL`.
- Analytics are collected through `POST /analytics/events`, normalized in `mindful_diabetes/analytics.py`, and stored through an `AnalyticsStore` interface.
- The current local analytics backend is SQLite at the configurable `ANALYTICS_LOCAL_PATH`. A remote backend already exists through `RemoteAnalyticsStore`, which keeps the dashboard independent from a specific database.
- Public tracking is handled by `static/js/site-analytics.js` and Free Guide tracking is embedded in `templates/free_guides.html` and `templates/free_guide_detail.html`.
- The project did not include Chart.js, Plotly, Bootstrap, or Tailwind. The upgrade uses server-rendered accessible chart components instead of sending raw events to the browser.

## Files changed

- `mindful_diabetes/analytics.py`: added an explicit repository boundary note, event-name aliases, richer daily aggregation, campaign/action metrics, guide filters, and newer date-range options.
- `mindful_diabetes/app.py`: added dashboard intelligence helpers, opportunity rules, scorecards, funnels, report links, guide detail analytics, named CSV exports, printable report route, and board-summary route.
- `templates/admin_dashboard.html`: rebuilt the admin analytics navigation into focused tabs and added scorecards, funnels, charts, opportunities, reports, and CSV export controls.
- `templates/admin/analytics_guide.html`: added per-guide analytics detail pages.
- `templates/admin/analytics_report.html`: added a print-friendly dashboard report.
- `templates/admin/analytics_board.html`: added a concise board-update summary.
- `static/css/site.css`: added responsive styles for funnels, scorecards, bar charts, donut charts, report controls, and print layout.

## Future Randy connection

Dashboard routes and templates call the analytics repository interface instead of opening SQLite directly. A future Randy-backed repository can replace or extend `RemoteAnalyticsStore` without rewriting the admin dashboard, chart logic, or recommendation rules.
