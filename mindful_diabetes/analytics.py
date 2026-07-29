import csv
import io
import json
import re
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.parse import urlparse


SCHEMA_VERSION = 1
MAX_ANALYTICS_PAYLOAD_BYTES = 32_000
MAX_BATCH_SIZE = 20
DEFAULT_RETENTION_DAYS = 180

VALID_EVENT_NAMES = {
    "page_view",
    "cta_impression",
    "donation_cta_click",
    "paypal_click",
    "donation_checkout_started",
    "donation_completed",
    "health_tool_click",
    "newsletter_form_view",
    "newsletter_form_interaction",
    "newsletter_signup",
    "outbound_link_click",
    "content_cta_click",
    "resource_download_click",
    "sponsor_click",
    "event_registration_click",
    "volunteer_cta_click",
}

EVENT_CATEGORIES = {
    "page_view": "content",
    "cta_impression": "impression",
    "donation_cta_click": "donation",
    "paypal_click": "donation",
    "donation_checkout_started": "donation",
    "donation_completed": "donation",
    "health_tool_click": "health_tool",
    "newsletter_form_view": "newsletter",
    "newsletter_form_interaction": "newsletter",
    "newsletter_signup": "newsletter",
    "outbound_link_click": "outbound",
    "content_cta_click": "content",
    "resource_download_click": "resource",
    "sponsor_click": "sponsor",
    "event_registration_click": "event",
    "volunteer_cta_click": "volunteer",
}

ALLOWED_METADATA_KEYS = {
    "campaign_id",
    "campaign_name",
    "donation_kind",
    "frequency",
    "provider",
    "checkout_observed",
    "completion_source",
    "tool_id",
    "tool_name",
    "tool_slug",
    "tool_destination_type",
    "signup_form_id",
    "block_position",
    "attribution_source",
    "provider_outcome",
    "subscriber_status",
    "accepted",
    "related_article",
    "resource_id",
    "resource_type",
    "sponsor_id",
    "event_id",
    "volunteer_role",
    "link_kind",
}

STRING_LIMITS = {
    "event_id": 96,
    "event_name": 64,
    "event_category": 48,
    "client_occurred_at": 40,
    "page_path": 240,
    "page_title": 180,
    "content_id": 96,
    "content_type": 32,
    "article_group": 80,
    "element_id": 120,
    "element_label": 160,
    "element_type": 64,
    "element_position": 96,
    "destination_url": 360,
    "destination_domain": 160,
    "referrer_url": 360,
    "referrer_domain": 160,
    "source": 120,
    "medium": 120,
    "campaign": 120,
    "term": 120,
    "campaign_content": 120,
    "anonymous_session_id": 96,
    "device_category": 16,
    "environment": 32,
}

EVENT_COLUMNS = [
    "event_id",
    "schema_version",
    "event_name",
    "event_category",
    "occurred_at",
    "client_occurred_at",
    "page_path",
    "page_title",
    "content_id",
    "content_type",
    "article_group",
    "element_id",
    "element_label",
    "element_type",
    "element_position",
    "destination_url",
    "destination_domain",
    "referrer_url",
    "referrer_domain",
    "source",
    "medium",
    "campaign",
    "term",
    "campaign_content",
    "anonymous_session_id",
    "device_category",
    "environment",
    "metadata_json",
]

CTA_CLICK_EVENTS = {
    "donation_cta_click",
    "paypal_click",
    "health_tool_click",
    "content_cta_click",
    "resource_download_click",
    "sponsor_click",
    "event_registration_click",
    "volunteer_cta_click",
}

EXCLUDED_PUBLIC_PATH_PREFIXES = ("/admin", "/analytics", "/static")


class AnalyticsValidationError(ValueError):
    pass


class AnalyticsStore:
    def store_event(self, event):
        raise NotImplementedError

    def store_events(self, events):
        inserted = 0
        duplicates = 0
        for event in events:
            if self.store_event(event):
                inserted += 1
            else:
                duplicates += 1
        return {"inserted": inserted, "duplicates": duplicates}

    def query_summary(self, start, end, filters=None):
        raise NotImplementedError

    def query_events(self, start, end, filters=None, page=1, page_size=50):
        raise NotImplementedError

    def export_events(self, start, end, filters=None):
        raise NotImplementedError

    def cleanup(self, before_date):
        raise NotImplementedError

    def health_check(self):
        raise NotImplementedError


class LocalAnalyticsStore(AnalyticsStore):
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def connect(self):
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA busy_timeout=3000")
        return connection

    def _ensure_schema(self):
        with self.connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS analytics_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL UNIQUE,
                    schema_version INTEGER NOT NULL,
                    event_name TEXT NOT NULL,
                    event_category TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    client_occurred_at TEXT,
                    page_path TEXT,
                    page_title TEXT,
                    content_id TEXT,
                    content_type TEXT,
                    article_group TEXT,
                    element_id TEXT,
                    element_label TEXT,
                    element_type TEXT,
                    element_position TEXT,
                    destination_url TEXT,
                    destination_domain TEXT,
                    referrer_url TEXT,
                    referrer_domain TEXT,
                    source TEXT,
                    medium TEXT,
                    campaign TEXT,
                    term TEXT,
                    campaign_content TEXT,
                    anonymous_session_id TEXT,
                    device_category TEXT,
                    environment TEXT,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL
                )
                """
            )
            for column in (
                "occurred_at",
                "event_name",
                "page_path",
                "content_id",
                "article_group",
                "destination_domain",
                "anonymous_session_id",
                "campaign",
                "environment",
            ):
                connection.execute(f"CREATE INDEX IF NOT EXISTS idx_analytics_{column} ON analytics_events ({column})")

    def store_event(self, event):
        row = {column: event.get(column, "") for column in EVENT_COLUMNS}
        row["metadata_json"] = json.dumps(event.get("metadata") or {}, sort_keys=True)
        row["created_at"] = event["occurred_at"]
        with self.connect() as connection:
            try:
                connection.execute(
                    """
                    INSERT INTO analytics_events (
                        event_id, schema_version, event_name, event_category, occurred_at,
                        client_occurred_at, page_path, page_title, content_id, content_type,
                        article_group, element_id, element_label, element_type, element_position,
                        destination_url, destination_domain, referrer_url, referrer_domain, source,
                        medium, campaign, term, campaign_content, anonymous_session_id,
                        device_category, environment, metadata_json, created_at
                    )
                    VALUES (
                        :event_id, :schema_version, :event_name, :event_category, :occurred_at,
                        :client_occurred_at, :page_path, :page_title, :content_id, :content_type,
                        :article_group, :element_id, :element_label, :element_type, :element_position,
                        :destination_url, :destination_domain, :referrer_url, :referrer_domain, :source,
                        :medium, :campaign, :term, :campaign_content, :anonymous_session_id,
                        :device_category, :environment, :metadata_json, :created_at
                    )
                    """,
                    row,
                )
            except sqlite3.IntegrityError:
                return False
        return True

    def query_summary(self, start, end, filters=None):
        filters = filters or {}
        previous_start = start - (end - start)
        previous_end = start
        current = self._period_summary(start, end, filters)
        previous = self._period_summary(previous_start, previous_end, filters)
        current["previous"] = previous["totals"]
        current["comparison"] = {
            key: compare_counts(current["totals"].get(key, 0), previous["totals"].get(key, 0))
            for key in current["totals"]
        }
        return current

    def _period_summary(self, start, end, filters=None):
        filters = filters or {}
        totals = {
            "page_views": self._count(start, end, filters, event_name="page_view"),
            "anonymous_sessions": self._distinct_sessions(start, end, filters),
            "donation_cta_clicks": self._count(start, end, filters, event_name="donation_cta_click"),
            "paypal_clicks": self._count(start, end, filters, event_name="paypal_click"),
            "checkout_starts": self._count(start, end, filters, event_name="donation_checkout_started"),
            "confirmed_donations": self._count(start, end, filters, event_name="donation_completed"),
            "health_tool_clicks": self._count(start, end, filters, event_name="health_tool_click"),
            "newsletter_signups": self._count(start, end, filters, event_name="newsletter_signup"),
            "newsletter_views": self._count(start, end, filters, event_name="newsletter_form_view"),
            "newsletter_interactions": self._count(start, end, filters, event_name="newsletter_form_interaction"),
            "cta_impressions": self._count(start, end, filters, event_name="cta_impression"),
        }
        return {
            "totals": totals,
            "top_pages": self._group_counts(start, end, filters, "page_path", event_name="page_view", limit=10),
            "top_content": self._content_table(start, end, filters),
            "article_groups": self._group_counts(start, end, filters, "article_group", limit=10),
            "donation_sources": self._group_counts(start, end, filters, "page_path", event_names=["donation_cta_click", "paypal_click"], limit=8),
            "donation_positions": self._group_counts(start, end, filters, "element_position", event_names=["donation_cta_click", "paypal_click"], limit=8),
            "donation_campaigns": self._group_counts(start, end, filters, "campaign", event_names=["donation_cta_click", "paypal_click"], limit=8),
            "health_tools": self._group_counts(start, end, filters, "element_label", event_name="health_tool_click", limit=8),
            "health_tool_pages": self._group_counts(start, end, filters, "page_path", event_name="health_tool_click", limit=8),
            "newsletter_pages": self._group_counts(start, end, filters, "page_path", event_name="newsletter_signup", limit=8),
            "newsletter_referrers": self._group_counts(start, end, filters, "referrer_domain", event_name="newsletter_signup", limit=8),
            "newsletter_sources": self._group_counts(start, end, filters, "source", event_name="newsletter_signup", limit=8),
            "device_categories": self._group_counts(start, end, filters, "device_category", limit=8),
            "traffic_sources": self._traffic_sources(start, end, filters),
            "cta_performance": self._cta_performance(start, end, filters),
            "daily_trend": self._daily_trend(start, end, filters),
        }

    def query_events(self, start, end, filters=None, page=1, page_size=50):
        page = max(1, int(page or 1))
        page_size = max(1, min(200, int(page_size or 50)))
        where, params = self._where(start, end, filters)
        offset = (page - 1) * page_size
        with self.connect() as connection:
            total = connection.execute(f"SELECT COUNT(*) FROM analytics_events {where}", params).fetchone()[0]
            rows = connection.execute(
                f"""
                SELECT * FROM analytics_events
                {where}
                ORDER BY occurred_at DESC, id DESC
                LIMIT ? OFFSET ?
                """,
                [*params, page_size, offset],
            ).fetchall()
        return {
            "events": [event_from_row(row) for row in rows],
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": max(1, (total + page_size - 1) // page_size),
        }

    def export_events(self, start, end, filters=None):
        result = self.query_events(start, end, filters, page=1, page_size=5000)
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Exported at", utc_now_iso()])
        writer.writerow([])
        writer.writerow(["Time", "Event", "Category", "Source page", "Page title", "Element label", "Position", "Destination", "Campaign", "Source", "Device"])
        for event in result["events"]:
            writer.writerow(
                [
                    csv_safe(event["occurred_at"]),
                    csv_safe(event["event_name"]),
                    csv_safe(event["event_category"]),
                    csv_safe(event["page_path"]),
                    csv_safe(event["page_title"]),
                    csv_safe(event["element_label"]),
                    csv_safe(event["element_position"]),
                    csv_safe(event["destination_url"]),
                    csv_safe(event["campaign"]),
                    csv_safe(event["source"]),
                    csv_safe(event["device_category"]),
                ]
            )
        return output.getvalue()

    def cleanup(self, before_date):
        before = to_utc_iso(before_date)
        with self.connect() as connection:
            cursor = connection.execute("DELETE FROM analytics_events WHERE occurred_at < ?", (before,))
            return cursor.rowcount

    def health_check(self):
        try:
            with self.connect() as connection:
                row = connection.execute(
                    "SELECT COUNT(*) AS count, MAX(occurred_at) AS last_recorded_at FROM analytics_events"
                ).fetchone()
            return {
                "ok": True,
                "backend": "local",
                "path": str(self.path),
                "event_count": row["count"],
                "last_recorded_at": row["last_recorded_at"] or "",
            }
        except sqlite3.Error as error:
            return {"ok": False, "backend": "local", "error": str(error), "event_count": 0, "last_recorded_at": ""}

    def _count(self, start, end, filters=None, event_name=None):
        where_filters = dict(filters or {})
        if event_name:
            where_filters["event_name"] = event_name
        where, params = self._where(start, end, where_filters)
        with self.connect() as connection:
            return connection.execute(f"SELECT COUNT(*) FROM analytics_events {where}", params).fetchone()[0]

    def _distinct_sessions(self, start, end, filters=None):
        where, params = self._where(start, end, filters)
        with self.connect() as connection:
            return connection.execute(
                f"SELECT COUNT(DISTINCT anonymous_session_id) FROM analytics_events {where} AND anonymous_session_id != ''",
                params,
            ).fetchone()[0]

    def _group_counts(self, start, end, filters, column, event_name=None, event_names=None, limit=10):
        where_filters = dict(filters or {})
        if event_name:
            where_filters["event_name"] = event_name
        where, params = self._where(start, end, where_filters)
        if event_names:
            placeholders = ",".join("?" for _ in event_names)
            where = f"{where} AND event_name IN ({placeholders})"
            params.extend(event_names)
        with self.connect() as connection:
            rows = connection.execute(
                f"""
                SELECT COALESCE(NULLIF({column}, ''), 'Unknown') AS label,
                       COUNT(*) AS count,
                       COUNT(DISTINCT anonymous_session_id) AS sessions
                FROM analytics_events
                {where}
                GROUP BY label
                ORDER BY count DESC, label ASC
                LIMIT ?
                """,
                [*params, limit],
            ).fetchall()
        return [dict(row) for row in rows if row["label"] != "Unknown" or row["count"]]

    def _content_table(self, start, end, filters):
        where, params = self._where(start, end, filters)
        with self.connect() as connection:
            rows = connection.execute(
                f"""
                SELECT COALESCE(NULLIF(page_path, ''), 'Unknown') AS page,
                       MAX(page_title) AS title,
                       MAX(article_group) AS article_group,
                       COUNT(CASE WHEN event_name = 'page_view' THEN 1 END) AS views,
                       COUNT(DISTINCT CASE WHEN event_name = 'page_view' THEN anonymous_session_id END) AS sessions,
                       COUNT(CASE WHEN event_name = 'donation_cta_click' THEN 1 END) AS donation_clicks,
                       COUNT(CASE WHEN event_name = 'paypal_click' THEN 1 END) AS paypal_clicks,
                       COUNT(CASE WHEN event_name = 'health_tool_click' THEN 1 END) AS tool_clicks,
                       COUNT(CASE WHEN event_name = 'newsletter_signup' THEN 1 END) AS newsletter_signups
                FROM analytics_events
                {where}
                GROUP BY page
                ORDER BY views DESC, donation_clicks DESC, paypal_clicks DESC, tool_clicks DESC, page ASC
                LIMIT 25
                """,
                params,
            ).fetchall()
        return [dict(row) for row in rows]

    def _daily_trend(self, start, end, filters):
        where, params = self._where(start, end, filters)
        with self.connect() as connection:
            rows = connection.execute(
                f"""
                SELECT substr(occurred_at, 1, 10) AS day,
                       COUNT(CASE WHEN event_name = 'page_view' THEN 1 END) AS page_views,
                       COUNT(CASE WHEN event_name = 'donation_cta_click' THEN 1 END) AS donation_clicks,
                       COUNT(CASE WHEN event_name = 'paypal_click' THEN 1 END) AS paypal_clicks,
                       COUNT(CASE WHEN event_name = 'health_tool_click' THEN 1 END) AS tool_clicks,
                       COUNT(CASE WHEN event_name = 'newsletter_signup' THEN 1 END) AS newsletter_signups
                FROM analytics_events
                {where}
                GROUP BY day
                ORDER BY day ASC
                """,
                params,
            ).fetchall()
        return [dict(row) for row in rows]

    def _traffic_sources(self, start, end, filters):
        where_filters = dict(filters or {})
        where_filters["event_name"] = "page_view"
        where, params = self._where(start, end, where_filters)
        with self.connect() as connection:
            rows = connection.execute(
                f"""
                SELECT CASE
                         WHEN source != '' THEN source
                         WHEN referrer_domain != '' THEN referrer_domain
                         ELSE 'Direct / unknown'
                       END AS label,
                       COUNT(*) AS count,
                       COUNT(DISTINCT anonymous_session_id) AS sessions
                FROM analytics_events
                {where}
                GROUP BY label
                ORDER BY count DESC, label ASC
                LIMIT 10
                """,
                params,
            ).fetchall()
        return [dict(row) for row in rows]

    def _cta_performance(self, start, end, filters):
        where, params = self._where(start, end, filters)
        click_events = sorted(CTA_CLICK_EVENTS)
        events = ["cta_impression", *click_events]
        placeholders = ",".join("?" for _ in events)
        with self.connect() as connection:
            rows = connection.execute(
                f"""
                SELECT COALESCE(NULLIF(element_id, ''), NULLIF(element_label, ''), page_path) AS element_key,
                       MAX(element_label) AS label,
                       page_path AS page,
                       element_position AS position,
                       COUNT(CASE WHEN event_name = 'cta_impression' THEN 1 END) AS impressions,
                       COUNT(CASE WHEN event_name IN ({','.join('?' for _ in click_events)}) THEN 1 END) AS clicks,
                       COUNT(DISTINCT CASE WHEN event_name IN ({','.join('?' for _ in click_events)}) THEN anonymous_session_id END) AS sessions
                FROM analytics_events
                {where} AND event_name IN ({placeholders})
                GROUP BY element_key, page_path, element_position
                HAVING impressions > 0 OR clicks > 0
                ORDER BY clicks DESC, impressions DESC, label ASC
                LIMIT 25
                """,
                [*click_events, *click_events, *params, *events],
            ).fetchall()
        performance = [dict(row) for row in rows]
        for row in performance:
            row["click_rate"] = numeric_rate(row.get("clicks", 0), row.get("impressions", 0))
            row["click_rate_label"] = percent_label(row["click_rate"])
        return performance

    def _where(self, start, end, filters=None):
        filters = filters or {}
        clauses = ["occurred_at >= ?", "occurred_at < ?", "COALESCE(page_path, '') NOT LIKE '/admin%'", "COALESCE(page_path, '') NOT LIKE '/analytics%'", "COALESCE(page_path, '') NOT LIKE '/static%'"]
        params = [to_utc_iso(start), to_utc_iso(end)]
        column_filters = {
            "event_name",
            "event_category",
            "page_path",
            "content_type",
            "article_group",
            "element_position",
            "destination_domain",
            "device_category",
            "campaign",
            "environment",
            "content_id",
        }
        for key in sorted(column_filters):
            value = (filters.get(key) or "").strip() if isinstance(filters.get(key), str) else filters.get(key)
            if value:
                clauses.append(f"{key} = ?")
                params.append(value)
        return "WHERE " + " AND ".join(clauses), params


class RemoteAnalyticsStore(AnalyticsStore):
    def __init__(self, base_url, api_token, timeout_seconds=5):
        self.base_url = (base_url or "").rstrip("/")
        self.api_token = api_token or ""
        self.timeout_seconds = float(timeout_seconds or 5)
        if not self.base_url:
            raise ValueError("ANALYTICS_REMOTE_BASE_URL is required for remote analytics storage.")
        if not self.api_token:
            raise ValueError("ANALYTICS_REMOTE_API_TOKEN is required for remote analytics storage.")

    def store_event(self, event):
        result = self._request("POST", "/events", payload=event)
        return bool(result.get("inserted"))

    def store_events(self, events):
        return self._request("POST", "/events/batch", payload=events)

    def query_summary(self, start, end, filters=None):
        return self._request("GET", "/summary", params=remote_params(start, end, filters))

    def query_events(self, start, end, filters=None, page=1, page_size=50):
        params = remote_params(start, end, filters)
        params.update({"page": str(page), "page_size": str(page_size)})
        return self._request("GET", "/events", params=params)

    def export_events(self, start, end, filters=None):
        return self._request("GET", "/events/export", params=remote_params(start, end, filters), raw_text=True)

    def cleanup(self, before_date):
        result = self._request("POST", "/cleanup", payload={"before_date": to_utc_iso(before_date)})
        return int(result.get("removed", 0))

    def health_check(self):
        return self._request("GET", "/health")

    def _request(self, method, path, payload=None, params=None, raw_text=False):
        query = f"?{urlencode(params or {})}" if params else ""
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        request_obj = Request(
            f"{self.base_url}{path}{query}",
            data=body,
            method=method,
            headers={
                "Authorization": f"Bearer {self.api_token}",
                "Accept": "text/csv" if raw_text else "application/json",
                "Content-Type": "application/json",
            },
        )
        try:
            with urlopen(request_obj, timeout=self.timeout_seconds) as response:
                raw_body = response.read().decode("utf-8")
                if raw_text:
                    return raw_body
                return json.loads(raw_body or "{}")
        except HTTPError as error:
            try:
                body_json = json.loads(error.read().decode("utf-8"))
                message = body_json.get("message") or body_json.get("error")
            except (json.JSONDecodeError, UnicodeDecodeError):
                message = None
            raise RuntimeError(message or f"Remote analytics request failed with HTTP {error.code}.") from error
        except URLError as error:
            raise RuntimeError("Remote analytics storage could not be reached.") from error


def analytics_store(config):
    backend = (config.get("ANALYTICS_STORAGE_BACKEND") or "local").lower()
    if backend == "remote":
        return RemoteAnalyticsStore(
            config.get("ANALYTICS_REMOTE_BASE_URL"),
            config.get("ANALYTICS_REMOTE_API_TOKEN"),
            config.get("ANALYTICS_REMOTE_TIMEOUT_SECONDS", 5),
        )
    return LocalAnalyticsStore(config.get("ANALYTICS_LOCAL_PATH"))


def analytics_enabled(config):
    if truthy(config.get("ANALYTICS_ENABLE_LOCAL_TESTING")):
        return True
    if config.get("TESTING"):
        return False
    if config.get("DEBUG"):
        return False
    return True


def normalize_event_payload(payload, config, now=None):
    if not isinstance(payload, dict):
        raise AnalyticsValidationError("Each analytics event must be an object.")
    event_name = clean_string(payload.get("event_name"), "event_name", required=True)
    if event_name not in VALID_EVENT_NAMES:
        raise AnalyticsValidationError("Unknown analytics event name.")

    metadata = payload.get("metadata") or {}
    if not isinstance(metadata, dict):
        raise AnalyticsValidationError("Analytics metadata must be an object.")
    clean_metadata = clean_metadata_fields(metadata)

    clean_event = {
        "event_id": clean_event_id(payload.get("event_id")),
        "schema_version": SCHEMA_VERSION,
        "event_name": event_name,
        "event_category": EVENT_CATEGORIES[event_name],
        "occurred_at": to_utc_iso(now or utc_now()),
        "metadata": clean_metadata,
    }
    for field in EVENT_COLUMNS:
        if field in {"event_id", "schema_version", "event_name", "event_category", "occurred_at", "metadata_json"}:
            continue
        value = payload.get(field)
        clean_event[field] = clean_string(value, field, required=False)

    if clean_event["device_category"] and clean_event["device_category"] not in {"desktop", "tablet", "mobile"}:
        raise AnalyticsValidationError("Device category is not valid.")
    if clean_event["content_type"] and clean_event["content_type"] not in {"page", "post", "static", "cms_page", "cms_post"}:
        raise AnalyticsValidationError("Content type is not valid.")

    clean_event["destination_domain"] = clean_event["destination_domain"] or domain_for(clean_event["destination_url"])
    clean_event["referrer_domain"] = clean_event["referrer_domain"] or domain_for(clean_event["referrer_url"])
    clean_event["environment"] = clean_event["environment"] or analytics_environment(config)
    if not is_public_analytics_path(clean_event["page_path"]):
        raise AnalyticsValidationError("Analytics event path is not public.")
    return clean_event


def parse_event_request(request_obj, config):
    if request_obj.content_length and request_obj.content_length > MAX_ANALYTICS_PAYLOAD_BYTES:
        raise AnalyticsValidationError("Analytics payload is too large.")
    if not request_obj.is_json:
        raise AnalyticsValidationError("Analytics endpoint accepts JSON only.")
    payload = request_obj.get_json(silent=True)
    if payload is None:
        raise AnalyticsValidationError("Analytics payload was not valid JSON.")
    raw_events = payload if isinstance(payload, list) else [payload]
    if len(raw_events) > MAX_BATCH_SIZE:
        raise AnalyticsValidationError("Analytics event batch is too large.")
    return [normalize_event_payload(event, config) for event in raw_events]


def clean_metadata_fields(metadata):
    clean = {}
    for key, value in metadata.items():
        if key not in ALLOWED_METADATA_KEYS:
            raise AnalyticsValidationError("Analytics metadata contains an unknown field.")
        if isinstance(value, bool):
            clean[key] = value
        elif value is None:
            clean[key] = ""
        elif isinstance(value, (int, float)):
            clean[key] = value
        elif isinstance(value, str):
            clean[key] = clamp(value, 160)
        else:
            raise AnalyticsValidationError("Analytics metadata values must be simple.")
    return clean


def clean_event_id(value):
    if value is None or value == "":
        return str(uuid.uuid4())
    cleaned = clean_string(value, "event_id", required=True)
    if not re.fullmatch(r"[A-Za-z0-9_.:-]{8,96}", cleaned):
        raise AnalyticsValidationError("Analytics event ID is not valid.")
    return cleaned


def clean_string(value, field, required=False):
    if value is None:
        if required:
            raise AnalyticsValidationError(f"{field} is required.")
        return ""
    if not isinstance(value, str):
        raise AnalyticsValidationError(f"{field} must be text.")
    value = value.strip()
    if required and not value:
        raise AnalyticsValidationError(f"{field} is required.")
    limit = STRING_LIMITS.get(field, 160)
    if len(value) > limit:
        raise AnalyticsValidationError(f"{field} is too long.")
    return value


def event_from_row(row):
    event = {key: row[key] for key in row.keys() if key not in {"id", "metadata_json", "created_at"}}
    try:
        event["metadata"] = json.loads(row["metadata_json"] or "{}")
    except json.JSONDecodeError:
        event["metadata"] = {}
    event["occurred_at_label"] = label_for_timestamp(event["occurred_at"])
    return event


def filters_from_args(args):
    keys = {
        "event_name",
        "event_category",
        "page_path",
        "content_type",
        "article_group",
        "element_position",
        "destination_domain",
        "device_category",
        "campaign",
        "environment",
        "content_id",
    }
    return {key: args.get(key, "").strip() for key in keys if args.get(key, "").strip()}


def remote_params(start, end, filters=None):
    params = {"start": to_utc_iso(start), "end": to_utc_iso(end)}
    for key, value in (filters or {}).items():
        if value:
            params[key] = value
    return params


def date_range_from_args(args, default_days=30):
    today = utc_now().date()
    range_name = (args.get("range") or f"{default_days}d").strip()
    if range_name == "today":
        start = datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc)
        end = start + timedelta(days=1)
    elif range_name in {"7d", "30d", "90d"}:
        days = int(range_name.removesuffix("d"))
        end = datetime.combine(today + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
        start = end - timedelta(days=days)
    elif range_name == "custom":
        start = parse_date_arg(args.get("start")) or datetime.combine(today - timedelta(days=default_days - 1), datetime.min.time(), tzinfo=timezone.utc)
        end_day = parse_date_arg(args.get("end")) or datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc)
        end = end_day + timedelta(days=1)
    else:
        range_name = f"{default_days}d"
        end = datetime.combine(today + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
        start = end - timedelta(days=default_days)
    return start, end, range_name


def parse_date_arg(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


ARTICLE_GROUP_OVERRIDES = {
    "fats-guide": "nutrition",
    "dash-diet": "nutrition",
    "indian-cuisine-for-diabetes-wellness": "nutrition",
    "healthy-eating": "nutrition",
    "glycemix-index-and-diabetes": "nutrition",
    "diabetes-management-and-diet": "nutrition",
    "eating-right-dietary-path-type-ii-type-iii-diabetes-prevention": "nutrition",
    "summer-diabetes": "diabetes management",
    "summer-diabetes-management": "diabetes management",
    "mounjaro-and-ozempic": "diabetes management",
    "community-support-for-type-3-diabetes": "diabetes management",
    "alzheimers-clinical-trials-june-2026": "Alzheimer's disease",
    "ipsc-alzheimers-modeling": "Alzheimer's disease",
    "diabetes-health-jeir-updates": "health tools",
    "diabetes-artificial-intelligence-jeir": "health tools",
    "memovela": "health tools",
    "daily-wellness-habits": "health tools",
}


def article_group_for_path(content, path):
    path = (path or "").strip("/")
    if not path:
        return "nonprofit updates"
    if path in ARTICLE_GROUP_OVERRIDES:
        return ARTICLE_GROUP_OVERRIDES[path]
    if path in {"research"}:
        return "research"
    if path in {"health-tools"}:
        return "health tools"
    if path in {"donation", "donate"}:
        return "nonprofit updates"
    if path in {"volunteer", "sponsors"}:
        return "community stories"
    item = getattr(content, "posts_by_slug", {}).get(path) or getattr(content, "pages_by_slug", {}).get(path)
    haystack = f"{item.get('title', '')} {item.get('slug', '')} {item.get('excerpt_text', '')}".lower() if item else path.lower()
    if any(term in haystack for term in ["recipe", "meal", "nutrition", "eating", "food"]):
        return "nutrition"
    if any(term in haystack for term in ["alzheimer", "brain", "cognitive", "dementia"]):
        return "Alzheimer's disease"
    if any(term in haystack for term in ["research", "study", "clinical", "trial", "biomarker", "therapy"]):
        return "research"
    if any(term in haystack for term in ["jeir", "memovela", "tool", "ai"]):
        return "health tools"
    if "diabetes" in haystack:
        return "diabetes management"
    return "nonprofit updates"


def is_public_analytics_path(path):
    path = path or "/"
    return not any(path.startswith(prefix) for prefix in EXCLUDED_PUBLIC_PATH_PREFIXES)


def content_context_for_path(content, path):
    slug = (path or "").strip("/")
    if not slug:
        item = getattr(content, "pages_by_slug", {}).get("mindful")
        return {"content_id": "static-home", "content_type": "static", "article_group": "nonprofit updates", "page_title": "Homepage"}
    item = getattr(content, "posts_by_slug", {}).get(slug)
    if item:
        return {"content_id": item.get("id") or slug, "content_type": "post", "article_group": article_group_for_path(content, path), "page_title": item.get("title", slug)}
    item = getattr(content, "pages_by_slug", {}).get(slug)
    if item:
        return {"content_id": item.get("id") or slug, "content_type": "page", "article_group": article_group_for_path(content, path), "page_title": item.get("title", slug)}
    return {"content_id": "", "content_type": "static", "article_group": article_group_for_path(content, path), "page_title": ""}


def enrich_event_with_request(event, request_obj, content):
    path = event.get("page_path") or request_obj.path or ""
    context = content_context_for_path(content, path)
    for key, value in context.items():
        event[key] = event.get(key) or value
    event["referrer_url"] = event.get("referrer_url") or (request_obj.referrer or "")
    event["referrer_domain"] = event.get("referrer_domain") or domain_for(event["referrer_url"])
    event["environment"] = event.get("environment") or analytics_environment(request_obj.environ.get("flask.app_config", {}))
    return event


def analytics_environment(config):
    if config.get("TESTING"):
        return "test"
    return config.get("ANALYTICS_ENVIRONMENT") or ("production" if config.get("DYNO") or not config.get("DEBUG") else "development")


def storage_health(config):
    try:
        return analytics_store(config).health_check()
    except Exception as error:
        return {"ok": False, "backend": config.get("ANALYTICS_STORAGE_BACKEND", "local"), "error": str(error), "event_count": 0, "last_recorded_at": ""}


def temporary_storage_active(config):
    return (config.get("ANALYTICS_STORAGE_BACKEND") or "local").lower() == "local"


def build_empty_summary():
    return {
        "totals": {},
        "previous": {},
        "comparison": {},
        "top_pages": [],
        "top_content": [],
        "article_groups": [],
        "donation_sources": [],
        "donation_positions": [],
        "donation_campaigns": [],
        "health_tools": [],
        "health_tool_pages": [],
        "newsletter_pages": [],
        "newsletter_referrers": [],
        "newsletter_sources": [],
        "device_categories": [],
        "traffic_sources": [],
        "cta_performance": [],
        "daily_trend": [],
    }


def compare_counts(current, previous):
    current = int(current or 0)
    previous = int(previous or 0)
    if previous == 0 and current == 0:
        return {"label": "No previous activity", "direction": "flat", "percent": None}
    if previous == 0:
        return {"label": "New activity this period", "direction": "up", "percent": None}
    change = ((current - previous) / previous) * 100
    direction = "up" if change > 0 else "down" if change < 0 else "flat"
    return {"label": f"{change:+.0f}% vs previous period", "direction": direction, "percent": change}


def click_rate(clicks, views):
    clicks = int(clicks or 0)
    views = int(views or 0)
    if views <= 0:
        return "No page views"
    return f"{(clicks / views) * 100:.1f}%"


def numeric_rate(numerator, denominator):
    denominator = int(denominator or 0)
    if denominator <= 0:
        return None
    return (int(numerator or 0) / denominator) * 100


def percent_label(value):
    if value is None:
        return "No impressions"
    return f"{value:.1f}%"


def weekly_summary(config, end=None):
    end = end or datetime.combine(utc_now().date(), datetime.min.time(), tzinfo=timezone.utc)
    start = end - timedelta(days=7)
    store = analytics_store(config)
    summary = store.query_summary(start, end, {"environment": analytics_environment(config)})
    top_page = (summary["top_pages"] or [{"label": "No page activity", "count": 0}])[0]
    top_group = (summary["article_groups"] or [{"label": "No article group", "count": 0}])[0]
    top_tool = (summary["health_tools"] or [{"label": "No health-tool clicks", "count": 0}])[0]
    top_source = (summary["newsletter_sources"] or summary["newsletter_referrers"] or [{"label": "No source activity", "count": 0}])[0]
    top_traffic_source = (summary.get("traffic_sources") or [{"label": "No traffic source activity", "count": 0}])[0]
    top_cta = (summary.get("cta_performance") or [{"label": "No CTA activity", "clicks": 0, "impressions": 0, "click_rate_label": "No impressions"}])[0]
    return {
        "start": start,
        "end": end,
        "summary": summary,
        "top_page": top_page,
        "top_group": top_group,
        "top_tool": top_tool,
        "top_source": top_source,
        "top_traffic_source": top_traffic_source,
        "top_cta": top_cta,
    }


def format_weekly_summary_text(report, admin_url="/admin/analytics/"):
    totals = report["summary"]["totals"]
    changes = meaningful_changes(report["summary"].get("comparison", {}))
    return "\n".join(
        [
            "Mindful Diabetes weekly analytics summary",
            f"Period: {report['start'].date()} through {(report['end'] - timedelta(days=1)).date()}",
            "",
            f"Page views: {totals.get('page_views', 0)}",
            f"Anonymous sessions: {totals.get('anonymous_sessions', 0)}",
            f"Top page: {report['top_page']['label']} ({report['top_page']['count']})",
            f"Top article group: {report['top_group']['label']} ({report['top_group']['count']})",
            f"Donation CTA clicks: {totals.get('donation_cta_clicks', 0)}",
            f"PayPal opens: {totals.get('paypal_clicks', 0)}",
            f"Health-tool clicks: {totals.get('health_tool_clicks', 0)}",
            f"Top health tool: {report['top_tool']['label']} ({report['top_tool']['count']})",
            f"Newsletter signups: {totals.get('newsletter_signups', 0)}",
            f"Strongest traffic source: {report['top_traffic_source']['label']} ({report['top_traffic_source']['count']})",
            f"Top CTA: {report['top_cta'].get('label') or report['top_cta'].get('element_key')} ({report['top_cta'].get('clicks', 0)} clicks, {report['top_cta'].get('click_rate_label', 'No impressions')})",
            "",
            "Notable changes:",
            *(changes or ["No meaningful previous-period changes yet."]),
            "",
            f"Open the dashboard: {admin_url}",
            "",
            "Donation clicks and PayPal opens indicate interest, not confirmed donations.",
        ]
    )


def meaningful_changes(comparison):
    labels = {
        "page_views": "Page views",
        "anonymous_sessions": "Anonymous sessions",
        "donation_cta_clicks": "Donation CTA clicks",
        "paypal_clicks": "PayPal opens",
        "health_tool_clicks": "Health-tool clicks",
        "newsletter_signups": "Newsletter signups",
    }
    changes = []
    for key, label in labels.items():
        item = comparison.get(key) or {}
        if item.get("direction") in {"up", "down"}:
            changes.append(f"- {label}: {item.get('label')}")
    return changes[:4]


def csv_safe(value):
    value = "" if value is None else str(value)
    if value.startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def domain_for(url):
    if not url:
        return ""
    parsed = urlparse(url)
    return (parsed.netloc or "").lower()


def to_utc_iso(value):
    if isinstance(value, str):
        return value
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def utc_now():
    return datetime.now(timezone.utc)


def utc_now_iso():
    return to_utc_iso(utc_now())


def label_for_timestamp(value):
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return ""
    return parsed.astimezone().strftime("%b %-d, %Y %-I:%M %p")


def clamp(value, limit):
    return value.strip()[:limit]


def truthy(value):
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}
