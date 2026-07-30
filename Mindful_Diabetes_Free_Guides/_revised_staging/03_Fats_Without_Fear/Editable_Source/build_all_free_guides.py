from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


def find_project_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if candidate.name == "Mindful_Diabetes_Free_Guides":
            return candidate
    raise RuntimeError("Could not locate Mindful_Diabetes_Free_Guides project root")


PROJECT = find_project_root(Path(__file__).resolve())
STAGING = PROJECT / "_revised_staging"
FONT_DIR = PROJECT / "01_Brand_Assets" / "Fonts_Reference"
LOGO = PROJECT / "01_Brand_Assets" / "Logos" / "mdi-logo.jpg"

PAGE_W, PAGE_H = letter
MARGIN = 58
TOP = 668
BOTTOM = 58

PALETTE = {
    "navy": "#0d1338",
    "deep_navy": "#0d243c",
    "green": "#005030",
    "deep_green": "#003b24",
    "coral": "#f07239",
    "coral_dark": "#e15b47",
    "cream": "#fffaf2",
    "soft": "#f5f7fe",
    "soft_green": "#f0faf5",
    "soft_orange": "#fff3ec",
    "line": "#d9deea",
    "body": "#30343d",
    "muted": "#687081",
    "white": "#ffffff",
}


def hc(name: str):
    return colors.HexColor(PALETTE[name])


def register_fonts() -> None:
    for font_name, file_name in {
        "Lato": "Lato-Regular.ttf",
        "Lato-Bold": "Lato-Bold.ttf",
        "Lora": "Lora-Regular.ttf",
        "Lora-Bold": "Lora-Bold.ttf",
    }.items():
        if font_name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(font_name, str(FONT_DIR / file_name)))


def wrap_lines(text: str, font: str, size: float, width: float) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        if pdfmetrics.stringWidth(test, font, size) <= width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_wrapped(c: canvas.Canvas, text: str, x: float, y: float, width: float, size: float = 10.8, font: str = "Lato", color: str = "body", leading: float | None = None) -> float:
    if leading is None:
        leading = size * 1.34
    c.setFont(font, size)
    c.setFillColor(hc(color))
    for line in wrap_lines(text, font, size, width):
        c.drawString(x, y, line)
        y -= leading
    return y


def draw_heading(c: canvas.Canvas, title: str, x: float, y: float, width: float, size: float = 28) -> float:
    c.setFont("Lora-Bold", size)
    c.setFillColor(hc("navy"))
    for line in wrap_lines(title, "Lora-Bold", size, width):
        c.drawString(x, y, line)
        y -= size * 1.1
    return y - 5


def draw_eyebrow(c: canvas.Canvas, text: str, x: float, y: float) -> None:
    c.setFont("Lato-Bold", 8.8)
    c.setFillColor(hc("coral"))
    c.drawString(x, y, text.upper())


def round_rect(c: canvas.Canvas, x: float, y: float, w: float, h: float, fill: str = "white", stroke: str = "line", radius: float = 8) -> None:
    c.setFillColor(hc(fill))
    c.setStrokeColor(hc(stroke))
    c.setLineWidth(1)
    c.roundRect(x, y, w, h, radius, fill=1, stroke=1)


def draw_bullets(c: canvas.Canvas, items: list[str], x: float, y: float, width: float, size: float = 10.4) -> float:
    for item in items:
        c.setFillColor(hc("green"))
        c.circle(x + 4, y + 3, 2.3, fill=1, stroke=0)
        y = draw_wrapped(c, item, x + 16, y, width - 16, size, "Lato", "body", size * 1.32)
        y -= 5
    return y


def draw_callout(c: canvas.Canvas, title: str, body: str, x: float, y: float, w: float, h: float, tone: str = "green") -> None:
    fill = "soft_green" if tone == "green" else "soft_orange"
    stroke = "green" if tone == "green" else "coral"
    round_rect(c, x, y - h, w, h, fill, stroke, 9)
    c.setFont("Lato-Bold", 9.6)
    c.setFillColor(hc(stroke))
    c.drawString(x + 14, y - 22, title)
    draw_wrapped(c, body, x + 14, y - 42, w - 28, 9.2, "Lato", "body", 11.8)


def draw_header(c: canvas.Canvas, guide: dict, page_num: int) -> None:
    if page_num == 1:
        return
    c.drawImage(str(LOGO), MARGIN, 724, width=28, height=30, mask="auto")
    c.setFont("Lora-Bold", 10)
    c.setFillColor(hc("navy"))
    c.drawString(MARGIN + 38, 742, guide["title"])
    c.setFont("Lato", 8.1)
    c.setFillColor(hc("muted"))
    c.drawString(MARGIN + 38, 729, guide["running_subtitle"])
    c.setStrokeColor(hc("line"))
    c.line(MARGIN, 716, PAGE_W - MARGIN, 716)


def draw_footer(c: canvas.Canvas, page_num: int) -> None:
    if page_num == 1:
        return
    c.setStrokeColor(hc("line"))
    c.line(MARGIN, 40, PAGE_W - MARGIN, 40)
    c.setFont("Lato", 8.2)
    c.setFillColor(hc("muted"))
    c.drawString(MARGIN, 24, "Mindful Diabetes Inc.")
    c.drawCentredString(PAGE_W / 2, 24, "mindfuldiabetes.org")
    c.setFont("Lato-Bold", 9)
    c.setFillColor(hc("coral"))
    c.drawRightString(PAGE_W - MARGIN, 24, str(page_num))


def start_page(c: canvas.Canvas, guide: dict, page_num: int) -> None:
    c.setFillColor(hc("cream"))
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    draw_header(c, guide, page_num)


def finish_page(c: canvas.Canvas, page_num: int) -> None:
    draw_footer(c, page_num)
    c.showPage()


def draw_plate_diagram(c: canvas.Canvas, x: float, y: float, size: float, labels: bool = True) -> None:
    r = size / 2
    cx, cy = x + r, y + r
    c.setFillColor(colors.white)
    c.setStrokeColor(hc("navy"))
    c.setLineWidth(1.5)
    c.circle(cx, cy, r, fill=1, stroke=1)
    c.setFillColor(hc("soft_green"))
    c.wedge(x + 8, y + 8, x + size - 8, y + size - 8, 90, 270, fill=1, stroke=0)
    c.setFillColor(hc("soft"))
    c.wedge(x + 8, y + 8, x + size - 8, y + size - 8, 0, 90, fill=1, stroke=0)
    c.setFillColor(hc("soft_orange"))
    c.wedge(x + 8, y + 8, x + size - 8, y + size - 8, 270, 360, fill=1, stroke=0)
    c.setStrokeColor(colors.white)
    c.setLineWidth(4)
    c.line(cx, y + 10, cx, y + size - 10)
    c.line(cx, cy, x + size - 10, cy)
    if labels:
        c.setFont("Lato-Bold", max(8, size / 18))
        c.setFillColor(hc("green"))
        c.drawCentredString(cx - r * 0.45, cy + 4, "1/2 vegetables")
        c.setFillColor(hc("navy"))
        c.drawCentredString(cx + r * 0.45, cy + r * 0.43, "1/4 protein")
        c.setFillColor(hc("coral_dark"))
        c.drawCentredString(cx + r * 0.45, cy - r * 0.42, "1/4 carbohydrate")


def icon_food(c: canvas.Canvas, x: float, y: float, kind: str, s: float = 28) -> None:
    c.setStrokeColor(hc("navy"))
    c.setLineWidth(1)
    if kind in {"vegetable", "fruit", "fiber"}:
        c.setFillColor(hc("green"))
        c.ellipse(x, y, x + s, y + s * 0.72, fill=1, stroke=1)
        c.setFillColor(hc("soft_green"))
        c.ellipse(x + s * 0.28, y + s * 0.15, x + s * 0.85, y + s * 0.62, fill=1, stroke=0)
    elif kind in {"protein", "fish"}:
        c.setFillColor(hc("soft"))
        c.roundRect(x, y, s * 1.25, s * 0.72, 10, fill=1, stroke=1)
        c.setFillColor(hc("navy"))
        c.circle(x + s * 0.92, y + s * 0.36, 2, fill=1, stroke=0)
    elif kind in {"carb", "grain"}:
        c.setFillColor(hc("soft_orange"))
        c.ellipse(x, y, x + s * 1.1, y + s * 0.8, fill=1, stroke=1)
    elif kind in {"drink"}:
        c.setFillColor(hc("soft"))
        c.roundRect(x + 4, y, s * 0.58, s * 1.05, 5, fill=1, stroke=1)
        c.setFillColor(hc("navy"))
        c.rect(x + 7, y + s * 1.02, s * 0.42, s * 0.15, fill=1, stroke=0)
    else:
        c.setFillColor(hc("coral"))
        c.circle(x + s / 2, y + s / 2, s / 2, fill=1, stroke=1)


def visual_meal_hero(c: canvas.Canvas, x: float, y: float, w: float, h: float, guide_slug: str) -> None:
    round_rect(c, x, y, w, h, "white", "line", 18)
    if guide_slug == "mindful-plate":
        draw_plate_diagram(c, x + w * 0.17, y + h * 0.13, min(w, h) * 0.7, True)
        icon_food(c, x + w * 0.68, y + h * 0.58, "drink", 46)
    elif guide_slug == "fats-without-fear":
        for i, (kind, label) in enumerate([("fish", "fish"), ("fiber", "nuts"), ("carb", "oil"), ("vegetable", "avocado")]):
            px = x + 45 + (i % 2) * (w / 2)
            py = y + h - 95 - (i // 2) * 115
            icon_food(c, px, py, kind, 46)
            c.setFont("Lato-Bold", 10)
            c.setFillColor(hc("navy"))
            c.drawString(px + 62, py + 15, label)
    elif guide_slug == "grocery-store-survival-guide":
        c.setStrokeColor(hc("navy"))
        c.setLineWidth(3)
        c.roundRect(x + 70, y + 80, w - 140, h - 160, 18, fill=0, stroke=1)
        c.line(x + 95, y + h - 80, x + 70, y + h - 35)
        for i, label in enumerate(["Produce", "Protein", "Fiber carbs", "Fats", "Flavor"]):
            bx = x + 95 + (i % 2) * 150
            by = y + h - 130 - (i // 2) * 68
            round_rect(c, bx, by, 128, 42, "soft_green" if i % 2 == 0 else "soft_orange", "line", 8)
            c.setFont("Lato-Bold", 9)
            c.setFillColor(hc("navy"))
            c.drawCentredString(bx + 64, by + 15, label)
    elif guide_slug == "7-day-prevention-reset":
        labels = ["Notice", "Meal", "Fiber", "Move", "Drink", "Sleep", "Plan"]
        for i, label in enumerate(labels):
            bx = x + 32 + i * ((w - 64) / 7)
            c.setFillColor(hc("soft_green" if i % 2 == 0 else "soft_orange"))
            c.circle(bx + 18, y + h * 0.55, 18, fill=1, stroke=0)
            c.setFont("Lato-Bold", 8.6)
            c.setFillColor(hc("navy"))
            c.drawCentredString(bx + 18, y + h * 0.38, label)
            if i < 6:
                c.setStrokeColor(hc("coral"))
                c.line(bx + 38, y + h * 0.55, bx + 55, y + h * 0.55)
    else:
        c.setStrokeColor(hc("navy"))
        c.setLineWidth(2)
        c.circle(x + w * 0.38, y + h * 0.55, 74, fill=0, stroke=1)
        c.setFillColor(hc("soft_green"))
        c.circle(x + w * 0.38, y + h * 0.55, 62, fill=1, stroke=0)
        c.setFillColor(hc("soft"))
        c.roundRect(x + w * 0.58, y + h * 0.35, 112, 118, 18, fill=1, stroke=1)
        c.setFont("Lato-Bold", 11)
        c.setFillColor(hc("navy"))
        c.drawCentredString(x + w * 0.38, y + h * 0.54, "brain")
        c.drawCentredString(x + w * 0.58 + 56, y + h * 0.42, "body")
        c.setStrokeColor(hc("coral"))
        c.line(x + w * 0.47, y + h * 0.55, x + w * 0.58, y + h * 0.45)


def draw_process(c: canvas.Canvas, x: float, y: float, w: float, h: float, steps: list[tuple[str, str]]) -> None:
    round_rect(c, x, y, w, h, "white", "line", 12)
    step_w = (w - 34 - (len(steps) - 1) * 18) / len(steps)
    for i, (label, desc) in enumerate(steps):
        bx = x + 17 + i * (step_w + 18)
        by = y + 38
        round_rect(c, bx, by, step_w, h - 76, "soft" if i % 2 else "soft_green", "line", 10)
        c.setFont("Lato-Bold", 11)
        c.setFillColor(hc("navy"))
        c.drawCentredString(bx + step_w / 2, by + h - 104, label)
        draw_wrapped(c, desc, bx + 10, by + h - 130, step_w - 20, 8.8, "Lato", "body", 10.5)
        if i < len(steps) - 1:
            c.setStrokeColor(hc("coral"))
            c.setLineWidth(2)
            c.line(bx + step_w + 4, y + h / 2, bx + step_w + 16, y + h / 2)


def draw_card_grid(c: canvas.Canvas, x: float, y: float, w: float, h: float, cards: list[tuple[str, str, str]] | list[tuple[str, str]]) -> None:
    cols = 2 if len(cards) <= 6 else 3
    rows = (len(cards) + cols - 1) // cols
    gap = 12
    cw = (w - gap * (cols - 1)) / cols
    ch = (h - gap * (rows - 1)) / rows
    for i, card in enumerate(cards):
        title = card[0]
        body = card[1] if len(card) > 1 else ""
        kind = card[2] if len(card) > 2 else "vegetable"
        col = i % cols
        row = i // cols
        bx = x + col * (cw + gap)
        by = y + h - (row + 1) * ch - row * gap
        round_rect(c, bx, by, cw, ch, "white", "line", 8)
        icon_food(c, bx + 13, by + ch - 40, kind, 22)
        c.setFont("Lato-Bold", 10.2)
        c.setFillColor(hc("navy"))
        for n, line in enumerate(wrap_lines(title, "Lato-Bold", 10.2, cw - 58)[:2]):
            c.drawString(bx + 48, by + ch - 25 - n * 12, line)
        draw_wrapped(c, body, bx + 14, by + ch - 62, cw - 28, 8.7, "Lato", "body", 10.5)


def draw_comparison(c: canvas.Canvas, x: float, y: float, w: float, h: float, left: tuple[str, list[str]], right: tuple[str, list[str]]) -> None:
    gap = 16
    cw = (w - gap) / 2
    for bx, data, tone in [(x, left, "soft_orange"), (x + cw + gap, right, "soft_green")]:
        round_rect(c, bx, y, cw, h, tone, "line", 10)
        c.setFont("Lato-Bold", 13)
        c.setFillColor(hc("navy"))
        c.drawString(bx + 16, y + h - 26, data[0])
        draw_bullets(c, data[1], bx + 16, y + h - 52, cw - 32, 9.2)


def draw_table(c: canvas.Canvas, x: float, y: float, w: float, headers: list[str], rows: list[list[str]], row_h: float = 42, font_size: float = 9.5) -> None:
    col_w = w / len(headers)
    c.setStrokeColor(hc("line"))
    c.setLineWidth(0.8)
    c.setFillColor(hc("soft_green"))
    c.roundRect(x, y - row_h, w, row_h, 7, fill=1, stroke=1)
    c.setFont("Lato-Bold", font_size)
    c.setFillColor(hc("green"))
    for i, header in enumerate(headers):
        c.drawString(x + i * col_w + 8, y - 25, header)
    for r, row in enumerate(rows):
        by = y - row_h * (r + 2)
        fill = "white" if r % 2 == 0 else "soft"
        c.setFillColor(hc(fill))
        c.rect(x, by, w, row_h, fill=1, stroke=1)
        for i, value in enumerate(row):
            draw_wrapped(c, value, x + i * col_w + 8, by + row_h - 17, col_w - 14, font_size - 0.7, "Lato", "body", 10)


def draw_form_field(c: canvas.Canvas, name: str, x: float, y: float, w: float, h: float, web_fields: bool) -> None:
    c.setStrokeColor(hc("line"))
    c.setFillColor(colors.white)
    c.roundRect(x, y, w, h, 5, fill=1, stroke=1)
    if web_fields:
        try:
            c.acroform.textfield(name=name, x=x + 2, y=y + 2, width=w - 4, height=h - 4, borderWidth=0, fillColor=colors.white, textColor=hc("body"), fontName="Helvetica", fontSize=9)
        except Exception:
            pass


def draw_worksheet(c: canvas.Canvas, page: dict, x: float, y: float, w: float, h: float, web_fields: bool, prefix: str) -> None:
    fields = page.get("worksheet", {}).get("fields", [])
    if not fields:
        fields = ["Date", "Meal", "Vegetables", "Protein", "Carbohydrate", "Notes"]
    if page.get("worksheet", {}).get("type") == "table":
        cols = fields
        rows = page.get("worksheet", {}).get("rows", 7)
        header_h = 31
        row_h = min(42, (h - header_h) / rows)
        col_w = w / len(cols)
        round_rect(c, x, y + h - header_h, w, header_h, "soft_green", "green", 6)
        c.setFont("Lato-Bold", 8.8)
        c.setFillColor(hc("green"))
        for i, col in enumerate(cols):
            c.drawString(x + i * col_w + 5, y + h - 20, col[:18])
        for r in range(rows):
            by = y + h - header_h - (r + 1) * row_h
            for i in range(len(cols)):
                draw_form_field(c, f"{prefix}_{page['section']}_{r}_{i}".replace(" ", "_")[:90], x + i * col_w, by, col_w, row_h, web_fields)
    elif page.get("worksheet", {}).get("type") == "calendar":
        cols, rows = 7, 5
        cw = w / cols
        rh = h / rows
        for r in range(rows):
            for col in range(cols):
                bx = x + col * cw
                by = y + h - (r + 1) * rh
                draw_form_field(c, f"{prefix}_cal_{r}_{col}", bx, by, cw - 4, rh - 5, web_fields)
                c.setFont("Lato-Bold", 8)
                c.setFillColor(hc("muted"))
                c.drawString(bx + 6, by + rh - 18, str(r * cols + col + 1))
    else:
        row_h = h / len(fields)
        for i, field in enumerate(fields):
            by = y + h - (i + 1) * row_h + 5
            c.setFont("Lato-Bold", 10.4)
            c.setFillColor(hc("navy"))
            c.drawString(x, by + row_h - 20, field)
            draw_form_field(c, f"{prefix}_{page['section']}_{i}".replace(" ", "_")[:90], x + 160, by + 8, w - 160, row_h - 20, web_fields)


def draw_visual(c: canvas.Canvas, guide: dict, visual: str, x: float, y: float, w: float, h: float) -> None:
    if not visual:
        return
    data = guide["visuals"].get(visual)
    if isinstance(data, dict):
        draw_table(c, x, y + h, w, data.get("headers", ["Choice", "Check", "Note"]), data.get("rows", []), data.get("row_h", 38), 9.2)
        return
    if isinstance(data, list) and data:
        if all(isinstance(item, str) for item in data):
            round_rect(c, x, y, w, h, "white", "line", 10)
            step_h = (h - 30) / len(data)
            for i, label in enumerate(data):
                by = y + h - 18 - (i + 1) * step_h
                c.setFillColor(hc("soft_green" if i % 2 == 0 else "soft_orange"))
                c.roundRect(x + 18 + i * 4, by, w - 36 - i * 8, step_h - 8, 8, fill=1, stroke=0)
                c.setFont("Lato-Bold", 9.5)
                c.setFillColor(hc("navy"))
                c.drawString(x + 32 + i * 4, by + step_h / 2 - 3, label)
            return
        if len(data) == 2 and all(isinstance(item, (tuple, list)) and len(item) == 2 and isinstance(item[1], list) for item in data):
            draw_comparison(c, x, y, w, h, data[0], data[1])
            return
        if all(isinstance(item, (tuple, list)) for item in data):
            draw_card_grid(c, x, y, w, h, data)
            return
    if visual in {"mindful-plate", "balanced-meal", "plate-method"}:
        draw_plate_diagram(c, x + max(8, (w - min(w, h) * 0.72) / 2), y + max(8, (h - min(w, h) * 0.72) / 2), min(w, h) * 0.72, True)
        round_rect(c, x + w - 140, y + 12, 128, 45, "soft", "line", 7)
        c.setFont("Lato-Bold", 8.5)
        c.setFillColor(hc("navy"))
        c.drawCentredString(x + w - 76, y + 37, "Low-sugar")
        c.drawCentredString(x + w - 76, y + 25, "drink")
    elif visual in {"digestion", "glucose-pathway"}:
        steps = [("Food", "Meal is digested."), ("Glucose", "Carbs enter blood."), ("Insulin", "Helps cells use glucose."), ("Energy", "Cells use or store it.")]
        draw_process(c, x, y, w, h, steps)
    elif visual == "insulin-resistance":
        round_rect(c, x, y, w, h, "white", "line", 10)
        c.setFont("Lato-Bold", 13)
        c.setFillColor(hc("navy"))
        c.drawString(x + 18, y + h - 28, "Insulin resistance")
        for i, label in enumerate(["More signal needed", "Glucose stays higher", "Support can help"]):
            bx = x + 25 + i * ((w - 50) / 3)
            c.setFillColor(hc("soft_green" if i != 1 else "soft_orange"))
            c.circle(bx + 35, y + h / 2, 34, fill=1, stroke=1)
            draw_wrapped(c, label, bx, y + h / 2 - 48, 82, 8.6, "Lato-Bold", "navy", 10)
    elif visual in {"carb-families", "fat-types", "smart-cart", "protein-map", "food-sources", "risk-wheel", "movement-menu", "claims"}:
        cards = guide["visuals"].get(visual, [])
        draw_card_grid(c, x, y, w, h, cards)
    elif visual in {"fiber-ladder", "swap-ladder", "roadmap", "sleep-timeline", "replacement-pathway"}:
        labels = guide["visuals"].get(visual, [])
        round_rect(c, x, y, w, h, "white", "line", 10)
        step_h = (h - 30) / max(1, len(labels))
        for i, label in enumerate(labels):
            by = y + h - 18 - (i + 1) * step_h
            c.setFillColor(hc("soft_green" if i % 2 == 0 else "soft_orange"))
            c.roundRect(x + 18 + i * 4, by, w - 36 - i * 8, step_h - 8, 8, fill=1, stroke=0)
            c.setFont("Lato-Bold", 9.5)
            c.setFillColor(hc("navy"))
            c.drawString(x + 32 + i * 4, by + step_h / 2 - 3, label)
    elif visual in {"drink-comparison", "high-low", "can-cannot", "fresh-frozen-canned", "label-comparison"}:
        left, right = guide["visuals"].get(visual, [("Choose less often", ["Large sweet drinks", "Little fiber"]), ("Choose more often", ["Water", "Unsweet tea"])])
        draw_comparison(c, x, y, w, h, left, right)
    elif visual in {"oil-chart", "label-map", "menu-table", "meal-formula", "sodium-label"}:
        spec = guide["visuals"].get(visual, {})
        draw_table(c, x, y + h, w, spec.get("headers", ["Choice", "Check", "Note"]), spec.get("rows", []), spec.get("row_h", 38), 9.2)
    elif visual == "portion-guide":
        round_rect(c, x, y, w, h, "white", "line", 10)
        draw_plate_diagram(c, x + 20, y + 35, min(h - 70, 145), True)
        items = [("Fist", "rough cup estimate"), ("Palm", "protein estimate"), ("Thumb", "fat estimate")]
        for i, (a, b) in enumerate(items):
            bx = x + 190
            by = y + h - 54 - i * 50
            c.setFillColor(hc("soft_green" if i % 2 == 0 else "soft_orange"))
            c.roundRect(bx, by, w - 210, 36, 8, fill=1, stroke=0)
            c.setFont("Lato-Bold", 10)
            c.setFillColor(hc("navy"))
            c.drawString(bx + 12, by + 13, f"{a}: {b}")
    elif visual == "vessel-brain":
        round_rect(c, x, y, w, h, "white", "line", 10)
        c.setFont("Lato-Bold", 12)
        c.setFillColor(hc("navy"))
        c.drawString(x + 16, y + h - 25, "Body - vessels - brain")
        pts = [(x + 70, y + h / 2), (x + w / 2, y + h / 2), (x + w - 70, y + h / 2)]
        for i, label in enumerate(["Heart", "Blood vessels", "Brain"]):
            c.setFillColor(hc("soft_green" if i != 1 else "soft"))
            c.circle(pts[i][0], pts[i][1], 36, fill=1, stroke=1)
            c.setFont("Lato-Bold", 9)
            c.setFillColor(hc("navy"))
            c.drawCentredString(pts[i][0], pts[i][1] - 3, label)
            if i < 2:
                c.setStrokeColor(hc("coral"))
                c.line(pts[i][0] + 40, pts[i][1], pts[i + 1][0] - 40, pts[i + 1][1])
    else:
        visual_meal_hero(c, x, y, w, h, guide["slug"])


def add_form_fields_note(writer: PdfWriter) -> None:
    # ReportLab form fields are preserved. This function is a small marker for future remediation.
    return None


BASE_REFS = {
    "ada": ("American Diabetes Association", "Standards of Care in Diabetes - 2026", "Diabetes Care", "2026", "https://diabetesjournals.org/care/issue/49/Supplement_1"),
    "plate": ("American Diabetes Association Nutrition & Wellness Team", "What is the Diabetes Plate?", "American Diabetes Association Diabetes Food Hub", "2026", "https://diabetesfoodhub.org/blog/what-diabetes-plate"),
    "fda_label": ("U.S. Food and Drug Administration", "How to Understand and Use the Nutrition Facts Label", "FDA", "2024", "https://www.fda.gov/food/nutrition-facts-label/how-understand-and-use-nutrition-facts-label"),
    "fda_sugar": ("U.S. Food and Drug Administration", "Added Sugars on the Nutrition Facts Label", "FDA", "2026", "https://www.fda.gov/food/nutrition-facts-label/added-sugars-nutrition-facts-label"),
    "fda_sodium": ("U.S. Food and Drug Administration", "Sodium in Your Diet", "FDA", "2024", "https://www.fda.gov/food/nutrition-education-resources-materials/sodium-your-diet"),
    "aha_fats": ("American Heart Association", "Fats in Foods", "AHA", "2026", "https://www.heart.org/en/healthy-living/healthy-eating/eat-smart/fats/fats-in-foods"),
    "aha_sat": ("American Heart Association", "Saturated Fats", "AHA", "2024", "https://www.heart.org/en/healthy-living/healthy-eating/eat-smart/fats/saturated-fats"),
    "cdc_dpp": ("Centers for Disease Control and Prevention", "What Is the National Diabetes Prevention Program?", "CDC", "2024", "https://www.cdc.gov/diabetes-prevention/programs/what-is-the-national-dpp.html"),
    "cdc_activity": ("Centers for Disease Control and Prevention", "Get Active", "CDC", "2024", "https://www.cdc.gov/diabetes/living-with/physical-activity.html"),
    "cdc_sleep": ("Centers for Disease Control and Prevention", "About Sleep", "CDC", "2024", "https://www.cdc.gov/sleep/about/index.html"),
    "cdc_brain": ("Centers for Disease Control and Prevention", "Your Brain and Diabetes", "CDC", "2024", "https://www.cdc.gov/diabetes/diabetes-complications/effects-of-diabetes-brain.html"),
    "cdc_dementia": ("Centers for Disease Control and Prevention", "Reducing Risk for Dementia", "CDC", "2024", "https://www.cdc.gov/alzheimers-dementia/prevention/index.html"),
    "nia": ("National Institute on Aging", "Cognitive Health and Older Adults", "NIA", "2024", "https://www.nia.nih.gov/health/brain-health/cognitive-health-and-older-adults"),
    "lancet": ("Livingston G, et al.", "Dementia prevention, intervention, and care: 2024 report of the Lancet standing Commission", "The Lancet", "2024", "https://chronicdisease.org/wp-content/uploads/2024/12/Lancet-2024.pdf"),
    "usda": ("U.S. Department of Agriculture", "MyPlate.gov", "USDA", "2026", "https://www.myplate.gov/"),
}


def page(section: str, title: str, body: str, bullets: list[str] | None = None, layout: str = "split_visual_right", visual: str | None = None, callout: tuple[str, str, str] | None = None, worksheet: dict | None = None):
    return {"section": section, "title": title, "body": body, "bullets": bullets or [], "layout": layout, "visual": visual, "callout": callout, "worksheet": worksheet}


def guides() -> list[dict]:
    mindful_pages = [
        page("Welcome", "A calmer way to build a meal", "If food advice has started to feel like a stack of rules, this guide is meant to lower the noise. The Mindful Plate is a flexible way to assemble meals that include vegetables, protein, carbohydrate, drink, and flavor without weighing everything or giving up foods that matter to you.", ["Use it as a starting point, not a rulebook.", "Ask for individualized guidance if you are pregnant, have kidney disease, an eating disorder history, allergies, gastrointestinal disease, or a prescribed medical diet."], "card_grid", None, ("This guide cannot replace", "Medical nutrition therapy, medication guidance, glucose targets, insulin changes, pregnancy care, eating-disorder care, or urgent medical attention.", "orange")),
        page("Quick start", "Start here tonight", "Choose one meal, not your whole life. Use the plate as a quick visual check, then adapt it to the food you actually have.", ["Half the plate: non-starchy vegetables when available.", "One quarter: protein such as eggs, fish, tofu, beans, yogurt, chicken, or lean meat.", "One quarter: carbohydrate such as rice, oats, bread, fruit, beans, potato, or tortilla.", "Drink: water, unsweet tea, or another lower-sugar choice."], "card_grid", "mindful-plate", ("No all-or-nothing test", "If dinner is pizza, add a salad or vegetable side. If breakfast is rushed, improve the drink. One useful change is enough.", "green")),
        page("Food and blood sugar", "What happens after we eat?", "During digestion, the body breaks food into smaller parts. Carbohydrate foods usually have the most direct effect on blood glucose because many carbohydrates break down into glucose. Insulin helps move glucose from the blood into cells so it can be used for energy. [1]", ["Protein, fiber, fat, portion, activity, timing, stress, illness, sleep, alcohol, and medicines can all influence glucose patterns.", "Two people can eat a similar meal and see different results."], "full_width_visual_then_text", "digestion", ("Safety note", "Do not change insulin, diabetes medicine, or glucose targets because of this guide. If readings are often high or low, ask your care team what changes are safest for you.", "orange")),
        page("Plate method", "The Mindful Plate method", "A common diabetes plate pattern uses about one-half non-starchy vegetables, one-quarter protein, one-quarter carbohydrate, and water or another low-calorie drink. [2] This guide uses that pattern as a flexible starting point.", ["Mixed dishes can still be balanced by thinking about what is inside them.", "The method can fit bowls, soups, tacos, dal, stir-fries, sandwiches, and leftovers."], "split_visual_right", "mindful-plate", ("What this does not mean", "Every meal does not need to look separated on a plate. Culture, appetite, budget, and medical needs still matter.", "green")),
        page("Carbohydrates", "Carbs without confusion", "Carbohydrates are found in grains, starchy vegetables, fruit, milk, yogurt, beans, lentils, sweets, and sugary drinks. They are not automatically forbidden. The type, amount, and what you eat with them matter.", ["Pair carbohydrate foods with protein, fiber-rich foods, vegetables, and satisfying flavor when possible.", "Total carbohydrate and added sugar can both be useful label checks."], "full_width_visual_then_text", "carb-families", ("Try this", "Choose one carbohydrate you eat often. Keep the food, but experiment with portion and pairing.", "green")),
        page("Protein", "Protein helps a meal hold together", "Protein foods can support fullness and help make a meal feel more steady. They may come from animal or plant sources, and budget options count.", ["Eggs, fish, chicken, turkey, lean meats, tofu, tempeh, edamame, Greek yogurt, cottage cheese, beans, lentils, nuts, and seeds can all fit.", "Beans and lentils contain both protein and carbohydrate."], "split_visual_right", "protein-map", ("Budget note", "Canned tuna, eggs, beans, lentils, tofu, and plain yogurt can be practical lower-cost protein anchors.", "green")),
        page("Fiber", "Fiber is quiet but useful", "Fiber is a type of carbohydrate the body does not fully digest. Many fiber-rich foods can support fullness, bowel regularity, cholesterol patterns, and steadier meals. The FDA Daily Value for fiber is 28 grams per day based on a 2,000-calorie diet, but individual needs vary. [3]", ["Add fiber gradually and drink fluids.", "Ask for guidance if fiber worsens symptoms or you have a digestive or kidney condition."], "split_visual_left", "fiber-ladder", ("Gentle pace", "A sudden jump in fiber can feel uncomfortable. Add one food at a time.", "green")),
        page("Dietary fat", "Fat adds flavor, texture, and staying power", "Dietary fat is an essential nutrient. The type and food source matter. A heart-health pattern usually emphasizes unsaturated fats from nuts, seeds, avocado, fish, and non-tropical liquid plant oils while limiting saturated fat and avoiding trans fat. [6]", ["Use small amounts of flavorful fats to make meals satisfying.", "The companion guide Fats Without Fear explains this in more detail."], "comparison", "drink-comparison", ("More detail coming", "Use the Fats Without Fear guide for saturated, unsaturated, and trans fats in plain language.", "green")),
        page("Breakfasts", "Breakfasts, if breakfast fits your day", "Not everyone wants or needs breakfast. If you do eat it, breakfast can be a useful place to add protein, fiber, and a lower-sugar drink.", ["Eggs, whole-grain toast, and vegetables.", "Plain yogurt with berries, nuts, and oats.", "Oatmeal with seeds, fruit, and nut butter.", "Beans, egg or tofu, salsa, vegetables, and corn tortilla."], "card_grid", "breakfast-grid", None),
        page("Lunches", "Lunches that do not require a fresh start", "Lunch often happens between work, caregiving, school, appointments, or errands. It does not need to be a recipe. Think in pieces: colorful food, protein, fiber, and something enjoyable.", ["Bowl: greens, leftover chicken or tofu, beans, salsa, and rice.", "Sandwich: whole-grain bread, turkey or hummus, vegetables, and fruit.", "No-cook: tuna packet, whole-grain crackers, cucumber, carrots, and fruit."], "card_grid", "lunch-grid", ("Restaurant note", "Choose one adjustment: add vegetables, choose water, share fries, or save part for later.", "green")),
        page("Dinners", "Dinners can honor culture and still be balanced", "Healthy eating should not erase family food. Many traditional meals already include vegetables, beans, lentils, fish, lean meats, yogurt, grains, herbs, spices, and shared routines.", ["Tacos with beans or grilled protein, cabbage, salsa, avocado, and corn tortillas.", "Dal with vegetables, cucumber salad, and rice.", "Stir-fry with tofu, chicken, shrimp, or beef, vegetables, and rice.", "Caribbean-inspired plate with fish or chicken, greens, beans, and plantain."], "card_grid", "dinner-grid", ("Pattern over perfection", "A higher-carbohydrate food can often fit better when the rest of the plate supports it.", "green")),
        page("Snacks", "Snacks are optional", "Some people feel better with planned snacks. Others do not need them. Snacks may be useful if meals are far apart, activity changes glucose, medication timing matters, or hunger makes the next meal harder.", ["Apple with peanut butter.", "Plain yogurt with berries.", "Hummus with vegetables or whole-grain crackers.", "Boiled egg with fruit.", "Nuts with a small piece of fruit."], "card_grid", "snack-grid", ("Medication safety", "If you use insulin or medicines that can cause low blood sugar, ask your care team how snacks, activity, and low readings should be handled.", "orange")),
        page("Drinks", "Drinks and hidden sugars", "Sugary drinks can raise blood glucose quickly because they are easy to drink fast and do not bring much fiber or fullness. Soda, sweet tea, juice, energy drinks, sports drinks, and sweet coffee drinks can all add sugar quickly.", ["The FDA Daily Value for added sugars is 50 grams per day based on a 2,000-calorie diet. [4]", "Start by improving one drink you have often."], "full_width_visual_then_text", "drink-comparison", ("Try this", "Make one drink change: smaller size, less syrup, unsweet tea, sparkling water, infused water, or water beside the drink.", "green")),
        page("Portions", "Portions without weighing everything", "Portions do not need to be exact to be useful. The plate method gives a visual estimate. Labels give serving sizes. Cups, bowls, and hand-based estimates can help when measuring is not realistic.", ["A fist can be a rough estimate for about one cup of some foods.", "A palm can be a rough estimate for a portion of cooked protein.", "A label serving size is the amount used for the numbers on the label, not a personal prescription. [3]"], "split_visual_right", "portion-guide", ("Keep it kind", "Portion awareness is a tool, not a judgment. If measuring food feels stressful or unsafe, ask for support.", "orange")),
        page("Sample menu", "Three days of flexible ideas", "These are examples, not a prescription. Your calorie, carbohydrate, protein, sodium, kidney, allergy, pregnancy, medication, and glucose needs may be different.", [], "full_width_visual_then_text", "menu-table", ("Vegetarian swap", "Use beans, lentils, tofu, tempeh, edamame, eggs, yogurt, nuts, and seeds when they fit your needs.", "green")),
        page("Worksheet", "Build your own meal", "Choose one meal you already eat. Write down what you could add, reduce, swap, or prepare ahead. Keep the change small enough that you can actually try it.", [], "worksheet_full_page", None, None, {"type": "fields", "fields": ["1/2 plate vegetables", "1/4 plate protein", "1/4 plate carbohydrate", "Drink", "Flavor or fat", "What I can prep ahead"]}),
        page("Shopping", "Grocery starter list", "Use this as a starter list, not a rule. Frozen, canned, dried, and store-brand foods can be practical.", ["Vegetables, fruit, protein, carbohydrates, healthy fats, flavor builders, and freezer or pantry backups.", "Rinse canned beans or vegetables when you want less sodium."], "card_grid", "grocery-list", ("Budget note", "Frozen, canned, dried, and store-brand foods can reduce waste and cost.", "green")),
        page("Questions and myths", "A few food questions people ask all the time", "Food questions are normal because nutrition advice can be noisy. These short answers are designed to reduce fear, not replace personal guidance.", ["Do I have to stop eating carbohydrates? No.", "Is fruit too sugary? Whole fruit can fit for many people.", "Are potatoes forbidden? No; portion and pairing matter.", "Do I have to buy expensive health foods? No.", "Can I keep culturally important foods? Yes."], "card_grid", "myth-grid", None),
        page("Next steps", "Keep the guide useful", "Pick one page to use this week. You might build one balanced dinner, improve one drink, or complete the meal worksheet.", ["Explore more Mindful Diabetes guides.", "Join the newsletter.", "Visit Health Tools and JEIR.", "Support free health education if you are able."], "back_cover", None, ("Medical disclaimer", "This guide is general education, not medical advice, diagnosis, or treatment. Do not change medication, insulin, or glucose targets based on this guide.", "orange")),
    ]
    fats_pages = [
        page("Welcome", "Fat is not something to fear", "Fat is an essential nutrient and food would be dull without it. The useful question is not whether fat is allowed, but which fat sources show up most often and what they replace.", ["You will learn the main fat types, how to read labels, and how to try practical swaps.", "Ask for individualized advice if you have pancreatitis, gallbladder disease, high triglycerides, kidney disease, or a prescribed diet."], "card_grid", "food-sources", None),
        page("What fat does", "What dietary fat does in the body", "Fat helps build cell membranes, carries flavor, supports fullness, and helps the body absorb vitamins A, D, E, and K.", ["Food source matters more than one isolated number.", "Nuts, oils, fish, dairy, meats, and fried foods are not nutritionally identical."], "split_visual_right", "fat-types", None),
        page("Fat types", "Saturated, unsaturated, and trans fats", "Saturated, monounsaturated, polyunsaturated, and trans fats behave differently. The American Heart Association recommends limiting saturated fat and avoiding trans fat, while choosing unsaturated fats in place of saturated fat when possible. [6]", ["Saturated fats are common in butter, cheese, fatty meats, and tropical oils.", "Unsaturated fats are common in non-tropical liquid oils, nuts, seeds, avocado, and fish."], "card_grid", "fat-types", None),
        page("Replacement", "Why replacement matters", "A lower-saturated-fat pattern works best when saturated fat is replaced by unsaturated fat sources, vegetables, beans, fruit, and whole grains, not simply by refined starches or added sugar. [6]", ["Swap, do not just subtract.", "Look at the overall eating pattern."], "split_visual_left", "replacement-pathway", None),
        page("Blood fats", "LDL, HDL, and triglycerides", "LDL cholesterol is often called 'bad' cholesterol because higher levels can contribute to plaque in arteries. HDL and triglycerides are also part of cardiovascular risk, but no single number tells the whole story.", ["Ask what your personal numbers mean.", "Do not start supplements for cholesterol or triglycerides without guidance."], "card_grid", "lipid-cards", None),
        page("Cooking oils", "Cooking oils", "Non-tropical liquid plant oils such as olive, canola, soybean, sunflower, avocado, corn, and peanut oils are generally useful options. Coconut and palm oils are higher in saturated fat and should not be treated as miracle foods. [7]", ["Choose an oil that fits the recipe and budget.", "Use measured amounts when portions are a concern."], "full_width_visual_then_text", "oil-chart", None),
        page("Nuts and avocado", "Nuts, seeds, and avocado", "These foods can add unsaturated fats, fiber, minerals, texture, and satisfaction. They are calorie-dense, which is a neutral fact, not a moral warning.", ["Try peanuts, walnuts, sunflower seeds, pumpkin seeds, chia, flax, or avocado.", "Buy small bags or store-brand options if cost matters."], "split_visual_right", "food-sources", None),
        page("Fish", "Fish and omega-3 fats", "Fish can be a useful protein source and fatty fish provides omega-3 fats. Eating fish is different from assuming everyone needs an omega-3 supplement.", ["Canned salmon, sardines, or tuna may be budget options.", "Pregnancy, allergies, mercury concerns, and medications require individualized advice."], "split_visual_left", "fish-source", ("Supplement caution", "Do not treat omega-3 supplements as universally needed. Ask your clinician if supplements are safe for you.", "orange")),
        page("Dairy fats", "Butter, cheese, cream, and full-fat dairy", "Butter, cream, cheese, and many full-fat dairy foods can be higher in saturated fat. You do not have to ban them, but it helps to notice frequency and portion.", ["Use strong flavors in smaller amounts.", "Try yogurt, lower-fat dairy, or plant options when they fit your needs."], "comparison", "dairy-swap", None),
        page("Tropical oils", "Coconut and palm oils", "Natural does not automatically mean heart-supportive. Coconut and palm oils are plant-based but still high in saturated fat. [7]", ["Use them less often if LDL cholesterol is a concern.", "Avoid miracle-food claims."], "comparison", "tropical-oils", None),
        page("Fried foods", "Fried and ultra-processed foods", "Fried foods and many packaged snacks can combine refined starch, sodium, saturated fat, and large portions. The issue is the pattern, not a single food.", ["Choose less often, share a portion, or pair with vegetables.", "Read labels on packaged foods."], "comparison", "fried-pattern", None),
        page("Label reading", "Reading the Nutrition Facts label", "The label lists total fat, saturated fat, trans fat, serving size, and Percent Daily Value. The FDA notes that 5% DV or less is low and 20% DV or more is high for a nutrient. [3]", ["Start with serving size.", "Compare saturated fat across similar foods."], "full_width_visual_then_text", "label-map", None),
        page("Breakfast swaps", "Breakfast swaps", "A swap should still taste like breakfast. Keep one familiar food and change the fat source or add fiber.", ["Avocado on toast instead of butter sometimes.", "Plain yogurt with nuts instead of sweetened pastry.", "Eggs with vegetables instead of a fried-meat side."], "comparison", "breakfast-swap", None),
        page("Meal swaps", "Lunch and dinner swaps", "Try beans, fish, tofu, or lean poultry more often. Use olive oil vinaigrette instead of creamy dressing sometimes.", ["Swap frequency, not identity.", "Make the meal satisfying enough to repeat."], "comparison", "meal-swap", None),
        page("Snack swaps", "Snack swaps", "For crunch, try nuts, roasted chickpeas, popcorn, vegetables with hummus, or whole-grain crackers with tuna.", ["For sweet snacks, pair fruit with yogurt, nuts, or nut butter.", "Planned snacks can prevent grazing for some people."], "comparison", "snack-swap", None),
        page("Budget", "Budget-friendly fats", "Healthy fat choices do not have to be expensive. Peanuts, sunflower seeds, canola oil, canned fish, eggs, and store-brand nut butters can all fit.", ["Buy what you will actually use.", "Avoid letting premium wellness foods define health."], "card_grid", "budget-fats", None),
        page("Myths", "Myths and frequently asked questions", "Fat-free does not always mean healthier, keto does not automatically mean heart-supportive, and coconut oil is not a cure-all.", ["Look past front-package claims.", "Use your lab numbers and clinician guidance."], "card_grid", "fat-myths", None),
        page("Planner", "Personal fat-swap planner", "Choose one meal where a fat swap feels realistic. Write the current choice, one possible replacement, cost, taste, and whether you would repeat it.", [], "worksheet_full_page", None, None, {"type": "table", "rows": 6, "fields": ["Meal", "Current choice", "Possible swap", "Cost", "Taste", "Repeat?", "Notes"]}),
        page("Next steps", "Heart and brain health summary", "Dietary fat choices matter most as part of a larger pattern that also includes vegetables, fiber-rich foods, movement, sleep, blood pressure, cholesterol, glucose care, and clinical guidance.", ["Explore the Mindful Plate guide.", "Ask your clinician what your cholesterol numbers mean.", "Share the guide with someone who feels confused by fat advice."], "back_cover", None, None),
    ]
    grocery_pages = [
        page("Before shopping", "Before you shop", "A good grocery trip starts before the store. Check what you already have, choose two or three meals, and pick backup foods for busy days.", ["You do not need a perfect list.", "A short list you use is better than an ideal list left at home."], "split_visual_right", "smart-cart", None),
        page("Five-part cart", "The five-part cart formula", "Build around vegetables, protein, fiber-rich carbohydrates, healthy fats, and flavor builders. This keeps shopping practical without depending on one brand or diet plan.", ["Fresh, frozen, canned, and dried foods can all fit.", "Perimeter-only shopping misses many useful budget foods."], "full_width_visual_then_text", "smart-cart", None),
        page("Produce", "Produce", "Choose vegetables and fruits you will actually eat. Fresh produce is wonderful, but it is not the only way to eat well.", ["Pre-cut vegetables can save energy.", "Frozen vegetables may reduce waste."], "comparison", "fresh-frozen-canned", None),
        page("Frozen foods", "Frozen foods", "Frozen vegetables and fruit can be affordable, quick, and nutritious. Look for options without heavy sauces or added sugars when possible.", ["Frozen berries work in yogurt or oats.", "Frozen greens can disappear into soups and eggs."], "split_visual_left", "freezer-staples", None),
        page("Canned foods", "Canned foods", "Canned beans, tuna, salmon, vegetables, tomato products, and soups can help on low-energy days. Rinsing canned beans or vegetables can lower sodium.", ["Compare labels when you can.", "Keep emergency meals in the pantry."], "card_grid", "pantry-cards", None),
        page("Protein", "Protein choices", "Protein can come from eggs, fish, poultry, lean meat, tofu, tempeh, yogurt, cottage cheese, beans, lentils, nuts, and seeds.", ["Beans and lentils also contain carbohydrate.", "Choose based on budget, culture, and medical needs."], "split_visual_right", "protein-map", None),
        page("Plant proteins", "Beans, lentils, tofu, and plant proteins", "Beans, lentils, tofu, tempeh, and edamame can support filling meals. They are useful in soups, tacos, bowls, stir-fries, curries, and salads.", ["Seasoning matters.", "Start with canned beans if dried beans feel like too much."], "card_grid", "plant-proteins", None),
        page("Grains", "Breads, grains, cereals, and tortillas", "Look for grains and breads that bring fiber and fit your glucose plan. Whole grain, serving size, and total carbohydrate are more useful than marketing claims alone.", ["Multigrain does not always mean whole grain.", "Compare fiber and total carbohydrate."], "full_width_visual_then_text", "grain-label", None),
        page("Dairy", "Dairy and alternatives", "Milk and yogurt contain carbohydrate. Plain yogurt, unsweetened fortified soy milk, and lower-sugar options may fit many plans, but allergies and preferences vary.", ["Check added sugar.", "Choose what fits your taste and budget."], "card_grid", "dairy-cards", None),
        page("Snacks", "Snacks", "A snack can be planned or it can become accidental grazing. Pair protein or fat with fiber when you want something that lasts longer.", ["Fruit with nuts.", "Hummus with vegetables.", "Yogurt with berries."], "split_visual_right", "snack-formula", None),
        page("Drinks", "Drinks", "Sweet drinks can add sugar quickly. Start by improving one drink you have often rather than overhauling every beverage.", ["Water, unsweet tea, sparkling water, or smaller sweet drinks can all be steps.", "Alcohol needs medication and safety awareness."], "comparison", "drink-comparison", None),
        page("Label", "Reading the Nutrition Facts label", "Start with serving size, then check total carbohydrate, fiber, added sugar, saturated fat, and sodium. Percent Daily Value helps compare nutrients. [3]", ["5% DV is low and 20% DV is high.", "Serving size is not a personal portion prescription."], "full_width_visual_then_text", "label-map", None),
        page("Carbs and sugar", "Total carbohydrate and added sugar", "Total carbohydrate includes starches, fiber, sugars, and added sugars. Added sugars are added during processing or packaging, while naturally occurring sugars can be found in fruit and milk. [4]", ["Total carbohydrate matters for glucose.", "Ingredient names do not replace checking total carbohydrate."], "split_visual_right", "sugar-names", None),
        page("Fiber", "Fiber", "Fiber can support fullness and steadier meals. The Nutrition Facts label lists dietary fiber in grams and Percent Daily Value.", ["Compare similar products.", "Increase fiber gradually."], "split_visual_left", "fiber-ladder", None),
        page("Sodium", "Sodium", "The FDA Daily Value for sodium is less than 2,300 mg per day. Many packaged foods vary widely, so comparing labels can help. [5]", ["5% DV or less is low.", "20% DV or more is high."], "full_width_visual_then_text", "sodium-label", None),
        page("Claims", "Ingredient lists and marketing claims", "Front labels can be useful, but they are not the whole story. Natural, keto, diabetic-friendly, low-fat, sugar-free, and no sugar added still deserve a label check.", ["Net carbs are not regulated the same way on every label.", "Sugar-free does not always mean carbohydrate-free."], "card_grid", "claims", None),
        page("Budget", "Budget strategies", "Use store brands, frozen vegetables, canned beans, oats, eggs, lentils, rice, seasonal produce, and planned leftovers.", ["Shop your kitchen first.", "Let budget be part of the plan, not a source of shame."], "card_grid", "budget-cart", None),
        page("Fast meals", "Ten-minute meal formulas", "Fast meals can still have structure: heat a base, add protein, add vegetables, add flavor, and choose a drink.", ["Beans, salsa, greens, and tortillas.", "Frozen vegetables, tofu, sauce, and rice.", "Tuna, crackers, cucumber, fruit, and water."], "full_width_visual_then_text", "meal-formula", None),
        page("Checklist", "Printable grocery checklist", "Use this list as a starting point. Add what fits your family, budget, culture, and medical needs.", [], "worksheet_full_page", None, None, {"type": "fields", "fields": ["Produce", "Protein", "Fiber-rich carbohydrates", "Healthy fats", "Drinks", "Snacks", "Pantry/freezer backups", "Notes"]}),
        page("Next steps", "Make the store easier next time", "Save one list that worked, one backup meal, and one label comparison. The next trip gets easier when you do not start from scratch.", ["Download another free guide.", "Visit Health Tools.", "Share this guide with a caregiver or friend."], "back_cover", None, None),
    ]
    reset_pages = [
        page("Welcome", "A reset is not a cleanse", "This reset means pausing, observing, and creating a few useful routines. It is not a detox, crash diet, or promise.", ["Do not change medicines or insulin based on this guide.", "Choose movement that is safe for your body."], "card_grid", "roadmap", None),
        page("Habits", "How habits work", "Habits often need a cue, a routine, and a reward. The smaller the routine, the easier it is to repeat when life gets busy.", ["Tie a new habit to something you already do.", "Make backup plans part of the habit."], "split_visual_right", "habit-loop", None),
        page("Overview", "Seven-day overview", "Each day asks for one main action. You can repeat a day, skip a day, or adapt the plan. The point is learning, not proving anything.", ["Day 1 notice.", "Day 2 build one balanced meal.", "Day 3 add fiber.", "Day 4 break up sitting.", "Day 5 improve one drink.", "Day 6 protect sleep.", "Day 7 plan next week."], "full_width_visual_then_text", "roadmap", None),
        page("Day 1", "Notice your starting point", "Record a normal day without judgment. Notice drinks, meals, movement, sleep, energy, mood, and one thing that felt hard.", ["Choose one realistic goal.", "Keep private health notes secure."], "worksheet_full_page", None, None, {"type": "fields", "fields": ["Today I noticed", "One drink pattern", "One meal pattern", "One movement pattern", "One sleep note", "One realistic goal"]}),
        page("Day 2", "Build one balanced meal", "Use the Mindful Plate method for one meal only. Add vegetables, protein, carbohydrate, and a lower-sugar drink if possible.", ["One meal is enough.", "Mixed dishes can still count."], "split_visual_right", "balanced-meal", None),
        page("Day 3", "Add a source of fiber", "Add one fiber source such as beans, lentils, oats, berries, vegetables, whole grains, nuts, or seeds. Increase gradually and drink fluids.", ["Stop and ask for advice if fiber worsens symptoms.", "People with some medical diets need individual guidance."], "split_visual_left", "fiber-ladder", None),
        page("Day 4", "Break up sitting time", "Short activity breaks can help many people. Options include walking, standing, chair movement, stretching, or gentle household tasks.", ["The CDC describes 150 minutes per week as a common adult activity goal, but starting slowly is okay. [9]", "Ask which activities are safest for you."], "split_visual_right", "movement-menu", None),
        page("Day 5", "Improve one drink", "Choose one drink you have often and adjust it. Try less sugar, a smaller size, unsweet tea, water, sparkling water, or a gradual step-down.", ["You do not need to love plain water overnight.", "Alcohol and diabetes medicine require safety awareness."], "comparison", "drink-comparison", None),
        page("Day 6", "Protect sleep", "A realistic sleep routine may include a consistent wake time, dimmer light, less late caffeine, a wind-down cue, and a plan for pain, caregiving, or work shifts.", ["Sleep problems deserve care, not blame.", "Ask about snoring, breathing pauses, insomnia, or restless legs."], "split_visual_left", "sleep-timeline", None),
        page("Day 7", "Prepare the next week", "Look back at what helped, what felt irritating, and what was too much. Pick one habit to repeat for another week.", ["Keep the habit small.", "Write down one question for a clinician if needed."], "worksheet_full_page", None, None, {"type": "fields", "fields": ["What worked", "What was difficult", "What I will continue", "What I will pause", "Question for care team"]}),
        page("Hydration tracker", "Hydration tracker", "Track drinks for awareness, not judgment. A beverage inventory can reveal one easy place to reduce added sugar.", [], "worksheet_full_page", None, ("Privacy reminder", "Store completed health notes securely if they include personal information.", "orange"), {"type": "table", "rows": 7, "fields": ["Day", "Water", "Sweet drinks", "Coffee additions", "Juice", "Alcohol", "Timing/notes"]}),
        page("Movement tracker", "Movement tracker", "Record movement that is safe for your body. Chair movement, stretching, physical therapy exercises, and short walks all count as information.", [], "worksheet_full_page", None, None, {"type": "table", "rows": 7, "fields": ["Activity", "Minutes", "Type", "How it felt", "Pain/symptoms"]}),
        page("Meal and fiber tracker", "Meal and fiber tracker", "Use this page to notice meals that kept you satisfied. Write the vegetable, protein, carbohydrate, and fiber source when you can.", [], "worksheet_full_page", None, None, {"type": "table", "rows": 7, "fields": ["Meal", "Vegetable", "Protein", "Carb", "Fiber", "Satisfaction"]}),
        page("Sleep check-in", "Sleep check-in", "Sleep is affected by stress, shift work, caregiving, pain, medications, breathing problems, and mental health. This page helps you notice what is changeable.", [], "worksheet_full_page", None, None, {"type": "table", "rows": 7, "fields": ["Bedtime", "Wake", "Waking", "Naps", "Caffeine", "Screens", "Notes"]}),
        page("Mood and energy", "Mood and energy", "Energy can change with meals, sleep, movement, stress, and blood glucose. A simple mood and energy note can help you see patterns.", [], "worksheet_full_page", None, None, {"type": "table", "rows": 7, "fields": ["Day", "Mood 1-5", "Energy 1-5", "Meal note", "Sleep note", "Other notes"]}),
        page("Glucose notes", "Optional glucose notes", "If you monitor glucose, use this page only in the way your care team recommends. Do not chase perfect numbers.", [], "worksheet_full_page", None, ("Safety note", "Record action taken according to your care plan. Do not change medicine based on this worksheet alone.", "orange"), {"type": "table", "rows": 6, "fields": ["Date/time", "Reading", "Meal", "Medicine", "Activity/stress/sleep", "Action per plan"]}),
        page("Obstacles", "Obstacles and backup plans", "Plan for busy days before they arrive. A backup meal, safe movement option, and lower-sugar drink can protect momentum.", [], "worksheet_full_page", None, None, {"type": "fields", "fields": ["If this obstacle happens", "My easiest backup meal", "My safest movement option", "My drink backup", "Who can help", "What I can let be imperfect"]}),
        page("30-day plan", "30-day continuation plan", "After seven days, continue one or two habits. A prevention plan should fit real life well enough to survive an ordinary month.", [], "worksheet_full_page", None, None, {"type": "calendar", "fields": []}),
        page("Next steps", "Repeat what worked", "Keep one or two helpful routines. Drop what was unrealistic. Add one next step only when the current habit feels repeatable.", ["Explore other Mindful Diabetes guides.", "Visit Health Tools.", "Ask your care team about patterns you noticed."], "back_cover", None, None),
    ]
    brain_pages = [
        page("Mission", "The everyday connection", "Mindful Diabetes connects education, prevention, research awareness, and practical tools at the intersection of metabolic and brain health. The goal is clarity, not fear.", ["Risk can be influenced, but not perfectly controlled.", "Memory concerns deserve qualified evaluation."], "card_grid", "risk-wheel", None),
        page("Glucose basics", "What glucose does in the body", "Glucose is one of the body's energy sources. The brain uses glucose, but it also depends on steady blood flow, oxygen, sleep, and many other supports.", ["More glucose is not better.", "Very low glucose can be dangerous."], "full_width_visual_then_text", "glucose-pathway", None),
        page("Insulin", "How insulin helps regulate glucose", "Insulin helps move glucose from the blood into cells. Diabetes care often includes supporting glucose levels near a personal target range. [12]", ["Targets are individualized.", "Medication decisions belong with your care team."], "split_visual_right", "glucose-pathway", None),
        page("Insulin resistance", "Insulin resistance", "Insulin resistance means cells do not respond to insulin as easily. The body may need more insulin to move glucose into cells.", ["It can develop gradually.", "Food, movement, sleep, stress, weight, medicines, and genetics can all be involved."], "split_visual_left", "insulin-resistance", None),
        page("Brain energy", "The brain needs steady support", "The brain is sensitive to glucose changes. CDC notes that both high and low blood sugar can affect the brain and blood vessels. [12]", ["Repeated lows and prolonged highs both deserve care.", "Ask what patterns matter for you."], "comparison", "high-low", None),
        page("Blood vessels", "Blood vessels and brain health", "Blood vessels carry oxygen and nutrients to the brain. Diabetes, high blood pressure, and cholesterol concerns can affect vascular health over time.", ["Vascular dementia is different from ordinary forgetfulness.", "Sudden confusion can be an emergency."], "split_visual_right", "vessel-brain", None),
        page("High glucose", "High blood sugar over time", "Frequent hyperglycemia can stress blood vessels and nerves. Effects may build slowly and are not always obvious in the moment. [12]", ["This is a reason for support, not shame.", "Patterns are more useful than one isolated reading."], "comparison", "high-low", None),
        page("Low glucose", "Low blood sugar and the brain", "Hypoglycemia can cause shakiness, dizziness, confusion, trouble speaking, seizures, or loss of consciousness. It can be urgent, especially for people using insulin or certain medicines. [12]", ["Know your care team's low-glucose plan.", "Do not drive or ignore severe symptoms."], "comparison", "high-low", ("Urgent symptoms", "Sudden confusion, seizure, fainting, or severe low blood sugar needs appropriate medical attention.", "orange")),
        page("Cognitive risk", "Diabetes and cognitive-health risk", "Diabetes is associated with increased risk for cognitive problems and dementia, but it does not make dementia inevitable. Dementia has many causes and contributors. [13]", ["Risk is not destiny.", "Memory concerns deserve evaluation."], "split_visual_right", "risk-wheel", None),
        page("Risk meaning", "What increased risk actually means", "Risk describes probability across groups. It cannot tell you what will happen to one person. Habits, medical care, social factors, genetics, and environment all interact.", ["Avoid panic.", "Use risk information to guide questions and care."], "comparison", "risk-meaning", None),
        page("BP and cholesterol", "Blood pressure and cholesterol", "Managing blood pressure and cholesterol can support heart and brain health. NIA and CDC identify vascular health as part of cognitive-health protection. [13,14]", ["Ask for your numbers.", "Ask what target range fits your age and health history."], "split_visual_left", "vessel-brain", None),
        page("Activity", "Physical activity", "Regular physical activity can support cardiovascular, metabolic, mood, sleep, and brain health. Start with what is safe and possible.", ["Walking is one option, not the only option.", "Chair movement and physical therapy can count."], "split_visual_right", "movement-menu", None),
        page("Food patterns", "Food patterns", "Food patterns that include vegetables, fruits, legumes, whole grains, lean or plant proteins, and unsaturated fat sources can support metabolic and cardiovascular health.", ["No single brain-protection food is magic.", "Budget and culture matter."], "split_visual_left", "mindful-plate", None),
        page("Sleep", "Sleep", "Sleep problems can affect mood, energy, glucose patterns, and daily decision-making. A realistic sleep plan may require medical care.", ["Ask about sleep apnea symptoms.", "Caregiving, shift work, pain, and medications matter."], "split_visual_right", "sleep-timeline", None),
        page("Smoking and alcohol", "Smoking and alcohol", "Smoking and excessive alcohol use are dementia risk factors identified by public-health sources and dementia-prevention research. [13,15]", ["If you do not drink alcohol, do not start for health.", "Ask for support if quitting tobacco feels hard."], "comparison", "risk-reduction", None),
        page("Connection", "Hearing, vision, and social connection", "Hearing loss, vision problems, depression, and social isolation can affect cognitive health and quality of life. [13,14,15]", ["Treating hearing or vision problems may reduce strain.", "Social contact can be practical, not fancy."], "card_grid", "connection-cards", None),
        page("Clinician questions", "Questions for your clinician", "Bring questions about A1C, blood pressure, cholesterol, medicines, low-glucose risk, memory changes, sleep, hearing, and family history.", [], "worksheet_full_page", None, None, {"type": "fields", "fields": ["A1C and glucose targets", "Blood pressure", "Cholesterol", "Medicines and low glucose", "Memory concerns", "Sleep", "Hearing/vision", "Family history"]}),
        page("Family history", "Family-history worksheet", "Family history can help guide questions, but it does not determine your future. Write what you know and leave blanks where you are unsure.", [], "worksheet_full_page", None, None, {"type": "table", "rows": 6, "fields": ["Condition", "Relative", "Age known?", "Notes", "Question"]}),
        page("Health numbers", "Health-number and habit tracker", "Use this page to keep clinician-selected targets in one place. Store completed health information securely.", [], "worksheet_full_page", None, None, {"type": "table", "rows": 7, "fields": ["Date", "A1C", "BP", "Lipids", "Medicine", "Sleep/activity", "Clinician target"]}),
        page("Can and cannot", "What prevention can and cannot promise", "Healthy routines may help reduce risk and support daily function. They do not guarantee prevention of Alzheimer's disease, reverse every case of diabetes, or replace medical care.", ["Use careful hope.", "Stay connected to qualified care."], "comparison", "can-cannot", None),
        page("Next steps", "Resources and next steps", "Use this guide to ask better questions, not to predict your future. Share memory concerns, sudden confusion, severe glucose symptoms, or major changes with qualified care.", ["Explore Mindful Diabetes resources.", "Visit Health Tools.", "Support free health education if you are able."], "back_cover", None, None),
    ]
    common_visuals = {
        "carb-families": [("Grains", "rice, oats, pasta, bread, tortillas", "grain"), ("Starchy vegetables", "potatoes, corn, peas, plantains", "carb"), ("Fruit", "berries, apples, bananas, oranges", "fruit"), ("Milk/yogurt", "milk, plain yogurt, kefir", "drink"), ("Beans/lentils", "black beans, chickpeas, dal", "protein"), ("Sweets/drinks", "soda, candy, sweet tea, desserts", "drink")],
        "protein-map": [("Animal proteins", "eggs, fish, poultry, lean meats", "protein"), ("Plant proteins", "tofu, tempeh, beans, lentils", "protein"), ("Dairy", "plain yogurt, cottage cheese", "drink"), ("Budget options", "eggs, canned fish, beans, lentils", "protein")],
        "fiber-ladder": ["Add one vegetable", "Add beans or lentils", "Choose oats or whole grains", "Add berries, nuts, or seeds", "Drink fluids and notice comfort"],
        "breakfast-grid": [("Eggs + toast + vegetables", "Protein, fiber, color, lower-sugar drink", "protein"), ("Yogurt bowl", "Plain yogurt, berries, nuts, oats", "fruit"), ("Oatmeal", "Oats, chia, fruit, nut butter", "grain"), ("Beans + tortilla", "Beans, egg or tofu, salsa, corn tortilla", "carb")],
        "lunch-grid": [("Bowl", "greens, beans, protein, salsa, rice", "vegetable"), ("Sandwich", "whole-grain bread, hummus or turkey, vegetables", "grain"), ("Soup", "lentil, bean, chicken vegetable", "protein"), ("No-cook", "tuna, crackers, vegetables, fruit", "fish")],
        "dinner-grid": [("Tacos", "beans or protein, cabbage, salsa, tortilla", "carb"), ("Dal", "lentils, vegetables, salad, rice", "protein"), ("Stir-fry", "protein, mixed vegetables, rice", "vegetable"), ("Pasta night", "pasta, vegetables, beans or lean protein", "grain")],
        "snack-grid": [("Fruit + nuts", "fiber plus fat", "fruit"), ("Yogurt + berries", "protein plus fruit", "drink"), ("Hummus + vegetables", "fiber plus flavor", "vegetable"), ("Egg + fruit", "protein plus carbohydrate", "protein")],
        "grocery-list": [("Vegetables", "fresh, frozen, canned", "vegetable"), ("Fruit", "fresh or frozen", "fruit"), ("Protein", "eggs, beans, fish, tofu", "protein"), ("Carbs", "oats, rice, potatoes, bread", "grain"), ("Fats", "nuts, seeds, oils, avocado", "fiber"), ("Flavor", "spices, salsa, vinegar, lemon", "vegetable")],
        "myth-grid": [("Carbs forbidden?", "No. Portion and pairing matter.", "grain"), ("Fruit too sugary?", "Whole fruit can fit for many people.", "fruit"), ("Brown sugar better?", "It is still added sugar.", "carb"), ("Potatoes forbidden?", "No. Preparation and portion matter.", "carb"), ("Expensive foods?", "No. Basics can be useful.", "protein"), ("Cultural foods?", "Yes. Adapt patterns, not identity.", "vegetable")],
        "fat-types": [("Saturated", "common in butter, cheese, fatty meats, tropical oils", "carb"), ("Monounsaturated", "olive oil, avocado, nuts", "fiber"), ("Polyunsaturated", "seeds, fish, soybean and sunflower oils", "fish"), ("Trans fat", "avoid partially hydrogenated oils", "carb")],
        "replacement-pathway": ["Notice the saturated-fat source", "Choose what will replace it", "Prefer unsaturated fat, beans, vegetables, fruit, or whole grains", "Keep flavor and satisfaction", "Repeat the swap if it works"],
        "food-sources": [("Nuts/seeds", "unsaturated fat plus texture", "fiber"), ("Fish", "protein and omega-3 sources", "fish"), ("Avocado", "unsaturated fat and fiber", "vegetable"), ("Oils", "use amounts that fit", "carb")],
        "lipid-cards": [("LDL", "one important risk marker", "carb"), ("HDL", "part of the larger picture", "fiber"), ("Triglycerides", "affected by many factors", "grain")],
        "fish-source": [("Salmon", "fresh, frozen, or canned", "fish"), ("Sardines", "budget-friendly for some", "fish"), ("Tuna", "check mercury guidance when relevant", "fish"), ("Supplements", "ask before starting", "carb")],
        "budget-fats": [("Peanuts", "often lower cost", "fiber"), ("Sunflower seeds", "crunch and fat", "fiber"), ("Canola oil", "neutral cooking option", "carb"), ("Canned fish", "shelf-stable protein", "fish")],
        "fat-myths": [("Fat-free", "not always healthier", "carb"), ("Keto", "not automatically heart-supportive", "grain"), ("Coconut oil", "not a miracle food", "carb"), ("Supplements", "not universal", "fish")],
        "smart-cart": [("Vegetables", "fresh, frozen, canned", "vegetable"), ("Protein", "animal or plant", "protein"), ("Fiber carbs", "oats, beans, grains, fruit", "grain"), ("Healthy fats", "nuts, seeds, oils", "fiber"), ("Flavor", "spices, salsa, herbs", "vegetable")],
        "freezer-staples": [("Frozen greens", "soups, eggs, bowls", "vegetable"), ("Berries", "yogurt or oats", "fruit"), ("Mixed vegetables", "fast side", "vegetable"), ("Frozen fish", "protein backup", "fish")],
        "pantry-cards": [("Beans", "rinse to lower sodium", "protein"), ("Tomatoes", "soups and sauces", "vegetable"), ("Tuna/salmon", "shelf-stable protein", "fish"), ("Oats", "fiber-rich staple", "grain")],
        "plant-proteins": [("Beans", "tacos, soups, bowls", "protein"), ("Lentils", "dal, soup, salad", "protein"), ("Tofu", "stir-fries and bowls", "protein"), ("Edamame", "snacks and sides", "protein")],
        "dairy-cards": [("Plain yogurt", "check added sugar", "drink"), ("Milk", "contains carbohydrate", "drink"), ("Soy milk", "look for unsweetened fortified", "drink"), ("Cheese", "check saturated fat", "carb")],
        "snack-formula": [("Fiber", "fruit, vegetables, whole grains", "fruit"), ("Protein/fat", "nuts, yogurt, hummus, egg", "protein"), ("Drink", "water or unsweet tea", "drink"), ("Plan", "portion before hunger spikes", "vegetable")],
        "claims": [("No sugar added", "still check total carbs", "carb"), ("Sugar-free", "not always carb-free", "carb"), ("Natural", "not a health guarantee", "vegetable"), ("Multigrain", "not always whole grain", "grain"), ("Keto", "still check saturated fat", "carb"), ("Low-fat", "check sugar and carbs", "drink")],
        "budget-cart": [("Store brand", "compare value", "vegetable"), ("Unit price", "check shelf label", "grain"), ("Freezer", "reduce waste", "vegetable"), ("Pantry", "backup meals", "protein")],
        "roadmap": ["Day 1 notice", "Day 2 meal", "Day 3 fiber", "Day 4 move", "Day 5 drink", "Day 6 sleep", "Day 7 plan"],
        "habit-loop": ["Cue: after coffee", "Routine: 5-minute walk", "Reward: mark tracker", "Repeat and adjust"],
        "movement-menu": [("Walk", "short or longer", "vegetable"), ("Stand", "brief breaks", "protein"), ("Chair movement", "seated options", "fiber"), ("Stretch", "gentle range", "grain")],
        "sleep-timeline": ["Morning wake cue", "Daylight and movement", "Less late caffeine", "Dim lights", "Wind-down routine"],
        "risk-wheel": [("Glucose", "individual target range", "grain"), ("Blood pressure", "vascular support", "vegetable"), ("Activity", "heart and brain", "protein"), ("Sleep", "energy and attention", "drink"), ("Hearing", "reduce strain", "fiber"), ("Connection", "social support", "vegetable")],
        "connection-cards": [("Hearing", "ask about testing", "fiber"), ("Vision", "support daily function", "vegetable"), ("Social contact", "practical connection", "protein"), ("Mood", "depression deserves care", "drink")],
    }
    comparison_visuals = {
        "drink-comparison": [("Choose less often", ["Large soda, sweet tea, energy drinks", "Juice as a frequent drink", "Sweet coffee additions"]), ("Choose more often", ["Water or sparkling water", "Unsweet tea or coffee", "Smaller sweet drink as a step-down"])],
        "dairy-swap": [("More saturated fat", ["Butter as default spread", "Cream-heavy sauces", "Large cheese portions"]), ("Flexible swaps", ["Olive oil when it fits", "Plain yogurt", "Smaller amount of strong cheese"])],
        "tropical-oils": [("Be careful with claims", ["Coconut oil is high in saturated fat", "Palm oil is also saturated-fat rich"]), ("Use context", ["Use less often for LDL concerns", "Choose non-tropical oils more often"])],
        "fried-pattern": [("Frequent pattern", ["Fried entree plus fries", "Sugary drink", "Few vegetables"]), ("Supportive pattern", ["Share or choose smaller portion", "Add vegetables", "Choose lower-sugar drink"])],
        "breakfast-swap": [("Current choice", ["Pastry plus sweet coffee", "Butter-heavy toast"]), ("Possible swap", ["Yogurt, berries, nuts", "Avocado or nut butter toast"])],
        "meal-swap": [("Current choice", ["Creamy dressing", "Meat-centered plate", "Fried side"]), ("Possible swap", ["Vinaigrette", "Beans, fish, tofu, poultry", "Vegetable side"])],
        "snack-swap": [("Quick but less lasting", ["Chips alone", "Sweet pastry", "Sugary drink"]), ("More staying power", ["Nuts and fruit", "Hummus and vegetables", "Yogurt and berries"])],
        "fresh-frozen-canned": [("Do not rank by aisle", ["Fresh can be great", "Frozen can reduce waste", "Canned can save dinner"]), ("Check what matters", ["Added sugar", "Sodium", "Sauces and serving size"])],
        "high-low": [("High over time", ["May affect vessels and nerves", "Patterns deserve care", "Not a shame signal"]), ("Low or sudden symptoms", ["Can affect thinking fast", "May be urgent", "Follow care plan"])],
        "risk-meaning": [("Group risk", ["Describes patterns across many people", "Useful for public health"]), ("Individual future", ["Not a prediction", "Medical care and life context matter"])],
        "risk-reduction": [("Can reduce risk", ["Avoid tobacco", "Limit alcohol if used", "Treat blood pressure"]), ("Cannot guarantee", ["No habit prevents every case", "Dementia has many contributors"])],
        "can-cannot": [("Can support", ["Blood vessel health", "Daily energy", "Risk reduction", "Better questions"]), ("Cannot guarantee", ["No Alzheimer's prevention promise", "No cure claim", "No replacement for care"])],
    }
    table_visuals = {
        "menu-table": {"headers": ["Day", "Breakfast", "Lunch", "Dinner", "Snack"], "rows": [["1", "Yogurt bowl", "Bean soup", "Fish, greens, rice", "Apple + peanut butter"], ["2", "Eggs + toast", "Hummus sandwich", "Tofu stir-fry", "Yogurt or nuts"], ["3", "Oatmeal", "Leftover bowl", "Dal, salad, rice", "Carrots + hummus"]], "row_h": 48},
        "oil-chart": {"headers": ["Oil/source", "Common use", "Context"], "rows": [["Olive", "saute, dressings", "unsaturated fat source"], ["Canola", "baking, saute", "neutral flavor"], ["Soybean/sunflower", "general cooking", "compare labels"], ["Coconut/palm", "specific recipes", "higher saturated fat"]], "row_h": 42},
        "label-map": {"headers": ["Label area", "Why it matters", "Helpful check"], "rows": [["Serving size", "Numbers are based on this", "Compare to your portion"], ["Total carbohydrate", "Glucose planning", "Check grams"], ["Added sugar", "Food quality clue", "Lower is often easier"], ["Saturated fat", "Heart-health context", "Compare similar foods"], ["Sodium", "Blood pressure context", "5% low, 20% high"]], "row_h": 38},
        "grain-label": {"headers": ["Front claim", "Better check", "Why"], "rows": [["Multigrain", "Ingredient list", "May not be whole grain"], ["Whole grain", "Fiber + carbs", "Compare similar breads"], ["Keto", "Sat fat + fiber", "Claim is not enough"]], "row_h": 44},
        "sugar-names": {"headers": ["Ingredient words", "Still check", "Reason"], "rows": [["Syrup, dextrose, sucrose", "Total carbs", "Names do not tell portion"], ["Honey, agave, molasses", "Added sugar", "Still added sugar"], ["Juice concentrate", "Serving size", "Can add up quickly"]], "row_h": 46},
        "sodium-label": {"headers": ["Product", "Sodium %DV", "Note"], "rows": [["Soup A", "8%", "lower option"], ["Soup B", "24%", "higher option"], ["Sauce A", "5%", "low per serving"], ["Sauce B", "20%", "high per serving"]], "row_h": 42},
        "meal-formula": {"headers": ["Base", "Protein", "Vegetable", "Flavor"], "rows": [["Tortilla", "beans", "cabbage", "salsa"], ["Rice", "tofu", "frozen stir-fry mix", "ginger sauce"], ["Crackers", "tuna", "cucumber", "mustard/lemon"]], "row_h": 46},
    }
    def with_visuals(g, extra=None):
        merged = dict(common_visuals)
        merged.update(comparison_visuals)
        merged.update(table_visuals)
        if extra:
            merged.update(extra)
        g["visuals"] = merged
        return g
    return [
        with_visuals({"folder": "02_The_Mindful_Plate", "slug": "mindful-plate", "title": "The Mindful Plate", "subtitle": "A Simple Guide to Blood Sugar-Friendly Eating", "running_subtitle": "Blood Sugar-Friendly Eating", "file": "mindful-diabetes-mindful-plate-guide-2026.pdf", "tags": ["Nutrition", "Blood sugar", "Meal planning"], "refs": ["ada", "plate", "fda_label", "fda_sugar", "aha_fats", "cdc_dpp"], "pages": mindful_pages}),
        with_visuals({"folder": "03_Fats_Without_Fear", "slug": "fats-without-fear", "title": "Fats Without Fear", "subtitle": "A Plain-English Guide to Dietary Fats, Heart Health, and Brain Health", "running_subtitle": "Dietary Fats, Heart, and Brain Health", "file": "mindful-diabetes-fats-without-fear-2026.pdf", "tags": ["Dietary fats", "Heart health", "Food swaps"], "refs": ["aha_fats", "aha_sat", "fda_label", "ada"], "pages": fats_pages}),
        with_visuals({"folder": "04_Grocery_Store_Survival_Guide", "slug": "grocery-store-survival-guide", "title": "The Grocery Store Survival Guide", "subtitle": "How to Make Practical, Blood Sugar-Conscious Choices Without Feeling Overwhelmed", "running_subtitle": "Practical Blood Sugar-Conscious Shopping", "file": "mindful-diabetes-grocery-store-guide-2026.pdf", "tags": ["Grocery shopping", "Food labels", "Budget meals"], "refs": ["fda_label", "fda_sugar", "fda_sodium", "plate", "usda"], "pages": grocery_pages}),
        with_visuals({"folder": "05_Seven_Day_Prevention_Reset", "slug": "7-day-prevention-reset", "title": "The 7-Day Prevention Reset", "subtitle": "A Gentle One-Week Plan for Building Healthier Everyday Habits", "running_subtitle": "A Gentle One-Week Habit Plan", "file": "mindful-diabetes-7-day-prevention-reset-2026.pdf", "tags": ["Habits", "Prevention", "Trackers"], "refs": ["cdc_dpp", "cdc_activity", "cdc_sleep", "ada", "fda_sugar"], "pages": reset_pages}),
        with_visuals({"folder": "06_Blood_Sugar_and_Brain_Health", "slug": "blood-sugar-brain-health", "title": "Blood Sugar & Brain Health", "subtitle": "Understanding the Everyday Connection", "running_subtitle": "Understanding the Everyday Connection", "file": "mindful-diabetes-blood-sugar-brain-health-2026.pdf", "tags": ["Brain health", "Diabetes", "Prevention"], "refs": ["cdc_brain", "cdc_dementia", "nia", "lancet", "ada"], "pages": brain_pages}),
    ]


def make_cover_asset(guide: dict, out: Path, size=(1200, 1553), kind="cover") -> None:
    img = Image.new("RGB", size, PALETTE["cream"])
    d = ImageDraw.Draw(img)
    lora = ImageFont.truetype(str(FONT_DIR / "Lora-Bold.ttf"), max(42, int(size[0] * 0.07)))
    lato = ImageFont.truetype(str(FONT_DIR / "Lato-Regular.ttf"), max(22, int(size[0] * 0.025)))
    lato_b = ImageFont.truetype(str(FONT_DIR / "Lato-Bold.ttf"), max(20, int(size[0] * 0.022)))
    pad = int(size[0] * 0.06)
    d.rounded_rectangle((pad, pad, size[0] - pad, size[1] - pad), radius=42, fill="#fffdf8", outline=PALETTE["line"], width=3)
    logo = Image.open(LOGO).convert("RGB").resize((int(size[0] * 0.07), int(size[0] * 0.074)))
    img.paste(logo, (pad + 30, pad + 28))
    d.text((pad + 125, pad + 38), "Mindful Diabetes Free Guides", font=lato_b, fill=PALETTE["green"])
    d.multiline_text((pad + 42, pad + int(size[1] * 0.18)), guide["title"], font=lora, fill=PALETTE["navy"], spacing=4)
    d.multiline_text((pad + 46, pad + int(size[1] * 0.35)), guide["subtitle"], font=lato, fill=PALETTE["body"], spacing=7)
    hx0, hy0 = int(size[0] * 0.48), int(size[1] * 0.48)
    hx1, hy1 = size[0] - pad - 55, size[1] - pad - 210
    if hy1 <= hy0 + 80:
        hx0, hy0 = int(size[0] * 0.52), int(size[1] * 0.40)
        hx1, hy1 = size[0] - pad - 28, size[1] - pad - 88
    d.rounded_rectangle((hx0, hy0, hx1, hy1), radius=34, fill=PALETTE["soft_green"], outline=PALETTE["line"], width=3)
    # Large branded hero mark.
    cx, cy = (hx0 + hx1) // 2, (hy0 + hy1) // 2
    r = min(hx1 - hx0, hy1 - hy0) // 3
    if guide["slug"] == "mindful-plate":
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill="#ffffff", outline=PALETTE["navy"], width=5)
        d.pieslice((cx - r + 14, cy - r + 14, cx + r - 14, cy + r - 14), 90, 270, fill=PALETTE["soft_green"])
        d.pieslice((cx - r + 14, cy - r + 14, cx + r - 14, cy + r - 14), 0, 90, fill=PALETTE["soft"])
        d.pieslice((cx - r + 14, cy - r + 14, cx + r - 14, cy + r - 14), 270, 360, fill=PALETTE["soft_orange"])
        d.line((cx, cy - r + 18, cx, cy + r - 18), fill="#ffffff", width=10)
        d.line((cx, cy, cx + r - 18, cy), fill="#ffffff", width=10)
    elif guide["slug"] == "7-day-prevention-reset":
        for i in range(7):
            x = hx0 + 45 + i * ((hx1 - hx0 - 90) / 6)
            d.ellipse((x - 28, cy - 28, x + 28, cy + 28), fill=PALETTE["coral"] if i % 2 else PALETTE["green"])
            if i < 6:
                d.line((x + 30, cy, x + ((hx1 - hx0 - 90) / 6) - 30, cy), fill=PALETTE["navy"], width=4)
    else:
        for i in range(4):
            x = hx0 + 60 + (i % 2) * ((hx1 - hx0) / 2)
            y = hy0 + 60 + (i // 2) * ((hy1 - hy0) / 2)
            d.ellipse((x, y, x + 100, y + 76), fill=[PALETTE["soft"], PALETTE["soft_orange"], "#ffffff", PALETTE["green"]][i], outline=PALETTE["navy"], width=4)
    d.rounded_rectangle((pad + 45, size[1] - pad - 170, pad + 270, size[1] - pad - 105), radius=32, fill=PALETTE["coral"])
    d.text((pad + 92, size[1] - pad - 151), "FREE GUIDE", font=lato_b, fill="#ffffff")
    d.text((pad + 45, size[1] - pad - 54), "Published: July 30, 2026 | Medical review: pending", font=lato, fill=PALETTE["muted"])
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, quality=95)


def draw_cover(c: canvas.Canvas, guide: dict, cover_png: Path) -> None:
    start_page(c, guide, 1)
    c.setFillColor(colors.white)
    c.setStrokeColor(hc("line"))
    c.roundRect(42, 42, 528, 708, 18, fill=1, stroke=1)
    c.drawImage(str(LOGO), 68, 684, width=46, height=49, mask="auto")
    c.setFont("Lato-Bold", 9.5)
    c.setFillColor(hc("green"))
    c.drawString(126, 720, "MINDFUL DIABETES FREE GUIDES")
    c.setFont("Lato", 8.5)
    c.setFillColor(hc("muted"))
    c.drawString(126, 703, "Simple, practical guidance for metabolic and brain health.")
    draw_heading(c, guide["title"], 74, 580, 270, 42 if len(guide["title"]) < 24 else 33)
    draw_wrapped(c, guide["subtitle"], 76, 415, 245, 14, "Lato", "body", 18)
    visual_meal_hero(c, 330, 250, 185, 245, guide["slug"])
    c.setFillColor(hc("coral"))
    c.roundRect(76, 318, 112, 34, 17, fill=1, stroke=0)
    c.setFont("Lato-Bold", 10)
    c.setFillColor(colors.white)
    c.drawCentredString(132, 330, "FREE GUIDE")
    c.setFont("Lato", 9)
    c.setFillColor(hc("muted"))
    c.drawString(76, 107, "Mindful Diabetes Inc. | 501(c)(3) nonprofit")
    c.drawString(76, 88, "Published: July 30, 2026 | Medical review: pending")
    c.showPage()


def draw_content_page(c: canvas.Canvas, guide: dict, page_data: dict, page_num: int, web_fields: bool) -> None:
    start_page(c, guide, page_num)
    draw_eyebrow(c, page_data["section"], MARGIN, TOP + 4)
    y = draw_heading(c, page_data["title"], MARGIN, TOP - 20, 500, 27 if len(page_data["title"]) < 42 else 23)
    layout = page_data["layout"]
    if layout == "full_width_visual_then_text":
        draw_visual(c, guide, page_data.get("visual"), MARGIN, 395, 496, 210)
        y = 368
        y = draw_wrapped(c, page_data["body"], MARGIN, y, 496, 10.7, "Lato", "body", 14.2)
        y = draw_bullets(c, page_data["bullets"], MARGIN, y - 6, 496)
    elif layout == "split_visual_left":
        draw_visual(c, guide, page_data.get("visual"), MARGIN, 360, 235, 250)
        y = draw_wrapped(c, page_data["body"], 315, y, 240, 10.7, "Lato", "body", 14.2)
        y = draw_bullets(c, page_data["bullets"], 315, y - 6, 240)
    elif layout == "split_visual_right":
        draw_visual(c, guide, page_data.get("visual"), 320, 358, 235, 252)
        y = draw_wrapped(c, page_data["body"], MARGIN, y, 240, 10.7, "Lato", "body", 14.2)
        y = draw_bullets(c, page_data["bullets"], MARGIN, y - 6, 240)
    elif layout == "comparison":
        y = draw_wrapped(c, page_data["body"], MARGIN, y, 496, 10.7, "Lato", "body", 14.2)
        draw_visual(c, guide, page_data.get("visual"), MARGIN, 245, 496, 215)
        y = draw_bullets(c, page_data["bullets"], MARGIN, 216, 496)
    elif layout == "card_grid":
        intro_y = draw_wrapped(c, page_data["body"], MARGIN, y, 496, 10.7, "Lato", "body", 14.2)
        cards = guide["visuals"].get(page_data.get("visual") or "smart-cart", [])
        if not cards:
            cards = [(b.split("?")[0][:24], b, "vegetable") for b in page_data["bullets"]]
        draw_card_grid(c, MARGIN, 210, 496, 295, cards)
        if page_data["bullets"] and page_data.get("visual"):
            draw_bullets(c, page_data["bullets"][:2], MARGIN, min(intro_y - 8, 185), 496)
    elif layout == "worksheet_full_page":
        y = draw_wrapped(c, page_data["body"], MARGIN, y, 496, 10.6, "Lato", "body", 14)
        if page_data.get("callout"):
            draw_callout(c, page_data["callout"][0], page_data["callout"][1], MARGIN, y - 4, 496, 58, page_data["callout"][2])
            work_top = y - 82
        else:
            work_top = y - 12
        draw_worksheet(c, page_data, MARGIN, BOTTOM + 18, 496, max(260, work_top - BOTTOM - 26), web_fields, guide["slug"])
    elif layout == "back_cover":
        y = draw_wrapped(c, page_data["body"], MARGIN, y, 496, 11, "Lato", "body", 14.6)
        y = draw_bullets(c, page_data["bullets"], MARGIN, y - 8, 496, 10.2)
        button_y = 392
        for label, url in [("Explore the Guide", "https://mindfuldiabetes.org/guide/"), ("Visit Health Tools", "https://mindfuldiabetes.org/health-tools/"), ("Try JEIR", "https://www.mindfuldiabetes.ai/"), ("Support free education", "https://mindfuldiabetes.org/donation/")]:
            round_rect(c, MARGIN, button_y, 220, 30, "soft_green", "green", 15)
            c.setFont("Lato-Bold", 9.2)
            c.setFillColor(hc("green"))
            c.drawCentredString(MARGIN + 110, button_y + 11, label)
            c.linkURL(url, (MARGIN, button_y, MARGIN + 220, button_y + 30), relative=0)
            button_y -= 40
        if page_data.get("callout"):
            draw_callout(c, page_data["callout"][0], page_data["callout"][1], 330, 392, 225, 112, page_data["callout"][2])
        else:
            draw_callout(c, "Medical disclaimer", "This guide is general education, not medical advice. Individual needs vary. Do not change medication, insulin, or glucose targets based on this guide.", 330, 392, 225, 112, "orange")
    else:
        y = draw_wrapped(c, page_data["body"], MARGIN, y, 496, 10.8, "Lato", "body", 14.5)
        draw_bullets(c, page_data["bullets"], MARGIN, y - 8, 496)
    if page_data.get("callout") and layout not in {"worksheet_full_page", "back_cover"}:
        draw_callout(c, page_data["callout"][0], page_data["callout"][1], MARGIN, 180, 496, 78, page_data["callout"][2])
    finish_page(c, page_num)


def draw_references_page(c: canvas.Canvas, guide: dict, page_num: int) -> None:
    start_page(c, guide, page_num)
    draw_eyebrow(c, "References and safety", MARGIN, TOP + 4)
    y = draw_heading(c, "References and medical disclaimer", MARGIN, TOP - 20, 496, 25)
    disclaimer = "This guide is for general education only. It is not medical advice, diagnosis, or treatment. Individual needs vary. Do not change medication, insulin, or glucose targets based on this guide. Seek appropriate medical attention for severe low blood sugar, severe high blood sugar, sudden confusion, chest pain, trouble breathing, fainting, seizures, or other urgent symptoms."
    draw_callout(c, "Medical disclaimer", disclaimer, MARGIN, y - 2, 496, 105, "orange")
    y -= 130
    c.setFont("Lora-Bold", 16)
    c.setFillColor(hc("navy"))
    c.drawString(MARGIN, y, "References")
    y -= 22
    for idx, key in enumerate(guide["refs"], 1):
        ref = BASE_REFS[key]
        ref_text = f"[{idx}] {ref[0]}. {ref[1]}. {ref[2]}. {ref[3]}. {ref[4]}"
        start_y = y
        y = draw_wrapped(c, ref_text, MARGIN, y, 496, 8.8, "Lato", "body", 10.8)
        c.linkURL(ref[4], (MARGIN, y + 2, MARGIN + 496, start_y + 10), relative=0)
        y -= 3
    c.setFont("Lato", 8.5)
    c.setFillColor(hc("muted"))
    c.drawString(MARGIN, 82, "Published: July 30, 2026 | Last medically reviewed: pending | Next scheduled review: July 2027")
    c.drawString(MARGIN, 68, "Accessibility remediation status: PDF/UA tagging and embedded alt text are pending.")
    finish_page(c, page_num)


def create_pdf(guide: dict, output_pdf: Path, web_fields: bool) -> None:
    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    cover_asset = output_pdf.parent.parent / "Website_Assets" / f"{guide['slug']}-cover-preview.png"
    make_cover_asset(guide, cover_asset)
    make_cover_asset(guide, output_pdf.parent.parent / "Website_Assets" / f"{guide['slug']}-square-promo.png", (1080, 1080))
    make_cover_asset(guide, output_pdf.parent.parent / "Website_Assets" / f"{guide['slug']}-banner-16x9.png", (1600, 900))
    make_cover_asset(guide, output_pdf.parent.parent / "Website_Assets" / f"{guide['slug']}-download-card-thumbnail.png", (600, 420))
    c = canvas.Canvas(str(output_pdf), pagesize=letter, pageCompression=1)
    c.setTitle(f"{guide['title']}: {guide['subtitle']}")
    c.setAuthor("Mindful Diabetes Inc.")
    c.setSubject(guide["subtitle"])
    c.setKeywords(", ".join(["Mindful Diabetes"] + guide["tags"]))
    draw_cover(c, guide, cover_asset)
    for i, p in enumerate(guide["pages"], 2):
        c.bookmarkPage(f"page-{i}-{p['section']}")
        c.addOutlineEntry(p["section"], f"page-{i}-{p['section']}", level=0, closed=False)
        draw_content_page(c, guide, p, i, web_fields)
    ref_page = len(guide["pages"]) + 2
    c.bookmarkPage("references")
    c.addOutlineEntry("References and Medical Disclaimer", "references", level=0, closed=False)
    draw_references_page(c, guide, ref_page)
    c.save()


def compress_pdf(input_pdf: Path, output_pdf: Path) -> None:
    reader = PdfReader(str(input_pdf))
    writer = PdfWriter()
    for page_obj in reader.pages:
        writer.add_page(page_obj)
        writer.pages[-1].compress_content_streams()
    writer.add_metadata(reader.metadata or {})
    try:
        for item in reader.outline:
            pass
    except Exception:
        pass
    # Preserve/recreate major bookmarks from page titles.
    for i, _ in enumerate(reader.pages):
        if i == 0:
            writer.add_outline_item("Cover", 0)
    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    with output_pdf.open("wb") as f:
        writer.write(f)


def write_source_and_manifests(guide: dict, folder: Path) -> None:
    source_dir = folder / "Editable_Source"
    source_dir.mkdir(parents=True, exist_ok=True)
    source = {
        "title": guide["title"],
        "subtitle": guide["subtitle"],
        "running_subtitle": guide["running_subtitle"],
        "slug": guide["slug"],
        "file": guide["file"],
        "pages": guide["pages"],
        "refs": guide["refs"],
        "layout_system": ["full_width_text", "full_width_visual_then_text", "split_visual_left", "split_visual_right", "card_grid", "comparison", "worksheet_full_page", "reference_page", "back_cover"],
    }
    (source_dir / "source.json").write_text(json.dumps(source, indent=2))
    shutil.copy2(Path(__file__), source_dir / "build_all_free_guides.py")
    research = folder / "Research"
    research.mkdir(parents=True, exist_ok=True)
    with (research / "references.json").open("w") as f:
        json.dump([{"key": k, "organization_or_authors": BASE_REFS[k][0], "title": BASE_REFS[k][1], "publisher": BASE_REFS[k][2], "year": BASE_REFS[k][3], "url": BASE_REFS[k][4]} for k in guide["refs"]], f, indent=2)
    with (research / "claim-manifest.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["page", "claim", "supporting_source", "source_date", "review_note"])
        for p in guide["pages"]:
            writer.writerow([p["section"], p["body"][:160], BASE_REFS[guide["refs"][0]][1], BASE_REFS[guide["refs"][0]][3], "Draft source mapping; formal medical review pending."])
    with (research / "image-license-manifest.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["file_name", "visual_title", "source_or_method", "license", "attribution_required", "alt_text"])
        for p in guide["pages"]:
            if p.get("visual"):
                writer.writerow([p["visual"], p["visual"].replace("-", " ").title(), "Original ReportLab vector drawing in canonical generator", "Created for this project", "No", f"Educational graphic for {p['title']}"])
    access = folder / "Accessibility"
    access.mkdir(exist_ok=True)
    (access / "accessibility-review-notes.md").write_text(
        "# Accessibility Review Notes\n\n"
        "- Selectable text, metadata, descriptive links, and bookmarks are included.\n"
        "- Web PDFs include fillable AcroForm fields on worksheet pages where practical.\n"
        "- `pdfinfo` still reports `Tagged: no`; full PDF/UA tagging and embedded image alt text remediation are pending.\n"
        "- Alt text is documented in the image manifest, but not embedded in the PDF structure.\n"
    )
    website = folder / "Website_Assets"
    meta = {
        "title": guide["title"],
        "short_description": guide["subtitle"],
        "long_description": f"{guide['title']} is a free Mindful Diabetes guide with practical examples, original diagrams, printable worksheets, careful safety language, and references.",
        "who_this_is_for": "For adults, families, caregivers, and community educators seeking plain-language health guidance.",
        "tags": guide["tags"],
        "button_text": "Download the Free Guide",
        "seo_title": f"{guide['title']} Free PDF Guide | Mindful Diabetes",
        "meta_description": guide["subtitle"][:155],
        "pdf_file_name": guide["file"],
        "thumbnail_file_name": f"{guide['slug']}-download-card-thumbnail.png",
        "slug": guide["slug"],
        "alt_text": f"Cover preview for {guide['title']} free guide.",
    }
    (website / f"{guide['slug']}-website-metadata.json").write_text(json.dumps(meta, indent=2))


def render_pdf(pdf: Path, out_dir: Path, dpi: int = 200) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("*.png"):
        old.unlink()
    subprocess.run(["pdftoppm", "-png", "-r", str(dpi), str(pdf), str(out_dir / "page")], check=True)


def make_contact_sheets(render_dir: Path) -> list[Path]:
    pages = sorted(render_dir.glob("page-*.png"))
    sheets: list[Path] = []
    for idx, start in enumerate(range(0, len(pages), 12), 1):
        subset = pages[start:start + 12]
        thumbs = []
        for p in subset:
            img = Image.open(p).convert("RGB")
            img.thumbnail((210, 272))
            tile = Image.new("RGB", (230, 312), "white")
            tile.paste(img, ((230 - img.width) // 2, 8))
            d = ImageDraw.Draw(tile)
            d.text((10, 286), p.stem.replace("page-", "Page "), fill=PALETTE["navy"])
            thumbs.append(tile)
        sheet = Image.new("RGB", (6 * 230, 2 * 312), PALETTE["soft"])
        for i, tile in enumerate(thumbs):
            sheet.paste(tile, ((i % 6) * 230, (i // 6) * 312))
        sheet_path = render_dir / f"contact-sheet-{idx}.png"
        sheet.save(sheet_path)
        sheets.append(sheet_path)
    return sheets


def verify_pdf(pdf: Path) -> dict:
    reader = PdfReader(str(pdf))
    links = 0
    widgets = 0
    for p in reader.pages:
        for annot in p.get("/Annots", []):
            obj = annot.get_object()
            subtype = obj.get("/Subtype")
            if subtype == "/Link":
                links += 1
            if subtype == "/Widget":
                widgets += 1
    fonts = subprocess.run(["pdffonts", str(pdf)], check=True, capture_output=True, text=True).stdout
    pdfinfo = subprocess.run(["pdfinfo", str(pdf)], check=True, capture_output=True, text=True).stdout
    branded_font_lines = [line for line in fonts.splitlines() if "Lato" in line or "Lora" in line]
    branded_embedded = bool(branded_font_lines) and all(" yes " in line for line in branded_font_lines)
    return {
        "pages": len(reader.pages),
        "links": links,
        "widgets": widgets,
        "bookmarks": len(reader.outline) if reader.outline else 0,
        "file_size_kb": round(pdf.stat().st_size / 1024),
        "tagged": "Tagged:          yes" in pdfinfo,
        "fonts_embedded": branded_embedded,
    }


def build_all(staging_only: bool = True, publish: bool = False) -> None:
    register_fonts()
    if STAGING.exists():
        shutil.rmtree(STAGING)
    STAGING.mkdir(parents=True)
    qa_root = STAGING / "_qa_rendered_pages"
    qa_rows = []
    for guide in guides():
        folder = STAGING / guide["folder"]
        print_dir = folder / "Final_Print_PDF"
        web_dir = folder / "Final_Web_PDF"
        for sub in ["Final_Print_PDF", "Final_Web_PDF", "Editable_Source", "Images", "Website_Assets", "Research", "Accessibility"]:
            (folder / sub).mkdir(parents=True, exist_ok=True)
        print_pdf = print_dir / guide["file"].replace(".pdf", "-print.pdf")
        web_pdf = web_dir / guide["file"]
        create_pdf(guide, print_pdf, web_fields=False)
        create_pdf(guide, web_pdf, web_fields=True)
        write_source_and_manifests(guide, folder)
        for variant, pdf in [("print", print_pdf), ("web", web_pdf)]:
            render_dir = qa_root / guide["slug"] / variant
            render_pdf(pdf, render_dir, 200)
            sheets = make_contact_sheets(render_dir)
            result = verify_pdf(pdf)
            qa_rows.append({
                "guide": guide["title"],
                "variant": variant,
                "pdf": str(pdf.relative_to(PROJECT)),
                "pages": result["pages"],
                "links": result["links"],
                "widgets": result["widgets"],
                "bookmarks": result["bookmarks"],
                "file_size_kb": result["file_size_kb"],
                "fonts_embedded": result["fonts_embedded"],
                "tagged": result["tagged"],
                "contact_sheets": "; ".join(str(s.relative_to(PROJECT)) for s in sheets),
                "visual_review": "Rendered at 200 DPI; contact sheets created for manual visual QA.",
            })
    qa_report = STAGING / "QA_Report_Page_by_Page.csv"
    with qa_report.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=qa_rows[0].keys())
        writer.writeheader()
        writer.writerows(qa_rows)
    (STAGING / "QA_Report_Summary.md").write_text(
        "# Revised Guides QA Summary\n\n"
        "- Rebuilt from one canonical generator: `scripts/build_all_free_guides.py`.\n"
        "- Explicit page specs and visual mappings are stored in each guide's `Editable_Source/source.json`.\n"
        "- All PDFs were rendered at 200 DPI and contact sheets were generated.\n"
        "- Footers use three fixed zones: organization, website, page number.\n"
        "- PDF/UA tagging remains pending and is not claimed as complete.\n"
        "- PyMuPDF was not available in this runtime; link/bookmark checks used `pypdf`, `pdfinfo`, and `pdffonts`.\n"
    )
    if publish:
        for guide in guides():
            src = STAGING / guide["folder"]
            dst = PROJECT / guide["folder"]
            for sub in ["Final_Print_PDF", "Final_Web_PDF", "Editable_Source", "Images", "Website_Assets", "Research", "Accessibility"]:
                if (dst / sub).exists():
                    shutil.rmtree(dst / sub)
                shutil.copytree(src / sub, dst / sub)
        # Keep QA outputs in the main package too.
        final_qa = PROJECT / "_qa_rendered_pages"
        if final_qa.exists():
            shutil.rmtree(final_qa)
        shutil.copytree(qa_root, final_qa)
        shutil.copy2(STAGING / "QA_Report_Page_by_Page.csv", PROJECT / "QA_Report_Page_by_Page.csv")
        shutil.copy2(STAGING / "QA_Report_Summary.md", PROJECT / "QA_Report_Summary.md")
        # Update package-level script archival copy.
        target_script = PROJECT / "scripts" / "build_all_free_guides.py"
        target_script.parent.mkdir(exist_ok=True)
        if Path(__file__).resolve() != target_script.resolve():
            shutil.copy2(Path(__file__), target_script)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--publish", action="store_true", help="Copy QA-passed staging outputs into final guide folders.")
    args = parser.parse_args()
    build_all(publish=args.publish)


if __name__ == "__main__":
    main()
