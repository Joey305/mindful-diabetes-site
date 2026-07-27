# Mindful Diabetes Website

Mindful Diabetes is a public health, education, and research website focused on preventing the progression of Type II diabetes toward cognitive decline and Type III diabetes risk.

This repository contains the Flask migration of the original WordPress site for [www.mindfuldiabetes.org](https://www.mindfuldiabetes.org/). It preserves the published pages, article library, media assets, donation flow, newsletter form, search experience, and sitemap in a lighter Python application that is easier to maintain and deploy.

<p>
  <a href="https://www.mindfuldiabetes.org/"><img alt="Visit Website" src="https://img.shields.io/badge/Visit-Website-1f7a5c?style=for-the-badge"></a>
  <a href="https://www.mindfuldiabetes.org/guide/"><img alt="Read the Guide" src="https://img.shields.io/badge/Read-The%20Guide-255f85?style=for-the-badge"></a>
  <a href="https://www.mindfuldiabetes.org/research/"><img alt="Explore Research" src="https://img.shields.io/badge/Explore-Research-6f4e7c?style=for-the-badge"></a>
  <a href="https://www.mindfuldiabetes.org/health-tools/"><img alt="Use Health Tools" src="https://img.shields.io/badge/Use-Health%20Tools-bb5f38?style=for-the-badge"></a>
  <a href="https://www.mindfuldiabetes.org/donation/"><img alt="Donate" src="https://img.shields.io/badge/Support-Donate-8a2f43?style=for-the-badge"></a>
</p>

---

## Project Status

Status: active Flask migration from WordPress.

Current coverage:

- 8 published WordPress pages migrated into Flask.
- 89 published WordPress posts available at their original slug paths.
- Homepage content served at `/`.
- Article guide served at `/guide/`.
- Search served at `/search/`.
- Research hub served at `/research/`.
- Health tools hub served at `/health-tools/`.
- Volunteer page served at `/volunteer/`.
- Donation flow served at `/donation/`.
- Sitemap generated at `/sitemap.xml`.
- WordPress uploads extracted into `static/uploads`.
- Newsletter forms wired for Mailchimp when environment values are provided.
- PayPal hosted donation button support.

---

## Website Navigation

Use these links when reviewing or sharing the public site.

| Page | Public URL | Purpose |
| --- | --- | --- |
| Home | [www.mindfuldiabetes.org](https://www.mindfuldiabetes.org/) | Main landing page and mission overview |
| Guide | [www.mindfuldiabetes.org/guide/](https://www.mindfuldiabetes.org/guide/) | Article library and educational posts |
| Search | [www.mindfuldiabetes.org/search/](https://www.mindfuldiabetes.org/search/) | Site-wide search across pages, posts, and tools |
| Research | [www.mindfuldiabetes.org/research/](https://www.mindfuldiabetes.org/research/) | Research publications and scientific context |
| Health Tools | [www.mindfuldiabetes.org/health-tools/](https://www.mindfuldiabetes.org/health-tools/) | Wellness tools and interactive resources |
| Volunteer | [www.mindfuldiabetes.org/volunteer/](https://www.mindfuldiabetes.org/volunteer/) | Volunteer interest and community support |
| Sponsors | [www.mindfuldiabetes.org/sponsors/](https://www.mindfuldiabetes.org/sponsors/) | Sponsor recognition and partnership context |
| Donate | [www.mindfuldiabetes.org/donation/](https://www.mindfuldiabetes.org/donation/) | PayPal hosted donation flow |
| Sitemap | [www.mindfuldiabetes.org/sitemap.xml](https://www.mindfuldiabetes.org/sitemap.xml) | Search engine sitemap |

Helpful redirects:

- `/blog/` redirects to `/guide/`.
- `/donate/` redirects to `/donation/`.
- Published WordPress pages and posts keep clean slug paths where possible.

---

## Repository Navigation

- [Project Status](#project-status)
- [Website Navigation](#website-navigation)
- [What This Site Does](#what-this-site-does)
- [Repository Layout](#repository-layout)
- [Quick Start](#quick-start)
- [Heroku Deployment](#heroku-deployment)
- [Environment Variables](#environment-variables)
- [Newsletter Setup](#newsletter-setup)
- [Donation Setup](#donation-setup)
- [Content Model](#content-model)
- [Search and Sitemap](#search-and-sitemap)
- [Testing](#testing)
- [Public Repo Safety](#public-repo-safety)
- [Maintenance Tips](#maintenance-tips)
- [Troubleshooting](#troubleshooting)

---

## What This Site Does

The Flask application turns the migrated WordPress content into a maintainable site with:

- A homepage built from the original `mindful` page.
- A guide page that paginates educational articles.
- A search page that indexes page titles, slugs, excerpts, body text, research entries, health tools, and volunteer content.
- Article pages with cleaned WordPress HTML, media handling, YouTube embedding, and article navigation.
- Donation shortcodes replaced with a PayPal hosted button form.
- Newsletter subscription forms that connect to Mailchimp when credentials are configured.
- Static asset support for images, audio, video, CSS, icons, and migrated upload files.
- A generated sitemap for all published pages and posts.

The app is intentionally small: Flask, Jinja templates, a JSON content seed, and tests.

---

## Repository Layout

```text
Mindful-Diabetes-Site/
|-- app.py
|-- mindful_diabetes/
|   |-- __init__.py
|   `-- app.py
|-- templates/
|   |-- base.html
|   |-- home.html
|   |-- guide.html
|   |-- post.html
|   |-- page.html
|   |-- research.html
|   |-- health_tools.html
|   |-- volunteer.html
|   |-- search.html
|   |-- subscribe.html
|   `-- sitemap.xml
|-- static/
|   |-- css/site.css
|   |-- img/
|   `-- uploads/
|-- mindful_diabetes_wp_parse_outputs/
|   |-- wp_migration_outputs/
|   |   `-- flask_content_seed.json
|   `-- wp_migration_parse/
|       `-- parse_wxr.py
|-- tools/
|   `-- extract_wpress_uploads.py
|-- tests/
|   `-- test_routes.py
|-- requirements.txt
|-- Procfile
|-- .python-version
|-- app.json
|-- .slugignore
|-- .env.example
|-- .gitignore
`-- README.md
```

Key files:

- `app.py`: local Flask entry point.
- `mindful_diabetes/app.py`: application factory, routes, content loading, cleanup helpers, Mailchimp integration, donation rendering, search, and sitemap behavior.
- `mindful_diabetes_wp_parse_outputs/wp_migration_outputs/flask_content_seed.json`: migrated public page/post content used by the app.
- `templates/`: Jinja views for the website.
- `static/css/site.css`: primary styling.
- `tests/test_routes.py`: route, rendering, search, donation, newsletter, and migration coverage tests.
- `Procfile`: Heroku web process command.
- `.python-version`: Python version requested by Heroku and local tooling.
- `app.json`: Heroku app metadata and safe config variable definitions.
- `.slugignore`: Heroku-only deploy exclusions for large/private non-runtime files.

---

## Quick Start

From the project folder:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m flask --app app run --port 5000
```

Then open:

```text
http://127.0.0.1:5000
```

Useful local URLs:

```text
http://127.0.0.1:5000/
http://127.0.0.1:5000/guide/
http://127.0.0.1:5000/search/
http://127.0.0.1:5000/research/
http://127.0.0.1:5000/health-tools/
http://127.0.0.1:5000/donation/
http://127.0.0.1:5000/sitemap.xml
```

Tip: restart the Flask server after editing `.env`, `requirements.txt`, or the content seed.

---

## Heroku Deployment

This project includes Heroku-ready files:

```text
Procfile
.python-version
app.json
.slugignore
requirements.txt
```

The web process runs the Flask app through Gunicorn:

```text
web: gunicorn app:app
```

The Python runtime is requested with `.python-version`:

```text
3.13
```

Basic Heroku flow:

```bash
heroku create mindful-diabetes-site
heroku buildpacks:set heroku/python
heroku config:set PAYPAL_HOSTED_BUTTON_ID=5BM2YU7LNZDVJ
heroku config:set MAILCHIMP_API_KEY=your-mailchimp-key
heroku config:set MAILCHIMP_AUDIENCE_ID=your-audience-id
heroku config:set MAILCHIMP_SERVER_PREFIX=us21
heroku config:set MAILCHIMP_TAGS="Mindful Diabetes Subscribers"
git push heroku main
heroku open
```

If newsletter subscriptions are not ready yet, skip the Mailchimp config vars. The site can still run without them.

Important Heroku media note:

- Heroku rejected a build when the compressed slug reached `1.1G`.
- `.slugignore` excludes large audio/video files (`.wav`, `.mp3`, `.mp4`, etc.) from Heroku's deploy package.
- Pages that reference excluded media may show missing audio/video until those assets are moved to external storage and the URLs are updated.
- Images and normal site files remain deployable from the app.

Tip: keep all production secrets in Heroku config vars. Do not commit `.env`.

---

## Environment Variables

Create a local `.env` file from `.env.example`:

```bash
cp .env.example .env
```

Then fill only the values needed for your local or production environment.

```bash
PAYPAL_HOSTED_BUTTON_ID=5BM2YU7LNZDVJ

MAILCHIMP_API_KEY=
MAILCHIMP_AUDIENCE_ID=
MAILCHIMP_SERVER_PREFIX=
MAILCHIMP_TAGS=Mindful Diabetes Subscribers
```

Environment variable reference:

| Variable | Required | Purpose |
| --- | --- | --- |
| `PAYPAL_HOSTED_BUTTON_ID` | Optional | Overrides the default PayPal hosted donation button ID |
| `MAILCHIMP_API_KEY` | Optional | Enables newsletter subscription when paired with an audience ID |
| `MAILCHIMP_AUDIENCE_ID` | Optional | Mailchimp list/audience ID for subscribers |
| `MAILCHIMP_SERVER_PREFIX` | Optional | Mailchimp data center prefix, such as `us21` |
| `MAILCHIMP_TAGS` | Optional | Comma-separated Mailchimp tags applied to new subscribers |
| `CONTENT_PATH` | Optional | Overrides the default `flask_content_seed.json` location |

Important: `.env` is intentionally ignored by Git. Do not commit real Mailchimp keys, private tokens, database dumps, or local backups.

---

## Newsletter Setup

Newsletter forms appear in the footer, homepage, guide page, article pages, and subscribe route.

To enable live subscriptions:

1. Create or open `.env`.
2. Add `MAILCHIMP_API_KEY`.
3. Add `MAILCHIMP_AUDIENCE_ID`.
4. Add `MAILCHIMP_SERVER_PREFIX` if the prefix is not already included at the end of the API key.
5. Restart Flask.
6. Test the form locally before deploying.

Behavior:

- If Mailchimp values are missing, newsletter UI can render without submitting to Mailchimp.
- If `MAILCHIMP_SERVER_PREFIX` is blank, the app tries to infer it from an API key ending like `-us21`.
- Subscribers are sent to Mailchimp using a hashed email member ID.
- Optional tags from `MAILCHIMP_TAGS` are applied to the subscriber.

Tip: keep `.env.example` safe and blank for private values. It should show names and defaults, not secrets.

---

## Donation Setup

The old WordPress GiveWP blocks are replaced during rendering with a PayPal hosted button.

Default hosted button ID:

```text
5BM2YU7LNZDVJ
```

Override locally or in production with:

```bash
PAYPAL_HOSTED_BUTTON_ID=your-hosted-button-id
```

Public donation link:

[www.mindfuldiabetes.org/donation/](https://www.mindfuldiabetes.org/donation/)

Tip: PayPal hosted button IDs are usually safe to render publicly because they are meant to appear in client-facing donation forms. Treat account credentials, API secrets, webhook secrets, and private PayPal dashboard data as sensitive.

---

## Content Model

The content seed is loaded from:

```text
mindful_diabetes_wp_parse_outputs/wp_migration_outputs/flask_content_seed.json
```

Each content item is normalized at startup with:

- `canonical_path`
- excerpt text
- preview image metadata
- article media metadata
- article section title
- searchable text

The app builds:

- `published_pages`: published WordPress pages.
- `latest_posts`: published WordPress posts sorted newest first.
- `pages_by_slug`: page lookup by slug.
- `posts_by_slug`: post lookup by slug.
- `nav_pages`: primary navigation pages.

Current migrated pages:

| Title | Slug | Public URL |
| --- | --- | --- |
| Home | `mindful` | [www.mindfuldiabetes.org](https://www.mindfuldiabetes.org/) |
| Guide | `guide` | [www.mindfuldiabetes.org/guide/](https://www.mindfuldiabetes.org/guide/) |
| Sponsors | `sponsors` | [www.mindfuldiabetes.org/sponsors/](https://www.mindfuldiabetes.org/sponsors/) |
| Donation | `donation` | [www.mindfuldiabetes.org/donation/](https://www.mindfuldiabetes.org/donation/) |
| Donation Confirmation | `donation-confirmation` | [www.mindfuldiabetes.org/donation-confirmation/](https://www.mindfuldiabetes.org/donation-confirmation/) |
| Donation Failed | `donation-failed` | [www.mindfuldiabetes.org/donation-failed/](https://www.mindfuldiabetes.org/donation-failed/) |
| Donor Dashboard | `donor-dashboard` | [www.mindfuldiabetes.org/donor-dashboard/](https://www.mindfuldiabetes.org/donor-dashboard/) |
| JOIN THE CAMINO | `jointhecamino` | [www.mindfuldiabetes.org/jointhecamino/](https://www.mindfuldiabetes.org/jointhecamino/) |

Featured recent posts in the current seed:

- [Diabetes Health AI Tool: JEIR Updates](https://www.mindfuldiabetes.org/diabetes-health-jeir-updates/)
- [Memovela: A Wellness Tracker for Insulin Resistance & Brain Health](https://www.mindfuldiabetes.org/memovela/)
- [Crossing the Finish Line: A Scientific & Personal Journey Through the Chicago Marathon 4:35](https://www.mindfuldiabetes.org/chicago-marathon-diabetes/)
- [From Beer Belly to Finish Line: Running for Health and the Chicago Diabetes Project](https://www.mindfuldiabetes.org/visceral-fat-diabetes-connection/)
- [From Rays to Resilience: How Sunlight Builds Better Bones](https://www.mindfuldiabetes.org/vitamin-d-bone-health/)
- [Hot Days, Healthy Ways: Managing Blood Sugar in the Summer Months](https://www.mindfuldiabetes.org/summer-diabetes/)

---

## Search and Sitemap

Search route:

```text
/search/
```

Search currently looks across:

- Page titles.
- Page slugs.
- Article titles.
- Article slugs.
- Excerpts.
- Cleaned article/page text.
- Research content.
- Health tools content.
- Volunteer content.

Sitemap route:

```text
/sitemap.xml
```

The sitemap includes every published page and post from the content seed. Use it after migrations or content updates to confirm public URLs are discoverable.

Tip: after changing content, run tests and open `/sitemap.xml` locally to confirm new URLs appear as expected.

---

## Testing

Run the full test suite:

```bash
.venv/bin/python -m pytest
```

Run concise output:

```bash
.venv/bin/python -m pytest -q
```

The tests cover:

- Homepage rendering.
- Guide pagination.
- Search behavior.
- Page and post routing.
- Redirects.
- Newsletter behavior.
- Mailchimp request construction.
- PayPal donation rendering.
- Sitemap generation.
- Migrated content coverage.

---

## Public Repo Safety

This repository is intended to be safe for a public GitHub repository when the ignore rules are respected.

Already ignored:

- `.env` and local environment variants.
- Python caches.
- Local virtual environments.
- Pytest cache.
- macOS metadata.
- WordPress backup archives.
- Database/export formats.
- WordPress XML exports.
- Migration CSV artifacts.
- Old WordPress debug logs.
- Mailchimp debug log artifacts from the imported upload tree.

Before pushing:

```bash
git status --short
```

Then confirm these are not staged:

- `.env`
- `.venv/`
- `__pycache__/`
- `.pytest_cache/`
- `*.wpress`
- `*.sql`
- `*.db`
- `*.sqlite`
- `mindfuldiabetesinc.WordPress.*.xml`
- `static/uploads/trustedlogin-logs/`
- `static/uploads/mailchimp-for-wp/debug-log.php`

Optional extra check:

```bash
rg -n --hidden "MAILCHIMP_API_KEY=.+|BEGIN .*PRIVATE KEY|sk-[A-Za-z0-9]|ghp_[A-Za-z0-9]|AWS_SECRET|DATABASE_URL" .
```

Tip: if a secret ever gets committed, rotate the secret immediately. Removing it from a later commit is not enough once it has been pushed publicly.

---

## Maintenance Tips

Content updates:

- Update `flask_content_seed.json` when adding migrated page/post content.
- Keep slugs stable so existing public links continue to work.
- Run the test suite after changing routes, templates, content parsing, or shortcode cleanup.

Design updates:

- Keep shared layout changes in `templates/base.html`.
- Keep reusable partials in `_newsletter_form.html`, `_social_links.html`, `_article_navigation.html`, and `_volunteer_callout.html`.
- Keep visual styling in `static/css/site.css`.

Media updates:

- Keep public images, audio, and video under `static/uploads` or `static/img`.
- Avoid committing temporary export folders or backup archives.
- Consider external media hosting or Git LFS if large media files become difficult to manage in Git.

Deployment updates:

- Set environment variables in the host platform, not in the repository.
- Confirm the production domain is `https://www.mindfuldiabetes.org`.
- Test `/`, `/guide/`, `/search/`, `/donation/`, `/subscribe/`, and `/sitemap.xml` after deployment.

---

## Troubleshooting

### Flask cannot find the content seed

Confirm this file exists:

```text
mindful_diabetes_wp_parse_outputs/wp_migration_outputs/flask_content_seed.json
```

If you store it elsewhere, set:

```bash
CONTENT_PATH=/absolute/path/to/flask_content_seed.json
```

### Newsletter submissions do not work

Check:

- `MAILCHIMP_API_KEY` is set.
- `MAILCHIMP_AUDIENCE_ID` is set.
- `MAILCHIMP_SERVER_PREFIX` is set or can be inferred from the API key suffix.
- Flask was restarted after editing `.env`.

### Donation button is wrong

Set:

```bash
PAYPAL_HOSTED_BUTTON_ID=correct-button-id
```

Then restart Flask and revisit:

```text
http://127.0.0.1:5000/donation/
```

### Static media is missing

Confirm the referenced files exist under:

```text
static/uploads/
```

If media was newly extracted from a private backup, review files before committing and make sure debug logs, backups, and private exports remain ignored.

### A page works without a trailing slash but redirects

That is expected. The app canonicalizes published pages and posts to slash-ending paths where appropriate.

---

## Related Public Links

<p>
  <a href="https://www.mindfuldiabetes.org/"><img alt="Home" src="https://img.shields.io/badge/Home-www.mindfuldiabetes.org-1f7a5c?style=flat-square"></a>
  <a href="https://www.mindfuldiabetes.org/guide/"><img alt="Guide" src="https://img.shields.io/badge/Guide-Articles-255f85?style=flat-square"></a>
  <a href="https://www.mindfuldiabetes.org/research/"><img alt="Research" src="https://img.shields.io/badge/Research-Publications-6f4e7c?style=flat-square"></a>
  <a href="https://www.mindfuldiabetes.org/volunteer/"><img alt="Volunteer" src="https://img.shields.io/badge/Volunteer-Get%20Involved-bb5f38?style=flat-square"></a>
  <a href="https://www.mindfuldiabetes.org/donation/"><img alt="Donate" src="https://img.shields.io/badge/Donate-Support%20the%20Mission-8a2f43?style=flat-square"></a>
</p>

---

## License and Use

Add the project license before publishing if this repository is intended for open-source reuse. If the repository is public only for transparency or deployment history, document which content, images, and media assets are owned by Mindful Diabetes and whether reuse is permitted.

---

Built for [www.mindfuldiabetes.org](https://www.mindfuldiabetes.org/).
