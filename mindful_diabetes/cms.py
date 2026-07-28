import copy
import html
import json
import mimetypes
import re
import secrets
import shutil
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import bleach
from markupsafe import Markup

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:  # pragma: no cover - optional production storage
    psycopg = None
    dict_row = None


ALLOWED_CONTENT_TYPES = {"page", "post"}
ALLOWED_STATUSES = {"draft", "published", "scheduled", "archived"}
ALLOWED_TEXT_COLORS = {"navy", "green", "orange", "body"}
ALLOWED_ALIGNMENTS = {"left", "center", "right"}
ALLOWED_HEADING_LEVELS = {1, 2, 3, 4}
ALLOWED_BUTTON_STYLES = {"green", "orange"}
ALLOWED_COLUMN_RATIOS = {"50-50", "60-40", "40-60"}
ALLOWED_CALLOUT_TONES = {"green", "orange", "neutral", "warning"}
ALLOWED_SPACER_SIZES = {"small", "medium", "large"}
ALLOWED_IMAGE_WIDTHS = {"narrow", "standard", "wide", "full"}
ALLOWED_BLOCK_TYPES = {
    "heading",
    "rich_text",
    "image",
    "button",
    "two_columns",
    "three_columns",
    "video",
    "callout",
    "divider",
    "spacer",
    "quote",
    "donation_cta",
    "newsletter_signup",
    "reusable_section",
}
ALLOWED_RICH_TAGS = [
    "p",
    "br",
    "strong",
    "b",
    "em",
    "i",
    "a",
    "ul",
    "ol",
    "li",
    "blockquote",
]
ALLOWED_RICH_ATTRIBUTES = {"a": ["href", "title", "target", "rel"]}
ALLOWED_IMAGE_SIGNATURES = {
    ".jpg": [b"\xff\xd8\xff"],
    ".jpeg": [b"\xff\xd8\xff"],
    ".png": [b"\x89PNG\r\n\x1a\n"],
    ".gif": [b"GIF87a", b"GIF89a"],
    ".webp": [b"RIFF"],
}
MAX_IMAGE_BYTES = 5 * 1024 * 1024


class CmsValidationError(ValueError):
    pass


def utc_now():
    return datetime.now(timezone.utc)


def iso_now():
    return utc_now().isoformat()


def parse_timestamp(value):
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def format_admin_datetime(value):
    parsed = parse_timestamp(value)
    if not parsed:
        return ""
    return parsed.astimezone().strftime("%b %-d, %Y %-I:%M %p")


def normalize_database_url(database_url):
    database_url = (database_url or "").strip()
    if database_url.startswith("postgres://"):
        return f"postgresql://{database_url[len('postgres://'):]}"
    return database_url


def database_configured(config):
    return bool(normalize_database_url(config.get("DATABASE_URL")) and psycopg)


def connect_database(config):
    connection = psycopg.connect(normalize_database_url(config.get("DATABASE_URL")), row_factory=dict_row)
    connection.autocommit = True
    return connection


def ensure_cms_storage(config):
    if database_configured(config):
        try:
            with connect_database(config) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        CREATE TABLE IF NOT EXISTS cms_content (
                            id TEXT PRIMARY KEY,
                            content_type TEXT NOT NULL,
                            title TEXT NOT NULL,
                            slug TEXT NOT NULL UNIQUE,
                            status TEXT NOT NULL,
                            excerpt TEXT NOT NULL DEFAULT '',
                            featured_image TEXT NOT NULL DEFAULT '',
                            blocks_json JSONB NOT NULL DEFAULT '[]'::jsonb,
                            settings_json JSONB NOT NULL DEFAULT '{}'::jsonb,
                            seo_json JSONB NOT NULL DEFAULT '{}'::jsonb,
                            author TEXT NOT NULL DEFAULT '',
                            created_at TIMESTAMPTZ NOT NULL,
                            updated_at TIMESTAMPTZ NOT NULL,
                            published_at TIMESTAMPTZ,
                            scheduled_at TIMESTAMPTZ,
                            archived_at TIMESTAMPTZ
                        )
                        """
                    )
                    cursor.execute(
                        """
                        CREATE TABLE IF NOT EXISTS cms_content_revisions (
                            id BIGSERIAL PRIMARY KEY,
                            content_id TEXT NOT NULL REFERENCES cms_content(id) ON DELETE CASCADE,
                            revision_number INTEGER NOT NULL,
                            title TEXT NOT NULL,
                            slug TEXT NOT NULL,
                            status TEXT NOT NULL,
                            excerpt TEXT NOT NULL DEFAULT '',
                            featured_image TEXT NOT NULL DEFAULT '',
                            blocks_json JSONB NOT NULL,
                            settings_json JSONB NOT NULL,
                            seo_json JSONB NOT NULL,
                            created_at TIMESTAMPTZ NOT NULL,
                            created_by TEXT NOT NULL DEFAULT ''
                        )
                        """
                    )
                    cursor.execute(
                        """
                        CREATE TABLE IF NOT EXISTS cms_reusable_sections (
                            id TEXT PRIMARY KEY,
                            name TEXT NOT NULL,
                            blocks_json JSONB NOT NULL,
                            created_at TIMESTAMPTZ NOT NULL,
                            updated_at TIMESTAMPTZ NOT NULL
                        )
                        """
                    )
                    cursor.execute("CREATE INDEX IF NOT EXISTS cms_content_updated_at_idx ON cms_content (updated_at DESC)")
            config["CMS_STORAGE_BACKEND"] = "Postgres"
            return
        except Exception:
            config["CMS_STORAGE_BACKEND"] = "local file"
            return

    config["CMS_STORAGE_BACKEND"] = "local file"


def cms_data_path(config):
    return Path(config.get("CMS_DATA_PATH") or Path(config.get("ADMIN_DATA_PATH", "")).parent / "cms_content.json")


def read_local_data(config):
    path = cms_data_path(config)
    if not path.exists():
        return {"content": [], "revisions": [], "reusable_sections": [], "assets": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"content": [], "revisions": [], "reusable_sections": [], "assets": []}
    data.setdefault("content", [])
    data.setdefault("revisions", [])
    data.setdefault("reusable_sections", [])
    data.setdefault("assets", [])
    return data


def write_local_data(config, data):
    path = cms_data_path(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def make_content_id():
    return f"cnt_{secrets.token_urlsafe(9).replace('-', '').replace('_', '')[:12]}"


def make_block_id():
    return f"blk_{secrets.token_urlsafe(8).replace('-', '').replace('_', '')[:10]}"


def slugify(value):
    slug = re.sub(r"[^a-z0-9]+", "-", (value or "").strip().lower())
    return re.sub(r"-+", "-", slug).strip("-") or "untitled"


def make_unique_slug(config, title, content_id=None, preferred_slug=""):
    base_slug = slugify(preferred_slug or title)
    candidate = base_slug
    index = 2
    existing = {item["slug"]: item["id"] for item in list_content(config)}
    while candidate in existing and existing[candidate] != content_id:
        candidate = f"{base_slug}-{index}"
        index += 1
    return candidate


def list_content(config):
    ensure_cms_storage(config)
    if database_configured(config) and config.get("CMS_STORAGE_BACKEND") == "Postgres":
        try:
            with connect_database(config) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT id, content_type, title, slug, status, excerpt, featured_image,
                               blocks_json, settings_json, seo_json, author, created_at, updated_at,
                               published_at, scheduled_at, archived_at
                        FROM cms_content
                        ORDER BY updated_at DESC
                        """
                    )
                    return [normalize_content_record(row) for row in cursor.fetchall()]
        except Exception:
            pass
    return [normalize_content_record(item) for item in read_local_data(config)["content"]]


def get_content(config, content_id):
    for item in list_content(config):
        if item["id"] == content_id:
            return item
    return None


def get_published_content_by_slug(config, slug):
    slug = slugify(slug)
    now = utc_now()
    for item in list_content(config):
        if item["slug"] != slug or item["status"] != "published":
            continue
        published_at = parse_timestamp(item.get("published_at"))
        if published_at and published_at > now:
            continue
        return item
    return None


def create_content(config, content_type, author=""):
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise CmsValidationError("Choose page or post.")
    title = "Untitled Page" if content_type == "page" else "Untitled Post"
    content_id = make_content_id()
    now = iso_now()
    item = {
        "id": content_id,
        "content_type": content_type,
        "title": title,
        "slug": make_unique_slug(config, title, content_id=content_id),
        "status": "draft",
        "excerpt": "",
        "featured_image": "",
        "blocks_json": [default_block("heading", text=title)],
        "settings_json": default_settings(content_type),
        "seo_json": {},
        "author": author or "",
        "created_at": now,
        "updated_at": now,
        "published_at": None,
        "scheduled_at": None,
        "archived_at": None,
    }
    save_content(config, item, actor=author, make_revision=False)
    return item


def save_content(config, item, actor="", make_revision=True):
    existing = get_content(config, item["id"])
    cleaned = validate_content_payload(config, item, existing=existing)
    if make_revision and existing and existing["status"] == "published":
        create_revision(config, existing, actor=actor)

    ensure_cms_storage(config)
    if database_configured(config) and config.get("CMS_STORAGE_BACKEND") == "Postgres":
        try:
            with connect_database(config) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO cms_content (
                            id, content_type, title, slug, status, excerpt, featured_image,
                            blocks_json, settings_json, seo_json, author, created_at, updated_at,
                            published_at, scheduled_at, archived_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id)
                        DO UPDATE SET content_type = EXCLUDED.content_type,
                                      title = EXCLUDED.title,
                                      slug = EXCLUDED.slug,
                                      status = EXCLUDED.status,
                                      excerpt = EXCLUDED.excerpt,
                                      featured_image = EXCLUDED.featured_image,
                                      blocks_json = EXCLUDED.blocks_json,
                                      settings_json = EXCLUDED.settings_json,
                                      seo_json = EXCLUDED.seo_json,
                                      author = EXCLUDED.author,
                                      updated_at = EXCLUDED.updated_at,
                                      published_at = EXCLUDED.published_at,
                                      scheduled_at = EXCLUDED.scheduled_at,
                                      archived_at = EXCLUDED.archived_at
                        """,
                        (
                            cleaned["id"],
                            cleaned["content_type"],
                            cleaned["title"],
                            cleaned["slug"],
                            cleaned["status"],
                            cleaned["excerpt"],
                            cleaned["featured_image"],
                            json.dumps(cleaned["blocks_json"]),
                            json.dumps(cleaned["settings_json"]),
                            json.dumps(cleaned["seo_json"]),
                            cleaned["author"],
                            parse_timestamp(cleaned["created_at"]) or utc_now(),
                            parse_timestamp(cleaned["updated_at"]) or utc_now(),
                            parse_timestamp(cleaned["published_at"]),
                            parse_timestamp(cleaned["scheduled_at"]),
                            parse_timestamp(cleaned["archived_at"]),
                        ),
                    )
                    return cleaned
        except Exception:
            pass

    data = read_local_data(config)
    data["content"] = [existing_item for existing_item in data["content"] if existing_item.get("id") != cleaned["id"]]
    data["content"].append(cleaned)
    write_local_data(config, data)
    return cleaned


def archive_content(config, content_id, actor=""):
    item = get_content(config, content_id)
    if not item:
        return None
    item["status"] = "archived"
    item["archived_at"] = iso_now()
    item["updated_at"] = iso_now()
    return save_content(config, item, actor=actor)


def duplicate_content(config, content_id, actor=""):
    item = get_content(config, content_id)
    if not item:
        return None
    duplicate = copy.deepcopy(item)
    duplicate["id"] = make_content_id()
    duplicate["title"] = f"{item['title']} Copy"
    duplicate["slug"] = make_unique_slug(config, duplicate["title"], content_id=duplicate["id"])
    duplicate["status"] = "draft"
    duplicate["created_at"] = iso_now()
    duplicate["updated_at"] = iso_now()
    duplicate["published_at"] = None
    duplicate["scheduled_at"] = None
    duplicate["archived_at"] = None
    duplicate["author"] = actor or duplicate.get("author", "")
    save_content(config, duplicate, actor=actor, make_revision=False)
    return duplicate


def validate_content_payload(config, payload, existing=None):
    now = iso_now()
    content_id = payload.get("id") or (existing or {}).get("id") or make_content_id()
    content_type = payload.get("content_type") if payload.get("content_type") in ALLOWED_CONTENT_TYPES else "page"
    title = clean_plain_text(payload.get("title") or "Untitled")
    slug = make_unique_slug(config, title, content_id=content_id, preferred_slug=payload.get("slug") or title)
    status = payload.get("status") if payload.get("status") in ALLOWED_STATUSES else "draft"
    blocks = validate_blocks(payload.get("blocks_json") or payload.get("blocks") or [])
    settings = validate_settings(payload.get("settings_json") or {}, content_type)
    seo = validate_seo(payload.get("seo_json") or {})
    featured_image = clean_url(payload.get("featured_image") or "")
    if status == "published":
        validate_publish_requirements(title, slug, blocks)
    return {
        "id": content_id,
        "content_type": content_type,
        "title": title,
        "slug": slug,
        "status": status,
        "excerpt": clean_plain_text(payload.get("excerpt") or "")[:500],
        "featured_image": featured_image,
        "blocks_json": blocks,
        "settings_json": settings,
        "seo_json": seo,
        "author": clean_plain_text(payload.get("author") or (existing or {}).get("author") or "")[:120],
        "created_at": payload.get("created_at") or (existing or {}).get("created_at") or now,
        "updated_at": now,
        "published_at": payload.get("published_at") or ((existing or {}).get("published_at") if status == "published" else None) or (now if status == "published" else None),
        "scheduled_at": payload.get("scheduled_at") if status == "scheduled" else None,
        "archived_at": payload.get("archived_at") if status == "archived" else None,
    }


def validate_publish_requirements(title, slug, blocks):
    if not title or title == "Untitled":
        raise CmsValidationError("Add a title before publishing.")
    if not slug:
        raise CmsValidationError("Add a slug before publishing.")
    validate_heading_balance(blocks)
    validate_images_for_publish(blocks)


def validate_heading_balance(blocks):
    h1_count = count_headings(blocks, level=1)
    if h1_count > 1:
        raise CmsValidationError("Use only one H1 heading before publishing.")


def count_headings(blocks, level=1):
    count = 0
    for block in blocks:
        if block.get("type") == "heading" and int(block.get("settings", {}).get("level") or 2) == level:
            count += 1
        for key in ("columns", "blocks"):
            nested = block.get("content", {}).get(key)
            if isinstance(nested, list):
                for column in nested:
                    if isinstance(column, dict):
                        count += count_headings(column.get("blocks", []), level=level)
                    elif isinstance(column, list):
                        count += count_headings(column, level=level)
    return count


def validate_images_for_publish(blocks):
    for block in blocks:
        if block.get("type") == "image":
            content = block.get("content", {})
            if content.get("src") and not content.get("decorative") and not content.get("alt"):
                raise CmsValidationError("Add alt text to every image before publishing, or mark it decorative.")
        columns = block.get("content", {}).get("columns", [])
        if isinstance(columns, list):
            for column in columns:
                validate_images_for_publish(column.get("blocks", []) if isinstance(column, dict) else [])


def validate_blocks(blocks):
    if not isinstance(blocks, list):
        raise CmsValidationError("Content blocks must be a list.")
    return [validate_block(block) for block in blocks if isinstance(block, dict)]


def validate_block(block):
    block_type = block.get("type")
    if block_type not in ALLOWED_BLOCK_TYPES:
        raise CmsValidationError("Unsupported content block.")
    settings = block.get("settings") if isinstance(block.get("settings"), dict) else {}
    content = block.get("content") if isinstance(block.get("content"), dict) else {}
    clean_block = {
        "id": clean_identifier(block.get("id")) or make_block_id(),
        "type": block_type,
        "version": 1,
        "settings": {},
        "content": {},
    }
    if block_type == "heading":
        clean_block["settings"] = {
            "level": bounded_choice(to_int(settings.get("level"), 2), ALLOWED_HEADING_LEVELS, 2),
            "alignment": bounded_choice(settings.get("alignment"), ALLOWED_ALIGNMENTS, "left"),
            "accent": bool(settings.get("accent")),
            "color": bounded_choice(settings.get("color"), ALLOWED_TEXT_COLORS, "navy"),
        }
        clean_block["content"] = {"text": clean_plain_text(content.get("text") or "Heading")}
    elif block_type == "rich_text":
        clean_block["content"] = {"html": sanitize_rich_text(content.get("html") or "<p>Add your text.</p>")}
    elif block_type == "image":
        clean_block["settings"] = {
            "alignment": bounded_choice(settings.get("alignment"), ALLOWED_ALIGNMENTS, "center"),
            "width": bounded_choice(settings.get("width"), ALLOWED_IMAGE_WIDTHS, "standard"),
            "frame": bool(settings.get("frame")),
        }
        clean_block["content"] = {
            "src": clean_url(content.get("src") or ""),
            "alt": clean_plain_text(content.get("alt") or ""),
            "caption": clean_plain_text(content.get("caption") or ""),
            "decorative": bool(content.get("decorative")),
        }
    elif block_type == "button":
        clean_block["settings"] = {
            "alignment": bounded_choice(settings.get("alignment"), ALLOWED_ALIGNMENTS, "left"),
            "style": bounded_choice(settings.get("style"), ALLOWED_BUTTON_STYLES, "green"),
            "new_tab": bool(settings.get("new_tab")),
        }
        clean_block["content"] = {
            "label": clean_plain_text(content.get("label") or "Learn more")[:80],
            "url": clean_url(content.get("url") or "/"),
        }
    elif block_type in {"two_columns", "three_columns"}:
        column_count = 2 if block_type == "two_columns" else 3
        clean_block["settings"] = {
            "ratio": bounded_choice(settings.get("ratio"), ALLOWED_COLUMN_RATIOS, "50-50")
            if block_type == "two_columns"
            else "equal"
        }
        columns = content.get("columns") if isinstance(content.get("columns"), list) else []
        clean_block["content"] = {
            "columns": [
                {
                    "id": clean_identifier((columns[index] if index < len(columns) and isinstance(columns[index], dict) else {}).get("id"))
                    or f"{clean_block['id']}_col_{index + 1}",
                    "blocks": validate_blocks((columns[index] if index < len(columns) and isinstance(columns[index], dict) else {}).get("blocks", [])),
                }
                for index in range(column_count)
            ]
        }
    elif block_type == "video":
        clean_block["settings"] = {"frame": bool(settings.get("frame"))}
        clean_block["content"] = {"url": clean_video_url(content.get("url") or "")}
    elif block_type == "callout":
        clean_block["settings"] = {"tone": bounded_choice(settings.get("tone"), ALLOWED_CALLOUT_TONES, "green")}
        clean_block["content"] = {
            "title": clean_plain_text(content.get("title") or "Helpful note"),
            "text": clean_plain_text(content.get("text") or ""),
            "icon": clean_plain_text(content.get("icon") or "")[:24],
        }
    elif block_type == "divider":
        clean_block["settings"] = {"style": "line"}
    elif block_type == "spacer":
        clean_block["settings"] = {"size": bounded_choice(settings.get("size"), ALLOWED_SPACER_SIZES, "medium")}
    elif block_type == "quote":
        clean_block["content"] = {
            "quote": clean_plain_text(content.get("quote") or "Add a quote."),
            "author": clean_plain_text(content.get("author") or ""),
            "role": clean_plain_text(content.get("role") or ""),
        }
    elif block_type == "donation_cta":
        clean_block["content"] = {
            "heading": clean_plain_text(content.get("heading") or "Support prevention education"),
            "body": clean_plain_text(content.get("body") or "Your gift supports Mindful Diabetes education, tools, and community work."),
            "button": clean_plain_text(content.get("button") or "Donate"),
        }
    elif block_type == "newsletter_signup":
        clean_block["content"] = {
            "heading": clean_plain_text(content.get("heading") or "Stay up to date"),
            "description": clean_plain_text(content.get("description") or "Get new articles and updates from Mindful Diabetes."),
        }
    elif block_type == "reusable_section":
        clean_block["content"] = {"section_id": clean_identifier(content.get("section_id") or "")}
    return clean_block


def default_block(block_type, text=""):
    if block_type == "heading":
        return validate_block({"type": "heading", "content": {"text": text or "New heading"}, "settings": {"level": 1}})
    return validate_block({"type": block_type})


def validate_settings(settings, content_type):
    settings = settings if isinstance(settings, dict) else {}
    template = settings.get("template") if settings.get("template") in {"standard", "full_width", "article", "landing"} else "standard"
    clean = {
        "template": template,
        "show_in_navigation": bool(settings.get("show_in_navigation")),
        "navigation_label": clean_plain_text(settings.get("navigation_label") or "")[:80],
        "navigation_position": to_int(settings.get("navigation_position"), 0),
        "category": clean_plain_text(settings.get("category") or "")[:80],
        "tags": [clean_plain_text(tag)[:40] for tag in settings.get("tags", []) if clean_plain_text(tag)] if isinstance(settings.get("tags"), list) else [],
        "estimated_reading_time": max(0, to_int(settings.get("estimated_reading_time"), 0)),
        "sidebar": bool(settings.get("sidebar", True)),
        "related_posts": bool(settings.get("related_posts", True)),
    }
    if content_type == "page":
        clean["category"] = ""
        clean["tags"] = []
    return clean


def default_settings(content_type):
    return validate_settings({"template": "standard", "sidebar": True, "related_posts": True}, content_type)


def validate_seo(seo):
    seo = seo if isinstance(seo, dict) else {}
    return {
        "seo_title": clean_plain_text(seo.get("seo_title") or "")[:70],
        "meta_description": clean_plain_text(seo.get("meta_description") or "")[:180],
        "social_title": clean_plain_text(seo.get("social_title") or "")[:90],
        "social_description": clean_plain_text(seo.get("social_description") or "")[:220],
        "social_image": clean_url(seo.get("social_image") or ""),
        "canonical_url": clean_url(seo.get("canonical_url") or ""),
        "noindex": bool(seo.get("noindex")),
    }


def sanitize_rich_text(value):
    cleaned = bleach.clean(
        value or "",
        tags=ALLOWED_RICH_TAGS,
        attributes=ALLOWED_RICH_ATTRIBUTES,
        protocols=["http", "https", "mailto"],
        strip=True,
    )
    cleaned = bleach.linkify(cleaned, callbacks=[set_link_attributes])
    return cleaned or "<p>Add your text.</p>"


def set_link_attributes(attrs, new=False):
    href_key = (None, "href")
    href = attrs.get(href_key, "")
    if href and not is_safe_url(href):
        return None
    attrs[(None, "rel")] = "noopener noreferrer"
    if attrs.get((None, "target")) == "_blank":
        attrs[(None, "target")] = "_blank"
    return attrs


def clean_plain_text(value):
    return html.unescape(re.sub(r"\s+", " ", bleach.clean(str(value or ""), tags=[], strip=True))).strip()


def clean_identifier(value):
    value = str(value or "").strip()
    return value if re.fullmatch(r"[A-Za-z0-9_-]{1,80}", value) else ""


def clean_url(value):
    value = str(value or "").strip()
    if not value:
        return ""
    if value.startswith("/"):
        return re.sub(r"[\r\n\t]", "", value)
    return value if is_safe_url(value) else ""


def clean_video_url(value):
    value = clean_url(value)
    if not value:
        return ""
    return value if video_embed_url(value) else ""


def is_safe_url(value):
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https", "mailto"} and not re.match(r"(?i)\s*javascript:", value or "")


def bounded_choice(value, allowed, default):
    return value if value in allowed else default


def to_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def create_revision(config, item, actor=""):
    revision = {
        "content_id": item["id"],
        "revision_number": next_revision_number(config, item["id"]),
        "title": item["title"],
        "slug": item["slug"],
        "status": item["status"],
        "excerpt": item.get("excerpt", ""),
        "featured_image": item.get("featured_image", ""),
        "blocks_json": item.get("blocks_json", []),
        "settings_json": item.get("settings_json", {}),
        "seo_json": item.get("seo_json", {}),
        "created_at": iso_now(),
        "created_by": actor or "",
    }
    if database_configured(config) and config.get("CMS_STORAGE_BACKEND") == "Postgres":
        try:
            with connect_database(config) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO cms_content_revisions (
                            content_id, revision_number, title, slug, status, excerpt, featured_image,
                            blocks_json, settings_json, seo_json, created_at, created_by
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s, %s)
                        """,
                        (
                            revision["content_id"],
                            revision["revision_number"],
                            revision["title"],
                            revision["slug"],
                            revision["status"],
                            revision["excerpt"],
                            revision["featured_image"],
                            json.dumps(revision["blocks_json"]),
                            json.dumps(revision["settings_json"]),
                            json.dumps(revision["seo_json"]),
                            parse_timestamp(revision["created_at"]),
                            revision["created_by"],
                        ),
                    )
                    return revision
        except Exception:
            pass
    data = read_local_data(config)
    data["revisions"].append(revision)
    write_local_data(config, data)
    return revision


def next_revision_number(config, content_id):
    return len(list_revisions(config, content_id)) + 1


def list_revisions(config, content_id):
    if database_configured(config) and config.get("CMS_STORAGE_BACKEND") == "Postgres":
        try:
            with connect_database(config) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT id, content_id, revision_number, title, slug, status, excerpt,
                               featured_image, blocks_json, settings_json, seo_json, created_at, created_by
                        FROM cms_content_revisions
                        WHERE content_id = %s
                        ORDER BY revision_number DESC
                        """,
                        (content_id,),
                    )
                    return [normalize_revision_record(row) for row in cursor.fetchall()]
        except Exception:
            pass
    revisions = [item for item in read_local_data(config)["revisions"] if item.get("content_id") == content_id]
    return sorted([normalize_revision_record(item) for item in revisions], key=lambda item: item["revision_number"], reverse=True)


def normalize_content_record(item):
    item = dict(item)
    return {
        "id": item.get("id") or "",
        "content_type": item.get("content_type") or "page",
        "title": item.get("title") or "Untitled",
        "slug": item.get("slug") or "",
        "status": item.get("status") or "draft",
        "excerpt": item.get("excerpt") or "",
        "featured_image": item.get("featured_image") or "",
        "blocks_json": normalize_json_value(item.get("blocks_json"), []),
        "settings_json": normalize_json_value(item.get("settings_json"), {}),
        "seo_json": normalize_json_value(item.get("seo_json"), {}),
        "author": item.get("author") or "",
        "created_at": timestamp_to_iso(item.get("created_at")),
        "updated_at": timestamp_to_iso(item.get("updated_at")),
        "published_at": timestamp_to_iso(item.get("published_at")),
        "scheduled_at": timestamp_to_iso(item.get("scheduled_at")),
        "archived_at": timestamp_to_iso(item.get("archived_at")),
        "updated_at_label": format_admin_datetime(item.get("updated_at")),
        "published_at_label": format_admin_datetime(item.get("published_at")),
    }


def normalize_revision_record(item):
    item = dict(item)
    item["blocks_json"] = normalize_json_value(item.get("blocks_json"), [])
    item["settings_json"] = normalize_json_value(item.get("settings_json"), {})
    item["seo_json"] = normalize_json_value(item.get("seo_json"), {})
    item["created_at"] = timestamp_to_iso(item.get("created_at"))
    item["created_at_label"] = format_admin_datetime(item.get("created_at"))
    return item


def normalize_json_value(value, default):
    if value is None:
        return copy.deepcopy(default)
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return copy.deepcopy(default)
    return value


def timestamp_to_iso(value):
    parsed = parse_timestamp(value)
    return parsed.isoformat() if parsed else None


def block_library():
    return [
        {"type": "heading", "label": "Heading", "description": "H1-H4 section heading"},
        {"type": "rich_text", "label": "Rich Text", "description": "Paragraphs, lists, links, quotes"},
        {"type": "image", "label": "Image", "description": "Image, alt text, caption"},
        {"type": "button", "label": "Button", "description": "Green or orange link button"},
        {"type": "two_columns", "label": "Two Columns", "description": "50/50, 60/40, or 40/60"},
        {"type": "three_columns", "label": "Three Columns", "description": "Three equal columns"},
        {"type": "video", "label": "Video", "description": "YouTube or Vimeo embed"},
        {"type": "callout", "label": "Callout Card", "description": "Highlighted note or warning"},
        {"type": "divider", "label": "Divider", "description": "Simple visual separator"},
        {"type": "spacer", "label": "Spacer", "description": "Small, medium, or large gap"},
        {"type": "quote", "label": "Quote", "description": "Quote with attribution"},
        {"type": "donation_cta", "label": "Donation CTA", "description": "Donation call to action"},
        {"type": "newsletter_signup", "label": "Newsletter Signup", "description": "Existing signup form"},
    ]


def render_blocks(blocks, config, renderer):
    return Markup("".join(render_block(block, config, renderer) for block in validate_blocks(blocks)))


def render_block(block, config, renderer):
    block_type = block["type"]
    template = f"blocks/{block_type}.html"
    return renderer(template, block=block, config=config, video_embed_url=video_embed_url)


def video_embed_url(raw_url):
    parsed = urlparse((raw_url or "").strip())
    host = parsed.netloc.lower().removeprefix("www.")
    video_id = ""
    if host == "youtu.be":
        video_id = parsed.path.strip("/").split("/")[0]
        return f"https://www.youtube.com/embed/{video_id}" if safe_video_id(video_id) else ""
    if host in {"youtube.com", "m.youtube.com"}:
        if parsed.path == "/watch":
            video_id = parse_qs(parsed.query).get("v", [""])[0]
        elif parsed.path.startswith("/embed/"):
            video_id = parsed.path.split("/embed/", 1)[1].split("/")[0]
        return f"https://www.youtube.com/embed/{video_id}" if safe_video_id(video_id) else ""
    if host == "vimeo.com":
        video_id = parsed.path.strip("/").split("/")[0]
        return f"https://player.vimeo.com/video/{video_id}" if re.fullmatch(r"\d{6,15}", video_id or "") else ""
    if host == "player.vimeo.com" and parsed.path.startswith("/video/"):
        video_id = parsed.path.split("/video/", 1)[1].split("/")[0]
        return f"https://player.vimeo.com/video/{video_id}" if re.fullmatch(r"\d{6,15}", video_id or "") else ""
    return ""


def safe_video_id(value):
    return bool(re.fullmatch(r"[\w-]{6,}", value or ""))


def save_uploaded_image(config, file_storage):
    if not file_storage or not file_storage.filename:
        raise CmsValidationError("Choose an image to upload.")
    storage = upload_storage_info(config)
    if storage["backend"] != "local":
        raise CmsValidationError("Image storage is not configured.")
    original_name = Path(file_storage.filename).name
    extension = Path(original_name).suffix.lower()
    if extension not in ALLOWED_IMAGE_SIGNATURES:
        raise CmsValidationError("Upload a JPG, PNG, GIF, or WebP image.")
    file_storage.stream.seek(0, 2)
    size = file_storage.stream.tell()
    file_storage.stream.seek(0)
    if size > MAX_IMAGE_BYTES:
        raise CmsValidationError("Images must be 5 MB or smaller.")
    header = file_storage.stream.read(16)
    file_storage.stream.seek(0)
    if not any(header.startswith(signature) for signature in ALLOWED_IMAGE_SIGNATURES[extension]):
        raise CmsValidationError("The uploaded file does not look like a valid image.")
    mime_type = mimetypes.types_map.get(extension, "application/octet-stream")
    today = utc_now()
    filename = f"{today.strftime('%Y%m%d')}-{secrets.token_hex(6)}{extension}"
    relative_path = f"uploads/admin/{today.strftime('%Y/%m')}/{filename}"
    destination = Path(config.get("CMS_LOCAL_UPLOAD_ROOT") or Path.cwd() / "static") / relative_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as handle:
        shutil.copyfileobj(file_storage.stream, handle)
    asset = {
        "id": f"asset_{secrets.token_hex(8)}",
        "url": f"/static/{relative_path}",
        "filename": original_name,
        "mime_type": mime_type,
        "size": size,
        "created_at": iso_now(),
        "persistent": False,
    }
    data = read_local_data(config)
    data["assets"].append(asset)
    write_local_data(config, data)
    return asset


def upload_storage_info(config):
    return {
        "backend": "local",
        "persistent": False,
        "message": "Local uploads are for development only. Configure persistent object storage before using uploads on Heroku.",
    }
