"""Send newly published Mindful Diabetes posts to Memovela as Resources."""

import hashlib
import hmac
import json
import time
from html import unescape
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from mindful_diabetes import cms


RESOURCE_TAG = "resource"
SOURCE_NAME = "Mindful Diabetes"


def is_post(item):
    """Support both CMS posts and the established site-content seed posts."""
    return item.get("content_type") == "post" or item.get("type") == "post"


def resource_blurb(item):
    """Prefer an authored blurb, then use the article preview as a safe fallback."""
    settings = item.get("settings_json") or {}
    return cms.clean_plain_text(
        settings.get("memovela_resource_blurb")
        or item.get("memovela_resource_blurb")
        or item.get("excerpt")
        or item.get("excerpt_html")
        or item.get("title")
        or ""
    )


def absolute_url(value, site_base_url):
    value = (value or "").strip()
    if not value:
        return ""
    if value.startswith("/"):
        return f"{site_base_url.rstrip('/')}{value}"
    return value


def resource_payload(item, site_base_url):
    """Return the versioned payload Memovela upserts into Dr. J's Global Vela."""
    is_cms_post = item.get("content_type") == "post"
    source_url = f"{site_base_url.rstrip('/')}/{item['slug']}/"
    external_id = f"mindful-diabetes:{item['id']}" if is_cms_post else f"mindful-diabetes:legacy:{item['slug']}"
    version = item.get("updated_at") if is_cms_post else item.get("modified") or item.get("date") or item["slug"]
    image_url = item.get("featured_image") if is_cms_post else item.get("hero_image") or item.get("og_image")
    return {
        "event": "mindful_diabetes.resource.upserted",
        "version": 1,
        "idempotency_key": f"{external_id}:{version}",
        "resource": {
            "external_id": external_id,
            "title": item["title"],
            "blurb": resource_blurb(item),
            "url": source_url,
            "image_url": absolute_url(image_url, site_base_url),
            "published_at": item.get("published_at") or item.get("date") or "",
            "author": item.get("author") or SOURCE_NAME,
            "tags": [RESOURCE_TAG, "mindful-diabetes"],
            "source": {"name": SOURCE_NAME, "url": site_base_url.rstrip("/")},
            "destination": {"vela": "global", "owner": "Dr. J"},
        },
    }


def sync_published_post(config, item):
    """POST a signed resource event. Publishing remains successful if Memovela is unavailable."""
    if not is_post(item):
        return {"status": "skipped", "message": "Only posts are shared with Memovela."}

    endpoint = (config.get("MEMOVELA_RESOURCE_WEBHOOK_URL") or "").strip()
    secret = (config.get("MEMOVELA_RESOURCE_WEBHOOK_SECRET") or "").strip()
    if not endpoint or not secret:
        return {"status": "not_configured", "message": "Published. Memovela sharing is not configured yet."}

    payload = resource_payload(item, config.get("SITE_BASE_URL") or "https://mindfuldiabetes.org")
    body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    timestamp = str(int(time.time()))
    signature = hmac.new(secret.encode("utf-8"), f"{timestamp}.".encode("ascii") + body, hashlib.sha256).hexdigest()
    request = Request(
        endpoint,
        data=body,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Mindful-Diabetes-Memovela-Sync/1.0",
            "X-Mindful-Timestamp": timestamp,
            "X-Mindful-Signature": f"sha256={signature}",
            "Idempotency-Key": payload["idempotency_key"],
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=float(config.get("MEMOVELA_RESOURCE_WEBHOOK_TIMEOUT_SECONDS", 8))) as response:
            if not 200 <= response.status < 300:
                return {"status": "failed", "message": "Published, but Memovela did not accept the Resource."}
            return {"status": "synced", "message": "Published and shared to Dr. J's Global Vela as a Resource."}
    except (HTTPError, URLError, OSError, ValueError):
        return {"status": "failed", "message": "Published, but the Memovela Resource sync needs to be retried."}
