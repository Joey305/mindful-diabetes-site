"""Send selected Mindful Diabetes articles to Memovela as Resources."""

import hashlib
import hmac
import json
import re
import time
from html import unescape
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


RESOURCE_TAG = "resource"
SOURCE_NAME = "Mindful Diabetes"


def resource_blurb(item):
    """Prefer the reviewed resource blurb, with a safe text-only fallback."""
    value = item.get("memovela_resource_blurb") or item.get("excerpt_html") or item["title"]
    value = unescape(re.sub(r"<[^>]+>", " ", value))
    return re.sub(r"\s+", " ", value).strip()[:1200]


def resource_payload(item, site_base_url):
    source_url = f"{site_base_url.rstrip('/')}/{item['slug']}/"
    external_id = f"mindful-diabetes:legacy:{item['slug']}"
    version = hashlib.sha256(
        f"{item['title']}|{resource_blurb(item)}|{source_url}|{item.get('modified') or item.get('date') or ''}".encode("utf-8")
    ).hexdigest()[:16]
    image_url = item.get("hero_image") or item.get("og_image") or ""
    if image_url.startswith("/"):
        image_url = f"{site_base_url.rstrip('/')}{image_url}"
    return {
        "event": "mindful_diabetes.resource.upserted",
        "version": 1,
        "idempotency_key": f"{external_id}:{version}",
        "resource": {
            "external_id": external_id,
            "title": item["title"],
            "blurb": resource_blurb(item),
            "url": source_url,
            "image_url": image_url,
            "published_at": item.get("date") or "",
            "author": item.get("author") or SOURCE_NAME,
            "tags": [RESOURCE_TAG, "mindful-diabetes"],
            "source": {"name": SOURCE_NAME, "url": site_base_url.rstrip("/")},
            "destination": {"vela": "global", "owner": "Dr. J"},
        },
    }


def sync_published_post(config, item):
    endpoint = (config.get("MEMOVELA_RESOURCE_WEBHOOK_URL") or "").strip()
    secret = (config.get("MEMOVELA_RESOURCE_WEBHOOK_SECRET") or "").strip()
    if not endpoint or not secret:
        return {"status": "not_configured", "message": "Memovela sharing is not configured yet."}
    payload = resource_payload(item, config.get("SITE_BASE_URL") or "https://mindfuldiabetes.org")
    body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    timestamp = str(int(time.time()))
    signature = hmac.new(secret.encode("utf-8"), f"{timestamp}.".encode("ascii") + body, hashlib.sha256).hexdigest()
    request = Request(endpoint, data=body, headers={
        "Content-Type": "application/json", "User-Agent": "Mindful-Diabetes-Memovela-Sync/1.0",
        "X-Mindful-Timestamp": timestamp, "X-Mindful-Signature": f"sha256={signature}",
        "Idempotency-Key": payload["idempotency_key"],
    }, method="POST")
    try:
        with urlopen(request, timeout=float(config.get("MEMOVELA_RESOURCE_WEBHOOK_TIMEOUT_SECONDS", 8))) as response:
            return {"status": "synced", "message": "Shared to Dr. J's Global Vela as a Resource."} if 200 <= response.status < 300 else {"status": "failed", "message": "Memovela rejected the Resource."}
    except (HTTPError, URLError, OSError, ValueError):
        return {"status": "failed", "message": "Memovela Resource sync needs to be retried."}
