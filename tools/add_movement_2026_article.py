#!/usr/bin/env python3
"""Import the approved 2026 movement-science article package into the site seed."""

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
SOURCE_ARCHIVE_DIR = Path("content/articles/2026-10/your-body-is-talking-every-time-you-move")
UPLOAD_DIR = Path("static/uploads/2026/10")
SLUG = "your-body-is-talking-every-time-you-move"
TITLE = "Your Body Is Talking Every Time You Move. Here's What Science Is Discovering."
# This is the local publication date, not the lead paper's October 12 publication date.
DATE = "2026-10-13 09:00:00"
EXCERPT = (
    "A new 2026 study tracked thousands of protein changes after exercise. Here is what those molecular "
    "signals tell us about muscles, glucose, immunity, and why small movements matter. The story pairs a "
    "molecular atlas with practical, appropriately cautious movement guidance."
)
WELLNESS_TOOLS_PANEL = """
<aside class="article-wellness-tools" data-memovela-focus="true" aria-label="Memovela movement habit tracker">
  <div class="article-wellness-tools__intro">
    <p class="eyebrow">Notice patterns, not perfection</p>
    <h2 class="article-wellness-tools__title">Track the habits that help you move.</h2>
    <p>Memovela can help you log activities, movement-related goals, and other daily habits over time. It supports personal reflection and consistency; it does not measure exerkines or diagnose a glucose response.</p>
  </div>
  <div class="article-wellness-tools__resources">
    <a href="https://apps.apple.com/us/app/memovela/id6796686305" target="_blank" rel="noopener noreferrer">Get Memovela on the App Store</a>
    <a href="https://memovela.com/" target="_blank" rel="noopener noreferrer">Use Memovela on the web</a>
    <a href="/memovela/">Read about Memovela</a>
  </div>
</aside>
""".strip()


def inline_markdown(text: str) -> str:
    """Render the deliberately small Markdown subset used in this approved article."""
    escaped = html.escape(text, quote=False)

    def link(match: re.Match[str]) -> str:
        label, href = match.groups()
        parsed = urlparse(href)
        external = bool(parsed.netloc) and not parsed.netloc.endswith("mindfuldiabetes.org")
        attrs = ' target="_blank" rel="noopener noreferrer"' if external else ""
        return f'<a href="{html.escape(href, quote=True)}"{attrs}>{inline_markdown(label)}</a>'

    escaped = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", link, escaped)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    return re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", escaped)


def figure_html(filename: str, metadata: dict[str, dict[str, object]]) -> str:
    image = metadata[filename]
    stem = Path(filename).stem
    srcset = ", ".join(
        [
            *(f"/static/uploads/2026/10/{stem}-{width}.webp {width}w" for width in (724, 1024)),
            f"/static/uploads/2026/10/{filename} 1600w",
        ]
    )
    return (
        f'<figure data-image-slot="{stem}"><picture>'
        f'<source type="image/webp" srcset="{srcset}" sizes="(max-width: 820px) 100vw, 820px">'
        f'<img width="1600" height="900" src="/static/uploads/2026/10/{filename}" '
        f'alt="{html.escape(str(image["alt"]), quote=True)}" '
        f'title="{html.escape(str(image["caption"]).split(".")[0], quote=True)}" loading="lazy">'
        f'</picture><figcaption>{inline_markdown(str(image["caption"]))}</figcaption></figure>'
    )


def markdown_to_html(markdown: str, metadata: dict[str, dict[str, object]]) -> str:
    """Convert the supplied copy without reauthoring it or duplicating its figure captions."""
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
            close_list()
            index += 1
            continue
        if line == "---":
            close_list()
            output.append("<hr>")
            index += 1
            continue

        image_match = re.match(r"!\[[^\]]*\]\(\.\./images/([^\s)]+)\)", line)
        if image_match:
            close_list()
            filename = image_match.group(1)
            if filename not in metadata:
                raise ValueError(f"No image manifest metadata for {filename}.")
            # The hero is already semantically rendered by the existing post template.
            if metadata[filename]["role"] != "cover":
                output.append(figure_html(filename, metadata))
            index += 1
            # Captions are rendered from the manifest, exactly once.
            while index < len(lines) and (
                not lines[index].strip() or lines[index].strip().startswith("*Figure ") or lines[index].strip().startswith("*Cover ")
            ):
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

        unordered, ordered = re.match(r"^-\s+(.+)$", line), re.match(r"^\d+\.\s+(.+)$", line)
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
            if (
                not next_line
                or next_line == "---"
                or re.match(r"^(#{2,3})\s+", next_line)
                or next_line.startswith(("![", "> ", "- "))
                or re.match(r"^\d+\.\s+", next_line)
            ):
                break
            paragraph.append(next_line)
            index += 1
        output.append(f"<p>{inline_markdown(' '.join(paragraph))}</p>")
        index += 1
    close_list()
    return "\n".join(output)


def copy_source_archive(source_root: Path) -> None:
    """Keep editable source copy, research guardrails, and original art in the repository."""
    for relative in (
        "README.md",
        "article/your-body-is-talking-every-time-you-move.md",
        "article/metadata.json",
        "article/memovela_blurb.md",
        "images/IMAGE_MANIFEST.md",
        "images/assets.json",
        "images/source/hero-original.png",
        "images/figure-01-muscle-organ-messages.svg",
        "images/figure-02-proteomics-timeline.svg",
        "images/figure-03-glut4-glucose-gateway.svg",
        "research/editorial_claim_audit.md",
        "research/sources_verified.md",
    ):
        destination = SOURCE_ARCHIVE_DIR / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_root / relative, destination)


def make_webp_derivatives(source: Path) -> None:
    for width in (724, 1024):
        subprocess.run(
            ["cwebp", "-quiet", "-q", "90", "-resize", str(width), "0", str(source), "-o", str(UPLOAD_DIR / f"{source.stem}-{width}.webp")],
            check=True,
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_root", type=Path, help="Extracted approved article-package directory")
    args = parser.parse_args()
    source_root = args.source_root
    article_path = source_root / "article/your-body-is-talking-every-time-you-move.md"
    package_metadata = json.loads((source_root / "article/metadata.json").read_text(encoding="utf-8"))
    image_manifest = json.loads((source_root / "images/assets.json").read_text(encoding="utf-8"))
    images = {image["recommended_file"]: image for image in image_manifest["images"]}
    content_html = markdown_to_html(article_path.read_text(encoding="utf-8"), images)
    content_html = content_html.replace(
        "\n<hr>\n<h2>Key takeaways</h2>",
        f"\n{WELLNESS_TOOLS_PANEL}\n<hr>\n<h2>Key takeaways</h2>",
        1,
    )

    copy_source_archive(source_root)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    for filename in images:
        source = source_root / "images" / filename
        destination = UPLOAD_DIR / filename
        shutil.copy2(source, destination)
        make_webp_derivatives(destination)
    shutil.copy2(source_root / "images/og-body-communication.jpg", UPLOAD_DIR / "og-body-communication.jpg")

    items = json.loads(CONTENT_PATH.read_text(encoding="utf-8"))
    items = [item for item in items if item.get("slug") != SLUG]
    hero = images["hero-body-communication.webp"]
    items.append(
        {
            "id": "5124",
            "type": "post",
            "status": "publish",
            "title": TITLE,
            "slug": SLUG,
            "url": package_metadata["url"],
            "date": DATE,
            "modified": DATE,
            "parent": "0",
            "menu_order": "0",
            "categories": [package_metadata["category"]],
            "tags": package_metadata["tags"],
            "featured_image_id": "hero-body-communication",
            "template": "default",
            "excerpt_html": EXCERPT,
            "seo_title": package_metadata["seo_title"],
            "meta_description": package_metadata["seo_description"],
            "canonical_url": package_metadata["url"],
            "og_title": TITLE,
            "og_description": package_metadata["summary"],
            "og_image": "/static/uploads/2026/10/og-body-communication.jpg",
            "hero_image": "/static/uploads/2026/10/hero-body-communication.webp",
            "hero_image_webp_srcset": ", ".join(
                [
                    *(f"/static/uploads/2026/10/hero-body-communication-{width}.webp {width}w" for width in (724, 1024)),
                    "/static/uploads/2026/10/hero-body-communication.webp 1600w",
                ]
            ),
            "hero_alt": hero["alt"],
            "hero_caption": hero["caption"],
            "hero_width": 1600,
            "hero_height": 900,
            "hero_title": TITLE,
            "hero_description": "Original conceptual medical illustration created for this article.",
            "memovela_resource_blurb": (source_root / "article/memovela_blurb.md").read_text(encoding="utf-8").split("## Recommended article-card blurb (public, ~45 words)\n\n", 1)[1].split("\n\n## ", 1)[0].strip(),
            # Preserve the blurb in the article record, but do not send anything to the app backend.
            "memovela_sync": False,
            "content_html": content_html,
        }
    )
    CONTENT_PATH.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
