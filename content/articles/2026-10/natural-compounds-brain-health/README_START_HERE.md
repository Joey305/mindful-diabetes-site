# MDI — Nature Under the Microscope | Complete Article Republish Handoff

**Status:** Complete editable draft and prepared implementation assets. **Not yet committed, deployed, or published.** This ZIP is intended to be dropped into Codex inside the existing Mindful Diabetes website repository.

## What this package is

A substantially rewritten article prepared for publication at:

**https://mindfuldiabetes.org/natural-compounds-brain-health/**

The previous January 28, 2025 page at **https://mindfuldiabetes.org/diabetes-supplements/** must permanently redirect (HTTP 301) to the new page. The previous URL must never become a 401, 404, soft 404, or login-only route.

The editorial overhaul replaces strong supplement-prevention claims and an outdated diabetes/Alzheimer terminology framework with an engaging, evidence-checked long-form science story covering chemistry, neuroscience, pharmacology, human trials, safety, and everyday metabolic-health priorities.

### Deliverables

| Location | Use |
|---|---|
| `content/ARTICLE.md` | **Canonical article text**, including all citations, FAQ, two tables, and **13 `<!-- FIGURE: ... -->` insertion markers** |
| `ARTICLE_PREVIEW.html` | Fully styled standalone preview (open after extracting the ZIP); does not represent the live website implementation |
| `editorial/figure_manifest.json` | Exact reading order, asset filenames, captions, alt text, credit, and scientific references for all 13 visuals |
| `assets/webp_optimized/` | 13 website-ready WebP files, 1600×900, brand embedded |
| `assets/png_hires/` | 13 higher-resolution 2400×1350 PNG originals, useful for zoom/download/sharing |
| `assets/svg_editable/` | 12 figure SVGs (raster hero is excluded); see caveat below |
| `assets/editable_sources/` | Editable PowerPoint source for six supplemental panels |
| `assets/branding/` | Exact user-provided MDI logo (only approved branding reference) |
| `assets/contact_sheet_all_13.jpg` | All visuals in one review sheet |
| `seo/seo_metadata.json` | SEO title, canonical URL, 301 migration rules, dates, and social image |
| `seo/FAQ_SCHEMA_TEMPLATE.json` | FAQ structured-data draft — only integrate if site already supports appropriate FAQ schema and visible questions |
| `seo/SEO_AND_INTERNAL_LINKS.md` | URL migration and link plan, redirects, feeds, and on-page SEO checks |
| `implementation/CODEX_PROMPT.md` | **Copy/paste this into Codex while the ZIP is available** |
| `implementation/QA_CHECKLIST.md` | Technical, scientific, accessibility, visual and deployment checks |
| `editorial/CORRECTIONS_AND_EDITORIAL_AUDIT.md` | What was changed from the old article and what remains out-of-scope |
| `editorial/EVIDENCE_REGISTER.csv` | Traceable research claims, designs, numbers and limitations |
| `editorial/MEMOVELA_BLURB.md` | Optional concise companion blurb for the app/article feed |

## Seven important requirements for the implementer

1. **Republish at `/natural-compounds-brain-health/`** with an unconditional **HTTP 301** from `/diabetes-supplements/`. New canonical URL must return **200 OK** and be public. Show **Published October 28, 2026**, if actually deployed on that date; retain January 28, 2025 as editorial history only. Do not leave a live duplicate of the old article.
2. **All 13 figures** must appear exactly once, in the editorial order specified in `figure_manifest.json`, placed at their markers in `ARTICLE.md`.
3. The visual assets are branded with Mindful Diabetes Inc. and its website; retain attribution in pixels, alt text, and figcaptions. Render captions as real HTML text.
4. Use accessible HTML tables for research/safety comparisons, not screenshots of the Markdown tables.
5. Preserve the site's actual subscription, donation, socials, related posts, JEIR, and Memovela behavior. Move promotional interruptions outside the core science story if the template allows; do not break their actions.
6. Remove all outdated/unsupported claims from **this article's authored copy, excerpt, metadata, and article-specific schema**. Be alert that the *shared global footer* also uses an outdated concept: see audit file; do not silently rewrite other pages.
7. **Do not claim production publication until tests, commit, deploy, and HTTP verification actually succeed.** If deployment is connected, complete it during the Codex run and return the public URL and commit/deploy IDs.

## Science and safety notes

This is a science-education article, not a supplement-purchase recommendation. Human trials differ in formulation, population, duration and endpoints. The 2026 brain/metabolic framework explicitly distinguishes diabetes, dementia, Alzheimer-associated pathology, glucose hypometabolism and brain insulin signaling dysregulation.

The experimental figures are original MDI illustrations, not external scientific figures reused without permission. SVG graphics are useful for scaling, but may include embedded image portions and are not guaranteed to have fully editable chemistry; use PNG/WebP for the production site unless vector support is tested. The six new panels have an editable PPTX.

## What to do next

Extract this updated v2 archive, open `ARTICLE_PREVIEW.html` for the full reading experience, and give Codex the extracted folder plus the contents of `implementation/CODEX_PROMPT.md`. **This v2 handoff supersedes the previous preserve-the-old-slug instructions.** Ask Codex to work inside the existing site repository, execute the QA checklist, and deploy only when checks pass.
