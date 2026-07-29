from __future__ import annotations

import csv
import io
import json
import os
import re
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from flask import Blueprint, Response, jsonify, request


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = PROJECT_ROOT / "MDinc" / "mdinc_analytics.sqlite3"
MAX_PAYLOAD_BYTES = 32_000
MAX_BATCH_SIZE = 20
SCHEMA_VERSION = 1

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


class ValidationError(ValueError):
    pass


def create_blueprint() -> Blueprint:
    bp = Blueprint("mdinc_analytics", __name__, url_prefix="/mindful-diabetes/analytics")

    @bp.post("/events")
    def store_one_event():
        ok, error = require_token()
        if not ok:
            return error
        try:
            events = parse_payload()
            if len(events) != 1:
                raise ValidationError("Submit one event to this endpoint.")
            result = store_events(events)
            return jsonify({"ok": True, **result}), 202
        except ValidationError as exc:
            return jsonify({"ok": False, "message": str(exc)}), 400

    @bp.post("/events/batch")
    def store_event_batch():
        ok, error = require_token()
        if not ok:
            return error
        try:
            result = store_events(parse_payload())
            return jsonify({"ok": True, **result}), 202
        except ValidationError as exc:
            return jsonify({"ok": False, "message": str(exc)}), 400

    @bp.get("/summary")
    def query_summary():
        ok, error = require_token()
        if not ok:
            return error
        start, end = date_range_from_args()
        filters = filters_from_args(request.args)
        return jsonify(summary_for(start, end, filters))

    @bp.get("/events")
    def query_events():
        ok, error = require_token()
        if not ok:
            return error
        start, end = date_range_from_args()
        filters = filters_from_args(request.args)
        page = max(1, int(request.args.get("page", 1)))
        page_size = max(1, min(200, int(request.args.get("page_size", 50))))
        return jsonify(events_for(start, end, filters, page, page_size))

    @bp.get("/events/export")
    def export_events():
        ok, error = require_token()
        if not ok:
            return error
        start, end = date_range_from_args()
        filters = filters_from_args(request.args)
        body = csv_export(start, end, filters)
        filename = f"mindful-diabetes-analytics-{start.date()}-to-{(end - timedelta(days=1)).date()}.csv"
        return Response(
            body,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
            mimetype="text/csv",
        )

    @bp.post("/cleanup")
    def cleanup_events():
        ok, error = require_token()
        if not ok:
            return error
        payload = request.get_json(silent=True) or {}
        before = parse_timestamp(payload.get("before_date")) or (utc_now() - timedelta(days=int(payload.get("retention_days") or 180)))
        removed = cleanup_before(before)
        return jsonify({"ok": True, "removed": removed})

    @bp.get("/health")
    def health():
        ok, error = require_token()
        if not ok:
            return error
        return jsonify({"ok": True, **storage_health()})

    return bp


def configured_token() -> str:
    return (
        os.environ.get("MDINC_ANALYTICS_API_TOKEN", "").strip()
        or os.environ.get("RANDY_API_TOKEN", "").strip()
    )


def db_path() -> Path:
    return Path(os.environ.get("MDINC_ANALYTICS_DB_PATH", str(DEFAULT_DB_PATH))).expanduser()


def require_token():
    token = configured_token()
    if not token:
        return False, (jsonify({"ok": False, "message": "MDinc analytics token is not configured."}), 500)
    if request.headers.get("Authorization", "") != f"Bearer {token}":
        return False, (jsonify({"ok": False, "message": "Unauthorized."}), 401)
    return True, None


def connect() -> sqlite3.Connection:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=3000")
    ensure_schema(conn)
    return conn


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
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
        conn.execute(f"CREATE INDEX IF NOT EXISTS idx_mdinc_analytics_{column} ON analytics_events ({column})")


def parse_payload() -> list[dict[str, Any]]:
    if request.content_length and request.content_length > MAX_PAYLOAD_BYTES:
        raise ValidationError("Analytics payload is too large.")
    if not request.is_json:
        raise ValidationError("Analytics endpoint accepts JSON only.")
    payload = request.get_json(silent=True)
    if payload is None:
        raise ValidationError("Analytics payload was not valid JSON.")
    raw_events = payload if isinstance(payload, list) else [payload]
    if len(raw_events) > MAX_BATCH_SIZE:
        raise ValidationError("Analytics event batch is too large.")
    return [normalize_event(event) for event in raw_events]


def normalize_event(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValidationError("Each analytics event must be an object.")
    event_name = clean_string(payload.get("event_name"), "event_name", required=True)
    if event_name not in VALID_EVENT_NAMES:
        raise ValidationError("Unknown analytics event name.")
    metadata = payload.get("metadata") or {}
    if not isinstance(metadata, dict):
        raise ValidationError("Analytics metadata must be an object.")
    event = {
        "event_id": clean_event_id(payload.get("event_id")),
        "schema_version": SCHEMA_VERSION,
        "event_name": event_name,
        "event_category": EVENT_CATEGORIES[event_name],
        "occurred_at": utc_iso(),
        "metadata": clean_metadata(metadata),
    }
    for field in EVENT_COLUMNS:
        if field in {"event_id", "schema_version", "event_name", "event_category", "occurred_at", "metadata_json"}:
            continue
        event[field] = clean_string(payload.get(field), field)
    if event["device_category"] and event["device_category"] not in {"desktop", "tablet", "mobile"}:
        raise ValidationError("Device category is not valid.")
    if not is_public_analytics_path(event["page_path"]):
        raise ValidationError("Analytics event path is not public.")
    return event


def clean_event_id(value: Any) -> str:
    if value is None or value == "":
        return str(uuid.uuid4())
    cleaned = clean_string(value, "event_id", required=True)
    if not re.fullmatch(r"[A-Za-z0-9_.:-]{8,96}", cleaned):
        raise ValidationError("Analytics event ID is not valid.")
    return cleaned


def clean_string(value: Any, field: str, required: bool = False) -> str:
    if value is None:
        if required:
            raise ValidationError(f"{field} is required.")
        return ""
    if not isinstance(value, str):
        raise ValidationError(f"{field} must be text.")
    value = value.strip()
    if required and not value:
        raise ValidationError(f"{field} is required.")
    if len(value) > STRING_LIMITS.get(field, 160):
        raise ValidationError(f"{field} is too long.")
    return value


def clean_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    clean = {}
    for key, value in metadata.items():
        if key not in ALLOWED_METADATA_KEYS:
            raise ValidationError("Analytics metadata contains an unknown field.")
        if isinstance(value, bool):
            clean[key] = value
        elif value is None:
            clean[key] = ""
        elif isinstance(value, (int, float)):
            clean[key] = value
        elif isinstance(value, str):
            clean[key] = value.strip()[:160]
        else:
            raise ValidationError("Analytics metadata values must be simple.")
    return clean


def store_events(events: list[dict[str, Any]]) -> dict[str, int]:
    inserted = 0
    duplicates = 0
    with connect() as conn:
        for event in events:
            row = {column: event.get(column, "") for column in EVENT_COLUMNS}
            row["metadata_json"] = json.dumps(event.get("metadata") or {}, sort_keys=True)
            row["created_at"] = event["occurred_at"]
            try:
                conn.execute(
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
                inserted += 1
            except sqlite3.IntegrityError:
                duplicates += 1
    return {"inserted": inserted, "duplicates": duplicates}


def date_range_from_args() -> tuple[datetime, datetime]:
    end = parse_timestamp(request.args.get("end")) or utc_now()
    start = parse_timestamp(request.args.get("start")) or (end - timedelta(days=30))
    if len((request.args.get("end") or "")) == 10:
        end = end + timedelta(days=1)
    return start, end


def filters_from_args(args) -> dict[str, str]:
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


def where_clause(start: datetime, end: datetime, filters: dict[str, str]) -> tuple[str, list[Any]]:
    clauses = ["occurred_at >= ?", "occurred_at < ?", "COALESCE(page_path, '') NOT LIKE '/admin%'", "COALESCE(page_path, '') NOT LIKE '/analytics%'", "COALESCE(page_path, '') NOT LIKE '/static%'"]
    params = [to_iso(start), to_iso(end)]
    for key in sorted(filters):
        clauses.append(f"{key} = ?")
        params.append(filters[key])
    return "WHERE " + " AND ".join(clauses), params


def summary_for(start: datetime, end: datetime, filters: dict[str, str]) -> dict[str, Any]:
    previous_start = start - (end - start)
    previous_end = start
    current = period_summary(start, end, filters)
    previous = period_summary(previous_start, previous_end, filters)
    current["previous"] = previous["totals"]
    current["comparison"] = {
        key: compare_counts(current["totals"].get(key, 0), previous["totals"].get(key, 0))
        for key in current["totals"]
    }
    return current


def period_summary(start: datetime, end: datetime, filters: dict[str, str]) -> dict[str, Any]:
    totals = {
        "page_views": count_events(start, end, filters, event_name="page_view"),
        "anonymous_sessions": distinct_sessions(start, end, filters),
        "donation_cta_clicks": count_events(start, end, filters, event_name="donation_cta_click"),
        "paypal_clicks": count_events(start, end, filters, event_name="paypal_click"),
        "checkout_starts": count_events(start, end, filters, event_name="donation_checkout_started"),
        "confirmed_donations": count_events(start, end, filters, event_name="donation_completed"),
        "health_tool_clicks": count_events(start, end, filters, event_name="health_tool_click"),
        "newsletter_signups": count_events(start, end, filters, event_name="newsletter_signup"),
        "newsletter_views": count_events(start, end, filters, event_name="newsletter_form_view"),
        "newsletter_interactions": count_events(start, end, filters, event_name="newsletter_form_interaction"),
        "cta_impressions": count_events(start, end, filters, event_name="cta_impression"),
    }
    return {
        "totals": totals,
        "top_pages": group_counts(start, end, filters, "page_path", event_name="page_view"),
        "top_content": content_table(start, end, filters),
        "article_groups": group_counts(start, end, filters, "article_group"),
        "donation_sources": group_counts(start, end, filters, "page_path", event_names=["donation_cta_click", "paypal_click"]),
        "donation_positions": group_counts(start, end, filters, "element_position", event_names=["donation_cta_click", "paypal_click"]),
        "donation_campaigns": group_counts(start, end, filters, "campaign", event_names=["donation_cta_click", "paypal_click"]),
        "health_tools": group_counts(start, end, filters, "element_label", event_name="health_tool_click"),
        "health_tool_pages": group_counts(start, end, filters, "page_path", event_name="health_tool_click"),
        "newsletter_pages": group_counts(start, end, filters, "page_path", event_name="newsletter_signup"),
        "newsletter_referrers": group_counts(start, end, filters, "referrer_domain", event_name="newsletter_signup"),
        "newsletter_sources": group_counts(start, end, filters, "source", event_name="newsletter_signup"),
        "device_categories": group_counts(start, end, filters, "device_category"),
        "traffic_sources": traffic_sources(start, end, filters),
        "cta_performance": cta_performance(start, end, filters),
        "daily_trend": daily_trend(start, end, filters),
    }


def count_events(start, end, filters, event_name=None) -> int:
    filters = dict(filters)
    if event_name:
        filters["event_name"] = event_name
    where, params = where_clause(start, end, filters)
    with connect() as conn:
        return int(conn.execute(f"SELECT COUNT(*) FROM analytics_events {where}", params).fetchone()[0])


def distinct_sessions(start, end, filters) -> int:
    where, params = where_clause(start, end, filters)
    with connect() as conn:
        return int(conn.execute(f"SELECT COUNT(DISTINCT anonymous_session_id) FROM analytics_events {where} AND anonymous_session_id != ''", params).fetchone()[0])


def group_counts(start, end, filters, column, event_name=None, event_names=None, limit=10) -> list[dict[str, Any]]:
    filters = dict(filters)
    if event_name:
        filters["event_name"] = event_name
    where, params = where_clause(start, end, filters)
    if event_names:
        where += f" AND event_name IN ({','.join('?' for _ in event_names)})"
        params.extend(event_names)
    with connect() as conn:
        rows = conn.execute(
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
    return [dict(row) for row in rows]


def content_table(start, end, filters) -> list[dict[str, Any]]:
    where, params = where_clause(start, end, filters)
    with connect() as conn:
        rows = conn.execute(
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


def daily_trend(start, end, filters) -> list[dict[str, Any]]:
    where, params = where_clause(start, end, filters)
    with connect() as conn:
        rows = conn.execute(
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


def traffic_sources(start, end, filters) -> list[dict[str, Any]]:
    filters = dict(filters)
    filters["event_name"] = "page_view"
    where, params = where_clause(start, end, filters)
    with connect() as conn:
        rows = conn.execute(
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


def cta_performance(start, end, filters) -> list[dict[str, Any]]:
    where, params = where_clause(start, end, filters)
    click_events = sorted(CTA_CLICK_EVENTS)
    all_events = ["cta_impression", *click_events]
    with connect() as conn:
        rows = conn.execute(
            f"""
            SELECT COALESCE(NULLIF(element_id, ''), NULLIF(element_label, ''), page_path) AS element_key,
                   MAX(element_label) AS label,
                   page_path AS page,
                   element_position AS position,
                   COUNT(CASE WHEN event_name = 'cta_impression' THEN 1 END) AS impressions,
                   COUNT(CASE WHEN event_name IN ({','.join('?' for _ in click_events)}) THEN 1 END) AS clicks,
                   COUNT(DISTINCT CASE WHEN event_name IN ({','.join('?' for _ in click_events)}) THEN anonymous_session_id END) AS sessions
            FROM analytics_events
            {where} AND event_name IN ({','.join('?' for _ in all_events)})
            GROUP BY element_key, page_path, element_position
            HAVING impressions > 0 OR clicks > 0
            ORDER BY clicks DESC, impressions DESC, label ASC
            LIMIT 25
            """,
            [*click_events, *click_events, *params, *all_events],
        ).fetchall()
    rows = [dict(row) for row in rows]
    for row in rows:
        row["click_rate"] = numeric_rate(row.get("clicks", 0), row.get("impressions", 0))
        row["click_rate_label"] = percent_label(row["click_rate"])
    return rows


def events_for(start, end, filters, page, page_size) -> dict[str, Any]:
    where, params = where_clause(start, end, filters)
    offset = (page - 1) * page_size
    with connect() as conn:
        total = int(conn.execute(f"SELECT COUNT(*) FROM analytics_events {where}", params).fetchone()[0])
        rows = conn.execute(
            f"SELECT * FROM analytics_events {where} ORDER BY occurred_at DESC, id DESC LIMIT ? OFFSET ?",
            [*params, page_size, offset],
        ).fetchall()
    return {
        "events": [event_from_row(row) for row in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": max(1, (total + page_size - 1) // page_size),
    }


def csv_export(start, end, filters) -> str:
    result = events_for(start, end, filters, 1, 5000)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Exported at", utc_iso()])
    writer.writerow([])
    writer.writerow(["Time", "Event", "Category", "Source page", "Page title", "Element label", "Position", "Destination", "Campaign", "Source", "Device"])
    for event in result["events"]:
        writer.writerow([
            csv_safe(event.get("occurred_at")),
            csv_safe(event.get("event_name")),
            csv_safe(event.get("event_category")),
            csv_safe(event.get("page_path")),
            csv_safe(event.get("page_title")),
            csv_safe(event.get("element_label")),
            csv_safe(event.get("element_position")),
            csv_safe(event.get("destination_url")),
            csv_safe(event.get("campaign")),
            csv_safe(event.get("source")),
            csv_safe(event.get("device_category")),
        ])
    return output.getvalue()


def cleanup_before(before: datetime) -> int:
    with connect() as conn:
        cursor = conn.execute("DELETE FROM analytics_events WHERE occurred_at < ?", (to_iso(before),))
        return int(cursor.rowcount)


def storage_health() -> dict[str, Any]:
    path = db_path()
    with connect() as conn:
        row = conn.execute("SELECT COUNT(*) AS event_count, MAX(occurred_at) AS last_recorded_at FROM analytics_events").fetchone()
    return {
        "backend": "randy-sqlite",
        "path": str(path),
        "event_count": int(row["event_count"]),
        "last_recorded_at": row["last_recorded_at"] or "",
    }


def event_from_row(row: sqlite3.Row) -> dict[str, Any]:
    event = {key: row[key] for key in row.keys() if key not in {"id", "metadata_json", "created_at"}}
    try:
        event["metadata"] = json.loads(row["metadata_json"] or "{}")
    except json.JSONDecodeError:
        event["metadata"] = {}
    event["occurred_at_label"] = label_for_timestamp(event.get("occurred_at"))
    return event


def compare_counts(current: int, previous: int) -> dict[str, Any]:
    if previous == 0 and current == 0:
        return {"label": "No previous activity", "direction": "flat", "percent": None}
    if previous == 0:
        return {"label": "New activity this period", "direction": "up", "percent": None}
    change = ((current - previous) / previous) * 100
    direction = "up" if change > 0 else "down" if change < 0 else "flat"
    return {"label": f"{change:+.0f}% vs previous period", "direction": direction, "percent": change}


def parse_timestamp(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if not value:
        return None
    text = str(value).strip()
    try:
        if len(text) == 10:
            return datetime.strptime(text, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def to_iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_iso() -> str:
    return to_iso(utc_now())


def label_for_timestamp(value: Any) -> str:
    parsed = parse_timestamp(value)
    if not parsed:
        return ""
    return parsed.astimezone().strftime("%b %-d, %Y %-I:%M %p")


def numeric_rate(numerator: Any, denominator: Any) -> float | None:
    denominator = int(denominator or 0)
    if denominator <= 0:
        return None
    return (int(numerator or 0) / denominator) * 100


def percent_label(value: float | None) -> str:
    if value is None:
        return "No impressions"
    return f"{value:.1f}%"


def is_public_analytics_path(path: str) -> bool:
    path = path or "/"
    return not any(path.startswith(prefix) for prefix in EXCLUDED_PUBLIC_PATH_PREFIXES)


def csv_safe(value: Any) -> str:
    text = "" if value is None else str(value)
    if text.startswith(("=", "+", "-", "@")):
        return "'" + text
    return text
