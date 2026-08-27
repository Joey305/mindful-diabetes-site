import base64
import csv
import io
import json
import html as html_lib
import hmac
import hashlib
import os
import random
import re
import secrets
import click
from datetime import datetime, timedelta, timezone
from functools import wraps
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, quote, urlencode, urlparse
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flask import Flask, abort, jsonify, redirect, render_template, request, session, url_for
from markupsafe import Markup, escape

from mindful_diabetes import cms
from mindful_diabetes import analytics
from mindful_diabetes import memovela as memovela_links
from mindful_diabetes import resources as resource_library

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:  # pragma: no cover - optional until DATABASE_URL is configured
    psycopg = None
    dict_row = None


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_CONTENT_PATH = (
    BASE_DIR
    / "mindful_diabetes_wp_parse_outputs"
    / "wp_migration_outputs"
    / "flask_content_seed.json"
)
DEFAULT_ADMIN_EMAIL = "jmschulz@mindfuldiabetes.org"
ADMIN_CODE_TTL_MINUTES = 10
ADMIN_SESSION_HOURS = 12
DEFAULT_GROWTH_GOALS = [
    {
        "metric": "page_views",
        "label": "Reach more readers",
        "target": 500,
        "unit": "pages read",
        "why": "More reading gives every newsletter, tool, and donation CTA more chances to work.",
    },
    {
        "metric": "anonymous_sessions",
        "label": "Grow visitor sessions",
        "target": 250,
        "unit": "sessions",
        "why": "Sessions are anonymous, but they show whether the site is reaching more people.",
    },
    {
        "metric": "newsletter_signups",
        "label": "Build the newsletter list",
        "target": 25,
        "unit": "signups",
        "why": "Email gives Mindful Diabetes a repeat audience instead of one-time visitors.",
    },
    {
        "metric": "health_tool_clicks",
        "label": "Send readers to tools",
        "target": 50,
        "unit": "tool clicks",
        "why": "Tool clicks show readers are moving from learning into action.",
    },
    {
        "metric": "donation_interest",
        "label": "Increase support intent",
        "target": 10,
        "unit": "support actions",
        "why": "Donation intent is an early signal before confirmed donations are connected.",
    },
]
PRESERVED_CONTENT_CLASSES = {
    "article-image-placeholder",
    "article-callout",
    "article-callout__title",
    "article-impact-card",
    "article-impact-grid",
    "article-table-wrap",
    "article-wellness-tools",
    "article-wellness-tools__intro",
    "article-wellness-tools__title",
    "article-wellness-tools__grid",
    "article-wellness-tools__resources",
    "article-tool-card",
    "article-tool-card--jeir",
    "article-tool-card--memovela",
    "article-tool-card--game",
    "eyebrow",
}


def load_env_file(path):
    if not path.exists():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env_file(BASE_DIR / ".env")


PAYPAL_HOSTED_BUTTON_ID = os.getenv("PAYPAL_HOSTED_BUTTON_ID", "5BM2YU7LNZDVJ")
POSTS_PER_GUIDE_PAGE = 9
DEFAULT_MAILCHIMP_TAGS = ["Mindful Diabetes Subscribers"]
PUBLIC_SITE_URL = os.getenv("SITE_BASE_URL", "https://mindfuldiabetes.org").rstrip("/")
FREE_GUIDES_PDF_STATIC_DIR = BASE_DIR / "static" / "free-guides" / "pdfs"
FREE_GUIDES_IMAGE_STATIC_DIR = BASE_DIR / "static" / "free-guides" / "images"
FREE_GUIDE_DEFINITIONS = [
    {
        "slug": "mindful-plate",
        "title": "The Mindful Plate",
        "subtitle": "A Simple Guide to Blood Sugar-Friendly Eating",
        "description": (
            "Learn a flexible way to build meals with vegetables, protein, carbohydrates, fiber, healthy fats, and satisfying flavor. "
            "The guide includes breakfast, lunch, dinner, snack, drink, and grocery examples, plus a printable meal-building worksheet."
        ),
        "who": "A practical first guide for people with type 2 diabetes, prediabetes, or an interest in more balanced everyday meals.",
        "category": "Nutrition",
        "tags": ["Nutrition", "Meal Planning", "Blood Sugar"],
        "page_count": 21,
        "pdf_filename": "mindful-diabetes-mindful-plate-guide-2026.pdf",
        "cover_filename": "mindful-plate-cover-preview.png",
        "thumb_filename": "mindful-plate-download-card-thumbnail.png",
        "banner_filename": "mindful-plate-banner-16x9.png",
        "square_filename": "mindful-plate-square-promo.png",
        "alt_text": "Cover preview for The Mindful Plate free guide.",
        "inside": [
            "A simple plate method for blood sugar-friendly meals",
            "How carbohydrates, protein, fat, and fiber work together",
            "Breakfast, lunch, dinner, snack, and drink examples",
            "Budget-conscious swaps and culturally flexible meal ideas",
            "A printable build-a-meal worksheet",
        ],
        "topics": ["Plate method", "Carbohydrates", "Fiber", "Protein", "Drinks", "Meal planning"],
        "related_guide_slugs": ["grocery-store-survival-guide", "fats-without-fear"],
        "related_links": [
            {"label": "Diabetes Guide", "endpoint": "guide"},
            {"label": "Health Tools", "endpoint": "health_tools"},
        ],
    },
    {
        "slug": "fats-without-fear",
        "title": "Fats Without Fear",
        "subtitle": "A Plain-English Guide to Dietary Fats, Heart Health, and Brain Health",
        "description": (
            "Understand saturated, unsaturated, and trans fats without the fear or confusing wellness claims. Compare cooking oils, "
            "learn how to read fat information on food labels, and try realistic swaps that still taste like real food."
        ),
        "who": "Anyone confused by conflicting advice about butter, oils, nuts, fish, cholesterol, coconut oil, or dietary fat.",
        "category": "Heart Health",
        "tags": ["Healthy Fats", "Heart Health", "Brain Health"],
        "page_count": 21,
        "pdf_filename": "mindful-diabetes-fats-without-fear-2026.pdf",
        "cover_filename": "fats-without-fear-cover-preview.png",
        "thumb_filename": "fats-without-fear-download-card-thumbnail.png",
        "banner_filename": "fats-without-fear-banner-16x9.png",
        "square_filename": "fats-without-fear-square-promo.png",
        "alt_text": "Cover preview for Fats Without Fear free guide.",
        "inside": [
            "The difference between unsaturated, saturated, and trans fats",
            "Cooking oil comparisons for everyday kitchens",
            "Food-label cues for heart-health decisions",
            "Realistic swaps for common meals and snacks",
            "A printable fat-swap worksheet",
        ],
        "topics": ["Unsaturated fats", "Saturated fat", "Trans fat", "Cooking oils", "Cholesterol", "Food swaps"],
        "related_guide_slugs": ["mindful-plate", "grocery-store-survival-guide", "blood-sugar-brain-health"],
        "related_links": [
            {"label": "Health Tools", "endpoint": "health_tools"},
            {"label": "Research", "endpoint": "research"},
        ],
    },
    {
        "slug": "grocery-store-survival-guide",
        "title": "The Grocery Store Survival Guide",
        "subtitle": "How to Make Practical, Blood Sugar-Conscious Choices Without Feeling Overwhelmed",
        "description": (
            "Make grocery shopping easier with a practical cart formula, label-reading guidance, affordable food ideas, pantry backups, "
            "quick meal combinations, and a printable shopping checklist."
        ),
        "who": "People who want to shop more confidently without needing a nutrition degree or an unlimited budget.",
        "category": "Shopping",
        "tags": ["Grocery Shopping", "Food Labels", "Budget-Friendly"],
        "page_count": 22,
        "pdf_filename": "mindful-diabetes-grocery-store-guide-2026.pdf",
        "cover_filename": "grocery-store-survival-guide-cover-preview.png",
        "thumb_filename": "grocery-store-survival-guide-download-card-thumbnail.png",
        "banner_filename": "grocery-store-survival-guide-banner-16x9.png",
        "square_filename": "grocery-store-survival-guide-square-promo.png",
        "alt_text": "Cover preview for The Grocery Store Survival Guide free guide.",
        "inside": [
            "A practical cart formula for balanced shopping",
            "How to use food labels without getting stuck",
            "Affordable staples and pantry backups",
            "Quick meal combinations from common ingredients",
            "A printable shopping checklist",
        ],
        "topics": ["Food labels", "Pantry staples", "Budget meals", "Cart planning", "Quick meals", "Shopping checklist"],
        "related_guide_slugs": ["mindful-plate", "fats-without-fear"],
        "related_links": [
            {"label": "Health Tools", "endpoint": "health_tools"},
            {"label": "Diabetes Guide", "endpoint": "guide"},
        ],
    },
    {
        "slug": "7-day-prevention-reset",
        "title": "The 7-Day Prevention Reset",
        "subtitle": "A Gentle One-Week Plan for Building Healthier Everyday Habits",
        "description": (
            "Spend one week noticing your routines and testing small changes related to meals, drinks, fiber, movement, sleep, and planning. "
            "Printable trackers help you learn what works without turning the week into a crash diet or perfection challenge."
        ),
        "who": "Anyone who wants a gentle, structured starting point rather than a dramatic lifestyle overhaul.",
        "category": "Habits",
        "tags": ["7-Day Plan", "Healthy Habits", "Printable Trackers"],
        "page_count": 21,
        "pdf_filename": "mindful-diabetes-7-day-prevention-reset-2026.pdf",
        "cover_filename": "7-day-prevention-reset-cover-preview.png",
        "thumb_filename": "7-day-prevention-reset-download-card-thumbnail.png",
        "banner_filename": "7-day-prevention-reset-banner-16x9.png",
        "square_filename": "7-day-prevention-reset-square-promo.png",
        "alt_text": "Cover preview for The 7-Day Prevention Reset free guide.",
        "inside": [
            "A one-week plan for meals, movement, sleep, and planning",
            "Low-pressure habit experiments instead of perfection goals",
            "Daily reflection prompts and routine check-ins",
            "Printable trackers for noticing what helps",
            "A reset recap worksheet for choosing next steps",
        ],
        "topics": ["Habit tracking", "Movement", "Sleep", "Meal routines", "Hydration", "Weekly planning"],
        "related_guide_slugs": ["mindful-plate", "grocery-store-survival-guide"],
        "related_links": [
            {"label": "Health Tools", "endpoint": "health_tools"},
            {"label": "Newsletter", "url": "#free-guides-newsletter"},
        ],
    },
    {
        "slug": "blood-sugar-brain-health",
        "title": "Blood Sugar & Brain Health",
        "subtitle": "Understanding the Everyday Connection",
        "description": (
            "Learn how glucose, insulin resistance, blood vessels, blood pressure, sleep, movement, hearing, social connection, and other "
            "factors may relate to long-term brain health. The guide explains risk carefully without suggesting that dementia is inevitable."
        ),
        "who": "Adults and families interested in the connection between metabolic, cardiovascular, and cognitive health.",
        "category": "Brain Health",
        "tags": ["Brain Health", "Diabetes Education", "Prevention"],
        "page_count": 24,
        "pdf_filename": "mindful-diabetes-blood-sugar-brain-health-2026.pdf",
        "cover_filename": "blood-sugar-brain-health-cover-preview.png",
        "thumb_filename": "blood-sugar-brain-health-download-card-thumbnail.png",
        "banner_filename": "blood-sugar-brain-health-banner-16x9.png",
        "square_filename": "blood-sugar-brain-health-square-promo.png",
        "alt_text": "Cover preview for Blood Sugar & Brain Health free guide.",
        "inside": [
            "A careful overview of metabolic and brain-health connections",
            "How blood vessels, pressure, sleep, and movement fit the picture",
            "Risk language that avoids fear and false certainty",
            "Family-friendly conversation prompts",
            "A printable brain-health action map",
        ],
        "topics": ["Insulin resistance", "Blood vessels", "Sleep", "Movement", "Blood pressure", "Cognitive health"],
        "related_guide_slugs": ["mindful-plate", "fats-without-fear", "7-day-prevention-reset"],
        "related_links": [
            {"label": "Research", "endpoint": "research"},
            {"label": "Health Tools", "endpoint": "health_tools"},
            {"label": "JEIR", "url": "https://www.mindfuldiabetes.ai/"},
            {"label": "Memovela", "url": memovela_links.MEMOVELA_WEB_URL},
        ],
    },
]
COMPANION_GUIDE_POSTS = {
    "fats-guide": "fats-without-fear",
}
FATS_GUIDE_LANDING = {
    "eyebrow": "Pathways to Wellness | Nutrition",
    "title": "The Truth About Fats",
    "subtitle": "Saturated, Unsaturated, and Trans Fats",
    "glance_cards": [
        {
            "title": "Unsaturated Fats",
            "body": "The article describes unsaturated fats as heart-healthy fats found in foods such as olive oil, avocados, nuts, seeds, and fatty fish.",
        },
        {
            "title": "Saturated Fats",
            "body": "Saturated fats are presented as more complex: they are commonly found in animal products and tropical oils, and the article emphasizes context and moderation.",
        },
        {
            "title": "Trans Fats",
            "body": "The article identifies trans fats as the fats to avoid, especially partially hydrogenated oils and highly processed foods that may contain them.",
        },
    ],
    "contents": [
        {"label": "Understanding Dietary Fats", "href": "#understanding-dietary-fats"},
        {"label": "Saturated Fats", "href": "#saturated-fats"},
        {"label": "Unsaturated Fats", "href": "#unsaturated-fats"},
        {"label": "Trans Fats", "href": "#trans-fats"},
        {"label": "Practical Food Choices", "href": "#practical-food-choices"},
        {"label": "Free Fats Guide", "href": "#free-fats-guide"},
        {"label": "Related Resources", "href": "#related-free-guides"},
    ],
    "related_guide_slugs": ["mindful-plate", "grocery-store-survival-guide", "blood-sugar-brain-health"],
}
RESEARCH_PUBLICATIONS = [
    {
        "title": "PyMACS: A Python-Based Automation Suite for GROMACS Molecular Dynamics Setup, Simulation, and Analysis",
        "date": "2026",
        "venue": "SSRN preprint / European Journal of Medicinal Chemistry record",
        "type": "Computational methods",
        "tags": ["Molecular dynamics", "Automation", "Drug discovery"],
        "excerpt": (
            "PyMACS turns a technically demanding molecular dynamics workflow into a more reproducible, scriptable pipeline. "
            "For Mindful Diabetes, this kind of computational infrastructure matters because it supports faster, cleaner exploration "
            "of biological targets and therapeutic hypotheses."
        ),
        "links": [
            {"label": "SSRN DOI", "url": "https://doi.org/10.2139/ssrn.6584500"},
            {"label": "Journal DOI", "url": "https://doi.org/10.1016/j.ejmech.2026.119038"},
        ],
    },
    {
        "title": "PRosettaC outperforms AlphaFold3 for modeling PROTAC ternary complexes",
        "date": "2025-10-28",
        "venue": "Scientific Reports",
        "type": "Journal article",
        "tags": ["PROTACs", "Protein modeling", "AI comparison"],
        "excerpt": (
            "This study compares structure-prediction approaches for PROTAC ternary complexes, a difficult problem in targeted protein degradation. "
            "It shows active work at the intersection of computational biology, therapeutic design, and model evaluation."
        ),
        "links": [{"label": "DOI", "url": "https://doi.org/10.1038/s41598-025-21502-8"}],
    },
    {
        "title": "Broad Perspective of Smart Home Technology in 2024",
        "date": "2024-08-07",
        "venue": "International Journal of Smart Technologies",
        "type": "Journal article",
        "tags": ["Smart homes", "Health technology", "Daily living"],
        "excerpt": (
            "This article surveys the modern smart-home landscape and its role in everyday support systems. "
            "That perspective connects directly to prevention work: better environments can make healthy routines easier to start and sustain."
        ),
        "links": [{"label": "DOI", "url": "https://doi.org/10.4018/IJST.350186"}],
    },
    {
        "title": "Targeted degrader technologies as prospective SARS-CoV-2 therapies",
        "date": "2024-01",
        "venue": "Drug Discovery Today",
        "type": "Journal article",
        "tags": ["Targeted degradation", "Antivirals", "Therapeutic strategy"],
        "excerpt": (
            "This review explores how targeted protein degradation could become part of antiviral therapeutic development. "
            "It reflects a broader research focus on translating molecular mechanisms into practical treatment strategies."
        ),
        "links": [{"label": "DOI", "url": "https://doi.org/10.1016/j.drudis.2023.103847"}],
    },
    {
        "title": "Dynamic scRNA-seq of live human pancreatic slices reveals functional endocrine cell neogenesis through an intermediate ducto-acinar stage",
        "date": "2023-11",
        "venue": "Cell Metabolism",
        "type": "Journal article",
        "tags": ["Pancreatic biology", "Single-cell RNA-seq", "Endocrine cells"],
        "excerpt": (
            "This pancreatic-slice study uses live human tissue and single-cell sequencing to investigate endocrine cell formation. "
            "It is especially relevant to diabetes research because it examines cellular plasticity in the organ central to insulin biology."
        ),
        "links": [{"label": "DOI", "url": "https://doi.org/10.1016/j.cmet.2023.10.001"}],
    },
    {
        "title": "Embryonic adipose development and consequences in later life",
        "date": "2023-10-18",
        "venue": "SCIREA Journal of Biology",
        "type": "Journal article",
        "tags": ["Adipose biology", "Development", "Metabolism"],
        "excerpt": (
            "This work looks at adipose development early in life and how developmental events may shape later health. "
            "It supports the Mindful Diabetes emphasis on prevention by looking upstream, before metabolic problems become entrenched."
        ),
        "links": [{"label": "DOI", "url": "https://doi.org/10.54647/biology180324"}],
    },
    {
        "title": "The Potential of Induced Pluripotent Stem Cells to Treat and Model Alzheimer's Disease",
        "date": "2021-05-26",
        "venue": "Stem Cells International",
        "type": "Journal article",
        "tags": ["Alzheimer's disease", "iPSCs", "Disease modeling"],
        "excerpt": (
            "This article reviews how induced pluripotent stem cells can help model Alzheimer's disease and support therapeutic discovery. "
            "It sits close to Mindful Diabetes' core mission by connecting brain health, disease modeling, and future intervention pathways."
        ),
        "links": [{"label": "DOI", "url": "https://doi.org/10.1155/2021/5511630"}],
    },
    {
        "title": "Concise Modular Synthesis of Thalassotalic Acids A-C",
        "date": "2019-04-26",
        "venue": "Journal of Natural Products",
        "type": "Journal article",
        "tags": ["Natural products", "Chemical synthesis", "Medicinal chemistry"],
        "excerpt": (
            "This chemistry paper focuses on modular synthesis of thalassotalic acids, adding a foundational medicinal-chemistry thread to the research portfolio. "
            "It rounds out the publication record with hands-on chemical synthesis experience."
        ),
        "links": [{"label": "DOI", "url": "https://doi.org/10.1021/acs.jnatprod.9b00028"}],
    },
]


def create_app(test_config=None):
    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder=str(BASE_DIR / "templates"),
        static_folder=str(BASE_DIR / "static"),
    )
    app.config.from_mapping(
        CONTENT_PATH=os.getenv("CONTENT_PATH", str(DEFAULT_CONTENT_PATH)),
        PAYPAL_HOSTED_BUTTON_ID=PAYPAL_HOSTED_BUTTON_ID,
        MAILCHIMP_API_KEY=os.getenv("MAILCHIMP_API_KEY", ""),
        MAILCHIMP_AUDIENCE_ID=os.getenv("MAILCHIMP_AUDIENCE_ID", ""),
        MAILCHIMP_SERVER_PREFIX=os.getenv("MAILCHIMP_SERVER_PREFIX", ""),
        MAILCHIMP_TAGS=os.getenv("MAILCHIMP_TAGS", ",".join(DEFAULT_MAILCHIMP_TAGS)),
        SECRET_KEY=os.getenv("SECRET_KEY") or os.getenv("ADMIN_SESSION_SECRET") or "dev-only-change-me",
        ADMIN_EMAIL=os.getenv("ADMIN_EMAIL", DEFAULT_ADMIN_EMAIL),
        ADMIN_EMAIL_FROM=os.getenv(
            "ADMIN_EMAIL_FROM",
            "Mindful Diabetes <login@auth.mindfuldiabetes.org>",
        ),
        ADMIN_DATA_PATH=os.getenv("ADMIN_DATA_PATH", str(BASE_DIR / "instance" / "admin_data.json")),
        CMS_DATA_PATH=os.getenv("CMS_DATA_PATH", str(BASE_DIR / "instance" / "cms_content.json")),
        CMS_LOCAL_UPLOAD_ROOT=os.getenv("CMS_LOCAL_UPLOAD_ROOT", str(BASE_DIR / "static")),
        ANALYTICS_STORAGE_BACKEND=os.getenv("ANALYTICS_STORAGE_BACKEND", "local"),
        ANALYTICS_LOCAL_PATH=os.getenv("ANALYTICS_LOCAL_PATH", str(BASE_DIR / "instance" / "analytics.sqlite3")),
        ANALYTICS_RETENTION_DAYS=int(os.getenv("ANALYTICS_RETENTION_DAYS", analytics.DEFAULT_RETENTION_DAYS)),
        ANALYTICS_ENABLE_LOCAL_TESTING=os.getenv("ANALYTICS_ENABLE_LOCAL_TESTING", ""),
        ANALYTICS_REPORT_RECIPIENTS=os.getenv("ANALYTICS_REPORT_RECIPIENTS", ""),
        ANALYTICS_GROWTH_GOALS_JSON=os.getenv("ANALYTICS_GROWTH_GOALS_JSON", ""),
        ANALYTICS_REMOTE_BASE_URL=os.getenv("ANALYTICS_REMOTE_BASE_URL", ""),
        ANALYTICS_REMOTE_API_TOKEN=os.getenv("ANALYTICS_REMOTE_API_TOKEN", ""),
        ANALYTICS_REMOTE_TIMEOUT_SECONDS=os.getenv("ANALYTICS_REMOTE_TIMEOUT_SECONDS", "5"),
        GOOGLE_ADS_CONVERSION_ID=os.getenv("GOOGLE_ADS_CONVERSION_ID", "AW-11435654295"),
        GOOGLE_ADS_CONVERSION_ACTIONS_JSON=os.getenv("GOOGLE_ADS_CONVERSION_ACTIONS_JSON", "{}"),
        GOOGLE_ADS_ENABLE_LOCAL_TESTING=os.getenv("GOOGLE_ADS_ENABLE_LOCAL_TESTING", ""),
        SITE_BASE_URL=os.getenv("SITE_BASE_URL", "https://mindfuldiabetes.org"),
        PAYPAL_CLIENT_ID=os.getenv("PAYPAL_CLIENT_ID", ""),
        PAYPAL_CLIENT_SECRET=os.getenv("PAYPAL_CLIENT_SECRET", ""),
        PAYPAL_WEBHOOK_ID=os.getenv("PAYPAL_WEBHOOK_ID", ""),
        PAYPAL_ENVIRONMENT=os.getenv("PAYPAL_ENVIRONMENT", "live"),
        BREVO_API_KEY=os.getenv("BREVO_API_KEY", ""),
        BREVO_SMTP_URL=os.getenv("BREVO_SMTP_URL", "https://api.brevo.com/v3/smtp/email"),
        DATABASE_URL=os.getenv("DATABASE_URL", ""),
        TURNSTILE_SITE_KEY=os.getenv("TURNSTILE_SITE_KEY", ""),
        TURNSTILE_SECRET_KEY=os.getenv("TURNSTILE_SECRET_KEY", ""),
        TURNSTILE_VERIFY_URL=os.getenv(
            "TURNSTILE_VERIFY_URL",
            "https://challenges.cloudflare.com/turnstile/v0/siteverify",
        ),
        SITE_DESCRIPTION=(
            "Preventing the progression of Type II to Type III Diabetes, "
            "one person at a time."
        ),
    )

    if test_config:
        app.config.update(test_config)

    app.secret_key = app.config["SECRET_KEY"]
    app.permanent_session_lifetime = timedelta(hours=ADMIN_SESSION_HOURS)

    content = load_content(Path(app.config["CONTENT_PATH"]))
    app.config["CONTENT"] = content
    ensure_admin_storage(app.config)
    cms.ensure_cms_storage(app.config)
    if app.config["ANALYTICS_STORAGE_BACKEND"] == "local":
        analytics.analytics_store(app.config).health_check()
    register_analytics_commands(app)

    @app.context_processor
    def inject_site_data():
        return {
            "nav_pages": content.nav_pages,
            "navigation_state": navigation_state_for_request(content),
            "paypal_button_id": app.config["PAYPAL_HOSTED_BUTTON_ID"],
            "site_description": app.config["SITE_DESCRIPTION"],
            "memovela": memovela_links.link_config(),
            "newsletter_enabled": is_mailchimp_configured(app.config),
            "turnstile_site_key": (
                app.config["TURNSTILE_SITE_KEY"] if is_turnstile_configured(app.config) else ""
            ),
            "admin_csrf_token": get_admin_csrf_token,
            "analytics_browser_config": browser_analytics_config(app.config),
            "google_ads_config": google_ads_tracking_config(app.config),
        }

    @app.template_filter("date_label")
    def date_label(value):
        return format_date(value)

    @app.template_filter("wordpress_html")
    def wordpress_html(value):
        return Markup(clean_wordpress_html(value or "", app.config["PAYPAL_HOSTED_BUTTON_ID"]))

    @app.template_filter("article_html")
    def article_html(value, post_slug="", companion_guide=None, post_title="", article_section_title=""):
        return Markup(
            clean_article_html(
                value or "",
                app.config["PAYPAL_HOSTED_BUTTON_ID"],
                post_slug=post_slug,
                companion_guide=companion_guide,
                post_title=post_title,
                article_section_title=article_section_title,
            )
        )

    @app.template_filter("jeir_article_html")
    def jeir_article_html(value):
        return Markup(
            clean_article_html(
                value or "",
                app.config["PAYPAL_HOSTED_BUTTON_ID"],
                post_slug="diabetes-health-jeir-updates",
            )
        )

    @app.errorhandler(404)
    def not_found(error):
        search_hint = " ".join(re.findall(r"[A-Za-z0-9]+", request.path.strip("/").replace("-", " ")))[:80]
        return (
            render_template(
                "404.html",
                search_hint=search_hint,
                latest_posts=content.latest_posts[:3],
            ),
            404,
        )

    def admin_required(view):
        @wraps(view)
        def wrapped_view(*args, **kwargs):
            if normalize_email(session.get("admin_email")) != normalize_email(app.config["ADMIN_EMAIL"]):
                return redirect(url_for("admin_login", next=request.path))
            return view(*args, **kwargs)

        return wrapped_view

    def render_cms_content(item, preview=False):
        rendered_blocks = cms.render_blocks(
            item["blocks_json"],
            app.config,
            lambda template, **context: render_template(template, item=item, **context),
        )
        template = "cms_post.html" if item["content_type"] == "post" else "cms_page.html"
        return render_template(
            template,
            item=item,
            rendered_blocks=rendered_blocks,
            preview=preview,
            latest_posts=content.latest_posts[:3],
        )

    @app.get("/")
    def home():
        page = content.pages_by_slug.get("mindful")
        if not page:
            abort(404)
        return render_template(
            "home.html",
            page=page,
            latest_posts=content.latest_posts[:6],
            memovela_post=content.posts_by_slug.get("memovela"),
        )

    @app.get("/guide/")
    def guide():
        page = content.pages_by_slug.get("guide")
        if not page:
            abort(404)
        page_number = request.args.get("page", default=1, type=int)
        if page_number < 1:
            abort(404)

        total_posts = len(content.latest_posts)
        total_pages = max(1, (total_posts + POSTS_PER_GUIDE_PAGE - 1) // POSTS_PER_GUIDE_PAGE)
        if page_number > total_pages:
            abort(404)

        start = (page_number - 1) * POSTS_PER_GUIDE_PAGE
        return render_template(
            "guide.html",
            page=page,
            latest_posts=content.latest_posts[start : start + POSTS_PER_GUIDE_PAGE],
            pagination={
                "page": page_number,
                "pages": total_pages,
                "total": total_posts,
                "per_page": POSTS_PER_GUIDE_PAGE,
                "endpoint": "guide",
            },
        )

    @app.get("/search/")
    def search():
        query = request.args.get("q", "").strip()
        results = search_content(
            content,
            query,
            extra_items=[
                health_tools_search_item(content),
                research_search_item(),
                volunteer_search_item(),
                resources_search_item(),
                *resource_search_items(),
                free_guides_search_item(),
                *free_guide_search_items(),
            ],
        )
        if query:
            record_server_analytics_event(
                app.config,
                content,
                "site_search",
                page_path=request.path,
                page_title="Search",
                element_id="site-search",
                element_label=query,
                element_type="form",
                element_position="site-search",
                source=request.args.get("utm_source", ""),
                medium=request.args.get("utm_medium", ""),
                campaign=request.args.get("utm_campaign", ""),
                term=request.args.get("utm_term", ""),
                campaign_content=request.args.get("utm_content", ""),
                metadata={"search_query": query.lower(), "result_count": len(results)},
            )
        return render_template("search.html", query=query, results=results)

    @app.get("/favicon.ico")
    def favicon():
        return redirect(url_for("static", filename="img/mdi-favicon-32.png"), code=302)

    @app.post("/subscribe/")
    def subscribe():
        email = request.form.get("email", "").strip()
        source = request.form.get("source", "site")
        bot_field = request.form.get("website", "").strip()

        if bot_field:
            return render_template(
                "subscribe.html",
                status="success",
                title="You're subscribed",
                message="Thanks for joining the Mindful Diabetes newsletter.",
                email=email,
                source=source,
            )

        if not is_valid_email(email):
            return render_template(
                "subscribe.html",
                status="error",
                title="Please check the email address",
                message="Enter a valid email address and try again.",
                email=email,
                source=source,
            ), 400

        turnstile_success, turnstile_message = verify_turnstile(
            app.config,
            request.form.get("cf-turnstile-response", ""),
            request.headers.get("CF-Connecting-IP") or request.remote_addr or "",
        )
        if not turnstile_success:
            return render_template(
                "subscribe.html",
                status="error",
                title="Please complete the human check",
                message=turnstile_message,
                email=email,
                source=source,
            ), 400

        if not is_mailchimp_configured(app.config):
            return render_template(
                "subscribe.html",
                status="setup",
                title="Newsletter signup is ready for Mailchimp",
                message=(
                    "The form is connected on the site. Add the Mailchimp API key "
                    "and audience ID to .env, then restart Flask to send signups to Mailchimp."
                ),
                email=email,
                source=source,
            ), 503

        success, message = subscribe_to_mailchimp(app.config, email)
        if not success:
            return render_template(
                "subscribe.html",
                status="error",
                title="We could not complete that signup",
                message=message,
                email=email,
                source=source,
            ), 502

        newsletter_success_event = request.form.get("analytics_success_event") or "newsletter_signup"
        if newsletter_success_event not in analytics.VALID_EVENT_NAMES:
            newsletter_success_event = "newsletter_signup"
        record_server_analytics_event(
            app.config,
            content,
            newsletter_success_event,
            page_path=request.form.get("page_path") or request.path,
            page_title="Newsletter signup",
            element_id=request.form.get("analytics_element_id", ""),
            element_label="Newsletter signup",
            element_type="form",
            element_position=request.form.get("analytics_position", source or "newsletter"),
            source=source,
            anonymous_session_id=request.form.get("analytics_session_id", ""),
            metadata={
                "signup_form_id": request.form.get("analytics_form_id") or source or "newsletter",
                "provider_outcome": "accepted",
                "subscriber_status": "accepted",
                "accepted": True,
            },
        )

        return render_template(
            "subscribe.html",
            status="success",
            title="You're subscribed",
            message="Thanks for joining the Mindful Diabetes newsletter.",
            email=email,
            source=source,
        )

    @app.get("/blog/")
    def blog_redirect():
        return redirect(url_for("guide"), code=301)

    @app.get("/donate/")
    def donate_redirect():
        return redirect(url_for("page_detail", slug="donation"), code=301)

    @app.get("/pages/")
    def pages_index():
        return render_template("pages.html", pages=content.published_pages)

    @app.get("/research/")
    def research():
        return render_template("research.html", publications=RESEARCH_PUBLICATIONS)

    @app.get("/health-tools/")
    def health_tools():
        tool_post_slugs = [
            "diabetes-health-jeir-updates",
            "memovela",
            "healthy-eating",
            "diabetes-artificial-intelligence-jeir",
        ]
        return render_template(
            "health_tools.html",
            tool_posts={slug: content.posts_by_slug.get(slug) for slug in tool_post_slugs},
        )

    @app.get("/free-guides")
    def free_guides_no_slash():
        return redirect(url_for("free_guides"), code=301)

    @app.get("/free-guides/")
    def free_guides():
        guides = build_free_guide_cards(content)
        return render_template(
            "free_guides.html",
            guides=guides,
            featured_guide=guides[0],
            canonical_url=f"{PUBLIC_SITE_URL}/free-guides",
        )

    @app.get("/resources")
    def resources_index():
        grouped_resources = resource_library.resources_grouped_by_category()
        return render_template(
            "resources.html",
            grouped_resources=grouped_resources,
            resources=resource_library.all_resources(),
            jeir_url=resource_library.JEIR_URL,
            ai_resources_url=resource_library.AI_RESOURCES_URL,
            canonical_url=f"{PUBLIC_SITE_URL}/resources",
        )

    @app.get("/resources/")
    def resources_index_slash():
        return redirect(url_for("resources_index"), code=301)

    @app.get("/resources/free-guides")
    @app.get("/resources/free-guides/")
    def resources_free_guides_redirect():
        return redirect(url_for("free_guides"), code=301)

    @app.get("/resources/<resource_slug>")
    def resource_detail(resource_slug):
        resource = resource_library.resource_by_slug(resource_slug)
        if not resource:
            abort(404)
        return redirect(url_with_attribution(resource["external_url"]), code=301)

    @app.get("/resources/<resource_slug>/")
    def resource_detail_slash(resource_slug):
        return redirect(url_for("resource_detail", resource_slug=resource_slug), code=301)

    @app.get("/free-guides/<guide_slug>")
    def free_guide_detail_no_slash(guide_slug):
        return redirect(url_for("free_guide_detail", guide_slug=guide_slug), code=301)

    @app.get("/free-guides/<guide_slug>/")
    def free_guide_detail(guide_slug):
        guides = build_free_guide_cards(content)
        guide = next((item for item in guides if item["slug"] == guide_slug), None)
        if not guide:
            abort(404)
        related_guides = [item for item in guides if item["slug"] in guide["related_guide_slugs"]]
        return render_template(
            "free_guide_detail.html",
            guide=guide,
            related_guides=related_guides,
            canonical_url=f"{PUBLIC_SITE_URL}/free-guides/{guide['slug']}",
        )

    @app.get("/volunteer/")
    def volunteer():
        return render_template("volunteer.html")

    @app.route("/admin/login/", methods=["GET", "POST"])
    def admin_login():
        admin_email = app.config["ADMIN_EMAIL"]
        if request.method == "POST":
            email = request.form.get("email", "").strip()
            code = request.form.get("code", "").strip()
            next_url = safe_admin_next_url(request.form.get("next") or request.args.get("next") or url_for("admin_dashboard"))

            if code:
                success, message = verify_admin_login_code(app.config, email, code)
                if success:
                    session.clear()
                    session.permanent = True
                    session["admin_email"] = normalize_email(admin_email)
                    session["admin_login_at"] = utc_now().isoformat()
                    record_activity_event(
                        app.config,
                        "admin_login",
                        request.path,
                        "Admin login",
                        {"email": normalize_email(admin_email)},
                    )
                    return redirect(next_url)

                return render_template(
                    "admin_login.html",
                    admin_email=admin_email,
                    email=email,
                    code_requested=True,
                    error=message,
                    next_url=next_url,
                ), 400

            if not is_valid_email(email):
                return render_template(
                    "admin_login.html",
                    admin_email=admin_email,
                    email=email,
                    error="Enter the admin email address to request a code.",
                    next_url=next_url,
                ), 400

            code_requested = False
            notice = "If that email is the site admin, a one-time code is on its way."
            error = ""
            if normalize_email(email) == normalize_email(admin_email):
                code_requested = True
                one_time_code = generate_admin_code()
                save_admin_login_code(app.config, email, one_time_code)
                sent, send_message = send_admin_login_code(app.config, email, one_time_code)
                if not sent:
                    error = send_message
                    code_requested = False
                else:
                    notice = "Check your email for the one-time admin code."

            return render_template(
                "admin_login.html",
                admin_email=admin_email,
                email=email,
                code_requested=code_requested,
                notice=notice,
                error=error,
                next_url=next_url,
            ), 503 if error else 200

        return render_template(
            "admin_login.html",
            admin_email=admin_email,
            email="",
            next_url=safe_admin_next_url(request.args.get("next") or url_for("admin_dashboard")),
        )

    @app.get("/admin/logout/")
    def admin_logout():
        session.clear()
        return redirect(url_for("admin_login"))

    @app.get("/admin/")
    @admin_required
    def admin_dashboard():
        dashboard = build_admin_dashboard(app.config, request.args)
        return render_template("admin_dashboard.html", dashboard=dashboard, admin_email=app.config["ADMIN_EMAIL"])

    @app.get("/admin/analytics/")
    @admin_required
    def admin_analytics():
        dashboard = build_admin_dashboard(app.config, request.args)
        return render_template("admin_dashboard.html", dashboard=dashboard, admin_email=app.config["ADMIN_EMAIL"], analytics_page=True)

    @app.get("/admin/analytics/events/")
    @admin_required
    def admin_analytics_events():
        start, end, range_name = analytics.date_range_from_args(request.args)
        filters = analytics.filters_from_args(request.args)
        result = analytics.analytics_store(app.config).query_events(start, end, filters, page=request.args.get("page", 1), page_size=50)
        return render_template(
            "admin/analytics_events.html",
            result=result,
            filters=filters,
            range_name=range_name,
            start=start.date().isoformat(),
            end=(end - timedelta(days=1)).date().isoformat(),
            storage=analytics.storage_health(app.config),
            temporary_storage=analytics.temporary_storage_active(app.config),
        )

    @app.get("/admin/analytics/export.csv")
    @admin_required
    def admin_analytics_export():
        start, end, _range_name = analytics.date_range_from_args(request.args)
        filters = analytics.filters_from_args(request.args)
        body = analytics.analytics_store(app.config).export_events(start, end, filters)
        filename = f"mindful-diabetes-analytics-{start.date()}-to-{(end - timedelta(days=1)).date()}.csv"
        return body, {
            "Content-Type": "text/csv; charset=utf-8",
            "Content-Disposition": f"attachment; filename={filename}",
        }

    @app.get("/admin/analytics/export/<kind>.csv")
    @admin_required
    def admin_analytics_named_export(kind):
        dashboard = build_admin_dashboard(app.config, request.args)
        body = dashboard_csv_export(kind, dashboard)
        filename = f"mindful-diabetes-{clean_campaign_value(kind)}-{dashboard['start']}-to-{dashboard['end']}.csv"
        return body, {
            "Content-Type": "text/csv; charset=utf-8",
            "Content-Disposition": f"attachment; filename={filename}",
        }

    @app.get("/admin/analytics/report/")
    @admin_required
    def admin_analytics_report():
        dashboard = build_admin_dashboard(app.config, request.args)
        return render_template("admin/analytics_report.html", dashboard=dashboard, admin_email=app.config["ADMIN_EMAIL"])

    @app.get("/admin/analytics/board/")
    @admin_required
    def admin_analytics_board_report():
        dashboard = build_admin_dashboard(app.config, request.args)
        return render_template("admin/analytics_board.html", dashboard=dashboard, admin_email=app.config["ADMIN_EMAIL"])

    @app.get("/admin/analytics/guides/<guide_slug>/")
    @admin_required
    def admin_analytics_guide_report(guide_slug):
        guide = free_guide_definition_by_slug(guide_slug)
        if not guide:
            abort(404)
        args = request.args.copy()
        start, end, range_name = analytics.date_range_from_args(args)
        filters = analytics.filters_from_args(args)
        filters["guide_slug"] = guide_slug
        filters["environment"] = analytics.analytics_environment(app.config)
        summary = analytics.analytics_store(app.config).query_summary(start, end, filters)
        report = dashboard_guide_report(guide, summary)
        return render_template(
            "admin/analytics_guide.html",
            guide=guide,
            report=report,
            summary=summary,
            range_name=range_name,
            start=start.date().isoformat(),
            end=(end - timedelta(days=1)).date().isoformat(),
        )

    @app.get("/admin/analytics/page/")
    @admin_required
    def admin_analytics_page_report():
        page_path = request.args.get("page_path", "/")
        args = request.args.copy()
        args = args.copy()
        start, end, range_name = analytics.date_range_from_args(args)
        summary = analytics.analytics_store(app.config).query_summary(start, end, {"page_path": page_path, "environment": analytics.analytics_environment(app.config)})
        events = analytics.analytics_store(app.config).query_events(start, end, {"page_path": page_path, "environment": analytics.analytics_environment(app.config)}, page=1, page_size=25)
        return render_template(
            "admin/analytics_page.html",
            page_path=page_path,
            summary=summary,
            events=events,
            recommendations=page_analytics_recommendations(summary),
            range_name=range_name,
            start=start.date().isoformat(),
            end=(end - timedelta(days=1)).date().isoformat(),
        )

    @app.post("/paypal/webhook/")
    def paypal_webhook():
        raw_body = request.get_data(cache=True)
        try:
            webhook_event = json.loads(raw_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return jsonify({"ok": False, "message": "Webhook payload was not valid JSON."}), 400
        if not paypal_webhook_configured(app.config):
            return jsonify({"ok": False, "message": "PayPal webhook is not configured."}), 503
        if not verify_paypal_webhook(app.config, webhook_event, request.headers):
            return jsonify({"ok": False, "message": "PayPal webhook could not be verified."}), 400
        event = paypal_analytics_event(webhook_event, app.config)
        if not event:
            return jsonify({"ok": True, "stored": 0, "ignored": True}), 202
        try:
            inserted = analytics.analytics_store(app.config).store_event(event)
        except Exception:
            return jsonify({"ok": False, "message": "PayPal webhook could not be stored."}), 202
        return jsonify({"ok": True, "stored": 1 if inserted else 0, "duplicates": 0 if inserted else 1}), 202

    @app.post("/analytics/events")
    def collect_analytics_events():
        if not analytics.analytics_enabled(app.config):
            return jsonify({"ok": True, "stored": 0, "disabled": True}), 202
        if not same_origin_request(request):
            return jsonify({"ok": False, "message": "Analytics request was not accepted."}), 403
        try:
            events = analytics.parse_event_request(request, app.config)
            for event in events:
                analytics.enrich_event_with_request(event, request, content)
                event["environment"] = analytics.analytics_environment(app.config)
            result = analytics.analytics_store(app.config).store_events(events)
        except analytics.AnalyticsValidationError as error:
            return jsonify({"ok": False, "message": str(error)}), 400
        except Exception:
            return jsonify({"ok": False, "message": "Analytics event could not be recorded."}), 202
        return jsonify({"ok": True, "stored": result["inserted"], "duplicates": result["duplicates"]}), 202

    @app.get("/admin/content/")
    @admin_required
    def admin_content_index():
        items = cms.list_content(app.config)
        query = request.args.get("q", "").strip().lower()
        content_type = request.args.get("type", "").strip()
        status = request.args.get("status", "").strip()
        if query:
            items = [
                item
                for item in items
                if query in item["title"].lower()
                or query in item["slug"].lower()
                or query in item.get("excerpt", "").lower()
            ]
        if content_type in {"page", "post"}:
            items = [item for item in items if item["content_type"] == content_type]
        if status in {"draft", "published", "scheduled", "archived"}:
            items = [item for item in items if item["status"] == status]
        return render_template(
            "admin/content/index.html",
            items=items,
            query=request.args.get("q", ""),
            content_type=content_type,
            status=status,
            storage_backend=app.config.get("CMS_STORAGE_BACKEND", "local file"),
            storage_warning=cms.upload_storage_info(app.config),
        )

    @app.post("/admin/pages/new/")
    @admin_required
    def admin_new_page():
        validate_admin_csrf()
        item = cms.create_content(app.config, "page", author=session.get("admin_email", ""))
        return redirect(url_for("admin_content_editor", content_id=item["id"]))

    @app.post("/admin/posts/new/")
    @admin_required
    def admin_new_post():
        validate_admin_csrf()
        item = cms.create_content(app.config, "post", author=session.get("admin_email", ""))
        return redirect(url_for("admin_content_editor", content_id=item["id"]))

    @app.get("/admin/content/<content_id>/edit/")
    @admin_required
    def admin_content_editor(content_id):
        item = cms.get_content(app.config, content_id)
        if not item:
            abort(404)
        return render_template(
            "admin/content/editor.html",
            item=item,
            blocks_json=json.dumps(item["blocks_json"]),
            settings_json=json.dumps(item["settings_json"]),
            seo_json=json.dumps(item["seo_json"]),
            block_library=cms.block_library(),
            storage_warning=cms.upload_storage_info(app.config),
        )

    @app.post("/admin/content/<content_id>/save/")
    @admin_required
    def admin_content_save(content_id):
        validate_admin_csrf()
        item = cms.get_content(app.config, content_id)
        if not item:
            abort(404)
        payload = request.get_json(silent=True) or request.form.to_dict()
        try:
            merged = merge_cms_payload(item, payload)
            saved = cms.save_content(app.config, merged, actor=session.get("admin_email", ""), make_revision=True)
        except cms.CmsValidationError as error:
            return jsonify({"ok": False, "message": str(error)}), 400
        return jsonify(
            {
                "ok": True,
                "message": "Draft saved",
                "content": cms_public_payload(saved),
                "view_url": cms_view_url(saved),
            }
        )

    @app.post("/admin/content/<content_id>/publish/")
    @admin_required
    def admin_content_publish(content_id):
        validate_admin_csrf()
        item = cms.get_content(app.config, content_id)
        if not item:
            abort(404)
        payload = request.get_json(silent=True) or request.form.to_dict()
        try:
            merged = merge_cms_payload(item, payload)
            merged["status"] = "published"
            saved = cms.save_content(app.config, merged, actor=session.get("admin_email", ""), make_revision=True)
        except cms.CmsValidationError as error:
            return jsonify({"ok": False, "message": str(error)}), 400
        return jsonify(
            {
                "ok": True,
                "message": "Published",
                "content": cms_public_payload(saved),
                "view_url": cms_view_url(saved),
            }
        )

    @app.get("/admin/content/<content_id>/preview/")
    @admin_required
    def admin_content_preview(content_id):
        item = cms.get_content(app.config, content_id)
        if not item:
            abort(404)
        return render_cms_content(item, preview=True)

    @app.get("/admin/content/<content_id>/revisions/")
    @admin_required
    def admin_content_revisions(content_id):
        item = cms.get_content(app.config, content_id)
        if not item:
            abort(404)
        return render_template("admin/content/revisions.html", item=item, revisions=cms.list_revisions(app.config, content_id))

    @app.post("/admin/content/<content_id>/duplicate/")
    @admin_required
    def admin_content_duplicate(content_id):
        validate_admin_csrf()
        item = cms.duplicate_content(app.config, content_id, actor=session.get("admin_email", ""))
        if not item:
            abort(404)
        return redirect(url_for("admin_content_editor", content_id=item["id"]))

    @app.post("/admin/content/<content_id>/archive/")
    @admin_required
    def admin_content_archive(content_id):
        validate_admin_csrf()
        item = cms.archive_content(app.config, content_id, actor=session.get("admin_email", ""))
        if not item:
            abort(404)
        return redirect(url_for("admin_content_index"))

    @app.post("/admin/assets/upload/")
    @admin_required
    def admin_asset_upload():
        validate_admin_csrf()
        try:
            asset = cms.save_uploaded_image(app.config, request.files.get("image"))
        except cms.CmsValidationError as error:
            return jsonify({"ok": False, "message": str(error)}), 400
        return jsonify({"ok": True, "asset": asset})

    @app.get("/random-article/")
    def random_article():
        exclude_slug = request.args.get("exclude", "").strip("/")
        choices = [post for post in content.latest_posts if post["slug"] != exclude_slug]
        if not choices:
            abort(404)
        post = random.choice(choices)
        return redirect(post["canonical_path"], code=302)

    @app.get("/sitemap.xml")
    def sitemap():
        extra_pages = [
            health_tools_search_item(content),
            research_search_item(),
            volunteer_search_item(),
            resources_search_item(),
            *resource_search_items(),
            free_guides_search_item(),
            *free_guide_search_items(),
        ]
        return render_template("sitemap.xml", pages=content.published_pages + extra_pages, posts=content.latest_posts), {
            "Content-Type": "application/xml"
        }

    @app.get("/<slug>/")
    def page_detail(slug):
        if slug == "mindful":
            return redirect(url_for("home"), code=301)

        page = content.pages_by_slug.get(slug)
        if page:
            if page["slug"] == "sponsors":
                return render_template("sponsors.html", page=page)
            return render_template("page.html", page=page, latest_posts=[])

        post = content.posts_by_slug.get(slug)
        if post:
            free_guide_cards = build_free_guide_cards(content)
            companion_guide = companion_guide_for_post(slug, free_guide_cards)
            companion_landing = companion_landing_for_post(slug)
            related_guides = companion_related_guides(companion_landing, free_guide_cards)
            related_posts = [item for item in content.latest_posts if item["slug"] != slug][:3]
            article_navigation = navigation_for_post(content.latest_posts, slug)
            return render_template(
                "post.html",
                post=post,
                companion_guide=companion_guide,
                companion_landing=companion_landing,
                companion_related_guides=related_guides,
                related_posts=related_posts,
                article_navigation=article_navigation,
                post_schema=post_article_schema(post),
            )

        cms_item = cms.get_published_content_by_slug(app.config, slug)
        if cms_item:
            return render_cms_content(cms_item)

        abort(404)

    @app.get("/<slug>")
    def page_detail_no_slash(slug):
        return redirect(url_for("page_detail", slug=slug), code=301)

    return app


class ContentIndex:
    def __init__(self, items):
        nav_order = {"mindful": 0, "guide": 1, "sponsors": 2, "donation": 3}
        free_guides_nav_page = {"slug": "free-guides", "title": "Free Guides", "canonical_path": "/free-guides/"}
        health_tools_nav_page = {"slug": "health-tools", "title": "Health Tools", "canonical_path": "/health-tools/"}
        research_nav_page = {"slug": "research", "title": "Research", "canonical_path": "/research/"}
        self.items = items
        self.published_pages = sorted(
            [item for item in items if item["type"] == "page" and item["status"] == "publish"],
            key=lambda item: (int(item.get("menu_order") or 0), item["title"].lower()),
        )
        self.latest_posts = sorted(
            [item for item in items if item["type"] == "post" and item["status"] == "publish"],
            key=lambda item: item.get("date") or "",
            reverse=True,
        )
        self.pages_by_slug = {item["slug"]: item for item in self.published_pages}
        self.posts_by_slug = {item["slug"]: item for item in self.latest_posts}
        self.nav_pages = sorted(
            [
                item
                for item in self.published_pages
                if item["slug"] in nav_order
            ],
            key=lambda item: nav_order[item["slug"]],
        )
        self.nav_pages.insert(2, free_guides_nav_page)
        self.nav_pages.insert(3, health_tools_nav_page)
        self.nav_pages.insert(4, research_nav_page)


def load_content(path):
    with path.open(encoding="utf-8") as handle:
        items = json.load(handle)

    for item in items:
        item["canonical_path"] = canonical_path_for(item)
        content_text = searchable_content_text(item.get("content_html", ""))
        item["excerpt_text"] = preview_text_for(item)
        preview_image = first_content_image(item.get("content_html", ""))
        item["preview_image_url"] = preview_image["src"] if preview_image else ""
        item["preview_image_alt"] = preview_image["alt"] if preview_image else item.get("title", "")
        item["preview_image_title"] = preview_image["title"] if preview_image else item.get("title", "")
        item["preview_image_description"] = preview_image["description"] if preview_image else ""
        item["article_section_title"] = article_section_title_for(
            item.get("content_html", ""),
            item.get("title", ""),
        )
        item["search_text"] = " ".join(
            [item.get("title", ""), item.get("slug", ""), item.get("excerpt_text", ""), content_text]
        ).lower()

    return ContentIndex(items)


def navigation_for_post(latest_posts, slug):
    slugs = [item["slug"] for item in latest_posts]
    if slug not in slugs:
        return {"previous": None, "next": None}

    index = slugs.index(slug)
    return {
        "previous": latest_posts[index + 1] if index + 1 < len(latest_posts) else None,
        "next": latest_posts[index - 1] if index > 0 else None,
    }


def youtube_url_to_embed(raw_url):
    parsed = urlparse(raw_url.rstrip(".,);"))
    video_id = ""

    if parsed.netloc in {"youtu.be", "www.youtu.be"}:
        video_id = parsed.path.strip("/").split("/")[0]
    elif parsed.netloc in {"youtube.com", "www.youtube.com"} and parsed.path == "/watch":
        video_id = parse_qs(parsed.query).get("v", [""])[0]

    if not re.fullmatch(r"[\w-]{6,}", video_id or ""):
        return ""
    return f"https://www.youtube.com/embed/{video_id}"


def article_section_title_for(raw_html, post_title=""):
    for match in re.finditer(r"<h[1-4]\b[^>]*>(.*?)</h[1-4]>", raw_html or "", re.IGNORECASE | re.DOTALL):
        heading = html_to_text(match.group(1))
        if re.search(r"\b(?:want|prefer)\b.*\blisten\b", heading, re.IGNORECASE):
            continue
        if headings_match(heading, post_title):
            return ""
        return heading
    return ""


def search_content(content, query, extra_items=None):
    terms = [term.lower() for term in re.findall(r"[A-Za-z0-9']+", query)]
    if not terms:
        return []

    phrase = query.lower()
    matches = []
    for item in content.published_pages + content.latest_posts + (extra_items or []):
        haystack = item.get("search_text", "")
        title = item.get("title", "").lower()
        if not all(term in haystack for term in terms):
            continue

        score = sum(4 for term in terms if term in title) + sum(1 for term in terms if term in haystack)
        if phrase and phrase in title:
            score += 8
        elif phrase and phrase in haystack:
            score += 3

        matches.append((score, item))

    return [item for score, item in sorted(matches, key=lambda match: (-match[0], match[1]["title"].lower()))]


def health_tools_search_item(content):
    tool_slugs = [
        "diabetes-health-jeir-updates",
        "memovela",
        "healthy-eating",
        "diabetes-artificial-intelligence-jeir",
    ]
    post_text = " ".join(
        content.posts_by_slug[slug]["search_text"]
        for slug in tool_slugs
        if slug in content.posts_by_slug
    )
    search_text = " ".join(
        [
            "health tools wellness tools JEIR AI health education Memovela wellness tracker mindful eating game",
            "blood sugar insulin resistance brain health metabolic health daily habits nutrition",
            post_text,
        ]
    )
    return {
        "type": "page",
        "title": "Health Tools",
        "canonical_path": "/health-tools/",
        "date": "",
        "excerpt_text": "Explore Mindful Diabetes tools for AI-guided health education, daily habit tracking, and playful nutrition learning.",
        "search_text": search_text.lower(),
    }


def research_search_item():
    search_text = " ".join(
        ["research publications joseph schulz orcid mindful diabetes"]
        + [
            " ".join(
                [
                    publication["title"],
                    publication["venue"],
                    publication["type"],
                    publication["excerpt"],
                    " ".join(publication["tags"]),
                ]
            )
            for publication in RESEARCH_PUBLICATIONS
        ]
    )
    return {
        "type": "page",
        "title": "Research",
        "canonical_path": "/research/",
        "date": "",
        "excerpt_text": "Peer-reviewed publications and research work from Joseph Schulz, organized around diabetes, brain health, biotechnology, and health technology.",
        "search_text": search_text.lower(),
    }


def volunteer_search_item():
    search_text = " ".join(
        [
            "volunteer volunteering get involved mindful diabetes nonprofit support",
            "writing editing research summaries social media community outreach",
            "tool testing feedback design media fundraising events partnerships",
            "JEIR Memovela Mindful Eating Game prevention education brain health diabetes",
        ]
    )
    return {
        "type": "page",
        "title": "Volunteer",
        "canonical_path": "/volunteer/",
        "date": "",
        "excerpt_text": "Explore volunteer opportunities with Mindful Diabetes, from writing and research summaries to outreach, tool testing, media, fundraising, and partnerships.",
        "search_text": search_text.lower(),
    }


def build_free_guide_cards(content):
    guides_by_slug = {definition["slug"]: definition for definition in FREE_GUIDE_DEFINITIONS}
    return [build_free_guide_card(definition, content, guides_by_slug) for definition in FREE_GUIDE_DEFINITIONS]


def companion_guide_for_post(post_slug, guides):
    guide_slug = COMPANION_GUIDE_POSTS.get(post_slug)
    if not guide_slug:
        return None
    return next((guide for guide in guides if guide["slug"] == guide_slug), None)


def companion_landing_for_post(post_slug):
    if post_slug == "fats-guide":
        return FATS_GUIDE_LANDING
    return None


def companion_related_guides(landing, guides):
    if not landing:
        return []
    related_slugs = landing.get("related_guide_slugs", [])
    return [guide for guide in guides if guide["slug"] in related_slugs]


def paypal_webhook_configured(config):
    return all(
        (
            config.get("PAYPAL_CLIENT_ID"),
            config.get("PAYPAL_CLIENT_SECRET"),
            config.get("PAYPAL_WEBHOOK_ID"),
        )
    )


def paypal_api_base(config):
    if str(config.get("PAYPAL_ENVIRONMENT") or "live").lower() == "sandbox":
        return "https://api-m.sandbox.paypal.com"
    return "https://api-m.paypal.com"


def paypal_access_token(config):
    credentials = f"{config.get('PAYPAL_CLIENT_ID')}:{config.get('PAYPAL_CLIENT_SECRET')}".encode("utf-8")
    auth = base64.b64encode(credentials).decode("ascii")
    request_obj = Request(
        f"{paypal_api_base(config)}/v1/oauth2/token",
        data=urlencode({"grant_type": "client_credentials"}).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Basic {auth}",
            "Accept": "application/json",
            "Accept-Language": "en_US",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    with urlopen(request_obj, timeout=10) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload.get("access_token") or ""


def verify_paypal_webhook(config, webhook_event, headers):
    required_headers = {
        "auth_algo": headers.get("PAYPAL-AUTH-ALGO", ""),
        "cert_url": headers.get("PAYPAL-CERT-URL", ""),
        "transmission_id": headers.get("PAYPAL-TRANSMISSION-ID", ""),
        "transmission_sig": headers.get("PAYPAL-TRANSMISSION-SIG", ""),
        "transmission_time": headers.get("PAYPAL-TRANSMISSION-TIME", ""),
    }
    if not all(required_headers.values()):
        return False
    token = paypal_access_token(config)
    if not token:
        return False
    verify_payload = {
        **required_headers,
        "webhook_id": config.get("PAYPAL_WEBHOOK_ID"),
        "webhook_event": webhook_event,
    }
    request_obj = Request(
        f"{paypal_api_base(config)}/v1/notifications/verify-webhook-signature",
        data=json.dumps(verify_payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    )
    try:
        with urlopen(request_obj, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return False
    return payload.get("verification_status") == "SUCCESS"


def paypal_analytics_event(webhook_event, config):
    event_type = str(webhook_event.get("event_type") or "").upper()
    event_name = paypal_event_name(event_type)
    if not event_name:
        return None
    resource = webhook_event.get("resource") if isinstance(webhook_event.get("resource"), dict) else {}
    amount_value, currency_code = paypal_amount(resource)
    resource_id = str(resource.get("id") or resource.get("sale_id") or resource.get("capture_id") or "")
    paypal_event_id = str(webhook_event.get("id") or "")
    stable_id = hashlib.sha256(f"{paypal_event_id}:{resource_id}:{event_type}".encode("utf-8")).hexdigest()[:32]
    metadata = {
        "provider": "paypal",
        "completion_source": "paypal_webhook",
        "paypal_event_id": paypal_event_id,
        "paypal_resource_id": resource_id,
        "paypal_event_type": event_type,
        "paypal_status": str(resource.get("status") or ""),
        "donation_status": paypal_donation_status(event_name),
        "amount_value": amount_value,
        "currency_code": currency_code,
    }
    payload = {
        "event_id": f"paypal:{stable_id}",
        "event_name": event_name,
        "page_path": "/donation/",
        "page_title": "PayPal donation",
        "content_id": "paypal-donation",
        "content_type": "static",
        "article_group": "nonprofit updates",
        "element_id": "paypal-webhook",
        "element_label": "PayPal webhook",
        "element_type": "webhook",
        "element_position": "server",
        "destination_domain": "paypal.com",
        "source": "paypal",
        "medium": "webhook",
        "campaign": str(resource.get("custom_id") or resource.get("invoice_id") or ""),
        "environment": analytics.analytics_environment(config),
        "metadata": metadata,
    }
    return analytics.normalize_event_payload(payload, config)


def paypal_event_name(event_type):
    if event_type in {"PAYMENT.CAPTURE.COMPLETED", "PAYMENT.SALE.COMPLETED"}:
        return "donation_completed"
    if event_type in {"PAYMENT.CAPTURE.REFUNDED", "PAYMENT.SALE.REFUNDED"}:
        return "donation_refunded"
    if event_type in {"PAYMENT.CAPTURE.DENIED", "PAYMENT.CAPTURE.DECLINED", "PAYMENT.SALE.DENIED"}:
        return "donation_denied"
    if event_type in {"CHECKOUT.ORDER.APPROVED"}:
        return "donation_checkout_started"
    return ""


def paypal_donation_status(event_name):
    return {
        "donation_completed": "completed",
        "donation_refunded": "refunded",
        "donation_denied": "denied",
        "donation_checkout_started": "checkout_started",
    }.get(event_name, "")


def paypal_amount(resource):
    amount = resource.get("amount") if isinstance(resource.get("amount"), dict) else {}
    seller_receivable = resource.get("seller_receivable_breakdown") if isinstance(resource.get("seller_receivable_breakdown"), dict) else {}
    gross_amount = seller_receivable.get("gross_amount") if isinstance(seller_receivable.get("gross_amount"), dict) else {}
    value = amount.get("value") or amount.get("total") or gross_amount.get("value") or ""
    currency = amount.get("currency_code") or amount.get("currency") or gross_amount.get("currency_code") or ""
    return str(value)[:32], str(currency).upper()[:8]


def build_free_guide_card(definition, content, guides_by_slug):
    pdf_static_path = f"free-guides/pdfs/{definition['pdf_filename']}"
    cover_static_path = f"free-guides/images/{definition['cover_filename']}"
    thumb_static_path = f"free-guides/images/{definition['thumb_filename']}"
    banner_static_path = f"free-guides/images/{definition['banner_filename']}"
    square_static_path = f"free-guides/images/{definition['square_filename']}"
    detail_path = f"/free-guides/{definition['slug']}/"
    canonical_url = f"{PUBLIC_SITE_URL}/free-guides/{definition['slug']}"
    share_text = f"{definition['title']} from Mindful Diabetes"
    related_links = [resolved_related_link(item, content) for item in definition.get("related_links", [])]
    related_links = [item for item in related_links if item]
    related_guides = [
        {
            "title": guides_by_slug[slug]["title"],
            "url": f"/free-guides/{slug}/",
        }
        for slug in definition.get("related_guide_slugs", [])
        if slug in guides_by_slug
    ]
    return {
        **definition,
        "publication_date": "2026",
        "review_status": "Medical review pending",
        "file_type": "PDF",
        "file_size": file_size_label(FREE_GUIDES_PDF_STATIC_DIR / definition["pdf_filename"]),
        "pdf_url": url_for("static", filename=pdf_static_path),
        "cover_url": url_for("static", filename=cover_static_path),
        "thumb_url": url_for("static", filename=thumb_static_path),
        "banner_url": url_for("static", filename=banner_static_path),
        "square_url": url_for("static", filename=square_static_path),
        "detail_url": detail_path,
        "canonical_url": canonical_url,
        "related_links": related_links,
        "related_guides": related_guides,
        "share_links": [
            {"platform": "email", "label": "Email", "url": f"mailto:?subject={quote(share_text)}&body={quote(canonical_url)}"},
            {"platform": "facebook", "label": "Facebook", "url": f"https://www.facebook.com/sharer/sharer.php?u={quote(canonical_url, safe='')}"},
            {"platform": "linkedin", "label": "LinkedIn", "url": f"https://www.linkedin.com/sharing/share-offsite/?url={quote(canonical_url, safe='')}"},
            {"platform": "whatsapp", "label": "WhatsApp", "url": f"https://wa.me/?text={quote(share_text + ' ' + canonical_url)}"},
        ],
    }


def resolved_related_link(link, content):
    if link.get("url"):
        return {"label": link["label"], "url": link["url"], "external": link["url"].startswith("http")}
    endpoint = link.get("endpoint")
    if endpoint == "guide":
        return {"label": link["label"], "url": url_for("guide"), "external": False}
    if endpoint == "health_tools":
        return {"label": link["label"], "url": url_for("health_tools"), "external": False}
    if endpoint == "research":
        return {"label": link["label"], "url": url_for("research"), "external": False}
    slug = link.get("slug")
    if slug and (slug in content.pages_by_slug or slug in content.posts_by_slug):
        return {"label": link["label"], "url": url_for("page_detail", slug=slug), "external": False}
    return None


def file_size_label(path):
    if not path.exists():
        return ""
    size = path.stat().st_size
    if size >= 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    return f"{round(size / 1024)} KB"


def free_guides_search_item():
    search_text = " ".join(
        [
            "free health guides mindful diabetes free PDFs resources worksheets download nutrition blood sugar fats grocery prevention brain health",
            *[
                " ".join([guide["title"], guide["subtitle"], guide["description"], guide["who"], " ".join(guide["tags"])])
                for guide in FREE_GUIDE_DEFINITIONS
            ],
        ]
    )
    return {
        "type": "page",
        "title": "Free Health Guides",
        "canonical_path": "/free-guides/",
        "date": "",
        "modified": "2026-07-30",
        "excerpt_text": "Download free Mindful Diabetes PDF guides with plain-English explanations, visual tools, and printable worksheets.",
        "search_text": search_text.lower(),
    }


def free_guide_search_items():
    return [
        {
            "type": "page",
            "title": guide["title"],
            "canonical_path": f"/free-guides/{guide['slug']}/",
            "date": "",
            "modified": "2026-07-30",
            "excerpt_text": guide["description"],
            "search_text": " ".join(
                [guide["title"], guide["subtitle"], guide["description"], guide["who"], " ".join(guide["tags"]), " ".join(guide["topics"])]
            ).lower(),
        }
        for guide in FREE_GUIDE_DEFINITIONS
    ]


def resources_search_item():
    resources = resource_library.all_resources()
    search_text = " ".join(
        [
            "resources mindful diabetes educational guides blood sugar metabolic health brain health daily habits doctor questions JEIR",
            *[
                " ".join(
                    [
                        resource["title"],
                        resource["category"],
                        resource["summary"],
                        resource["big_idea"],
                        resource["best_lens"],
                        " ".join(resource["learning_points"]),
                    ]
                )
                for resource in resources
            ],
        ]
    )
    return {
        "type": "page",
        "title": "Educational Resources",
        "canonical_path": "/resources",
        "date": "",
        "modified": "2026-08-04",
        "excerpt_text": "Explore Mindful Diabetes Inc. educational resources on blood sugar, metabolic health, brain health, daily habits, and questions for qualified healthcare professionals.",
        "search_text": search_text.lower(),
    }


def url_with_attribution(destination_url):
    preserved_keys = {
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "utm_content",
        "utm_term",
        "gclid",
    }
    pairs = [
        (key, value)
        for key, value in request.args.items()
        if key in preserved_keys and value
    ]
    if not pairs:
        return destination_url

    separator = "&" if "?" in destination_url else "?"
    return f"{destination_url}{separator}{urlencode(pairs)}"


def resource_search_items():
    return [
        {
            "type": "page",
            "title": resource["title"],
            "canonical_path": resource["canonical_path"],
            "date": "2026-07-31",
            "modified": "2026-07-31",
            "excerpt_text": resource["meta_description"],
            "search_text": " ".join(
                [
                    resource["title"],
                    resource["category"],
                    resource["summary"],
                    resource["big_idea"],
                    resource["best_lens"],
                    " ".join(resource["learning_points"]),
                    " ".join(title for title, _body in resource["sections"]),
                ]
            ).lower(),
        }
        for resource in resource_library.all_resources()
    ]


def resource_article_schema(resource, canonical_url):
    return {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": resource["title"],
        "description": resource["meta_description"],
        "datePublished": "2026-07-31",
        "dateModified": "2026-07-31",
        "author": {
            "@type": "Organization",
            "name": "Mindful Diabetes Editorial Team",
        },
        "publisher": organization_schema(),
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": canonical_url,
        },
        "url": canonical_url,
        "articleSection": resource["category"],
        "isAccessibleForFree": True,
    }


def post_article_schema(post):
    canonical_url = post.get("canonical_url") or f"{PUBLIC_SITE_URL}{post.get('canonical_path', '')}"
    image = post.get("og_image") or post.get("hero_image") or post.get("preview_image_url")
    if image and image.startswith("/"):
        image = f"{PUBLIC_SITE_URL}{image}"
    schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": post.get("title", ""),
        "description": post.get("meta_description") or post.get("excerpt_text", ""),
        "datePublished": (post.get("date") or "")[:10],
        "dateModified": (post.get("modified") or post.get("date") or "")[:10],
        "author": {"@type": "Organization", "name": "Mindful Diabetes Inc."},
        "publisher": organization_schema(),
        "mainEntityOfPage": {"@type": "WebPage", "@id": canonical_url},
        "url": canonical_url,
        "articleSection": (post.get("categories") or ["Pathways to Wellness"])[0],
        "isAccessibleForFree": True,
    }
    if image:
        schema["image"] = image
    return schema


def resource_breadcrumb_schema(resource, canonical_url):
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": 1,
                "name": "Resources",
                "item": f"{PUBLIC_SITE_URL}/resources",
            },
            {
                "@type": "ListItem",
                "position": 2,
                "name": resource["category"],
                "item": f"{PUBLIC_SITE_URL}/resources#{resource['category_slug']}",
            },
            {
                "@type": "ListItem",
                "position": 3,
                "name": resource["title"],
                "item": canonical_url,
            },
        ],
    }


def organization_schema():
    return {
        "@type": "Organization",
        "name": "Mindful Diabetes Inc.",
        "url": PUBLIC_SITE_URL,
        "logo": f"{PUBLIC_SITE_URL}/static/img/mdi-logo.jpg",
    }


def is_valid_email(email):
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email or ""))


def is_mailchimp_configured(config):
    return bool(config.get("MAILCHIMP_API_KEY") and config.get("MAILCHIMP_AUDIENCE_ID"))


def is_turnstile_configured(config):
    return bool(config.get("TURNSTILE_SITE_KEY") and config.get("TURNSTILE_SECRET_KEY"))


def utc_now():
    return datetime.now(timezone.utc)


def normalize_email(email):
    return (email or "").strip().lower()


def generate_admin_code():
    return "".join(secrets.choice("0123456789") for _ in range(6))


def hash_admin_code(config, email, code):
    secret = config.get("SECRET_KEY") or "dev-only-change-me"
    value = f"{secret}:{normalize_email(email)}:{code.strip()}".encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def get_database_url(config):
    database_url = (config.get("DATABASE_URL") or "").strip()
    if database_url.startswith("postgres://"):
        return f"postgresql://{database_url[len('postgres://'):]}"
    return database_url


def database_configured(config):
    return bool(get_database_url(config) and psycopg)


def connect_admin_database(config):
    connection = psycopg.connect(get_database_url(config), row_factory=dict_row)
    connection.autocommit = True
    return connection


def ensure_admin_storage(config):
    if database_configured(config):
        try:
            with connect_admin_database(config) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        CREATE TABLE IF NOT EXISTS admin_login_codes (
                            email TEXT PRIMARY KEY,
                            code_hash TEXT NOT NULL,
                            expires_at TIMESTAMPTZ NOT NULL,
                            attempts INTEGER NOT NULL DEFAULT 0,
                            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                        )
                        """
                    )
                    cursor.execute(
                        """
                        CREATE TABLE IF NOT EXISTS admin_activity_events (
                            id BIGSERIAL PRIMARY KEY,
                            event_type TEXT NOT NULL,
                            path TEXT NOT NULL,
                            title TEXT NOT NULL DEFAULT '',
                            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
                            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                        )
                        """
                    )
                    cursor.execute(
                        """
                        CREATE INDEX IF NOT EXISTS admin_activity_events_created_at_idx
                        ON admin_activity_events (created_at DESC)
                        """
                    )
                    cursor.execute(
                        """
                        CREATE INDEX IF NOT EXISTS admin_activity_events_event_type_idx
                        ON admin_activity_events (event_type)
                        """
                    )
            config["ADMIN_STORAGE_BACKEND"] = "Postgres"
            return
        except Exception:
            config["ADMIN_STORAGE_BACKEND"] = "local file"
            return

    config["ADMIN_STORAGE_BACKEND"] = "local file"


def admin_data_path(config):
    return Path(config.get("ADMIN_DATA_PATH") or BASE_DIR / "instance" / "admin_data.json")


def read_admin_file_data(config):
    path = admin_data_path(config)
    if not path.exists():
        return {"login_codes": {}, "activity_events": []}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"login_codes": {}, "activity_events": []}

    data.setdefault("login_codes", {})
    data.setdefault("activity_events", [])
    return data


def write_admin_file_data(config, data):
    path = admin_data_path(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def save_admin_login_code(config, email, code):
    code_hash = hash_admin_code(config, email, code)
    expires_at = utc_now() + timedelta(minutes=ADMIN_CODE_TTL_MINUTES)

    if database_configured(config):
        try:
            ensure_admin_storage(config)
            with connect_admin_database(config) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO admin_login_codes (email, code_hash, expires_at, attempts, created_at)
                        VALUES (%s, %s, %s, 0, NOW())
                        ON CONFLICT (email)
                        DO UPDATE SET code_hash = EXCLUDED.code_hash,
                                      expires_at = EXCLUDED.expires_at,
                                      attempts = 0,
                                      created_at = NOW()
                        """,
                        (normalize_email(email), code_hash, expires_at),
                    )
                    return
        except Exception:
            pass

    data = read_admin_file_data(config)
    data["login_codes"][normalize_email(email)] = {
        "code_hash": code_hash,
        "expires_at": expires_at.isoformat(),
        "attempts": 0,
        "created_at": utc_now().isoformat(),
    }
    write_admin_file_data(config, data)


def verify_admin_login_code(config, email, code):
    email = normalize_email(email)
    if email != normalize_email(config.get("ADMIN_EMAIL")):
        return False, "That code did not match. Request a fresh code and try again."

    record = get_admin_login_code(config, email)
    if not record:
        return False, "Request a fresh code and try again."

    expires_at = parse_timestamp(record.get("expires_at"))
    if not expires_at or expires_at < utc_now():
        delete_admin_login_code(config, email)
        return False, "That code expired. Request a fresh code and try again."

    if int(record.get("attempts") or 0) >= 5:
        delete_admin_login_code(config, email)
        return False, "Too many attempts. Request a fresh code and try again."

    expected_hash = record.get("code_hash") or ""
    submitted_hash = hash_admin_code(config, email, code)
    if hmac.compare_digest(expected_hash, submitted_hash):
        delete_admin_login_code(config, email)
        return True, ""

    increment_admin_login_attempts(config, email)
    return False, "That code did not match. Try again or request a fresh code."


def get_admin_login_code(config, email):
    if database_configured(config):
        try:
            ensure_admin_storage(config)
            with connect_admin_database(config) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT email, code_hash, expires_at, attempts, created_at
                        FROM admin_login_codes
                        WHERE email = %s
                        """,
                        (normalize_email(email),),
                    )
                    return cursor.fetchone()
        except Exception:
            pass

    return read_admin_file_data(config)["login_codes"].get(normalize_email(email))


def delete_admin_login_code(config, email):
    if database_configured(config):
        try:
            ensure_admin_storage(config)
            with connect_admin_database(config) as connection:
                with connection.cursor() as cursor:
                    cursor.execute("DELETE FROM admin_login_codes WHERE email = %s", (normalize_email(email),))
                    return
        except Exception:
            pass

    data = read_admin_file_data(config)
    data["login_codes"].pop(normalize_email(email), None)
    write_admin_file_data(config, data)


def increment_admin_login_attempts(config, email):
    if database_configured(config):
        try:
            ensure_admin_storage(config)
            with connect_admin_database(config) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE admin_login_codes SET attempts = attempts + 1 WHERE email = %s",
                        (normalize_email(email),),
                    )
                    return
        except Exception:
            pass

    data = read_admin_file_data(config)
    record = data["login_codes"].get(normalize_email(email))
    if record:
        record["attempts"] = int(record.get("attempts") or 0) + 1
        write_admin_file_data(config, data)


def parse_email_identity(raw_value):
    value = (raw_value or "").strip()
    match = re.fullmatch(r"\s*(?P<name>.*?)\s*<(?P<email>[^>]+)>\s*", value)
    if match:
        return {"name": match.group("name").strip() or match.group("email").strip(), "email": match.group("email").strip()}
    return {"email": value}


def send_admin_login_code(config, email, code):
    return send_brevo_email(
        config,
        [email],
        "Your Mindful Diabetes admin code",
        (
            f"Your Mindful Diabetes admin code is {code}. "
            f"It expires in {ADMIN_CODE_TTL_MINUTES} minutes."
        ),
        (
            "<p>Your Mindful Diabetes admin code is:</p>"
            f"<p style=\"font-size:28px;font-weight:700;letter-spacing:4px;\">{code}</p>"
            f"<p>This code expires in {ADMIN_CODE_TTL_MINUTES} minutes.</p>"
        ),
    )


def send_brevo_email(config, recipients, subject, text_content, html_content):
    api_key = config.get("BREVO_API_KEY") or ""
    if not api_key:
        return False, "Brevo email is not configured yet. Add BREVO_API_KEY in Heroku Config Vars."

    sender = parse_email_identity(config.get("ADMIN_EMAIL_FROM"))
    payload = {
        "sender": sender,
        "to": [{"email": email} for email in recipients],
        "subject": subject,
        "textContent": text_content,
        "htmlContent": html_content,
    }
    request_obj = Request(
        config.get("BREVO_SMTP_URL") or "https://api.brevo.com/v3/smtp/email",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "api-key": api_key,
            "accept": "application/json",
            "Content-Type": "application/json",
        },
    )

    try:
        with urlopen(request_obj, timeout=12) as response:
            if 200 <= response.status < 300:
                return True, "Code sent"
    except HTTPError as error:
        try:
            body = json.loads(error.read().decode("utf-8"))
            message = body.get("message") or body.get("detail")
        except (json.JSONDecodeError, UnicodeDecodeError):
            message = None
        return False, message or "Brevo rejected the login email request."
    except URLError:
        return False, "Could not reach Brevo. Please try again."

    return False, "Brevo returned an unexpected response."


def record_activity_event(config, event_type, path, title="", metadata=None):
    metadata = metadata or {}
    created_at = utc_now()

    if database_configured(config):
        try:
            ensure_admin_storage(config)
            with connect_admin_database(config) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO admin_activity_events (event_type, path, title, metadata, created_at)
                        VALUES (%s, %s, %s, %s::jsonb, %s)
                        """,
                        (event_type, path, title or "", json.dumps(metadata), created_at),
                    )
                    return
        except Exception:
            pass

    data = read_admin_file_data(config)
    events = data["activity_events"]
    next_id = (max([int(event.get("id", 0)) for event in events], default=0) + 1) if events else 1
    events.append(
        {
            "id": next_id,
            "event_type": event_type,
            "path": path,
            "title": title or "",
            "metadata": metadata,
            "created_at": created_at.isoformat(),
        }
    )
    data["activity_events"] = events[-5000:]
    write_admin_file_data(config, data)


def fetch_admin_events(config, limit=750):
    if database_configured(config):
        try:
            ensure_admin_storage(config)
            with connect_admin_database(config) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT id, event_type, path, title, metadata, created_at
                        FROM admin_activity_events
                        ORDER BY created_at DESC
                        LIMIT %s
                        """,
                        (limit,),
                    )
                    return [normalize_event_record(row) for row in cursor.fetchall()]
        except Exception:
            pass

    events = read_admin_file_data(config)["activity_events"]
    normalized_events = [normalize_event_record(event) for event in events]
    return sorted(normalized_events, key=lambda event: event["created_at"], reverse=True)[:limit]


def normalize_event_record(event):
    created_at = parse_timestamp(event.get("created_at")) or utc_now()
    metadata = event.get("metadata") or {}
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except json.JSONDecodeError:
            metadata = {}
    return {
        "id": event.get("id"),
        "event_type": event.get("event_type") or "",
        "path": event.get("path") or "",
        "title": event.get("title") or "",
        "metadata": metadata,
        "created_at": created_at,
        "created_at_label": created_at.astimezone().strftime("%b %-d, %Y %-I:%M %p"),
    }


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


def build_admin_dashboard(config, args=None):
    args = args or {}
    start, end, range_name = analytics.date_range_from_args(args)
    filters = analytics.filters_from_args(args)
    filters.setdefault("environment", analytics.analytics_environment(config))
    store = analytics.analytics_store(config)
    try:
        summary = store.query_summary(start, end, filters)
        recent = store.query_events(start, end, filters, page=1, page_size=20)
    except Exception:
        summary = analytics.build_empty_summary()
        recent = {"events": [], "total": 0, "page": 1, "pages": 1}

    totals = summary["totals"]
    normalize_dashboard_groups(summary)
    page_views = totals.get("page_views", 0)
    missed_opportunities = dashboard_missed_opportunities(summary)
    health_scores = dashboard_health_scores(totals, page_views)
    insights = dashboard_insights(summary, missed_opportunities)
    growth_goals = dashboard_growth_goals(config, summary)
    recommended_actions = dashboard_recommended_actions(summary, missed_opportunities, health_scores)
    search_insights = dashboard_search_insights(summary)
    resource_insights = dashboard_resource_insights(summary)
    funnels = dashboard_funnels(summary)
    opportunities = dashboard_opportunities(summary, missed_opportunities, resource_insights, search_insights)
    growth_scorecards = dashboard_growth_scorecards(summary, opportunities)
    campaign_insights = dashboard_campaign_insights(summary)
    content_intelligence = dashboard_content_intelligence(summary, resource_insights)
    anomaly_alerts = dashboard_anomaly_alerts(summary)
    monthly_brief = dashboard_monthly_brief(summary, opportunities, resource_insights, campaign_insights)
    chart_blocks = dashboard_chart_blocks(summary)
    growth_experiments = dashboard_growth_experiments(summary, missed_opportunities, growth_goals, search_insights)
    weekly_brief = dashboard_weekly_brief(summary, growth_goals, growth_experiments, search_insights, resource_insights)
    stats = [
        dashboard_stat("Pages read", page_views, summary, "page_views", "Public page loads during the selected period."),
        dashboard_stat("Browser sessions", totals.get("anonymous_sessions", 0), summary, "anonymous_sessions", "Anonymous browser sessions, not identified people."),
        dashboard_stat("Support button clicks", totals.get("donation_cta_clicks", 0), summary, "donation_cta_clicks", "Donation/support buttons clicked before PayPal opens."),
        dashboard_stat("PayPal donation page opened", totals.get("paypal_clicks", 0), summary, "paypal_clicks", "PayPal opened; not a confirmed donation."),
        dashboard_stat("Confirmed donations", totals.get("confirmed_donations", 0), summary, "confirmed_donations", "Verified PayPal webhook donations only."),
        dashboard_stat("Health-tool clicks", totals.get("health_tool_clicks", 0), summary, "health_tool_clicks", "Clicks to JEIR, Memovela, and related tools."),
        dashboard_stat("Newsletter signups", totals.get("newsletter_signups", 0), summary, "newsletter_signups", "Successful accepted newsletter signups only."),
        dashboard_stat("Free guide downloads", totals.get("resource_pdf_downloads", 0), summary, "resource_pdf_downloads", "Downloads of the public PDF guides."),
    ]
    for event in recent["events"]:
        event["human_label"] = human_event_label(event)

    return {
        "storage_backend": config.get("ANALYTICS_STORAGE_BACKEND") or "local",
        "storage": analytics.storage_health(config),
        "temporary_storage": analytics.temporary_storage_active(config),
        "range_name": range_name,
        "start": start.date().isoformat(),
        "end": (end - timedelta(days=1)).date().isoformat(),
        "filters": filters,
        "summary": summary,
        "insights": insights,
        "health_scores": health_scores,
        "growth_goals": growth_goals,
        "recommended_actions": recommended_actions,
        "growth_experiments": growth_experiments,
        "search_insights": search_insights,
        "resource_insights": resource_insights,
        "funnels": funnels,
        "opportunities": opportunities,
        "growth_scorecards": growth_scorecards,
        "campaign_insights": campaign_insights,
        "content_intelligence": content_intelligence,
        "anomaly_alerts": anomaly_alerts,
        "monthly_brief": monthly_brief,
        "chart_blocks": chart_blocks,
        "guide_options": [item for item in FREE_GUIDE_DEFINITIONS],
        "weekly_brief": weekly_brief,
        "campaign_builder": dashboard_campaign_builder(config, args),
        "missed_opportunities": missed_opportunities,
        "pages_by_purpose": dashboard_pages_by_purpose(summary),
        "device_insights": dashboard_device_insights(summary),
        "benchmarks": dashboard_benchmarks(totals, page_views),
        "trend_max": dashboard_trend_max(summary.get("daily_trend", [])),
        "resource_trend_max": dashboard_resource_trend_max(summary.get("daily_trend", [])),
        "report_links": dashboard_report_links(args),
        "metric_definitions": dashboard_metric_definitions(),
        "board_update": dashboard_board_update(summary, opportunities, resource_insights, campaign_insights),
        "stats": stats,
        "recent_events": recent["events"],
        "top_paths": [{"path": item["label"], "count": item["count"]} for item in summary.get("top_pages", [])],
        "rates": {
            "donation_cta": analytics.click_rate(totals.get("donation_cta_clicks", 0), page_views),
            "paypal": analytics.click_rate(totals.get("paypal_clicks", 0), page_views),
            "health_tools": analytics.click_rate(totals.get("health_tool_clicks", 0), page_views),
            "newsletter": analytics.click_rate(totals.get("newsletter_signups", 0), page_views),
        },
        "paypal_webhook_configured": paypal_webhook_configured(config),
        "confirmed_donations_available": totals.get("confirmed_donations", 0) > 0 or paypal_webhook_configured(config),
        "confirmed_donation_amount": money_from_cents(totals.get("confirmed_donation_amount_cents", 0)),
        "refunded_donation_amount": money_from_cents(totals.get("refunded_donation_amount_cents", 0)),
    }


def dashboard_stat(label, value, summary, key, help_text):
    comparison = summary.get("comparison", {}).get(key, {})
    return {
        "label": label,
        "value": value,
        "previous": summary.get("previous", {}).get(key, 0),
        "change": comparison.get("label", "No previous activity"),
        "direction": comparison.get("direction", "flat"),
        "help": help_text,
    }


def money_from_cents(cents, currency="$"):
    cents = int(cents or 0)
    return f"{currency}{cents / 100:,.2f}"


def dashboard_funnels(summary):
    totals = summary.get("totals", {})
    return {
        "free_guides": build_funnel(
            "Free Guides funnel",
            [
                ("Guide cards seen", totals.get("resource_card_views", 0), "Trackable"),
                ("Guide detail viewed", totals.get("resource_detail_views", 0), "Trackable"),
                ("PDF opened", totals.get("resource_pdf_views", 0), "Trackable"),
                ("PDF downloaded", totals.get("resource_pdf_downloads", 0), "Trackable"),
                ("Guide shared", totals.get("resource_share_clicks", 0), "Trackable"),
            ],
            "Shows whether people move from seeing a guide to using and sharing it.",
        ),
        "donations": build_funnel(
            "Donation intent funnel",
            [
                ("Donation page viewed", totals.get("donation_page_views", 0), "Tracked when donation page view events are available"),
                ("Support button clicked", totals.get("donation_cta_clicks", 0), "Trackable"),
                ("PayPal opened", totals.get("paypal_clicks", 0), "Trackable"),
                ("Donation completed", totals.get("confirmed_donations", 0), "Unavailable unless PayPal confirmation is connected"),
            ],
            "PayPal opens are interest signals, not confirmed gifts.",
        ),
        "newsletter": build_funnel(
            "Newsletter funnel",
            [
                ("Form viewed", totals.get("newsletter_views", 0), "Trackable"),
                ("Signup started", totals.get("newsletter_interactions", 0) or totals.get("newsletter_signup_starts", 0), "Trackable"),
                ("Signup succeeded", totals.get("newsletter_signups", 0), "Trackable"),
                ("Signup error", totals.get("newsletter_signup_errors", 0), "Tracked only when provider errors are reported"),
            ],
            "Shows whether visible forms are turning readers into repeat visitors.",
        ),
        "health_tools": build_funnel(
            "Health Tools funnel",
            [
                ("Tool page viewed", totals.get("health_tool_views", 0), "Tracked when tool-view events are available"),
                ("Tool clicked", totals.get("health_tool_clicks", 0), "Trackable"),
                ("Outbound destination opened", totals.get("health_tool_clicks", 0), "Same signal for now"),
            ],
            "Shows whether readers move from information to a practical tool.",
        ),
        "search": build_funnel(
            "Search usefulness funnel",
            [
                ("Search submitted", totals.get("site_searches", 0), "Trackable"),
                ("Result clicked", totals.get("search_result_clicks", 0), "Trackable"),
                ("No-result search", sum(int(row.get("no_results") or 0) for row in summary.get("search_no_results", [])), "Trackable"),
            ],
            "A useful search helps people find content and exposes topics the site may be missing.",
        ),
    }


def build_funnel(title, raw_steps, note):
    steps = []
    first_count = int(raw_steps[0][1] or 0) if raw_steps else 0
    previous_count = None
    for label, count, availability in raw_steps:
        count = int(count or 0)
        if previous_count is None:
            conversion = None
            dropoff = 0
        else:
            conversion = analytics.numeric_rate(count, previous_count)
            dropoff = max(0, previous_count - count)
        steps.append(
            {
                "label": label,
                "count": count,
                "availability": availability,
                "conversion": analytics.percent_label(conversion) if conversion is not None else "Start",
                "overall": analytics.percent_label(analytics.numeric_rate(count, first_count)) if first_count else "No starting activity",
                "dropoff": dropoff,
                "width": max(4, round((count / max(first_count, 1)) * 100, 1)) if count else 4,
            }
        )
        previous_count = count
    return {"title": title, "steps": steps, "note": note, "finding": funnel_finding(title, steps)}


def funnel_finding(title, steps):
    if not steps or not any(step["count"] for step in steps):
        return "More activity is needed before this funnel can say anything useful."
    if "Free Guides" in title:
        seen = steps[0]["count"]
        opened = steps[2]["count"] if len(steps) > 2 else 0
        downloaded = steps[3]["count"] if len(steps) > 3 else 0
        shared = steps[4]["count"] if len(steps) > 4 else 0
        if seen and not opened:
            return "Many visitors see guide cards, but they are not opening the PDFs yet."
        if opened and not downloaded:
            return "People are opening PDFs, but download clicks are weak."
        if downloaded and not shared:
            return "Downloads are happening, but sharing is still low."
    if "Search" in title and steps[-1]["count"]:
        return "Some searches are not finding useful results, which may reveal content gaps."
    return "The funnel is collecting measurable signals for this period."


def dashboard_opportunities(summary, missed_opportunities, resource_insights, search_insights):
    opportunities = []
    for row in missed_opportunities[:4]:
        opportunities.append(
            opportunity_item(
                f"Traffic without action: {row['title']}",
                f"{row['views']} views; missing {row['missing']}",
                "This page is attracting readers but not moving them toward a useful next step.",
                row["recommendation"],
                "High" if row["views"] >= 10 else "Medium",
                confidence_label(row["views"]),
                dashboard_url("admin_analytics_page_report", page_path=row["page"]) if row.get("page") else "",
            )
        )
    guide_rows = resource_insights.get("top_guides", [])
    average_download_rate = average_rate([row.get("download_rate") for row in guide_rows])
    for row in guide_rows:
        pdf_views = int(row.get("pdf_views") or 0)
        downloads = int(row.get("downloads") or 0)
        shares = int(row.get("shares") or 0)
        rate = row.get("download_rate")
        if pdf_views >= 5 and downloads < max(1, pdf_views * 0.2):
            opportunities.append(
                opportunity_item(
                    f"Opened but not downloaded: {row['title']}",
                    f"{pdf_views} PDF opens; {downloads} downloads",
                    "Readers may be interested, but the download action is not convincing enough.",
                    "Move the download button higher and make the button text more direct.",
                    "High" if pdf_views >= 20 else "Medium",
                    confidence_label(pdf_views),
                    dashboard_url("admin_analytics_guide_report", guide_slug=row["slug"]),
                )
            )
        elif downloads >= 3 and shares == 0:
            opportunities.append(
                opportunity_item(
                    f"Downloaded but not shared: {row['title']}",
                    f"{downloads} downloads; 0 shares",
                    "The guide may be useful, but visitors are not being prompted to pass it along.",
                    "Add a short share prompt near the download confirmation and sidebar buttons.",
                    "Medium",
                    confidence_label(downloads),
                    dashboard_url("admin_analytics_guide_report", guide_slug=row["slug"]),
                )
            )
        elif rate is not None and average_download_rate is not None and rate > average_download_rate and int(row.get("card_views") or 0) < 10:
            opportunities.append(
                opportunity_item(
                    f"Promote a strong guide: {row['title']}",
                    f"{row.get('download_rate_label')} download rate",
                    "This guide converts well when people find it, but visibility is still limited.",
                    "Add this guide to relevant articles and upcoming campaign links.",
                    "Low",
                    confidence_label(pdf_views + downloads),
                    dashboard_url("admin_analytics_guide_report", guide_slug=row["slug"]),
                )
            )
    for row in search_insights.get("no_result_queries", [])[:3]:
        count = int(row.get("no_results") or row.get("count") or 0)
        if count:
            opportunities.append(
                opportunity_item(
                    f"Search gap: {row['label']}",
                    f"{count} no-result searches",
                    "People are asking the site for this topic and may not be finding a clear answer.",
                    f"Create or update content that directly answers '{row['label']}'.",
                    "High" if count >= 10 else "Medium",
                    confidence_label(count),
                    dashboard_url("admin_analytics", _anchor="search"),
                )
            )
    for campaign in summary.get("campaign_performance", [])[:5]:
        views = int(campaign.get("page_views") or 0)
        actions = int(campaign.get("actions") or 0)
        if views >= 5 and actions == 0:
            opportunities.append(
                opportunity_item(
                    f"Campaign traffic without action: {campaign['label']}",
                    f"{views} visits; 0 meaningful actions",
                    "The link is bringing people in, but the landing page is not creating useful next steps.",
                    "Review the landing page CTA and make the campaign promise match the page.",
                    "Medium",
                    confidence_label(views),
                    dashboard_url("admin_analytics", _anchor="campaigns"),
                )
            )
    if not opportunities:
        opportunities.append(
            opportunity_item(
                "Keep building the baseline",
                "No urgent missed opportunity yet",
                "The dashboard needs more visitor behavior before it can rank opportunities confidently.",
                "Review again after the next email, social post, or partner push.",
                "Low",
                "Low",
                "",
            )
        )
    priority_order = {"High": 0, "Medium": 1, "Low": 2}
    return sorted(opportunities, key=lambda item: (priority_order.get(item["priority"], 9), item["title"]))[:10]


def opportunity_item(title, metric, why, action, priority, confidence, url):
    return {"title": title, "metric": metric, "why": why, "action": action, "priority": priority, "confidence": confidence, "url": url}


def confidence_label(sample_size):
    sample_size = int(sample_size or 0)
    if sample_size >= 25:
        return "High"
    if sample_size >= 5:
        return "Medium"
    return "Low"


def average_rate(values):
    cleaned = [float(value) for value in values if value is not None]
    if not cleaned:
        return None
    return sum(cleaned) / len(cleaned)


def dashboard_growth_scorecards(summary, opportunities):
    totals = summary.get("totals", {})
    previous = summary.get("previous", {})
    page_views = int(totals.get("page_views") or 0)
    sessions = int(totals.get("anonymous_sessions") or 0)
    downloads = int(totals.get("resource_pdf_downloads") or 0)
    shares = int(totals.get("resource_share_clicks") or 0)
    donation_intent = int(totals.get("donation_cta_clicks") or 0) + int(totals.get("paypal_clicks") or 0)
    searches = int(totals.get("site_searches") or 0)
    search_clicks = int(totals.get("search_result_clicks") or 0)
    no_results = sum(int(row.get("no_results") or 0) for row in summary.get("search_no_results", []))
    return [
        growth_scorecard("Audience growth", sessions, previous.get("anonymous_sessions", 0), "Anonymous sessions in this period.", "Share the strongest page through the best current source."),
        growth_scorecard("Resource engagement", downloads + shares, int(previous.get("resource_pdf_downloads") or 0) + int(previous.get("resource_share_clicks") or 0), "Guide downloads plus shares.", "Promote the guide with the strongest conversion rate."),
        growth_scorecard("Donation intent", donation_intent, int(previous.get("donation_cta_clicks") or 0) + int(previous.get("paypal_clicks") or 0), "Support clicks and PayPal opens, not confirmed donations.", "Place one clearer support message on a high-traffic page."),
        growth_scorecard("Newsletter growth", totals.get("newsletter_signups", 0), previous.get("newsletter_signups", 0), "Successful newsletter signups.", "Add a stronger signup promise near useful article sections."),
        growth_scorecard("Search usefulness", search_clicks, previous.get("search_result_clicks", 0), f"{searches} searches; {no_results} no-result searches.", "Create content for repeated no-result searches."),
        growth_scorecard("Content opportunity", len(opportunities), 0, "Ranked opportunities found from real activity.", "Work the highest-confidence opportunity first."),
    ]


def growth_scorecard(label, current, previous, explanation, action):
    current = int(current or 0)
    previous = int(previous or 0)
    comparison = analytics.compare_counts(current, previous)
    if current >= 25:
        status = "Strong"
    elif comparison["direction"] == "up":
        status = "Improving"
    elif current > 0:
        status = "Stable"
    else:
        status = "Insufficient data"
    return {
        "label": label,
        "status": status,
        "tone": "good" if status in {"Strong", "Improving"} else "watch" if status == "Stable" else "low",
        "current": current,
        "previous": previous,
        "change": comparison["label"],
        "explanation": explanation,
        "action": action,
    }


def dashboard_campaign_insights(summary):
    rows = summary.get("campaign_performance", [])
    if not rows:
        return {
            "notes": ["Campaign insights will appear after links with UTM tracking bring visitors to the site."],
            "best_traffic": None,
            "best_action_rate": None,
            "best_downloads": None,
        }
    best_traffic = max(rows, key=lambda row: int(row.get("page_views") or 0))
    best_action_rate = max(rows, key=lambda row: float(row.get("action_rate") or 0))
    best_downloads = max(rows, key=lambda row: int(row.get("pdf_downloads") or 0))
    notes = [
        f"{best_traffic['label']} brought the most tracked visits ({best_traffic.get('page_views', 0)}).",
        f"{best_action_rate['label']} has the strongest action rate ({best_action_rate.get('action_rate_label')}).",
    ]
    if int(best_downloads.get("pdf_downloads") or 0):
        notes.append(f"{best_downloads['label']} generated the most guide downloads.")
    weak = next((row for row in rows if int(row.get("page_views") or 0) >= 5 and int(row.get("actions") or 0) == 0), None)
    if weak:
        notes.append(f"{weak['label']} has traffic but no meaningful actions yet.")
    return {"notes": notes[:4], "best_traffic": best_traffic, "best_action_rate": best_action_rate, "best_downloads": best_downloads}


def dashboard_content_intelligence(summary, resource_insights):
    rows = summary.get("top_content", [])
    guides = resource_insights.get("top_guides", [])
    best_guide = first_item(sorted(guides, key=lambda row: (int(row.get("downloads") or 0), int(row.get("pdf_views") or 0)), reverse=True))
    recommendations = []
    if best_guide:
        guide_terms = guide_recommendation_terms(best_guide.get("title", ""))
        for row in rows:
            page_text = f"{row.get('title', '')} {row.get('page', '')} {row.get('article_group', '')}".lower()
            if int(row.get("views") or 0) >= 2 and any(term in page_text for term in guide_terms):
                recommendations.append(
                    {
                        "page": row.get("page"),
                        "title": row.get("title") or row.get("page"),
                        "guide": best_guide.get("title"),
                        "reason": f"This page has related topic language and {row.get('views', 0)} views; the guide has {best_guide.get('downloads', 0)} downloads.",
                        "action": "Consider adding a visible guide callout on this page.",
                    }
                )
    return {
        "best_by_traffic": rows[:6],
        "best_by_actions": sorted(rows, key=lambda row: int(row.get("meaningful_actions") or 0), reverse=True)[:6],
        "guide_recommendations": recommendations[:5],
    }


def guide_recommendation_terms(title):
    terms = [term for term in re.split(r"[^a-z0-9]+", str(title).lower()) if len(term) >= 4]
    extras = {
        "plate": ["meal", "nutrition", "food", "eating"],
        "grocery": ["shopping", "food", "label", "pantry"],
        "fats": ["fat", "oil", "heart", "cholesterol"],
        "brain": ["brain", "cognitive", "alzheimer", "dementia"],
        "reset": ["habit", "sleep", "movement", "routine"],
    }
    for term in list(terms):
        terms.extend(extras.get(term, []))
    return sorted(set(terms))


def dashboard_anomaly_alerts(summary):
    alerts = []
    trend = summary.get("daily_trend", [])
    alerts.extend(daily_metric_alerts(trend, "page_views", "traffic"))
    alerts.extend(daily_metric_alerts(trend, "pdf_downloads", "guide downloads"))
    alerts.extend(daily_metric_alerts(trend, "paypal_clicks", "PayPal opens"))
    if summary.get("search_no_results"):
        top_gap = summary["search_no_results"][0]
        if int(top_gap.get("no_results") or 0) >= 3:
            alerts.append(
                {
                    "title": "Repeated no-result searches",
                    "detail": f"'{top_gap['label']}' produced {top_gap.get('no_results')} no-result searches.",
                    "action": "Create or improve content for this term.",
                    "tone": "watch",
                }
            )
    if not alerts:
        alerts.append({"title": "No unusual warnings", "detail": "Nothing crossed the dashboard's lightweight alert thresholds.", "action": "Keep collecting baseline activity.", "tone": "good"})
    return alerts[:6]


def daily_metric_alerts(rows, key, label):
    if len(rows) < 4:
        return []
    values = [int(row.get(key) or 0) for row in rows]
    recent = values[-1]
    baseline_values = values[:-1]
    baseline = sum(baseline_values) / max(1, len(baseline_values))
    if baseline < 3 and recent < 6:
        return []
    if recent >= baseline * 2 and recent - baseline >= 5:
        return [{"title": f"Possible {label} spike", "detail": f"The latest day was {recent}, compared with a recent average of {baseline:.1f}.", "action": "Check which source or campaign caused the lift.", "tone": "good"}]
    if baseline >= 5 and recent <= baseline * 0.35:
        return [{"title": f"Possible {label} drop", "detail": f"The latest day was {recent}, compared with a recent average of {baseline:.1f}.", "action": "Check whether a campaign ended, a link changed, or traffic source shifted.", "tone": "watch"}]
    if max(values) == 0:
        return [{"title": f"No {label} activity", "detail": f"{label.title()} stayed flat across this period.", "action": "Promote the related page or CTA in one outreach channel.", "tone": "low"}]
    return []


def dashboard_monthly_brief(summary, opportunities, resource_insights, campaign_insights):
    totals = summary.get("totals", {})
    top_page = first_item(summary.get("top_pages")) or {"label": "No page activity", "count": 0}
    top_guide = first_item(resource_insights.get("top_guides", [])) or {"title": "No guide activity", "downloads": 0}
    top_campaign = campaign_insights.get("best_action_rate") or {"label": "No campaign activity", "action_rate_label": "No page views"}
    opportunity = opportunities[0] if opportunities else {"title": "No urgent opportunity", "action": "Keep collecting baseline data."}
    return [
        f"This period reached {totals.get('anonymous_sessions', 0)} anonymous sessions and {totals.get('page_views', 0)} page reads.",
        f"Top page: {top_page['label']} with {top_page['count']} views.",
        f"Top guide: {top_guide['title']} with {top_guide.get('downloads', 0)} downloads.",
        f"Best campaign by action rate: {top_campaign['label']} ({top_campaign.get('action_rate_label')}).",
        f"Biggest opportunity: {opportunity['title']}. Next step: {opportunity['action']}",
    ]


def dashboard_chart_blocks(summary):
    return {
        "top_pages": ranked_chart_rows(summary.get("top_pages", []), "label", "count"),
        "top_content": ranked_chart_rows(summary.get("top_content", []), "title", "views"),
        "traffic_sources": donut_chart(summary.get("traffic_sources", [])),
        "devices": donut_chart(summary.get("device_categories", [])),
        "share_platforms": donut_chart(summary.get("resource_share_platforms", [])),
    }


def ranked_chart_rows(rows, label_key, value_key):
    cleaned = []
    max_value = max([int(row.get(value_key) or 0) for row in rows] or [1])
    for row in rows[:8]:
        value = int(row.get(value_key) or 0)
        cleaned.append({"label": row.get(label_key) or row.get("page") or row.get("label") or "Untitled", "value": value, "width": max(3, round((value / max(max_value, 1)) * 100, 1))})
    return cleaned


def donut_chart(rows):
    colors = ["#005030", "#f07239", "#4169e1", "#7b3fe4", "#008c7a", "#9b2c2c", "#8792a2"]
    total = sum(int(row.get("count") or 0) for row in rows)
    if total <= 0:
        return {"segments": [], "gradient": "conic-gradient(#e4e6ef 0 100%)"}
    cursor = 0
    gradient_parts = []
    segments = []
    for index, row in enumerate(rows[:7]):
        value = int(row.get("count") or 0)
        if not value:
            continue
        percent = (value / total) * 100
        start = cursor
        cursor += percent
        color = colors[index % len(colors)]
        gradient_parts.append(f"{color} {start:.2f}% {cursor:.2f}%")
        segments.append({"label": row.get("label") or "Unknown", "count": value, "percent": f"{percent:.1f}%", "color": color})
    return {"segments": segments, "gradient": f"conic-gradient({', '.join(gradient_parts)})"}


def dashboard_report_links(args):
    clean_args = {key: args.get(key) for key in ("range", "start", "end", "guide_slug", "campaign", "source", "medium", "device_category", "event_name") if args.get(key)}
    return {
        "print": dashboard_url("admin_analytics_report", **clean_args),
        "board": dashboard_url("admin_analytics_board_report", **clean_args),
        "daily": dashboard_url("admin_analytics_named_export", kind="daily", **clean_args),
        "guides": dashboard_url("admin_analytics_named_export", kind="guides", **clean_args),
        "content": dashboard_url("admin_analytics_named_export", kind="content", **clean_args),
        "campaigns": dashboard_url("admin_analytics_named_export", kind="campaigns", **clean_args),
        "search": dashboard_url("admin_analytics_named_export", kind="search", **clean_args),
        "opportunities": dashboard_url("admin_analytics_named_export", kind="opportunities", **clean_args),
    }


def dashboard_url(endpoint, **values):
    try:
        return url_for(endpoint, **values)
    except RuntimeError:
        anchor = values.pop("_anchor", None)
        query_values = {key: value for key, value in values.items() if value not in {None, ""}}
        path = {
            "admin_analytics": "/admin/analytics/",
            "admin_analytics_report": "/admin/analytics/report/",
            "admin_analytics_board_report": "/admin/analytics/board/",
            "admin_analytics_page_report": "/admin/analytics/page/",
            "admin_analytics_named_export": f"/admin/analytics/export/{query_values.pop('kind', 'overview')}.csv",
            "admin_analytics_guide_report": f"/admin/analytics/guides/{query_values.pop('guide_slug', '')}/",
        }.get(endpoint, "/admin/analytics/")
        query = urlencode(query_values)
        suffix = f"?{query}" if query else ""
        if anchor:
            suffix += f"#{anchor}"
        return f"{path}{suffix}"


def dashboard_metric_definitions():
    return [
        "A meaningful action is a guide download or share, newsletter signup, PayPal open, health-tool click, or search-result click.",
        "Donation clicks and PayPal opens are donation intent, not confirmed donations.",
        "Previous-period comparisons use the immediately preceding date range with the same duration.",
        "Guide download rate uses downloads divided by guide detail views plus PDF opens.",
        "Opportunity priority is lowered when the sample size is small.",
    ]


def dashboard_board_update(summary, opportunities, resource_insights, campaign_insights):
    totals = summary.get("totals", {})
    top_campaign = campaign_insights.get("best_action_rate") or {"label": "No tracked campaign yet", "action_rate_label": "No page views"}
    return [
        {"label": "Audience reached", "value": totals.get("anonymous_sessions", 0), "note": "Anonymous sessions, not identified people."},
        {"label": "Resources used", "value": resource_insights.get("pdf_views", 0), "note": "PDF opens across free guides."},
        {"label": "Guide downloads", "value": resource_insights.get("downloads", 0), "note": "Download button clicks."},
        {"label": "Newsletter growth", "value": totals.get("newsletter_signups", 0), "note": "Successful signups only."},
        {"label": "Donation intent", "value": int(totals.get("donation_cta_clicks") or 0) + int(totals.get("paypal_clicks") or 0), "note": "Support clicks and PayPal opens, not confirmed gifts."},
        {"label": "Most valuable campaign", "value": top_campaign["label"], "note": f"Action rate: {top_campaign.get('action_rate_label')}."},
        {"label": "Major opportunity", "value": opportunities[0]["title"] if opportunities else "No urgent opportunity", "note": opportunities[0]["action"] if opportunities else "Keep collecting data."},
    ]


def dashboard_csv_export(kind, dashboard):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Mindful Diabetes analytics export"])
    writer.writerow(["Report", kind])
    writer.writerow(["Start", dashboard["start"]])
    writer.writerow(["End", dashboard["end"]])
    writer.writerow([])
    kind = clean_campaign_value(kind)
    if kind == "daily":
        writer.writerow(["Date", "Page views", "Sessions", "Guide detail views", "PDF opens", "PDF downloads", "Guide shares", "Donation clicks", "PayPal opens", "Newsletter signups", "Health-tool clicks", "Searches"])
        for row in dashboard["summary"].get("daily_trend", []):
            writer.writerow([row.get("day"), row.get("page_views", 0), row.get("sessions", 0), row.get("guide_detail_views", 0), row.get("pdf_views", 0), row.get("pdf_downloads", 0), row.get("guide_shares", 0), row.get("donation_clicks", 0), row.get("paypal_clicks", 0), row.get("newsletter_signups", 0), row.get("tool_clicks", 0), row.get("searches", 0)])
    elif kind == "guides":
        writer.writerow(["Guide", "Category", "Cards seen", "Details", "PDF opens", "Downloads", "Shares", "Download rate", "Related clicks", "Support clicks"])
        for row in dashboard["resource_insights"].get("top_guides", []):
            writer.writerow([safe_cell(row.get("title")), safe_cell(row.get("category")), row.get("card_views", 0), row.get("detail_views", 0), row.get("pdf_views", 0), row.get("downloads", 0), row.get("shares", 0), row.get("download_rate_label"), row.get("related_clicks", 0), row.get("donation_clicks", 0)])
    elif kind == "content":
        writer.writerow(["Page", "Title", "Group", "Views", "Sessions", "Guide actions", "Tool clicks", "Newsletter signups", "Donation clicks", "Meaningful actions"])
        for row in dashboard["summary"].get("top_content", []):
            writer.writerow([safe_cell(row.get("page")), safe_cell(row.get("title")), safe_cell(row.get("article_group")), row.get("views", 0), row.get("sessions", 0), row.get("guide_actions", 0), row.get("tool_clicks", 0), row.get("newsletter_signups", 0), row.get("donation_clicks", 0), row.get("meaningful_actions", 0)])
    elif kind == "campaigns":
        writer.writerow(["Campaign", "Source", "Medium", "Views", "Sessions", "Guide details", "PDF opens", "Downloads", "Shares", "Newsletter signups", "Donation clicks", "PayPal opens", "Health-tool clicks", "Meaningful actions", "Action rate"])
        for row in dashboard["summary"].get("campaign_performance", []):
            writer.writerow([safe_cell(row.get("label")), safe_cell(row.get("source")), safe_cell(row.get("medium")), row.get("page_views", 0), row.get("sessions", 0), row.get("guide_detail_views", 0), row.get("pdf_views", 0), row.get("pdf_downloads", 0), row.get("guide_shares", 0), row.get("newsletter_signups", 0), row.get("donation_clicks", 0), row.get("paypal_clicks", 0), row.get("health_tool_clicks", 0), row.get("actions", 0), row.get("action_rate_label")])
    elif kind == "search":
        writer.writerow(["Search term", "Searches", "No-result searches", "Average results"])
        for row in dashboard["search_insights"].get("top_queries", []):
            writer.writerow([safe_cell(row.get("label")), row.get("count", 0), row.get("no_results", 0), row.get("avg_results", "")])
        writer.writerow([])
        writer.writerow(["No-result term", "Count"])
        for row in dashboard["search_insights"].get("no_result_queries", []):
            writer.writerow([safe_cell(row.get("label")), row.get("no_results", row.get("count", 0))])
    elif kind == "opportunities":
        writer.writerow(["Priority", "Opportunity", "Metric", "Confidence", "Why it matters", "Recommended action"])
        for row in dashboard["opportunities"]:
            writer.writerow([row["priority"], safe_cell(row["title"]), safe_cell(row["metric"]), row["confidence"], safe_cell(row["why"]), safe_cell(row["action"])])
    else:
        writer.writerow(["Metric", "Value", "Previous period", "Change"])
        for stat in dashboard["stats"]:
            writer.writerow([safe_cell(stat["label"]), stat["value"], stat["previous"], safe_cell(stat["change"])])
    return output.getvalue()


def safe_cell(value):
    return analytics.csv_safe("" if value is None else value)


def dashboard_guide_report(guide, summary):
    totals = summary.get("totals", {})
    top_sources = summary.get("resource_source_pages", []) or summary.get("traffic_sources", [])
    download_rate = analytics.numeric_rate(totals.get("resource_pdf_downloads", 0), int(totals.get("resource_detail_views") or 0) + int(totals.get("resource_pdf_views") or 0))
    share_rate = analytics.numeric_rate(totals.get("resource_share_clicks", 0), totals.get("resource_pdf_downloads", 0))
    warnings = []
    if totals.get("resource_pdf_views", 0) >= 3 and not totals.get("resource_pdf_downloads", 0):
        warnings.append("People opened this guide but did not download it.")
    if totals.get("resource_pdf_downloads", 0) >= 3 and not totals.get("resource_share_clicks", 0):
        warnings.append("This guide is downloaded but rarely shared.")
    if totals.get("resource_card_views", 0) >= 5 and not totals.get("resource_detail_views", 0) and not totals.get("resource_pdf_views", 0):
        warnings.append("This guide receives card visibility but has a low open rate.")
    if not warnings:
        warnings.append("No guide-specific warning crossed the dashboard thresholds yet.")
    suggestions = []
    if totals.get("resource_card_views", 0) and not totals.get("resource_detail_views", 0):
        suggestions.append("Improve the guide-card title or description.")
    if totals.get("resource_pdf_views", 0) and not totals.get("resource_pdf_downloads", 0):
        suggestions.append("Move the PDF download button higher and use clearer button text.")
    if totals.get("resource_pdf_downloads", 0) and not totals.get("resource_share_clicks", 0):
        suggestions.append("Add a sharing prompt near the download confirmation.")
    if first_item(top_sources):
        suggestions.append(f"Promote the guide through {top_sources[0]['label']}, the strongest current source.")
    if not suggestions:
        suggestions.append("Keep collecting guide activity before changing the page.")
    return {
        "download_rate": analytics.percent_label(download_rate),
        "share_rate": analytics.percent_label(share_rate),
        "warnings": warnings[:5],
        "suggestions": suggestions[:5],
        "top_sources": top_sources[:8],
        "trend_max": dashboard_resource_trend_max(summary.get("daily_trend", [])),
    }


def free_guide_definition_by_slug(slug):
    return next((item for item in FREE_GUIDE_DEFINITIONS if item["slug"] == slug), None)


def normalize_dashboard_groups(summary):
    for row in summary.get("top_content", []):
        page = row.get("page") or ""
        mapped = analytics.ARTICLE_GROUP_OVERRIDES.get(page.strip("/"))
        if mapped:
            row["article_group"] = mapped
    grouped = {}
    for row in summary.get("top_content", []):
        group = row.get("article_group") or "Unknown"
        grouped[group] = grouped.get(group, 0) + int(row.get("views") or 0)
    if grouped:
        summary["article_groups"] = [
            {"label": label, "count": count, "sessions": 0}
            for label, count in sorted(grouped.items(), key=lambda item: (-item[1], item[0]))[:10]
        ]


def dashboard_missed_opportunities(summary):
    rows = []
    for row in summary.get("top_content", []):
        views = int(row.get("views") or 0)
        if views < 2:
            continue
        missing = []
        if int(row.get("donation_clicks") or 0) == 0 and int(row.get("paypal_clicks") or 0) == 0:
            missing.append("donation")
        if int(row.get("tool_clicks") or 0) == 0:
            missing.append("health tool")
        if int(row.get("newsletter_signups") or 0) == 0:
            missing.append("newsletter")
        if missing:
            rows.append(
                {
                    "page": row.get("page") or "",
                    "title": row.get("title") or row.get("page") or "Untitled page",
                    "views": views,
                    "score": missed_opportunity_score(row),
                    "missing": ", ".join(missing),
                    "recommendation": missed_opportunity_recommendation(missing),
                }
            )
    return sorted(rows, key=lambda row: (-row["score"], -row["views"], row["title"]))[:8]


def missed_opportunity_score(row):
    views = int(row.get("views") or 0)
    missing_count = 0
    for key in ("donation_clicks", "paypal_clicks", "tool_clicks", "newsletter_signups"):
        if int(row.get(key) or 0) == 0:
            missing_count += 1
    return views * max(1, missing_count)


def missed_opportunity_recommendation(missing):
    if "donation" in missing:
        return "Try a clearer support CTA near the first useful section."
    if "health tool" in missing:
        return "Add a tool CTA that matches the article topic."
    if "newsletter" in missing:
        return "Place the newsletter form closer to the article body."
    return "Review CTA placement."


def dashboard_insights(summary, missed_opportunities):
    totals = summary.get("totals", {})
    insights = []
    top_page = first_item(summary.get("top_pages"))
    if top_page:
        insights.append(f"{top_page['label']} is the top page in this period with {top_page['count']} views.")
    top_tool = first_item(summary.get("health_tools"))
    if top_tool:
        insights.append(f"{top_tool['label']} is the most-clicked health tool.")
    top_search = first_item(summary.get("search_queries"))
    if top_search:
        insights.append(f"Visitors are searching for {top_search['label']}, which can guide the next article or page update.")
    top_campaign = first_item(summary.get("campaign_performance"))
    if top_campaign:
        insights.append(f"{top_campaign['label']} is the strongest tracked campaign with {top_campaign.get('page_views', 0)} views.")
    if totals.get("cta_impressions", 0) and not totals.get("donation_cta_clicks", 0) and not totals.get("paypal_clicks", 0):
        insights.append("Donation CTAs are being seen, but no donation or PayPal clicks are recorded yet.")
    if totals.get("newsletter_views", 0) and not totals.get("newsletter_signups", 0):
        insights.append("Newsletter forms are visible, but successful signups are not recorded yet.")
    if missed_opportunities:
        insights.append(f"{missed_opportunities[0]['title']} has traffic but missing {missed_opportunities[0]['missing']} engagement.")
    if not insights:
        insights.append("Analytics are collecting cleanly. More insights will appear as visitors interact with CTAs.")
    return insights[:5]


def dashboard_health_scores(totals, page_views):
    action_clicks = sum(
        int(totals.get(key) or 0)
        for key in ("donation_cta_clicks", "paypal_clicks", "health_tool_clicks", "newsletter_signups")
    )
    return [
        score_item("Traffic", page_views, [(100, "Good"), (25, "Growing")], "Quiet", "Pages read in this period."),
        score_item("Engagement", analytics.numeric_rate(action_clicks, page_views), [(5, "Good"), (2, "Needs attention")], "Quiet", "Action clicks compared with pages read.", suffix="%"),
        score_item("Donation intent", int(totals.get("donation_cta_clicks", 0)) + int(totals.get("paypal_clicks", 0)), [(5, "Active"), (1, "Starting")], "Low", "Donation/support actions recorded."),
        score_item("Newsletter growth", int(totals.get("newsletter_signups", 0)), [(5, "Active"), (1, "Starting")], "Not started", "Successful newsletter signups."),
        score_item("Health-tool interest", int(totals.get("health_tool_clicks", 0)), [(5, "Active"), (1, "Starting")], "Low", "Clicks to JEIR, Memovela, and tools."),
    ]


def score_item(label, value, thresholds, fallback, help_text, suffix=""):
    numeric = 0 if value is None else float(value)
    status = fallback
    for threshold, status_label in thresholds:
        if numeric >= threshold:
            status = status_label
            break
    return {
        "label": label,
        "value": "No data" if value is None else f"{numeric:.1f}{suffix}" if suffix else f"{int(numeric)}",
        "status": status,
        "tone": score_tone(status),
        "help": help_text,
    }


def score_tone(status):
    if status in {"Good", "Active"}:
        return "good"
    if status in {"Growing", "Starting", "Needs attention"}:
        return "watch"
    return "low"


def dashboard_recommended_actions(summary, missed_opportunities, health_scores):
    totals = summary.get("totals", {})
    actions = []
    top_missed = missed_opportunities[0] if missed_opportunities else None
    if top_missed:
        actions.append(
            {
                "priority": "High",
                "title": f"Improve {top_missed['title']}",
                "why": f"It has {top_missed['views']} views but is missing {top_missed['missing']} engagement.",
                "next_step": top_missed["recommendation"],
                "page": top_missed["page"],
            }
        )
    if totals.get("cta_impressions", 0) and not totals.get("donation_cta_clicks", 0) and not totals.get("paypal_clicks", 0):
        actions.append(
            {
                "priority": "High",
                "title": "Test a clearer donation message",
                "why": "Visitors are seeing support buttons, but no donation clicks or PayPal opens are recorded.",
                "next_step": "Try language like 'Support free diabetes tools' on high-traffic articles.",
                "page": "",
            }
        )
    if totals.get("newsletter_views", 0) and not totals.get("newsletter_signups", 0):
        actions.append(
            {
                "priority": "Medium",
                "title": "Move newsletter signup closer to the article",
                "why": "Newsletter forms are visible, but successful signups are not showing yet.",
                "next_step": "Add a short benefit line and place the form after the first helpful section.",
                "page": "",
            }
        )
    if int(totals.get("health_tool_clicks", 0) or 0) < 3 and summary.get("top_pages"):
        actions.append(
            {
                "priority": "Medium",
                "title": "Add a relevant health-tool CTA to top articles",
                "why": "Health-tool interest is still early, and top articles can send more readers to JEIR or Memovela.",
                "next_step": "Add a contextual JEIR or Memovela button to the top three most-read articles.",
                "page": summary["top_pages"][0]["label"],
            }
        )
    if not actions:
        actions.append(
            {
                "priority": "Low",
                "title": "Keep collecting data",
                "why": "Nothing urgent stands out in this date range.",
                "next_step": "Review again after more public traffic arrives.",
                "page": "",
            }
        )
    return actions[:5]


def dashboard_growth_goals(config, summary):
    goals = load_growth_goals(config)
    rows = []
    totals = summary.get("totals", {})
    for goal in goals:
        target = max(1, int(goal.get("target") or 1))
        value = growth_metric_value(totals, goal.get("metric"))
        progress = min(100, round((value / target) * 100, 1))
        remaining = max(0, target - value)
        rows.append(
            {
                "metric": goal.get("metric"),
                "label": goal.get("label") or goal.get("metric", "Goal"),
                "value": value,
                "target": target,
                "unit": goal.get("unit") or "",
                "why": goal.get("why") or "",
                "progress": progress,
                "remaining": remaining,
                "status": goal_status(progress),
            }
        )
    return rows[:6]


def load_growth_goals(config):
    raw = (config.get("ANALYTICS_GROWTH_GOALS_JSON") or "").strip()
    if not raw:
        return DEFAULT_GROWTH_GOALS
    try:
        goals = json.loads(raw)
    except json.JSONDecodeError:
        return DEFAULT_GROWTH_GOALS
    if not isinstance(goals, list):
        return DEFAULT_GROWTH_GOALS
    cleaned = []
    allowed_metrics = {
        "page_views",
        "anonymous_sessions",
        "newsletter_signups",
        "health_tool_clicks",
        "donation_interest",
        "site_searches",
        "search_result_clicks",
        "action_clicks",
    }
    for goal in goals:
        if not isinstance(goal, dict) or goal.get("metric") not in allowed_metrics:
            continue
        try:
            target = int(goal.get("target") or 0)
        except (TypeError, ValueError):
            continue
        if target <= 0:
            continue
        cleaned.append(
            {
                "metric": goal["metric"],
                "label": clamp_plain_text(goal.get("label") or goal["metric"].replace("_", " ").title(), 60),
                "target": min(target, 1_000_000),
                "unit": clamp_plain_text(goal.get("unit") or "", 32),
                "why": clamp_plain_text(goal.get("why") or "", 180),
            }
        )
    return cleaned or DEFAULT_GROWTH_GOALS


def growth_metric_value(totals, metric):
    if metric == "donation_interest":
        return int(totals.get("donation_cta_clicks") or 0) + int(totals.get("paypal_clicks") or 0)
    if metric == "action_clicks":
        return sum(
            int(totals.get(key) or 0)
            for key in (
                "newsletter_signups",
                "donation_cta_clicks",
                "paypal_clicks",
                "health_tool_clicks",
                "search_result_clicks",
            )
        )
    return int(totals.get(metric) or 0)


def goal_status(progress):
    if progress >= 100:
        return "Reached"
    if progress >= 70:
        return "Close"
    if progress >= 25:
        return "Moving"
    return "Starting"


def dashboard_search_insights(summary):
    totals = summary.get("totals", {})
    searches = int(totals.get("site_searches") or 0)
    clicks = int(totals.get("search_result_clicks") or 0)
    no_result_rows = summary.get("search_no_results") or []
    click_rate = analytics.numeric_rate(clicks, searches)
    notes = []
    top_query = first_item(summary.get("search_queries"))
    if top_query:
        notes.append(f"Top search: {top_query['label']} ({top_query['count']} searches).")
    if no_result_rows:
        notes.append(f"Content gap: {no_result_rows[0]['label']} was searched with no results.")
    if searches and not clicks:
        notes.append("People are searching, but no search-result clicks are recorded yet.")
    if not notes:
        notes.append("Search insights will appear after visitors use the site search.")
    return {
        "searches": searches,
        "clicks": clicks,
        "click_rate": analytics.percent_label(click_rate),
        "top_queries": summary.get("search_queries", [])[:8],
        "no_result_queries": no_result_rows[:8],
        "result_clicks": summary.get("search_result_clicks", [])[:8],
        "notes": notes[:4],
    }


def dashboard_resource_insights(summary):
    totals = summary.get("totals", {})
    pdf_views = int(totals.get("resource_pdf_views") or 0)
    downloads = int(totals.get("resource_pdf_downloads") or 0)
    shares = int(totals.get("resource_share_clicks") or 0)
    detail_views = int(totals.get("resource_detail_views") or 0)
    cards_seen = int(totals.get("resource_card_views") or 0)
    guide_rows = summary.get("resource_guides", [])
    top_guide = first_item(guide_rows)
    download_rate = analytics.numeric_rate(downloads, pdf_views + detail_views)
    notes = []
    if top_guide:
        notes.append(f"{top_guide['title']} is the strongest free guide so far with {top_guide.get('downloads', 0)} downloads and {top_guide.get('shares', 0)} shares.")
    if pdf_views and not downloads:
        notes.append("People are opening PDFs, but download clicks are not showing yet.")
    if downloads and not shares:
        notes.append("Guides are being downloaded, but sharing has not started yet.")
    if cards_seen and not detail_views and not pdf_views:
        notes.append("Guide cards are being seen, but visitors are not opening guide details or PDFs yet.")
    if not notes:
        notes.append("Free Guide insights will appear after visitors view, download, or share the PDFs.")
    return {
        "pdf_views": pdf_views,
        "downloads": downloads,
        "shares": shares,
        "detail_views": detail_views,
        "cards_seen": cards_seen,
        "download_rate": analytics.percent_label(download_rate) if download_rate is not None else "No PDF/detail views",
        "top_guides": guide_rows[:8],
        "action_mix": summary.get("resource_action_mix", [])[:10],
        "share_platforms": summary.get("resource_share_platforms", [])[:8],
        "source_pages": summary.get("resource_source_pages", [])[:8],
        "related_clicks": summary.get("resource_related_clicks", [])[:8],
        "notes": notes[:4],
    }


def dashboard_growth_experiments(summary, missed_opportunities, goals, search_insights):
    totals = summary.get("totals", {})
    experiments = []
    if search_insights.get("no_result_queries"):
        query = search_insights["no_result_queries"][0]["label"]
        experiments.append(
            experiment_item(
                "Create a page for a searched topic",
                "Ready to run",
                f"Visitors searched for '{query}' and did not get a satisfying result.",
                f"Publish or update content that directly answers '{query}'.",
                "Watch search-result clicks and page views for the new or updated page.",
            )
        )
    if missed_opportunities:
        page = missed_opportunities[0]
        experiments.append(
            experiment_item(
                "Add one stronger CTA to a high-traffic page",
                "Ready to run",
                f"{page['title']} has traffic but is missing {page['missing']} engagement.",
                page["recommendation"],
                "Compare CTA clicks on this page over the next 7 to 14 days.",
            )
        )
    if int(totals.get("newsletter_views") or 0) and not int(totals.get("newsletter_signups") or 0):
        experiments.append(
            experiment_item(
                "Test a clearer newsletter promise",
                "Ready to run",
                "Newsletter forms are visible, but signups are not happening yet.",
                "Try a short promise like 'Get practical prevention notes once a week.'",
                "Watch newsletter interactions and accepted signups.",
            )
        )
    top_campaign = first_item(summary.get("campaign_performance"))
    if top_campaign:
        experiments.append(
            experiment_item(
                "Repeat the best campaign source",
                "Watching",
                f"{top_campaign['label']} is the strongest tracked campaign so far.",
                "Reuse the same source and message on one similar outreach channel.",
                "Compare page views and action rate between campaign links.",
            )
        )
    weak_goal = first_unmet_goal(goals)
    if weak_goal and len(experiments) < 5:
        experiments.append(
            experiment_item(
                f"Push the '{weak_goal['label']}' goal",
                "Planning",
                f"This goal is {weak_goal['progress']}% complete for the selected period.",
                "Choose one public page and add a single matching next step for readers.",
                f"Track progress toward {weak_goal['target']} {weak_goal['unit']}.",
            )
        )
    if not experiments:
        experiments.append(
            experiment_item(
                "Keep the baseline running",
                "Watching",
                "No urgent growth issue stands out yet.",
                "Let the tracker collect more behavior before changing multiple pages.",
                "Review this panel after the next outreach push.",
            )
        )
    return experiments[:5]


def experiment_item(title, status, why, action, measure):
    return {"title": title, "status": status, "why": why, "action": action, "measure": measure}


def first_unmet_goal(goals):
    pending = [goal for goal in goals if goal.get("progress", 0) < 100]
    return sorted(pending, key=lambda goal: (goal.get("progress", 0), -goal.get("target", 0)))[0] if pending else None


def dashboard_weekly_brief(summary, goals, experiments, search_insights, resource_insights=None):
    totals = summary.get("totals", {})
    top_page = first_item(summary.get("top_pages")) or {"label": "No page activity", "count": 0}
    top_source = first_item(summary.get("traffic_sources")) or {"label": "No traffic source yet", "count": 0}
    top_campaign = first_item(summary.get("campaign_performance")) or {"label": "No campaign activity", "page_views": 0, "actions": 0}
    leading_goal = first_unmet_goal(goals) or (goals[0] if goals else {"label": "Growth", "remaining": 0, "unit": ""})
    top_resource = first_item((resource_insights or {}).get("top_guides", [])) or {"title": "No guide activity", "downloads": 0, "shares": 0}
    return [
        f"Top page: {top_page['label']} with {top_page['count']} views.",
        f"Strongest traffic source: {top_source['label']} with {top_source['count']} visits.",
        f"Searches: {totals.get('site_searches', 0)} total, with {search_insights.get('click_rate')} clicking into a result.",
        f"Top free guide: {top_resource['title']} with {top_resource.get('downloads', 0)} downloads and {top_resource.get('shares', 0)} shares.",
        f"Best campaign: {top_campaign['label']} with {top_campaign.get('page_views', 0)} views and {top_campaign.get('actions', 0)} actions.",
        f"Goal focus: {leading_goal['label']} needs {leading_goal.get('remaining', 0)} more {leading_goal.get('unit', 'actions')}.",
        f"Next experiment: {experiments[0]['title'] if experiments else 'Keep collecting baseline data'}.",
    ]


def dashboard_campaign_builder(config, args):
    site_base_url = (config.get("SITE_BASE_URL") or "https://mindfuldiabetes.org").rstrip("/")
    page_path = clean_campaign_page(args.get("campaign_page") or "/donation/")
    source = clean_campaign_value(args.get("campaign_source") or "newsletter")
    medium = clean_campaign_value(args.get("campaign_medium") or "email")
    campaign = clean_campaign_value(args.get("campaign_name") or "growth_push")
    content = clean_campaign_value(args.get("campaign_content") or "support_cta")
    term = clean_campaign_value(args.get("campaign_term") or "")
    params = {
        "utm_source": source,
        "utm_medium": medium,
        "utm_campaign": campaign,
        "utm_content": content,
    }
    if term:
        params["utm_term"] = term
    generated_url = f"{site_base_url}{page_path}?{urlencode(params)}"
    return {
        "page_path": page_path,
        "source": source,
        "medium": medium,
        "campaign": campaign,
        "content": content,
        "term": term,
        "url": generated_url,
    }


def clean_campaign_page(value):
    value = (value or "/").strip()
    if value.startswith("http://") or value.startswith("https://"):
        value = urlparse(value).path or "/"
    if not value.startswith("/"):
        value = "/" + value
    value = value.split("?", 1)[0].split("#", 1)[0]
    value = re.sub(r"[^A-Za-z0-9/_-]", "", value)
    if not value or value.startswith(("/admin", "/analytics", "/static")):
        return "/"
    if not value.endswith("/"):
        value += "/"
    return value[:180]


def clean_campaign_value(value):
    value = (value or "").strip().lower().replace(" ", "_")
    value = re.sub(r"[^a-z0-9_.-]", "", value)
    return value[:80]


def clamp_plain_text(value, limit):
    return re.sub(r"\s+", " ", str(value or "")).strip()[:limit]


def dashboard_pages_by_purpose(summary):
    buckets = {
        "Best education pages": [],
        "Best health-tool pages": [],
        "Best donation-interest pages": [],
        "Best newsletter pages": [],
        "Traffic but no action": [],
    }
    for row in summary.get("top_content", []):
        item = {
            "page": row.get("page") or "",
            "title": row.get("title") or row.get("page") or "Untitled page",
            "count": int(row.get("views") or 0),
        }
        if item["count"]:
            buckets["Best education pages"].append(item)
        if int(row.get("tool_clicks") or 0):
            buckets["Best health-tool pages"].append({**item, "count": int(row.get("tool_clicks") or 0)})
        if int(row.get("donation_clicks") or 0) or int(row.get("paypal_clicks") or 0):
            buckets["Best donation-interest pages"].append({**item, "count": int(row.get("donation_clicks") or 0) + int(row.get("paypal_clicks") or 0)})
        if int(row.get("newsletter_signups") or 0):
            buckets["Best newsletter pages"].append({**item, "count": int(row.get("newsletter_signups") or 0)})
        if item["count"] >= 2 and not any(int(row.get(key) or 0) for key in ("donation_clicks", "paypal_clicks", "tool_clicks", "newsletter_signups")):
            buckets["Traffic but no action"].append(item)
    return [
        {"label": label, "items": sorted(items, key=lambda item: (-item["count"], item["title"]))[:5]}
        for label, items in buckets.items()
    ]


def dashboard_device_insights(summary):
    devices = summary.get("device_categories", [])
    total = sum(int(item.get("count") or 0) for item in devices)
    if not total:
        return ["Device insights will appear after more visitor activity is recorded."]
    top = max(devices, key=lambda item: int(item.get("count") or 0))
    notes = [f"{top.get('label', 'Unknown')} is the most common device category in this period."]
    if str(top.get("label")).lower() == "mobile":
        notes.append("Check that CTA buttons and newsletter forms appear high enough on phone screens.")
    else:
        notes.append("Compare this with mobile behavior as more traffic arrives.")
    return notes


def dashboard_benchmarks(totals, page_views):
    return [
        benchmark_item("Health-tool click rate", totals.get("health_tool_clicks", 0), page_views, "2-5%", "Good early signal when readers try JEIR, Memovela, or the game."),
        benchmark_item("Newsletter signup rate", totals.get("newsletter_signups", 0), page_views, "1-3%", "Useful for turning article readers into repeat visitors."),
        benchmark_item("Donation intent rate", int(totals.get("donation_cta_clicks", 0)) + int(totals.get("paypal_clicks", 0)), page_views, "0.5-2%", "Usually lower than tool clicks and needs repeated exposure."),
    ]


def benchmark_item(label, numerator, denominator, healthy_range, note):
    rate = analytics.numeric_rate(numerator, denominator)
    return {
        "label": label,
        "value": analytics.percent_label(rate),
        "healthy_range": healthy_range,
        "note": note,
    }


def human_event_label(event):
    labels = {
        "page_view": "Someone viewed a public page",
        "cta_impression": "Someone saw a call-to-action",
        "donation_cta_click": "Someone clicked a support button",
        "paypal_click": "Someone opened PayPal",
        "donation_completed": "PayPal confirmed a donation",
        "donation_refunded": "PayPal reported a refund",
        "donation_denied": "PayPal denied a payment",
        "health_tool_click": "Someone opened a health tool",
        "newsletter_form_view": "Someone saw a newsletter form",
        "newsletter_form_interaction": "Someone interacted with a newsletter form",
        "newsletter_signup": "Someone joined the newsletter",
        "site_search": "Someone searched the site",
        "search_result_click": "Someone clicked a search result",
        "content_cta_click": "Someone clicked a content button",
        "resource_download_click": "Someone clicked a resource download",
        "free_guides_page_view": "Someone viewed the Free Guides library",
        "resource_card_view": "Someone saw a guide card",
        "resource_detail_view": "Someone viewed a guide detail page",
        "resource_pdf_view": "Someone opened a guide PDF",
        "resource_pdf_download": "Someone downloaded a guide PDF",
        "resource_share_click": "Someone shared a guide",
        "resource_related_link_click": "Someone clicked a related guide link",
        "resource_newsletter_click": "Someone clicked the Free Guides newsletter form",
        "resource_newsletter_submit": "Someone joined from the Free Guides page",
        "resource_donation_click": "Someone clicked Free Guides support",
        "sponsor_click": "Someone clicked a sponsor link",
        "event_registration_click": "Someone clicked event registration",
        "volunteer_cta_click": "Someone clicked a volunteer button",
    }
    event_name = event.get("event_name") or ""
    label = labels.get(event_name, event_name.replace("_", " ").title())
    if event.get("element_label"):
        return f"{label}: {event['element_label']}"
    return label


def first_item(rows):
    return rows[0] if rows else None


def dashboard_trend_max(rows):
    values = []
    for row in rows:
        values.extend(
            [
                int(row.get("page_views") or 0),
                int(row.get("donation_clicks") or 0),
                int(row.get("paypal_clicks") or 0),
                int(row.get("tool_clicks") or 0),
                int(row.get("newsletter_signups") or 0),
                int(row.get("pdf_downloads") or 0),
                int(row.get("guide_shares") or 0),
                int(row.get("searches") or 0),
            ]
        )
    return max(1, max(values, default=1))


def dashboard_resource_trend_max(rows):
    values = []
    for row in rows:
        values.extend(
            [
                int(row.get("guide_detail_views") or 0),
                int(row.get("pdf_views") or 0),
                int(row.get("pdf_downloads") or 0),
                int(row.get("guide_shares") or 0),
            ]
        )
    return max(1, max(values, default=1))


def page_analytics_recommendations(summary):
    totals = summary.get("totals", {})
    recommendations = []
    if totals.get("page_views", 0) and not totals.get("cta_impressions", 0):
        recommendations.append("This page has views but no tracked CTA impressions. Add or label at least one clear CTA.")
    if totals.get("cta_impressions", 0) and not totals.get("donation_cta_clicks", 0) and not totals.get("paypal_clicks", 0):
        recommendations.append("Donation/support CTAs are visible but not clicked. Try a more specific support message or a higher placement.")
    if totals.get("page_views", 0) >= 2 and not totals.get("health_tool_clicks", 0):
        recommendations.append("Readers are arriving here, but no health-tool clicks are recorded. Add a relevant JEIR, Memovela, or game CTA.")
    if totals.get("newsletter_views", 0) and not totals.get("newsletter_interactions", 0):
        recommendations.append("Newsletter forms are visible but not interacted with. Move the form closer to the main article content.")
    if not recommendations:
        recommendations.append("No urgent recommendation yet. Keep collecting data for this page.")
    return recommendations


def should_track_request(response):
    tracked_endpoints = {
        "home",
        "guide",
        "search",
        "pages_index",
        "research",
        "resources_index",
        "resource_detail",
        "health_tools",
        "volunteer",
        "page_detail",
    }
    return (
        request.method == "GET"
        and response.status_code == 200
        and request.endpoint in tracked_endpoints
        and "text/html" in (response.content_type or "")
    )


def browser_analytics_config(config):
    enabled = analytics.analytics_enabled(config)
    if request.path.startswith(("/admin", "/analytics", "/static")):
        enabled = False
    return {
        "enabled": enabled,
        "endpoint": "/analytics/events",
        "environment": analytics.analytics_environment(config),
    }


def google_ads_tracking_config(config):
    conversion_id = (config.get("GOOGLE_ADS_CONVERSION_ID") or "").strip()
    if conversion_id and not conversion_id.startswith("AW-"):
        conversion_id = f"AW-{conversion_id}"

    enabled = bool(conversion_id)
    if config.get("TESTING") or config.get("DEBUG"):
        enabled = analytics.truthy(config.get("GOOGLE_ADS_ENABLE_LOCAL_TESTING"))
    if request.path.startswith(("/admin", "/analytics", "/static")):
        enabled = False

    return {
        "enabled": enabled,
        "conversion_id": conversion_id,
        "event_send_to": google_ads_event_send_to(config, conversion_id),
    }


def google_ads_event_send_to(config, conversion_id):
    raw_actions = (config.get("GOOGLE_ADS_CONVERSION_ACTIONS_JSON") or "").strip()
    if not raw_actions or not conversion_id:
        return {}
    try:
        actions = json.loads(raw_actions)
    except json.JSONDecodeError:
        return {}
    if not isinstance(actions, dict):
        return {}

    event_send_to = {}
    for event_name, send_to in actions.items():
        event_name = analytics.EVENT_NAME_ALIASES.get(event_name, event_name)
        if event_name not in analytics.MEANINGFUL_ACTION_EVENTS:
            continue
        if not isinstance(send_to, str):
            continue
        send_to = send_to.strip()
        if not send_to:
            continue
        event_send_to[event_name] = send_to if send_to.startswith("AW-") else f"{conversion_id}/{send_to}"
    return event_send_to


def same_origin_request(request_obj):
    origin = request_obj.headers.get("Origin")
    if not origin:
        return True
    return origin.rstrip("/") == request_obj.host_url.rstrip("/")


def record_server_analytics_event(config, content, event_name, **values):
    if not analytics.analytics_enabled(config):
        return False
    payload = {
        "event_id": values.pop("event_id", f"server:{event_name}:{secrets.token_urlsafe(24)}"),
        "event_name": event_name,
        "environment": analytics.analytics_environment(config),
        **values,
    }
    event = analytics.normalize_event_payload(payload, config)
    fake_path = event.get("page_path") or "/"
    context = analytics.content_context_for_path(content, fake_path)
    for key, value in context.items():
        event[key] = event.get(key) or value
    return analytics.analytics_store(config).store_event(event)


def register_analytics_commands(app):
    @app.cli.command("analytics-cleanup")
    def analytics_cleanup_command():
        retention_days = int(app.config.get("ANALYTICS_RETENTION_DAYS") or analytics.DEFAULT_RETENTION_DAYS)
        before = analytics.utc_now() - timedelta(days=retention_days)
        removed = analytics.analytics_store(app.config).cleanup(before)
        click.echo(f"Removed {removed} analytics event(s) older than {retention_days} days.")

    @app.cli.command("analytics-send-weekly-summary")
    def analytics_weekly_summary_command():
        recipients = [
            email.strip()
            for email in (app.config.get("ANALYTICS_REPORT_RECIPIENTS") or app.config.get("ADMIN_EMAIL") or "").split(",")
            if is_valid_email(email.strip())
        ]
        if not recipients:
            raise click.ClickException("Set ANALYTICS_REPORT_RECIPIENTS to one or more administrator emails.")
        report = analytics.weekly_summary(app.config)
        admin_url = os.getenv("SITE_BASE_URL", "https://mindfuldiabetes.org").rstrip("/") + "/admin/analytics/"
        text = analytics.format_weekly_summary_text(report, admin_url=admin_url)
        sent, message = send_brevo_email(
            app.config,
            recipients,
            "Mindful Diabetes weekly analytics summary",
            text,
            "<pre style=\"font-family:Arial,sans-serif;white-space:pre-wrap;\">" + html_lib.escape(text) + "</pre>",
        )
        if not sent:
            raise click.ClickException(message)
        click.echo(f"Weekly analytics summary sent to {len(recipients)} recipient(s).")


def title_for_request(content, endpoint, view_args):
    if endpoint == "home":
        return "Homepage"
    if endpoint == "guide":
        return "Guide"
    if endpoint == "search":
        return "Search"
    if endpoint == "pages_index":
        return "All Pages"
    if endpoint == "research":
        return "Research"
    if endpoint == "health_tools":
        return "Health Tools"
    if endpoint == "volunteer":
        return "Volunteer"
    if endpoint == "resources_index":
        return "Educational Resources"
    if endpoint == "resource_detail":
        resource = resource_library.resource_by_slug((view_args or {}).get("resource_slug", ""))
        return resource["title"] if resource else "Educational Resource"
    if endpoint == "page_detail":
        slug = (view_args or {}).get("slug", "")
        item = content.pages_by_slug.get(slug) or content.posts_by_slug.get(slug)
        return item.get("title", slug) if item else slug
    return endpoint or ""


def navigation_state_for_request(content):
    endpoint = request.endpoint or ""
    slug = (request.view_args or {}).get("slug", "")
    is_post = endpoint == "page_detail" and slug in content.posts_by_slug
    is_page = endpoint == "page_detail" and slug in content.pages_by_slug
    path = request.path or "/"
    state = {
        "section": "",
        "home": endpoint == "home",
        "pathways": endpoint == "guide" or is_post,
        "research": endpoint == "research",
        "resources": endpoint in {"resources_index", "resources_index_slash", "resource_detail", "resource_detail_slash"} or path.startswith("/resources"),
        "free_guides": endpoint in {"free_guides", "free_guide_detail", "free_guides_no_slash", "free_guide_detail_no_slash"} or path.startswith("/free-guides"),
        "health_tools": endpoint == "health_tools",
        "sponsors": is_page and slug == "sponsors",
        "donation": is_page and slug == "donation",
    }
    if state["pathways"] or state["research"]:
        state["section"] = "learn"
    elif state["resources"] or state["free_guides"] or state["health_tools"]:
        state["section"] = "resources"
    elif state["sponsors"] or state["donation"]:
        state["section"] = "about_support"
    elif state["home"]:
        state["section"] = "home"
    return state


def public_query_args(args):
    return {key: args.get(key, "") for key in ("q", "page") if args.get(key)}


def safe_admin_next_url(raw_url):
    url = raw_url or "/admin/"
    if not url.startswith("/") or url.startswith("//"):
        return "/admin/"
    if not url.startswith("/admin/"):
        return "/admin/"
    return url


def get_admin_csrf_token():
    token = session.get("admin_csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["admin_csrf_token"] = token
    return token


def validate_admin_csrf():
    expected = session.get("admin_csrf_token")
    submitted = request.headers.get("X-CSRF-Token") or request.form.get("csrf_token")
    if not expected or not submitted or not hmac.compare_digest(expected, submitted):
        abort(400)


def merge_cms_payload(existing, payload):
    merged = dict(existing)
    payload = payload or {}
    for key in (
        "title",
        "slug",
        "status",
        "excerpt",
        "featured_image",
        "content_type",
        "author",
        "published_at",
        "scheduled_at",
        "archived_at",
    ):
        if key in payload:
            merged[key] = payload[key]
    for key in ("blocks_json", "settings_json", "seo_json"):
        if key in payload:
            merged[key] = payload[key]
    for browser_key, model_key in (("blocks", "blocks_json"), ("settings", "settings_json"), ("seo", "seo_json")):
        if browser_key in payload:
            merged[model_key] = payload[browser_key]
    return merged


def cms_public_payload(item):
    return {
        "id": item["id"],
        "title": item["title"],
        "slug": item["slug"],
        "status": item["status"],
        "content_type": item["content_type"],
        "updated_at": item["updated_at"],
        "published_at": item["published_at"],
    }


def cms_view_url(item):
    return url_for("page_detail", slug=item["slug"]) if item.get("status") == "published" else ""


def verify_turnstile(config, token, remote_ip=""):
    if not is_turnstile_configured(config):
        return True, ""

    if not token:
        return False, "Please complete the human verification and try again."

    payload = {
        "secret": config["TURNSTILE_SECRET_KEY"],
        "response": token,
    }
    if remote_ip:
        payload["remoteip"] = remote_ip

    request_obj = Request(
        config["TURNSTILE_VERIFY_URL"],
        data=urlencode(payload).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    try:
        with urlopen(request_obj, timeout=8) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        try:
            result = json.loads(error.read().decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            result = {}
    except (URLError, json.JSONDecodeError, UnicodeDecodeError):
        return False, "We could not verify the signup. Please try again."

    if result.get("success"):
        return True, ""

    return False, "Please complete the human verification and try again."


def mailchimp_server_prefix(config):
    explicit_prefix = (config.get("MAILCHIMP_SERVER_PREFIX") or "").strip()
    if explicit_prefix:
        return explicit_prefix

    api_key = config.get("MAILCHIMP_API_KEY") or ""
    if "-" in api_key:
        return api_key.rsplit("-", 1)[1]
    return ""


def subscribe_to_mailchimp(config, email):
    server_prefix = mailchimp_server_prefix(config)
    if not server_prefix:
        return False, "Mailchimp needs a server prefix, such as us21. Add MAILCHIMP_SERVER_PREFIX to .env."

    email_hash = hashlib.md5(email.lower().encode("utf-8")).hexdigest()
    url = (
        f"https://{server_prefix}.api.mailchimp.com/3.0/lists/"
        f"{config['MAILCHIMP_AUDIENCE_ID']}/members/{email_hash}"
    )
    tags = [tag.strip() for tag in (config.get("MAILCHIMP_TAGS") or "").split(",") if tag.strip()]
    payload = {
        "email_address": email,
        "status_if_new": "subscribed",
        "status": "subscribed",
    }
    if tags:
        payload["tags"] = tags

    request_obj = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        method="PUT",
        headers={
            "Authorization": f"apikey {config['MAILCHIMP_API_KEY']}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urlopen(request_obj, timeout=12) as response:
            if 200 <= response.status < 300:
                return True, "Subscribed"
    except HTTPError as error:
        try:
            body = json.loads(error.read().decode("utf-8"))
            detail = body.get("detail") or body.get("title")
        except (json.JSONDecodeError, UnicodeDecodeError):
            detail = None
        return False, detail or "Mailchimp rejected the signup. Check the API key and audience ID."
    except URLError:
        return False, "Could not reach Mailchimp. Please try again later."

    return False, "Mailchimp returned an unexpected response."


def canonical_path_for(item):
    if item["type"] == "page" and item["slug"] == "mindful":
        return "/"
    return f"/{item['slug'].strip('/')}/"


def preview_text_for(item):
    if item.get("excerpt_html"):
        return html_to_text(item["excerpt_html"])
    return first_meaningful_content_text(item.get("content_html", ""))


def first_meaningful_content_text(raw_html):
    text = searchable_content_text(raw_html)
    sentences = re.split(r"(?<=[.!?])\s+", text)
    preview = " ".join(sentences[:3]).strip()
    return preview or text


def first_content_image(raw_html):
    extractor = FirstImageParser()
    extractor.feed(rewrite_upload_urls(raw_html or ""))
    return extractor.image


class FirstImageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.image = None

    def handle_starttag(self, tag, attrs):
        if self.image or tag.lower() != "img":
            return

        attr_map = {name.lower(): value for name, value in attrs if value is not None}
        src = attr_map.get("src", "").strip()
        if not src or self._is_tracking_pixel(src, attr_map):
            return

        self.image = {
            "src": html_lib.unescape(src),
            "alt": html_lib.unescape(attr_map.get("alt", "")).strip(),
            "title": html_lib.unescape(attr_map.get("title", "")).strip(),
            "description": html_lib.unescape(attr_map.get("data-description", "")).strip(),
        }

    @staticmethod
    def _is_tracking_pixel(src, attrs):
        width = attrs.get("width")
        height = attrs.get("height")
        if width == "1" or height == "1":
            return True
        return "paypal.com" in src or "paypalobjects.com" in src


def format_date(value):
    if not value:
        return ""
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").strftime("%B %-d, %Y")
    except ValueError:
        return value[:10]


def clean_wordpress_html(raw_html, paypal_button_id):
    html = raw_html
    html = re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)
    html = re.sub(r"<script\b[^>]*>.*?</script>", "", html, flags=re.IGNORECASE | re.DOTALL)
    html = re.sub(r"<style\b[^>]*>.*?</style>", "", html, flags=re.IGNORECASE | re.DOTALL)
    html = rewrite_upload_urls(html)
    html = rewrite_internal_href_attributes(html)
    html = strip_imported_attributes(html)
    html = wrap_media_iframes(html)
    html = re.sub(r"\[give_form[^\]]*\]", paypal_form(paypal_button_id), html, flags=re.IGNORECASE)
    html = re.sub(r"\[give_receipt[^\]]*\]", donation_receipt_message(paypal_button_id), html, flags=re.IGNORECASE)
    html = re.sub(r"\[give_donor_dashboard[^\]]*\]", donor_dashboard_message(paypal_button_id), html, flags=re.IGNORECASE)
    html = embed_bare_youtube_urls(html)
    html = remove_empty_paragraphs(html)
    html = remove_empty_list_items(html)
    html = re.sub(r"<iframe\b", '<iframe loading="lazy"', html, flags=re.IGNORECASE)
    return html


def strip_imported_attributes(html):
    def replace(match):
        attr_name = match.group("name").lower()
        attr_value = match.group("value")

        if attr_name == "class":
            classes = [item for item in attr_value.split() if item in PRESERVED_CONTENT_CLASSES]
            if classes:
                return f' class="{" ".join(classes)}"'

        if attr_name in {"data-description", "data-image-slot"}:
            return match.group(0)

        return ""

    return re.sub(
        r'\s(?P<name>class|style|data-[\w-]+)="(?P<value>[^"]*)"',
        replace,
        html,
        flags=re.IGNORECASE,
    )


def clean_article_html(
    raw_html,
    paypal_button_id,
    post_slug="",
    companion_guide=None,
    post_title="",
    article_section_title="",
):
    html = clean_wordpress_html(raw_html, paypal_button_id)
    html = rewrite_article_subscribe_links(html)
    # The 2026 fasting feature uses semantic figure markup from its approved
    # editorial package; its first inline figure is not a legacy hero to strip.
    if post_slug != "intermittent-fasting-diabetes-2026":
        html = remove_article_media(html)
    html = remove_duplicate_intro_heading(html, post_title, article_section_title)
    if post_slug == "memovela":
        html = update_memovela_article_html(html)
    elif post_slug == "summer-walks-hydration-diabetes":
        html = update_summer_walks_memovela_html(html)
    elif post_slug == "otc-cgm-children-stelo-family-guide":
        html = update_pediatric_cgm_memovela_html(html)
    if companion_guide:
        html = remove_companion_article_distractions(html)
    else:
        html = replace_imported_donation_blocks(html, paypal_button_id)
        html = replace_imported_wellness_tools_blocks(html)
        html = promote_chicago_marathon_figure(html)
    html = remove_empty_figures(html)
    html = wrap_article_tables(html)
    html = wrap_article_sections(html)
    if companion_guide:
        html = add_fats_article_heading_ids(html)
        html = insert_companion_guide_cta(html, companion_guide)
    return html


def normalized_heading_text(value):
    text = html_lib.unescape(value or "").strip().lower()
    text = re.sub(r"[\u2018\u2019]", "'", text)
    text = re.sub(r"[\u201c\u201d]", '"', text)
    text = re.sub(r"&", " and ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def headings_match(first_heading, post_title):
    if not first_heading or not post_title:
        return False
    return normalized_heading_text(first_heading) == normalized_heading_text(post_title)


def remove_duplicate_intro_heading(html, post_title, article_section_title=""):
    duplicate_targets = [target for target in [post_title, article_section_title] if target]
    if not duplicate_targets:
        return html

    first_heading = re.search(
        r"(?P<prefix>^\s*)(?P<heading><h[1-4]\b[^>]*>(?P<content>.*?)</h[1-4]>)",
        html or "",
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not first_heading:
        return html

    heading_text = html_to_text(first_heading.group("content"))
    if not any(headings_match(heading_text, target) for target in duplicate_targets):
        return html

    return html[: first_heading.start("heading")] + html[first_heading.end("heading") :]


def memovela_app_store_badge_html(placement):
    placement = escape(placement)
    app_store_url = escape(memovela_links.MEMOVELA_APP_STORE_URL)
    return f"""
    <a class="app-store-badge" href="{app_store_url}" target="_blank" rel="noopener noreferrer" aria-label="Download Memovela on the App Store" data-track-event="memovela_app_store_click" data-track-category="health_tool" data-track-label="Download Memovela on the App Store" data-track-id="memovela-app-store-{placement}" data-track-position="{placement}" data-track-destination="{app_store_url}" data-tool-id="memovela" data-tool-name="Memovela" data-tool-slug="memovela" data-tool-destination-type="app_store" data-cta-position="{placement}">
      <img src="/static/img/download-on-the-app-store.svg" alt="Download Memovela on the App Store" width="120" height="40" loading="lazy">
    </a>
    """


def memovela_web_link_html(label, placement, css_class="button-secondary", track_id="memovela-web"):
    label = escape(label)
    placement = escape(placement)
    css_class = escape(css_class)
    track_id = escape(track_id)
    web_url = escape(memovela_links.MEMOVELA_WEB_URL)
    return f"""<a class="{css_class}" href="{web_url}" target="_blank" rel="noopener" data-track-event="memovela_web_click" data-track-category="health_tool" data-track-label="{label}" data-track-id="{track_id}" data-track-position="{placement}" data-track-destination="{web_url}" data-tool-id="memovela" data-tool-name="Memovela" data-tool-slug="memovela" data-tool-destination-type="web" data-cta-position="{placement}">{label}</a>"""


def update_memovela_article_html(html):
    intro_callout = f"""
    <aside class="memovela-inline-cta" aria-labelledby="memovela-app-availability">
      <p class="eyebrow">Now available on the App Store</p>
      <h2 id="memovela-app-availability">Memovela is available for iPhone and iPad.</h2>
      <p>The web version remains available from any compatible browser, so Android, desktop, and shared-device visitors still have a clear path.</p>
      <div class="memovela-inline-cta__actions">
        {memovela_app_store_badge_html("memovela_article")}
        {memovela_web_link_html("Use Memovela on the web", "memovela_article", track_id="memovela-article-web-intro")}
      </div>
    </aside>
    """
    html = re.sub(
        r"(<p>✨\s*<strong>Meet Memovela</strong>.*?</p>)",
        lambda match: match.group(1) + intro_callout,
        html,
        count=1,
        flags=re.IGNORECASE | re.DOTALL,
    )
    html = re.sub(
        r"<h2>Where Memovela Is Right Now \(and What’s Coming Next\).*?</h2>\s*"
        r"<p>Right now, Memovela is in an exciting early stage — it’s already usable, and we’re actively improving it week by week\.</p>",
        "<h2>Using Memovela Today</h2><p>Memovela is available on the App Store for iPhone and iPad, and the web version remains available for people using Android, desktop, or any compatible browser. We continue improving both paths so the habit-tracking experience stays simple and supportive.</p>",
        html,
        count=1,
        flags=re.IGNORECASE | re.DOTALL,
    )
    try_memovela = f"""
    <h3>✨ Try Memovela</h3>
    <p>Choose the path that fits your device: download the native iPhone/iPad app, or continue with the web version in your browser.</p>
    <div class="memovela-inline-cta memovela-inline-cta--compact" aria-label="Memovela download and web options">
      <div class="memovela-inline-cta__actions">
        {memovela_app_store_badge_html("memovela_article")}
        {memovela_web_link_html("Create your free account on the web", "memovela_article", track_id="memovela-article-web-account")}
        <a class="text-link" href="{escape(memovela_links.MEMOVELA_WEB_URL)}login" target="_blank" rel="noopener" data-track-event="memovela_web_click" data-track-category="health_tool" data-track-label="Log in to Memovela on the web" data-track-id="memovela-article-web-login" data-track-position="memovela_article" data-track-destination="{escape(memovela_links.MEMOVELA_WEB_URL)}login" data-tool-id="memovela" data-tool-name="Memovela" data-tool-slug="memovela" data-tool-destination-type="web" data-cta-position="memovela_article">Already have an account? Log in on the web</a>
      </div>
    </div>
    """
    html = re.sub(
        r"<h3>✨ Try Memovela</h3>\s*<ul\b[^>]*>.*?</ul>\s*<p><em>\(If you’re reading this on mobile: save it to your home screen and treat it like a tiny daily check-in\.\)</em></p>",
        try_memovela,
        html,
        count=1,
        flags=re.IGNORECASE | re.DOTALL,
    )
    html = re.sub(
        r"<p><strong>Try Memovela:</strong>\s*<a href=\"https://memovela\.com\">https://memovela\.com</a></p>",
        f"""<p><strong>Use Memovela on the web:</strong> <a href="{escape(memovela_links.MEMOVELA_WEB_URL)}" target="_blank" rel="noopener">memovela.com</a></p>""",
        html,
        count=1,
        flags=re.IGNORECASE,
    )
    return html


def update_summer_walks_memovela_html(html):
    replacement = f"""
    <aside class="article-wellness-tools" data-memovela-focus="true" aria-label="Memovela for walking and hydration habits">
      <div class="article-wellness-tools__intro">
        <p class="eyebrow">Make the habit easier to remember</p>
        <p class="article-wellness-tools__title">Track walks, hydration, and recovery with Memovela.</p>
        <p>Memovela helps you notice movement, water, meals, and body check-ins over time without turning a summer walk into another source of pressure.</p>
      </div>
      <div class="memovela-inline-cta__actions">
        {memovela_app_store_badge_html("blog_article")}
        {memovela_web_link_html("Use Memovela on the web", "blog_article", track_id="summer-walks-memovela-web")}
        <a class="text-link" href="/memovela/">Read about Memovela</a>
      </div>
    </aside>
    """
    pattern = (
        r"<div class=\"article-wellness-tools\" aria-label=\"Free wellness tools\">"
        r".*?<a href=\"/memovela/\">Read about Memovela</a>.*?"
        r"</div>\s*</div>"
    )
    html, count = re.subn(pattern, replacement, html, count=1, flags=re.IGNORECASE | re.DOTALL)
    if count:
        return html
    return html


def update_pediatric_cgm_memovela_html(html):
    replacement = f"""
    <aside class="article-wellness-tools" data-memovela-focus="true" aria-label="Memovela for routine notes">
      <div class="article-wellness-tools__intro">
        <p class="eyebrow">Track the question, not every number</p>
        <p class="article-wellness-tools__title">Use simple routine notes to support better conversations.</p>
        <p>When families are preparing for a clinician conversation, a short symptom note or routine log can sometimes be more helpful than reacting to every sensor point. For broader wellness journaling, Memovela is available on the App Store and on the web.</p>
      </div>
      <div class="memovela-inline-cta__actions">
        {memovela_app_store_badge_html("blog_article")}
        {memovela_web_link_html("Use Memovela on the web", "blog_article", track_id="pediatric-cgm-memovela-web")}
        <a class="text-link" href="/memovela/">Read about Memovela</a>
      </div>
    </aside>
    """
    return re.sub(
        r"<aside class=\"article-wellness-tools\">\s*<div class=\"article-wellness-tools__intro\">\s*"
        r"<p class=\"eyebrow\">Mindful Diabetes Tools</p>\s*"
        r"<h2 class=\"article-wellness-tools__title\">Track the Question, Not Every Number</h2>\s*"
        r"<p>When families are preparing for a clinician conversation.*?</p>\s*</div>\s*</aside>",
        replacement,
        html,
        count=1,
        flags=re.IGNORECASE | re.DOTALL,
    )


def remove_companion_article_distractions(html):
    html = re.sub(
        r"\s*<h[2-4]\b[^>]*>\s*[^<]*Join Us in Preventing Type 3 Diabetes\s*</h[2-4]>.*?"
        r"<form action=\"https://www\.paypal\.com/donate\".*?</form>",
        "",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    html = re.sub(
        r"\s*<figure>\s*<a\b[^>]*href=[\"']/chicago-marathon-diabetes/?[\"'][^>]*>\s*<img\b.*?</a>\s*"
        r"<figcaption>.*?raised over \$2,500.*?</figcaption>\s*</figure>\s*",
        "",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    html = re.sub(
        r"\s*<h[2-4]\b[^>]*>\s*(?:[^<]*?)Try Our Free Wellness Tools!\s*</h[2-4]>\s*"
        r"<p\b[^>]*>.*?</p>\s*(?:<a\b[^>]*>.*?</a>\s*){4}",
        "",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    html = re.sub(
        r"\s*<h[2-4]\b[^>]*>\s*[^<]*Continue Exploring.*",
        "",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return html


def add_fats_article_heading_ids(html):
    heading_ids = [
        (r"Understanding Fats", "understanding-dietary-fats"),
        (r"Saturated Fats: The Controversial Fat", "saturated-fats"),
        (r"Unsaturated Fats: The Heart-Healthy Fat", "unsaturated-fats"),
        (r"Trans Fats: The Harmful Fat", "trans-fats"),
        (r"Conclusion:", "practical-food-choices"),
    ]
    for heading_pattern, heading_id in heading_ids:
        html = add_id_to_matching_heading(html, heading_pattern, heading_id)
    return html


def add_id_to_matching_heading(html, heading_pattern, heading_id):
    matched = False

    def replace(match):
        nonlocal matched
        if matched:
            return match.group(0)
        attrs = match.group("attrs") or ""
        if re.search(r"\bid=", attrs, re.IGNORECASE):
            return match.group(0)
        heading_text = html_to_text(match.group("content"))
        if not re.search(heading_pattern, heading_text, re.IGNORECASE):
            return match.group(0)
        matched = True
        return f"<{match.group('tag')}{attrs} id=\"{heading_id}\">{match.group('content')}</{match.group('tag')}>"

    return re.sub(
        r"<(?P<tag>h[2-4])(?P<attrs>\b[^>]*)>(?P<content>.*?)</(?P=tag)>",
        replace,
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )


def insert_companion_guide_cta(html, companion_guide):
    cta_html = companion_guide_article_cta(companion_guide, "mid-article")
    pattern = (
        r"(?P<section><section\b[^>]*>\s*<h4\b[^>]*>\s*1\.3 Health Impacts and Dietary Recommendations\s*</h4>.*?</section>)"
    )
    inserted, count = re.subn(
        pattern,
        lambda match: match.group("section") + cta_html,
        html,
        count=1,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if count:
        return inserted
    return html


def companion_guide_article_cta(guide, position):
    guide_title = escape(guide["title"])
    guide_subtitle = escape(guide["subtitle"])
    guide_description = escape(guide["description"])
    detail_url = escape(guide["detail_url"])
    pdf_url = escape(guide["pdf_url"])
    cover_url = escape(guide["cover_url"])
    file_size = escape(guide.get("file_size") or "")
    return f"""
    <aside class="companion-guide-inline" aria-labelledby="companion-guide-inline-heading">
      <div class="companion-guide-inline__cover">
        <img src="{cover_url}" alt="Cover preview for {guide_title}.">
      </div>
      <div class="companion-guide-inline__copy">
        <p class="eyebrow">Want the practical version?</p>
        <h2 id="companion-guide-inline-heading">{guide_title}</h2>
        <p class="free-guide-subtitle">{guide_subtitle}</p>
        <p>{guide_description}</p>
        <ul>
          <li>Cooking-oil comparisons</li>
          <li>Food-label guidance</li>
          <li>Realistic meal swaps</li>
          <li>Printable fat-swap worksheet</li>
        </ul>
        <div class="free-guide-actions">
          <a class="button-primary" href="{detail_url}" data-track-event="resource_related_link_click" data-track-category="resource" data-track-label="Open {guide_title}" data-track-id="article-companion-{position}-{escape(guide['slug'])}" data-track-position="{position}" data-track-destination="{detail_url}" data-guide-title="{guide_title}" data-guide-slug="{escape(guide['slug'])}" data-guide-category="{escape(guide['category'])}" data-page-count="{escape(str(guide['page_count']))}" data-file-type="{escape(guide['file_type'])}" data-file-size="{file_size}" data-action="open-guide" data-button-location="{position}" data-source-page="/fats-guide/" data-track-impression="1">Open the Free Guide</a>
          <a class="button-secondary" href="{pdf_url}" target="_blank" rel="noopener noreferrer" data-track-event="resource_pdf_view" data-track-category="resource" data-track-label="View {guide_title}" data-track-id="article-companion-pdf-{position}-{escape(guide['slug'])}" data-track-position="{position}" data-track-destination="{pdf_url}" data-guide-title="{guide_title}" data-guide-slug="{escape(guide['slug'])}" data-guide-category="{escape(guide['category'])}" data-page-count="{escape(str(guide['page_count']))}" data-file-type="{escape(guide['file_type'])}" data-file-size="{file_size}" data-action="view" data-button-location="{position}" data-source-page="/fats-guide/">View PDF</a>
        </div>
      </div>
    </aside>
    """


def remove_empty_paragraphs(html):
    empty_paragraph = r"<p>\s*(?:&nbsp;|\u00a0|&#160;|<br\s*/?>)*\s*</p>"
    return re.sub(empty_paragraph, "", html, flags=re.IGNORECASE)


def remove_empty_list_items(html):
    empty_list_item = r"<li>\s*(?:&nbsp;|\u00a0|&#160;|<br\s*/?>)*\s*</li>"
    html = re.sub(empty_list_item, "", html, flags=re.IGNORECASE)
    return re.sub(r"<(ul|ol)>\s*</\1>", "", html, flags=re.IGNORECASE)


def remove_empty_figures(html):
    return re.sub(r"<figure>\s*</figure>", "", html, flags=re.IGNORECASE)


def wrap_article_tables(html):
    return re.sub(
        r"(<table\b.*?</table>)",
        r'<div class="article-table-wrap">\1</div>',
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )


def rewrite_upload_urls(html):
    return re.sub(
        r"https://mindfuldiabetes\.org/wp-content/uploads/",
        "/static/uploads/",
        html,
        flags=re.IGNORECASE,
    )


def rewrite_internal_href_attributes(html):
    def rewrite(match):
        quote = match.group("quote")
        url = match.group("url")
        parsed = urlparse(url)
        if parsed.netloc != "mindfuldiabetes.org":
            return match.group(0)
        new_url = parsed.path or "/"
        if parsed.query:
            new_url = f"{new_url}?{parsed.query}"
        if parsed.fragment:
            new_url = f"{new_url}#{parsed.fragment}"
        return f'href={quote}{new_url}{quote}'

    return re.sub(
        r'href=(?P<quote>["\'])(?P<url>https://mindfuldiabetes\.org[^"\']*)(?P=quote)',
        rewrite,
        html,
        flags=re.IGNORECASE,
    )


def rewrite_article_subscribe_links(html):
    def rewrite(match):
        attrs = match.group("attrs")
        label = html_to_text(match.group("label"))
        href_match = re.search(r'href=(?P<quote>["\'])(?P<href>.*?)(?P=quote)', attrs, re.IGNORECASE)
        if not href_match:
            return match.group(0)

        href = href_match.group("href").strip()
        if label.lower() != "subscribe":
            return match.group(0)
        if href not in {"/guide/", "/guide", "https://mindfuldiabetes.org/guide/", "https://www.mindfuldiabetes.org/guide/"}:
            return match.group(0)

        quote = href_match.group("quote")
        new_attrs = re.sub(
            r'href=(?P<quote>["\']).*?(?P=quote)',
            f"href={quote}#subscribe{quote}",
            attrs,
            count=1,
            flags=re.IGNORECASE,
        )
        new_attrs = re.sub(r"\s+target=(?P<quote>[\"']).*?(?P=quote)", "", new_attrs, flags=re.IGNORECASE)
        new_attrs = re.sub(r"\s+rel=(?P<quote>[\"']).*?(?P=quote)", "", new_attrs, flags=re.IGNORECASE)
        return f"<a{new_attrs}>{match.group('label')}</a>"

    return re.sub(
        r"<a(?P<attrs>\b[^>]*)>(?P<label>.*?)</a>",
        rewrite,
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )


def embed_bare_youtube_urls(html):
    def youtube_embed(match):
        raw_url = html_lib.unescape(match.group("url"))
        embed_url = youtube_url_to_embed(raw_url)
        if not embed_url:
            return match.group(0)

        return f"""
        <div class="video-frame">
          <iframe src="{embed_url}" title="Mindful Diabetes video" allowfullscreen></iframe>
        </div>
        """

    return re.sub(
        r"(?<![\"'=])(?P<url>https?://(?:www\.)?(?:youtu\.be/[^\s<]+|youtube\.com/watch\?[^\s<]+))",
        youtube_embed,
        html,
        flags=re.IGNORECASE,
    )


def wrap_media_iframes(html):
    def iframe_wrapper(match):
        iframe_html = match.group(0)
        if "youtube.com/embed" not in iframe_html.lower() and "player.vimeo.com" not in iframe_html.lower():
            return iframe_html
        return f'<div class="video-frame">{iframe_html}</div>'

    return re.sub(r"<iframe\b.*?</iframe>", iframe_wrapper, html, flags=re.IGNORECASE | re.DOTALL)


def remove_article_media(html):
    html = re.sub(r"\s*<img\b[^>]*>\s*", "", html, count=1, flags=re.IGNORECASE | re.DOTALL)
    html = re.sub(
        r"\s*<h[2-4]\b[^>]*>\s*(?:want|prefer)[^<]*listen[^<]*</h[2-4]>\s*",
        "",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    html = re.sub(r"\s*<audio\b.*?</audio>\s*", "", html, flags=re.IGNORECASE | re.DOTALL)
    html = re.sub(
        r"\s*<div class=\"video-frame\">\s*<iframe\b.*?</iframe>\s*</div>\s*",
        "",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return html


def replace_imported_donation_blocks(html, paypal_button_id):
    replacement = f"""
    <div class="article-callout">
      <p class="article-callout__title">Support prevention education</p>
      <p>Your gift supports Mindful Diabetes education, tools, and prevention-focused community work.</p>
      {paypal_form(paypal_button_id)}
    </div>
    """
    html = re.sub(
        r"\s*<h[2-4]\b[^>]*>\s*[^<]*Join Us in Preventing Type 3 Diabetes\s*</h[2-4]>.*?"
        r"<form action=\"https://www\.paypal\.com/donate\".*?</form>",
        replacement,
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return html


def replace_imported_wellness_tools_blocks(html):
    return re.sub(
        r"\s*<h[2-4]\b[^>]*>\s*(?:[^<]*?)Try Our Free Wellness Tools!\s*</h[2-4]>\s*"
        r"<p\b[^>]*>.*?</p>\s*(?:<a\b[^>]*>.*?</a>\s*){4}",
        wellness_tools_panel(),
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )


def promote_chicago_marathon_figure(html):
    pattern = (
        r"\s*<figure>\s*"
        r"(?P<media><a\b[^>]*href=[\"']/chicago-marathon-diabetes/?[\"'][^>]*>\s*<img\b.*?</a>)\s*"
        r"<figcaption>(?P<caption>.*?raised over \$2,500.*?</figcaption>)\s*"
        r"</figure>\s*"
    )

    def replacement(match):
        media_html = match.group("media").strip()
        caption_html = re.sub(
            r"</?figcaption\b[^>]*>",
            "",
            match.group("caption"),
            flags=re.IGNORECASE,
        )
        caption_text = html_lib.unescape(html_to_text(caption_html))
        return f"""
        <aside class="article-impact-card" aria-label="Chicago Marathon community impact">
          <div class="article-impact-card__media">
            {media_html}
          </div>
          <div class="article-impact-card__copy">
            <p class="eyebrow">Community impact</p>
            <p class="article-impact-card__title">Chicago Marathon Diabetes Project</p>
            <p>{escape(caption_text)}</p>
            <a class="article-impact-card__link" href="/chicago-marathon-diabetes/">Read the marathon story</a>
          </div>
        </aside>
        """

    return re.sub(pattern, replacement, html, count=1, flags=re.IGNORECASE | re.DOTALL)


def wellness_tools_panel():
    return f"""
    <div class="article-wellness-tools" aria-label="Free wellness tools">
      <div class="article-wellness-tools__intro">
        <p class="eyebrow">Free wellness tools</p>
        <p class="article-wellness-tools__title">Choose a tool for your next healthy step</p>
        <p>Explore AI-guided learning, daily habit tracking, and a playful nutrition game built around Mindful Diabetes prevention education.</p>
      </div>
      <div class="article-wellness-tools__grid">
        <a class="article-tool-card article-tool-card--jeir" href="https://www.mindfuldiabetes.ai/" target="_blank" rel="noopener" data-track-event="health_tool_click" data-track-category="health_tool" data-track-label="JEIR" data-track-id="imported-wellness-jeir" data-track-position="imported-wellness-tools" data-tool-id="jeir" data-tool-name="JEIR" data-tool-slug="jeir" data-tool-destination-type="external" data-track-impression="1">
          <span>JEIR</span>
          <strong>AI Wellness Guide</strong>
          <small>Ask clearer questions about blood sugar, insulin resistance, and brain health.</small>
        </a>
        <a class="article-tool-card article-tool-card--memovela" href="{memovela_links.MEMOVELA_WEB_URL}" target="_blank" rel="noopener" data-track-event="memovela_web_click" data-track-category="health_tool" data-track-label="Memovela" data-track-id="imported-wellness-memovela" data-track-position="imported-wellness-tools" data-track-destination="{memovela_links.MEMOVELA_WEB_URL}" data-tool-id="memovela" data-tool-name="Memovela" data-tool-slug="memovela" data-tool-destination-type="web" data-track-impression="1">
          <span>Memovela</span>
          <strong>Wellness Tracker</strong>
          <small>Build repeatable habits around movement, meals, sleep, hydration, and check-ins.</small>
        </a>
        <a class="article-tool-card article-tool-card--game" href="https://www.jeir.fun/" target="_blank" rel="noopener" data-track-event="health_tool_click" data-track-category="health_tool" data-track-label="Mindful Eating Game" data-track-id="imported-wellness-game" data-track-position="imported-wellness-tools" data-tool-id="mindful-eating-game" data-tool-name="Mindful Eating Game" data-tool-slug="healthy-eating" data-tool-destination-type="external" data-track-impression="1">
          <span>Game</span>
          <strong>Mindful Eating Game</strong>
          <small>Play a quick nutrition game and make healthy choices feel more memorable.</small>
        </a>
      </div>
      <div class="article-wellness-tools__resources">
        <a href="/memovela/">Read about Memovela</a>
        <a href="/healthy-eating/">Read about the game</a>
        <a href="/diabetes-artificial-intelligence-jeir/">Read about JEIR AI</a>
      </div>
      <div class="article-wellness-tools__app" aria-label="Download Memovela">
        <div>
          <p class="eyebrow">Daily habits app</p>
          <p>Want one simple place to practice the habits in this article? Memovela is available on the App Store and on the web.</p>
        </div>
        <div class="memovela-inline-cta__actions">
          {memovela_app_store_badge_html("blog_article")}
          {memovela_web_link_html("Use Memovela on the web", "blog_article", track_id="wellness-panel-memovela-web")}
        </div>
      </div>
    </div>
    """


def wrap_article_sections(html):
    heading_ranges = top_level_heading_ranges(html)
    if not heading_ranges:
        return html

    groups = []
    leading = html[: heading_ranges[0][0]].strip()
    if html_to_text(leading) or re.search(r"<(?:img|iframe|audio|table)\b", leading, re.IGNORECASE):
        groups.append(leading)

    for index, (start, end) in enumerate(heading_ranges):
        next_start = heading_ranges[index + 1][0] if index + 1 < len(heading_ranges) else len(html)
        group = html[start:next_start].strip()
        if group:
            groups.append(group)

    if not groups:
        return html

    variants = ["article-section--green", "article-section--orange", "article-section--white"]
    wrapped = []
    for index, group in enumerate(groups):
        text_length = len(html_to_text(group))
        has_rich_content = re.search(r"<(?:img|iframe|audio|table|form)\b", group, re.IGNORECASE)
        if text_length < 120 and not has_rich_content:
            wrapped.append(group)
            continue
        wrapped.append(f'<section class="article-section {variants[index % len(variants)]}">{group}</section>')

    return "\n".join(wrapped)


def top_level_heading_ranges(html):
    ranges = []
    container_depth = 0
    token_pattern = re.compile(
        r"(?P<heading><h[2-4]\b[^>]*>.*?</h[2-4]>)|"
        r"(?P<tag></?(?:aside|blockquote|div|figure|form|ol|section|table|ul)\b[^>]*>)",
        flags=re.IGNORECASE | re.DOTALL,
    )

    for match in token_pattern.finditer(html):
        heading_html = match.group("heading")
        if heading_html:
            if container_depth == 0:
                ranges.append((match.start(), match.end()))
            continue

        tag_html = match.group("tag").lower()
        if tag_html.startswith("</"):
            container_depth = max(0, container_depth - 1)
        else:
            container_depth += 1

    return ranges


def paypal_form(paypal_button_id):
    button_id = escape(paypal_button_id)
    return f"""
    <form class="paypal-donation-form" action="https://www.paypal.com/donate" method="post" target="_blank" data-track-event="paypal_click" data-track-category="donation" data-track-label="Donate with PayPal" data-track-id="wordpress-paypal-donate" data-track-position="imported-content" data-track-destination="https://www.paypal.com/donate" data-provider="paypal" data-campaign-id="general-support" data-track-impression="1">
      <input type="hidden" name="hosted_button_id" value="{button_id}">
      <button class="donate-button" type="submit">Donate with PayPal</button>
    </form>
    """


def donation_receipt_message(paypal_button_id):
    return f"""
    <div class="notice">
      <p>Thank you for supporting Mindful Diabetes Inc. PayPal will send the official donation confirmation after processing.</p>
      {paypal_form(paypal_button_id)}
    </div>
    """


def donor_dashboard_message(paypal_button_id):
    return f"""
    <div class="notice">
      <p>The old WordPress donor dashboard has been retired. Future donation management should happen through PayPal.</p>
      {paypal_form(paypal_button_id)}
    </div>
    """


def html_to_text(raw_html):
    text = re.sub(r"<script\b[^>]*>.*?</script>", " ", raw_html, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<style\b[^>]*>.*?</style>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\[[^\]]+\]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def searchable_content_text(raw_html):
    text = html_to_text(raw_html)
    boilerplate_markers = [
        r"Interested in staying up to date",
        r"Try Our Free Wellness Tools",
        r"Join Us in Preventing Type 3 Diabetes",
        r"Check out our Shop",
        r"Donate Now",
    ]
    for marker in boilerplate_markers:
        text = re.split(marker, text, maxsplit=1, flags=re.IGNORECASE)[0]
    return text


app = create_app()
