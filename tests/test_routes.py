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
    assert len(content.latest_posts) == 90

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
    assert ".article-impact-card" in css
    assert "var(--secondary) 0 50%" in css
    assert "var(--miami-green) 50% 100%" in css


def test_new_summer_hydration_post_has_links_and_placeholders():
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

    assert response.status_code == 200
    assert b"Summer Walks, Hydration, and Diabetes" in response.data
    assert response.data.count(b'class="article-image-placeholder"') == 6
    assert all(link in response.data for link in internal_links)
    assert all(link in response.data for link in external_links)


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
