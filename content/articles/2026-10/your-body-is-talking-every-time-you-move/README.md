# Mindful Diabetes: Your Body Is Talking Every Time You Move

**STATUS:** Complete editorial handoff, ready for implementation by Codex and final human review. This ZIP is an article production package, **not a downloadable guide**. No PDF, PDF landing page, or new guide should be added to the public website.

## Purpose

Publish a new English-language long-form *Pathways to Wellness* article explaining October 2026 exercise proteomics research, glucose uptake through GLUT4, limits of a short 2026 exercise-snack trial, and practical movement habits. The implementation must follow the existing Flask-based mindfuldiabetes.org article design, metadata, feeds, sitemap, search and responsive patterns.

## Read first

1. `article/your-body-is-talking-every-time-you-move.md` - complete edited article including SEO frontmatter, all image placements, captions, internal links, app CTA and references.
2. `implementation/CODEX_PROMPT.md` - paste this prompt into Codex with the ZIP, in the website repository.
3. `images/IMAGE_MANIFEST.md` - exact placement order, captions, alt text, source names, export formats.
4. `research/sources_verified.md` - verified DOIs and supporting evidence.
5. `research/editorial_claim_audit.md` - claims that must not be strengthened accidentally.

## Contents

- `article/*.md`: article, Memovela blurb, social/email copy.
- `article/metadata.json`: machine-readable title, slug, SEO and canonical link suggestions.
- `images/hero-body-communication.webp`: optimized article cover.
- `images/hero-body-communication.jpg`: JPEG cover fallback.
- `images/og-body-communication.jpg`: 1200x630 social cover crop.
- `images/figure-0*.webp`: recommended inline production images (1600x900).
- `images/figure-0*.png`: raster fallbacks (1600x900).
- `images/figure-0*.svg`: editable original diagrams (1600x900 viewBox) for later updates.
- `images/source/hero-original.png`: unedited original concept art.
- `images/IMAGE_MANIFEST.md` and `images/assets.json`: human-readable and structured image details.
- `implementation/CODEX_PROMPT.md`: concrete implementation tasks/tests.
- `research/*`: citations and claim audit.

## Expected published URL

https://mindfuldiabetes.org/your-body-is-talking-every-time-you-move/

This is a proposed slug. Check for conflicts against the actual repository before using it; retain the chosen canonical slug consistently across route, sitemap, feed and links.

## How to implement

- Work in existing website repository, inspect the current article content architecture and adopt its conventions.
- Use the Markdown as the authoritative **copy**, not as a mandate to implement raw frontmatter in the live site.
- Do not render the frontmatter or duplicate the H1 in a page that already displays it from metadata.
- Use local WebP images. Use OG JPEG as `og:image`, or the site's existing preferred equivalent.
- Keep all six scientific references, including the ADA and WHO sources, in the displayed article's source section.
- Preserve original image captions and descriptive alt text. Do not use the screenshots of the journal figures.
- Preserve the existing Memovela article CTA behavior. The iOS App Store link is verified; optionally include the existing Memovela web link.
- Do not make changes to the public guide/PDF download collection.
- Use the actual site's publishing date and avoid claiming to have deployed before tests finish.

## Scientific boundaries

The central human study is a molecular atlas after one cycling workout, not a clinical outcomes trial. The follow-up short-bout study had n=31, ran over two days, involved *vigorous* exercise, and did not significantly change mean glucose. Avoid making clinical or causal claims beyond these results. The figure diagrams are conceptual original artwork.
