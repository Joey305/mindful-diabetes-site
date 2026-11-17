# Codex task — Mindful Diabetes protein fingerprint research feature

You are given the *updated, scientifically corrected* article package.

## Goal
Implement the article **Your Blood Has a Hidden Protein Fingerprint. Could It Reveal Insulin Resistance?** using the current Mindful Diabetes website architecture and design conventions, with proper references, SEO, responsive image handling, feed/sitemap updates, and article listing/related article links.

## Read in this order
1. `README_FIRST.md`
2. `article/ARTICLE_READY_FOR_EDITORIAL_REVIEW.md`
3. `sources/SOURCE_VERIFICATION.md`
4. `sources/SCIENTIFIC_FIGURE_AUDIT.md`
5. `sources/FIGURE_CORRECTIONS_COMPLETED.md`
6. `metadata/figure_manifest.json`
7. `metadata/seo.json` and `metadata/editorial_extras.md`

## Critical artwork instructions
- Use **only** `assets/visual_final/` illustrations for the 7 figures. All older DRAFT assets are superseded.
- Use WebP as displayed assets and PNG as full-size click-to-zoom targets. No “Figure N” labels inside artwork.
- Match `figure_number` to each position and exact caption/alt text from the manifest.
- Figure 5 is **schematic**: the bottom panel is directional biological context, not fabricated or reconstructed quantitative participant data. Keep this clear in its caption.
- Treat Figure 4's tissue arrows as Human Protein Atlas-inferred conceptual relationships.
- Figure 6 R² is measured-versus-estimated clamp M value in independent n=43 validation, NOT clinical diagnostic sensitivity.
- Figure 7 compares UK Biobank future T2D C-indices, NOT individual risk probabilities.
- Original square MDI branding is supplied under `brand/`.

## Publication gates
- New article-specific wide hero image and social OG asset **still need editorial approval**; neither is supplied here.
- Final visual/editorial sign-off is needed on the corrected seven educational illustrations.
- Validate numerical details against primary DOI https://doi.org/10.1038/s42255-026-01662-1.
- Follow the website's standard structured data, RSS, sitemap, canonical route and meta conventions; do not invent the actual posting date.
- Do not publish to production until release gates are satisfied. Report changes, build tests, remaining approvals, and deployment status.

Suggested slug: `/blood-protein-fingerprint-insulin-resistance-2026/`.
