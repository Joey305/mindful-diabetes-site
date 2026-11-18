#!/usr/bin/env python3
"""Import the corrected 2026 protein-fingerprint article package.

The supplied Markdown remains the editorial source of truth.  This importer
only adds semantic HTML, responsive figure markup, and site metadata.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
from pathlib import Path
from urllib.parse import urlparse


CONTENT_PATH = Path("mindful_diabetes_wp_parse_outputs/wp_migration_outputs/flask_content_seed.json")
ARCHIVE_ROOT = Path("content/articles/2026-11/blood-protein-fingerprint-insulin-resistance-2026")
UPLOAD_DIR = Path("static/uploads/2026/11")
SLUG = "blood-protein-fingerprint-insulin-resistance-2026"
TITLE = "Your Blood Has a Hidden Protein Fingerprint. Could It Reveal Insulin Resistance?"
URL = f"https://mindfuldiabetes.org/{SLUG}/"
DATE = "2026-11-17 09:00:00"
MEMOVELA_RESOURCE_BLURB = (
    "Your blood carries a molecular conversation. New research suggests circulating protein patterns can help "
    "scientists understand insulin sensitivity across multiple organs. Explore how exercise, adipose signaling, "
    "glucose measures, and emerging biomarker models fit together—then use Memovela to keep track of the "
    "everyday habits you can actually observe. Memovela does not measure protein biomarkers or diagnose insulin resistance."
)


def inline_markdown(text: str) -> str:
    escaped = html.escape(text, quote=False)

    def link(match: re.Match[str]) -> str:
        label, href = match.groups()
        parsed = urlparse(href)
        attrs = ' target="_blank" rel="noopener noreferrer"' if parsed.netloc and not parsed.netloc.endswith("mindfuldiabetes.org") else ""
        return f'<a href="{html.escape(href, quote=True)}"{attrs}>{inline_markdown(label)}</a>'

    # URLs can legitimately contain balanced parentheses (for example, DOIs),
    # but must never consume the next Markdown link in a paragraph.
    escaped = re.sub(r"\[([^\]]+)\]\((https?://(?:[^\s()]|\([^)]*\))+?)\)", link, escaped)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(
        r"\*\*(.*?)\*([^*]+)\*\*\*",
        r"<strong>\1<em>\2</em></strong>",
        escaped,
    )
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", escaped)
    return escaped


def figure_html(item: dict[str, object]) -> str:
    webp = Path(str(item["webp_path"])).name
    png = Path(str(item["png_path"])).name
    number = int(item["figure_number"])
    return (
        f'<figure class="article-figure article-figure--protein-fingerprint" data-image-slot="protein-fingerprint-figure-{number}">'
        f'<a class="article-figure__expand" href="/static/uploads/2026/11/{png}" target="_blank" rel="noopener" '
        f'aria-label="Open full-resolution Figure {number}: {html.escape(str(item["figure_name"]), quote=True)}">'
        f'<img src="/static/uploads/2026/11/{webp}" width="1122" height="1402" loading="lazy" '
        f'alt="{html.escape(str(item["alt_text"]), quote=True)}"></a>'
        f'<figcaption><strong>Figure {number}.</strong> {inline_markdown(str(item["caption_subject"]))} '
        f'<span class="figure-science-source">Educational adaptation based on Kjærgaard et al., '
        f'<a href="https://doi.org/10.1038/s42255-026-01662-1" target="_blank" rel="noopener noreferrer">Nature Metabolism (2026)</a>.</span></figcaption>'
        "</figure>"
    )


def markdown_to_html(markdown: str, figures: dict[int, dict[str, object]]) -> str:
    body = re.sub(r"^---.*?---\s*", "", markdown, count=1, flags=re.DOTALL)
    body = re.sub(r"^# .+\n+", "", body)
    lines, output, index, in_list = body.splitlines(), [], 0, None

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            output.append(f"</{in_list}>")
            in_list = None

    while index < len(lines):
        line = lines[index].strip()
        if not line:
            close_list(); index += 1; continue
        figure_slot = re.match(r"<!-- FIGURE (\d+) SLOT:.*-->", line)
        if figure_slot:
            close_list()
            number = int(figure_slot.group(1))
            output.append(figure_html(figures[number]))
            index += 1
            # The supplied suggested caption belongs to the superseded draft;
            # use the corrected manifest caption exactly once.
            while index < len(lines) and (not lines[index].strip() or lines[index].lstrip().startswith("*Suggested Figure")):
                index += 1
            continue
        if line == "---":
            close_list(); output.append("<hr>"); index += 1; continue
        heading = re.match(r"^(#{2,3})\s+(.+)$", line)
        if heading:
            close_list(); level = len(heading.group(1)); output.append(f"<h{level}>{inline_markdown(heading.group(2))}</h{level}>"); index += 1; continue
        if line.startswith("|"):
            close_list()
            rows = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                cells = [cell.strip() for cell in lines[index].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells): rows.append(cells)
                index += 1
            head, *rest = rows
            output.append("<div class=\"article-table-wrap\"><table><thead><tr>" + "".join(f"<th>{inline_markdown(c)}</th>" for c in head) + "</tr></thead><tbody>" + "".join("<tr>" + "".join(f"<td>{inline_markdown(c)}</td>" for c in row) + "</tr>" for row in rest) + "</tbody></table></div>")
            continue
        unordered, ordered = re.match(r"^-\s+(.+)$", line), re.match(r"^\d+\.\s+(.+)$", line)
        if unordered or ordered:
            wanted = "ul" if unordered else "ol"
            if in_list != wanted:
                close_list(); output.append(f"<{wanted}>"); in_list = wanted
            output.append(f"<li>{inline_markdown((unordered or ordered).group(1))}</li>"); index += 1; continue
        close_list(); paragraph = [line]
        while index + 1 < len(lines):
            nxt = lines[index + 1].strip()
            if not nxt or nxt == "---" or re.match(r"^(#{2,3})\s+", nxt) or nxt.startswith(("<!-- FIGURE", "|", "- ")) or re.match(r"^\d+\.\s+", nxt): break
            paragraph.append(nxt); index += 1
        output.append(f"<p>{inline_markdown(' '.join(paragraph))}</p>"); index += 1
    close_list()
    return "\n".join(output)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_root", type=Path, help="Extracted corrected-figure handoff directory")
    args = parser.parse_args()
    source = args.source_root
    manifest = json.loads((source / "metadata/figure_manifest.json").read_text(encoding="utf-8"))
    seo = json.loads((source / "metadata/seo.json").read_text(encoding="utf-8"))
    figures = {int(item["figure_number"]): item for item in manifest}
    manuscript = (source / "article/ARTICLE_READY_FOR_EDITORIAL_REVIEW.md").read_text(encoding="utf-8")
    content_html = markdown_to_html(manuscript, figures)

    # Keep the handoff, audit trail, corrected PNG originals, and WebP display
    # assets editable in-repo.  The readme documents the unresolved approval gate.
    shutil.copytree(source, ARCHIVE_ROOT, dirs_exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    for figure in figures.values():
        for key in ("webp_path", "png_path"):
            asset = source / str(figure[key])
            shutil.copy2(asset, UPLOAD_DIR / asset.name)

    items = json.loads(CONTENT_PATH.read_text(encoding="utf-8"))
    items = [item for item in items if item.get("slug") != SLUG]
    items.append({
        "id": "protein-fingerprint-2026",
        "type": "post", "status": "publish", "title": TITLE, "slug": SLUG,
        "url": URL, "date": DATE, "modified": DATE, "parent": "0", "menu_order": "0",
        "categories": seo["categories"], "tags": seo["tags"], "template": "default",
        "excerpt_html": seo["dek"], "seo_title": seo["seo_title"],
        "meta_description": seo["meta_description"], "canonical_url": URL,
        "og_title": TITLE, "og_description": seo["meta_description"],
        "hero_image": "/static/uploads/2026/11/editorial-review/protein-fingerprint-hero-proposal.png",
        "hero_alt": "Blood-plasma sample with conceptual protein structures in a metabolic research laboratory.",
        "hero_caption": "Editorial scientific illustration for Mindful Diabetes. Molecular structures are conceptual and do not depict participant data.",
        "hero_width": 1672, "hero_height": 941,
        "og_image": "/static/uploads/2026/11/editorial-review/protein-fingerprint-social-proposal-1200x630.png",
        "publication_gate": "EDITORIAL_APPROVAL_REQUIRED_FOR_FIGURES_AND_HERO_OG",
        "figure_status": "SCIENTIFIC_CORRECTED_AWAITING_EDITORIAL_VISUAL_APPROVAL",
        "primary_paper_published": seo["primary_paper_published"],
        "memovela_resource_blurb": MEMOVELA_RESOURCE_BLURB,
        "memovela_sync": True,
        "content_html": content_html,
    })
    CONTENT_PATH.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
