import json
import html as html_lib
import hmac
import hashlib
import os
import random
import re
import secrets
from datetime import datetime, timedelta, timezone
from functools import wraps
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flask import Flask, abort, redirect, render_template, request, session, url_for
from markupsafe import Markup, escape

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
PRESERVED_CONTENT_CLASSES = {
    "article-image-placeholder",
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

    @app.context_processor
    def inject_site_data():
        return {
            "nav_pages": content.nav_pages,
            "paypal_button_id": app.config["PAYPAL_HOSTED_BUTTON_ID"],
            "site_description": app.config["SITE_DESCRIPTION"],
            "newsletter_enabled": is_mailchimp_configured(app.config),
            "turnstile_site_key": (
                app.config["TURNSTILE_SITE_KEY"] if is_turnstile_configured(app.config) else ""
            ),
        }

    @app.template_filter("date_label")
    def date_label(value):
        return format_date(value)

    @app.template_filter("wordpress_html")
    def wordpress_html(value):
        return Markup(clean_wordpress_html(value or "", app.config["PAYPAL_HOSTED_BUTTON_ID"]))

    @app.template_filter("article_html")
    def article_html(value, post_slug=""):
        return Markup(
            clean_article_html(
                value or "",
                app.config["PAYPAL_HOSTED_BUTTON_ID"],
                post_slug=post_slug,
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

    def admin_required(view):
        @wraps(view)
        def wrapped_view(*args, **kwargs):
            if normalize_email(session.get("admin_email")) != normalize_email(app.config["ADMIN_EMAIL"]):
                return redirect(url_for("admin_login", next=request.path))
            return view(*args, **kwargs)

        return wrapped_view

    @app.after_request
    def track_public_activity(response):
        if should_track_request(response):
            record_activity_event(
                app.config,
                "page_view",
                request.path,
                title_for_request(content, request.endpoint, request.view_args or {}),
                {
                    "query": public_query_args(request.args),
                    "referrer": request.referrer or "",
                    "user_agent": (request.user_agent.string or "")[:240],
                },
            )
        return response

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
            ],
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

        record_activity_event(
            app.config,
            "newsletter_signup",
            request.path,
            "Newsletter signup",
            {
                "source": source,
                "email_domain": email.rsplit("@", 1)[1].lower() if "@" in email else "",
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
        dashboard = build_admin_dashboard(app.config)
        return render_template("admin_dashboard.html", dashboard=dashboard, admin_email=app.config["ADMIN_EMAIL"])

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
            related_posts = [item for item in content.latest_posts if item["slug"] != slug][:3]
            article_navigation = navigation_for_post(content.latest_posts, slug)
            return render_template(
                "post.html",
                post=post,
                related_posts=related_posts,
                article_navigation=article_navigation,
            )

        abort(404)

    @app.get("/<slug>")
    def page_detail_no_slash(slug):
        return redirect(url_for("page_detail", slug=slug), code=301)

    return app


class ContentIndex:
    def __init__(self, items):
        nav_order = {"mindful": 0, "guide": 1, "sponsors": 2, "donation": 3}
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
        self.nav_pages.insert(2, research_nav_page)
        self.nav_pages.insert(2, health_tools_nav_page)


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
        item["article_section_title"] = article_section_title_for(item.get("content_html", "")) or item.get("title", "")
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


def article_section_title_for(raw_html):
    for match in re.finditer(r"<h[1-4]\b[^>]*>(.*?)</h[1-4]>", raw_html or "", re.IGNORECASE | re.DOTALL):
        heading = html_to_text(match.group(1))
        if re.search(r"\b(?:want|prefer)\b.*\blisten\b", heading, re.IGNORECASE):
            continue
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
    api_key = config.get("BREVO_API_KEY") or ""
    if not api_key:
        return False, "Brevo email is not configured yet. Add BREVO_API_KEY in Heroku Config Vars."

    sender = parse_email_identity(config.get("ADMIN_EMAIL_FROM"))
    payload = {
        "sender": sender,
        "to": [{"email": email}],
        "subject": "Your Mindful Diabetes admin code",
        "textContent": (
            f"Your Mindful Diabetes admin code is {code}. "
            f"It expires in {ADMIN_CODE_TTL_MINUTES} minutes."
        ),
        "htmlContent": (
            "<p>Your Mindful Diabetes admin code is:</p>"
            f"<p style=\"font-size:28px;font-weight:700;letter-spacing:4px;\">{code}</p>"
            f"<p>This code expires in {ADMIN_CODE_TTL_MINUTES} minutes.</p>"
        ),
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


def build_admin_dashboard(config):
    events = fetch_admin_events(config)
    now = utc_now()
    since_7_days = now - timedelta(days=7)
    today = now.date()
    page_views = [event for event in events if event["event_type"] == "page_view"]
    newsletter_signups = [event for event in events if event["event_type"] == "newsletter_signup"]
    admin_logins = [event for event in events if event["event_type"] == "admin_login"]
    today_events = [event for event in events if event["created_at"].date() == today]
    recent_page_views = [event for event in page_views if event["created_at"] >= since_7_days]

    path_counts = {}
    for event in page_views:
        path_counts[event["path"]] = path_counts.get(event["path"], 0) + 1

    top_paths = [
        {"path": path, "count": count}
        for path, count in sorted(path_counts.items(), key=lambda item: (-item[1], item[0]))[:8]
    ]

    return {
        "storage_backend": config.get("ADMIN_STORAGE_BACKEND") or "local file",
        "stats": [
            {"label": "Visits tracked", "value": len(page_views)},
            {"label": "Last 7 days", "value": len(recent_page_views)},
            {"label": "Newsletter signups", "value": len(newsletter_signups)},
            {"label": "Today", "value": len(today_events)},
        ],
        "admin_login_count": len(admin_logins),
        "top_paths": top_paths,
        "recent_events": events[:30],
        "next_widgets": [
            "Donation and PayPal click tracking",
            "Newsletter source trends",
            "Most-read article groups",
            "Health-tool outbound clicks",
            "Weekly email summary to the admin",
        ],
    }


def should_track_request(response):
    tracked_endpoints = {
        "home",
        "guide",
        "search",
        "pages_index",
        "research",
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
    if endpoint == "page_detail":
        slug = (view_args or {}).get("slug", "")
        item = content.pages_by_slug.get(slug) or content.posts_by_slug.get(slug)
        return item.get("title", slug) if item else slug
    return endpoint or ""


def public_query_args(args):
    return {key: args.get(key, "") for key in ("q", "page") if args.get(key)}


def safe_admin_next_url(raw_url):
    url = raw_url or "/admin/"
    if not url.startswith("/") or url.startswith("//"):
        return "/admin/"
    if not url.startswith("/admin/"):
        return "/admin/"
    return url


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


def clean_article_html(raw_html, paypal_button_id, post_slug=""):
    html = clean_wordpress_html(raw_html, paypal_button_id)
    html = rewrite_article_subscribe_links(html)
    html = remove_article_media(html)
    html = replace_imported_donation_blocks(html, paypal_button_id)
    html = replace_imported_wellness_tools_blocks(html)
    html = promote_chicago_marathon_figure(html)
    html = remove_empty_figures(html)
    html = wrap_article_sections(html)
    return html


def remove_empty_paragraphs(html):
    empty_paragraph = r"<p>\s*(?:&nbsp;|\u00a0|&#160;|<br\s*/?>)*\s*</p>"
    return re.sub(empty_paragraph, "", html, flags=re.IGNORECASE)


def remove_empty_list_items(html):
    empty_list_item = r"<li>\s*(?:&nbsp;|\u00a0|&#160;|<br\s*/?>)*\s*</li>"
    html = re.sub(empty_list_item, "", html, flags=re.IGNORECASE)
    return re.sub(r"<(ul|ol)>\s*</\1>", "", html, flags=re.IGNORECASE)


def remove_empty_figures(html):
    return re.sub(r"<figure>\s*</figure>", "", html, flags=re.IGNORECASE)


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
    return """
    <div class="article-wellness-tools" aria-label="Free wellness tools">
      <div class="article-wellness-tools__intro">
        <p class="eyebrow">Free wellness tools</p>
        <p class="article-wellness-tools__title">Choose a tool for your next healthy step</p>
        <p>Explore AI-guided learning, daily habit tracking, and a playful nutrition game built around Mindful Diabetes prevention education.</p>
      </div>
      <div class="article-wellness-tools__grid">
        <a class="article-tool-card article-tool-card--jeir" href="https://www.mindfuldiabetes.ai/" target="_blank" rel="noopener">
          <span>JEIR</span>
          <strong>AI Wellness Guide</strong>
          <small>Ask clearer questions about blood sugar, insulin resistance, and brain health.</small>
        </a>
        <a class="article-tool-card article-tool-card--memovela" href="https://memovela.com/" target="_blank" rel="noopener">
          <span>Memovela</span>
          <strong>Wellness Tracker</strong>
          <small>Build repeatable habits around movement, meals, sleep, hydration, and check-ins.</small>
        </a>
        <a class="article-tool-card article-tool-card--game" href="https://www.jeir.fun/" target="_blank" rel="noopener">
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
    list_depth = 0
    token_pattern = re.compile(
        r"(?P<heading><h[2-4]\b[^>]*>.*?</h[2-4]>)|(?P<tag></?(?:ul|ol)\b[^>]*>)",
        flags=re.IGNORECASE | re.DOTALL,
    )

    for match in token_pattern.finditer(html):
        heading_html = match.group("heading")
        if heading_html:
            if list_depth == 0:
                ranges.append((match.start(), match.end()))
            continue

        tag_html = match.group("tag").lower()
        if tag_html.startswith("</"):
            list_depth = max(0, list_depth - 1)
        else:
            list_depth += 1

    return ranges


def paypal_form(paypal_button_id):
    button_id = escape(paypal_button_id)
    return f"""
    <form class="paypal-donation-form" action="https://www.paypal.com/donate" method="post" target="_blank">
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
