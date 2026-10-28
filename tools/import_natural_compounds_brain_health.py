#!/usr/bin/env python3
"""Import the approved Nature Under the Microscope article package.

The source manuscript and figure manifest remain in ``content/articles`` so future
edits can be audited without reverse-engineering the rendered HTML record.
"""

from __future__ import annotations

import html
import json
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
HANDOFF = Path("/tmp/mdi-v2-handoff/MDI_Nature_Article_Republish_Handoff")
ARCHIVE = ROOT / "content/articles/2026-10/natural-compounds-brain-health"
UPLOADS = ROOT / "static/uploads/2026/10"
CONTENT = ROOT / "mindful_diabetes_wp_parse_outputs/wp_migration_outputs/flask_content_seed.json"
SLUG = "natural-compounds-brain-health"
TITLE = "Nature Under the Microscope: Can Mushrooms, Spices, and Ancient Trees Protect Our Brains?"
CANONICAL = "https://mindfuldiabetes.org/natural-compounds-brain-health/"
PUBLISHED = "2026-10-28 09:00:00-04:00"


def inline(text: str) -> str:
    value = html.escape(text, quote=False)

    def link(match: re.Match[str]) -> str:
        label, href = match.groups()
        parsed = urlparse(href)
        external = bool(parsed.netloc) and not parsed.netloc.endswith("mindfuldiabetes.org")
        attrs = ' target="_blank" rel="noopener noreferrer"' if external else ""
        return f'<a href="{html.escape(href, quote=True)}"{attrs}>{inline(label)}</a>'

    value = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", link, value)
    value = re.sub(r"\[\[(\d+)\]\]\(#(ref-\d+)\)", r'<a href="#\2" aria-label="Reference \1">[\1]</a>', value)
    value = re.sub(r"`([^`]+)`", r"<code>\1</code>", value)
    value = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", value)
    return re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", value)


def figure_html(item: dict, hero: bool = False) -> str:
    asset_id = item["asset_id"]
    webp = f"/static/uploads/2026/10/{asset_id}.webp"
    png = f"/static/uploads/2026/10/{asset_id}.png"
    loading = 'loading="eager" fetchpriority="high"' if hero else 'loading="lazy" decoding="async"'
    references = " ".join(f'<a href="#ref-{number}" aria-label="Reference {number}">[{number}]</a>' for number in item["references"])
    return (
        f'<figure data-image-slot="{asset_id}"><a href="{png}" target="_blank" rel="noopener noreferrer" '
        f'aria-label="Open full-resolution {html.escape(item["label"], quote=True)} in a new tab"><picture>'
        f'<source type="image/webp" srcset="/static/uploads/2026/10/{asset_id}-724.webp 724w, '
        f'/static/uploads/2026/10/{asset_id}-1024.webp 1024w, {webp} 1600w" sizes="(max-width: 820px) 100vw, 820px">'
        f'<img src="{webp}" width="1600" height="900" alt="{html.escape(item["alt"], quote=True)}" '
        f'title="{html.escape(item["label"], quote=True)} — open full resolution" {loading}></picture></a>'
        f'<figcaption><strong>{html.escape(item["label"])}.</strong> {inline(item["caption"])} '
        f'<span>Credit: {html.escape(item["credit"])}.</span>{(" " + references) if references else ""}</figcaption></figure>'
    )


def render_table(lines: list[str]) -> str:
    rows = [[cell.strip() for cell in line.strip().strip("|").split("|")] for line in lines]
    headers, body = rows[0], rows[2:]
    header_html = "".join(f'<th scope="col">{inline(cell)}</th>' for cell in headers)
    body_html = "".join("<tr>" + "".join(f"<td>{inline(cell)}</td>" for cell in row) + "</tr>" for row in body)
    return f'<div class="article-table-wrap" tabindex="0" aria-label="Scrollable comparison table"><table><thead><tr>{header_html}</tr></thead><tbody>{body_html}</tbody></table></div>'


def render_markdown(markdown: str, figures: dict[str, dict]) -> str:
    lines, output, index, list_type = markdown.splitlines(), [], 0, None

    def close_list() -> None:
        nonlocal list_type
        if list_type:
            output.append(f"</{list_type}>")
            list_type = None

    while index < len(lines):
        line = lines[index].strip()
        if not line:
            close_list(); index += 1; continue
        marker = re.fullmatch(r"<!-- FIGURE: ([\w_]+) -->", line)
        if marker:
            close_list()
            asset_id = marker.group(1)
            # The cover is rendered once by the shared post hero component.
            if not asset_id.startswith("00_"):
                output.append(figure_html(figures[asset_id]))
            index += 1; continue
        if line.startswith("|"):
            close_list(); table_lines = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                table_lines.append(lines[index].strip()); index += 1
            output.append(render_table(table_lines)); continue
        heading = re.match(r"^(#{2,3})\s+(.+)$", line)
        if heading:
            close_list(); level = len(heading.group(1)); text = heading.group(2)
            slug = re.sub(r"[^a-z0-9]+", "-", re.sub(r"<[^>]+>", "", text.lower())).strip("-")
            output.append(f'<h{level} id="{slug}">{inline(text)}</h{level}>')
            index += 1; continue
        if line.startswith("> "):
            close_list(); output.append(f"<blockquote><p>{inline(line[2:])}</p></blockquote>")
            index += 1; continue
        unordered, ordered = re.match(r"^-\s+(.+)$", line), re.match(r"^\d+\.\s+(.+)$", line)
        if unordered or ordered:
            wanted = "ul" if unordered else "ol"
            if list_type != wanted:
                close_list(); output.append(f"<{wanted}>"); list_type = wanted
            output.append(f"<li>{inline((unordered or ordered).group(1))}</li>")
            index += 1; continue
        close_list()
        paragraph = [line]
        while index + 1 < len(lines):
            upcoming = lines[index + 1].strip()
            if not upcoming or upcoming.startswith(("#", "|", "> ", "- ", "<!-- FIGURE:")) or re.match(r"^\d+\.\s+", upcoming):
                break
            paragraph.append(upcoming); index += 1
        output.append(f"<p>{inline(' '.join(paragraph))}</p>")
        index += 1
    close_list()
    return "\n".join(output)


def copy_assets(manifest: list[dict]) -> None:
    UPLOADS.mkdir(parents=True, exist_ok=True)
    for item in manifest:
        asset_id = item["asset_id"]
        for source_key, suffix in (("webp_path", ".webp"), ("png_path", ".png")):
            shutil.copy2(HANDOFF / item[source_key], UPLOADS / f"{asset_id}{suffix}")
        webp = UPLOADS / f"{asset_id}.webp"
        for width in (724, 1024):
            subprocess.run(["cwebp", "-quiet", "-q", "90", "-resize", str(width), "0", str(webp), "-o", str(UPLOADS / f"{asset_id}-{width}.webp")], check=True)


def main() -> None:
    if not HANDOFF.exists():
        raise SystemExit(f"Missing extracted handoff: {HANDOFF}")
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    for relative in ("README_START_HERE.md", "content/ARTICLE.md", "editorial/figure_manifest.json", "editorial/EVIDENCE_REGISTER.csv", "seo/seo_metadata.json"):
        destination = ARCHIVE / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(HANDOFF / relative, destination)
    manifest = json.loads((HANDOFF / "editorial/figure_manifest.json").read_text(encoding="utf-8"))
    figure_index = {item["asset_id"]: item for item in manifest}
    manuscript = (HANDOFF / "content/ARTICLE.md").read_text(encoding="utf-8")
    if len(re.findall(r"<!-- FIGURE: [\w_]+ -->", manuscript)) != 13:
        raise SystemExit("Expected 13 figure markers in the approved manuscript.")
    copy_assets(manifest)
    body = render_markdown("\n".join(manuscript.splitlines()[5:]), figure_index)
    modified = datetime.now().astimezone().isoformat(timespec="seconds")
    items = json.loads(CONTENT.read_text(encoding="utf-8"))
    old = next((item for item in items if item.get("slug") == "diabetes-supplements"), {})
    items = [item for item in items if item.get("slug") not in {"diabetes-supplements", SLUG}]
    items.append({
        "id": old.get("id", "4271"), "type": "post", "status": "publish", "title": TITLE,
        "slug": SLUG, "url": CANONICAL, "date": PUBLISHED, "modified": modified,
        "parent": "0", "menu_order": "0", "categories": ["Pathways to Wellness"],
        "tags": ["lion's mane mushroom", "turmeric", "curcumin", "ginkgo biloba", "brain health", "clinical trials"],
        "featured_image_id": "00_hero_nature_under_microscope", "template": "default",
        "excerpt_html": "What do a remarkable mushroom, a golden spice, and an ancient tree teach us about brain health? Investigate real clinical trials, molecular biology, and the surprising limits of supplement claims.",
        "seo_title": "Lion's Mane, Turmeric & Ginkgo: Brain Health Science | MDI",
        "meta_description": "Can lion's mane, turmeric, or ginkgo protect your brain? Explore the chemistry, human trials, diabetes connections, and safety behind the claims.",
        "canonical_url": CANONICAL, "og_title": "Nature Under the Microscope | Mindful Diabetes Inc.",
        "og_description": "The science of lion's mane, turmeric, and ginkgo: fascinating chemistry, mixed human evidence, and what matters for brain and metabolic health.",
        "og_image": "/static/uploads/2026/10/00_hero_nature_under_microscope.webp",
        "hero_image": "/static/uploads/2026/10/00_hero_nature_under_microscope.webp",
        "hero_image_webp_srcset": "/static/uploads/2026/10/00_hero_nature_under_microscope-724.webp 724w, /static/uploads/2026/10/00_hero_nature_under_microscope-1024.webp 1024w, /static/uploads/2026/10/00_hero_nature_under_microscope.webp 1600w",
        "hero_alt": figure_index["00_hero_nature_under_microscope"]["alt"],
        "hero_caption": figure_index["00_hero_nature_under_microscope"]["caption"],
        "hero_width": 1600, "hero_height": 900, "hero_title": TITLE,
        "hero_description": "Original Mindful Diabetes science illustration created for this article.",
        "editorial_history": "This completely rewritten article replaces an earlier Mindful Diabetes article first published January 28, 2025.",
        "memovela_resource_blurb": "A skeptical guide to lion's mane, turmeric, and ginkgo: what human trials do—and do not—show about brain and metabolic health.",
        "memovela_sync": False, "content_html": body,
    })
    serialized = json.dumps(items, ensure_ascii=False, indent=2)
    # Retain the legacy route only at the HTTP redirect. Existing articles may
    # still mention it in contextual reading links, which should now point
    # straight to the canonical article rather than taking an avoidable hop.
    serialized = serialized.replace(
        "https://mindfuldiabetes.org/diabetes-supplements/",
        CANONICAL,
    )
    CONTENT.write_text(serialized + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
