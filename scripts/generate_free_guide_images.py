from __future__ import annotations

import math
from pathlib import Path
from textwrap import wrap

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
FONT_DIR = ROOT / "Mindful_Diabetes_Free_Guides" / "01_Brand_Assets" / "Fonts_Reference"
LOGO = ROOT / "Mindful_Diabetes_Free_Guides" / "01_Brand_Assets" / "Logos" / "mdi-logo.jpg"
OUT_DIR = ROOT / "static" / "free-guides" / "images"

PALETTE = {
    "navy": "#0d1338",
    "ink": "#17203f",
    "green": "#005030",
    "deep_green": "#003b24",
    "leaf": "#2f7d57",
    "coral": "#f07239",
    "coral_dark": "#df5a32",
    "cream": "#fffaf2",
    "paper": "#fffdf8",
    "soft": "#f5f7fe",
    "soft_green": "#edf8f1",
    "soft_orange": "#fff0e7",
    "line": "#d9deea",
    "muted": "#687081",
    "white": "#ffffff",
    "gold": "#f4ba49",
    "sky": "#b9ddec",
    "plum": "#7d5a79",
}

GUIDES = [
    {
        "slug": "mindful-plate",
        "title": "The Mindful Plate",
        "subtitle": "A Simple Guide to Blood Sugar-Friendly Eating",
        "category": "Nutrition",
        "tags": ["Vegetables", "Protein", "Fiber", "Balanced meals"],
        "accent": "#f4ba49",
    },
    {
        "slug": "fats-without-fear",
        "title": "Fats Without Fear",
        "subtitle": "A Plain-English Guide to Dietary Fats, Heart Health, and Brain Health",
        "category": "Heart Health",
        "tags": ["Oils", "Nuts", "Labels", "Heart health"],
        "accent": "#7d5a79",
    },
    {
        "slug": "grocery-store-survival-guide",
        "title": "The Grocery Store Survival Guide",
        "subtitle": "How to Make Practical, Blood Sugar-Conscious Choices Without Feeling Overwhelmed",
        "category": "Shopping",
        "tags": ["Food labels", "Pantry", "Budget", "Quick meals"],
        "accent": "#2f7d57",
    },
    {
        "slug": "7-day-prevention-reset",
        "title": "The 7-Day Prevention Reset",
        "subtitle": "A Gentle One-Week Plan for Building Healthier Everyday Habits",
        "category": "Habits",
        "tags": ["Trackers", "Movement", "Sleep", "Planning"],
        "accent": "#b35b37",
    },
    {
        "slug": "blood-sugar-brain-health",
        "title": "Blood Sugar & Brain Health",
        "subtitle": "Understanding the Everyday Connection",
        "category": "Brain Health",
        "tags": ["Glucose", "Blood vessels", "Sleep", "Brain health"],
        "accent": "#3d7d8f",
    },
]

ASSETS = [
    ("cover-preview", (1200, 1553), "cover"),
    ("download-card-thumbnail", (1200, 675), "thumb"),
    ("banner-16x9", (1600, 900), "banner"),
    ("square-promo", (1080, 1080), "square"),
]


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_DIR / name), size)


def blend(hex_a: str, hex_b: str, t: float) -> str:
    a = tuple(int(hex_a[i : i + 2], 16) for i in (1, 3, 5))
    b = tuple(int(hex_b[i : i + 2], 16) for i in (1, 3, 5))
    c = tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))
    return "#{:02x}{:02x}{:02x}".format(*c)


def text_size(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=fnt)
    return box[2] - box[0], box[3] - box[1]


def wrap_text(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont, width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        if text_size(draw, test, fnt)[0] <= width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_wrapped(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    fnt: ImageFont.FreeTypeFont,
    fill: str,
    width: int,
    line_gap: int,
    max_lines: int | None = None,
) -> int:
    x, y = xy
    lines = wrap_text(draw, text, fnt, width)
    if max_lines is not None:
        lines = lines[:max_lines]
    line_h = text_size(draw, "Ag", fnt)[1] + line_gap
    for line in lines:
        draw.text((x, y), line, font=fnt, fill=fill)
        y += line_h
    return y


def rounded_shadow(base: Image.Image, box: tuple[int, int, int, int], radius: int, blur: int, opacity: int) -> None:
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.rounded_rectangle(box, radius=radius, fill=(13, 19, 56, opacity))
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    base.alpha_composite(layer)


def draw_pill(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str, fill: str, text_fill: str, fnt: ImageFont.FreeTypeFont) -> None:
    draw.rounded_rectangle(box, radius=(box[3] - box[1]) // 2, fill=fill)
    tw, th = text_size(draw, text, fnt)
    draw.text(((box[0] + box[2] - tw) // 2, (box[1] + box[3] - th) // 2 - 2), text, font=fnt, fill=text_fill)


def paste_logo(base: Image.Image, x: int, y: int, size: int) -> None:
    logo = Image.open(LOGO).convert("RGB").resize((size, size), Image.Resampling.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle((0, 0, size, size), radius=max(8, size // 5), fill=255)
    base.paste(logo, (x, y), mask)


def draw_plate(draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int) -> None:
    box = (cx - r, cy - r, cx + r, cy + r)
    draw.ellipse(box, fill=PALETTE["white"], outline=PALETTE["navy"], width=max(4, r // 22))
    inner = (cx - r + 16, cy - r + 16, cx + r - 16, cy + r - 16)
    draw.pieslice(inner, 90, 270, fill=PALETTE["soft_green"])
    draw.pieslice(inner, 0, 90, fill=PALETTE["soft"])
    draw.pieslice(inner, 270, 360, fill=PALETTE["soft_orange"])
    w = max(8, r // 14)
    draw.line((cx, cy - r + 20, cx, cy + r - 20), fill=PALETTE["white"], width=w)
    draw.line((cx, cy, cx + r - 20, cy), fill=PALETTE["white"], width=w)
    for angle, color in [(210, PALETTE["green"]), (35, PALETTE["gold"]), (320, PALETTE["coral"])]:
        ax = cx + int(math.cos(math.radians(angle)) * r * 0.58)
        ay = cy + int(math.sin(math.radians(angle)) * r * 0.58)
        draw.ellipse((ax - r // 13, ay - r // 13, ax + r // 13, ay + r // 13), fill=color)


def draw_food_icon(draw: ImageDraw.ImageDraw, x: int, y: int, scale: int, fill: str) -> None:
    draw.ellipse((x, y + scale // 5, x + scale, y + scale), fill=fill, outline=PALETTE["navy"], width=max(2, scale // 18))
    draw.ellipse((x + scale // 4, y + scale // 3, x + scale * 3 // 4, y + scale * 5 // 6), fill=blend(fill, PALETTE["white"], 0.45))
    draw.arc((x + scale // 5, y, x + scale, y + scale // 2), 195, 330, fill=PALETTE["green"], width=max(2, scale // 18))


def draw_calendar(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], accent: str) -> None:
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(box, radius=28, fill=PALETTE["white"], outline=PALETTE["line"], width=3)
    draw.rounded_rectangle((x0, y0, x1, y0 + 75), radius=28, fill=PALETTE["green"])
    for i in range(7):
        cx = x0 + 58 + i * ((x1 - x0 - 116) // 6)
        cy = y0 + 150 + (i % 2) * 28
        draw.ellipse((cx - 28, cy - 28, cx + 28, cy + 28), fill=accent if i % 2 else PALETTE["soft_green"], outline=PALETTE["navy"], width=3)
        if i < 6:
            nx = x0 + 58 + (i + 1) * ((x1 - x0 - 116) // 6)
            draw.line((cx + 31, cy, nx - 31, y0 + 150 + ((i + 1) % 2) * 28), fill=PALETTE["coral"], width=5)


def draw_cart(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], accent: str) -> None:
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(box, radius=28, fill=PALETTE["white"], outline=PALETTE["line"], width=3)
    draw.line((x0 + 70, y0 + 86, x0 + 106, y1 - 100, x1 - 80, y1 - 100, x1 - 44, y0 + 120), fill=PALETTE["navy"], width=9, joint="curve")
    draw.line((x0 + 32, y0 + 86, x0 + 76, y0 + 86), fill=PALETTE["navy"], width=9)
    for i, color in enumerate([PALETTE["green"], accent, PALETTE["gold"], PALETTE["sky"], PALETTE["coral"]]):
        px = x0 + 125 + (i % 3) * 92
        py = y0 + 120 + (i // 3) * 76
        draw_food_icon(draw, px, py, 62, color)
    draw.ellipse((x0 + 115, y1 - 78, x0 + 155, y1 - 38), fill=PALETTE["navy"])
    draw.ellipse((x1 - 150, y1 - 78, x1 - 110, y1 - 38), fill=PALETTE["navy"])


def draw_fats(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], accent: str) -> None:
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(box, radius=28, fill=PALETTE["white"], outline=PALETTE["line"], width=3)
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    draw.ellipse((cx - 96, cy - 80, cx + 26, cy + 42), fill=PALETTE["soft_green"], outline=PALETTE["navy"], width=4)
    draw.ellipse((cx - 68, cy - 50, cx - 2, cy + 16), fill=PALETTE["green"])
    draw.polygon((cx + 25, cy - 58, cx + 148, cy - 30, cx + 148, cy + 44, cx + 25, cy + 70), fill=PALETTE["sky"], outline=PALETTE["navy"])
    draw.ellipse((cx + 98, cy - 8, cx + 116, cy + 10), fill=PALETTE["navy"])
    draw.rounded_rectangle((x0 + 70, y1 - 150, x0 + 180, y1 - 54), radius=20, fill=blend(accent, PALETTE["white"], 0.18), outline=PALETTE["navy"], width=4)
    draw.ellipse((x0 + 102, y1 - 194, x0 + 150, y1 - 145), fill=PALETTE["gold"], outline=PALETTE["navy"], width=3)
    for i in range(5):
        draw.ellipse((x1 - 190 + i * 25, y1 - 118, x1 - 145 + i * 25, y1 - 74), fill=[PALETTE["gold"], PALETTE["coral"], PALETTE["green"], PALETTE["soft_orange"], accent][i], outline=PALETTE["navy"], width=3)


def draw_brain(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], accent: str) -> None:
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(box, radius=28, fill=PALETTE["white"], outline=PALETTE["line"], width=3)
    cx, cy = x0 + (x1 - x0) // 2 - 50, y0 + (y1 - y0) // 2
    draw.ellipse((cx - 110, cy - 88, cx + 80, cy + 102), fill=PALETTE["soft_green"], outline=PALETTE["navy"], width=5)
    for i in range(4):
        draw.arc((cx - 72 + i * 25, cy - 56, cx + 26 + i * 20, cy + 58), 80, 280, fill=accent, width=5)
    draw.rounded_rectangle((cx + 115, cy - 112, cx + 262, cy + 116), radius=24, fill=PALETTE["soft"], outline=PALETTE["navy"], width=4)
    for i, color in enumerate([PALETTE["green"], PALETTE["coral"], accent]):
        y = cy - 62 + i * 62
        draw.line((cx + 80, cy, cx + 115, y), fill=color, width=5)
        draw.ellipse((cx + 145, y - 18, cx + 181, y + 18), fill=color)
        draw.line((cx + 181, y, cx + 226, y), fill=color, width=5)


def draw_art(draw: ImageDraw.ImageDraw, guide: dict, box: tuple[int, int, int, int]) -> None:
    slug = guide["slug"]
    accent = guide["accent"]
    if slug == "mindful-plate":
        x0, y0, x1, y1 = box
        draw.rounded_rectangle(box, radius=28, fill=PALETTE["white"], outline=PALETTE["line"], width=3)
        draw_plate(draw, (x0 + x1) // 2, (y0 + y1) // 2, min(x1 - x0, y1 - y0) // 3)
        for idx, color in enumerate([PALETTE["green"], PALETTE["coral"], PALETTE["gold"], PALETTE["sky"]]):
            draw_food_icon(draw, x0 + 52 + idx * ((x1 - x0 - 120) // 4), y1 - 135, 60, color)
    elif slug == "fats-without-fear":
        draw_fats(draw, box, accent)
    elif slug == "grocery-store-survival-guide":
        draw_cart(draw, box, accent)
    elif slug == "7-day-prevention-reset":
        draw_calendar(draw, box, accent)
    else:
        draw_brain(draw, box, accent)


def background(size: tuple[int, int], accent: str) -> Image.Image:
    w, h = size
    img = Image.new("RGBA", size, PALETTE["cream"])
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(1, h - 1)
        d.line((0, y, w, y), fill=blend(PALETTE["cream"], PALETTE["soft"], t * 0.75))
    d.rounded_rectangle((-w * 0.08, h * 0.72, w * 0.65, h * 1.1), radius=w // 8, fill=blend(PALETTE["soft_green"], PALETTE["white"], 0.25))
    d.rounded_rectangle((w * 0.68, -h * 0.08, w * 1.08, h * 0.36), radius=w // 8, fill=blend(accent, PALETTE["white"], 0.7))
    return img


def add_brand_header(img: Image.Image, draw: ImageDraw.ImageDraw, x: int, y: int, scale: float) -> int:
    logo_size = int(58 * scale)
    paste_logo(img, x, y, logo_size)
    draw.text((x + logo_size + int(18 * scale), y + int(5 * scale)), "Mindful Diabetes", font=font("Lato-Bold.ttf", int(23 * scale)), fill=PALETTE["green"])
    draw.text((x + logo_size + int(18 * scale), y + int(35 * scale)), "Free Health Guides", font=font("Lato-Regular.ttf", int(17 * scale)), fill=PALETTE["muted"])
    return y + logo_size


def add_tags(draw: ImageDraw.ImageDraw, tags: list[str], x: int, y: int, max_w: int, scale: float) -> int:
    fnt = font("Lato-Bold.ttf", int(17 * scale))
    cx = x
    for tag in tags:
        tw, th = text_size(draw, tag, fnt)
        pill_w = tw + int(30 * scale)
        if cx + pill_w > x + max_w:
            break
        box = (cx, y, cx + pill_w, y + int(36 * scale))
        draw.rounded_rectangle(box, radius=int(18 * scale), fill=PALETTE["soft_green"], outline=PALETTE["line"], width=max(1, int(1.5 * scale)))
        draw.text((cx + int(15 * scale), y + int(8 * scale)), tag, font=fnt, fill=PALETTE["green"])
        cx += pill_w + int(10 * scale)
    return y + int(46 * scale)


def render_cover(guide: dict, size: tuple[int, int]) -> Image.Image:
    w, h = size
    scale = w / 1200
    img = background(size, guide["accent"])
    d = ImageDraw.Draw(img)
    pad = int(72 * scale)
    card = (pad, pad, w - pad, h - pad)
    rounded_shadow(img, (card[0] + 14, card[1] + 18, card[2] + 14, card[3] + 18), int(34 * scale), int(22 * scale), 30)
    d.rounded_rectangle(card, radius=int(36 * scale), fill=PALETTE["paper"], outline=PALETTE["line"], width=int(3 * scale))
    add_brand_header(img, d, pad + int(48 * scale), pad + int(42 * scale), scale)
    draw_pill(d, (w - pad - int(250 * scale), pad + int(46 * scale), w - pad - int(50 * scale), pad + int(98 * scale)), "FREE GUIDE", PALETTE["coral"], PALETTE["white"], font("Lato-Bold.ttf", int(21 * scale)))

    title_font = font("Lora-Bold.ttf", int(78 * scale if len(guide["title"]) < 25 else 67 * scale))
    sub_font = font("Lato-Regular.ttf", int(30 * scale))
    title_y = pad + int(235 * scale)
    title_bottom = draw_wrapped(d, (pad + int(58 * scale), title_y), guide["title"], title_font, PALETTE["navy"], int(680 * scale), int(16 * scale), 3)
    draw_wrapped(d, (pad + int(60 * scale), title_bottom + int(28 * scale)), guide["subtitle"], sub_font, PALETTE["ink"], int(690 * scale), int(11 * scale), 3)

    art_box = (pad + int(58 * scale), int(h * 0.52), w - pad - int(58 * scale), h - pad - int(225 * scale))
    draw_art(d, guide, art_box)
    add_tags(d, guide["tags"], pad + int(58 * scale), h - pad - int(150 * scale), int(850 * scale), scale)
    d.text((pad + int(58 * scale), h - pad - int(63 * scale)), "Published 2026 | Medical review pending | No signup required", font=font("Lato-Regular.ttf", int(20 * scale)), fill=PALETTE["muted"])
    return img.convert("RGB")


def render_landscape(guide: dict, size: tuple[int, int], mode: str) -> Image.Image:
    w, h = size
    scale = w / 1600
    img = background(size, guide["accent"])
    d = ImageDraw.Draw(img)
    pad = int(76 * scale)
    rounded_shadow(img, (pad + 14, pad + 18, w - pad + 14, h - pad + 18), int(32 * scale), int(22 * scale), 28)
    d.rounded_rectangle((pad, pad, w - pad, h - pad), radius=int(34 * scale), fill=PALETTE["paper"], outline=PALETTE["line"], width=max(2, int(3 * scale)))
    add_brand_header(img, d, pad + int(48 * scale), pad + int(42 * scale), scale)

    left = pad + int(58 * scale)
    text_w = int(w * 0.49)
    d.text((left, pad + int(148 * scale)), guide["category"].upper(), font=font("Lato-Bold.ttf", int(24 * scale)), fill=PALETTE["coral"])
    title_font = font("Lora-Bold.ttf", int(74 * scale if len(guide["title"]) < 25 else 62 * scale))
    bottom = draw_wrapped(d, (left, pad + int(190 * scale)), guide["title"], title_font, PALETTE["navy"], text_w, int(12 * scale), 3)
    draw_wrapped(d, (left, bottom + int(22 * scale)), guide["subtitle"], font("Lato-Bold.ttf", int(30 * scale)), PALETTE["green"], text_w, int(12 * scale), 3)
    add_tags(d, guide["tags"], left, h - pad - int(124 * scale), text_w, scale)
    draw_pill(d, (left, h - pad - int(68 * scale), left + int(230 * scale), h - pad - int(18 * scale)), "FREE PDF", PALETTE["coral"], PALETTE["white"], font("Lato-Bold.ttf", int(21 * scale)))
    d.text((left + int(252 * scale), h - pad - int(57 * scale)), "No signup required", font=font("Lato-Bold.ttf", int(20 * scale)), fill=PALETTE["green"])

    art_box = (int(w * 0.59), pad + int(130 * scale), w - pad - int(58 * scale), h - pad - int(96 * scale))
    draw_art(d, guide, art_box)
    return img.convert("RGB")


def render_square(guide: dict, size: tuple[int, int]) -> Image.Image:
    w, h = size
    scale = w / 1080
    img = background(size, guide["accent"])
    d = ImageDraw.Draw(img)
    pad = int(62 * scale)
    d.rounded_rectangle((pad, pad, w - pad, h - pad), radius=int(34 * scale), fill=PALETTE["paper"], outline=PALETTE["line"], width=int(3 * scale))
    add_brand_header(img, d, pad + int(40 * scale), pad + int(38 * scale), scale)
    d.text((pad + int(42 * scale), pad + int(160 * scale)), guide["category"].upper(), font=font("Lato-Bold.ttf", int(21 * scale)), fill=PALETTE["coral"])
    title_font = font("Lora-Bold.ttf", int(59 * scale if len(guide["title"]) < 25 else 51 * scale))
    bottom = draw_wrapped(d, (pad + int(42 * scale), pad + int(196 * scale)), guide["title"], title_font, PALETTE["navy"], int(w - pad * 2 - 84 * scale), int(9 * scale), 3)
    draw_wrapped(d, (pad + int(44 * scale), bottom + int(18 * scale)), guide["subtitle"], font("Lato-Bold.ttf", int(24 * scale)), PALETTE["green"], int(w - pad * 2 - 88 * scale), int(8 * scale), 2)
    draw_art(d, guide, (pad + int(70 * scale), int(h * 0.57), w - pad - int(70 * scale), h - pad - int(92 * scale)))
    draw_pill(d, (pad + int(42 * scale), h - pad - int(74 * scale), pad + int(246 * scale), h - pad - int(24 * scale)), "FREE PDF", PALETTE["coral"], PALETTE["white"], font("Lato-Bold.ttf", int(20 * scale)))
    return img.convert("RGB")


def save_all() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for guide in GUIDES:
        for suffix, size, mode in ASSETS:
            if mode == "cover":
                img = render_cover(guide, size)
            elif mode == "square":
                img = render_square(guide, size)
            else:
                img = render_landscape(guide, size, mode)
            out = OUT_DIR / f"{guide['slug']}-{suffix}.png"
            img.save(out, optimize=True, quality=95)
            print(out)


if __name__ == "__main__":
    save_all()
