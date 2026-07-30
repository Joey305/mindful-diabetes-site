from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path

from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "Mindful_Diabetes_Free_Guides"
FONT_DIR = PROJECT / "01_Brand_Assets" / "Fonts_Reference"
LOGO = PROJECT / "01_Brand_Assets" / "Logos" / "mdi-logo.jpg"

COLORS = {
    "navy": "#0d1338",
    "green": "#005030",
    "coral": "#f07239",
    "cream": "#fffaf2",
    "soft": "#f5f7fe",
    "line": "#e4e6ef",
    "body": "#343842",
    "muted": "#6c7280",
}


GUIDES = [
    ("02_The_Mindful_Plate", "The Mindful Plate", "mindful-plate", "mindful-diabetes-mindful-plate-guide-2026.pdf", "Nutrition, Blood sugar, Meal planning"),
    ("03_Fats_Without_Fear", "Fats Without Fear", "fats-without-fear", "mindful-diabetes-fats-without-fear-2026.pdf", "Dietary fats, Heart health, Food swaps"),
    ("04_Grocery_Store_Survival_Guide", "The Grocery Store Survival Guide", "grocery-store-survival-guide", "mindful-diabetes-grocery-store-guide-2026.pdf", "Grocery shopping, Food labels, Budget meals"),
    ("05_Seven_Day_Prevention_Reset", "The 7-Day Prevention Reset", "7-day-prevention-reset", "mindful-diabetes-7-day-prevention-reset-2026.pdf", "Habits, Prevention, Trackers"),
    ("06_Blood_Sugar_and_Brain_Health", "Blood Sugar & Brain Health", "blood-sugar-brain-health", "mindful-diabetes-blood-sugar-brain-health-2026.pdf", "Brain health, Diabetes, Prevention"),
]


def h(name):
    return colors.HexColor(COLORS[name])


def register_fonts():
    for font_name, file_name in {
        "Lato": "Lato-Regular.ttf",
        "Lato-Bold": "Lato-Bold.ttf",
        "Lora-Bold": "Lora-Bold.ttf",
    }.items():
        if font_name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(font_name, str(FONT_DIR / file_name)))


def wrap(text, font, size, width):
    words = text.split()
    lines, current = [], ""
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


def draw_text(c, value, x, y, w, size=10, font="Lato", color="body", leading=None):
    if leading is None:
        leading = size * 1.35
    c.setFont(font, size)
    c.setFillColor(h(color))
    for line in wrap(value, font, size, w):
        c.drawString(x, y, line)
        y -= leading
    return y


def simple_pdf(path: Path, title: str, sections: list[tuple[str, str]]):
    path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(path), pagesize=letter, pageCompression=1)
    c.setTitle(title)
    c.setAuthor("Mindful Diabetes Inc.")
    c.setFillColor(h("cream"))
    c.rect(0, 0, 612, 792, fill=1, stroke=0)
    c.drawImage(str(LOGO), 54, 700, width=42, height=45, mask="auto")
    c.setFont("Lora-Bold", 28)
    c.setFillColor(h("navy"))
    c.drawString(112, 724, title)
    y = 666
    for heading, body in sections:
        c.setFont("Lora-Bold", 15)
        c.setFillColor(h("green"))
        c.drawString(72, y, heading)
        y -= 22
        y = draw_text(c, body, 72, y, 468, 10.2, "Lato", "body", 13)
        y -= 14
        if y < 80:
            c.showPage()
            c.setFillColor(h("cream"))
            c.rect(0, 0, 612, 792, fill=1, stroke=0)
            y = 700
    c.save()


def load_metadata(folder_name: str, slug: str) -> dict:
    folder = PROJECT / folder_name / "Website_Assets"
    matches = list(folder.glob(f"{slug}*website-metadata.json"))
    if matches:
        return json.loads(matches[0].read_text())
    return {}


def main():
    register_fonts()
    for folder in [
        "00_README_FIRST",
        "01_Brand_Assets/Color_Palette",
        "01_Brand_Assets/Icons",
        "01_Brand_Assets/Templates",
        "07_Resource_Page/Download_Cards",
        "08_Shared_Research/Source_Library",
        "08_Shared_Research/Research_Notes",
        "09_Licensing_and_Permissions/Permissions",
    ]:
        (PROJECT / folder).mkdir(parents=True, exist_ok=True)

    # README-FIRST PDF.
    simple_pdf(
        PROJECT / "00_README_FIRST" / "README_FIRST.pdf",
        "README First",
        [
            ("What this package contains", "Five Mindful Diabetes Free Guides in print and web PDF versions, editable source files, generated visual assets, website assets, research manifests, accessibility notes, and licensing documentation."),
            ("Where final PDFs are located", "Each guide folder contains `Final_Print_PDF` and `Final_Web_PDF`. Web PDFs use the public file names intended for download cards. Print PDFs include `-print` in the file name."),
            ("Editable source", "Editable source is stored in each guide's `Editable_Source` folder. The current editable format is Python/JSON production source plus original image assets. This preserves the complete layout and content generation path."),
            ("Logo and fonts", "The active Mindful Diabetes logo from `static/img/mdi-logo.jpg` is used. Headings use Lora. Body text uses Lato. Font files are included under `01_Brand_Assets/Fonts_Reference`."),
            ("Review dates", "Published: July 30, 2026. Last medically reviewed: pending. Next scheduled review: July 2027, or earlier if ADA, CDC, AHA, FDA, USDA, or federal guidance changes."),
            ("Accessibility status", "The PDFs include selectable text, metadata, descriptive links, bookmarks, and documented alt text. Full PDF/UA tagging should be completed in a dedicated remediation tool before broad clinical distribution."),
            ("Recommended upload order", "Upload web PDFs first, then cover previews and thumbnails, then create the Free Health Resources page, then connect analytics tracking on download/open/share/newsletter/donation events."),
        ],
    )

    simple_pdf(
        PROJECT / "00_README_FIRST" / "Brand_Summary.pdf",
        "Brand Summary",
        [
            ("Visual direction", "Warm Editorial Guide Series covers paired with practical information-design interiors. The look should feel calm, trustworthy, human, and connected to mindfuldiabetes.org."),
            ("Core colors", "Navy #0d1338, forest green #005030, coral-orange #f07239, cream #fffaf2, soft green #f0faf5, soft blue-white #f5f7fe, and neutral gray for secondary text."),
            ("Typography", "Lora is used for editorial headings. Lato is used for body copy, labels, captions, buttons, page numbers, and references."),
            ("Logo use", "Use the active square Mindful Diabetes logo without stretching, recoloring, cropping, or placing it on a visually busy background."),
        ],
    )

    simple_pdf(
        PROJECT / "00_README_FIRST" / "Publication_Checklist.pdf",
        "Publication Checklist",
        [
            ("Before upload", "Confirm the latest PDF version number, publication date, medical-review status, links, file names, and page count."),
            ("Medical review", "A qualified clinician, registered dietitian, diabetes educator, or appropriate reviewer should review each guide before broad clinical or partner distribution."),
            ("Technical review", "Open each PDF on desktop and mobile, print a worksheet page, check links, verify file size, and confirm no text or graphics are clipped."),
            ("Website review", "Confirm download buttons are keyboard-accessible, have descriptive alt text, and include analytics data attributes without personal health information."),
        ],
    )

    wb = Workbook()
    ws = wb.active
    ws.title = "Guides"
    ws.append(["Guide", "Folder", "Slug", "Web PDF", "Topics", "Published", "Medical Review", "Next Review"])
    for folder, title, slug, file_name, tags in GUIDES:
        ws.append([title, folder, slug, file_name, tags, "2026-07-30", "Pending", "2027-07-30"])
    wb.save(PROJECT / "00_README_FIRST" / "Project_Manifest.xlsx")

    # Resource page content.
    page_copy = [
        "# Free Health Resources",
        "",
        "Practical guidance should be easy to understand and easy to access. These free Mindful Diabetes guides turn complicated health topics into clear explanations, everyday examples, and printable tools.",
        "",
        "These resources are for general education. They do not replace medical care, personalized nutrition advice, medication guidance, or urgent medical attention.",
        "",
    ]
    seo_rows = []
    for folder, title, slug, file_name, tags in GUIDES:
        meta = load_metadata(folder, slug)
        page_copy += [
            f"## {title}",
            "",
            meta.get("short_description", ""),
            "",
            f"Who this is for: {meta.get('who_this_is_for', '')}",
            "",
            f"Topics: {', '.join(meta.get('tags', tags.split(', ')))}",
            "",
            f"Suggested button: {meta.get('button_text', 'Download the Free Guide')}",
            "",
        ]
        seo_rows.append({
            "title": title,
            "slug": slug,
            "seo_title": meta.get("seo_title", f"{title} Free PDF Guide | Mindful Diabetes"),
            "meta_description": meta.get("meta_description", ""),
            "pdf_file_name": file_name,
            "thumbnail_file_name": meta.get("thumbnail_file_name", f"{slug}-download-card-thumbnail.png"),
            "tags": tags,
        })
        thumb = PROJECT / folder / "Website_Assets" / f"{slug}-download-card-thumbnail.png"
        if thumb.exists():
            shutil.copy2(thumb, PROJECT / "07_Resource_Page" / "Download_Cards" / thumb.name)
    (PROJECT / "07_Resource_Page" / "Page_Copy.md").write_text("\n".join(page_copy))

    with (PROJECT / "07_Resource_Page" / "SEO_Metadata.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=seo_rows[0].keys())
        writer.writeheader()
        writer.writerows(seo_rows)

    (PROJECT / "07_Resource_Page" / "Analytics_Event_Specification.md").write_text(
        "# Analytics Event Specification\n\n"
        "Use non-identifying analytics only. Do not collect personal health information.\n\n"
        "Recommended events:\n"
        "- `resource_card_view`\n"
        "- `resource_pdf_download`\n"
        "- `resource_pdf_open`\n"
        "- `resource_share_click`\n"
        "- `resource_newsletter_click`\n"
        "- `resource_donation_click`\n\n"
        "Recommended fields: `guide_title`, `guide_slug`, `resource_page_url`, `referring_page`, `button_position`, `device_category`, `download_format`, `timestamp`.\n"
    )

    simple_pdf(
        PROJECT / "07_Resource_Page" / "Page_Layout_Specification.pdf",
        "Free Health Resources Page Layout",
        [
            ("Hero", "Use a clear heading, one short paragraph, and a restrained CTA to browse the guide cards. Avoid a marketing-heavy landing page."),
            ("Guide cards", "Use five download cards with cover preview, title, one-sentence description, page count, tags, review date, and accessible download button."),
            ("Trust and safety", "Include a concise medical disclaimer, publication dates, and a note that guides are educational and not personalized care."),
            ("Secondary CTAs", "Add newsletter, Health Tools, volunteer, and support links below the guide cards so education remains primary."),
        ],
    )

    (PROJECT / "08_Shared_Research" / "Citation_Library.bib").write_text(
        "@misc{ada2026standards, title={Standards of Care in Diabetes - 2026}, author={{American Diabetes Association}}, year={2026}, url={https://diabetesjournals.org/care/issue/49/Supplement_1}}\n"
        "@misc{fdaNutritionFacts, title={How to Understand and Use the Nutrition Facts Label}, author={{U.S. Food and Drug Administration}}, year={2024}, url={https://www.fda.gov/food/nutrition-facts-label/how-understand-and-use-nutrition-facts-label}}\n"
        "@misc{cdcBrainDiabetes, title={Your Brain and Diabetes}, author={{Centers for Disease Control and Prevention}}, year={2024}, url={https://www.cdc.gov/diabetes/diabetes-complications/effects-of-diabetes-brain.html}}\n"
        "@article{lancetDementia2024, title={Dementia prevention, intervention, and care: 2024 report of the Lancet standing Commission}, author={Livingston, Gill and others}, journal={The Lancet}, year={2024}, url={https://chronicdisease.org/wp-content/uploads/2024/12/Lancet-2024.pdf}}\n"
    )
    (PROJECT / "08_Shared_Research" / "Research_Notes" / "source-inventory.md").write_text(
        "# Source Inventory\n\nPrimary sources include ADA Standards of Care 2026, ADA Diabetes Plate guidance, FDA Nutrition Facts Label materials, AHA dietary fat guidance, CDC diabetes/brain health materials, CDC National Diabetes Prevention Program materials, NIA cognitive health materials, USDA MyPlate, and the 2024 Lancet Commission report on dementia prevention.\n"
    )
    (PROJECT / "09_Licensing_and_Permissions" / "Attributions.md").write_text(
        "# Attributions\n\n- Mindful Diabetes logo: supplied site asset, used as organizational branding.\n- Lato and Lora: open-source Google Fonts/OFL family files used for embedded typography.\n- Guide visuals and website promotional images: original generated production assets created for this project.\n- No web-search images were used in the PDFs.\n"
    )
    print("created shared package assets")


if __name__ == "__main__":
    main()
