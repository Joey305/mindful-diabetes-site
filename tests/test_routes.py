import json
from importlib import import_module

from mindful_diabetes import create_app


app_module = import_module("mindful_diabetes.app")


class StubUrlopenResponse:
    def __init__(self, status=200, body=b"{}"):
        self.status = status
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self):
        return self.body


def test_published_wordpress_pages_and_posts_resolve():
    app = create_app({"TESTING": True})
    client = app.test_client()
    content = app.config["CONTENT"]

    expected_items = content.published_pages + content.latest_posts

    assert len(content.published_pages) == 8
    assert len(content.latest_posts) == 93

    for item in expected_items:
        response = client.get(item["canonical_path"])
        assert response.status_code == 200, item["canonical_path"]


def test_wordpress_home_slug_redirects_to_root():
    app = create_app({"TESTING": True})
    client = app.test_client()

    response = client.get("/mindful/")

    assert response.status_code == 301
    assert response.headers["Location"].endswith("/")


def test_givewp_shortcode_is_replaced_by_paypal():
    app = create_app({"TESTING": True})
    client = app.test_client()

    response = client.get("/donation/")

    assert response.status_code == 200
    assert b"Donate with PayPal" in response.data
    assert b"Help without donating" in response.data
    assert b"Share your time or skills" in response.data
    assert b'href="/volunteer/"' in response.data
    assert b"[give_form" not in response.data


def test_donation_page_emphasizes_paypal_cta():
    app = create_app({"TESTING": True})
    client = app.test_client()
    css = (app_module.BASE_DIR / "static" / "css" / "site.css").read_text(encoding="utf-8")

    response = client.get("/donation/")

    assert response.status_code == 200
    assert b'class="paypal-donation-form"' in response.data
    assert b'class="donate-button"' in response.data
    assert ".page-donation .paypal-donation-form" in css
    assert ".page-donation .paypal-donation-form .donate-button" in css
    assert "Secure PayPal donation" in css


def test_uploaded_media_urls_are_local_static_assets():
    app = create_app({"TESTING": True})
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert b'src="/static/uploads/' in response.data
    assert b"https://mindfuldiabetes.org/wp-content/uploads/" not in response.data


def test_footer_links_to_all_social_channels():
    app = create_app({"TESTING": True})
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert b"Follow Us" in response.data
    assert b"social-link-row--footer" in response.data
    assert b"https://www.facebook.com/profile.php?id=61551356473510" in response.data
    assert b"https://www.instagram.com/mindfuldiabetesinc/" in response.data
    assert b"https://www.youtube.com/channel/UCrh06dTVO4bnUMFEgBj6p0g" in response.data
    assert b"https://www.tiktok.com/@mindfuldiabetesinc" in response.data
    assert b"https://www.linkedin.com/company/mindful-diabetes-inc" in response.data
    assert b"YouTube" in response.data
    assert b"LinkedIn" in response.data


def test_subscribe_links_scroll_to_footer_form_on_current_page():
    app = create_app({"TESTING": True})
    client = app.test_client()

    response = client.get("/memovela/")

    assert response.status_code == 200
    assert b'id="subscribe"' in response.data
    assert b'href="#subscribe"' in response.data
    assert b'href="#subscribe" target="_blank"' not in response.data
    assert b'href="/guide/">Subscribe</a>' not in response.data


def test_mobile_menu_and_guide_signup_are_available():
    app = create_app({"TESTING": True})
    client = app.test_client()

    response = client.get("/guide/")
    css = (app_module.BASE_DIR / "static" / "css" / "site.css").read_text(encoding="utf-8")

    assert response.status_code == 200
    assert b'class="mobile-menu"' in response.data
    assert b'class="mobile-nav"' in response.data
    assert b'id="guide-subscribe"' in response.data
    assert b"Stay close to the newest prevention guides." in response.data
    assert ".mobile-menu" in css
    assert ".guide-signup .social-link-row" in css


def test_homepage_restores_key_original_sections():
    app = create_app({"TESTING": True})
    client = app.test_client()
    first_post = app.config["CONTENT"].latest_posts[0]

    response = client.get("/")

    assert response.status_code == 200
    assert response.data.count(b'class="mission-card"') == 3
    assert b"https://www.youtube.com/embed/ixqrtPd0E7s" in response.data
    assert b"https://memovela.com" in response.data
    assert b"Featured fundraiser" in response.data
    assert b"Turn a story into prevention research." in response.data
    assert b"100% of sales donated" in response.data
    assert b'class="post-card guide-post-card home-post-card"' in response.data
    assert first_post["preview_image_url"].encode() in response.data


def test_guide_paginates_posts_nine_at_a_time():
    app = create_app({"TESTING": True})
    client = app.test_client()

    first_page = client.get("/guide/")
    second_page = client.get("/guide/?page=2")
    missing_page = client.get("/guide/?page=999")

    assert first_page.status_code == 200
    assert second_page.status_code == 200
    assert missing_page.status_code == 404
    assert first_page.data.count(b'class="post-card guide-post-card"') == 9
    assert second_page.data.count(b'class="post-card guide-post-card"') == 9
    assert b'aria-current="page">1</span>' in first_page.data
    assert b'href="/guide/?page=2"' in first_page.data


def test_guide_uses_restored_pathways_layout():
    app = create_app({"TESTING": True})
    client = app.test_client()

    response = client.get("/guide/")

    assert response.status_code == 200
    assert b"Guide: Pathways to Wellness" in response.data
    assert b"Type 3 Diabetes Guide:" in response.data
    assert b"BLOG-COVER2-768x494.png" in response.data
    assert b"Our Guide's 3 Prong Approach" in response.data
    assert b"Recent Posts" in response.data
    assert b"social-link--tiktok" in response.data
    assert b"https://www.tiktok.com/@mindfuldiabetesinc" in response.data
    assert b"Unsure" not in response.data


def test_guide_cards_show_images_and_full_excerpts():
    app = create_app({"TESTING": True})
    client = app.test_client()
    first_post = app.config["CONTENT"].latest_posts[0]

    response = client.get("/guide/")

    assert response.status_code == 200
    assert b'class="post-card guide-post-card"' in response.data
    assert b'class="guide-post-card__image"' in response.data
    assert first_post["preview_image_url"].encode() in response.data
    assert first_post["preview_image_url"].startswith("/static/uploads/")
    assert first_post["excerpt_text"].encode() in response.data
    assert len(first_post["excerpt_text"]) > 220
    assert b"Read More" in response.data


def test_sponsors_page_uses_custom_presentational_layout():
    app = create_app({"TESTING": True})
    client = app.test_client()

    response = client.get("/sponsors/")

    assert response.status_code == 200
    assert b'class="sponsors-hero"' in response.data
    assert response.data.count(b'class="sponsor-logo-card"') == 3
    assert b"Smart Door Solution" in response.data
    assert b"Citrus Sculpt" in response.data
    assert b"JSM Cooperative" in response.data
    assert b"Meet the Founder" in response.data
    assert response.data.count(b'class="featured-article-card"') == 3
    assert b"Help without donating" in response.data
    assert b"Share your time or skills" in response.data
    assert b'href="/volunteer/"' in response.data


def test_research_page_lists_orcid_publications():
    app = create_app({"TESTING": True})
    client = app.test_client()

    response = client.get("/research/")

    assert response.status_code == 200
    assert b"Active research across diabetes" in response.data
    assert b"https://orcid.org/0000-0001-7276-1835" in response.data
    assert response.data.count(b'class="publication-card"') == 8
    assert b"Dynamic scRNA-seq of live human pancreatic slices" in response.data
    assert b"The Potential of Induced Pluripotent Stem Cells" in response.data
    assert b"https://doi.org/10.1155/2021/5511630" in response.data


def test_home_links_research_page_and_nav_promotes_it():
    app = create_app({"TESTING": True})
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert b'href="/research/"' in response.data
    assert b"View Our Research" in response.data
    assert b">Research</a>" in response.data
    assert b'href="/health-tools/"' in response.data
    assert b">Health Tools</a>" in response.data


def test_jeir_article_uses_pilot_layout():
    app = create_app({"TESTING": True})
    client = app.test_client()

    response = client.get("/diabetes-health-jeir-updates/")

    assert response.status_code == 200
    assert b"post-pilot post-diabetes-health-jeir-updates" in response.data
    assert b'class="article-post-hero"' in response.data
    assert b"MindfulDiabetes.ai Has Leveled Up" in response.data
    assert b"https://www.mindfuldiabetes.ai/" in response.data
    assert b"https://www.youtube.com/embed/aOk3eEcSQGo" not in response.data
    assert b"https://youtu.be/aOk3eEcSQGo" not in response.data
    assert b"Join Us in Preventing Type 3 Diabetes" not in response.data
    assert b"<li>\xc2\xa0</li>" not in response.data
    assert b"<ul></ul>" not in response.data
    assert response.data.count(b'class="article-sidebar-card"') == 4
    assert b"Follow Mindful Diabetes" in response.data
    assert b"social-link--youtube" in response.data
    assert b"social-link--tiktok" in response.data
    assert b"https://www.tiktok.com/@mindfuldiabetesinc" in response.data
    assert b'class="article-impact-card"' in response.data
    assert b"Chicago Marathon Diabetes Project" in response.data
    assert b"Read the marathon story" in response.data


def test_health_tools_page_showcases_all_three_tools():
    app = create_app({"TESTING": True})
    client = app.test_client()
    posts = app.config["CONTENT"].posts_by_slug

    response = client.get("/health-tools/")

    assert response.status_code == 200
    assert b"Practical tools for blood sugar, brain health, and everyday habits" in response.data
    assert b"JEIR, your AI wellness guide" in response.data
    assert b"Memovela for metabolic and brain health" in response.data
    assert b"Mindful Eating Game" in response.data
    assert b"https://www.mindfuldiabetes.ai/" in response.data
    assert b"https://memovela.com/" in response.data
    assert b"https://www.jeir.fun/" in response.data
    assert posts["diabetes-health-jeir-updates"]["preview_image_url"].encode() in response.data
    assert posts["memovela"]["preview_image_url"].encode() in response.data
    assert posts["healthy-eating"]["preview_image_url"].encode() in response.data
    assert b"Health Tools Hub" in response.data


def test_volunteer_page_is_footer_only_and_linked_from_support():
    app = create_app({"TESTING": True})
    client = app.test_client()

    home = client.get("/")
    volunteer = client.get("/volunteer/")

    assert home.status_code == 200
    assert volunteer.status_code == 200
    assert b'href="/volunteer/"' in home.data
    assert b"Volunteer with Mindful Diabetes" in volunteer.data
    assert b"Guide writing and editing" in volunteer.data
    assert b"Tool testing and feedback" in volunteer.data
    assert b"Email us to volunteer" in volunteer.data
    assert b">Volunteer</a>" in volunteer.data

    header_html = home.data.split(b"</header>", 1)[0]
    footer_html = home.data.split(b"<footer", 1)[1]
    assert b'href="/volunteer/"' not in header_html
    assert b'href="/volunteer/"' in footer_html


def test_search_finds_research_page_publications():
    app = create_app({"TESTING": True})
    client = app.test_client()

    response = client.get("/search/?q=PROTAC")

    assert response.status_code == 200
    assert b"Research" in response.data
    assert b"/research/" in response.data


def test_search_finds_health_tools_page():
    app = create_app({"TESTING": True})
    client = app.test_client()

    response = client.get("/search/?q=Memovela%20JEIR%20game")

    assert response.status_code == 200
    assert b"Health Tools" in response.data
    assert b"/health-tools/" in response.data


def test_search_finds_volunteer_page():
    app = create_app({"TESTING": True})
    client = app.test_client()

    response = client.get("/search/?q=volunteer%20research%20summaries")

    assert response.status_code == 200
    assert b"Volunteer" in response.data
    assert b"/volunteer/" in response.data


def test_camino_is_not_promoted_in_header_or_footer():
    app = create_app({"TESTING": True})
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert b"JOIN THE CAMINO" not in response.data
    assert b"Join the Camino" not in response.data
    assert b'href="/jointhecamino/"' not in response.data


def test_search_finds_matching_pages_and_posts():
    app = create_app({"TESTING": True})
    client = app.test_client()

    response = client.get("/search/?q=JEIR")

    assert response.status_code == 200
    assert b"Search Mindful Diabetes" in response.data
    assert b"JEIR" in response.data
    assert b"diabetes-health-jeir-updates" in response.data


def test_favicon_links_render_from_base_template():
    app = create_app({"TESTING": True})
    client = app.test_client()

    for path in ["/", "/guide/", "/memovela/", "/search/"]:
        response = client.get(path)

        assert response.status_code == 200
        assert b"mdi-logo.jpg" in response.data
        assert b"mdi-favicon-32.png" in response.data
        assert b"mdi-favicon-192.png" in response.data
        assert b"apple-touch-icon" in response.data


def test_favicon_fallback_redirects_to_local_asset():
    app = create_app({"TESTING": True})
    client = app.test_client()

    response = client.get("/favicon.ico")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/static/img/mdi-favicon-32.png")


def test_newsletter_forms_render_on_key_pages():
    app = create_app({"TESTING": True})
    client = app.test_client()

    expected_form_counts = {
        "/": 2,
        "/guide/": 2,
        "/memovela/": 2,
    }

    for path, form_count in expected_form_counts.items():
        response = client.get(path)

        assert response.status_code == 200
        assert response.data.count(b'action="/subscribe/"') == form_count
        assert b"Subscribe" in response.data


def test_subscribe_without_mailchimp_config_shows_setup_message():
    app = create_app(
        {
            "TESTING": True,
            "MAILCHIMP_API_KEY": "",
            "MAILCHIMP_AUDIENCE_ID": "",
            "TURNSTILE_SITE_KEY": "",
            "TURNSTILE_SECRET_KEY": "",
        }
    )
    client = app.test_client()

    response = client.post("/subscribe/", data={"email": "reader@example.com", "source": "test"})

    assert response.status_code == 503
    assert b"Newsletter signup is ready for Mailchimp" in response.data
    assert b"reader@example.com" in response.data


def test_subscribe_rejects_invalid_email():
    app = create_app({"TESTING": True})
    client = app.test_client()

    response = client.post("/subscribe/", data={"email": "not-an-email"})

    assert response.status_code == 400
    assert b"Please check the email address" in response.data


def test_turnstile_widget_renders_without_exposing_secret_key():
    app = create_app(
        {
            "TESTING": True,
            "TURNSTILE_SITE_KEY": "public-site-key",
            "TURNSTILE_SECRET_KEY": "private-secret-key",
        }
    )
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert b"https://challenges.cloudflare.com/turnstile/v0/api.js" in response.data
    assert b"/static/js/newsletter-turnstile.js" in response.data
    assert b'class="cf-turnstile newsletter-form__turnstile"' in response.data
    assert b'data-sitekey="public-site-key"' in response.data
    assert b'data-appearance="execute"' in response.data
    assert b'data-execution="execute"' in response.data
    assert b"private-secret-key" not in response.data


def test_turnstile_widget_stays_hidden_until_both_keys_exist():
    app = create_app(
        {
            "TESTING": True,
            "TURNSTILE_SITE_KEY": "public-site-key",
            "TURNSTILE_SECRET_KEY": "",
        }
    )
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert b"cf-turnstile" not in response.data
    assert b"public-site-key" not in response.data


def test_subscribe_requires_turnstile_token_when_configured(monkeypatch):
    def fail_urlopen(*args, **kwargs):
        raise AssertionError("Turnstile and Mailchimp should not be called without a token.")

    monkeypatch.setattr(app_module, "urlopen", fail_urlopen)
    app = create_app(
        {
            "TESTING": True,
            "MAILCHIMP_API_KEY": "mailchimp-key-us21",
            "MAILCHIMP_AUDIENCE_ID": "audience-id",
            "TURNSTILE_SITE_KEY": "public-site-key",
            "TURNSTILE_SECRET_KEY": "private-secret-key",
        }
    )
    client = app.test_client()

    response = client.post("/subscribe/", data={"email": "reader@example.com"})

    assert response.status_code == 400
    assert b"Please complete the human check" in response.data
    assert b"Please complete the human verification and try again." in response.data


def test_subscribe_verifies_turnstile_before_mailchimp(monkeypatch):
    calls = []

    def fake_urlopen(request_obj, timeout):
        calls.append(request_obj.full_url)
        if "siteverify" in request_obj.full_url:
            assert b"secret=private-secret-key" in request_obj.data
            assert b"response=turnstile-token" in request_obj.data
            return StubUrlopenResponse(body=b'{"success": true}')
        assert "api.mailchimp.com" in request_obj.full_url
        return StubUrlopenResponse(body=b"{}")

    monkeypatch.setattr(app_module, "urlopen", fake_urlopen)
    app = create_app(
        {
            "TESTING": True,
            "MAILCHIMP_API_KEY": "mailchimp-key-us21",
            "MAILCHIMP_AUDIENCE_ID": "audience-id",
            "TURNSTILE_SITE_KEY": "public-site-key",
            "TURNSTILE_SECRET_KEY": "private-secret-key",
        }
    )
    client = app.test_client()

    response = client.post(
        "/subscribe/",
        data={
            "email": "reader@example.com",
            "source": "test",
            "cf-turnstile-response": "turnstile-token",
        },
    )

    assert response.status_code == 200
    assert b"Thanks for joining the Mindful Diabetes newsletter." in response.data
    assert calls[0].endswith("/turnstile/v0/siteverify")
    assert "api.mailchimp.com" in calls[1]


def test_subscribe_honeypot_silently_skips_bot_submission(monkeypatch):
    def fail_urlopen(*args, **kwargs):
        raise AssertionError("Bot submissions should not call Turnstile or Mailchimp.")

    monkeypatch.setattr(app_module, "urlopen", fail_urlopen)
    app = create_app(
        {
            "TESTING": True,
            "MAILCHIMP_API_KEY": "mailchimp-key-us21",
            "MAILCHIMP_AUDIENCE_ID": "audience-id",
            "TURNSTILE_SITE_KEY": "public-site-key",
            "TURNSTILE_SECRET_KEY": "private-secret-key",
        }
    )
    client = app.test_client()

    response = client.post(
        "/subscribe/",
        data={"email": "bot@example.com", "website": "https://spam.example"},
    )

    assert response.status_code == 200
    assert b"Thanks for joining the Mindful Diabetes newsletter." in response.data


def test_footer_uses_contact_button_without_public_phone_or_address():
    app = create_app({"TESTING": True})
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert b"Contact Us" in response.data
    assert b"407-314-5152" not in response.data
    assert b"25885 SW 139th Path" not in response.data
    assert b"Guidestar Profile" not in response.data


def test_post_article_navigation_links_neighbor_posts():
    app = create_app({"TESTING": True})
    client = app.test_client()
    posts = app.config["CONTENT"].latest_posts
    current_index = next(
        index for index, post in enumerate(posts) if post["slug"] == "diabetes-health-jeir-updates"
    )

    response = client.get("/diabetes-health-jeir-updates/")

    assert response.status_code == 200
    assert b'class="article-navigation"' in response.data
    assert b"Previous article" in response.data
    assert b"Next article" in response.data
    assert b"Random article" in response.data
    assert b'href="/random-article/?exclude=diabetes-health-jeir-updates"' in response.data

    if current_index + 1 < len(posts):
        assert posts[current_index + 1]["canonical_path"].encode() in response.data
    if current_index == 0:
        assert b"You are at the newest article" in response.data


def test_random_article_redirects_to_a_post(monkeypatch):
    app = create_app({"TESTING": True})
    client = app.test_client()
    target_post = app.config["CONTENT"].latest_posts[-1]
    monkeypatch.setattr(app_module.random, "choice", lambda posts: target_post)

    response = client.get("/random-article/")

    assert response.status_code == 302
    assert response.headers["Location"].endswith(target_post["canonical_path"])


def test_every_post_uses_shared_article_template():
    app = create_app({"TESTING": True})
    client = app.test_client()

    for post in app.config["CONTENT"].latest_posts:
        response = client.get(post["canonical_path"])

        assert response.status_code == 200, post["canonical_path"]
        assert b'class="article-post-hero"' in response.data, post["canonical_path"]
        assert response.data.count(b'class="article-post-shell"') == 1, post["canonical_path"]
        assert response.data.count(b'class="article-post-body"') == 1, post["canonical_path"]
        assert response.data.count(b'class="article-post-sidebar"') == 1, post["canonical_path"]
        assert b'class="wp-content article-content"' in response.data, post["canonical_path"]
        assert response.data.count(b'class="article-sidebar-card"') == 4, post["canonical_path"]
        assert b'action="/subscribe/"' in response.data, post["canonical_path"]
        assert b'class="article-callout"></section>' not in response.data, post["canonical_path"]
        assert b'<div class="article-callout"><section' not in response.data, post["canonical_path"]


def test_article_section_wrapping_does_not_split_list_items():
    app = create_app({"TESTING": True})
    client = app.test_client()

    for post in app.config["CONTENT"].latest_posts:
        response = client.get(post["canonical_path"])

        assert response.status_code == 200, post["canonical_path"]
        assert b"</li><li></section>" not in response.data, post["canonical_path"]
        assert b"</ul></li><li></section>" not in response.data, post["canonical_path"]
        if post["slug"] == "diabetes-artificial-intelligence-jeir":
            assert b"<h4><strong>Exercise Recommendations" in response.data
            assert b"<h4><strong>Weight Management Strategies" in response.data
            assert b"</section>\n<section class=\"article-section article-section--green\"><h4><strong>Exercise Recommendations" not in response.data


def test_every_post_uses_styled_wellness_tools_panel():
    app = create_app({"TESTING": True})
    client = app.test_client()

    for post in app.config["CONTENT"].latest_posts:
        response = client.get(post["canonical_path"])

        assert response.status_code == 200, post["canonical_path"]
        assert b'class="article-wellness-tools"' in response.data, post["canonical_path"]
        assert b"https://memovela.com/" in response.data, post["canonical_path"]
        assert b"Read about Memovela" in response.data, post["canonical_path"]
        assert b"md-glow-btn" not in response.data, post["canonical_path"]


def test_chicago_marathon_impact_card_replaces_imported_blog_promo():
    app = create_app({"TESTING": True})
    client = app.test_client()

    posts_with_imported_promo = [
        post
        for post in app.config["CONTENT"].latest_posts
        if "raised over $2,500" in post["content_html"]
        and "/chicago-marathon-diabetes/" in post["content_html"]
    ]

    assert len(posts_with_imported_promo) == 88
    for post in posts_with_imported_promo:
        response = client.get(post["canonical_path"])

        assert response.status_code == 200, post["canonical_path"]
        assert b'class="article-impact-card"' in response.data, post["canonical_path"]
        assert b"Chicago Marathon Diabetes Project" in response.data, post["canonical_path"]
        assert b"Read the marathon story" in response.data, post["canonical_path"]
        assert b"<figcaption>Click the photo to read about how we raised over $2,500" not in response.data


def test_article_navigation_handles_oldest_and_newest_posts():
    app = create_app({"TESTING": True})
    client = app.test_client()
    posts = app.config["CONTENT"].latest_posts

    newest = client.get(posts[0]["canonical_path"])
    oldest = client.get(posts[-1]["canonical_path"])

    assert newest.status_code == 200
    assert oldest.status_code == 200
    assert b"You are at the newest article" in newest.data
    assert posts[1]["canonical_path"].encode() in newest.data
    assert b"You are at the oldest article" in oldest.data
    assert posts[-2]["canonical_path"].encode() in oldest.data


def test_random_article_excludes_current_post(monkeypatch):
    app = create_app({"TESTING": True})
    client = app.test_client()
    current_post = app.config["CONTENT"].latest_posts[0]
    seen_choices = []

    def choose(posts):
        seen_choices.extend(posts)
        return posts[0]

    monkeypatch.setattr(app_module.random, "choice", choose)

    response = client.get(f"/random-article/?exclude={current_post['slug']}")

    assert response.status_code == 302
    assert current_post not in seen_choices
    assert response.headers["Location"] != current_post["canonical_path"]


def test_articles_remove_blog_audio_video_prompts():
    app = create_app({"TESTING": True})
    client = app.test_client()

    for path in ["/diabetes-health-jeir-updates/", "/memovela/", "/type-3-diabetes/"]:
        response = client.get(path)

        assert response.status_code == 200
        assert b'class="article-post-hero__media"' in response.data
        assert b'class="article-post-media"' not in response.data
        assert b'class="video-frame"' not in response.data
        assert b"<audio" not in response.data
        assert b"Listen or watch" not in response.data
        assert b"Choose the format that fits your day" not in response.data
        assert b"Use the audio version for a quick listen" not in response.data
        assert b"Full article" not in response.data
        assert b"Want to listen instead?" not in response.data


def test_shared_article_css_frames_images_and_videos():
    css = (app_module.BASE_DIR / "static" / "css" / "site.css").read_text(encoding="utf-8")

    assert ".article-post-hero__media" in css
    assert ".article-content img" in css
    assert ".article-content .article-image-placeholder" in css
    assert ".article-content .video-frame" in css
    assert ".article-wellness-tools" in css
    assert ".article-tool-card--memovela" in css
    assert ".article-impact-grid" in css
    assert ".article-impact-card" in css
    assert "var(--secondary) 0 50%" in css
    assert "var(--miami-green) 50% 100%" in css


def test_new_summer_hydration_post_has_links_and_generated_images():
    app = create_app({"TESTING": True})
    client = app.test_client()
    response = client.get("/summer-walks-hydration-diabetes/")

    internal_links = [
        b'href="/guide/"',
        b'href="/summer-diabetes/"',
        b'href="/summer-diabetes-management/"',
        b'href="/walking-health/"',
        b'href="/walking-heart-health/"',
        b'href="/low-impact-exercise/"',
        b'href="/prevent-type-3-diabetes-with-exercise/"',
        b'href="/daily-wellness-habits/"',
        b'href="/blood-sugar-body/"',
        b'href="/type-3-diabetes/"',
        b'href="/connecting-diabetes-and-alzheimers/"',
        b'href="/insulin-resistance-cognitive-decline/"',
        b'href="/food-sequencing-diabetes/"',
        b'href="/mindful-eating/"',
        b'href="/healthy-eating/"',
        b'href="/memovela/"',
        b'href="/diabetes-health-jeir-updates/"',
        b'href="/donation/"',
    ]
    external_links = [
        b"https://www.cdc.gov/diabetes/articles/managing-diabetes-in-the-heat.html",
        b"https://medlineplus.gov/dehydration.html",
        b"https://medlineplus.gov/heatillness.html",
        b"https://www.ncbi.nlm.nih.gov/books/NBK526095/",
        b"https://pubmed.ncbi.nlm.nih.gov/32998820/",
        b"https://pubmed.ncbi.nlm.nih.gov/20150024/",
        b"https://pubmed.ncbi.nlm.nih.gov/35868079/",
        b"https://magazine.medlineplus.gov/article/h20-for-healthy-aging",
        b"https://pubmed.ncbi.nlm.nih.gov/27329025/",
        b"https://pubmed.ncbi.nlm.nih.gov/33217794/",
    ]
    image_assets = [
        b"/static/uploads/2026/07/summer-walks-hydration-diabetes-hero.webp",
        b"/static/uploads/2026/07/summer-walking-shaded-route.webp",
        b"/static/uploads/2026/07/summer-hydration-kit-diabetes.webp",
        b"/static/uploads/2026/07/summer-walk-body-signals-checklist.webp",
        b"/static/uploads/2026/07/summer-walk-cool-down-hydration.webp",
        b"/static/uploads/2026/07/check-carry-choose-cool-down.webp",
    ]

    assert response.status_code == 200
    assert b"Summer Walks, Hydration, and Diabetes" in response.data
    assert b"A shaded summer walking path with a water bottle" in response.data
    assert b"Summer walking essentials for diabetes and hydration" in response.data
    assert b"Hero image for a Mindful Diabetes article about summertime walking" in response.data
    assert b"Supporting image for a section about planning safer summer walks" in response.data
    assert b"Mobile-friendly infographic summarizing hydration" in response.data
    assert b"A little planning can make summer walks safer" in response.data
    assert all(asset in response.data for asset in image_assets)
    assert all(link in response.data for link in internal_links)
    assert all(link in response.data for link in external_links)


def test_summer_hydration_preview_images_include_seo_metadata():
    app = create_app({"TESTING": True})
    client = app.test_client()
    post = app.config["CONTENT"].posts_by_slug["summer-walks-hydration-diabetes"]

    assert post["preview_image_title"] == "Summer walking essentials for diabetes and hydration"
    assert post["preview_image_description"].startswith("Hero image for a Mindful Diabetes article")

    for path in ["/", "/guide/", "/summer-walks-hydration-diabetes/"]:
        response = client.get(path)

        assert response.status_code == 200
        assert b"/static/uploads/2026/07/summer-walks-hydration-diabetes-hero.webp" in response.data
        assert b'title="Summer walking essentials for diabetes and hydration"' in response.data
        assert b'data-description="Hero image for a Mindful Diabetes article' in response.data


def test_april_alzheimers_research_post_has_sources_and_generated_images():
    app = create_app({"TESTING": True})
    client = app.test_client()
    response = client.get("/alzheimers-research-blood-tests-tau-trials/")
    post = app.config["CONTENT"].posts_by_slug["alzheimers-research-blood-tests-tau-trials"]

    internal_links = [
        b'href="/type-3-diabetes/"',
        b'href="/connecting-diabetes-and-alzheimers/"',
        b'href="/insulin-resistance-cognitive-decline/"',
        b'href="/glucose-metabolism-and-brain-health/"',
        b'href="/blood-sugar-body/"',
        b'href="/daily-wellness-habits/"',
        b'href="/walking-health/"',
        b'href="/prevent-type-3-diabetes-with-exercise/"',
        b'href="/mental-health/"',
        b'href="/stress-in-diabetes-and-strategies-for-stress-management/"',
        b'href="/mind-diet/"',
        b'href="/food-sequencing-diabetes/"',
        b'href="/mindful-eating/"',
        b'href="/diabetes-artificial-intelligence-jeir/"',
        b'href="/memovela/"',
        b'href="/guide/"',
        b'href="/donation/"',
    ]
    external_links = [
        b"https://www.nature.com/articles/s41591-026-04303-y",
        b"https://www.multipark.lu.se/article/new-ai-model-can-detect-multiple-cognitive-brain-diseases-single-blood-sample",
        b"https://www.nature.com/articles/s41467-026-71732-1",
        b"https://link.springer.com/article/10.1186/s13195-026-02044-1",
        b"https://www.sciencedirect.com/science/article/pii/S2274580726000270",
        b"https://clinicaltrials.gov/study/NCT04468659",
        b"https://clinicaltrials.gov/study/NCT05026866",
        b"https://www.alzheimers.gov/clinical-trials",
        b"https://www.accessdata.fda.gov/drugsatfda_docs/label/2025/761375s000lbl.pdf",
        b"https://www.accessdata.fda.gov/drugsatfda_docs/label/2025/761248s004lbl.pdf",
        b"https://pubmed.ncbi.nlm.nih.gov/42075835/",
    ]
    image_assets = [
        b"/static/uploads/2026/04/alzheimers-research-blood-tests-tau-trials-hero.webp",
        b"/static/uploads/2026/04/plasma-proteomics-dementia-ai-model.webp",
        b"/static/uploads/2026/04/alzheimers-tau-timeline-biomarkers.webp",
        b"/static/uploads/2026/04/preclinical-alzheimers-biomarker-context.webp",
        b"/static/uploads/2026/04/digital-memory-blood-biomarker-trials.webp",
        b"/static/uploads/2026/04/alzheimers-aria-safety-monitoring.webp",
    ]

    assert response.status_code == 200
    assert post["date"] == "2026-04-18 09:00:00"
    assert b"Alzheimer" in response.data
    assert b"Families deserve hope, but not hype" in response.data
    assert b"Blood protein patterns in Alzheimer" in response.data
    assert b"Safety monitoring in Alzheimer" in response.data
    assert b"Hero image for a Mindful Diabetes article translating early April 2026" in response.data
    assert b"Supporting image for a section about anti-amyloid therapy safety" in response.data
    assert all(asset in response.data for asset in image_assets)
    assert all(link in response.data for link in internal_links)
    assert all(link in response.data for link in external_links)


def test_april_alzheimers_research_preview_image_includes_seo_metadata():
    app = create_app({"TESTING": True})
    client = app.test_client()
    post = app.config["CONTENT"].posts_by_slug["alzheimers-research-blood-tests-tau-trials"]

    assert post["preview_image_title"] == "Alzheimer’s research explained with warmth and honesty"
    assert post["preview_image_description"].startswith("Hero image for a Mindful Diabetes article")

    for path in ["/guide/", "/alzheimers-research-blood-tests-tau-trials/"]:
        response = client.get(path)

        assert response.status_code == 200
        assert b"/static/uploads/2026/04/alzheimers-research-blood-tests-tau-trials-hero.webp" in response.data
        assert b'title="Alzheimer\xe2\x80\x99s research explained with warmth and honesty"' in response.data
        assert b'data-description="Hero image for a Mindful Diabetes article translating early April 2026' in response.data


def test_february_ipsc_alzheimers_post_has_sources_and_generated_images():
    app = create_app({"TESTING": True})
    client = app.test_client()
    response = client.get("/ipsc-cells-alzheimers-disease-models/")
    post = app.config["CONTENT"].posts_by_slug["ipsc-cells-alzheimers-disease-models"]

    internal_links = [
        b'href="/type-3-diabetes/"',
        b'href="/connecting-diabetes-and-alzheimers/"',
        b'href="/insulin-resistance-cognitive-decline/"',
        b'href="/glucose-metabolism-and-brain-health/"',
        b'href="/daily-wellness-habits/"',
        b'href="/walking-heart-health/"',
        b'href="/mind-diet/"',
        b'href="/food-sequencing-diabetes/"',
        b'href="/mindful-eating/"',
        b'href="/stress-in-diabetes-and-strategies-for-stress-management/"',
        b'href="/mental-health/"',
        b'href="/memovela/"',
        b'href="/guide/"',
        b'href="/donation/"',
    ]
    external_links = [
        b"https://www.cell.com/cell/fulltext/S0092-8674(06)00976-7",
        b"https://www.cell.com/cell/fulltext/S0092-8674(07)01471-7",
        b"https://www.nature.com/articles/nature10821",
        b"https://www.cell.com/neuron/fulltext/S0896-6273(18)30307-2",
        b"https://www.cell.com/neuron/fulltext/S0896-6273(21)00926-0",
        b"https://www.nature.com/articles/s41467-020-19264-0",
        b"https://onlinelibrary.wiley.com/doi/10.1002/adhm.202505427",
        b"https://www.nature.com/articles/s42003-025-07507-7",
        b"https://alz-journals.onlinelibrary.wiley.com/doi/10.1002/alz.71117",
        b"https://advanced.onlinelibrary.wiley.com/doi/10.1002/advs.202505549",
        b"https://onlinelibrary.wiley.com/doi/10.1155/2021/5511630",
        b"https://onlinelibrary.wiley.com/doi/10.1155/2021/5511630#bib-0120",
        b"https://onlinelibrary.wiley.com/doi/10.1155/2021/5511630#bib-0139",
    ]
    image_assets = [
        b"/static/uploads/2026/02/ipsc-alzheimers-modeling-hero.webp",
        b"/static/uploads/2026/02/cellular-time-machine-ipsc-workflow.webp",
        b"/static/uploads/2026/02/isogenic-ipsc-lines-alzheimers-research.webp",
        b"/static/uploads/2026/02/brain-organoid-on-chip-alzheimers-model.webp",
        b"/static/uploads/2026/02/ipsc-microglia-neuron-organoid-model.webp",
        b"/static/uploads/2026/02/ipsc-models-promise-limits-alzheimers.webp",
        b"/static/uploads/2026/02/key-ipsc-signals.webp",
    ]

    assert response.status_code == 200
    assert post["date"] == "2026-02-16 09:00:00"
    assert b"Tiny Cells, Big Questions" in response.data
    assert b"A positive drug signal in a cell model is not proof" in response.data
    assert b"iPSC models do not recreate a whole brain" in response.data
    assert b"How Our Earlier Stem Cells International Review Fits In" in response.data
    assert b"Table 1. Selected genetic iPSC models of Alzheimer" in response.data
    assert b"APOE type can influence APP transcription" in response.data
    assert b"Hero image for a Mindful Diabetes article explaining how induced pluripotent stem cells" in response.data
    assert b"Supporting image for a section about iPSC-derived microglia" in response.data
    assert b"Educational figure showing where key Alzheimer" in response.data
    assert b"Where key Alzheimer" in response.data
    assert all(asset in response.data for asset in image_assets)
    assert all(link in response.data for link in internal_links)
    assert all(link in response.data for link in external_links)


def test_february_ipsc_alzheimers_preview_image_includes_seo_metadata():
    app = create_app({"TESTING": True})
    client = app.test_client()
    post = app.config["CONTENT"].posts_by_slug["ipsc-cells-alzheimers-disease-models"]

    assert post["preview_image_title"] == "iPSC models help researchers study Alzheimer’s disease in human cells"
    assert post["preview_image_description"].startswith("Hero image for a Mindful Diabetes article")

    for path in ["/guide/", "/ipsc-cells-alzheimers-disease-models/"]:
        response = client.get(path)

        assert response.status_code == 200
        assert b"/static/uploads/2026/02/ipsc-alzheimers-modeling-hero.webp" in response.data
        assert b'title="iPSC models help researchers study Alzheimer\xe2\x80\x99s disease in human cells"' in response.data
        assert b'data-description="Hero image for a Mindful Diabetes article explaining how induced pluripotent stem cells' in response.data


def test_january_amyloid_plaques_post_has_sources_and_generated_images():
    app = create_app({"TESTING": True})
    client = app.test_client()
    response = client.get("/amyloid-plaques-alzheimers-research/")
    post = app.config["CONTENT"].posts_by_slug["amyloid-plaques-alzheimers-research"]

    internal_links = [
        b'href="/type-3-diabetes/"',
        b'href="/connecting-diabetes-and-alzheimers/"',
        b'href="/insulin-resistance-cognitive-decline/"',
        b'href="/glucose-metabolism-and-brain-health/"',
        b'href="/blood-sugar-body/"',
        b'href="/daily-wellness-habits/"',
        b'href="/walking-health/"',
        b'href="/prevent-type-3-diabetes-with-exercise/"',
        b'href="/mental-health/"',
        b'href="/stress-in-diabetes-and-strategies-for-stress-management/"',
        b'href="/mind-diet/"',
        b'href="/food-sequencing-diabetes/"',
        b'href="/mindful-eating/"',
        b'href="/healthy-eating/"',
        b'href="/memovela/"',
        b'href="/diabetes-artificial-intelligence-jeir/"',
        b'href="/guide/"',
        b'href="/donation/"',
    ]
    external_links = [
        b"https://www.nia.nih.gov/health/what-happens-brain-alzheimers-disease",
        b"https://www.nia.nih.gov/health/alzheimers-causes-and-risk-factors/what-causes-alzheimers-disease",
        b"https://www.nature.com/articles/s41467-025-59085-7",
        b"https://www.nature.com/articles/s41467-025-63328-y",
        b"https://www.nature.com/articles/s41591-025-03574-1",
        b"https://jnm.snmjournals.org/content/early/2025/01/07/jnumed.124.268756",
        b"https://pubmed.ncbi.nlm.nih.gov/36449413/",
        b"https://pubmed.ncbi.nlm.nih.gov/37459141/",
        b"https://pubmed.ncbi.nlm.nih.gov/37966285/",
        b"https://www.nejm.org/doi/full/10.1056/NEJMoa2305032",
        b"https://clinicaltrials.gov/study/NCT04468659",
        b"https://www.alzheimers.gov/clinical-trials",
    ]
    image_assets = [
        b"/static/uploads/2026/01/amyloid-plaques-alzheimers-research-hero.webp",
        b"/static/uploads/2026/01/amyloid-soluble-fibrils-plaque-comparison.webp",
        b"/static/uploads/2026/01/microglia-amyloid-clearance-research.webp",
        b"/static/uploads/2026/01/amyloid-pet-biomarker-research-scene.webp",
        b"/static/uploads/2026/01/amyloid-tau-inflammation-vascular-map.webp",
        b"/static/uploads/2026/01/amyloid-research-translation-pathway.webp",
    ]

    assert response.status_code == 200
    assert post["date"] == "2026-01-15 09:00:00"
    assert post["content_html"].count("<img ") == 6
    assert b"Amyloid Plaques Are Not the Whole Story" in response.data
    assert b"What We Can Honestly Say" in response.data
    assert b"Reducing amyloid is a biological achievement" in response.data
    assert b"Hero image for a Mindful Diabetes article explaining amyloid plaque research" in response.data
    assert b"Supporting image for a section about amyloid PET" in response.data
    assert b'class="article-impact-grid"' in response.data
    grid_start = response.data.find(b'class="article-impact-grid"')
    first_card_start = response.data.find(b"What It Can Tell Us", grid_start)
    second_card_start = response.data.find(b"What It Cannot Tell Us Alone", grid_start)
    next_section_start = response.data.find(b"Where Translational Research Goes Next", grid_start)
    grid_section_start = response.data.rfind(b'<section class="article-section', 0, grid_start)

    assert grid_start < first_card_start < second_card_start < next_section_start
    assert grid_section_start == response.data.rfind(b'<section class="article-section', 0, first_card_start)
    assert grid_section_start == response.data.rfind(b'<section class="article-section', 0, second_card_start)
    assert all(asset in response.data for asset in image_assets)
    assert all(link in response.data for link in internal_links)
    assert all(link in response.data for link in external_links)


def test_january_amyloid_plaques_preview_image_and_tone_guardrails():
    app = create_app({"TESTING": True})
    client = app.test_client()
    post = app.config["CONTENT"].posts_by_slug["amyloid-plaques-alzheimers-research"]
    content = post["content_html"].lower()
    blocked_phrases = [
        "for a lay reader",
        "in plain english",
        "the name is a mouthful",
        "it is easier than it sounds",
        "that sounds technical",
        "the important thing for readers",
        "you do not need to know",
        "miracle",
        "breakthrough",
    ]

    assert post["preview_image_title"] == "Amyloid plaques in Alzheimer’s research"
    assert post["preview_image_description"].startswith("Hero image for a Mindful Diabetes article")
    assert all(phrase not in content for phrase in blocked_phrases)

    for path in ["/guide/", "/amyloid-plaques-alzheimers-research/"]:
        response = client.get(path)

        assert response.status_code == 200
        assert b"/static/uploads/2026/01/amyloid-plaques-alzheimers-research-hero.webp" in response.data
        assert b'title="Amyloid plaques in Alzheimer\xe2\x80\x99s research"' in response.data
        assert b'data-description="Hero image for a Mindful Diabetes article explaining amyloid plaque research' in response.data


def test_articles_do_not_expose_mailchimp_api_key():
    secret = "test-us21-secret-api-key"
    app = create_app(
        {
            "TESTING": True,
            "MAILCHIMP_API_KEY": secret,
            "MAILCHIMP_AUDIENCE_ID": "audience-id",
        }
    )
    client = app.test_client()

    for post in app.config["CONTENT"].latest_posts:
        response = client.get(post["canonical_path"])

        assert response.status_code == 200, post["canonical_path"]
        assert secret.encode() not in response.data, post["canonical_path"]


def test_admin_dashboard_requires_email_code_login(tmp_path, monkeypatch):
    sent_payloads = []

    def fake_urlopen(request_obj, timeout=0):
        sent_payloads.append(json.loads(request_obj.data.decode("utf-8")))
        assert request_obj.full_url == "https://api.brevo.com/v3/smtp/email"
        assert request_obj.headers["Api-key"] == "brevo-test-key"
        return StubUrlopenResponse(status=201, body=b'{"messageId":"test"}')

    monkeypatch.setattr(app_module, "urlopen", fake_urlopen)
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "ADMIN_EMAIL": "jmschulz@mindfuldiabetes.org",
            "BREVO_API_KEY": "brevo-test-key",
            "ADMIN_DATA_PATH": str(tmp_path / "admin_data.json"),
        }
    )
    client = app.test_client()

    protected_response = client.get("/admin/")
    assert protected_response.status_code == 302
    assert protected_response.headers["Location"].endswith("/admin/login/?next=/admin/")

    login_page_response = client.get("/admin/login/")
    assert login_page_response.status_code == 200
    assert b'value="jmschulz@mindfuldiabetes.org"' not in login_page_response.data

    request_code_response = client.post(
        "/admin/login/",
        data={"email": "jmschulz@mindfuldiabetes.org"},
    )
    assert request_code_response.status_code == 200
    assert b"Check your email for the one-time admin code." in request_code_response.data
    assert sent_payloads

    code = sent_payloads[0]["textContent"].split(" is ")[1].split(".")[0]
    login_response = client.post(
        "/admin/login/",
        data={"email": "jmschulz@mindfuldiabetes.org", "code": code},
    )

    assert login_response.status_code == 302
    assert login_response.headers["Location"].endswith("/admin/")

    dashboard_response = client.get("/admin/")
    assert dashboard_response.status_code == 200
    assert b"Site activity" in dashboard_response.data
    assert b"Signed in as jmschulz@mindfuldiabetes.org" in dashboard_response.data


def test_admin_activity_tracks_public_page_views(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "ADMIN_DATA_PATH": str(tmp_path / "admin_data.json"),
        }
    )
    client = app.test_client()

    response = client.get("/guide/")
    assert response.status_code == 200

    dashboard = app_module.build_admin_dashboard(app.config)
    assert dashboard["stats"][0]["value"] == 1
    assert dashboard["top_paths"][0] == {"path": "/guide/", "count": 1}


def sign_in_admin(client):
    with client.session_transaction() as flask_session:
        flask_session["admin_email"] = "jmschulz@mindfuldiabetes.org"
        flask_session["admin_csrf_token"] = "csrf-test-token"
    return "csrf-test-token"


def test_admin_dashboard_links_to_content_studio(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "ADMIN_DATA_PATH": str(tmp_path / "admin_data.json"),
            "CMS_DATA_PATH": str(tmp_path / "cms_content.json"),
        }
    )
    client = app.test_client()
    sign_in_admin(client)

    response = client.get("/admin/")

    assert response.status_code == 200
    assert b"Content studio" in response.data
    assert b"Create New Page" in response.data
    assert b"Create New Post" in response.data
    assert b"Manage Content" in response.data


def test_admin_content_flow_saves_publishes_and_renders_sanitized_blocks(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "ADMIN_DATA_PATH": str(tmp_path / "admin_data.json"),
            "CMS_DATA_PATH": str(tmp_path / "cms_content.json"),
        }
    )
    client = app.test_client()
    csrf_token = sign_in_admin(client)

    create_response = client.post("/admin/pages/new/", data={"csrf_token": csrf_token})
    assert create_response.status_code == 302
    editor_path = create_response.headers["Location"]
    content_id = editor_path.split("/admin/content/", 1)[1].split("/edit/", 1)[0]

    editor_response = client.get(editor_path)
    assert editor_response.status_code == 200
    assert b"Block inserter" in editor_response.data
    assert b"Save Draft" in editor_response.data
    assert b"Publish" in editor_response.data

    payload = {
        "id": content_id,
        "content_type": "page",
        "title": "CMS Test Page",
        "slug": "cms-test-page",
        "status": "draft",
        "excerpt": "A safe editable page.",
        "blocks": [
            {
                "id": "heading-one",
                "type": "heading",
                "version": 1,
                "settings": {"level": 1, "alignment": "left", "accent": True, "color": "navy"},
                "content": {"text": "CMS Test Page"},
            },
            {
                "id": "body-copy",
                "type": "rich_text",
                "version": 1,
                "settings": {},
                "content": {
                    "html": '<p>Hello <strong>reader</strong>.</p><script>alert("bad")</script><a href="javascript:alert(1)">bad link</a>'
                },
            },
            {
                "id": "cta",
                "type": "button",
                "version": 1,
                "settings": {"style": "orange", "alignment": "center", "new_tab": False},
                "content": {"label": "Donate", "url": "/donation/"},
            },
        ],
        "settings": {"template": "standard"},
        "seo": {"seo_title": "Safe CMS Page", "meta_description": "A safe page."},
    }

    save_response = client.post(
        f"/admin/content/{content_id}/save/",
        data=json.dumps(payload),
        content_type="application/json",
        headers={"X-CSRF-Token": csrf_token},
    )
    assert save_response.status_code == 200
    assert save_response.json["ok"] is True

    public_draft_response = client.get("/cms-test-page/")
    assert public_draft_response.status_code == 404

    publish_response = client.post(
        f"/admin/content/{content_id}/publish/",
        data=json.dumps(payload),
        content_type="application/json",
        headers={"X-CSRF-Token": csrf_token},
    )
    assert publish_response.status_code == 200
    assert publish_response.json["ok"] is True
    assert publish_response.json["view_url"] == "/cms-test-page/"

    public_response = client.get("/cms-test-page/")
    assert public_response.status_code == 200
    assert b"CMS Test Page" in public_response.data
    assert b"Hello <strong>reader</strong>" in public_response.data
    assert b"<script>" not in public_response.data
    assert b"javascript:alert" not in public_response.data
    assert b'href="/donation/"' in public_response.data


def test_admin_content_state_changes_require_csrf(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "ADMIN_DATA_PATH": str(tmp_path / "admin_data.json"),
            "CMS_DATA_PATH": str(tmp_path / "cms_content.json"),
        }
    )
    client = app.test_client()
    sign_in_admin(client)

    response = client.post("/admin/pages/new/")

    assert response.status_code == 400


def test_admin_editor_uses_fullscreen_gutenberg_style_shell(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "ADMIN_DATA_PATH": str(tmp_path / "admin_data.json"),
            "CMS_DATA_PATH": str(tmp_path / "cms_content.json"),
        }
    )
    client = app.test_client()
    csrf_token = sign_in_admin(client)
    create_response = client.post("/admin/pages/new/", data={"csrf_token": csrf_token})
    editor_path = create_response.headers["Location"]

    response = client.get(editor_path)

    assert response.status_code == 200
    assert b"class=\"site-header\"" not in response.data
    assert b"site-nav" not in response.data
    assert b"header-search" not in response.data
    assert b"Back to Content" in response.data
    assert b"Document outline" in response.data
    assert b"data-inserter" in response.data
    assert b'aria-hidden="true" data-inserter' in response.data
    assert b"data-settings-drawer" in response.data
    assert b'aria-hidden="true" data-settings-drawer' in response.data
    assert b"data-insert-zone" in response.data
    assert b"data-document-title" in response.data
    assert b"data-settings-tab=\"block\"" in response.data
    assert b"data-settings-tab=\"document\"" in response.data
    assert b"data-settings-tab=\"seo\"" not in response.data
    assert b"Content JSON" not in response.data
    assert b"Settings JSON" not in response.data
    assert b"Advanced Developer Mode" in response.data


def test_admin_editor_block_inserter_groups_blocks_by_category(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "ADMIN_DATA_PATH": str(tmp_path / "admin_data.json"),
            "CMS_DATA_PATH": str(tmp_path / "cms_content.json"),
        }
    )
    client = app.test_client()
    csrf_token = sign_in_admin(client)
    create_response = client.post("/admin/posts/new/", data={"csrf_token": csrf_token})

    response = client.get(create_response.headers["Location"])

    assert response.status_code == 200
    for label in [
        b"Frequently Used",
        b"Basic",
        b"Layout",
        b"Media",
        b"Article",
        b"Education",
        b"Research",
        b"Health and Nutrition",
        b"Nonprofit",
    ]:
        assert label in response.data
    assert b'data-block-type="heading"' in response.data
    assert b'data-block-type="faq"' in response.data
    assert b'data-block-type="research_summary"' in response.data


def test_cms_new_mindful_diabetes_blocks_render_and_sanitize(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "ADMIN_DATA_PATH": str(tmp_path / "admin_data.json"),
            "CMS_DATA_PATH": str(tmp_path / "cms_content.json"),
        }
    )
    client = app.test_client()
    csrf_token = sign_in_admin(client)
    create_response = client.post("/admin/posts/new/", data={"csrf_token": csrf_token})
    content_id = create_response.headers["Location"].split("/admin/content/", 1)[1].split("/edit/", 1)[0]

    payload = {
        "id": content_id,
        "content_type": "post",
        "title": "Mindful Block Pack",
        "slug": "mindful-block-pack",
        "status": "draft",
        "blocks": [
            {
                "id": "toc",
                "type": "table_of_contents",
                "version": 1,
                "settings": {"sticky": True, "collapse_mobile": True, "highlight_current": True},
                "content": {"heading": "Article guide"},
            },
            {
                "id": "heading-a1c",
                "type": "heading",
                "version": 1,
                "settings": {"level": 2, "alignment": "left", "accent": True, "color": "green"},
                "content": {"text": "Understanding A1C"},
            },
            {
                "id": "faq",
                "type": "faq",
                "version": 1,
                "settings": {"style": "orange", "multiple_open": True, "faq_schema": True},
                "content": {
                    "heading": "Diabetes questions",
                    "items": [{"question": "Can I eat carbohydrates?", "answer": "<p>Yes, with planning.</p><script>bad()</script>"}],
                },
            },
            {
                "id": "myth",
                "type": "myth_fact",
                "version": 1,
                "settings": {},
                "content": {"myth": "Diabetes means no carbs.", "fact": "Carbohydrates can fit with thoughtful portions."},
            },
            {
                "id": "citation",
                "type": "citation",
                "version": 1,
                "settings": {"display": "card"},
                "content": {
                    "authors": "Schulz J",
                    "title": "Helpful research",
                    "journal": "Mindful Diabetes Review",
                    "year": "2026",
                    "doi": "10.1234/example",
                    "pubmed_url": "javascript:alert(1)",
                },
            },
            {
                "id": "related",
                "type": "related_posts",
                "version": 1,
                "settings": {"count": 2, "layout": "cards", "show_image": False, "show_date": True, "show_excerpt": False},
                "content": {"heading": "Related reading"},
            },
        ],
        "settings": {"template": "article"},
        "seo": {},
    }

    publish_response = client.post(
        f"/admin/content/{content_id}/publish/",
        data=json.dumps(payload),
        content_type="application/json",
        headers={"X-CSRF-Token": csrf_token},
    )
    assert publish_response.status_code == 200

    response = client.get("/mindful-block-pack/")

    assert response.status_code == 200
    assert b"Article guide" in response.data
    assert b'href="#understanding-a1c"' in response.data
    assert b'id="understanding-a1c"' in response.data
    assert b"Diabetes questions" in response.data
    assert b'itemtype="https://schema.org/FAQPage"' in response.data
    assert b"<script>" not in response.data
    assert b"Diabetes means no carbs." in response.data
    assert b"Helpful research" in response.data
    assert b"javascript:alert" not in response.data
    assert b"Related reading" in response.data


def test_cms_block_library_includes_domain_specific_blocks():
    labels = {block["type"] for block in app_module.cms.block_library()}

    for expected in [
        "faq",
        "card_grid",
        "statistics",
        "research_summary",
        "nutrition_facts",
        "health_tool_card",
        "community_story",
    ]:
        assert expected in labels
