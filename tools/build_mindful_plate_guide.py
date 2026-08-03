from __future__ import annotations

import csv
import json
import math
import os
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "Mindful_Diabetes_Free_Guides"
GUIDE = PROJECT / "02_The_Mindful_Plate"
FONT_DIR = PROJECT / "01_Brand_Assets" / "Fonts_Reference"
LOGO = PROJECT / "01_Brand_Assets" / "Logos" / "mdi-logo.jpg"

PRINT_PDF = GUIDE / "Final_Print_PDF" / "mindful-diabetes-mindful-plate-guide-2026-print.pdf"
WEB_PDF = GUIDE / "Final_Web_PDF" / "mindful-diabetes-mindful-plate-guide-2026.pdf"
IMAGES = GUIDE / "Images"
SOURCE = GUIDE / "Editable_Source"
RESEARCH = GUIDE / "Research"
ACCESS = GUIDE / "Accessibility"
WEBSITE = GUIDE / "Website_Assets"


COLORS = {
    "navy": "#0d1338",
    "deep_navy": "#0d243c",
    "coral": "#f07239",
    "coral_dark": "#e15b47",
    "green": "#005030",
    "deep_green": "#003b24",
    "cream": "#fffaf2",
    "soft": "#f5f7fe",
    "soft_green": "#f0faf5",
    "soft_orange": "#fff3ec",
    "line": "#e4e6ef",
    "body": "#343842",
    "muted": "#6c7280",
    "white": "#ffffff",
}


def hex_color(name: str):
    return colors.HexColor(COLORS[name])


def ensure_dirs() -> None:
    for path in [
        GUIDE / "Final_Print_PDF",
        GUIDE / "Final_Web_PDF",
        SOURCE,
        IMAGES,
        WEBSITE,
        RESEARCH,
        ACCESS,
    ]:
        path.mkdir(parents=True, exist_ok=True)


def register_fonts() -> None:
    fonts = {
        "Lato": "Lato-Regular.ttf",
        "Lato-Bold": "Lato-Bold.ttf",
        "Lora": "Lora-Regular.ttf",
        "Lora-Bold": "Lora-Bold.ttf",
    }
    for font_name, file_name in fonts.items():
        pdfmetrics.registerFont(TTFont(font_name, str(FONT_DIR / file_name)))


def pil_font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_DIR / name), size=size)


def wrap_text(text: str, font_name: str, font_size: float, width: float) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        if pdfmetrics.stringWidth(test, font_name, font_size) <= width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def text_box(
    c: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    w: float,
    size: float = 10.8,
    leading: float | None = None,
    font: str = "Lato",
    color: str = "body",
    max_lines: int | None = None,
) -> float:
    c.setFillColor(hex_color(color))
    c.setFont(font, size)
    if leading is None:
        leading = size * 1.35
    lines = wrap_text(text, font, size, w)
    if max_lines is not None:
        lines = lines[:max_lines]
    for line in lines:
        c.drawString(x, y, line)
        y -= leading
    return y


def title(c: canvas.Canvas, text: str, x: float, y: float, w: float, size: float = 31) -> float:
    c.setFillColor(hex_color("navy"))
    c.setFont("Lora-Bold", size)
    lines = wrap_text(text, "Lora-Bold", size, w)
    for line in lines:
        c.drawString(x, y, line)
        y -= size * 1.12
    return y - 4


def heading(c: canvas.Canvas, text: str, x: float, y: float, w: float, size: float = 19) -> float:
    c.setFillColor(hex_color("navy"))
    c.setFont("Lora-Bold", size)
    lines = wrap_text(text, "Lora-Bold", size, w)
    for line in lines:
        c.drawString(x, y, line)
        y -= size * 1.12
    return y - 2


def eyebrow(c: canvas.Canvas, text: str, x: float, y: float) -> None:
    c.setFillColor(hex_color("coral"))
    c.setFont("Lato-Bold", 8.5)
    c.drawString(x, y, text.upper())


def bullet_list(c: canvas.Canvas, items: list[str], x: float, y: float, w: float, size: float = 10.3) -> float:
    for item in items:
        c.setFillColor(hex_color("green"))
        c.circle(x + 4, y + 3, 2.2, fill=1, stroke=0)
        y = text_box(c, item, x + 15, y, w - 15, size=size, font="Lato", color="body")
        y -= 4
    return y


def callout(c: canvas.Canvas, title_text: str, body: str, x: float, y: float, w: float, h: float, tone: str = "green") -> None:
    fill = "soft_green" if tone == "green" else "soft_orange"
    border = "green" if tone == "green" else "coral"
    c.setFillColor(hex_color(fill))
    c.setStrokeColor(hex_color(border))
    c.setLineWidth(1.1)
    c.roundRect(x, y - h, w, h, 8, stroke=1, fill=1)
    c.setFillColor(hex_color(border))
    c.setFont("Lato-Bold", 9.5)
    c.drawString(x + 14, y - 22, title_text)
    text_box(c, body, x + 14, y - 40, w - 28, size=9.5, leading=12.5, font="Lato", color="body")


def chip(c: canvas.Canvas, text: str, x: float, y: float, fill: str = "soft_green", stroke: str = "green") -> float:
    width = pdfmetrics.stringWidth(text, "Lato-Bold", 8.5) + 20
    c.setFillColor(hex_color(fill))
    c.setStrokeColor(hex_color(stroke))
    c.roundRect(x, y - 16, width, 20, 10, stroke=1, fill=1)
    c.setFillColor(hex_color(stroke))
    c.setFont("Lato-Bold", 8.5)
    c.drawString(x + 10, y - 10, text)
    return x + width + 8


def footer(c: canvas.Canvas, page_num: int, section: str) -> None:
    if page_num == 1:
        return
    c.setStrokeColor(hex_color("line"))
    c.line(54, 40, 558, 40)
    c.setFillColor(hex_color("muted"))
    c.setFont("Lato", 8.5)
    c.drawString(54, 25, "Mindful Diabetes Inc. | Free Guides | mindfuldiabetes.org")
    c.drawCentredString(306, 25, section)
    c.setFillColor(hex_color("coral"))
    c.setFont("Lato-Bold", 9)
    c.drawRightString(558, 25, str(page_num))


def page_header(c: canvas.Canvas, page_num: int, section: str) -> None:
    if page_num == 1:
        return
    c.drawImage(str(LOGO), 54, 724, width=28, height=30, mask="auto")
    c.setFillColor(hex_color("navy"))
    c.setFont("Lora-Bold", 10)
    c.drawString(90, 742, "The Mindful Plate")
    c.setFillColor(hex_color("muted"))
    c.setFont("Lato", 8)
    c.drawString(90, 729, "A Simple Guide to Blood Sugar-Friendly Eating")
    c.setStrokeColor(hex_color("line"))
    c.line(54, 716, 558, 716)


def start_page(c: canvas.Canvas, page_num: int, section: str) -> None:
    c.setFillColor(hex_color("cream"))
    c.rect(0, 0, 612, 792, fill=1, stroke=0)
    page_header(c, page_num, section)


def end_page(c: canvas.Canvas, page_num: int, section: str) -> None:
    footer(c, page_num, section)
    c.showPage()


def draw_plate(c: canvas.Canvas, x: float, y: float, r: float) -> None:
    c.setFillColor(colors.white)
    c.setStrokeColor(hex_color("navy"))
    c.setLineWidth(1.6)
    c.circle(x, y, r, fill=1, stroke=1)
    c.setFillColor(hex_color("soft_green"))
    c.wedge(x - r + 8, y - r + 8, x + r - 8, y + r - 8, 90, 270, fill=1, stroke=0)
    c.setFillColor(hex_color("soft_orange"))
    c.wedge(x - r + 8, y - r + 8, x + r - 8, y + r - 8, 270, 360, fill=1, stroke=0)
    c.setFillColor(hex_color("soft"))
    c.wedge(x - r + 8, y - r + 8, x + r - 8, y + r - 8, 0, 90, fill=1, stroke=0)
    c.setStrokeColor(colors.white)
    c.setLineWidth(3)
    c.line(x, y - r + 12, x, y + r - 12)
    c.line(x, y, x + r - 12, y)
    c.setFillColor(hex_color("green"))
    c.setFont("Lato-Bold", 10)
    c.drawCentredString(x - r * 0.38, y + 2, "1/2")
    c.drawCentredString(x - r * 0.38, y - 13, "vegetables")
    c.setFillColor(hex_color("navy"))
    c.drawCentredString(x + r * 0.36, y + r * 0.37, "1/4")
    c.drawCentredString(x + r * 0.36, y + r * 0.22, "protein")
    c.setFillColor(hex_color("coral_dark"))
    c.drawCentredString(x + r * 0.36, y - r * 0.33, "1/4")
    c.drawCentredString(x + r * 0.36, y - r * 0.48, "carbs")


def asset_canvas(name: str, size=(1800, 1200), bg="cream") -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", size, COLORS[bg])
    return img, ImageDraw.Draw(img)


def save_asset(img: Image.Image, name: str) -> str:
    path = IMAGES / name
    img.save(path, quality=95)
    return str(path)


def save_cropped_asset(source_name: str, output_name: str, top_crop: int) -> None:
    source = Image.open(IMAGES / source_name).convert("RGB")
    cropped = source.crop((0, top_crop, source.width, source.height))
    cropped.save(IMAGES / output_name, quality=95)


def rounded_rect(draw: ImageDraw.ImageDraw, xy, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def generate_visual_assets() -> list[dict[str, str]]:
    assets: list[dict[str, str]] = []
    lato = pil_font("Lato-Regular.ttf", 42)
    lato_b = pil_font("Lato-Bold.ttf", 52)
    lora_b = pil_font("Lora-Bold.ttf", 82)
    small = pil_font("Lato-Regular.ttf", 30)

    # 1 cover
    img, d = asset_canvas("mindful-plate-cover-illustration.png", (1800, 2400), "cream")
    d.rounded_rectangle((120, 120, 1680, 2280), radius=58, fill="#fffdf8", outline=COLORS["line"], width=3)
    d.ellipse((345, 620, 1455, 1730), fill="#ffffff", outline=COLORS["navy"], width=8)
    d.pieslice((405, 680, 1395, 1670), 90, 270, fill=COLORS["soft_green"])
    d.pieslice((405, 680, 1395, 1670), 0, 90, fill=COLORS["soft"])
    d.pieslice((405, 680, 1395, 1670), 270, 360, fill=COLORS["soft_orange"])
    d.line((900, 690, 900, 1660), fill="#ffffff", width=15)
    d.line((900, 1175, 1390, 1175), fill="#ffffff", width=15)
    for cx, cy, col in [(590, 900, "#2f8f5b"), (660, 1040, "#70b77e"), (555, 1240, "#3f9e76"), (700, 1360, "#81bd64")]:
        d.ellipse((cx - 58, cy - 40, cx + 58, cy + 40), fill=col)
    for cx, cy in [(1070, 865), (1180, 960), (1085, 1048)]:
        d.rounded_rectangle((cx - 85, cy - 45, cx + 85, cy + 45), radius=30, fill="#f5d7bd", outline="#b06d43", width=4)
    for cx, cy, col in [(1100, 1360, "#b27c3f"), (1190, 1435, "#cf9b56"), (1020, 1490, "#a86c34")]:
        d.ellipse((cx - 70, cy - 50, cx + 70, cy + 50), fill=col, outline="#72471f", width=3)
    d.text((180, 270), "Mindful Diabetes Free Guides", font=lato_b, fill=COLORS["green"])
    d.text((180, 360), "The Mindful\nPlate", font=lora_b, fill=COLORS["navy"], spacing=6)
    d.text((180, 560), "A simple guide to blood sugar-friendly eating", font=lato, fill=COLORS["body"])
    d.rounded_rectangle((180, 1990, 610, 2070), radius=40, fill=COLORS["coral"])
    d.text((225, 2008), "FREE GUIDE", font=lato_b, fill="#ffffff")
    save_asset(img, "mindful-plate-cover-illustration.png")
    assets.append({"file": "mindful-plate-cover-illustration.png", "title": "Cover meal illustration", "alt": "Illustrated balanced plate with vegetables, protein, and carbohydrate sections."})

    # 2 plate diagram
    img, d = asset_canvas("mindful-plate-diagram.png")
    d.text((90, 80), "The Mindful Plate method", font=lora_b, fill=COLORS["navy"])
    cx, cy, r = 720, 650, 430
    d.ellipse((cx-r, cy-r, cx+r, cy+r), fill="#ffffff", outline=COLORS["navy"], width=7)
    d.pieslice((cx-r+25, cy-r+25, cx+r-25, cy+r-25), 90, 270, fill=COLORS["soft_green"])
    d.pieslice((cx-r+25, cy-r+25, cx+r-25, cy+r-25), 0, 90, fill=COLORS["soft"])
    d.pieslice((cx-r+25, cy-r+25, cx+r-25, cy+r-25), 270, 360, fill=COLORS["soft_orange"])
    d.line((cx, cy-r+30, cx, cy+r-30), fill="#ffffff", width=15)
    d.line((cx, cy, cx+r-30, cy), fill="#ffffff", width=15)
    d.text((360, 610), "1/2\nnon-starchy\nvegetables", font=lato_b, fill=COLORS["green"], align="center")
    d.text((920, 420), "1/4\nprotein", font=lato_b, fill=COLORS["navy"], align="center")
    d.text((920, 800), "1/4\nquality\ncarbohydrate", font=lato_b, fill=COLORS["coral_dark"], align="center")
    rounded_rect(d, (1230, 450, 1650, 700), 30, COLORS["soft"], COLORS["line"], 3)
    d.text((1285, 510), "Water or another\nlow-sugar drink", font=lato_b, fill=COLORS["navy"])
    d.text((1285, 640), "Flexible starting point,\nnot a rigid rule.", font=small, fill=COLORS["body"])
    save_asset(img, "mindful-plate-diagram.png")
    assets.append({"file": "mindful-plate-diagram.png", "title": "Mindful Plate diagram", "alt": "Plate divided into one-half vegetables, one-quarter protein, and one-quarter carbohydrate, with a drink note."})

    # 3 pathway
    img, d = asset_canvas("digestion-glucose-insulin-pathway.png", (1800, 1050))
    d.text((90, 70), "What happens after we eat?", font=lora_b, fill=COLORS["navy"])
    steps = [
        ("Meal", "Food enters the stomach\nand begins digestion."),
        ("Glucose", "Carbohydrates break down\ninto glucose in the blood."),
        ("Insulin", "Insulin helps move glucose\nfrom blood into cells."),
        ("Energy", "Cells use glucose for energy\nor store some for later."),
    ]
    x = 120
    for i, (h, b) in enumerate(steps):
        rounded_rect(d, (x, 345, x + 315, 680), 34, "#ffffff", COLORS["line"], 4)
        d.ellipse((x + 98, 390, x + 218, 510), fill=[COLORS["soft_green"], COLORS["soft_orange"], COLORS["soft"], "#f9f0c7"][i], outline=COLORS["navy"], width=4)
        d.text((x + 40, 535), h, font=lato_b, fill=COLORS["navy"])
        d.text((x + 40, 605), b, font=small, fill=COLORS["body"], spacing=4)
        if i < 3:
            d.line((x + 330, 510, x + 410, 510), fill=COLORS["coral"], width=8)
            d.polygon([(x + 410, 510), (x + 380, 492), (x + 380, 528)], fill=COLORS["coral"])
        x += 410
    d.text((120, 805), "The speed and size of the rise can be affected by the food, portion, fiber, protein, fat, timing, activity, stress, illness, sleep, and medicines.", font=lato, fill=COLORS["body"])
    save_asset(img, "digestion-glucose-insulin-pathway.png")
    assets.append({"file": "digestion-glucose-insulin-pathway.png", "title": "Digestion glucose insulin pathway", "alt": "Four-step pathway from meal to glucose to insulin to cell energy."})

    # 4 carb families
    img, d = asset_canvas("carbohydrate-food-families.png", (1800, 1200))
    d.text((90, 75), "Carbohydrate food families", font=lora_b, fill=COLORS["navy"])
    groups = [
        ("Grains", "rice, oats, pasta,\nbread, tortillas"),
        ("Starchy vegetables", "potatoes, corn,\npeas, plantains"),
        ("Fruit", "berries, apples,\nbananas, oranges"),
        ("Milk/yogurt", "milk, plain yogurt,\nkefir"),
        ("Beans/lentils", "black beans,\nchickpeas, dal"),
        ("Sweets/drinks", "soda, candy,\nsweet tea, desserts"),
    ]
    for i, (h, b) in enumerate(groups):
        row = i // 3
        col = i % 3
        x = 110 + col * 555
        y = 250 + row * 390
        fill = [COLORS["soft"], COLORS["soft_orange"], COLORS["soft_green"], "#f8f4ff", "#eef8f8", "#fff2f2"][i]
        rounded_rect(d, (x, y, x + 470, y + 280), 30, fill, COLORS["line"], 3)
        d.text((x + 34, y + 35), h, font=lato_b, fill=COLORS["navy"])
        d.text((x + 34, y + 125), b, font=lato, fill=COLORS["body"], spacing=7)
    save_asset(img, "carbohydrate-food-families.png")
    assets.append({"file": "carbohydrate-food-families.png", "title": "Carbohydrate food families", "alt": "Six groups of carbohydrate foods, including grains, fruit, starchy vegetables, dairy, beans, and sweets."})

    # 5 fiber visual
    img, d = asset_canvas("fiber-visual.png", (1800, 1100))
    d.text((90, 75), "Fiber helps meals feel steadier", font=lora_b, fill=COLORS["navy"])
    rounded_rect(d, (170, 320, 800, 820), 36, "#ffffff", COLORS["line"], 4)
    rounded_rect(d, (1000, 320, 1630, 820), 36, "#ffffff", COLORS["line"], 4)
    d.text((250, 380), "Lower-fiber meal", font=lato_b, fill=COLORS["coral_dark"])
    d.text((1080, 380), "Higher-fiber meal", font=lato_b, fill=COLORS["green"])
    d.line((260, 700, 710, 700), fill=COLORS["line"], width=5)
    d.line((260, 700, 360, 450, 710, 640), fill=COLORS["coral"], width=10)
    d.line((1090, 700, 1540, 700), fill=COLORS["line"], width=5)
    pts = [(1090, 690), (1210, 590), (1340, 555), (1540, 620)]
    for a, b in zip(pts, pts[1:]):
        d.line((*a, *b), fill=COLORS["green"], width=10)
    d.text((250, 760), "May digest faster\nfor some people.", font=small, fill=COLORS["body"])
    d.text((1080, 760), "Often slows digestion\nand supports fullness.", font=small, fill=COLORS["body"])
    save_asset(img, "fiber-visual.png")
    assets.append({"file": "fiber-visual.png", "title": "Fiber visual", "alt": "Comparison showing a sharper curve for lower-fiber meals and a steadier curve for higher-fiber meals."})

    # 6 breakfast grid
    img, d = asset_canvas("breakfast-example-grid.png", (1800, 1200))
    d.text((90, 75), "Four breakfast examples", font=lora_b, fill=COLORS["navy"])
    examples = [
        ("Eggs + toast + vegetables", "eggs, greens, whole-grain toast"),
        ("Yogurt bowl", "plain yogurt, berries, nuts, oats"),
        ("Oatmeal", "oats, chia, fruit, nut butter"),
        ("Beans + tortilla", "beans, egg, salsa, corn tortilla"),
    ]
    for i, (h, b) in enumerate(examples):
        x = 120 + (i % 2) * 830
        y = 250 + (i // 2) * 410
        rounded_rect(d, (x, y, x + 710, y + 310), 32, "#ffffff", COLORS["line"], 4)
        d.ellipse((x + 45, y + 58, x + 255, y + 268), fill=COLORS["soft_green"], outline=COLORS["navy"], width=4)
        d.ellipse((x + 90, y + 100, x + 145, y + 155), fill=COLORS["coral"])
        d.ellipse((x + 155, y + 165, x + 215, y + 225), fill=COLORS["green"])
        d.text((x + 300, y + 70), h, font=lato_b, fill=COLORS["navy"])
        d.text((x + 300, y + 155), b, font=small, fill=COLORS["body"])
    save_asset(img, "breakfast-example-grid.png")
    assets.append({"file": "breakfast-example-grid.png", "title": "Breakfast example grid", "alt": "Four balanced breakfast examples using eggs, yogurt, oatmeal, and beans."})

    # 7 drink comparison
    img, d = asset_canvas("drink-comparison-graphic.png", (1800, 1150))
    d.text((90, 75), "Drinks can change the meal", font=lora_b, fill=COLORS["navy"])
    drinks = [
        ("Water", "0 g carbs", COLORS["soft"]),
        ("Unsweet tea", "0 g carbs", COLORS["soft_green"]),
        ("Milk", "check label", "#f8f4ff"),
        ("Juice", "can add up fast", COLORS["soft_orange"]),
        ("Soda", "high added sugar", "#fff2f2"),
    ]
    for i, (h, b, fill) in enumerate(drinks):
        x = 140 + i * 325
        d.rounded_rectangle((x, 310, x + 210, 765), radius=52, fill=fill, outline=COLORS["navy"], width=4)
        d.rectangle((x + 42, 260, x + 168, 330), fill=COLORS["navy"])
        d.text((x + 35, 820), h, font=lato_b, fill=COLORS["navy"])
        d.text((x + 35, 880), b, font=small, fill=COLORS["body"])
    d.text((140, 1010), "A drink does not need to be perfect. Start by improving one drink you have often.", font=lato, fill=COLORS["body"])
    save_asset(img, "drink-comparison-graphic.png")
    assets.append({"file": "drink-comparison-graphic.png", "title": "Drink comparison graphic", "alt": "Five drink options from water and unsweet tea to soda, with carbohydrate notes."})

    # 8 worksheet
    img, d = asset_canvas("build-a-meal-worksheet.png", (1800, 1350), "white")
    d.text((90, 70), "Build your own Mindful Plate", font=lora_b, fill=COLORS["navy"])
    labels = ["1/2 plate vegetables", "1/4 plate protein", "1/4 plate carbohydrate", "Drink", "Flavor or fat", "What I can prep ahead"]
    for i, lab in enumerate(labels):
        x = 110 + (i % 2) * 830
        y = 230 + (i // 2) * 330
        rounded_rect(d, (x, y, x + 720, y + 245), 25, COLORS["soft"], COLORS["line"], 3)
        d.text((x + 30, y + 32), lab, font=lato_b, fill=COLORS["navy"])
        for n in range(3):
            yy = y + 100 + n * 42
            d.line((x + 38, yy, x + 675, yy), fill="#b8beca", width=2)
    save_asset(img, "build-a-meal-worksheet.png")
    assets.append({"file": "build-a-meal-worksheet.png", "title": "Build a meal worksheet", "alt": "Printable worksheet with spaces for vegetables, protein, carbohydrate, drink, flavor, and prep-ahead notes."})

    for source_name, output_name, top_crop in [
        ("mindful-plate-diagram.png", "mindful-plate-diagram-pdf.png", 190),
        ("digestion-glucose-insulin-pathway.png", "digestion-glucose-insulin-pathway-pdf.png", 190),
        ("carbohydrate-food-families.png", "carbohydrate-food-families-pdf.png", 190),
        ("fiber-visual.png", "fiber-visual-pdf.png", 190),
        ("breakfast-example-grid.png", "breakfast-example-grid-pdf.png", 190),
        ("drink-comparison-graphic.png", "drink-comparison-graphic-pdf.png", 190),
        ("build-a-meal-worksheet.png", "build-a-meal-worksheet-pdf.png", 165),
    ]:
        save_cropped_asset(source_name, output_name, top_crop)

    return assets


def generate_website_assets() -> None:
    logo = Image.open(LOGO).convert("RGB").resize((86, 91))
    lora_big = pil_font("Lora-Bold.ttf", 86)
    lora_med = pil_font("Lora-Bold.ttf", 58)
    lato = pil_font("Lato-Regular.ttf", 34)
    lato_b = pil_font("Lato-Bold.ttf", 28)

    def draw_plate_mark(d: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
        x0, y0, x1, y1 = box
        d.ellipse(box, fill="#ffffff", outline=COLORS["navy"], width=5)
        d.pieslice((x0 + 18, y0 + 18, x1 - 18, y1 - 18), 90, 270, fill=COLORS["soft_green"])
        d.pieslice((x0 + 18, y0 + 18, x1 - 18, y1 - 18), 0, 90, fill=COLORS["soft"])
        d.pieslice((x0 + 18, y0 + 18, x1 - 18, y1 - 18), 270, 360, fill=COLORS["soft_orange"])
        cx = (x0 + x1) // 2
        cy = (y0 + y1) // 2
        d.line((cx, y0 + 24, cx, y1 - 24), fill="#ffffff", width=10)
        d.line((cx, cy, x1 - 24, cy), fill="#ffffff", width=10)

    # Vertical cover preview.
    img = Image.new("RGB", (1200, 1553), COLORS["cream"])
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((72, 72, 1128, 1480), radius=42, fill="#fffdf8", outline=COLORS["line"], width=3)
    img.paste(logo, (116, 114))
    d.text((225, 128), "MINDFUL DIABETES FREE GUIDES", font=lato_b, fill=COLORS["green"])
    d.text((116, 320), "The\nMindful\nPlate", font=lora_big, fill=COLORS["navy"], spacing=4)
    d.text((120, 650), "A Simple Guide to Blood\nSugar-Friendly Eating", font=lato, fill=COLORS["body"], spacing=7)
    draw_plate_mark(d, (650, 600, 1035, 985))
    d.rounded_rectangle((120, 1260, 365, 1330), radius=35, fill=COLORS["coral"])
    d.text((168, 1278), "FREE GUIDE", font=lato_b, fill="#ffffff")
    img.save(WEBSITE / "mindful-plate-cover-preview.png", quality=95)

    # Square promo.
    img = Image.new("RGB", (1080, 1080), COLORS["soft_green"])
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((64, 64, 1016, 1016), radius=38, fill="#fffdf8", outline=COLORS["line"], width=3)
    img.paste(logo.resize((72, 76)), (100, 100))
    d.text((195, 116), "Mindful Diabetes Free Guides", font=lato_b, fill=COLORS["green"])
    d.text((100, 240), "The Mindful\nPlate", font=lora_big, fill=COLORS["navy"], spacing=3)
    d.text((105, 452), "Simple guidance for building\nblood sugar-friendly meals.", font=lato, fill=COLORS["body"], spacing=8)
    draw_plate_mark(d, (585, 470, 915, 800))
    d.rounded_rectangle((105, 850, 455, 918), radius=34, fill=COLORS["coral"])
    d.text((150, 868), "Download free", font=lato_b, fill="#ffffff")
    img.save(WEBSITE / "mindful-plate-square-promo.png", quality=95)

    # 16:9 banner.
    img = Image.new("RGB", (1600, 900), COLORS["cream"])
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, 1600, 900), fill=COLORS["cream"])
    d.rounded_rectangle((70, 70, 1530, 830), radius=34, fill="#fffdf8", outline=COLORS["line"], width=3)
    img.paste(logo.resize((76, 80)), (120, 120))
    d.text((220, 132), "Mindful Diabetes Free Guides", font=lato_b, fill=COLORS["green"])
    d.text((120, 265), "The Mindful Plate", font=lora_big, fill=COLORS["navy"])
    d.text((124, 390), "A simple guide to blood sugar-friendly eating", font=lato, fill=COLORS["body"])
    d.rounded_rectangle((124, 545, 470, 615), radius=35, fill=COLORS["coral"])
    d.text((178, 563), "Download the Free Guide", font=lato_b, fill="#ffffff")
    draw_plate_mark(d, (1020, 225, 1390, 595))
    img.save(WEBSITE / "mindful-plate-banner-16x9.png", quality=95)

    # Download-card thumbnail.
    img = Image.new("RGB", (600, 420), COLORS["soft"])
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((28, 28, 572, 392), radius=24, fill="#fffdf8", outline=COLORS["line"], width=2)
    d.text((54, 58), "The Mindful Plate", font=lora_med, fill=COLORS["navy"])
    d.text((58, 145), "Blood sugar-friendly eating", font=lato_b, fill=COLORS["green"])
    draw_plate_mark(d, (320, 130, 510, 320))
    d.rounded_rectangle((58, 300, 218, 344), radius=22, fill=COLORS["coral"])
    d.text((82, 310), "Free PDF", font=lato_b, fill="#ffffff")
    img.save(WEBSITE / "mindful-plate-download-card-thumbnail.png", quality=95)


@dataclass
class Ref:
    n: int
    label: str
    source: str
    year: str
    url: str


REFS = [
    Ref(1, "American Diabetes Association", "Standards of Care in Diabetes - 2026", "2026", "https://diabetesjournals.org/care/issue/49/Supplement_1"),
    Ref(2, "American Diabetes Association Nutrition & Wellness Team", "What is the Diabetes Plate?", "2026", "https://diabetesfoodhub.org/blog/what-diabetes-plate"),
    Ref(3, "U.S. Food and Drug Administration", "How to Understand and Use the Nutrition Facts Label", "2024", "https://www.fda.gov/food/nutrition-facts-label/how-understand-and-use-nutrition-facts-label"),
    Ref(4, "U.S. Food and Drug Administration", "Added Sugars on the Nutrition Facts Label", "2026", "https://www.fda.gov/food/nutrition-facts-label/added-sugars-nutrition-facts-label"),
    Ref(5, "Centers for Disease Control and Prevention", "What Is the National Diabetes Prevention Program?", "2024", "https://www.cdc.gov/diabetes-prevention/programs/what-is-the-national-dpp.html"),
    Ref(6, "Centers for Disease Control and Prevention", "Your Brain and Diabetes", "2024", "https://www.cdc.gov/diabetes/diabetes-complications/effects-of-diabetes-brain.html"),
    Ref(7, "American Heart Association", "Fats in Foods", "2026", "https://www.heart.org/en/healthy-living/healthy-eating/eat-smart/fats/fats-in-foods"),
    Ref(8, "American Heart Association", "Saturated Fats", "2024", "https://www.heart.org/en/healthy-living/healthy-eating/eat-smart/fats/saturated-fats"),
]


def draw_cover(c: canvas.Canvas) -> None:
    c.setFillColor(hex_color("cream"))
    c.rect(0, 0, 612, 792, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setStrokeColor(hex_color("line"))
    c.roundRect(42, 42, 528, 708, 18, fill=1, stroke=1)
    c.drawImage(str(LOGO), 68, 684, width=46, height=49, mask="auto")
    c.setFillColor(hex_color("green"))
    c.setFont("Lato-Bold", 9.5)
    c.drawString(126, 720, "MINDFUL DIABETES FREE GUIDES")
    c.setFillColor(hex_color("muted"))
    c.setFont("Lato", 8.5)
    c.drawString(126, 703, "Simple, practical guidance for metabolic and brain health.")
    c.drawImage(str(IMAGES / "mindful-plate-cover-illustration.png"), 306, 248, width=220, height=293, mask="auto")
    c.setFillColor(hex_color("navy"))
    c.setFont("Lora-Bold", 48)
    c.drawString(74, 565, "The")
    c.drawString(74, 512, "Mindful")
    c.drawString(74, 459, "Plate")
    c.setFillColor(hex_color("body"))
    c.setFont("Lato", 16)
    c.drawString(76, 415, "A Simple Guide to Blood")
    c.drawString(76, 393, "Sugar-Friendly Eating")
    c.setFillColor(hex_color("coral"))
    c.roundRect(76, 326, 112, 34, 17, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Lato-Bold", 10)
    c.drawCentredString(132, 338, "FREE GUIDE")
    c.setFillColor(hex_color("muted"))
    c.setFont("Lato", 9)
    c.drawString(76, 107, "Mindful Diabetes Inc. | 501(c)(3) nonprofit")
    c.drawString(76, 88, "Published: July 30, 2026 | Medical review: pending")
    c.linkURL("https://mindfuldiabetes.org", (74, 78, 220, 100), relative=0)
    footer(c, 1, "")
    c.showPage()


def content_pages(c: canvas.Canvas) -> None:
    # Page 2
    start_page(c, 2, "Welcome")
    x, y, w = 72, 672, 468
    eyebrow(c, "Welcome", x, y)
    y = title(c, "A calmer way to build a meal", x, y - 24, w, 30)
    y = text_box(c, "If food advice has started to feel like a stack of rules, this guide is meant to lower the noise. The Mindful Plate is a flexible way to assemble meals that include vegetables, protein, carbohydrate, and flavor without weighing everything or giving up foods that matter to you.", x, y - 12, w, 12.2, 16)
    y = text_box(c, "It is written for adults with type 2 diabetes, prediabetes, a family history of diabetes, or an interest in metabolic and brain health. Caregivers and family members may also find it useful.", x, y - 8, w, 11.2, 15)
    callout(c, "This guide can help with", "Building balanced meals, reading your plate more clearly, choosing drinks with less added sugar, and planning a few realistic meals for the week.", x, y - 20, 220, 112, "green")
    callout(c, "This guide cannot replace", "Medical nutrition therapy, medication advice, glucose targets, insulin adjustment, pregnancy care, eating-disorder care, kidney-disease guidance, or urgent medical attention.", x + 248, y - 20, 220, 112, "orange")
    y -= 160
    y = heading(c, "A useful plate is not a perfect plate", x, y, w, 18)
    y = text_box(c, "Some meals are mixed together in a bowl. Some come from a restaurant. Some are leftovers eaten between responsibilities. That is real life. Use this method as a starting point, then adapt it with your clinician or dietitian if you have specific needs.", x, y - 6, w, 11, 14.5)
    end_page(c, 2, "Welcome")

    # Page 3
    start_page(c, 3, "Quick Start")
    x, y = 72, 672
    eyebrow(c, "Quick start", x, y)
    y = title(c, "Start here tonight", x, y - 24, 468, 30)
    steps = [
        "Choose one meal, not your whole life.",
        "Fill about half the plate with non-starchy vegetables if you have them.",
        "Add a protein food such as eggs, chicken, fish, tofu, beans, yogurt, or lean meat.",
        "Choose one carbohydrate food such as rice, oats, bread, potato, fruit, lentils, or tortilla.",
        "Pick water, unsweet tea, or another drink that does not add much sugar.",
        "Notice how you feel afterward. If you check glucose, follow the plan your care team gave you.",
    ]
    y = bullet_list(c, steps, x, y - 8, 468)
    callout(c, "No all-or-nothing test", "If half the plate is not possible, add one vegetable side. If dinner is pizza, add a salad or vegetables and use the next meal as another chance.", x, y - 12, 468, 88, "green")
    y -= 126
    y = heading(c, "Contents", x, y, 468, 18)
    contents = [
        "4 What happens after we eat?",
        "5 The Mindful Plate method",
        "6-9 Carbohydrates, protein, fiber, and fat",
        "10-13 Breakfast, lunch, dinner, and snacks",
        "14-16 Drinks, portions, and sample menus",
        "17-20 Worksheets, grocery list, questions, references",
    ]
    y = bullet_list(c, contents, x, y - 6, 468, 10)
    end_page(c, 3, "Quick Start")

    # Page 4
    start_page(c, 4, "Food and Blood Sugar")
    x, y = 72, 672
    eyebrow(c, "Food and blood sugar", x, y)
    y = title(c, "What happens after we eat?", x, y - 24, 468, 30)
    c.drawImage(str(IMAGES / "digestion-glucose-insulin-pathway-pdf.png"), 76, 392, width=460, height=220, mask="auto")
    y = 362
    y = text_box(c, "During digestion, the body breaks food into smaller parts. Carbohydrate foods usually have the most direct effect on blood glucose because many carbohydrates break down into glucose. Insulin is a hormone that helps move glucose from the blood into cells so it can be used for energy. [1]", x, y, 468, 10.8, 14.2)
    y = text_box(c, "That does not mean carbohydrates are the only thing that matters. Protein, fiber, fat, the size of the portion, timing, activity, illness, stress, sleep, alcohol, and medicines can all influence glucose patterns. Two people can eat a similar meal and see different results.", x, y - 8, 468, 10.8, 14.2)
    callout(c, "Safety note", "Do not change insulin, diabetes medicine, or glucose targets because of this guide. If your readings are often high or low, ask your care team what changes are safest for you.", x, y - 18, 468, 86, "orange")
    end_page(c, 4, "Food and Blood Sugar")

    # Page 5
    start_page(c, 5, "Plate Method")
    x, y = 72, 672
    eyebrow(c, "The method", x, y)
    y = title(c, "The Mindful Plate", x, y - 24, 220, 30)
    draw_plate(c, 402, 424, 118)
    c.setFillColor(colors.white)
    c.setStrokeColor(hex_color("line"))
    c.roundRect(292, 282, 220, 58, 8, fill=1, stroke=1)
    c.setFillColor(hex_color("navy"))
    c.setFont("Lato-Bold", 9)
    c.drawString(308, 318, "Water or another low-sugar drink")
    c.setFillColor(hex_color("body"))
    c.setFont("Lato", 8.2)
    c.drawString(308, 302, "Optional unsaturated fat can add flavor.")
    y = text_box(c, "The plate method is a simple visual approach. A common diabetes plate pattern uses about one-half non-starchy vegetables, one-quarter protein, and one-quarter carbohydrate, with water or another low-calorie drink. [2]", x, y - 4, 220, 10.8, 14)
    y = text_box(c, "This guide uses that pattern as a flexible starting point. It can work with many food traditions: rice and beans, dal and vegetables, tacos, stir-fries, soups, sandwiches, Mediterranean meals, Caribbean plates, or leftovers.", x, y - 8, 220, 10.8, 14)
    callout(c, "What this does not mean", "It does not mean every meal must look separated on a plate. Mixed dishes can still be balanced by thinking about what is inside them and what you serve alongside them.", 72, 190, 468, 90, "green")
    end_page(c, 5, "Plate Method")

    # Page 6
    start_page(c, 6, "Carbohydrates")
    x, y = 72, 672
    eyebrow(c, "Carbohydrates", x, y)
    y = title(c, "Carbs without confusion", x, y - 24, 468, 30)
    c.drawImage(str(IMAGES / "carbohydrate-food-families-pdf.png"), 76, 335, width=460, height=258, mask="auto")
    y = 305
    y = text_box(c, "Carbohydrates are found in grains, starchy vegetables, fruit, milk, yogurt, beans, lentils, sweets, and sugary drinks. They are not automatically forbidden. The type, amount, and what you eat with them matter.", x, y, 468, 10.8, 14.2)
    y = text_box(c, "A helpful pattern is to pair carbohydrate foods with protein, fiber-rich foods, and vegetables when possible. For example, rice with beans and vegetables is different from rice alone. Oatmeal with nuts and berries is different from sweetened cereal and juice.", x, y - 8, 468, 10.8, 14.2)
    callout(c, "Try this", "Choose one carbohydrate you eat often. Keep the food, but experiment with the portion and what you pair it with.", x, y - 18, 468, 74, "green")
    end_page(c, 6, "Carbohydrates")

    # Page 7
    start_page(c, 7, "Protein")
    x, y = 72, 672
    eyebrow(c, "Protein", x, y)
    y = title(c, "Protein helps a meal hold together", x, y - 24, 468, 29)
    y = text_box(c, "Protein foods can support fullness and help make a meal feel more steady. They may come from animal or plant sources: eggs, fish, chicken, turkey, lean meats, tofu, tempeh, edamame, Greek yogurt, cottage cheese, beans, lentils, and nuts or seeds.", x, y - 8, 468, 11.3, 15)
    y = heading(c, "Budget-friendly options", x, y - 14, 468, 18)
    y = bullet_list(c, [
        "Canned tuna or salmon, if it fits your budget and preferences.",
        "Eggs, which can work at breakfast, lunch, or dinner.",
        "Dried or canned beans and lentils. Rinse canned beans to lower sodium.",
        "Plain yogurt bought in a larger container instead of single sweetened cups.",
        "Frozen fish or chicken when fresh options are expensive.",
    ], x, y - 4, 468)
    callout(c, "Beans count in two places", "Beans and lentils contain protein and carbohydrate. They can still fit beautifully. Pair them with vegetables and consider the rest of the meal.", x, y - 12, 468, 82, "green")
    end_page(c, 7, "Protein")

    # Page 8
    start_page(c, 8, "Fiber")
    x, y = 72, 672
    eyebrow(c, "Fiber", x, y)
    y = title(c, "Fiber is quiet but powerful", x, y - 24, 468, 30)
    c.drawImage(str(IMAGES / "fiber-visual-pdf.png"), 78, 420, width=458, height=214, mask="auto")
    y = 386
    y = text_box(c, "Fiber is a type of carbohydrate the body does not fully digest. Many fiber-rich foods can help with fullness, bowel regularity, cholesterol patterns, and steadier meals. The FDA Daily Value for fiber is 28 grams per day based on a 2,000-calorie diet, but individual needs vary. [3]", x, y, 468, 10.5, 13.8)
    y = text_box(c, "Add fiber gradually. A sudden jump from very little fiber to a lot can cause gas, bloating, or discomfort. Fluids matter too. People with digestive disease, kidney disease, swallowing problems, or certain medical diets should ask for individualized guidance.", x, y - 8, 468, 10.5, 13.8)
    end_page(c, 8, "Fiber")

    # Page 9
    start_page(c, 9, "Dietary Fat")
    x, y = 72, 672
    eyebrow(c, "Dietary fat", x, y)
    y = title(c, "Fat adds flavor, texture, and staying power", x, y - 24, 468, 28)
    y = text_box(c, "Dietary fat is an essential nutrient. It helps with cell function, flavor, satisfaction, and absorption of some vitamins. The type and food source matter. A heart-health pattern usually emphasizes unsaturated fats from foods such as nuts, seeds, avocado, fish, and non-tropical liquid plant oils, while limiting saturated fat and avoiding trans fat. [7]", x, y - 8, 468, 11, 14.5)
    y = heading(c, "Small amounts can go a long way", x, y - 14, 468, 18)
    y = bullet_list(c, [
        "Add avocado or nuts to a meal that needs staying power.",
        "Use olive, canola, soybean, or other non-tropical liquid oils when they fit the recipe.",
        "Choose fried foods and high-saturated-fat foods less often if heart health is a concern.",
        "If you have cholesterol, kidney, liver, or digestive concerns, ask your care team what fits you.",
    ], x, y - 4, 468)
    callout(c, "More detail coming", "This guide gives only the basics. The companion guide Fats Without Fear will explain saturated, unsaturated, and trans fats in plain language.", x, y - 12, 468, 82, "green")
    end_page(c, 9, "Dietary Fat")

    # Page 10
    start_page(c, 10, "Breakfasts")
    x, y = 72, 672
    eyebrow(c, "Examples", x, y)
    y = title(c, "Breakfasts, if breakfast fits your day", x, y - 24, 468, 29)
    c.drawImage(str(IMAGES / "breakfast-example-grid-pdf.png"), 76, 315, width=460, height=258, mask="auto")
    y = 285
    y = text_box(c, "Not everyone wants or needs breakfast. If you do eat it, breakfast can be a useful place to add protein, fiber, and a lower-sugar drink.", x, y, 468, 10.8, 14.2)
    y = bullet_list(c, [
        "Eggs, whole-grain toast, sauteed greens, and tomato.",
        "Plain yogurt with berries, nuts, and a small amount of oats.",
        "Oatmeal with chia or ground flax, fruit, and nut butter.",
        "Beans, egg or tofu, salsa, vegetables, and a corn tortilla.",
    ], x, y - 8, 468)
    end_page(c, 10, "Breakfasts")

    # Page 11
    start_page(c, 11, "Lunches")
    x, y = 72, 672
    eyebrow(c, "Examples", x, y)
    y = title(c, "Lunches that do not require a fresh start", x, y - 24, 468, 29)
    y = text_box(c, "Lunch often happens between work, caregiving, school, appointments, or errands. It does not need to be a recipe. Think in pieces: something colorful, something protein-rich, something with fiber, and something you enjoy.", x, y - 8, 468, 11, 14.5)
    y = heading(c, "Flexible lunch ideas", x, y - 14, 468, 18)
    y = bullet_list(c, [
        "Bowl: greens, leftover chicken or tofu, beans, salsa, and brown rice or quinoa.",
        "Sandwich: whole-grain bread, turkey or hummus, vegetables, and fruit on the side.",
        "Soup: lentil, bean, chicken vegetable, or minestrone, plus salad if available.",
        "No-cook: tuna packet, whole-grain crackers, cucumber, carrots, and fruit.",
        "Leftovers: add a vegetable side or a handful of greens to yesterday's dinner.",
    ], x, y - 4, 468)
    callout(c, "Restaurant note", "If lunch is ordered out, look for one adjustment: add vegetables, choose water, share fries, or save part for later. One useful change is enough.", x, y - 12, 468, 82, "green")
    end_page(c, 11, "Lunches")

    # Page 12
    start_page(c, 12, "Dinners")
    x, y = 72, 672
    eyebrow(c, "Examples", x, y)
    y = title(c, "Dinners can honor culture and still be balanced", x, y - 24, 468, 28)
    y = text_box(c, "Healthy eating should not erase family food. Many traditional meals already include the pieces we are looking for: vegetables, beans, lentils, fish, lean meats, yogurt, grains, herbs, spices, and shared routines.", x, y - 8, 468, 11, 14.5)
    y = bullet_list(c, [
        "Tacos: beans or grilled chicken, cabbage, salsa, avocado, and corn tortillas.",
        "Dal: lentils with vegetables, cucumber salad, and a smaller scoop of rice if needed.",
        "Stir-fry: tofu, chicken, shrimp, or beef with mixed vegetables and rice.",
        "Mediterranean plate: fish, salad, roasted vegetables, hummus, and pita.",
        "Caribbean-inspired plate: stewed chicken or fish, greens, beans, and plantain.",
        "Pasta night: pasta with vegetables, tomato sauce, beans or lean protein, and salad.",
    ], x, y - 4, 468)
    callout(c, "The portion and the pattern matter", "No single food has to carry the whole meal. A higher-carb food can often fit better when the rest of the plate supports it.", x, y - 12, 468, 78, "green")
    end_page(c, 12, "Dinners")

    # Page 13
    start_page(c, 13, "Snacks")
    x, y = 72, 672
    eyebrow(c, "Snacks", x, y)
    y = title(c, "Snacks are optional", x, y - 24, 468, 31)
    y = text_box(c, "Some people feel better with planned snacks. Others do not need them. Snacks may be useful if meals are far apart, activity changes your glucose, medication timing matters, or hunger makes the next meal harder to manage.", x, y - 8, 468, 11.2, 15)
    y = heading(c, "Protein plus fiber snack ideas", x, y - 14, 468, 18)
    y = bullet_list(c, [
        "Apple slices with peanut butter.",
        "Plain yogurt with berries.",
        "Hummus with carrots, cucumbers, or whole-grain crackers.",
        "A boiled egg with fruit.",
        "Edamame or roasted chickpeas.",
        "Nuts with a small piece of fruit.",
    ], x, y - 4, 468)
    callout(c, "Medication safety", "If you use insulin or medicines that can cause low blood sugar, ask your care team how snacks, activity, and low readings should be handled.", x, y - 12, 468, 82, "orange")
    end_page(c, 13, "Snacks")

    # Page 14
    start_page(c, 14, "Drinks")
    x, y = 72, 672
    eyebrow(c, "Drinks", x, y)
    y = title(c, "Drinks and hidden sugars", x, y - 24, 468, 30)
    c.drawImage(str(IMAGES / "drink-comparison-graphic-pdf.png"), 76, 365, width=460, height=246, mask="auto")
    y = 334
    y = text_box(c, "Sugary drinks can raise blood glucose quickly because they are easy to drink fast and do not bring much fiber or fullness. Soda, sweet tea, juice, energy drinks, sports drinks, and sweet coffee drinks can all add sugar quickly.", x, y, 468, 10.8, 14.2)
    y = text_box(c, "The FDA Daily Value for added sugars is 50 grams per day based on a 2,000-calorie diet. The Dietary Guidelines recommend limiting added sugars to less than 10 percent of daily calories. [4]", x, y - 8, 468, 10.8, 14.2)
    callout(c, "Try this", "Pick one drink you have often and make one change: smaller size, less syrup, unsweet tea, sparkling water, infused water, or water beside the drink.", x, y - 18, 468, 74, "green")
    end_page(c, 14, "Drinks")

    # Page 15
    start_page(c, 15, "Portions")
    x, y = 72, 672
    eyebrow(c, "Portions", x, y)
    y = title(c, "Portions without weighing everything", x, y - 24, 468, 29)
    y = text_box(c, "Portions do not need to be exact to be useful. The plate method gives a visual estimate. Labels give serving sizes. Cups, bowls, and hand-based estimates can help when measuring is not realistic.", x, y - 8, 468, 11.1, 14.8)
    y = heading(c, "Helpful rough estimates", x, y - 14, 468, 18)
    y = bullet_list(c, [
        "A fist can be a rough estimate for about one cup of some foods.",
        "A palm can be a rough estimate for a portion of cooked meat, poultry, fish, tofu, or tempeh.",
        "A thumb can be a rough estimate for a small amount of oil, nut butter, or dressing.",
        "A label serving size is not a personalized recommendation. It is the amount used for the numbers on the label. [3]",
    ], x, y - 4, 468)
    callout(c, "Keep it kind", "Portion awareness is a tool, not a judgment. If measuring food feels stressful or unsafe for you, ask for support from a clinician or dietitian.", x, y - 12, 468, 82, "orange")
    end_page(c, 15, "Portions")

    # Page 16
    start_page(c, 16, "Sample Menu")
    x, y = 72, 672
    eyebrow(c, "Sample menu", x, y)
    y = title(c, "Three days of flexible ideas", x, y - 24, 468, 30)
    meals = [
        ("Day 1", "Yogurt bowl | Bean and vegetable soup | Fish, greens, rice | Apple with peanut butter"),
        ("Day 2", "Eggs and toast | Turkey or hummus sandwich | Chicken or tofu stir-fry | Yogurt or nuts"),
        ("Day 3", "Oatmeal with seeds | Leftover bowl | Dal, salad, and rice | Carrots with hummus"),
    ]
    for day, text in meals:
        c.setFillColor(colors.white)
        c.setStrokeColor(hex_color("line"))
        c.roundRect(x, y - 92, 468, 82, 8, fill=1, stroke=1)
        c.setFillColor(hex_color("green"))
        c.setFont("Lato-Bold", 11)
        c.drawString(x + 14, y - 32, day)
        text_box(c, text, x + 80, y - 32, 370, 10.2, 13.5)
        y -= 98
    y = text_box(c, "These are examples, not a prescription. Your calorie, carbohydrate, protein, sodium, kidney, allergy, pregnancy, medication, and glucose needs may be different.", x, y - 4, 468, 10.8, 14.2, color="body")
    callout(c, "Vegetarian swap", "Use beans, lentils, tofu, tempeh, edamame, eggs, yogurt, nuts, and seeds in patterns that fit your food traditions and medical needs.", x, y - 14, 468, 70, "green")
    end_page(c, 16, "Sample Menu")

    # Page 17
    start_page(c, 17, "Worksheet")
    x, y = 72, 672
    eyebrow(c, "Printable worksheet", x, y)
    y = title(c, "Build your own meal", x, y - 24, 468, 30)
    c.drawImage(str(IMAGES / "build-a-meal-worksheet-pdf.png"), 70, 140, width=472, height=311, mask="auto")
    callout(c, "How to use it", "Choose one meal you already eat. Write down what you could add, reduce, swap, or prepare ahead. Keep the change small enough that you can actually try it.", 72, 540, 468, 82, "green")
    end_page(c, 17, "Worksheet")

    # Page 18
    start_page(c, 18, "Grocery Starter List")
    x, y = 72, 672
    eyebrow(c, "Shopping", x, y)
    y = title(c, "Grocery starter list", x, y - 24, 468, 30)
    cols = [
        ("Vegetables", "greens, carrots, peppers, broccoli, cabbage, frozen mixed vegetables"),
        ("Fruit", "berries, apples, oranges, bananas, peaches, frozen fruit"),
        ("Protein", "eggs, fish, chicken, tofu, yogurt, beans, lentils, tuna"),
        ("Carbs", "oats, brown rice, tortillas, potatoes, whole-grain bread, quinoa"),
        ("Fats", "olive or canola oil, nuts, seeds, avocado, nut butter"),
        ("Flavor", "garlic, herbs, spices, salsa, vinegar, lemon, low-sodium broth"),
    ]
    for i, (h, b) in enumerate(cols):
        col = i % 2
        row = i // 2
        xx = x + col * 242
        yy = y - row * 115
        c.setFillColor(colors.white)
        c.setStrokeColor(hex_color("line"))
        c.roundRect(xx, yy - 92, 222, 82, 8, fill=1, stroke=1)
        c.setFillColor(hex_color("green" if i % 2 == 0 else "coral"))
        c.setFont("Lato-Bold", 10)
        c.drawString(xx + 12, yy - 30, h)
        text_box(c, b, xx + 12, yy - 48, 198, 8.8, 11.5)
    callout(c, "Budget note", "Frozen, canned, dried, and store-brand foods can be practical. Rinse canned beans or vegetables when you want less sodium.", x, 210, 468, 74, "green")
    end_page(c, 18, "Grocery Starter List")

    # Page 19
    start_page(c, 19, "Common Questions")
    x, y = 72, 672
    eyebrow(c, "Questions and myths", x, y)
    y = title(c, "A few food questions people ask all the time", x, y - 24, 468, 27)
    qas = [
        ("Do I have to stop eating carbohydrates?", "No. Many people do better by choosing portions and pairings that fit their plan."),
        ("Is fruit too sugary?", "Whole fruit brings water, fiber, vitamins, and flavor. Portion and individual response still matter."),
        ("Is brown sugar healthier?", "Brown sugar is still added sugar. It may taste different, but it is not a blood sugar workaround."),
        ("Are potatoes forbidden?", "No. Think about portion, preparation, and the rest of the meal."),
        ("Do I have to buy expensive health foods?", "No. Beans, oats, frozen vegetables, eggs, canned fish, and plain yogurt can be useful basics."),
        ("Can I keep culturally important foods?", "Yes. The goal is to adapt patterns, not erase identity."),
    ]
    for q, a in qas:
        c.setFillColor(hex_color("navy"))
        c.setFont("Lato-Bold", 9.7)
        c.drawString(x, y, q)
        y = text_box(c, a, x, y - 16, 468, 9.6, 12.5)
        y -= 9
    end_page(c, 19, "Common Questions")

    # Page 20
    start_page(c, 20, "Next Steps")
    x, y = 72, 672
    eyebrow(c, "Next steps", x, y)
    y = title(c, "Keep the guide useful", x, y - 24, 468, 30)
    y = text_box(c, "Pick one page to use this week. You might build one balanced dinner, improve one drink, or complete the meal worksheet. If you track glucose, compare changes only in the way your care team recommends.", x, y - 8, 468, 10.5, 13.8)
    y = heading(c, "Mindful Diabetes resources", x, y - 10, 468, 17)
    links = [
        ("Explore the Guide", "https://mindfuldiabetes.org/guide/"),
        ("Visit Health Tools", "https://mindfuldiabetes.org/health-tools/"),
        ("Try JEIR", "https://www.mindfuldiabetes.ai/"),
        ("Support free health education", "https://mindfuldiabetes.org/donation/"),
    ]
    for label, url in links:
        c.setFillColor(hex_color("soft_green"))
        c.setStrokeColor(hex_color("green"))
        c.roundRect(x, y - 25, 220, 27, 12, fill=1, stroke=1)
        c.setFillColor(hex_color("green"))
        c.setFont("Lato-Bold", 9)
        c.drawCentredString(x + 110, y - 15, label)
        c.linkURL(url, (x, y - 25, x + 220, y + 2), relative=0)
        y -= 36
    y = heading(c, "Medical disclaimer", x + 248, 388, 220, 15)
    text_box(c, "This guide is for general education only. It is not medical advice, diagnosis, or treatment. Individual nutrition needs vary. Do not change medication, insulin, or glucose targets based on this guide. Seek appropriate medical attention for severe low blood sugar, severe high blood sugar, sudden confusion, chest pain, trouble breathing, fainting, seizures, or other urgent symptoms.", x + 248, y + 104, 220, 8.3, 10.5)
    c.setFillColor(hex_color("navy"))
    c.setFont("Lora-Bold", 14)
    c.drawString(x, 224, "References")
    yy = 204
    for ref in REFS:
        line = f"[{ref.n}] {ref.label}. {ref.source}. {ref.year}."
        yy = text_box(c, line, x, yy, 468, 7.4, 9.1, font="Lato", color="body")
        c.linkURL(ref.url, (x, yy + 2, x + 468, yy + 13), relative=0)
        yy -= 1
    c.setFillColor(hex_color("muted"))
    c.setFont("Lato", 7.7)
    c.drawString(x, 66, "Published: July 30, 2026 | Last medically reviewed: pending | Next scheduled review: July 2027")
    end_page(c, 20, "Next Steps")


def write_manifests(assets: list[dict[str, str]]) -> None:
    image_rows = []
    for asset in assets:
        image_rows.append({
            "file_name": asset["file"],
            "visual_title": asset["title"],
            "source_or_method": "Original vector-style illustration generated locally with Python/Pillow for Mindful Diabetes.",
            "license": "Created for this project; no third-party image content.",
            "attribution_required": "No",
            "pdf_page": "",
            "alt_text": asset["alt"],
            "caption": asset["title"],
            "editing_performed": "Created at production size and placed into PDF layout.",
        })
    with (RESEARCH / "image-license-manifest.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=image_rows[0].keys())
        writer.writeheader()
        writer.writerows(image_rows)

    claims = [
        ["Carbohydrate foods commonly have the most direct effect on blood glucose.", "ADA Standards of Care 2026", "2026", "The Mindful Plate p4", "Direct/inferred from nutrition therapy guidance"],
        ["The diabetes plate pattern uses non-starchy vegetables, protein, carbohydrate, and a low-calorie drink.", "ADA Diabetes Food Hub, What is the Diabetes Plate?", "2026", "The Mindful Plate p5", "Direct"],
        ["Percent Daily Value can help identify whether a nutrient is high or low; 5% low and 20% high.", "FDA Nutrition Facts Label", "2024", "The Mindful Plate p15/references", "Direct"],
        ["FDA Daily Value for dietary fiber is 28 g based on 2,000 calories.", "FDA Nutrition Facts Label", "2024", "The Mindful Plate p8", "Direct"],
        ["Daily Value for added sugars is 50 g based on 2,000 calories; Dietary Guidelines recommend less than 10% calories from added sugars.", "FDA Added Sugars", "2026", "The Mindful Plate p14", "Direct"],
        ["Lifestyle changes can help prevent or delay type 2 diabetes for people at high risk, but are not guarantees.", "CDC National DPP", "2024", "The Mindful Plate safety framing", "Direct with cautious wording"],
        ["Both high and low blood sugar can affect the brain and require individualized targets.", "CDC Your Brain and Diabetes", "2024", "The Mindful Plate p4/p20", "Direct with cautious wording"],
        ["AHA recommends emphasizing unsaturated fats in place of saturated and trans fats.", "AHA Fats in Foods", "2026", "The Mindful Plate p9", "Direct"],
    ]
    with (RESEARCH / "claim-manifest.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["claim", "supporting_source", "source_date", "where_used", "review_note"])
        writer.writerows(claims)

    with (RESEARCH / "references.json").open("w") as f:
        json.dump([ref.__dict__ for ref in REFS], f, indent=2)

    source_text = {
        "title": "The Mindful Plate",
        "subtitle": "A Simple Guide to Blood Sugar-Friendly Eating",
        "version": "2026.1",
        "published": "July 30, 2026",
        "medical_review": "Pending",
        "source_note": "Editable production source is the Python layout file plus generated image assets and research manifests.",
    }
    with (SOURCE / "mindful-plate-source.json").open("w") as f:
        json.dump(source_text, f, indent=2)

    with (ACCESS / "accessibility-review-notes.md").open("w") as f:
        f.write(
            "# Accessibility Review Notes\n\n"
            "- Text in the PDF is selectable.\n"
            "- Major sections are represented with PDF bookmarks.\n"
            "- Links are embedded and descriptive.\n"
            "- Meaningful image alt text is documented in `Research/image-license-manifest.csv`.\n"
            "- Color is paired with labels, not used alone for essential meaning.\n"
            "- Full PDF/UA tagging should be completed in Acrobat, LibreOffice, or a dedicated remediation tool before clinical/community distribution.\n"
        )

    with (WEBSITE / "mindful-plate-website-metadata.json").open("w") as f:
        json.dump({
            "title": "The Mindful Plate",
            "short_description": "A friendly guide to building blood sugar-conscious meals with vegetables, protein, carbohydrates, drinks, portions, and flexible real-life examples.",
            "long_description": "The Mindful Plate helps readers understand how food affects blood sugar without turning meals into a math problem. It explains carbohydrates, protein, fiber, fats, drinks, portions, sample menus, and culturally flexible meal ideas in plain language, with printable tools for planning one useful meal at a time.",
            "who_this_is_for": "For adults with type 2 diabetes, prediabetes, family history, caregivers, or anyone who wants clearer meal guidance.",
            "tags": ["Nutrition", "Blood sugar", "Meal planning"],
            "button_text": "Download the Free Guide",
            "seo_title": "The Mindful Plate Free PDF Guide | Mindful Diabetes",
            "meta_description": "Download a free Mindful Diabetes guide to building balanced, blood sugar-friendly meals with practical examples, diagrams, and worksheets.",
            "pdf_file_name": "mindful-diabetes-mindful-plate-guide-2026.pdf",
            "thumbnail_file_name": "mindful-plate-download-card-thumbnail.png",
            "slug": "mindful-plate",
            "alt_text": "Cover of The Mindful Plate free guide showing a balanced meal illustration.",
        }, f, indent=2)


def build_pdf() -> None:
    c = canvas.Canvas(str(PRINT_PDF), pagesize=letter, pageCompression=1)
    c.setTitle("The Mindful Plate: A Simple Guide to Blood Sugar-Friendly Eating")
    c.setAuthor("Mindful Diabetes Inc.")
    c.setSubject("Free guide to blood sugar-friendly eating")
    c.setKeywords("Mindful Diabetes, diabetes, prediabetes, nutrition, plate method, blood sugar, meal planning")
    draw_cover(c)
    content_pages(c)
    c.save()

    # Add bookmarks and compress streams for web version.
    reader = PdfReader(str(PRINT_PDF))
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
        writer.pages[-1].compress_content_streams()
    writer.add_metadata({
        "/Title": "The Mindful Plate: A Simple Guide to Blood Sugar-Friendly Eating",
        "/Author": "Mindful Diabetes Inc.",
        "/Subject": "Free guide to blood sugar-friendly eating",
        "/Keywords": "Mindful Diabetes, diabetes, prediabetes, nutrition, plate method, blood sugar, meal planning",
    })
    bookmarks = [
        ("Cover", 0),
        ("Welcome", 1),
        ("Quick Start", 2),
        ("Food and Blood Sugar", 3),
        ("The Mindful Plate Method", 4),
        ("Carbohydrates, Protein, Fiber, and Fat", 5),
        ("Meal Examples", 9),
        ("Worksheet", 16),
        ("References and Disclaimer", 19),
    ]
    for label, page_number in bookmarks:
        writer.add_outline_item(label, page_number)
    with WEB_PDF.open("wb") as f:
        writer.write(f)


def main() -> None:
    ensure_dirs()
    register_fonts()
    assets = generate_visual_assets()
    generate_website_assets()
    build_pdf()
    write_manifests(assets)
    print(f"created {PRINT_PDF}")
    print(f"created {WEB_PDF}")


if __name__ == "__main__":
    main()
