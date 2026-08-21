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

from mindful_diabetes import memovela as memovela_links

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
ALLOWED_FAQ_STYLES = {"green", "orange", "neutral"}
ALLOWED_GRID_COLUMNS = {2, 3, 4}
ALLOWED_RELATED_LAYOUTS = {"cards", "compact"}
ALLOWED_FEATURED_LAYOUTS = {"image_left", "text_left", "background", "compact"}
ALLOWED_ALERT_TYPES = {"information", "success", "caution", "urgent", "medical"}
ALLOWED_PROCESS_LAYOUTS = {"vertical", "horizontal", "timeline"}
ALLOWED_HERO_HEIGHTS = {"compact", "large"}
ALLOWED_CONTAINER_WIDTHS = {"narrow", "standard", "wide", "full"}
ALLOWED_CONTAINER_BACKGROUNDS = {"white", "soft", "green", "orange"}
ALLOWED_IMAGE_RATIOS = {"natural", "square", "wide"}
ALLOWED_EMBED_PROVIDERS = {"google_maps", "spotify"}
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
    "faq",
    "card_grid",
    "statistics",
    "table_of_contents",
    "related_posts",
    "featured_content",
    "resource_download",
    "citation",
    "alert_notice",
    "icon_list",
    "process_steps",
    "definition",
    "comparison_table",
    "side_by_side",
    "myth_fact",
    "quiz",
    "sponsor_logo_grid",
    "team_profile",
    "donation_progress",
    "volunteer_cta",
    "event",
    "newsletter_archive",
    "author_bio",
    "article_metadata",
    "medical_reviewer",
    "social_sharing",
    "post_navigation",
    "footnotes",
    "hero_section",
    "section_container",
    "tabs",
    "image_gallery",
    "image_text",
    "logo_badge_row",
    "embed",
    "recipe_card",
    "nutrition_facts",
    "glucose_tip",
    "meal_swap",
    "health_tool_card",
    "research_summary",
    "study_snapshot",
    "community_story",
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
    elif block_type == "faq":
        clean_block["settings"] = {
            "style": bounded_choice(settings.get("style"), ALLOWED_FAQ_STYLES, "green"),
            "multiple_open": bool(settings.get("multiple_open")),
            "faq_schema": bool(settings.get("faq_schema", True)),
        }
        clean_block["content"] = {
            "heading": clean_plain_text(content.get("heading") or "Frequently asked questions"),
            "items": clean_pairs(content.get("items"), "Question", "Answer", rich_second=True),
        }
    elif block_type == "card_grid":
        clean_block["settings"] = {
            "columns": bounded_choice(to_int(settings.get("columns"), 3), ALLOWED_GRID_COLUMNS, 3),
            "equal_height": bool(settings.get("equal_height", True)),
            "mobile_horizontal": bool(settings.get("mobile_horizontal")),
        }
        clean_block["content"] = {"cards": clean_cards(content.get("cards"))}
    elif block_type == "statistics":
        clean_block["settings"] = {"count_up": bool(settings.get("count_up"))}
        clean_block["content"] = {"items": clean_statistics(content.get("items"))}
    elif block_type == "table_of_contents":
        clean_block["settings"] = {
            "sticky": bool(settings.get("sticky")),
            "collapse_mobile": bool(settings.get("collapse_mobile", True)),
            "highlight_current": bool(settings.get("highlight_current", True)),
        }
        clean_block["content"] = {"heading": clean_plain_text(content.get("heading") or "On this page")}
    elif block_type == "related_posts":
        clean_block["settings"] = {
            "count": min(max(to_int(settings.get("count"), 3), 1), 6),
            "layout": bounded_choice(settings.get("layout"), ALLOWED_RELATED_LAYOUTS, "cards"),
            "show_image": bool(settings.get("show_image", True)),
            "show_date": bool(settings.get("show_date", True)),
            "show_excerpt": bool(settings.get("show_excerpt", True)),
        }
        clean_block["content"] = {
            "heading": clean_plain_text(content.get("heading") or "Related reading"),
            "category": clean_plain_text(content.get("category") or "")[:80],
            "tags": clean_text_list(content.get("tags"), limit=8),
            "slugs": [slugify(item) for item in clean_text_list(content.get("slugs"), limit=8)],
        }
    elif block_type == "featured_content":
        clean_block["settings"] = {"layout": bounded_choice(settings.get("layout"), ALLOWED_FEATURED_LAYOUTS, "image_left")}
        clean_block["content"] = {
            "slug": slugify(content.get("slug") or ""),
            "eyebrow": clean_plain_text(content.get("eyebrow") or "Featured"),
            "title_override": clean_plain_text(content.get("title_override") or ""),
            "description_override": clean_plain_text(content.get("description_override") or ""),
            "image_override": clean_url(content.get("image_override") or ""),
            "button": clean_plain_text(content.get("button") or "Read more")[:80],
        }
    elif block_type == "resource_download":
        clean_block["settings"] = {"email_required": bool(settings.get("email_required"))}
        clean_block["content"] = {
            "title": clean_plain_text(content.get("title") or "Resource download"),
            "description": clean_plain_text(content.get("description") or ""),
            "file_url": clean_resource_url(content.get("file_url") or ""),
            "file_type": clean_plain_text(content.get("file_type") or "PDF")[:20],
            "file_size": clean_plain_text(content.get("file_size") or "")[:30],
            "preview_image": clean_url(content.get("preview_image") or ""),
            "button": clean_plain_text(content.get("button") or "Download")[:80],
        }
    elif block_type == "citation":
        clean_block["settings"] = {"display": bounded_choice(settings.get("display"), {"compact", "card", "reference"}, "compact")}
        clean_block["content"] = clean_citation(content)
    elif block_type == "alert_notice":
        clean_block["settings"] = {"type": bounded_choice(settings.get("type"), ALLOWED_ALERT_TYPES, "information")}
        clean_block["content"] = {
            "heading": clean_plain_text(content.get("heading") or "Note"),
            "message": sanitize_rich_text(content.get("message") or "<p>This information is educational.</p>"),
        }
    elif block_type == "icon_list":
        clean_block["content"] = {
            "heading": clean_plain_text(content.get("heading") or ""),
            "items": clean_icon_items(content.get("items")),
        }
    elif block_type == "process_steps":
        clean_block["settings"] = {"layout": bounded_choice(settings.get("layout"), ALLOWED_PROCESS_LAYOUTS, "vertical")}
        clean_block["content"] = {
            "heading": clean_plain_text(content.get("heading") or "Step by step"),
            "steps": clean_title_text_items(content.get("steps"), "Step", "Add a short description."),
        }
    elif block_type == "definition":
        clean_block["content"] = {
            "term": clean_plain_text(content.get("term") or "Term"),
            "definition": clean_plain_text(content.get("definition") or "Simple definition."),
            "explanation": sanitize_rich_text(content.get("explanation") or ""),
            "source": clean_url(content.get("source") or ""),
        }
    elif block_type == "comparison_table":
        clean_block["settings"] = {"highlight_column": max(0, to_int(settings.get("highlight_column"), 0))}
        clean_block["content"] = {
            "headers": clean_text_list(content.get("headers"), fallback=["Option A", "Option B"], limit=6),
            "rows": clean_table_rows(content.get("rows")),
        }
    elif block_type == "side_by_side":
        clean_block["content"] = {
            "left_label": clean_plain_text(content.get("left_label") or "Before"),
            "left_title": clean_plain_text(content.get("left_title") or "Problem"),
            "left_text": clean_plain_text(content.get("left_text") or ""),
            "right_label": clean_plain_text(content.get("right_label") or "After"),
            "right_title": clean_plain_text(content.get("right_title") or "Solution"),
            "right_text": clean_plain_text(content.get("right_text") or ""),
        }
    elif block_type == "myth_fact":
        clean_block["content"] = {
            "myth": clean_plain_text(content.get("myth") or "Add the myth."),
            "fact": clean_plain_text(content.get("fact") or "Add the fact."),
        }
    elif block_type == "quiz":
        answers = clean_quiz_answers(content.get("answers"))
        clean_block["content"] = {
            "question": clean_plain_text(content.get("question") or "Knowledge check"),
            "answers": answers,
            "explanation": clean_plain_text(content.get("explanation") or ""),
        }
    elif block_type == "sponsor_logo_grid":
        clean_block["settings"] = {"grayscale": bool(settings.get("grayscale"))}
        clean_block["content"] = {"sponsors": clean_sponsors(content.get("sponsors"))}
    elif block_type == "team_profile":
        clean_block["content"] = {
            "photo": clean_url(content.get("photo") or ""),
            "name": clean_plain_text(content.get("name") or "Team member"),
            "role": clean_plain_text(content.get("role") or ""),
            "credentials": clean_plain_text(content.get("credentials") or ""),
            "bio": clean_plain_text(content.get("bio") or ""),
            "profile_url": clean_url(content.get("profile_url") or ""),
        }
    elif block_type == "donation_progress":
        clean_block["content"] = {
            "campaign": clean_plain_text(content.get("campaign") or "Fundraising campaign"),
            "raised": max(0, to_int(content.get("raised"), 0)),
            "goal": max(1, to_int(content.get("goal"), 1000)),
            "donors": max(0, to_int(content.get("donors"), 0)),
            "button": clean_plain_text(content.get("button") or "Donate")[:80],
            "url": clean_url(content.get("url") or "/donation/"),
        }
    elif block_type == "volunteer_cta":
        clean_block["content"] = {
            "title": clean_plain_text(content.get("title") or "Volunteer with Mindful Diabetes"),
            "description": clean_plain_text(content.get("description") or ""),
            "time_commitment": clean_plain_text(content.get("time_commitment") or ""),
            "location": clean_plain_text(content.get("location") or "Remote"),
            "button": clean_plain_text(content.get("button") or "Volunteer")[:80],
            "url": clean_url(content.get("url") or "/volunteer/"),
        }
    elif block_type == "event":
        clean_block["content"] = {
            "title": clean_plain_text(content.get("title") or "Event"),
            "date": clean_plain_text(content.get("date") or ""),
            "time": clean_plain_text(content.get("time") or ""),
            "timezone": clean_plain_text(content.get("timezone") or ""),
            "location": clean_plain_text(content.get("location") or ""),
            "description": clean_plain_text(content.get("description") or ""),
            "registration_url": clean_url(content.get("registration_url") or ""),
            "calendar_url": clean_url(content.get("calendar_url") or ""),
        }
    elif block_type == "newsletter_archive":
        clean_block["settings"] = {"count": min(max(to_int(settings.get("count"), 3), 1), 8)}
        clean_block["content"] = {"heading": clean_plain_text(content.get("heading") or "Newsletter archive"), "items": clean_newsletter_items(content.get("items"))}
    elif block_type == "author_bio":
        clean_block["content"] = {
            "photo": clean_url(content.get("photo") or ""),
            "name": clean_plain_text(content.get("name") or ""),
            "credentials": clean_plain_text(content.get("credentials") or ""),
            "bio": clean_plain_text(content.get("bio") or ""),
            "profile_url": clean_url(content.get("profile_url") or ""),
        }
    elif block_type == "article_metadata":
        clean_block["settings"] = {
            "show_author": bool(settings.get("show_author", True)),
            "show_dates": bool(settings.get("show_dates", True)),
            "show_category": bool(settings.get("show_category", True)),
            "show_reading_time": bool(settings.get("show_reading_time", True)),
        }
        clean_block["content"] = {"reviewed_by": clean_plain_text(content.get("reviewed_by") or "")}
    elif block_type == "medical_reviewer":
        clean_block["content"] = {
            "name": clean_plain_text(content.get("name") or "Medical reviewer"),
            "credentials": clean_plain_text(content.get("credentials") or ""),
            "review_date": clean_plain_text(content.get("review_date") or ""),
            "profile_url": clean_url(content.get("profile_url") or ""),
            "statement": clean_plain_text(content.get("statement") or "Reviewed for educational clarity and accuracy."),
        }
    elif block_type == "social_sharing":
        clean_block["settings"] = {"facebook": bool(settings.get("facebook", True)), "linkedin": bool(settings.get("linkedin", True)), "x": bool(settings.get("x", True)), "email": bool(settings.get("email", True)), "copy": bool(settings.get("copy", True))}
        clean_block["content"] = {"heading": clean_plain_text(content.get("heading") or "Share this")}
    elif block_type == "post_navigation":
        clean_block["content"] = {"heading": clean_plain_text(content.get("heading") or "Keep reading")}
    elif block_type == "footnotes":
        clean_block["content"] = {"heading": clean_plain_text(content.get("heading") or "Footnotes"), "notes": clean_text_list(content.get("notes"), fallback=["Add a note."], limit=30)}
    elif block_type == "hero_section":
        clean_block["settings"] = {
            "height": bounded_choice(settings.get("height"), ALLOWED_HERO_HEIGHTS, "compact"),
            "alignment": bounded_choice(settings.get("alignment"), ALLOWED_ALIGNMENTS, "left"),
            "overlay": bool(settings.get("overlay")),
        }
        clean_block["content"] = {
            "title": clean_plain_text(content.get("title") or "Hero title"),
            "subtitle": clean_plain_text(content.get("subtitle") or ""),
            "image": clean_url(content.get("image") or ""),
            "primary_label": clean_plain_text(content.get("primary_label") or ""),
            "primary_url": clean_url(content.get("primary_url") or ""),
            "secondary_label": clean_plain_text(content.get("secondary_label") or ""),
            "secondary_url": clean_url(content.get("secondary_url") or ""),
        }
    elif block_type == "section_container":
        clean_block["settings"] = {
            "width": bounded_choice(settings.get("width"), ALLOWED_CONTAINER_WIDTHS, "standard"),
            "background": bounded_choice(settings.get("background"), ALLOWED_CONTAINER_BACKGROUNDS, "soft"),
            "spacing": bounded_choice(settings.get("spacing"), ALLOWED_SPACER_SIZES, "medium"),
            "frame": bool(settings.get("frame")),
        }
        clean_block["content"] = {"blocks": validate_blocks(content.get("blocks") or [])}
    elif block_type == "tabs":
        clean_block["content"] = {"tabs": clean_tabs(content.get("tabs"))}
    elif block_type == "image_gallery":
        clean_block["settings"] = {
            "columns": bounded_choice(to_int(settings.get("columns"), 3), ALLOWED_GRID_COLUMNS, 3),
            "ratio": bounded_choice(settings.get("ratio"), ALLOWED_IMAGE_RATIOS, "natural"),
            "frame": bool(settings.get("frame")),
        }
        clean_block["content"] = {"images": clean_gallery_images(content.get("images"))}
    elif block_type == "image_text":
        clean_block["settings"] = {
            "image_position": bounded_choice(settings.get("image_position"), {"left", "right"}, "left"),
            "vertical_alignment": bounded_choice(settings.get("vertical_alignment"), {"top", "center"}, "center"),
        }
        clean_block["content"] = {
            "image": clean_url(content.get("image") or ""),
            "alt": clean_plain_text(content.get("alt") or ""),
            "heading": clean_plain_text(content.get("heading") or "Image and text"),
            "text": clean_plain_text(content.get("text") or ""),
            "button": clean_plain_text(content.get("button") or ""),
            "url": clean_url(content.get("url") or ""),
        }
    elif block_type == "logo_badge_row":
        clean_block["content"] = {"badges": clean_badges(content.get("badges"))}
    elif block_type == "embed":
        provider = bounded_choice(settings.get("provider"), ALLOWED_EMBED_PROVIDERS, "google_maps")
        clean_block["settings"] = {"provider": provider}
        clean_block["content"] = {"url": clean_embed_url(provider, content.get("url") or "")}
    elif block_type == "recipe_card":
        clean_block["content"] = clean_recipe(content)
    elif block_type == "nutrition_facts":
        clean_block["content"] = {
            "serving_size": clean_plain_text(content.get("serving_size") or ""),
            "calories": clean_plain_text(content.get("calories") or ""),
            "carbohydrates": clean_plain_text(content.get("carbohydrates") or ""),
            "fiber": clean_plain_text(content.get("fiber") or ""),
            "protein": clean_plain_text(content.get("protein") or ""),
            "fat": clean_plain_text(content.get("fat") or ""),
            "sodium": clean_plain_text(content.get("sodium") or ""),
            "estimated": bool(content.get("estimated", True)),
        }
    elif block_type == "glucose_tip":
        clean_block["content"] = {
            "heading": clean_plain_text(content.get("heading") or "Glucose-friendly tip"),
            "explanation": clean_plain_text(content.get("explanation") or ""),
            "example": clean_plain_text(content.get("example") or ""),
            "source": clean_url(content.get("source") or ""),
        }
    elif block_type == "meal_swap":
        clean_block["content"] = {"heading": clean_plain_text(content.get("heading") or "Meal swap"), "swaps": clean_pairs(content.get("swaps"), "Instead of", "Consider")}
    elif block_type == "health_tool_card":
        clean_block["content"] = {
            "tool": bounded_choice(content.get("tool"), {"jeir", "memovela", "health_tools", "mindful_eating"}, "health_tools"),
            "title_override": clean_plain_text(content.get("title_override") or ""),
            "description": clean_plain_text(content.get("description") or ""),
            "button": clean_plain_text(content.get("button") or "Open tool")[:80],
            "image": clean_url(content.get("image") or ""),
        }
    elif block_type == "research_summary":
        clean_block["content"] = {
            "question": clean_plain_text(content.get("question") or "Research question"),
            "methods": clean_plain_text(content.get("methods") or ""),
            "finding": clean_plain_text(content.get("finding") or ""),
            "why_it_matters": clean_plain_text(content.get("why_it_matters") or ""),
            "limitations": clean_plain_text(content.get("limitations") or ""),
            "source": clean_url(content.get("source") or ""),
        }
    elif block_type == "study_snapshot":
        clean_block["content"] = {
            "study_type": clean_plain_text(content.get("study_type") or ""),
            "participants": clean_plain_text(content.get("participants") or ""),
            "duration": clean_plain_text(content.get("duration") or ""),
            "population": clean_plain_text(content.get("population") or ""),
            "outcome": clean_plain_text(content.get("outcome") or ""),
            "publication": clean_plain_text(content.get("publication") or ""),
        }
    elif block_type == "community_story":
        clean_block["settings"] = {"permission_confirmed": bool(settings.get("permission_confirmed"))}
        clean_block["content"] = {
            "name": clean_plain_text(content.get("name") or "Anonymous community member"),
            "anonymous": bool(content.get("anonymous", True)),
            "photo": clean_url(content.get("photo") or ""),
            "story": clean_plain_text(content.get("story") or ""),
            "pull_quote": clean_plain_text(content.get("pull_quote") or ""),
            "consent_reference": clean_plain_text(content.get("consent_reference") or ""),
        }
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


def clean_text_list(value, fallback=None, limit=12):
    items = value if isinstance(value, list) else []
    cleaned = [clean_plain_text(item) for item in items if clean_plain_text(item)]
    if not cleaned and fallback:
        cleaned = fallback
    return cleaned[:limit]


def clean_pairs(value, first_default, second_default, rich_second=False):
    items = value if isinstance(value, list) else []
    cleaned = []
    for item in items[:20]:
        if not isinstance(item, dict):
            continue
        first = clean_plain_text(item.get("question") or item.get("left") or item.get("first") or item.get("instead") or first_default)
        second_raw = item.get("answer") or item.get("right") or item.get("second") or item.get("consider") or second_default
        second = sanitize_rich_text(second_raw) if rich_second else clean_plain_text(second_raw)
        cleaned.append({"first": first, "second": second})
    return cleaned or [{"first": first_default, "second": sanitize_rich_text(second_default) if rich_second else second_default}]


def clean_cards(value):
    items = value if isinstance(value, list) else []
    cards = []
    for item in items[:12]:
        if not isinstance(item, dict):
            continue
        cards.append(
            {
                "image": clean_url(item.get("image") or ""),
                "icon": clean_plain_text(item.get("icon") or "")[:24],
                "category": clean_plain_text(item.get("category") or "")[:60],
                "heading": clean_plain_text(item.get("heading") or "Card"),
                "description": clean_plain_text(item.get("description") or ""),
                "button": clean_plain_text(item.get("button") or "Learn more")[:80],
                "url": clean_url(item.get("url") or ""),
            }
        )
    return cards or [{"image": "", "icon": "", "category": "", "heading": "Helpful resource", "description": "Add a short description.", "button": "Learn more", "url": ""}]


def clean_statistics(value):
    items = value if isinstance(value, list) else []
    stats = []
    for item in items[:8]:
        if not isinstance(item, dict):
            continue
        stats.append(
            {
                "prefix": clean_plain_text(item.get("prefix") or "")[:8],
                "number": clean_plain_text(item.get("number") or "0")[:24],
                "suffix": clean_plain_text(item.get("suffix") or "")[:12],
                "label": clean_plain_text(item.get("label") or "Impact number"),
                "icon": clean_plain_text(item.get("icon") or "")[:24],
            }
        )
    return stats or [{"prefix": "", "number": "12,500", "suffix": "+", "label": "People reached through diabetes education", "icon": ""}]


def clean_citation(content):
    return {
        "authors": clean_plain_text(content.get("authors") or ""),
        "title": clean_plain_text(content.get("title") or "Article title"),
        "journal": clean_plain_text(content.get("journal") or ""),
        "year": clean_plain_text(content.get("year") or ""),
        "doi": clean_plain_text(content.get("doi") or ""),
        "pubmed_url": clean_url(content.get("pubmed_url") or ""),
        "number": clean_plain_text(content.get("number") or ""),
    }


def clean_icon_items(value):
    items = value if isinstance(value, list) else []
    cleaned = []
    for item in items[:12]:
        if not isinstance(item, dict):
            continue
        cleaned.append(
            {
                "icon": clean_plain_text(item.get("icon") or "")[:24],
                "title": clean_plain_text(item.get("title") or "Item"),
                "description": clean_plain_text(item.get("description") or ""),
                "url": clean_url(item.get("url") or ""),
            }
        )
    return cleaned or [{"icon": "", "title": "Practical support", "description": "Add a short description.", "url": ""}]


def clean_title_text_items(value, title_default, text_default):
    items = value if isinstance(value, list) else []
    cleaned = []
    for item in items[:16]:
        if not isinstance(item, dict):
            continue
        cleaned.append({"title": clean_plain_text(item.get("title") or title_default), "text": clean_plain_text(item.get("text") or text_default)})
    return cleaned or [{"title": title_default, "text": text_default}]


def clean_table_rows(value):
    rows = value if isinstance(value, list) else []
    cleaned = []
    for row in rows[:16]:
        cells = row.get("cells") if isinstance(row, dict) else row
        if not isinstance(cells, list):
            continue
        cleaned.append({"cells": [clean_plain_text(cell) for cell in cells[:6]]})
    return cleaned or [{"cells": ["Add comparison text", "Add comparison text"]}]


def clean_quiz_answers(value):
    answers = value if isinstance(value, list) else []
    cleaned = []
    has_correct = False
    for item in answers[:6]:
        if not isinstance(item, dict):
            continue
        correct = bool(item.get("correct"))
        has_correct = has_correct or correct
        cleaned.append({"text": clean_plain_text(item.get("text") or "Answer"), "correct": correct})
    if not cleaned:
        cleaned = [{"text": "Answer A", "correct": True}, {"text": "Answer B", "correct": False}]
        has_correct = True
    if cleaned and not has_correct:
        cleaned[0]["correct"] = True
    return cleaned


def clean_sponsors(value):
    items = value if isinstance(value, list) else []
    sponsors = []
    for item in items[:16]:
        if not isinstance(item, dict):
            continue
        sponsors.append(
            {
                "logo": clean_url(item.get("logo") or ""),
                "name": clean_plain_text(item.get("name") or "Sponsor"),
                "url": clean_url(item.get("url") or ""),
                "level": clean_plain_text(item.get("level") or ""),
            }
        )
    return sponsors or [{"logo": "", "name": "Sponsor name", "url": "", "level": ""}]


def clean_newsletter_items(value):
    items = value if isinstance(value, list) else []
    newsletters = []
    for item in items[:12]:
        if not isinstance(item, dict):
            continue
        newsletters.append(
            {
                "title": clean_plain_text(item.get("title") or "Newsletter"),
                "date": clean_plain_text(item.get("date") or ""),
                "description": clean_plain_text(item.get("description") or ""),
                "url": clean_url(item.get("url") or ""),
            }
        )
    return newsletters or [{"title": "Newsletter issue", "date": "", "description": "Add a short description.", "url": ""}]


def clean_tabs(value):
    items = value if isinstance(value, list) else []
    tabs = []
    for item in items[:8]:
        if not isinstance(item, dict):
            continue
        tabs.append({"title": clean_plain_text(item.get("title") or "Tab"), "body": sanitize_rich_text(item.get("body") or "<p>Add tab content.</p>")})
    return tabs or [{"title": "Overview", "body": "<p>Add tab content.</p>"}]


def clean_gallery_images(value):
    images = value if isinstance(value, list) else []
    cleaned = []
    for item in images[:20]:
        if not isinstance(item, dict):
            continue
        cleaned.append({"src": clean_url(item.get("src") or ""), "alt": clean_plain_text(item.get("alt") or ""), "caption": clean_plain_text(item.get("caption") or "")})
    return cleaned or [{"src": "", "alt": "", "caption": ""}]


def clean_badges(value):
    items = value if isinstance(value, list) else []
    badges = []
    for item in items[:16]:
        if not isinstance(item, dict):
            continue
        badges.append({"image": clean_url(item.get("image") or ""), "label": clean_plain_text(item.get("label") or "Badge"), "url": clean_url(item.get("url") or "")})
    return badges or [{"image": "", "label": "Badge", "url": ""}]


def clean_resource_url(value):
    url = clean_url(value)
    if not url:
        return ""
    path = urlparse(url).path.lower()
    return url if re.search(r"\.(pdf|doc|docx|xls|xlsx|csv|zip)$", path) else ""


def clean_embed_url(provider, value):
    url = clean_url(value)
    if not url:
        return ""
    host = urlparse(url).netloc.lower().removeprefix("www.")
    if provider == "google_maps" and host in {"google.com", "maps.google.com"}:
        return url
    if provider == "spotify" and host in {"open.spotify.com"}:
        return url
    return ""


def clean_recipe(content):
    return {
        "title": clean_plain_text(content.get("title") or "Recipe"),
        "image": clean_url(content.get("image") or ""),
        "prep_time": clean_plain_text(content.get("prep_time") or ""),
        "cook_time": clean_plain_text(content.get("cook_time") or ""),
        "servings": clean_plain_text(content.get("servings") or ""),
        "ingredients": clean_text_list(content.get("ingredients"), fallback=["Add an ingredient"], limit=40),
        "steps": clean_text_list(content.get("steps"), fallback=["Add a step"], limit=30),
        "nutrition": clean_plain_text(content.get("nutrition") or ""),
        "tags": clean_text_list(content.get("tags"), limit=12),
    }


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
    blocks = [
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
        {"type": "faq", "label": "FAQ / Accordion", "description": "Question and answer sections"},
        {"type": "card_grid", "label": "Card Grid", "description": "Clickable resource cards"},
        {"type": "statistics", "label": "Impact Numbers", "description": "Prominent statistics"},
        {"type": "table_of_contents", "label": "Table of Contents", "description": "Links to H2 and H3 sections"},
        {"type": "related_posts", "label": "Related Posts", "description": "Dynamic related reading"},
        {"type": "featured_content", "label": "Featured Content", "description": "Promote one page or post"},
        {"type": "resource_download", "label": "Resource Download", "description": "PDF or document download"},
        {"type": "citation", "label": "Citation", "description": "Research reference"},
        {"type": "alert_notice", "label": "Health Notice", "description": "Educational alert or disclaimer"},
        {"type": "icon_list", "label": "Icon List", "description": "Visual list of benefits or steps"},
        {"type": "process_steps", "label": "Step-by-Step", "description": "Numbered process"},
        {"type": "definition", "label": "Definition", "description": "Glossary-style term"},
        {"type": "comparison_table", "label": "Comparison Table", "description": "Structured rows and columns"},
        {"type": "side_by_side", "label": "Side-by-Side", "description": "Compare two ideas"},
        {"type": "myth_fact", "label": "Myth vs Fact", "description": "Educational contrast"},
        {"type": "quiz", "label": "Quiz", "description": "One-question knowledge check"},
        {"type": "sponsor_logo_grid", "label": "Sponsor Logos", "description": "Sponsor recognition grid"},
        {"type": "team_profile", "label": "Team Profile", "description": "Person or expert profile"},
        {"type": "donation_progress", "label": "Donation Progress", "description": "Campaign progress bar"},
        {"type": "volunteer_cta", "label": "Volunteer CTA", "description": "Volunteer opportunity"},
        {"type": "event", "label": "Event", "description": "Webinar or community event"},
        {"type": "newsletter_archive", "label": "Newsletter Archive", "description": "Recent newsletter list"},
        {"type": "author_bio", "label": "Author Bio", "description": "Author profile block"},
        {"type": "article_metadata", "label": "Article Metadata", "description": "Date, author, category"},
        {"type": "medical_reviewer", "label": "Medical Reviewer", "description": "Reviewer credibility note"},
        {"type": "social_sharing", "label": "Social Sharing", "description": "Share buttons"},
        {"type": "post_navigation", "label": "Post Navigation", "description": "Previous and next posts"},
        {"type": "footnotes", "label": "Footnotes", "description": "Numbered reference notes"},
        {"type": "hero_section", "label": "Hero Section", "description": "Controlled page hero"},
        {"type": "section_container", "label": "Section Container", "description": "Reusable layout container"},
        {"type": "tabs", "label": "Tabs", "description": "Tabbed topic panels"},
        {"type": "image_gallery", "label": "Image Gallery", "description": "Structured image grid"},
        {"type": "image_text", "label": "Image and Text", "description": "Simple media section"},
        {"type": "logo_badge_row", "label": "Logo / Badge Row", "description": "Affiliations and badges"},
        {"type": "embed", "label": "Approved Embed", "description": "Google Maps or Spotify"},
        {"type": "recipe_card", "label": "Recipe Card", "description": "Recipe and ingredients"},
        {"type": "nutrition_facts", "label": "Nutrition Facts", "description": "Structured nutrition fields"},
        {"type": "glucose_tip", "label": "Glucose-Friendly Tip", "description": "Branded practical tip"},
        {"type": "meal_swap", "label": "Meal Swap", "description": "Instead-of and consider pairs"},
        {"type": "health_tool_card", "label": "Health Tool Card", "description": "Dynamic tool promotion"},
        {"type": "research_summary", "label": "Research Summary", "description": "Plain-language study summary"},
        {"type": "study_snapshot", "label": "Study Snapshot", "description": "Compact research facts"},
        {"type": "community_story", "label": "Community Story", "description": "Consent-aware story"},
    ]
    categories = {
        "basic": {"heading", "rich_text", "image", "button", "quote", "divider", "spacer"},
        "layout": {"section_container", "two_columns", "three_columns", "image_text", "card_grid", "tabs"},
        "media": {"image_gallery", "video", "embed", "resource_download"},
        "article": {
            "hero_section",
            "table_of_contents",
            "article_metadata",
            "author_bio",
            "medical_reviewer",
            "citation",
            "footnotes",
            "related_posts",
            "social_sharing",
            "post_navigation",
        },
        "education": {"faq", "definition", "process_steps", "comparison_table", "myth_fact", "quiz", "alert_notice"},
        "research": {"research_summary", "study_snapshot", "featured_content"},
        "health": {"recipe_card", "nutrition_facts", "glucose_tip", "meal_swap", "health_tool_card"},
        "nonprofit": {
            "donation_cta",
            "donation_progress",
            "volunteer_cta",
            "sponsor_logo_grid",
            "team_profile",
            "community_story",
            "event",
            "newsletter_signup",
            "newsletter_archive",
            "logo_badge_row",
            "statistics",
            "icon_list",
        },
    }
    icons = {
        "heading": "H",
        "rich_text": "¶",
        "image": "Img",
        "button": "Btn",
        "quote": "“”",
        "section_container": "Sec",
        "faq": "FAQ",
        "card_grid": "Grid",
        "statistics": "#",
        "research_summary": "Rx",
        "recipe_card": "Rec",
        "donation_cta": "$",
    }
    category_for_type = {}
    for category, block_types in categories.items():
        for block_type in block_types:
            category_for_type[block_type] = category
    for block in blocks:
        block["category"] = category_for_type.get(block["type"], "basic")
        block["icon"] = icons.get(block["type"], "+")
    return blocks


def render_blocks(blocks, config, renderer):
    prepared_blocks = prepare_blocks_for_render(validate_blocks(blocks))
    toc_items = collect_toc_items(prepared_blocks)
    return Markup("".join(render_block(block, config, renderer, toc_items=toc_items) for block in prepared_blocks))


def render_block(block, config, renderer, toc_items=None):
    block_type = block["type"]
    template = f"blocks/{block_type}.html"
    return renderer(
        template,
        block=block,
        config=config,
        video_embed_url=video_embed_url,
        embed_url=embed_url,
        toc_items=toc_items or [],
        related_content=related_content_for_block(block, config),
        featured_content=featured_content_for_block(block, config),
        health_tool=health_tool_for_block(block),
        social_share_links=social_share_links,
    )


def prepare_blocks_for_render(blocks):
    blocks = copy.deepcopy(blocks)
    used = set()

    def annotate(items):
        for block in items:
            if block.get("type") == "heading":
                text = block.get("content", {}).get("text") or "section"
                base = slugify(text)
                anchor = base
                index = 2
                while anchor in used:
                    anchor = f"{base}-{index}"
                    index += 1
                used.add(anchor)
                block.setdefault("settings", {})["anchor"] = anchor
            for column in block.get("content", {}).get("columns", []):
                annotate(column.get("blocks", []))
            annotate(block.get("content", {}).get("blocks", []))

    annotate(blocks)
    return blocks


def collect_toc_items(blocks):
    items = []

    def collect(block_list):
        for block in block_list:
            if block.get("type") == "heading" and int(block.get("settings", {}).get("level") or 2) in {2, 3}:
                items.append(
                    {
                        "level": int(block.get("settings", {}).get("level") or 2),
                        "text": block.get("content", {}).get("text") or "Section",
                        "anchor": block.get("settings", {}).get("anchor") or slugify(block.get("content", {}).get("text") or "section"),
                    }
                )
            for column in block.get("content", {}).get("columns", []):
                collect(column.get("blocks", []))
            collect(block.get("content", {}).get("blocks", []))

    collect(blocks)
    return items


def content_lookup(config):
    content = config.get("CONTENT")
    pages = getattr(content, "published_pages", []) if content else []
    posts = getattr(content, "latest_posts", []) if content else []
    return pages, posts


def related_content_for_block(block, config):
    if block.get("type") != "related_posts":
        return []
    pages, posts = content_lookup(config)
    slugs = block.get("content", {}).get("slugs", [])
    count = int(block.get("settings", {}).get("count") or 3)
    if slugs:
        by_slug = {item.get("slug"): item for item in pages + posts}
        return [by_slug[slug] for slug in slugs if slug in by_slug][:count]
    return posts[:count]


def featured_content_for_block(block, config):
    if block.get("type") != "featured_content":
        return None
    pages, posts = content_lookup(config)
    slug = block.get("content", {}).get("slug")
    for item in pages + posts:
        if item.get("slug") == slug:
            return item
    return posts[0] if posts else None


def health_tool_for_block(block):
    if block.get("type") != "health_tool_card":
        return {}
    tools = {
        "jeir": {"title": "JEIR", "url": "https://www.mindfuldiabetes.ai/", "description": "AI-guided diabetes and wellness education."},
        "memovela": {"title": "Memovela", "url": memovela_links.MEMOVELA_WEB_URL, "description": "A memory and wellness support tool."},
        "health_tools": {"title": "Health Tools Hub", "url": "/health-tools/", "description": "Explore Mindful Diabetes wellness tools."},
        "mindful_eating": {"title": "Mindful Eating", "url": "/mindful-eating/", "description": "Practice nutrition choices with a mindful lens."},
    }
    return tools.get(block.get("content", {}).get("tool"), tools["health_tools"])


def social_share_links(url="", title=""):
    encoded_url = url or ""
    encoded_title = title or ""
    return {
        "facebook": f"https://www.facebook.com/sharer/sharer.php?u={encoded_url}",
        "linkedin": f"https://www.linkedin.com/sharing/share-offsite/?url={encoded_url}",
        "x": f"https://twitter.com/intent/tweet?url={encoded_url}&text={encoded_title}",
        "email": f"mailto:?subject={encoded_title}&body={encoded_url}",
    }


def embed_url(provider, raw_url):
    cleaned = clean_embed_url(provider, raw_url)
    if not cleaned:
        return ""
    parsed = urlparse(cleaned)
    if provider == "spotify":
        path = parsed.path.strip("/")
        return f"https://open.spotify.com/embed/{path}" if path else ""
    if provider == "google_maps":
        return cleaned
    return ""


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
