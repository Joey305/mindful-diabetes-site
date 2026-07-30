import fs from "node:fs/promises";
import path from "node:path";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const ROOT = "/Users/jerrismacbook/Desktop/Mindful-Diabetes-Site";
const OUT_DIR = path.join(ROOT, "Mindful_Diabetes_Free_Guides/04_Grocery_Store_Survival_Guide");
const ASSET_DIR = path.join(OUT_DIR, "Editable_Source/Rebuilt_Assets");
const TMP_DIR = path.join(ROOT, "tmp_grocery_rebuild");
const FINAL_PPTX = path.join(OUT_DIR, "Editable_Source/mindful-diabetes-grocery-store-guide-2026-redesigned-corrected.pptx");
const RENDER_DIR = path.join(TMP_DIR, "rendered_pages");
const LAYOUT_DIR = path.join(TMP_DIR, "layouts");
const LOGO = path.join(ROOT, "Mindful_Diabetes_Free_Guides/01_Brand_Assets/Logos/mdi-logo.jpg");

const IMG = {
  cover: path.join(ASSET_DIR, "cover-grocery-bags-cart.png"),
  before: path.join(ASSET_DIR, "before-shop-list-kitchen.png"),
  freezer: path.join(ASSET_DIR, "freezer-section-foods.png"),
  budget: path.join(ASSET_DIR, "budget-pantry-staples.png"),
  cart: path.join(ASSET_DIR, "five-part-grocery-cart.png"),
};

const W = 816;
const H = 1056;
const P = {
  cream: "#FBF3EA",
  paper: "#FFFDF7",
  green: "#034B2F",
  green2: "#166444",
  softGreen: "#E6F2EC",
  navy: "#192442",
  coral: "#F26A2E",
  coralSoft: "#FCE4D8",
  blueSoft: "#EEF7FA",
  goldSoft: "#FFF3CD",
  ink: "#16211D",
  muted: "#5C6C67",
  rule: "#D9E2DA",
  white: "#FFFFFF",
};

const refs = [
  ["U.S. Food and Drug Administration", "How to Understand and Use the Nutrition Facts Label", "FDA", "2024", "https://www.fda.gov/food/nutrition-facts-label/how-understand-and-use-nutrition-facts-label"],
  ["U.S. Food and Drug Administration", "Daily Value on the Nutrition and Supplement Facts Labels", "FDA", "2024", "https://www.fda.gov/food/nutrition-facts-label/daily-value-nutrition-and-supplement-facts-labels"],
  ["U.S. Food and Drug Administration", "Added Sugars on the Nutrition Facts Label", "FDA", "2026", "https://www.fda.gov/food/nutrition-facts-label/added-sugars-nutrition-facts-label"],
  ["Centers for Disease Control and Prevention", "Counting Carbohydrates", "CDC", "2024", "https://www.cdc.gov/diabetes/healthy-eating/carb-counting.html"],
  ["American Diabetes Association", "What is the Diabetes Plate?", "ADA", "2026", "https://diabetesfoodhub.org/blog/what-diabetes-plate"],
  ["U.S. Department of Agriculture", "MyPlate: Fruits and Vegetables", "USDA MyPlate", "2026", "https://www.myplate.gov/eat-healthy/fruits"],
  ["U.S. Department of Agriculture", "MyPlate: Dairy", "USDA MyPlate", "2026", "https://www.myplate.gov/eat-healthy/dairy"],
  ["U.S. Department of Agriculture", "MyPlate: Protein Foods", "USDA MyPlate", "2026", "https://www.myplate.gov/eat-healthy/protein-foods"],
  ["U.S. Food and Drug Administration", "Sodium in Your Diet", "FDA", "2024", "https://www.fda.gov/food/nutrition-education-resources-materials/sodium-your-diet"],
];

let logoBytes;
const imageBytes = {};

async function writeBlob(filePath, blob) {
  await fs.writeFile(filePath, new Uint8Array(await blob.arrayBuffer()));
}

async function bytes(filePath) {
  const b = await fs.readFile(filePath);
  return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength);
}

function shape(slide, geometry, x, y, w, h, fill = "none", line = "none", radius = undefined) {
  return slide.shapes.add({
    geometry,
    position: { left: x, top: y, width: w, height: h },
    fill,
    line: { style: "solid", fill: line, width: line === "none" ? 0 : 1.05 },
    ...(radius ? { borderRadius: radius } : {}),
  });
}

function text(slide, value, x, y, w, h, opts = {}) {
  const s = shape(slide, "textbox", x, y, w, h, "none", "none");
  s.text = value;
  s.text.style = {
    fontSize: opts.size ?? 16,
    bold: opts.bold ?? false,
    italic: opts.italic ?? false,
    color: opts.color ?? P.ink,
    typeface: opts.face ?? "Lato",
    alignment: opts.align ?? "left",
    verticalAlignment: opts.valign ?? "top",
    lineSpacing: opts.leading ?? 1.16,
    autoFit: "none",
    wrap: "square",
    insets: { top: 2, right: 4, bottom: 2, left: 4 },
  };
  if (opts.link) {
    s.text.get(value).link = { uri: opts.link, isExternal: true };
  }
  return s;
}

function image(slide, imagePath, alt, x, y, w, h, fit = "cover", radius = 12) {
  slide.images.add({
    blob: imageBytes[imagePath],
    contentType: "image/png",
    alt,
    fit,
    geometry: "roundRect",
    borderRadius: radius,
    position: { left: x, top: y, width: w, height: h },
  });
}

function chrome(slide, page, section) {
  if (page === 1 || page === 21) return;
  slide.images.add({ blob: logoBytes, contentType: "image/jpeg", alt: "Mindful Diabetes Inc. logo", fit: "cover", geometry: "roundRect", borderRadius: 8, position: { left: 58, top: 30, width: 27, height: 29 } });
  text(slide, "Grocery Store Survival Guide", 92, 35, 260, 18, { size: 10.3, bold: true, color: P.green, face: "Lora" });
  text(slide, section, 92, 51, 280, 15, { size: 8.8, color: P.muted });
  shape(slide, "line", 58, 75, 700, 0, "none", P.rule);
  shape(slide, "line", 58, 1009, 700, 0, "none", P.rule);
  text(slide, "Mindful Diabetes Inc.", 58, 1020, 185, 18, { size: 8.8, color: P.muted });
  text(slide, "mindfuldiabetes.org", 332, 1020, 155, 18, { size: 8.8, color: P.muted, align: "center", link: "https://www.mindfuldiabetes.org/" });
  text(slide, `${page}`, 723, 1020, 35, 18, { size: 8.8, color: P.coral, align: "right" });
}

function title(slide, section, headline, support = "") {
  const long = headline.length > 42;
  text(slide, section.toUpperCase(), 66, 83, 500, 22, { size: 12, bold: true, color: P.coral });
  text(slide, headline, 62, 112, 690, long ? 96 : 76, { size: long ? 30 : 34, bold: true, color: P.navy, face: "Lora", leading: 1.03 });
  if (support) text(slide, support, 66, long ? 218 : 196, 670, 64, { size: 15, color: P.muted, leading: 1.24 });
}

function notes(slide, extra = "") {
  slide.speakerNotes.textFrame.setText(`[Sources]\n${refs.map((r, i) => `- [${i + 1}] ${r[0]}, ${r[1]}: ${r[4]}`).join("\n")}\n${extra ? `- Asset note: ${extra}\n` : ""}`);
}

function callout(slide, heading, body, x, y, w, h, tone = "green") {
  const fill = tone === "orange" ? P.coralSoft : tone === "blue" ? P.blueSoft : P.softGreen;
  const line = tone === "orange" ? "#F3B499" : tone === "blue" ? "#C8DCE5" : "#B8D8C8";
  shape(slide, "roundRect", x, y, w, h, fill, line, 10);
  text(slide, heading, x + 16, y + 14, w - 32, 22, { size: 13.2, bold: true, color: tone === "orange" ? "#8F3519" : P.green });
  text(slide, body, x + 16, y + 42, w - 32, h - 50, { size: 11.5, color: P.ink, leading: 1.16 });
}

function bullet(slide, item, x, y, w, opts = {}) {
  if (opts.checkbox) {
    shape(slide, "rect", x, y + 4, 12, 12, P.white, opts.dot ?? P.green);
  } else {
    shape(slide, "ellipse", x, y + 6, 8, 8, opts.dot ?? P.coral, "none");
  }
  text(slide, item, x + 22, y, w - 22, opts.h ?? 30, { size: opts.size ?? 12.2, color: opts.color ?? P.ink, leading: 1.14 });
}

function bullets(slide, items, x, y, w, opts = {}) {
  items.forEach((item, i) => bullet(slide, item, x, y + i * (opts.gap ?? 34), w, opts));
}

function card(slide, heading, body, x, y, w, h, opts = {}) {
  shape(slide, "roundRect", x, y, w, h, opts.fill ?? P.white, opts.line ?? P.rule, 10);
  if (opts.check) shape(slide, "rect", x + 14, y + 18, 13, 13, P.white, opts.accent ?? P.green);
  else shape(slide, "ellipse", x + 14, y + 18, 16, 16, opts.fill === P.coralSoft ? P.coralSoft : P.softGreen, opts.accent ?? P.green);
  text(slide, heading, x + 42, y + 13, w - 54, 22, { size: opts.headSize ?? 12.6, bold: true, color: opts.headColor ?? P.navy });
  text(slide, body, x + 42, y + 40, w - 54, h - 46, { size: opts.size ?? 10.6, color: opts.bodyColor ?? P.muted, leading: 1.1 });
}

function tag(slide, label, x, y, w, tone = "green") {
  shape(slide, "roundRect", x, y, w, 26, tone === "orange" ? P.coralSoft : P.softGreen, tone === "orange" ? "#F3B499" : "#B8D8C8", 13);
  text(slide, label, x + 10, y + 6, w - 20, 14, { size: 9.8, bold: true, color: tone === "orange" ? "#8F3519" : P.green, align: "center" });
}

function twoColCards(slide, entries, x, y, cardW = 318, cardH = 92, gapY = 22) {
  entries.forEach((e, i) => {
    card(slide, e[0], e[1], x + (i % 2) * (cardW + 28), y + Math.floor(i / 2) * (cardH + gapY), cardW, cardH, e[2] ?? {});
  });
}

function simpleTable(slide, data, x, y, widths, rowH, headerFill = P.softGreen) {
  for (let r = 0; r < data.length; r++) {
    let xx = x;
    for (let c = 0; c < data[r].length; c++) {
      shape(slide, "rect", xx, y + r * rowH, widths[c], rowH, r === 0 ? headerFill : (r % 2 ? P.white : "#FAFCFA"), "#D6DED8");
      text(slide, data[r][c], xx + 8, y + r * rowH + 9, widths[c] - 16, rowH - 12, { size: r === 0 ? 10.6 : 9.7, bold: r === 0, color: P.ink, leading: 1.05 });
      xx += widths[c];
    }
  }
}

function packageCard(slide, titleText, claim, x, y, w, h, fill = P.white) {
  shape(slide, "roundRect", x, y, w, h, fill, P.rule, 10);
  shape(slide, "rect", x + 18, y + 18, w - 36, 42, P.softGreen, "none");
  text(slide, claim, x + 24, y + 30, w - 48, 16, { size: 10.3, bold: true, color: P.green, align: "center" });
  text(slide, titleText, x + 18, y + 78, w - 36, 22, { size: 13, bold: true, color: P.navy, face: "Lora", align: "center" });
  shape(slide, "rect", x + 44, y + 118, w - 88, 50, P.coralSoft, "none");
}

function nutritionMini(slide, x, y, titleText, rows) {
  shape(slide, "rect", x, y, 250, 236, P.white, P.ink);
  text(slide, "Nutrition Facts", x + 10, y + 10, 170, 25, { size: 18, bold: true, color: P.ink });
  text(slide, titleText, x + 10, y + 40, 200, 18, { size: 10.2, bold: true, color: P.green });
  let yy = y + 66;
  rows.forEach((r, i) => {
    shape(slide, "line", x + 10, yy - 4, 230, 0, "none", i === 0 ? P.ink : P.rule);
    text(slide, r[0], x + 12, yy, 130, 18, { size: r[2] ? 10.5 : 9.7, bold: !!r[2], color: P.ink });
    text(slide, r[1], x + 145, yy, 85, 18, { size: r[2] ? 10.5 : 9.7, bold: !!r[2], color: P.ink, align: "right" });
    yy += 28;
  });
}

function fullNutritionLabel(slide) {
  const x = 66, y = 300, w = 330;
  shape(slide, "rect", x, y, w, 500, P.white, P.ink);
  text(slide, "Nutrition Facts", x + 12, y + 12, 220, 34, { size: 25, bold: true, color: P.ink });
  const rows = [
    ["Serving size", "1 cup", true, "1"],
    ["Servings per container", "2", false, "2"],
    ["Calories", "240", true, ""],
    ["Total Fat", "12g  15%", true, ""],
    ["Saturated Fat", "4g  20%", false, "6"],
    ["Sodium", "480mg  21%", true, "7"],
    ["Total Carbohydrate", "34g  12%", true, "3"],
    ["Dietary Fiber", "4g  14%", false, "4"],
    ["Total Sugars", "12g", false, ""],
    ["Added Sugars", "8g  16%", false, "5"],
  ];
  let yy = y + 62;
  rows.forEach((r, i) => {
    shape(slide, "line", x + 10, yy - 4, w - 20, 0, "none", i === 2 ? P.ink : P.rule);
    text(slide, r[0], x + 12 + (r[2] ? 0 : 18), yy, 180, 20, { size: r[2] ? 12.6 : 11.2, bold: r[2], color: P.ink });
    text(slide, r[1], x + 206, yy, 92, 20, { size: r[2] ? 12.6 : 11.2, bold: r[2], color: P.ink, align: "right" });
    if (r[3]) {
      shape(slide, "ellipse", x + w - 20, yy - 2, 22, 22, P.coral, "none");
      text(slide, r[3], x + w - 14, yy + 2, 10, 10, { size: 8.5, bold: true, color: P.white, align: "center" });
    }
    yy += i === 2 ? 42 : 35;
  });
  const calls = [
    ["1", "Serving size describes the label.", 430, 312],
    ["2", "Servings per container can change the math.", 430, 382],
    ["3", "Total carbohydrate is the main carb line.", 430, 452],
    ["4", "Fiber is included in total carbohydrate.", 430, 522],
    ["5", "Added sugar is separate from total sugars.", 430, 592],
    ["6", "Saturated fat helps compare similar foods.", 430, 662],
    ["7", "Sodium and %DV help with comparison.", 430, 732],
  ];
  calls.forEach(c => {
    shape(slide, "ellipse", c[2], c[3], 28, 28, P.coral, "none");
    text(slide, c[0], c[2] + 7, c[3] + 5, 10, 10, { size: 9.5, bold: true, color: P.white, align: "center" });
    text(slide, c[1], c[2] + 40, c[3] + 3, 240, 36, { size: 11.5, color: P.ink, leading: 1.12 });
  });
}

function worksheetLine(slide, label, x, y, w, h = 40) {
  text(slide, label, x, y + 8, 175, 22, { size: 11.8, bold: true, color: P.navy });
  shape(slide, "roundRect", x + 185, y, w - 185, h, P.white, "#CCD8D1", 6);
}

async function main() {
  await fs.mkdir(RENDER_DIR, { recursive: true });
  await fs.mkdir(LAYOUT_DIR, { recursive: true });
  logoBytes = await bytes(LOGO);
  for (const p of Object.values(IMG)) imageBytes[p] = await bytes(p);

  const deck = Presentation.create({ slideSize: { width: W, height: H } });
  const pages = [];
  function addPage(section, fn) {
    const slide = deck.slides.add();
    slide.background.fill = section === "Next steps" ? P.green : P.paper;
    pages.push(slide);
    const pageNumber = pages.length;
    chrome(slide, pageNumber, section);
    fn(slide, pageNumber);
    notes(slide);
  }

  addPage("Cover", (slide) => {
    image(slide, IMG.cover, "Reusable bags and grocery cart with practical groceries", 0, 0, 816, 568, "cover", 0);
    shape(slide, "rect", 0, 0, 816, 568, "#012C24/45", "none");
    slide.images.add({ blob: logoBytes, contentType: "image/jpeg", alt: "Mindful Diabetes Inc. logo", fit: "cover", geometry: "roundRect", borderRadius: 9, position: { left: 62, top: 62, width: 54, height: 58 } });
    text(slide, "Mindful Diabetes Free Guides", 132, 72, 340, 24, { size: 16, bold: true, color: P.white, face: "Lora" });
    text(slide, "501(c)(3) nonprofit health education", 132, 98, 320, 18, { size: 10.5, color: "#E6F2EC" });
    shape(slide, "roundRect", 62, 486, 108, 34, P.coral, "none", 17);
    text(slide, "FREE GUIDE", 77, 495, 80, 15, { size: 10, bold: true, color: P.white, align: "center" });
    text(slide, "The Grocery Store Survival Guide", 62, 618, 690, 120, { size: 47, bold: true, color: P.navy, face: "Lora", leading: 0.98 });
    text(slide, "How to Make Practical, Blood Sugar-Conscious Choices Without Feeling Overwhelmed", 66, 760, 670, 54, { size: 18, bold: true, color: P.green, leading: 1.15 });
    text(slide, "A warm, practical shopping guide for building a cart that fits your life, budget, schedule, and health needs.", 66, 844, 660, 54, { size: 14.5, color: P.ink, leading: 1.22 });
    callout(slide, "Inside", "Planning, cart formula, aisle strategies, product comparisons, label reading, backup meals, and a printable grocery list.", 66, 910, 660, 70, "green");
    text(slide, "Published July 30, 2026 | Medical review pending", 66, 1002, 430, 18, { size: 10.2, color: P.muted });
    text(slide, "mindfuldiabetes.org", 594, 1002, 140, 18, { size: 10.2, color: P.green, bold: true, align: "right", link: "https://www.mindfuldiabetes.org/" });
  });

  addPage("Before you shop", (slide) => {
    title(slide, "Before you shop", "A short list you use beats an ideal list left at home", "Start with what is already in your kitchen, then choose a few realistic meals for the week.");
    image(slide, IMG.before, "Grocery bag, blank list, and practical food on a kitchen counter", 66, 288, 310, 250, "cover");
    const checks = ["Check the refrigerator, freezer, and pantry.", "Choose two or three meals.", "Pick one or two backup meals.", "Check the household schedule.", "Write a short list.", "Bring bags, coupons, mobility tools, or reminders."];
    checks.forEach((c, i) => card(slide, `${i + 1}`, c, 406, 286 + i * 78, 310, 58, { check: true, size: 11.6, headSize: 13, fill: i % 2 ? P.white : P.softGreen }));
    callout(slide, "Kind shopping rule", "The goal is not a perfect cart. The goal is food you can use before it spoils, on days that are busy, tired, or unpredictable.", 66, 800, 650, 88, "green");
  });

  addPage("Five-part cart", (slide) => {
    title(slide, "Five-part cart", "Use five flexible categories, not a perfect grocery script", "The categories help you build meals. They do not need equal space in the cart, and fresh, frozen, canned, dried, and shelf-stable foods can all fit. [5]");
    image(slide, IMG.cart, "Overhead grocery cart with practical food categories", 86, 286, 490, 430, "contain");
    const labels = [
      ["Vegetables and fruit", "fresh, frozen, canned", 78, 302],
      ["Protein", "animal or plant", 560, 330],
      ["Fiber-rich carbs", "beans, oats, grains, fruit", 64, 650],
      ["Healthy fats", "nuts, seeds, oils", 558, 646],
      ["Flavor builders", "spices, salsa, herbs", 296, 735],
    ];
    labels.forEach((l, i) => {
      const tone = i === 2 ? "blue" : i === 3 ? "orange" : "green";
      callout(slide, l[0], l[1], l[2], l[3], i === 4 ? 224 : 176, 74, tone);
    });
    callout(slide, "Use what works", "Perimeter-only shopping can miss useful budget foods such as beans, oats, canned tomatoes, frozen vegetables, lentils, and shelf-stable fish.", 66, 860, 650, 78, "green");
  });

  addPage("Produce", (slide) => {
    title(slide, "Produce", "Fresh, frozen, and canned all count", "Choose vegetables and fruit you will actually use. Fresh can be wonderful, but it is not morally superior to frozen or canned options. [6]");
    const cols = [
      ["Fresh", "Useful when it will be eaten before spoiling.", ["Leafy greens", "Peppers", "Carrots", "Tomatoes"]],
      ["Frozen", "Helpful for convenience and reducing waste.", ["Broccoli", "Mixed vegetables", "Berries", "Greens"]],
      ["Canned", "Useful for low-energy days and shelf stability.", ["Tomatoes", "Peaches in water or juice", "Carrots", "Vegetable mixes"]],
    ];
    cols.forEach((c, i) => {
      const x = 66 + i * 228;
      shape(slide, "roundRect", x, 306, 200, 330, i === 0 ? P.white : i === 1 ? P.blueSoft : P.softGreen, P.rule, 12);
      text(slide, c[0], x + 18, 328, 160, 24, { size: 18, bold: true, color: P.green, face: "Lora" });
      text(slide, c[1], x + 18, 366, 160, 58, { size: 11.6, color: P.ink, leading: 1.14 });
      bullets(slide, c[2], x + 22, 450, 150, { gap: 38, size: 11.4 });
    });
    callout(slide, "What to check", "For canned fruit, check syrup versus water or juice. For vegetables, compare sodium when practical. For frozen produce, check sauces and added sugars.", 66, 760, 650, 86, "green");
  });

  addPage("Frozen foods", (slide) => {
    title(slide, "Frozen foods", "The freezer section can reduce waste and rescue dinner", "Frozen foods can be affordable, fast, and useful. The package details matter more than the freezer aisle itself.");
    image(slide, IMG.freezer, "Freezer case with plain frozen vegetables, berries, fish, and meals", 66, 286, 326, 320, "cover");
    twoColCards(slide, [
      ["Frozen greens", "Soups, eggs, bowls, sauces."],
      ["Frozen berries", "Yogurt, oats, smoothies."],
      ["Mixed vegetables", "Fast side or stir-fry base."],
      ["Frozen fish", "Protein backup for busy weeks."],
    ], 420, 286, 145, 112, 24);
    callout(slide, "Check the package", "Look for sauce, added sugar, sodium, serving size, protein, and vegetables. A simple frozen meal can still be supplemented with extra vegetables or protein.", 66, 760, 650, 90, "orange");
  });

  addPage("Canned and shelf-stable", (slide) => {
    title(slide, "Canned and shelf-stable", "Pantry foods are not a fallback failure", "Canned, dried, and shelf-stable foods can make useful emergency meals. Oats belong with pantry grains, not canned foods.");
    image(slide, IMG.budget, "Budget-friendly shelf-stable foods with canned goods, oats, lentils, rice, eggs, carrots, and frozen vegetables", 66, 288, 310, 214, "cover");
    twoColCards(slide, [
      ["Canned beans", "Rinsing may reduce some sodium; draining changes the final contents."],
      ["Canned tomatoes", "Useful for soups, stews, sauces, and shakshuka-style meals."],
      ["Tuna, salmon, or chicken", "Shelf-stable protein; compare sodium and serving size."],
      ["Canned vegetables or fruit", "Look for sodium, syrup, water, or juice as needed."],
      ["Dried lentils", "Quick-cooking pantry protein plus carbohydrate and fiber."],
      ["Oats", "A pantry grain, useful for breakfast or baking, not canned food."],
    ], 66, 536, 318, 82, 18);
    callout(slide, "Backup meal idea", "Keep one meal you can make when energy is low: beans plus tomatoes plus frozen vegetables, or soup plus extra protein and a whole-grain side.", 66, 866, 650, 78, "green");
  });

  addPage("Protein choices", (slide) => {
    title(slide, "Protein choices", "Choose by use, budget, culture, storage, and medical needs", "Protein foods can be animal-based or plant-based. Beans and lentils provide protein, carbohydrate, and fiber, so they may matter in glucose planning. [8]");
    twoColCards(slide, [
      ["Quick fridge proteins", "Eggs, yogurt, cottage cheese, tofu, tempeh."],
      ["Freezer proteins", "Fish, poultry, lean meats, edamame, cooked beans."],
      ["Pantry proteins", "Beans, lentils, canned fish or chicken, nuts, seeds."],
      ["Meal context", "Tacos, soup, stir-fry, bowls, sandwiches, salads."],
    ], 66, 302, 318, 108, 26);
    callout(slide, "No moral ranking", "The best protein option is the one that fits the meal, the household, allergies, taste, storage, preparation time, and medical needs.", 66, 800, 650, 86, "green");
  });

  addPage("Plant proteins", (slide) => {
    title(slide, "Plant proteins", "Canned beans count", "You do not need to begin with dried beans. Start where your time, tools, digestion, and budget are today.");
    const items = [["Beans", "Tacos, soups, bowls, salads."], ["Lentils", "Dal, soup, curry, salad."], ["Tofu", "Stir-fry, bowls, scramble."], ["Tempeh", "Skillet meals, sandwiches."], ["Edamame", "Snacks, sides, bowls."], ["Seasoning", "Cumin, garlic, ginger, curry, salsa, herbs."]];
    items.forEach((it, i) => card(slide, it[0], it[1], 66 + (i % 2) * 342, 300 + Math.floor(i / 2) * 128, 306, 96, { fill: i % 3 === 0 ? P.softGreen : P.white }));
    callout(slide, "Glucose planning note", "Beans, lentils, and edamame are often filling because they bring protein and fiber, but they also contain carbohydrate. Use your own plan if you count carbs.", 66, 810, 650, 86, "blue");
  });

  addPage("Breads and grains", (slide) => {
    title(slide, "Breads, grains, cereals, and tortillas", "Front-package claims are only the first sentence", "Compare similar products by serving size, total carbohydrate, fiber, added sugar, saturated fat when relevant, ingredients, and what you enjoy.");
    const table = [
      ["Front claim", "Useful next check", "Why it matters"],
      ["Multigrain", "Ingredient list", "May not mean whole grain"],
      ["Whole grain", "Fiber + carbs", "Still compare serving sizes"],
      ["Keto", "Saturated fat + fiber", "Claim alone is not enough"],
      ["High-fiber", "Serving size + tolerance", "More is not always better"],
      ["No added sugar", "Total carbohydrate", "May still contain starch"],
    ];
    simpleTable(slide, table, 66, 302, [150, 210, 290], 52);
    callout(slide, "Store-shelf method", "Pick two similar items, then compare the label. One number does not decide the best choice; the food has to fit your meal, taste, budget, and glucose plan.", 66, 720, 650, 92, "green");
  });

  addPage("Dairy and alternatives", (slide) => {
    title(slide, "Dairy and alternatives", "The cooler section is not one category nutritionally", "Milk and yogurt often contain carbohydrate. Cheese usually has little carbohydrate, but can add saturated fat and sodium. Fortified soy milk differs from many other plant beverages. [7]");
    twoColCards(slide, [
      ["Milk", "Check serving size, carbohydrate, and how you use it."],
      ["Plain yogurt", "Check protein and added sugar; add fruit if desired."],
      ["Flavored yogurt", "Check added sugar and total carbohydrate."],
      ["Cheese", "Often lower carb; compare sodium and saturated fat."],
      ["Fortified soy milk", "Often closer to dairy milk for protein than many alternatives."],
      ["Other plant drinks", "Almond, oat, coconut, and rice beverages vary widely."],
    ], 66, 292, 318, 90, 20);
    callout(slide, "Comparison prompts", "Is it sweetened? How much protein? Is it fortified? Does it fit allergies, preferences, kidney needs, or other medical considerations?", 66, 838, 650, 86, "green");
  });

  addPage("Snacks", (slide) => {
    title(slide, "Snacks", "A planned snack can be useful, and some people may not need one", "Snacking is not a character test. If snacks help your schedule, medication plan, activity, or hunger, make them practical.");
    twoColCards(slide, [
      ["Fruit + nuts", "Portable, filling, easy to repeat."],
      ["Yogurt + berries", "Protein plus fruit; check added sugar."],
      ["Hummus + vegetables", "Fiber, flavor, and crunch."],
      ["Egg + fruit", "Simple protein plus carbohydrate."],
      ["Crackers + tuna", "Shelf-stable option with protein."],
      ["Roasted chickpeas", "Crunchy, portable, contains carbs and fiber."],
      ["Nut butter + apple", "Satisfying; portion as needed."],
      ["Popcorn + another food", "May need protein or fat if it does not last."],
    ], 66, 294, 318, 74, 16);
    callout(slide, "Medication safety", "If you use insulin or medicines that can cause low blood sugar, ask your care team how snacks, activity, and low-glucose treatment should be handled.", 66, 890, 650, 72, "orange");
  });

  addPage("Drinks", (slide) => {
    title(slide, "Drinks", "Change one frequent drink before changing everything", "Sweet drinks can add sugar quickly, but the next step can be gradual. Juice is not universally forbidden; context and portion matter.");
    const drinks = [["Water", "default", P.softGreen], ["Sparkling water", "unsweetened", P.softGreen], ["Tea or coffee", "watch add-ins", P.softGreen], ["Smaller sweet drink", "step-down option", P.goldSoft], ["Soda", "sugar quickly adds up", P.coralSoft], ["Sweet tea", "sugar varies", P.coralSoft], ["Juice", "portion and purpose matter", P.goldSoft], ["Energy/sports drinks", "check sugar and caffeine", P.coralSoft]];
    drinks.forEach((d, i) => {
      const x = 66 + (i % 4) * 168;
      const y = 306 + Math.floor(i / 4) * 122;
      shape(slide, "roundRect", x, y, 138, 82, d[2], P.rule, 12);
      shape(slide, "rect", x + 22, y + 18, 24, 42, P.white, P.green);
      text(slide, d[0], x + 56, y + 18, 72, 18, { size: 10.8, bold: true, color: P.navy });
      text(slide, d[1], x + 56, y + 40, 72, 24, { size: 8.9, color: P.muted });
    });
    callout(slide, "Alcohol safety", "Alcohol can interact with diabetes medicines and can affect glucose decisions. Ask your clinician what is safe for you, especially if you use insulin or medicines that can cause lows.", 66, 720, 650, 92, "orange");
  });

  addPage("Nutrition Facts label", (slide) => {
    title(slide, "Nutrition Facts label", "Start with serving size, then scan what matters for your meal", "The label is a comparison tool, not a personal portion prescription. Use it alongside your own plan and the way you will eat the food. [1,2]");
    fullNutritionLabel(slide);
    callout(slide, "Fast rule of thumb", "For many nutrients, 5% Daily Value or less is low and 20% Daily Value or more is high. The amount is per labeled serving. [2]", 66, 850, 650, 80, "green");
  });

  addPage("Carbs and added sugar", (slide) => {
    title(slide, "Carbs and added sugar", "Added sugar is one clue; total carbohydrate is still the main carb line", "Total carbohydrate includes starch, sugars, added sugars, and fiber. It can matter for carbohydrate-counting or glucose-management plans. [3,4]");
    shape(slide, "roundRect", 82, 300, 280, 360, P.blueSoft, "#C8DCE5", 16);
    text(slide, "Total carbohydrate includes", 110, 330, 230, 30, { size: 18, bold: true, color: P.navy, face: "Lora", align: "center" });
    [["Starches", 385], ["Sugars", 450], ["Added sugars", 515], ["Fiber", 580]].forEach(([l, y]) => {
      shape(slide, "roundRect", 126, y, 190, 42, P.white, P.rule, 9);
      text(slide, l, 140, y + 12, 160, 16, { size: 12.4, bold: true, color: P.green, align: "center" });
    });
    simpleTable(slide, [
      ["Ingredient words", "Still check"],
      ["Syrup, dextrose, sucrose", "Total carbohydrate"],
      ["Honey, agave, molasses", "Added sugars + serving size"],
      ["Juice concentrate", "Total carbs and portion"],
      ["No sugar added", "May not be low carbohydrate"],
      ["Sugar-free", "May not be carbohydrate-free"],
    ], 418, 306, [160, 220], 54, P.coralSoft);
    callout(slide, "Plain-English takeaway", "Ingredient names can help you notice added sweeteners. They do not replace the Nutrition Facts label or your portion.", 66, 780, 650, 82, "green");
  });

  addPage("Fiber", (slide) => {
    title(slide, "Fiber", "Compare similar foods, then increase gradually", "Fiber-rich foods can support fullness, digestive health, overall dietary quality, cholesterol management, and more balanced meals. Individual glucose and digestive responses vary.");
    const foods = ["Vegetables", "Beans", "Lentils", "Oats", "Whole grains", "Berries", "Nuts", "Seeds"];
    foods.forEach((f, i) => tag(slide, f, 70 + (i % 4) * 166, 292 + Math.floor(i / 4) * 44, 132, i % 3 === 0 ? "orange" : "green"));
    nutritionMini(slide, 90, 418, "Option 1", [["Serving size", "1 bar", true], ["Total carb", "28g", true], ["Dietary fiber", "2g  7%"], ["Added sugars", "9g  18%"], ["Sodium", "120mg  5%"]]);
    nutritionMini(slide, 450, 418, "Option 2", [["Serving size", "1 bar", true], ["Total carb", "29g", true], ["Dietary fiber", "6g  21%"], ["Added sugars", "5g  10%"], ["Sodium", "150mg  7%"]]);
    callout(slide, "Comfort note", "Increase fiber gradually, drink fluids, and adjust for digestive conditions, kidney needs, medications, and your care team's advice.", 66, 790, 650, 82, "green");
  });

  addPage("Sodium", (slide) => {
    title(slide, "Sodium", "Compare similar products before deciding", "The FDA Daily Value for sodium is 2,300 mg per day. The %DV is per labeled serving, and individual recommendations may differ. [2,9]");
    nutritionMini(slide, 92, 310, "Option 1 canned soup", [["Serving size", "1 cup", true], ["Servings/container", "2"], ["Sodium", "520mg  23%", true], ["Total carb", "24g  9%"], ["Protein", "9g"]]);
    nutritionMini(slide, 462, 310, "Option 2 canned soup", [["Serving size", "1 cup", true], ["Servings/container", "2"], ["Sodium", "760mg  33%", true], ["Total carb", "23g  8%"], ["Protein", "10g"]]);
    callout(slide, "How to compare", "First compare the same serving size. Then ask how much you will actually eat, how often you buy it, and what else is in the meal.", 66, 610, 650, 86, "green");
    callout(slide, "Daily Value cue", "For many nutrients, 5% DV or less is generally low and 20% DV or more is generally high. One label line does not make a food universally good or bad.", 66, 724, 650, 92, "blue");
  });

  addPage("Claims and ingredients", (slide) => {
    title(slide, "Ingredient lists and marketing claims", "Front labels can be useful, but they are not the whole story", "Claims may be helpful clues. They do not replace the Nutrition Facts label, ingredient list, serving size, and your health needs. [1,3]");
    const claims = ["No sugar added", "Sugar-free", "Natural", "Multigrain", "Keto", "Low-fat", "High-protein", "Organic"];
    claims.forEach((c, i) => packageCard(slide, "Front", c, 66 + (i % 4) * 170, 296 + Math.floor(i / 4) * 166, 140, 132, i % 2 ? P.white : P.softGreen));
    callout(slide, "Back-of-package checks", "Serving size, total carbohydrate, fiber, added sugar, saturated fat, sodium, and ingredient list. Net carbs is not one of the standard Nutrition Facts lines. [1]", 66, 696, 650, 92, "green");
  });

  addPage("Budget strategies", (slide) => {
    title(slide, "Budget strategies", "Let budget be part of the plan, not a source of shame", "A realistic plan uses what is already available and avoids buying aspirational foods that will not be eaten.");
    image(slide, IMG.budget, "Budget-friendly foods arranged on a table", 66, 292, 310, 210, "cover");
    const items = ["Shop the kitchen first.", "Plan meals around what is already available.", "Compare unit prices.", "Use store brands.", "Use frozen vegetables.", "Use canned beans.", "Buy seasonal produce when useful.", "Freeze leftovers.", "Build pantry backup meals.", "Reduce waste before adding more variety."];
    bullets(slide, items.slice(0, 5), 416, 292, 290, { checkbox: true, gap: 42, size: 11.8 });
    bullets(slide, items.slice(5), 416, 524, 290, { checkbox: true, gap: 42, size: 11.8 });
    callout(slide, "Useful question", "Will I actually eat this before it spoils? That question can protect both your budget and your energy.", 66, 788, 650, 78, "green");
  });

  addPage("Ten-minute meals", (slide) => {
    title(slide, "Ten-minute meal formulas", "Build from a base, a protein, a vegetable or fruit, and flavor", "These are flexible formulas, not prescriptions. Swap based on culture, budget, appetite, allergies, tools, and what is already in the kitchen.");
    const meals = [
      ["Taco or tortilla meal", "Tortilla + beans or protein + cabbage or frozen vegetables + salsa or avocado"],
      ["Rice bowl", "Rice + tofu, egg, fish, or chicken + frozen stir-fry vegetables + sauce"],
      ["Pantry plate", "Crackers or bread + tuna, hummus, or beans + cucumber, carrots, or fruit"],
      ["Soup upgrade", "Canned soup + extra vegetables + beans, chicken, tofu, or egg + whole-grain side"],
    ];
    meals.forEach((m, i) => {
      const x = 66 + (i % 2) * 342, y = 300 + Math.floor(i / 2) * 180;
      shape(slide, "roundRect", x, y, 306, 140, i % 2 ? P.blueSoft : P.softGreen, P.rule, 12);
      text(slide, m[0], x + 18, y + 18, 260, 24, { size: 15, bold: true, color: P.green, face: "Lora" });
      text(slide, m[1], x + 18, y + 56, 260, 58, { size: 11.7, color: P.ink, leading: 1.15 });
    });
    callout(slide, "Backup meal line", "Write one formula on your grocery list. Repeating a meal that works is not boring; it is a way to lower decision fatigue.", 66, 770, 650, 82, "green");
  });

  addPage("Checklist", (slide) => {
    title(slide, "Printable grocery checklist", "Make one list that works for your household", "Use this as a starting point. Add what fits your family, budget, culture, medical needs, and schedule.");
    const left = ["Shop my kitchen first: refrigerator", "Shop my kitchen first: freezer", "Shop my kitchen first: pantry", "Produce", "Protein", "Fiber-rich carbohydrates", "Healthy fats", "Flavor builders", "Dairy or alternatives", "Drinks", "Snacks", "Pantry and freezer backups", "Household or non-food items"];
    left.forEach((l, i) => {
      const x = i < 7 ? 66 : 420;
      const y = i < 7 ? 292 + i * 58 : 292 + (i - 7) * 58;
      shape(slide, "rect", x, y + 10, 12, 12, P.white, P.green);
      text(slide, l, x + 20, y + 5, 165, 20, { size: 10.4, bold: true, color: P.navy });
      shape(slide, "roundRect", x + 188, y, i < 7 ? 150 : 150, 38, P.white, "#CCD8D1", 5);
      text(slide, "Qty", x + 300, y + 10, 34, 14, { size: 8.5, color: P.muted, align: "right" });
    });
    worksheetLine(slide, "Meals planned", 66, 724, 650, 38);
    worksheetLine(slide, "Backup meals", 66, 772, 650, 38);
    worksheetLine(slide, "Already have", 66, 820, 650, 38);
    worksheetLine(slide, "Need to buy / budget", 66, 868, 650, 38);
    worksheetLine(slide, "Store or household notes", 66, 916, 650, 38);
  });

  addPage("Next steps", (slide) => {
    slide.images.add({ blob: logoBytes, contentType: "image/jpeg", alt: "Mindful Diabetes Inc. logo", fit: "cover", geometry: "roundRect", borderRadius: 8, position: { left: 66, top: 72, width: 50, height: 54 } });
    text(slide, "Make the store easier next time", 66, 190, 660, 70, { size: 36, bold: true, color: P.white, face: "Lora" });
    text(slide, "Save one list that worked, one backup meal, and one product comparison. The next grocery trip gets easier when you do not start from scratch.", 70, 292, 650, 58, { size: 15, color: "#E6F2EC", leading: 1.22 });
    const actions = [
      ["Explore the Guide", "mindfuldiabetes.org/guide/", "https://www.mindfuldiabetes.org/guide/"],
      ["Visit Health Tools", "mindfuldiabetes.org/health-tools/", "https://www.mindfuldiabetes.org/health-tools/"],
      ["Try JEIR", "mindfuldiabetes.org/research/", "https://www.mindfuldiabetes.org/research/"],
      ["Support free education", "mindfuldiabetes.org/donation/", "https://www.mindfuldiabetes.org/donation/"],
    ];
    actions.forEach((a, i) => {
      const y = 420 + i * 86;
      const fill = i === 3 ? P.coral : P.white;
      shape(slide, "roundRect", 82, y, 570, 54, fill, "none", 10);
      text(slide, a[0], 106, y + 16, 250, 18, { size: 13, bold: true, color: i === 3 ? P.white : P.green, link: a[2] });
      text(slide, a[1], 360, y + 17, 260, 16, { size: 10.5, color: i === 3 ? "#FFF4EC" : P.muted, align: "right", link: a[2] });
    });
    callout(slide, "Medical disclaimer", "This guide is general education, not medical advice, diagnosis, or treatment. Do not change medication, insulin, glucose targets, or a prescribed medical diet based on this guide.", 82, 790, 570, 86, "orange");
    text(slide, "Mindful Diabetes Inc. | 501(c)(3) nonprofit | Free to share for education", 82, 958, 600, 18, { size: 10, color: "#E6F2EC" });
  });

  addPage("References and safety", (slide) => {
    title(slide, "References and safety", "References and medical disclaimer", "Every numbered citation in this guide appears here.");
    text(slide, "Medical disclaimer", 66, 224, 680, 22, { size: 14, bold: true, color: P.coral });
    text(slide, "This guide provides general health education. It is not medical advice, diagnosis, treatment, nutrition therapy, or a medication plan. Do not change insulin, diabetes medication, cholesterol medication, glucose targets, pregnancy care, kidney-disease care, or any prescribed medical diet because of this guide. For urgent symptoms, seek medical care.", 66, 250, 680, 82, { size: 12, color: P.ink, leading: 1.17 });
    text(slide, "References", 66, 362, 680, 24, { size: 14, bold: true, color: P.green });
    const refText = refs.map((r, i) => `${i + 1}. ${r[0]}. ${r[1]}. ${r[2]}; ${r[3]}. ${r[4]}`).join("\n");
    text(slide, refText, 66, 394, 680, 440, { size: 9.25, color: P.ink, leading: 1.12 });
    callout(slide, "Publication information", "Published July 30, 2026 | Medical review pending | Next scheduled review July 2027 | Accessibility review: basic visual QA completed; PDF/UA tagging not completed.", 66, 864, 650, 82, "green");
  });

  for (let i = 0; i < pages.length; i++) {
    const stem = `page-${String(i + 1).padStart(2, "0")}`;
    await writeBlob(path.join(RENDER_DIR, `${stem}.png`), await deck.export({ slide: pages[i], format: "png", scale: 2 }));
    await fs.writeFile(path.join(LAYOUT_DIR, `${stem}.json`), await (await pages[i].export({ format: "layout" })).text());
  }
  await writeBlob(path.join(TMP_DIR, "grocery-montage.webp"), await deck.export({ format: "webp", montage: true, scale: 1 }));
  const inspect = await deck.inspect({ kind: "slide,textbox,shape,image,notes", maxChars: 20000 });
  await fs.writeFile(`${FINAL_PPTX}.inspect.ndjson`, inspect.ndjson);
  const pptx = await PresentationFile.exportPptx(deck);
  await pptx.save(FINAL_PPTX);
  console.log(JSON.stringify({ FINAL_PPTX, RENDER_DIR, LAYOUT_DIR }, null, 2));
}

main().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});
