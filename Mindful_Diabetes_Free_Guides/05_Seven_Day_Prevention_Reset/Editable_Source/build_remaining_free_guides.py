from __future__ import annotations

import csv
import json
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
FONT_DIR = PROJECT / "01_Brand_Assets" / "Fonts_Reference"
LOGO = PROJECT / "01_Brand_Assets" / "Logos" / "mdi-logo.jpg"

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


def h(name: str):
    return colors.HexColor(COLORS[name])


def register_fonts() -> None:
    for font_name, file_name in {
        "Lato": "Lato-Regular.ttf",
        "Lato-Bold": "Lato-Bold.ttf",
        "Lora": "Lora-Regular.ttf",
        "Lora-Bold": "Lora-Bold.ttf",
    }.items():
        if font_name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(font_name, str(FONT_DIR / file_name)))


def pil_font(file_name: str, size: int):
    return ImageFont.truetype(str(FONT_DIR / file_name), size=size)


def wrap(text: str, font: str, size: float, width: float) -> list[str]:
    words = text.split()
    lines = []
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


def text(c, text_value, x, y, w, size=10.4, font="Lato", color="body", leading=None):
    if leading is None:
        leading = size * 1.35
    c.setFont(font, size)
    c.setFillColor(h(color))
    for line in wrap(text_value, font, size, w):
        c.drawString(x, y, line)
        y -= leading
    return y


def heading(c, text_value, x, y, w, size=28):
    c.setFont("Lora-Bold", size)
    c.setFillColor(h("navy"))
    for line in wrap(text_value, "Lora-Bold", size, w):
        c.drawString(x, y, line)
        y -= size * 1.12
    return y - 4


def eyebrow(c, value, x, y):
    c.setFont("Lato-Bold", 8.4)
    c.setFillColor(h("coral"))
    c.drawString(x, y, value.upper())


def bullets(c, items, x, y, w):
    for item in items:
        c.setFillColor(h("green"))
        c.circle(x + 4, y + 3, 2, fill=1, stroke=0)
        y = text(c, item, x + 15, y, w - 15, 9.8, "Lato", "body", 12.8)
        y -= 4
    return y


def callout(c, title, body, x, y, w, height, tone="green"):
    fill = "soft_green" if tone == "green" else "soft_orange"
    stroke = "green" if tone == "green" else "coral"
    c.setFillColor(h(fill))
    c.setStrokeColor(h(stroke))
    c.roundRect(x, y - height, w, height, 8, fill=1, stroke=1)
    c.setFont("Lato-Bold", 9.2)
    c.setFillColor(h(stroke))
    c.drawString(x + 12, y - 21, title)
    text(c, body, x + 12, y - 39, w - 24, 8.8, "Lato", "body", 11.4)


def draw_page_base(c, guide, page_num, section):
    c.setFillColor(h("cream"))
    c.rect(0, 0, 612, 792, fill=1, stroke=0)
    if page_num > 1:
        c.drawImage(str(LOGO), 54, 724, width=28, height=30, mask="auto")
        c.setFont("Lora-Bold", 10)
        c.setFillColor(h("navy"))
        c.drawString(90, 742, guide["title"])
        c.setFont("Lato", 8)
        c.setFillColor(h("muted"))
        c.drawString(90, 729, guide["subtitle"])
        c.setStrokeColor(h("line"))
        c.line(54, 716, 558, 716)


def finish_page(c, guide, page_num, section):
    if page_num > 1:
        c.setStrokeColor(h("line"))
        c.line(54, 40, 558, 40)
        c.setFont("Lato", 8)
        c.setFillColor(h("muted"))
        c.drawString(54, 25, "Mindful Diabetes Inc. | Free Guides | mindfuldiabetes.org")
        c.drawCentredString(306, 25, section[:24])
        c.setFont("Lato-Bold", 9)
        c.setFillColor(h("coral"))
        c.drawRightString(558, 25, str(page_num))
    c.showPage()


def make_tile_asset(path: Path, title_value: str, labels: list[str], accent="green") -> None:
    img = Image.new("RGB", (1800, 1200), COLORS["cream"])
    d = ImageDraw.Draw(img)
    lora = pil_font("Lora-Bold.ttf", 72)
    lato = pil_font("Lato-Regular.ttf", 34)
    lato_b = pil_font("Lato-Bold.ttf", 42)
    d.text((90, 70), title_value, font=lora, fill=COLORS["navy"])
    for i, label in enumerate(labels):
        x = 120 + (i % 4) * 410
        y = 260 + (i // 4) * 370
        fill = [COLORS["soft_green"], COLORS["soft"], COLORS["soft_orange"], "#f8f4ff"][i % 4]
        d.rounded_rectangle((x, y, x + 330, y + 260), radius=28, fill=fill, outline=COLORS["line"], width=3)
        d.ellipse((x + 34, y + 34, x + 104, y + 104), fill=COLORS[accent], outline=COLORS["navy"], width=3)
        d.text((x + 34, y + 130), label, font=lato_b if len(label) < 20 else lato, fill=COLORS["navy"], spacing=4)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, quality=95)


def make_tracker_asset(path: Path, title_value: str, columns: list[str]) -> None:
    img = Image.new("RGB", (1800, 1200), "#ffffff")
    d = ImageDraw.Draw(img)
    lora = pil_font("Lora-Bold.ttf", 72)
    lato_b = pil_font("Lato-Bold.ttf", 34)
    d.text((90, 70), title_value, font=lora, fill=COLORS["navy"])
    x0, y0 = 110, 230
    cell_w, cell_h = 240, 95
    for i, col in enumerate(columns):
        x = x0 + i * cell_w
        d.rounded_rectangle((x, y0, x + cell_w - 14, y0 + 70), radius=18, fill=COLORS["soft_green"], outline=COLORS["line"], width=2)
        d.text((x + 24, y0 + 18), col, font=lato_b, fill=COLORS["green"])
    for row in range(1, 8):
        y = y0 + 80 + row * cell_h
        for i in range(len(columns)):
            x = x0 + i * cell_w
            d.rounded_rectangle((x, y, x + cell_w - 14, y + cell_h - 18), radius=14, fill=COLORS["soft"], outline=COLORS["line"], width=2)
            d.rectangle((x + 22, y + 24, x + 52, y + 54), outline=COLORS["green"], width=3)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, quality=95)


def make_website_assets(guide, folder: Path):
    folder.mkdir(parents=True, exist_ok=True)
    logo = Image.open(LOGO).convert("RGB").resize((72, 76))
    lora_big = pil_font("Lora-Bold.ttf", 66)
    lora_med = pil_font("Lora-Bold.ttf", 42)
    lato = pil_font("Lato-Regular.ttf", 28)
    lato_b = pil_font("Lato-Bold.ttf", 24)

    for name, size in [
        ("cover-preview", (1200, 1553)),
        ("square-promo", (1080, 1080)),
        ("banner-16x9", (1600, 900)),
        ("download-card-thumbnail", (600, 420)),
    ]:
        img = Image.new("RGB", size, COLORS["cream"])
        d = ImageDraw.Draw(img)
        pad = max(28, int(size[0] * 0.055))
        d.rounded_rectangle((pad, pad, size[0] - pad, size[1] - pad), radius=34, fill="#fffdf8", outline=COLORS["line"], width=3)
        img.paste(logo, (pad + 32, pad + 32))
        d.text((pad + 125, pad + 42), "Mindful Diabetes Free Guides", font=lato_b, fill=COLORS["green"])
        title_font = lora_big if size[0] > 700 else lora_med
        d.text((pad + 45, pad + 175), guide["title"], font=title_font, fill=COLORS["navy"], spacing=4)
        d.text((pad + 48, pad + 330 if size[1] > 600 else pad + 250), guide["subtitle"], font=lato, fill=COLORS["body"], spacing=5)
        x1 = size[0] - pad - 280
        y1 = size[1] - pad - 280
        d.ellipse((x1, y1, x1 + 210, y1 + 210), fill=COLORS["soft_green"], outline=COLORS["navy"], width=4)
        d.line((x1 + 105, y1 + 20, x1 + 105, y1 + 190), fill="#ffffff", width=8)
        d.line((x1 + 105, y1 + 105, x1 + 190, y1 + 105), fill="#ffffff", width=8)
        d.rounded_rectangle((pad + 50, size[1] - pad - 110, pad + 300, size[1] - pad - 56), radius=27, fill=COLORS["coral"])
        d.text((pad + 82, size[1] - pad - 96), "Free PDF", font=lato_b, fill="#ffffff")
        img.save(folder / f"{guide['slug']}-{name}.png", quality=95)


def page_data():
    return [
        {
            "folder": "03_Fats_Without_Fear",
            "slug": "fats-without-fear",
            "file": "mindful-diabetes-fats-without-fear-2026.pdf",
            "title": "Fats Without Fear",
            "subtitle": "A Plain-English Guide to Dietary Fats, Heart Health, and Brain Health",
            "accent": "coral",
            "description": "A clear, nonjudgmental guide to saturated, unsaturated, and trans fats, with practical swaps for everyday meals.",
            "who": "For readers confused by fat advice who want heart-conscious choices without food fear.",
            "tags": ["Dietary fats", "Heart health", "Food swaps"],
            "refs": [
                ("American Heart Association", "Fats in Foods", "2026", "https://www.heart.org/en/healthy-living/healthy-eating/eat-smart/fats/fats-in-foods"),
                ("American Heart Association", "Saturated Fats", "2024", "https://www.heart.org/en/healthy-living/healthy-eating/eat-smart/fats/saturated-fats"),
                ("American Heart Association", "Diet and Lifestyle Recommendations", "2026", "https://www.heart.org/en/healthy-living/healthy-eating/eat-smart/nutrition-basics/aha-diet-and-lifestyle-recommendations"),
                ("U.S. Food and Drug Administration", "How to Understand and Use the Nutrition Facts Label", "2024", "https://www.fda.gov/food/nutrition-facts-label/how-understand-and-use-nutrition-facts-label"),
                ("American Diabetes Association", "Standards of Care in Diabetes - 2026", "2026", "https://diabetesjournals.org/care/issue/49/Supplement_1"),
            ],
            "visuals": [
                ("cover-foods", "Fats in everyday foods", ["olive oil", "nuts", "fish", "avocado", "butter", "fried foods", "seeds", "labels"]),
                ("fat-family-tree", "The fat family tree", ["saturated", "monounsaturated", "polyunsaturated", "trans fat", "omega-3", "omega-6", "food source", "pattern"]),
                ("replacement-pathway", "Replacement matters", ["less often", "swap", "replace", "pattern", "LDL", "heart", "brain", "daily meals"]),
                ("oil-chart", "Cooking oil comparison", ["olive", "canola", "soybean", "sunflower", "avocado", "corn", "peanut", "tropical oils"]),
                ("food-source-chart", "Food sources of fats", ["nuts", "seeds", "fish", "avocado", "dairy", "meat", "baked foods", "fried foods"]),
                ("label-annotation", "Read the fat line", ["serving size", "total fat", "saturated fat", "trans fat", "%DV", "ingredients", "portion", "context"]),
                ("swap-ladder", "Swap ladder", ["breakfast", "lunch", "dinner", "snack", "cook", "spread", "crunch", "flavor"]),
                ("planner", "Personal fat-swap planner", ["meal", "current choice", "possible swap", "why", "budget", "taste", "repeat", "notes"]),
            ],
            "pages": [
                ("Welcome", "Fat is not something to fear. Your body needs fat, and food would be dull without it. The useful question is not whether fat is allowed, but which foods show up most often and what they replace.", ["Use this guide to spot fat types, read labels, and try one swap at a time.", "If you have pancreatitis, gallbladder disease, kidney disease, high triglycerides, or a prescribed diet, ask for individual advice."]),
                ("What dietary fat does", "Fat helps build cell membranes, carries flavor, supports fullness, and helps the body absorb vitamins A, D, E, and K. It also provides more energy per gram than carbohydrate or protein, so portions can add up quickly without being wrong.", ["Food source matters more than one isolated number.", "Nuts, oils, fish, dairy, meats, and fried foods are not nutritionally identical."]),
                ("The main fat types", "Saturated, monounsaturated, polyunsaturated, and trans fats behave differently in the body. The American Heart Association recommends limiting saturated fat and avoiding trans fat, while choosing unsaturated fats in place of saturated fat when possible. [1]", ["Saturated fats are common in butter, cheese, fatty meats, and tropical oils.", "Unsaturated fats are common in non-tropical liquid oils, nuts, seeds, avocado, and fish."]),
                ("Why replacement matters", "A lower-saturated-fat pattern works best when saturated fat is replaced by unsaturated fat sources, vegetables, beans, fruit, and whole grains, not simply by refined starches or added sugar. [3]", ["Swap butter for olive oil in a recipe where the flavor still works.", "Add beans or fish more often instead of making every meal meat-centered."]),
                ("LDL, HDL, and triglycerides", "LDL cholesterol is often called 'bad' cholesterol because higher levels can contribute to plaque in arteries. HDL and triglycerides are also part of cardiovascular risk, but no single number tells the whole story.", ["Ask your clinician what your personal numbers mean.", "Do not start supplements for cholesterol or triglycerides without guidance."]),
                ("Cooking oils", "Non-tropical liquid plant oils such as olive, canola, soybean, sunflower, avocado, corn, and peanut oils are generally useful options. Coconut and palm oils are higher in saturated fat and should not be treated as miracle foods. [2]", ["Choose an oil that fits the recipe and budget.", "Use measured amounts when portions are a concern."]),
                ("Nuts, seeds, and avocado", "These foods can add unsaturated fats, fiber, minerals, texture, and satisfaction. They are calorie-dense, which is a neutral fact, not a moral warning.", ["Try peanuts, walnuts, sunflower seeds, pumpkin seeds, chia, flax, or avocado.", "Buy small bags or store-brand options if cost matters."]),
                ("Fish and omega-3 fats", "Fish can be a useful protein source and fatty fish provides omega-3 fats. Eating fish is different from assuming everyone needs an omega-3 supplement.", ["Canned salmon, sardines, or tuna may be budget options.", "Pregnancy, allergies, mercury concerns, and medications require individualized advice."]),
                ("Butter, cheese, and dairy", "Butter, cream, cheese, and many full-fat dairy foods can be higher in saturated fat. You do not have to ban them, but it helps to notice frequency and portion.", ["Use strong flavors in smaller amounts.", "Try yogurt, lower-fat dairy, or plant options when they fit your needs."]),
                ("Coconut and palm oils", "Natural does not automatically mean heart-supportive. Coconut and palm oils are plant-based but still high in saturated fat. [2]", ["Use them less often if LDL cholesterol is a concern.", "Avoid miracle-food claims."]),
                ("Fried and ultra-processed foods", "Fried foods and many packaged snacks can combine refined starch, sodium, saturated fat, and large portions. The issue is the pattern, not a single food.", ["Choose less often, share a portion, or pair with vegetables.", "Read labels on packaged foods."]),
                ("Reading the label", "The Nutrition Facts label lists total fat, saturated fat, trans fat, serving size, and Percent Daily Value. The FDA notes that 5% DV or less is low and 20% DV or more is high for a nutrient. [4]", ["Start with serving size.", "Compare saturated fat across similar foods."]),
                ("Breakfast swaps", "A swap should still taste like breakfast. Try avocado on toast instead of butter sometimes, plain yogurt with nuts instead of sweetened pastry, or eggs with vegetables instead of a fried-meat side.", ["Keep one familiar food.", "Change the fat source or add fiber."]),
                ("Lunch and dinner swaps", "Try beans, fish, tofu, or lean poultry more often. Use olive oil vinaigrette instead of creamy dressing sometimes. Add vegetables before deciding you need a bigger entree.", ["Swap frequency, not identity.", "Make the meal satisfying enough to repeat."]),
                ("Snack swaps", "For crunch, try nuts, roasted chickpeas, popcorn, vegetables with hummus, or whole-grain crackers with tuna. For sweet snacks, pair fruit with yogurt, nuts, or nut butter.", ["Portions matter because fats are dense.", "Planned snacks can prevent grazing for some people."]),
                ("Budget-friendly fats", "Healthy fat choices do not have to be expensive. Peanuts, sunflower seeds, canola oil, canned fish, eggs, and store-brand nut butters can all fit.", ["Buy what you will actually use.", "Avoid letting premium wellness foods define health."]),
                ("Myths", "Fat-free does not always mean healthier, keto does not automatically mean heart-supportive, and coconut oil is not a cure-all. Food choices work through patterns over time.", ["Look past front-package claims.", "Use your lab numbers and clinician guidance."]),
                ("Personal swap planner", "Choose one meal where a fat swap feels realistic. Write the current choice, one possible replacement, cost, taste, and whether you would repeat it.", ["A good swap is one you can live with.", "One repeatable change beats ten abandoned ideas."]),
            ],
        },
        {
            "folder": "04_Grocery_Store_Survival_Guide",
            "slug": "grocery-store-survival-guide",
            "file": "mindful-diabetes-grocery-store-guide-2026.pdf",
            "title": "The Grocery Store Survival Guide",
            "subtitle": "How to Make Practical, Blood Sugar-Conscious Choices Without Feeling Overwhelmed",
            "accent": "green",
            "description": "A practical shopping guide for labels, budget choices, pantry foods, drinks, snacks, and fast meal formulas.",
            "who": "For anyone who wants to shop with less overwhelm and more confidence.",
            "tags": ["Grocery shopping", "Food labels", "Budget meals"],
            "refs": [
                ("U.S. Food and Drug Administration", "How to Understand and Use the Nutrition Facts Label", "2024", "https://www.fda.gov/food/nutrition-facts-label/how-understand-and-use-nutrition-facts-label"),
                ("U.S. Food and Drug Administration", "Added Sugars on the Nutrition Facts Label", "2026", "https://www.fda.gov/food/nutrition-facts-label/added-sugars-nutrition-facts-label"),
                ("U.S. Food and Drug Administration", "Sodium in Your Diet", "2024", "https://www.fda.gov/food/nutrition-education-resources-materials/sodium-your-diet"),
                ("American Diabetes Association", "What is the Diabetes Plate?", "2026", "https://diabetesfoodhub.org/blog/what-diabetes-plate"),
                ("USDA", "MyPlate.gov", "2026", "https://www.myplate.gov/"),
            ],
            "visuals": [
                ("cover-cart", "A smarter grocery cart", ["produce", "protein", "fiber carbs", "healthy fats", "flavor", "freezer", "pantry", "drinks"]),
                ("five-part-cart", "The five-part cart formula", ["vegetables", "protein", "carbs", "fats", "flavor", "freezer", "pantry", "backup"]),
                ("fresh-frozen-canned", "Fresh, frozen, canned, dried", ["fresh", "frozen", "canned", "dried", "rinse", "compare", "store", "use"]),
                ("protein-map", "Protein choices", ["eggs", "beans", "tofu", "fish", "chicken", "yogurt", "nuts", "lentils"]),
                ("label-map", "Nutrition Facts map", ["serving", "carbs", "fiber", "added sugar", "sodium", "sat fat", "%DV", "ingredients"]),
                ("sugar-names", "Added sugar names", ["syrup", "dextrose", "sucrose", "honey", "molasses", "juice concentrate", "maltose", "agave"]),
                ("meal-formula", "Ten-minute meal formula", ["base", "protein", "vegetable", "flavor", "heat", "assemble", "leftovers", "pack"]),
                ("checklist", "Printable grocery checklist", ["produce", "protein", "carbs", "fats", "drinks", "snacks", "pantry", "notes"]),
            ],
            "pages": [
                ("Before you shop", "A good grocery trip starts before the store. Check what you already have, choose two or three meals, and pick backup foods for busy days.", ["You do not need a perfect list.", "A short list you use is better than an ideal list left at home."]),
                ("The five-part cart", "Build around vegetables, protein, fiber-rich carbohydrates, healthy fats, and flavor builders. This keeps shopping practical without depending on one brand or diet plan.", ["Fresh, frozen, canned, and dried foods can all fit.", "Perimeter-only shopping misses many useful budget foods."]),
                ("Produce", "Choose vegetables and fruits you will actually eat. Fresh produce is wonderful, but it is not the only way to eat well.", ["Pre-cut vegetables can save energy.", "Frozen vegetables may reduce waste."]),
                ("Frozen foods", "Frozen vegetables and fruit can be affordable, quick, and nutritious. Look for options without heavy sauces or added sugars when possible.", ["Frozen berries work in yogurt or oats.", "Frozen greens can disappear into soups and eggs."]),
                ("Canned foods", "Canned beans, tuna, salmon, vegetables, tomato products, and soups can help on low-energy days. Rinsing canned beans or vegetables can lower sodium.", ["Compare labels when you can.", "Keep emergency meals in the pantry."]),
                ("Protein choices", "Protein can come from eggs, fish, poultry, lean meat, tofu, tempeh, yogurt, cottage cheese, beans, lentils, nuts, and seeds.", ["Beans and lentils also contain carbohydrate.", "Choose based on budget, culture, and medical needs."]),
                ("Plant proteins", "Beans, lentils, tofu, tempeh, and edamame can support filling meals. They are useful in soups, tacos, bowls, stir-fries, curries, and salads.", ["Seasoning matters.", "Start with canned beans if dried beans feel like too much."]),
                ("Breads and grains", "Look for grains and breads that bring fiber and fit your glucose plan. Whole grain, serving size, and total carbohydrate are more useful than marketing claims alone.", ["Multigrain does not always mean whole grain.", "Compare fiber and total carbohydrate."]),
                ("Dairy and alternatives", "Milk and yogurt contain carbohydrate. Plain yogurt, unsweetened fortified soy milk, and lower-sugar options may fit many plans, but allergies and preferences vary.", ["Check added sugar.", "Choose what fits your taste and budget."]),
                ("Snacks", "A snack can be planned or it can become accidental grazing. Pair protein or fat with fiber when you want something that lasts longer.", ["Fruit with nuts.", "Hummus with vegetables.", "Yogurt with berries."]),
                ("Drinks", "Sweet drinks can add sugar quickly. Start by improving one drink you have often rather than overhauling every beverage.", ["Water, unsweet tea, sparkling water, or smaller sweet drinks can all be steps.", "Alcohol needs medication and safety awareness."]),
                ("Nutrition Facts label", "Start with serving size, then check total carbohydrate, fiber, added sugar, saturated fat, and sodium. Percent Daily Value helps compare nutrients. [1]", ["5% DV is low and 20% DV is high.", "Serving size is not a personal portion prescription."]),
                ("Carbs and added sugar", "Total carbohydrate includes starches, fiber, sugars, and added sugars. Added sugars are added during processing or packaging, while naturally occurring sugars can be found in fruit and milk. [2]", ["Total carbohydrate matters for glucose.", "Added sugar helps you judge food quality."]),
                ("Fiber", "Fiber can support fullness and steadier meals. The Nutrition Facts label lists dietary fiber in grams and Percent Daily Value.", ["Compare similar products.", "Increase fiber gradually."]),
                ("Sodium", "The FDA Daily Value for sodium is less than 2,300 mg per day. Many packaged foods vary widely, so comparing labels can help. [3]", ["5% DV or less is low.", "20% DV or more is high."]),
                ("Ingredient lists and claims", "Front labels can be useful, but they are not the whole story. Natural, keto, diabetic-friendly, low-fat, sugar-free, and no sugar added still deserve a label check.", ["Net carbs are not regulated the same way on every label.", "Sugar-free does not always mean carbohydrate-free."]),
                ("Budget strategies", "Use store brands, frozen vegetables, canned beans, oats, eggs, lentils, rice, seasonal produce, and planned leftovers.", ["Shop your kitchen first.", "Let budget be part of the plan, not a source of shame."]),
                ("Ten-minute meals", "Fast meals can still have structure: heat a base, add protein, add vegetables, add flavor, and choose a drink.", ["Beans, salsa, greens, and tortillas.", "Frozen vegetables, tofu, sauce, and rice."]),
            ],
        },
        {
            "folder": "05_Seven_Day_Prevention_Reset",
            "slug": "7-day-prevention-reset",
            "file": "mindful-diabetes-7-day-prevention-reset-2026.pdf",
            "title": "The 7-Day Prevention Reset",
            "subtitle": "A Gentle One-Week Plan for Building Healthier Everyday Habits",
            "accent": "green",
            "description": "A gentle seven-day habit guide for meals, drinks, movement, sleep, tracking, and next-week planning.",
            "who": "For readers who want a realistic one-week starting point without a crash diet or cleanse.",
            "tags": ["Habits", "Prevention", "Trackers"],
            "refs": [
                ("Centers for Disease Control and Prevention", "National Diabetes Prevention Program", "2024", "https://www.cdc.gov/diabetes-prevention/programs/what-is-the-national-dpp.html"),
                ("Centers for Disease Control and Prevention", "Get Active", "2024", "https://www.cdc.gov/diabetes/living-with/physical-activity.html"),
                ("Centers for Disease Control and Prevention", "About Sleep", "2024", "https://www.cdc.gov/sleep/about/index.html"),
                ("American Diabetes Association", "Standards of Care in Diabetes - 2026", "2026", "https://diabetesjournals.org/care/issue/49/Supplement_1"),
                ("U.S. Food and Drug Administration", "Added Sugars on the Nutrition Facts Label", "2026", "https://www.fda.gov/food/nutrition-facts-label/added-sugars-nutrition-facts-label"),
            ],
            "visuals": [
                ("cover-reset", "A gentle weekly reset", ["notice", "meal", "fiber", "move", "drink", "sleep", "review", "repeat"]),
                ("roadmap", "Seven-day roadmap", ["Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7", "Next week"]),
                ("habit-loop", "The habit loop", ["cue", "routine", "reward", "repeat", "adjust", "support", "notice", "plan"]),
                ("balanced-meal", "One balanced meal", ["vegetables", "protein", "carb", "drink", "flavor", "fiber", "portion", "repeat"]),
                ("fiber-ladder", "Fiber addition ladder", ["add beans", "add oats", "add fruit", "add greens", "drink water", "pause", "notice", "adjust"]),
                ("movement-menu", "Movement menu", ["walk", "stand", "chair", "stretch", "stairs", "balance", "dance", "break"]),
                ("sleep-timeline", "Sleep routine timeline", ["lights", "caffeine", "screen", "meds", "pain", "wakeup", "routine", "doctor"]),
                ("weekly-tracker", "Weekly tracker", ["Day", "Water", "Meal", "Move", "Sleep", "Mood", "Notes"]),
            ],
            "pages": [
                ("Welcome and safety", "This reset is not a detox, cleanse, crash diet, or promise. It means pausing for one week, noticing patterns, and choosing a few routines that can support metabolic health.", ["Do not change medication or insulin without your care team.", "If activity is unsafe for you, ask what movements fit."]),
                ("How habits work", "Habits often need a cue, a routine, and a reward. The smaller the routine, the easier it is to repeat when life gets busy.", ["Tie a new habit to something you already do.", "Make backup plans part of the habit."]),
                ("Seven-day overview", "Each day asks for one main action. You can repeat a day, skip a day, or adapt the plan. The point is learning, not proving anything.", ["Notice.", "Build one meal.", "Add fiber.", "Break up sitting.", "Improve one drink.", "Protect sleep.", "Plan next week."]),
                ("Day 1: notice your starting point", "Record a normal day without judgment. Notice drinks, meals, movement, sleep, energy, mood, and one thing that felt hard.", ["Choose one realistic goal.", "Keep private health notes secure."]),
                ("Day 2: build one balanced meal", "Use the Mindful Plate method for one meal only. Add vegetables, protein, carbohydrate, and a low-sugar drink if possible.", ["One meal is enough.", "Mixed dishes can still count."]),
                ("Day 3: add fiber", "Add one fiber source such as beans, lentils, oats, berries, vegetables, whole grains, nuts, or seeds. Increase gradually and drink fluids.", ["Stop and ask for advice if fiber worsens symptoms.", "People with some medical diets need individual guidance."]),
                ("Day 4: break up sitting time", "Short activity breaks can help many people. Options include walking, standing, chair movement, stretching, or gentle household tasks.", ["The CDC describes 150 minutes per week as a common adult activity goal, but starting slowly is okay. [2]", "Ask your doctor which activities are safest."]),
                ("Day 5: improve one drink", "Choose one drink you have often and adjust it. Try less sugar, a smaller size, unsweet tea, water, sparkling water, or a gradual step-down.", ["You do not need to love plain water overnight.", "Alcohol and diabetes medicine require safety awareness."]),
                ("Day 6: protect sleep", "A realistic sleep routine may include a consistent wake time, dimmer light, less late caffeine, a wind-down cue, and a plan for pain, caregiving, or work shifts.", ["Sleep problems deserve care, not blame.", "Ask about snoring, breathing pauses, insomnia, or restless legs."]),
                ("Day 7: prepare next week", "Look back at what helped, what felt irritating, and what was too much. Pick one habit to repeat for another week.", ["Keep the habit small.", "Write down one question for a clinician if needed."]),
                ("Hydration tracker", "Track drinks for awareness, not judgment. A beverage inventory can reveal one easy place to reduce added sugar.", ["Note water, sweet drinks, coffee additions, juice, alcohol, and timing.", "Ask about fluid limits if you have heart or kidney disease."]),
                ("Movement tracker", "Record any movement that is safe for your body. Chair movement, stretching, physical therapy exercises, and short walks all count as information.", ["Track minutes or checkmarks.", "Pain is a signal to adapt, not push through blindly."]),
                ("Meal and fiber tracker", "Use this page to notice meals that kept you satisfied. Write the vegetable, protein, carbohydrate, and fiber source when you can.", ["Patterns matter more than one meal.", "Use notes, not grades."]),
                ("Sleep check-in", "Sleep is affected by stress, shift work, caregiving, pain, medications, breathing problems, and mental health. This page helps you notice what is changeable.", ["Track bedtime, wake time, naps, caffeine, alcohol, screens, and nighttime waking.", "Bring persistent sleep problems to a clinician."]),
                ("Mood and energy", "Energy can change with meals, sleep, movement, stress, and blood glucose. A simple mood and energy note can help you see patterns.", ["Use words, numbers, or colors.", "Sudden confusion or severe symptoms need urgent care."]),
                ("Optional glucose notes", "If you monitor glucose, use this page only in the way your care team recommends. Do not chase perfect numbers.", ["Record context: meal, medicine, activity, stress, illness, sleep.", "Ask what high or low patterns mean for you."]),
                ("Obstacles and backup plans", "Plan for busy days before they arrive. A backup meal, safe movement option, and lower-sugar drink can protect momentum.", ["Choose the easiest version.", "Ask family or household members for practical support."]),
                ("30-day continuation", "After seven days, continue one or two habits. A prevention plan should fit real life well enough to survive an ordinary month.", ["Repeat what worked.", "Drop what was unrealistic.", "Add one next step only."]),
            ],
        },
        {
            "folder": "06_Blood_Sugar_and_Brain_Health",
            "slug": "blood-sugar-brain-health",
            "file": "mindful-diabetes-blood-sugar-brain-health-2026.pdf",
            "title": "Blood Sugar & Brain Health",
            "subtitle": "Understanding the Everyday Connection",
            "accent": "navy",
            "description": "A careful guide to glucose, insulin resistance, blood vessels, dementia risk, and everyday habits that may support brain health.",
            "who": "For adults and caregivers who want a calm explanation of diabetes and long-term cognitive health.",
            "tags": ["Brain health", "Diabetes", "Prevention"],
            "refs": [
                ("Centers for Disease Control and Prevention", "Your Brain and Diabetes", "2024", "https://www.cdc.gov/diabetes/diabetes-complications/effects-of-diabetes-brain.html"),
                ("Centers for Disease Control and Prevention", "Reducing Risk for Dementia", "2024", "https://www.cdc.gov/alzheimers-dementia/prevention/index.html"),
                ("National Institute on Aging", "Cognitive Health and Older Adults", "2024", "https://www.nia.nih.gov/health/brain-health/cognitive-health-and-older-adults"),
                ("Livingston G, et al.", "Dementia prevention, intervention, and care: 2024 report of the Lancet standing Commission", "2024", "https://chronicdisease.org/wp-content/uploads/2024/12/Lancet-2024.pdf"),
                ("American Diabetes Association", "Standards of Care in Diabetes - 2026", "2026", "https://diabetesjournals.org/care/issue/49/Supplement_1"),
            ],
            "visuals": [
                ("cover-brain", "Everyday brain health", ["meal", "walk", "sleep", "glucose", "heart", "vessels", "memory", "support"]),
                ("glucose-pathway", "Glucose and insulin pathway", ["food", "glucose", "insulin", "cells", "energy", "storage", "targets", "variation"]),
                ("insulin-resistance", "Insulin resistance", ["cell", "insulin", "signal", "glucose", "resistance", "time", "support", "care"]),
                ("vessel-brain", "Blood vessels and brain", ["heart", "vessels", "brain", "oxygen", "pressure", "cholesterol", "glucose", "flow"]),
                ("high-low", "High and low glucose", ["high", "low", "symptoms", "timing", "urgent", "targets", "medicine", "doctor"]),
                ("risk-wheel", "Brain-health factors wheel", ["diabetes", "blood pressure", "activity", "sleep", "hearing", "smoking", "alcohol", "social"]),
                ("clinician-questions", "Questions for your clinician", ["targets", "meds", "A1C", "BP", "cholesterol", "memory", "sleep", "hearing"]),
                ("number-tracker", "Health-number tracker", ["A1C", "BP", "LDL", "sleep", "activity", "medicine", "notes"]),
            ],
            "pages": [
                ("Mindful Diabetes mission", "Mindful Diabetes connects education, prevention, research awareness, and practical tools at the intersection of metabolic and brain health.", ["The goal is clarity, not fear.", "Risk can be influenced, but not perfectly controlled."]),
                ("What glucose does", "Glucose is one of the body's energy sources. The brain uses glucose, but it also depends on steady blood flow, oxygen, sleep, and many other supports.", ["More is not always better.", "Very low glucose can be dangerous."]),
                ("How insulin helps", "Insulin helps move glucose from the blood into cells. Diabetes care often includes supporting glucose levels near a personal target range. [1]", ["Targets are individualized.", "Medication decisions belong with your care team."]),
                ("Insulin resistance", "Insulin resistance means cells do not respond to insulin as easily. The body may need more insulin to move glucose into cells.", ["It can develop gradually.", "Food, movement, sleep, stress, weight, medicines, and genetics can all be involved."]),
                ("The brain needs steady support", "The brain is sensitive to glucose changes. CDC notes that both high and low blood sugar can affect the brain and blood vessels. [1]", ["Repeated lows and prolonged highs both deserve care.", "Ask what patterns matter for you."]),
                ("Blood vessels and brain health", "Blood vessels carry oxygen and nutrients to the brain. Diabetes, high blood pressure, and cholesterol concerns can affect vascular health over time.", ["Vascular dementia is different from ordinary forgetfulness.", "Sudden confusion can be an emergency."]),
                ("High blood sugar over time", "Frequent hyperglycemia can stress blood vessels and nerves. Effects may build slowly and are not always obvious in the moment. [1]", ["This is a reason for support, not shame.", "Patterns are more useful than one isolated reading."]),
                ("Low blood sugar", "Hypoglycemia can cause shakiness, dizziness, confusion, trouble speaking, seizures, or loss of consciousness. It can be urgent, especially for people using insulin or certain medicines. [1]", ["Know your care team's low-glucose plan.", "Do not drive or ignore severe symptoms."]),
                ("Diabetes and cognitive risk", "Diabetes is associated with increased risk for cognitive problems and dementia, but it does not make dementia inevitable. Dementia has many causes and contributors. [2]", ["Risk is not destiny.", "Memory concerns deserve evaluation."]),
                ("What increased risk means", "Risk describes probability across groups. It cannot tell you what will happen to one person. Habits, medical care, social factors, genetics, and environment all interact.", ["Avoid panic.", "Use risk information to guide questions and care."]),
                ("Blood pressure and cholesterol", "Managing blood pressure and cholesterol can support heart and brain health. NIA and CDC identify vascular health as part of cognitive-health protection. [2,3]", ["Ask for your numbers.", "Ask what target range fits your age and health history."]),
                ("Physical activity", "Regular physical activity can support cardiovascular, metabolic, mood, sleep, and brain health. Start with what is safe and possible.", ["Walking is one option, not the only option.", "Chair movement and physical therapy can count."]),
                ("Food patterns", "Food patterns that include vegetables, fruits, legumes, whole grains, lean or plant proteins, and unsaturated fat sources can support metabolic and cardiovascular health.", ["No single brain-protection food is magic.", "Budget and culture matter."]),
                ("Sleep", "Sleep problems can affect mood, energy, glucose patterns, and daily decision-making. A realistic sleep plan may require medical care.", ["Ask about sleep apnea symptoms.", "Caregiving, shift work, pain, and medications matter."]),
                ("Smoking and alcohol", "Smoking and excessive alcohol use are dementia risk factors identified by public-health sources and dementia-prevention research. [2,4]", ["If you do not drink alcohol, do not start for health.", "Ask for support if quitting tobacco feels hard."]),
                ("Hearing, vision, and connection", "Hearing loss, vision problems, depression, and social isolation can affect cognitive health and quality of life. [2,3,4]", ["Treating hearing or vision problems may reduce strain.", "Social contact can be practical, not fancy."]),
                ("Questions for a clinician", "Bring questions about A1C, blood pressure, cholesterol, medicines, low-glucose risk, memory changes, sleep, hearing, and family history.", ["Write questions before the visit.", "Bring a medication list."]),
                ("What prevention can and cannot promise", "Healthy routines may help reduce risk and support daily function. They do not guarantee prevention of Alzheimer's disease, reverse every case of diabetes, or replace medical care.", ["Use careful hope.", "Stay connected to qualified care."]),
            ],
        },
    ]


def create_guide(guide):
    folder = PROJECT / guide["folder"]
    for sub in ["Final_Print_PDF", "Final_Web_PDF", "Editable_Source", "Images", "Website_Assets", "Research", "Accessibility"]:
        (folder / sub).mkdir(parents=True, exist_ok=True)
    images = folder / "Images"
    website = folder / "Website_Assets"
    research = folder / "Research"
    access = folder / "Accessibility"
    source = folder / "Editable_Source"

    visual_manifest = []
    for stem, title_value, labels in guide["visuals"]:
        image_path = images / f"{guide['slug']}-{stem}.png"
        if "tracker" in stem or "planner" in stem or "checklist" in stem or "questions" in stem:
            make_tracker_asset(image_path, title_value, labels[:7])
        else:
            make_tile_asset(image_path, title_value, labels, guide["accent"] if guide["accent"] in COLORS else "green")
        visual_manifest.append({
            "file_name": image_path.name,
            "visual_title": title_value,
            "source_or_method": "Original vector-style illustration generated locally with Python/Pillow for Mindful Diabetes.",
            "license": "Created for this project; no third-party image content.",
            "attribution_required": "No",
            "pdf_page": "",
            "alt_text": f"Educational graphic titled {title_value}.",
            "caption": title_value,
            "editing_performed": "Created at production size and placed into PDF layout.",
        })
    make_website_assets(guide, website)

    print_pdf = folder / "Final_Print_PDF" / guide["file"].replace(".pdf", "-print.pdf")
    web_pdf = folder / "Final_Web_PDF" / guide["file"]
    c = canvas.Canvas(str(print_pdf), pagesize=letter, pageCompression=1)
    c.setTitle(f"{guide['title']}: {guide['subtitle']}")
    c.setAuthor("Mindful Diabetes Inc.")
    c.setSubject(guide["description"])
    c.setKeywords(", ".join(["Mindful Diabetes"] + guide["tags"]))

    # Cover
    c.setFillColor(h("cream"))
    c.rect(0, 0, 612, 792, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setStrokeColor(h("line"))
    c.roundRect(42, 42, 528, 708, 18, fill=1, stroke=1)
    c.drawImage(str(LOGO), 68, 684, width=46, height=49, mask="auto")
    c.setFont("Lato-Bold", 9.5)
    c.setFillColor(h("green"))
    c.drawString(126, 720, "MINDFUL DIABETES FREE GUIDES")
    c.setFont("Lato", 8.5)
    c.setFillColor(h("muted"))
    c.drawString(126, 703, "Simple, practical guidance for metabolic and brain health.")
    heading(c, guide["title"], 74, 570, 290, 42 if len(guide["title"]) < 25 else 34)
    text(c, guide["subtitle"], 76, 405, 260, 13.6, "Lato", "body", 18)
    c.drawImage(str(images / f"{guide['slug']}-{guide['visuals'][0][0]}.png"), 326, 235, width=190, height=127, mask="auto")
    c.setFillColor(h("coral"))
    c.roundRect(76, 320, 112, 34, 17, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Lato-Bold", 10)
    c.drawCentredString(132, 332, "FREE GUIDE")
    c.setFont("Lato", 9)
    c.setFillColor(h("muted"))
    c.drawString(76, 107, "Mindful Diabetes Inc. | 501(c)(3) nonprofit")
    c.drawString(76, 88, "Published: July 30, 2026 | Medical review: pending")
    c.showPage()

    # Welcome and contents
    draw_page_base(c, guide, 2, "Welcome")
    eyebrow(c, "Welcome", 72, 672)
    y = heading(c, "How to use this guide", 72, 648, 468, 29)
    y = text(c, guide["description"] + " It is designed for ordinary days, imperfect schedules, mixed budgets, and real families.", 72, y - 8, 468, 11.2, "Lato", "body", 15)
    callout(c, "Use it for education", "This guide cannot diagnose, treat, or replace medical care. Individual needs vary, and medicines or insulin should not be changed based on a PDF.", 72, y - 16, 468, 84, "orange")
    y -= 125
    heading(c, "Contents", 72, y, 468, 18)
    contents = [p[0] for p in guide["pages"]]
    y -= 32
    for i, item in enumerate(contents[:18], 1):
        col = 0 if i <= 9 else 1
        yy = y - ((i - 1) % 9) * 26
        xx = 72 + col * 248
        c.setFont("Lato-Bold", 8.8)
        c.setFillColor(h("coral"))
        c.drawString(xx, yy, f"{i + 2:02d}")
        text(c, item, xx + 26, yy, 210, 8.8, "Lato", "body", 11)
    finish_page(c, guide, 2, "Welcome")

    for idx, page in enumerate(guide["pages"], 3):
        section, body, items = page
        draw_page_base(c, guide, idx, section)
        eyebrow(c, section, 72, 672)
        y = heading(c, section, 72, 648, 468, 25 if len(section) < 36 else 21)
        visual_index = (idx - 3) % len(guide["visuals"])
        if idx in {4, 6, 8, 10, 12, 14, 17, 19}:
            stem = guide["visuals"][visual_index][0]
            c.drawImage(str(images / f"{guide['slug']}-{stem}.png"), 310, 430, width=218, height=145, mask="auto")
            y = min(y, 405)
        y = text(c, body, 72, y - 8, 468 if idx not in {4, 6, 8, 10, 12, 14, 17, 19} else 210, 10.8, "Lato", "body", 14.4)
        y = bullets(c, items, 72, y - 8, 468 if idx not in {4, 6, 8, 10, 12, 14, 17, 19} else 210)
        if idx in {5, 9, 13, 16, 18}:
            callout(c, "Try this", "Choose one small action from this page and test it for one ordinary day. Keep what helps and adjust what does not.", 72, max(172, y - 12), 468, 72, "green")
        finish_page(c, guide, idx, section)

    # References and disclaimer page 21.
    page_num = 21
    draw_page_base(c, guide, page_num, "References")
    eyebrow(c, "References and safety", 72, 672)
    y = heading(c, "References, resources, and medical disclaimer", 72, 648, 468, 24)
    y = text(c, "This guide is for general education only. It is not medical advice, diagnosis, or treatment. Talk with a licensed healthcare professional before making significant changes, especially if you are pregnant, have kidney disease, a history of eating disorder, food allergies, gastrointestinal disease, severe low blood sugar, severe high blood sugar, or other medical conditions.", 72, y - 8, 468, 9.6, "Lato", "body", 12.4)
    y = text(c, "Do not change medication, insulin, or glucose targets based on this guide. Seek appropriate medical attention for urgent symptoms, including severe hypoglycemia, severe hyperglycemia, sudden confusion, chest pain, trouble breathing, fainting, or seizures.", 72, y - 8, 468, 9.6, "Lato", "body", 12.4)
    y = heading(c, "Mindful Diabetes resources", 72, y - 10, 220, 15)
    links = [
        ("Guide", "https://mindfuldiabetes.org/guide/"),
        ("Health Tools", "https://mindfuldiabetes.org/health-tools/"),
        ("JEIR", "https://www.mindfuldiabetes.ai/"),
        ("Support free education", "https://mindfuldiabetes.org/donation/"),
    ]
    for label, url in links:
        c.setFillColor(h("soft_green"))
        c.setStrokeColor(h("green"))
        c.roundRect(72, y - 23, 210, 25, 11, fill=1, stroke=1)
        c.setFillColor(h("green"))
        c.setFont("Lato-Bold", 8.8)
        c.drawCentredString(177, y - 14, label)
        c.linkURL(url, (72, y - 23, 282, y + 2), relative=0)
        y -= 34
    yy = 260
    c.setFont("Lora-Bold", 14)
    c.setFillColor(h("navy"))
    c.drawString(72, yy, "References")
    yy -= 22
    for n, ref in enumerate(guide["refs"], 1):
        yy = text(c, f"[{n}] {ref[0]}. {ref[1]}. {ref[2]}.", 72, yy, 468, 7.6, "Lato", "body", 9.3)
        c.linkURL(ref[3], (72, yy + 2, 540, yy + 12), relative=0)
        yy -= 2
    c.setFont("Lato", 7.8)
    c.setFillColor(h("muted"))
    c.drawString(72, 66, "Published: July 30, 2026 | Last medically reviewed: pending | Next scheduled review: July 2027")
    finish_page(c, guide, page_num, "References")
    c.save()

    reader = PdfReader(str(print_pdf))
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
        writer.pages[-1].compress_content_streams()
    writer.add_metadata({
        "/Title": f"{guide['title']}: {guide['subtitle']}",
        "/Author": "Mindful Diabetes Inc.",
        "/Subject": guide["description"],
        "/Keywords": ", ".join(["Mindful Diabetes"] + guide["tags"]),
    })
    for label, target in [("Cover", 0), ("Welcome", 1), ("Core Guide", 2), ("Worksheets and Tools", 16), ("References", 20)]:
        writer.add_outline_item(label, target)
    with web_pdf.open("wb") as f:
        writer.write(f)

    with (research / "image-license-manifest.csv").open("w", newline="") as f:
        writer_csv = csv.DictWriter(f, fieldnames=visual_manifest[0].keys())
        writer_csv.writeheader()
        writer_csv.writerows(visual_manifest)
    with (research / "references.json").open("w") as f:
        json.dump([{"organization_or_authors": r[0], "title": r[1], "year": r[2], "url": r[3]} for r in guide["refs"]], f, indent=2)
    with (research / "claim-manifest.csv").open("w", newline="") as f:
        writer_csv = csv.writer(f)
        writer_csv.writerow(["claim", "supporting_source", "source_date", "where_used", "review_note"])
        for page in guide["pages"]:
            writer_csv.writerow([page[1][:120], guide["refs"][0][1], guide["refs"][0][2], page[0], "Draft fact-check source mapping; formal medical review pending."])
    with (access / "accessibility-review-notes.md").open("w") as f:
        f.write("# Accessibility Review Notes\n\n- Selectable text, metadata, descriptive links, and PDF bookmarks are included.\n- Image alt text is documented in the image license manifest.\n- Full PDF/UA tagging should be completed in a dedicated remediation tool before broad clinical distribution.\n")
    with (source / "source.json").open("w") as f:
        json.dump(guide, f, indent=2)
    with (source / "build_remaining_free_guides.py").open("w") as f:
        f.write(Path(__file__).read_text())
    with (website / f"{guide['slug']}-website-metadata.json").open("w") as f:
        json.dump({
            "title": guide["title"],
            "short_description": guide["description"],
            "long_description": guide["description"] + " It includes plain-English explanations, practical examples, original graphics, printable tools, citations, and a medical safety disclaimer.",
            "who_this_is_for": guide["who"],
            "tags": guide["tags"],
            "button_text": "Download the Free Guide",
            "seo_title": f"{guide['title']} Free PDF Guide | Mindful Diabetes",
            "meta_description": guide["description"][:155],
            "pdf_file_name": guide["file"],
            "thumbnail_file_name": f"{guide['slug']}-download-card-thumbnail.png",
            "slug": guide["slug"],
            "alt_text": f"Cover preview for {guide['title']} free guide.",
        }, f, indent=2)
    print(f"created {web_pdf}")


def main():
    register_fonts()
    for guide in page_data():
        create_guide(guide)


if __name__ == "__main__":
    main()
