import json
import html as html_lib
import hashlib
import os
import random
import re
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flask import Flask, abort, redirect, render_template, request, url_for
from markupsafe import Markup, escape


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_CONTENT_PATH = (
    BASE_DIR
    / "mindful_diabetes_wp_parse_outputs"
    / "wp_migration_outputs"
    / "flask_content_seed.json"
)


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

    content = load_content(Path(app.config["CONTENT_PATH"]))
    app.config["CONTENT"] = content

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
    html = re.sub(r"\s(?:class|style|data-[\w-]+)=\"[^\"]*\"", "", html)
    html = wrap_media_iframes(html)
    html = re.sub(r"\[give_form[^\]]*\]", paypal_form(paypal_button_id), html, flags=re.IGNORECASE)
    html = re.sub(r"\[give_receipt[^\]]*\]", donation_receipt_message(paypal_button_id), html, flags=re.IGNORECASE)
    html = re.sub(r"\[give_donor_dashboard[^\]]*\]", donor_dashboard_message(paypal_button_id), html, flags=re.IGNORECASE)
    html = embed_bare_youtube_urls(html)
    html = remove_empty_paragraphs(html)
    html = remove_empty_list_items(html)
    html = re.sub(r"<iframe\b", '<iframe loading="lazy"', html, flags=re.IGNORECASE)
    return html


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
