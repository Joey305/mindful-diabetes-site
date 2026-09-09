#!/usr/bin/env python3
"""Import the supplied September 2026 fat-cell research feature into the site seed."""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlparse


CONTENT_PATH = Path("mindful_diabetes_wp_parse_outputs/wp_migration_outputs/flask_content_seed.json")
SLUG = "fat-cells-store-release-energy-2026"
TITLE = "How Fat Cells Store and Release Energy: New 2026 Research on Insulin, Leptin & Exercise"
DATE = "2026-09-09 09:00:00"
UPLOAD_DIR = Path("static/uploads/2026/09")
MEMOVELA_RESOURCE_BLURB = (
    "Fat cells do far more than store energy. This research guide explains how insulin, exercise "
    "signals, leptin, and brain glucose sensing work together—and why steady, repeatable habits "
    "matter more than chasing a single metabolic switch."
)
EXCERPT = (
    "Fat cells are not passive storage bags. New 2026 studies reveal how insulin directs lipid storage, "
    "exercise signals help mobilize fuel, leptin communicates with the brain, and obesity may alter brain "
    "glucose sensing—without turning new molecular findings into unproven treatments."
)
WELLNESS_TOOLS_PANEL = """
<aside class="article-wellness-tools">
  <div class="article-wellness-tools__intro">
    <p class="eyebrow">Mindful Diabetes Tools</p>
    <h2 class="article-wellness-tools__title">Turn research into repeatable routines</h2>
    <p>Memovela offers a gentle place to notice meals, movement, sleep, hydration, and personal goals while you build habits that fit your life.</p>
  </div>
  <div class="article-wellness-tools__resources">
    <a href="https://memovela.com/" target="_blank" rel="noopener">Use Memovela on the web</a>
    <a href="/memovela/">Read about Memovela</a>
  </div>
</aside>
""".strip()


def parse_front_matter(markdown: str) -> tuple[dict[str, str], str]:
    match = re.match(r"^---\n(.*?)\n---\n", markdown, flags=re.DOTALL)
    if not match:
        raise ValueError("The article is missing its front matter.")
    fields = {}
    for line in match.group(1).splitlines():
        if ":" in line and not line.startswith(" "):
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip().strip('"')
    return fields, markdown[match.end() :]


def inline_markdown(text: str) -> str:
    escaped = html.escape(text, quote=False)

    def link(match: re.Match[str]) -> str:
        label, href = match.groups()
        parsed = urlparse(href)
        external = parsed.netloc and not parsed.netloc.endswith("mindfuldiabetes.org")
        attrs = ' target="_blank" rel="noopener"' if external else ""
        return f'<a href="{html.escape(href, quote=True)}"{attrs}>{inline_markdown(label)}</a>'

    escaped = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", link, escaped)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", escaped)
    return escaped


def markdown_to_html(markdown: str, image_metadata: dict[str, dict[str, str]]) -> str:
    lines = markdown.splitlines()
    output: list[str] = []
    index = 0
    in_list: str | None = None

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            output.append(f"</{in_list}>")
            in_list = None

    while index < len(lines):
        line = lines[index].strip()
        if not line or line.startswith("<!--") or line.startswith("CODEX /"):
            close_list()
            index += 1
            continue
        if line == "---":
            close_list()
            output.append("<hr>")
            index += 1
            continue
        image = re.match(r'!\[[^\]]*\]\(\.\./images/([^\s)]+)(?:\s+"[^"]*")?\)', line)
        if image:
            close_list()
            filename = image.group(1)
            metadata = image_metadata[filename]
            width = 1672 if filename.endswith("hero.png") else 1448
            height = 941 if filename.endswith("hero.png") else 1086
            srcset = ", ".join(
                f"/static/uploads/2026/09/{Path(filename).stem}-{target_width}.webp {target_width}w"
                for target_width in (724, 1024, width)
            )
            if metadata["role"] != "hero / Open Graph":
                output.append(
                    f'<figure data-image-slot="{Path(filename).stem}">'
                    f'<picture><source type="image/webp" srcset="{srcset}" sizes="(max-width: 820px) 100vw, 820px">'
                    f'<img width="{width}" height="{height}" src="/static/uploads/2026/09/{filename}" '
                    f'alt="{html.escape(metadata["alt"], quote=True)}" '
                    f'title="{html.escape(metadata["title"], quote=True)}" '
                    f'data-description="{html.escape(metadata["description"], quote=True)}" '
                    f'loading="{metadata["loading"]}" /></picture>'
                    f'<figcaption>{inline_markdown(metadata["caption"])}</figcaption></figure>'
                )
            caption_index = index + 1
            while caption_index < len(lines) and not lines[caption_index].strip():
                caption_index += 1
            if caption_index < len(lines) and lines[caption_index].strip().startswith("*Figure "):
                index = caption_index
            index += 1
            continue
        heading = re.match(r"^(#{2,3})\s+(.+)$", line)
        if heading:
            close_list()
            level = len(heading.group(1))
            output.append(f"<h{level}>{inline_markdown(heading.group(2))}</h{level}>")
            index += 1
            continue
        if line.startswith("> "):
            close_list()
            output.append(f"<blockquote><p>{inline_markdown(line[2:])}</p></blockquote>")
            index += 1
            continue
        unordered = re.match(r"^-\s+(.+)$", line)
        ordered = re.match(r"^\d+\.\s+(.+)$", line)
        if unordered or ordered:
            wanted = "ul" if unordered else "ol"
            if in_list != wanted:
                close_list()
                output.append(f"<{wanted}>")
                in_list = wanted
            output.append(f"<li>{inline_markdown((unordered or ordered).group(1))}</li>")
            index += 1
            continue
        close_list()
        paragraph = [line]
        while index + 1 < len(lines):
            next_line = lines[index + 1].strip()
            if not next_line or next_line == "---" or re.match(r"^(#{2,3})\s+", next_line) or next_line.startswith(("![]", "![", "> ", "- ")) or re.match(r"^\d+\.\s+", next_line):
                break
            paragraph.append(next_line)
            index += 1
        output.append(f"<p>{inline_markdown(' '.join(paragraph))}</p>")
        index += 1
    close_list()
    return "\n".join(output)


def make_webp_derivatives(source: Path, destination: Path) -> None:
    width = 1448 if source.name != "fat-cells-store-release-energy-2026-hero.png" else 1672
    for target_width in (724, 1024, width):
        target = destination / f"{source.stem}-{target_width}.webp"
        subprocess.run(
            ["cwebp", "-quiet", "-q", "90", "-resize", str(target_width), "0", str(source), "-o", str(target)],
            check=True,
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_root", type=Path, help="Extracted article-package directory")
    args = parser.parse_args()
    source_root = args.source_root
    metadata = json.loads((source_root / "metadata" / "image-metadata.json").read_text(encoding="utf-8"))
    front_matter, body = parse_front_matter(
        (source_root / "article" / "how-fat-cells-store-release-energy-2026.md").read_text(encoding="utf-8")
    )
    body = re.sub(r"^\s*# .+\n+", "", body)
    body = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL)
    content_html = f"{markdown_to_html(body, metadata)}\n{WELLNESS_TOOLS_PANEL}"

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    for image in sorted((source_root / "images").glob("*.png")):
        shutil.copy2(image, UPLOAD_DIR / image.name)
        make_webp_derivatives(image, UPLOAD_DIR)

    items = json.loads(CONTENT_PATH.read_text(encoding="utf-8"))
    items = [item for item in items if item.get("slug") != SLUG]
    items.append(
        {
            "id": "5121",
            "type": "post",
            "status": "publish",
            "title": TITLE,
            "slug": SLUG,
            "url": f"https://mindfuldiabetes.org/{SLUG}/",
            "date": DATE,
            "modified": DATE,
            "parent": "0",
            "menu_order": "0",
            "categories": [front_matter.get("category", "Research & Updates")],
            "tags": [
                "Adipose Tissue", "Insulin Resistance", "Lipid Droplets", "Leptin", "Exercise",
                "Metabolic Health", "Type 2 Diabetes", "Obesity Research",
            ],
            "featured_image_id": Path(front_matter["hero_image"]).stem,
            "template": "default",
            "excerpt_html": EXCERPT,
            "seo_title": front_matter["meta_title"],
            "meta_description": front_matter["meta_description"],
            "canonical_url": f"https://mindfuldiabetes.org/{SLUG}/",
            "og_title": front_matter["meta_title"],
            "og_description": front_matter["meta_description"],
            "og_image": f"/static/uploads/2026/09/{front_matter['og_image']}",
            "hero_image": f"/static/uploads/2026/09/{front_matter['hero_image']}",
            "hero_image_webp_srcset": ", ".join(
                f"/static/uploads/2026/09/{Path(front_matter['hero_image']).stem}-{target_width}.webp {target_width}w"
                for target_width in (724, 1024, 1672)
            ),
            "hero_alt": metadata[front_matter["hero_image"]]["alt"],
            "hero_title": metadata[front_matter["hero_image"]]["title"],
            "hero_description": metadata[front_matter["hero_image"]]["description"],
            "memovela_resource_blurb": MEMOVELA_RESOURCE_BLURB,
            "memovela_sync": True,
            "content_html": content_html,
        }
    )
    CONTENT_PATH.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
