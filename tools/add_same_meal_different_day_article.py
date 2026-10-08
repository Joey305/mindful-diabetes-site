#!/usr/bin/env python3
"""Import the approved Same Meal, Different Day article package."""

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
UPLOAD_DIR = Path("static/uploads/2026/10")
SLUG = "same-meal-different-glucose-response"
TITLE = "Why the Same Meal Can Affect Your Body Differently Every Day"
DATE = "2026-10-07 09:00:00"
EXCERPT = (
    "Why can the same breakfast feel completely different from one day to the next? "
    "Explore how sleep, stress, timing, movement, meal composition, and your own biology "
    "can shape the way your body responds to food—and why one reading is more useful as "
    "an observation than a verdict."
)
MEMOVELA_RESOURCE_BLURB = (
    "Why can the same breakfast feel different from one day to the next?\n\n"
    "A meal response reflects more than food alone. Sleep, stress, timing, movement, "
    "meal sequence, and everyday physiology can all shape the context. This illustrated "
    "guide explains why repeated observations are more useful than judging one meal or one "
    "glucose curve—and how tracking the wider context can help you notice patterns over time."
)
WELLNESS_TOOLS_PANEL = """
<aside class="article-wellness-tools" aria-label="Memovela wellness context tracker">
  <div class="article-wellness-tools__intro">
    <p class="eyebrow">Track the context</p>
    <h2 class="article-wellness-tools__title">Notice patterns across the whole day.</h2>
    <p>Memovela can bring meals, movement, workouts, hydration, sleep or recovery, goals, habits, and other health signals together so recurring relationships are easier to explore. It is a wellness-pattern tool, not a diagnostic tool or a replacement for medical care.</p>
  </div>
  <div class="article-wellness-tools__resources">
    <a href="https://memovela.com/" target="_blank" rel="noopener">Use Memovela on the web</a>
    <a href="/memovela/">Read about Memovela</a>
    <a href="/health-tools/">Explore Mindful Diabetes Health Tools</a>
  </div>
</aside>
""".strip()

IMAGE_INFO = {
    "01_same-meal-different-day.png": (
        "Split-screen showing the same woman eating the same oatmeal breakfast on two different days, one calm and rested and one tired and stressed, with different illustrative glucose-response curves.",
        "Figure 1. Same meal, different day. The curves are illustrative, not individual clinical data. The point is the changing context around an otherwise similar meal.",
    ),
    "02_meal-is-only-one-input.png": (
        "Overhead breakfast surrounded by sleep, stress, time of day, movement, previous meals, metabolic health, medication or illness, and meal composition, all feeding into a glucose response.",
        "Figure 2. The meal is only one input. This is a systems diagram, not a ranking: the relative importance of each factor differs by person and situation.",
    ),
    "03_what-happens-after-you-eat.png": (
        "Horizontal biological pathway showing food, digestion, bloodstream glucose, pancreatic insulin release, and glucose handling by muscle, liver, and adipose tissue.",
        "Figure 3. A simplified view of post-meal glucose handling. The diagram is educational and intentionally omits many regulatory pathways.",
    ),
    "04_same-food-different-response.png": (
        "One standardized breakfast leading to three different people with three different illustrative glucose-response curves.",
        "Figure 4. Same food, different response. The curves are conceptual illustrations of between-person variability and are not reproduced from a specific study.",
    ),
    "05_breakfast-started-yesterday.png": (
        "Timeline from dinner through evening activity, sleep, waking, breakfast, and the post-meal response, showing that prior context carries into the next morning.",
        "Figure 5. Breakfast started yesterday. The final curves are illustrative; the figure represents carryover context rather than a prediction for any individual.",
    ),
    "06_body-knows-what-time-it-is.png": (
        "The same person eating the same meal in the morning and evening with a 24-hour clock, liver, pancreas, muscle, and different illustrative glucose curves.",
        "Figure 6. Same meal, different biological time. The glucose curves are illustrative and should not be read as universal morning-versus-evening values.",
    ),
    "07_dinner-doesnt-end-last-bite.png": (
        "The same dinner branching into sitting on a couch or taking a short walk, with working muscle and different illustrative glucose-response curves.",
        "Figure 7. Post-meal movement changes the context around dinner. The curves are illustrative; the image is not a prescription for a specific walking duration or glucose reduction.",
    ),
    "08_one-reading-is-not-a-verdict.png": (
        "Four repeated breakfasts with slightly different illustrative glucose curves, combined into a pattern, alongside a diagram showing that a CGM measures interstitial fluid.",
        "Figure 8. One reading is an observation; repeated observations can reveal a pattern. All curves shown here are illustrative, not patient data.",
    ),
    "09_same-plate-different-sequence.png": (
        "The same plate of vegetables, protein, and carbohydrate eaten carbohydrate-first or vegetables-and-protein-first, with conceptual response curves below.",
        "Figure 9. Same plate, different sequence. The plotted curves are conceptual and are not a reproduction of the Shukla trial data.",
    ),
    "10_track-the-context.png": (
        "A central person surrounded by nutrition, movement, workouts, hydration, sleep or recovery, goals, habits, and health signals, all flowing toward the concept of patterns.",
        "Figure 10. Don't just track the meal; track the context. Memovela is intended to help organize everyday wellness patterns, not to diagnose disease or replace individualized medical care.",
    ),
}


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


def dimensions_for(filename: str) -> tuple[int, int]:
    return (1672, 941) if filename.startswith(("03_", "05_", "09_")) else (1448, 1086)


def figure_html(filename: str) -> str:
    alt, caption = IMAGE_INFO[filename]
    width, height = dimensions_for(filename)
    stem = Path(filename).stem
    srcset = ", ".join(
        f"/static/uploads/2026/10/{stem}-{size}.webp {size}w" for size in (724, 1024, width)
    )
    return (
        f'<figure data-image-slot="{stem}"><picture>'
        f'<source type="image/webp" srcset="{srcset}" sizes="(max-width: 820px) 100vw, 820px">'
        f'<img width="{width}" height="{height}" src="/static/uploads/2026/10/{filename}" '
        f'alt="{html.escape(alt, quote=True)}" title="{html.escape(caption.split(".")[0], quote=True)}" '
        f'loading="lazy"></picture><figcaption>{html.escape(caption)}</figcaption></figure>'
    )


def markdown_to_html(markdown: str) -> str:
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
        image = re.match(r"!\[[^\]]*\]\(images/([^\s)]+)\)", line)
        if image:
            close_list()
            output.append(figure_html(image.group(1)))
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
    width, _ = dimensions_for(source.name)
    for size in (724, 1024, width):
        subprocess.run(
            ["cwebp", "-quiet", "-q", "90", "-resize", str(size), "0", str(source), "-o", str(UPLOAD_DIR / f"{source.stem}-{size}.webp")],
            check=True,
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_root", type=Path, help="Extracted approved article package directory")
    source_root = parser.parse_args().source_root
    content_html = markdown_to_html((source_root / "article.md").read_text(encoding="utf-8"))
    content_html = content_html.replace(
        "</figure>\n<h2>From one meal to the bigger metabolic picture</h2>",
        f"</figure>\n{WELLNESS_TOOLS_PANEL}\n<h2>From one meal to the bigger metabolic picture</h2>",
        1,
    )

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    for image in sorted((source_root / "images").glob("*.png")):
        destination = UPLOAD_DIR / image.name
        shutil.copy2(image, destination)
        make_webp_derivatives(destination)

    cover = "00-cover-preview_same-meal-different-day.png"
    cover_alt = "Split-screen image of the same woman eating the same oatmeal breakfast on a calm bright day and a tired stressful day, with the headline Same Meal. Different Day."
    items = json.loads(CONTENT_PATH.read_text(encoding="utf-8"))
    items = [item for item in items if item.get("slug") != SLUG]
    items.append({
        "id": "5123", "type": "post", "status": "publish", "title": TITLE, "slug": SLUG,
        "url": f"https://mindfuldiabetes.org/{SLUG}/", "date": DATE, "modified": DATE, "parent": "0", "menu_order": "0",
        "categories": ["Pathways to Wellness"],
        "tags": ["Blood sugar", "Glucose", "Continuous glucose monitoring", "Nutrition", "Sleep", "Stress", "Exercise", "Meal timing", "Personalized nutrition", "Memovela"],
        "featured_image_id": Path(cover).stem, "template": "default", "excerpt_html": EXCERPT,
        "seo_title": f"{TITLE} | Mindful Diabetes", "meta_description": "The same meal doesn't always produce the same response. Learn how sleep, stress, movement, meal timing, biology, and other factors can influence post-meal glucose patterns.",
        "canonical_url": f"https://mindfuldiabetes.org/{SLUG}/", "og_title": "Same Meal. Different Day. Why Your Body Can Respond Differently",
        "og_description": "A glucose response is not a property of food alone. Your sleep, stress, timing, movement, physiology, and measurement context matter too.",
        "og_image": f"/static/uploads/2026/10/{cover}", "hero_image": f"/static/uploads/2026/10/{cover}",
        "hero_image_webp_srcset": ", ".join(f"/static/uploads/2026/10/{Path(cover).stem}-{size}.webp {size}w" for size in (724, 1024, 1448)),
        "hero_alt": cover_alt, "hero_title": TITLE, "hero_description": "Featured article illustration for Same Meal, Different Day.",
        "memovela_resource_blurb": MEMOVELA_RESOURCE_BLURB, "memovela_sync": True,
        "content_html": content_html,
    })
    CONTENT_PATH.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
