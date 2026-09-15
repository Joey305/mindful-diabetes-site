#!/usr/bin/env python3
"""Import the approved September 2026 metabolic-syndrome research feature."""

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
SLUG = "metabolic-syndrome-midlife-brain-2026"
TITLE = "Is Metabolic Syndrome Changing Your Brain Before You Notice? New 2026 Evidence From Midlife"
DATE = "2026-09-14 09:00:00"
UPLOAD_DIR = Path("static/uploads/2026/09")
MEMOVELA_RESOURCE_BLURB = (
    "Could metabolic syndrome be changing the brain before memory problems are obvious?\n\n"
    "A new 2026 fMRI study of cognitively unimpaired adults in midlife found subtle differences in the brain’s default mode network, especially with abdominal obesity and low HDL. Combined with new evidence that dementia risk varies across diabetes phenotypes, the findings raise an important prevention question: what can cardiometabolic health tell us about the brain before symptoms appear?"
)
EXCERPT = (
    "New 2026 research suggests metabolic syndrome is associated with subtle default-mode-network differences in cognitively unimpaired adults ages 40–65, with abdominal obesity and low HDL standing out. Here is what the findings mean—and what they do not."
)
WELLNESS_TOOLS_PANEL = """
<aside class="article-wellness-tools">
  <div class="article-wellness-tools__intro">
    <p class="eyebrow">Mindful Diabetes Tools</p>
    <h2 class="article-wellness-tools__title">Turn prevention into repeatable routines</h2>
    <p>Memovela offers a gentle place to notice meals, movement, sleep, hydration, and personal goals while you build habits that fit your life.</p>
  </div>
  <div class="article-wellness-tools__resources">
    <a href="https://memovela.com/" target="_blank" rel="noopener">Use Memovela on the web</a>
    <a href="/memovela/">Read about Memovela</a>
  </div>
</aside>
""".strip()


def inline_markdown(text: str) -> str:
    escaped = html.escape(text, quote=False)

    def link(match: re.Match[str]) -> str:
        label, href = match.groups()
        external = bool(urlparse(href).netloc) and not urlparse(href).netloc.endswith("mindfuldiabetes.org")
        attrs = ' target="_blank" rel="noopener"' if external else ""
        return f'<a href="{html.escape(href, quote=True)}"{attrs}>{inline_markdown(label)}</a>'

    escaped = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", link, escaped)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    return re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", escaped)


def markdown_to_html(markdown: str, metadata: dict[str, dict[str, str]]) -> str:
    lines, output, index, in_list = markdown.splitlines(), [], 0, None

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            output.append(f"</{in_list}>")
            in_list = None

    while index < len(lines):
        line = lines[index].strip()
        if not line:
            close_list(); index += 1; continue
        image = re.match(r'!\[[^\]]*\]\(\.\./images/([^\s)]+)(?:\s+"[^"]*")?\)', line)
        if image:
            close_list()
            filename, info = image.group(1), metadata[image.group(1)]
            if not info["role"].startswith("hero"):
                width, height = 1448, 1086
                stem = Path(filename).stem
                srcset = ", ".join(f"/static/uploads/2026/09/{stem}-{size}.webp {size}w" for size in (724, 1024, width))
                output.append(
                    f'<figure data-image-slot="{stem}"><picture><source type="image/webp" srcset="{srcset}" sizes="(max-width: 820px) 100vw, 820px">'
                    f'<img width="{width}" height="{height}" src="/static/uploads/2026/09/{filename}" alt="{html.escape(info["alt"], quote=True)}" '
                    f'title="{html.escape(info["title"], quote=True)}" data-description="{html.escape(info["description"], quote=True)}" loading="lazy"></picture>'
                    f'<figcaption>{inline_markdown(info["caption"])}</figcaption></figure>'
                )
            index += 1
            while index < len(lines) and (not lines[index].strip() or lines[index].strip().startswith("*Figure ")):
                index += 1
            continue
        heading = re.match(r"^(#{2,3})\s+(.+)$", line)
        if heading:
            close_list(); level = len(heading.group(1)); output.append(f"<h{level}>{inline_markdown(heading.group(2))}</h{level}>"); index += 1; continue
        if line.startswith("> "):
            close_list(); output.append(f"<blockquote><p>{inline_markdown(line[2:])}</p></blockquote>"); index += 1; continue
        unordered, ordered = re.match(r"^-\s+(.+)$", line), re.match(r"^\d+\.\s+(.+)$", line)
        if unordered or ordered:
            wanted = "ul" if unordered else "ol"
            if in_list != wanted:
                close_list(); output.append(f"<{wanted}>"); in_list = wanted
            output.append(f"<li>{inline_markdown((unordered or ordered).group(1))}</li>"); index += 1; continue
        if line == "---":
            close_list(); output.append("<hr>"); index += 1; continue
        close_list(); paragraph = [line]
        while index + 1 < len(lines):
            next_line = lines[index + 1].strip()
            if not next_line or next_line == "---" or re.match(r"^(#{2,3})\s+", next_line) or next_line.startswith(("![", "> ", "- ")) or re.match(r"^\d+\.\s+", next_line):
                break
            paragraph.append(next_line); index += 1
        output.append(f"<p>{inline_markdown(' '.join(paragraph))}</p>"); index += 1
    close_list()
    return "\n".join(output)


def make_webp_derivatives(source: Path) -> None:
    width = 1672 if source.name.endswith("hero.png") else 1448
    for target_width in (724, 1024, width):
        subprocess.run(["cwebp", "-quiet", "-q", "90", "-resize", str(target_width), "0", str(source), "-o", str(UPLOAD_DIR / f"{source.stem}-{target_width}.webp")], check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_root", type=Path, help="Extracted article-package directory")
    source_root = parser.parse_args().source_root
    metadata = json.loads((source_root / "metadata" / "image-metadata.json").read_text(encoding="utf-8"))
    markdown = (source_root / "article" / f"{SLUG}.md").read_text(encoding="utf-8")
    body = re.sub(r"^---.*?---\s*", "", markdown, count=1, flags=re.DOTALL)
    body = re.sub(r"^# .+\n+", "", body)
    body = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL)
    content_html = f"{markdown_to_html(body, metadata)}\n{WELLNESS_TOOLS_PANEL}"

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    for image in sorted((source_root / "images").glob("*.png")):
        destination = UPLOAD_DIR / image.name
        shutil.copy2(image, destination)
        make_webp_derivatives(destination)

    items = json.loads(CONTENT_PATH.read_text(encoding="utf-8"))
    items = [item for item in items if item.get("slug") != SLUG]
    hero = "metabolic-syndrome-midlife-brain-2026-hero.png"
    hero_stem = Path(hero).stem
    items.append({
        "id": "5122", "type": "post", "status": "publish", "title": TITLE, "slug": SLUG,
        "url": f"https://mindfuldiabetes.org/{SLUG}/", "date": DATE, "modified": DATE, "parent": "0", "menu_order": "0",
        "categories": ["Research & Updates"],
        "tags": ["Metabolic Syndrome", "Brain Health", "Midlife", "Default Mode Network", "Type 2 Diabetes", "Dementia Prevention", "Abdominal Obesity", "HDL Cholesterol"],
        "featured_image_id": hero_stem, "template": "default", "excerpt_html": EXCERPT,
        "seo_title": "Metabolic Syndrome & Brain Health: New 2026 Midlife Study",
        "meta_description": "A new 2026 fMRI study links midlife metabolic syndrome with subtle default-mode-network differences. Learn what abdominal obesity, HDL and diabetes phenotypes may mean for brain health.",
        "canonical_url": f"https://mindfuldiabetes.org/{SLUG}/", "og_title": "Metabolic Syndrome & Brain Health: New 2026 Midlife Study",
        "og_description": "A new 2026 fMRI study links midlife metabolic syndrome with subtle default-mode-network differences. Learn what abdominal obesity, HDL and diabetes phenotypes may mean for brain health.",
        "og_image": f"/static/uploads/2026/09/{hero}", "hero_image": f"/static/uploads/2026/09/{hero}",
        "hero_image_webp_srcset": ", ".join(f"/static/uploads/2026/09/{hero_stem}-{size}.webp {size}w" for size in (724, 1024, 1672)),
        "hero_alt": metadata[hero]["alt"], "hero_title": metadata[hero]["title"], "hero_description": metadata[hero]["description"],
        "memovela_resource_blurb": MEMOVELA_RESOURCE_BLURB, "memovela_sync": True, "content_html": content_html,
    })
    CONTENT_PATH.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
