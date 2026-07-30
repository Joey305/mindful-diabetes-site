import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, Presentation, PresentationFile } from "@oai/artifact-tool";

const ROOT = "/Users/jerrismacbook/Desktop/Mindful-Diabetes-Site";
const OUT_DIR = path.join(ROOT, "Mindful_Diabetes_Free_Guides/02_The_Mindful_Plate");
const ASSET_DIR = path.join(OUT_DIR, "Editable_Source/Rebuilt_Assets");
const TMP_DIR = path.join(ROOT, "tmp_mindful_plate_pptx");
const FINAL_PPTX = path.join(OUT_DIR, "Editable_Source/mindful-diabetes-mindful-plate-guide-2026-redesigned-corrected.pptx");
const RENDER_DIR = path.join(TMP_DIR, "rendered_pages");
const LAYOUT_DIR = path.join(TMP_DIR, "layouts");
const LOGO = path.join(ROOT, "Mindful_Diabetes_Free_Guides/01_Brand_Assets/Logos/mdi-logo.jpg");
const COVER_PHOTO = path.join(ASSET_DIR, "cover-balanced-plate.png");
const WELCOME_PHOTO = path.join(ASSET_DIR, "welcome-shared-table.png");

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
  gold: "#F5C66B",
  ink: "#16211D",
  muted: "#5C6C67",
  rule: "#D9E2DA",
  white: "#FFFFFF",
};

const refs = [
  ["American Diabetes Association", "Standards of Care in Diabetes - 2026", "Diabetes Care", "2026", "https://diabetesjournals.org/care/issue/49/Supplement_1"],
  ["American Diabetes Association Nutrition & Wellness Team", "What is the Diabetes Plate?", "ADA Diabetes Food Hub", "2026", "https://diabetesfoodhub.org/blog/what-diabetes-plate"],
  ["U.S. Food and Drug Administration", "How to Understand and Use the Nutrition Facts Label", "FDA", "2024", "https://www.fda.gov/food/nutrition-facts-label/how-understand-and-use-nutrition-facts-label"],
  ["U.S. Food and Drug Administration", "Added Sugars on the Nutrition Facts Label", "FDA", "2026", "https://www.fda.gov/food/nutrition-facts-label/added-sugars-nutrition-facts-label"],
  ["American Heart Association", "The Facts on Fats", "AHA", "2025", "https://www.heart.org/en/healthy-living/healthy-eating/eat-smart/fats/the-facts-on-fats"],
  ["Centers for Disease Control and Prevention", "About the Lifestyle Change Program", "CDC", "2024", "https://www.cdc.gov/diabetes-prevention/lifestyle-change-program/lifestyle-change-program-details.html"],
];

async function writeBlob(filePath, blob) {
  await fs.writeFile(filePath, new Uint8Array(await blob.arrayBuffer()));
}

async function bytes(filePath) {
  const b = await fs.readFile(filePath);
  return b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength);
}

function addShape(slide, geometry, x, y, w, h, fill = "none", line = "none", radius = undefined) {
  return slide.shapes.add({
    geometry,
    position: { left: x, top: y, width: w, height: h },
    fill,
    line: { style: "solid", fill: line, width: line === "none" ? 0 : 1.2 },
    ...(radius ? { borderRadius: radius } : {}),
  });
}

function text(slide, value, x, y, w, h, opts = {}) {
  const s = addShape(slide, "textbox", x, y, w, h, "none", "none");
  s.text = value;
  s.text.style = {
    fontSize: opts.size ?? 16,
    fontSizePt: opts.pt,
    bold: opts.bold ?? false,
    italic: opts.italic ?? false,
    color: opts.color ?? P.ink,
    typeface: opts.face ?? "Lato",
    alignment: opts.align ?? "left",
    verticalAlignment: opts.valign ?? "top",
    lineSpacing: opts.leading ?? 1.16,
    autoFit: opts.autoFit ?? "none",
    wrap: "square",
    insets: { top: 2, right: 4, bottom: 2, left: 4 },
  };
  return s;
}

function title(slide, section, headline, support = "") {
  const longTitle = headline.length > 45;
  text(slide, section.toUpperCase(), 66, 83, 280, 22, { size: 12, bold: true, color: P.coral });
  text(slide, headline, 62, 112, 650, longTitle ? 104 : 76, { size: longTitle ? 32 : 34, bold: true, color: P.navy, face: "Lora", leading: 1.03 });
  if (support) text(slide, support, 66, longTitle ? 224 : 196, 670, 58, { size: 15, color: P.muted, leading: 1.25 });
}

function chrome(slide, page, section) {
  if (page === 1) return;
  slide.images.add({ blob: logoBytes, contentType: "image/jpeg", alt: "Mindful Diabetes Inc. logo", fit: "cover", geometry: "roundRect", borderRadius: 8, position: { left: 58, top: 30, width: 27, height: 29 } });
  text(slide, "The Mindful Plate", 92, 35, 200, 18, { size: 10.5, bold: true, color: P.green, face: "Lora" });
  text(slide, section, 92, 51, 230, 15, { size: 8.8, color: P.muted });
  addShape(slide, "line", 58, 75, 700, 0, "none", P.rule);
  addShape(slide, "line", 58, 1009, 700, 0, "none", P.rule);
  text(slide, "Mindful Diabetes Inc.", 58, 1020, 185, 18, { size: 8.8, color: P.muted });
  text(slide, "mindfuldiabetes.org", 332, 1020, 155, 18, { size: 8.8, color: P.muted, align: "center" });
  text(slide, `${page}`, 723, 1020, 35, 18, { size: 8.8, color: P.coral, align: "right" });
}

function callout(slide, heading, body, x, y, w, h, tone = "green") {
  const fill = tone === "orange" ? P.coralSoft : P.softGreen;
  const line = tone === "orange" ? "#F3B499" : "#B8D8C8";
  addShape(slide, "roundRect", x, y, w, h, fill, line, 10);
  text(slide, heading, x + 17, y + 14, w - 34, 22, { size: 13, bold: true, color: tone === "orange" ? "#8F3519" : P.green });
  text(slide, body, x + 17, y + 42, w - 34, h - 52, { size: 12, color: P.ink, leading: 1.17 });
}

function bullets(slide, items, x, y, w, opts = {}) {
  items.forEach((item, i) => {
    const yy = y + i * (opts.gap ?? 38);
    addShape(slide, "ellipse", x, yy + 5, 10, 10, opts.dot ?? P.coral, "none");
    text(slide, item, x + 22, yy, w - 22, opts.lineH ?? 34, { size: opts.size ?? 13.5, color: opts.color ?? P.ink, leading: 1.18 });
  });
}

function imageCard(slide, imagePath, alt, x, y, w, h, fit = "cover") {
  slide.images.add({ blob: imageBytesByPath[imagePath], contentType: imagePath.endsWith(".jpg") ? "image/jpeg" : "image/png", alt, fit, geometry: "roundRect", borderRadius: 14, position: { left: x, top: y, width: w, height: h } });
}

function notes(slide, assetNote = "") {
  slide.speakerNotes.textFrame.setText(`[Sources]\n- ADA Standards of Care in Diabetes - 2026: ${refs[0][4]}\n- ADA Diabetes Food Hub, What is the Diabetes Plate?: ${refs[1][4]}\n- FDA Nutrition Facts Label resources: ${refs[2][4]} and ${refs[3][4]}\n- American Heart Association, The Facts on Fats: ${refs[4][4]}\n- CDC National Diabetes Prevention Program lifestyle change program: ${refs[5][4]}\n${assetNote ? `- Asset note: ${assetNote}\n` : ""}`);
}

function iconLabel(slide, label, sub, x, y, w, h, color = P.softGreen) {
  addShape(slide, "roundRect", x, y, w, h, P.white, P.rule, 10);
  addShape(slide, "ellipse", x + 16, y + 20, 20, 20, color, P.green);
  text(slide, label, x + 48, y + 16, w - 64, 20, { size: 13.5, bold: true, color: P.navy });
  text(slide, sub, x + 48, y + 39, w - 64, 38, { size: 10.5, color: P.muted, leading: 1.1 });
}

function plateDiagram(slide, x, y, size, big = false) {
  addShape(slide, "ellipse", x, y, size, size, P.white, P.navy);
  addShape(slide, "line", x + size / 2, y + 8, 0, size - 16, "none", P.navy);
  addShape(slide, "line", x + size / 2, y + size / 2, size / 2 - 8, 0, "none", P.navy);
  text(slide, "1/2 plate\nnon-starchy\nvegetables", x + 28, y + size / 2 - 43, size / 2 - 50, 88, { size: big ? 17 : 12, bold: true, color: P.green, align: "center", leading: 1.05 });
  text(slide, "1/4 plate\nprotein", x + size / 2 + 30, y + 70, size / 2 - 52, 52, { size: big ? 17 : 12, bold: true, color: P.navy, align: "center", leading: 1.05 });
  text(slide, "1/4 plate\ncarbohydrate", x + size / 2 + 26, y + size / 2 + 50, size / 2 - 52, 58, { size: big ? 17 : 12, bold: true, color: P.coral, align: "center", leading: 1.05 });
  addShape(slide, "roundRect", x + size - 5, y + size / 2 + 112, 100, 58, P.blueSoft, "#BFDCE6", 12);
  text(slide, "lower-sugar\ndrink", x + size + 7, y + size / 2 + 125, 76, 34, { size: 11, bold: true, color: P.navy, align: "center", leading: 1.08 });
}

function stepFlow(slide, x, y) {
  const steps = [
    ["Food", "Meal or snack"],
    ["Digestion", "Carbs break into glucose"],
    ["Insulin", "Helps cells use glucose"],
    ["Energy", "Use now or store"],
  ];
  steps.forEach(([h, b], i) => {
    const xx = x + i * 168;
    if (i > 0) {
      addShape(slide, "line", xx - 42, y + 55, 56, 0, "none", P.coral);
    }
    addShape(slide, "roundRect", xx, y, 130, 112, i % 2 ? P.blueSoft : P.softGreen, "#C8DAD2", 12);
    addShape(slide, "ellipse", xx + 49, y + 17, 32, 32, P.white, "#C8DAD2");
    text(slide, h, xx + 12, y + 57, 106, 22, { size: 14, bold: true, color: P.navy, align: "center" });
    text(slide, b, xx + 14, y + 80, 102, 25, { size: 9.5, color: P.muted, align: "center", leading: 1.05 });
  });
}

function cards(slide, entries, x, y, cols, cardW, cardH, gapX, gapY) {
  entries.forEach((e, i) => {
    const xx = x + (i % cols) * (cardW + gapX);
    const yy = y + Math.floor(i / cols) * (cardH + gapY);
    iconLabel(slide, e[0], e[1], xx, yy, cardW, cardH, e[2] ?? P.softGreen);
  });
}

function worksheetLine(slide, label, x, y, w, h) {
  text(slide, label, x, y + 12, 210, 24, { size: 12.5, bold: true, color: P.navy });
  addShape(slide, "roundRect", x + 225, y, w - 225, h, P.white, "#D6DED8", 8);
}

function addReferencePage(slide) {
  title(slide, "References and safety", "References and medical disclaimer", "Human-readable sources and the boundaries of this guide.");
  text(slide, "Medical disclaimer", 66, 230, 680, 22, { size: 14, bold: true, color: P.coral });
  text(slide, "This guide provides general health education. It is not medical advice, diagnosis, treatment, nutrition therapy, or a medication plan. Do not change insulin, diabetes medication, glucose targets, pregnancy care, kidney-disease care, or any prescribed medical diet because of this guide. For symptoms of severe low blood sugar, severe high blood sugar, chest pain, trouble breathing, confusion, fainting, or another emergency, seek urgent medical care.", 66, 256, 680, 94, { size: 12.5, color: P.ink, leading: 1.19 });
  text(slide, "References", 66, 382, 680, 24, { size: 14, bold: true, color: P.green });
  const refText = refs.map((r, i) => `${i + 1}. ${r[0]}. ${r[1]}. ${r[2]}; ${r[3]}. ${r[4]}`).join("\n");
  text(slide, refText, 66, 414, 680, 405, { size: 10.7, color: P.ink, leading: 1.22 });
  addShape(slide, "roundRect", 66, 850, 680, 94, P.softGreen, "#B8D8C8", 10);
  text(slide, "Publication information", 84, 868, 220, 20, { size: 12.5, bold: true, color: P.green });
  text(slide, "Published: July 30, 2026 | Medical review: pending | Next scheduled review: July 2027\nMindful Diabetes Inc., 501(c)(3) nonprofit | Free to share for education, with attribution.", 84, 895, 620, 44, { size: 11.5, color: P.ink, leading: 1.18 });
}

let logoBytes;
const imageBytesByPath = {};

async function main() {
  await fs.mkdir(RENDER_DIR, { recursive: true });
  await fs.mkdir(LAYOUT_DIR, { recursive: true });
  logoBytes = await bytes(LOGO);
  for (const p of [COVER_PHOTO, WELCOME_PHOTO, LOGO]) imageBytesByPath[p] = await bytes(p);

  const presentation = Presentation.create({ slideSize: { width: W, height: H } });
  presentation.theme.colorScheme = {
    name: "Mindful Diabetes",
    themeColors: {
      dk1: P.ink, lt1: P.paper, dk2: P.navy, lt2: P.cream,
      accent1: P.green, accent2: P.coral, accent3: P.softGreen,
      accent4: P.blueSoft, accent5: P.gold, accent6: P.muted,
      hlink: P.green, folHlink: P.navy,
    },
  };

  function addPage(section, fn) {
    const slide = presentation.slides.add();
    slide.background.fill = P.paper;
    const pageNum = presentation.slides.items.length;
    chrome(slide, pageNum, section);
    fn(slide, pageNum);
    notes(slide);
    return slide;
  }

  addPage("Cover", (slide) => {
    slide.background.fill = P.cream;
    imageCard(slide, COVER_PHOTO, "Balanced meal with vegetables, protein, carbohydrate, and water", 0, 0, W, 596);
    addShape(slide, "rect", 0, 0, W, 596, "#032D28/58", "none");
    slide.images.add({ blob: logoBytes, contentType: "image/jpeg", alt: "Mindful Diabetes Inc. logo", fit: "cover", geometry: "roundRect", borderRadius: 10, position: { left: 62, top: 60, width: 54, height: 58 } });
    text(slide, "Mindful Diabetes Free Guides", 128, 65, 340, 24, { size: 15, bold: true, color: P.white, face: "Lora" });
    text(slide, "501(c)(3) nonprofit health education", 128, 91, 310, 20, { size: 10.5, color: "#E6F2EC" });
    addShape(slide, "roundRect", 62, 484, 102, 32, P.coral, "none", 16);
    text(slide, "FREE GUIDE", 76, 492, 78, 16, { size: 10, bold: true, color: P.white, align: "center" });
    text(slide, "The Mindful Plate", 62, 625, 660, 78, { size: 59, bold: true, color: P.navy, face: "Lora", leading: 0.98 });
    text(slide, "A Simple Guide to Blood Sugar-Friendly Eating", 66, 720, 610, 34, { size: 20, color: P.green, bold: true });
    text(slide, "Use a flexible plate pattern to build meals with vegetables, protein, carbohydrate, flavor, and a lower-sugar drink - without turning food into a math problem.", 66, 774, 650, 78, { size: 15.2, color: P.ink, leading: 1.24 });
    callout(slide, "Inside", "Quick-start plate visual, food examples, drink comparison, grocery starter list, printable worksheet, safety notes, and references.", 66, 878, 660, 82, "green");
    text(slide, "Published July 30, 2026 | Medical review: pending", 66, 988, 500, 18, { size: 10.5, color: P.muted });
    text(slide, "mindfuldiabetes.org", 594, 988, 140, 18, { size: 10.5, color: P.green, bold: true, align: "right" });
    notes(slide, "Cover photograph generated for this project and visually inspected for no text, no watermarks, and realistic plate proportions.");
  });

  addPage("Welcome", (slide) => {
    title(slide, "Welcome", "A calmer way to build a meal", "This guide is for real kitchens, busy schedules, mixed dishes, familiar foods, and small changes that can actually happen.");
    imageCard(slide, WELCOME_PHOTO, "People sharing a simple meal at a kitchen table", 66, 250, 684, 298);
    const strips = [["Flexible", "Use the plate as a starting point."], ["Practical", "Frozen, canned, dried, and store-brand foods count."], ["Personal", "Culture, budget, appetite, and medical needs still matter."]];
    strips.forEach((s, i) => {
      addShape(slide, "roundRect", 66 + i * 228, 586, 205, 92, i === 1 ? P.blueSoft : P.softGreen, "#C9DAD3", 9);
      text(slide, s[0], 86 + i * 228, 606, 165, 22, { size: 15, bold: true, color: P.green });
      text(slide, s[1], 86 + i * 228, 636, 160, 36, { size: 11.5, color: P.ink, leading: 1.15 });
    });
    text(slide, "If food advice has started to feel like a stack of rules, let this guide lower the noise. The Mindful Plate is a simple way to assemble a meal: vegetables, protein, carbohydrate, drink, and flavor. You do not have to weigh everything or give up foods that matter to you.", 76, 722, 640, 102, { size: 14.5, color: P.ink, leading: 1.22 });
    callout(slide, "This guide cannot replace", "Medical nutrition therapy, medication guidance, glucose targets, insulin changes, pregnancy care, eating-disorder care, or urgent medical attention.", 66, 866, 684, 82, "orange");
    notes(slide, "Welcome photograph generated for this project and visually inspected for no text, labels, or watermarks.");
  });

  addPage("Quick start", (slide) => {
    title(slide, "Quick start", "Start here tonight", "Choose one meal, not your whole life. Use the plate as a quick visual check, then adapt it to the food you actually have.");
    plateDiagram(slide, 108, 270, 420, true);
    bullets(slide, ["Half the plate: non-starchy vegetables when available.", "One quarter: protein such as eggs, fish, tofu, beans, yogurt, chicken, or lean meat.", "One quarter: carbohydrate such as rice, oats, bread, fruit, beans, potato, or tortilla.", "Drink: water, unsweet tea, or another lower-sugar choice."], 80, 742, 650, { gap: 38, size: 13.8 });
    callout(slide, "No all-or-nothing test", "If dinner is pizza, add a salad or vegetable side. If breakfast is rushed, improve the drink. One useful change is enough.", 66, 900, 684, 72, "green");
  });

  addPage("Food and blood sugar", (slide) => {
    title(slide, "Food and blood sugar", "What happens after we eat?", "The short version: food is digested, some foods become glucose, insulin helps glucose move into cells, and many everyday factors affect the pattern.");
    stepFlow(slide, 78, 292);
    text(slide, "During digestion, the body breaks food into smaller parts. Carbohydrate foods usually have the most direct effect on blood glucose because many carbohydrates break down into glucose. Insulin helps move glucose from the blood into cells so it can be used for energy.", 76, 474, 640, 98, { size: 14.2, color: P.ink, leading: 1.24 });
    bullets(slide, ["Protein, fiber, fat, portion, activity, timing, stress, illness, sleep, alcohol, and medicines can all influence glucose patterns.", "Two people can eat a similar meal and see different results."], 80, 606, 650, { gap: 52 });
    callout(slide, "Safety note", "Do not change insulin, diabetes medicine, or glucose targets because of this guide. If readings are often high or low, ask your care team what changes are safest for you.", 66, 832, 684, 92, "orange");
  });

  addPage("Plate method", (slide) => {
    title(slide, "Plate method", "The Mindful Plate method", "A common diabetes plate pattern uses about one-half non-starchy vegetables, one-quarter protein, one-quarter carbohydrate, and water or another low-calorie drink.");
    text(slide, "It can fit bowls, soups, tacos, dal, stir-fries, sandwiches, and leftovers. Mixed dishes can still be balanced by thinking about what is inside them.", 66, 250, 320, 96, { size: 14, color: P.ink, leading: 1.22 });
    bullets(slide, ["Vegetables add volume, color, fiber, and nutrients.", "Protein can help a meal feel more satisfying.", "Carbohydrate foods can fit with attention to portion and pairing.", "A lower-sugar drink keeps the meal simpler."], 70, 380, 330, { gap: 45 });
    plateDiagram(slide, 426, 302, 250);
    callout(slide, "What this does not mean", "Every meal does not need to look separated on a plate. Culture, appetite, budget, and medical needs still matter.", 66, 842, 684, 78, "green");
  });

  addPage("Carbohydrates", (slide) => {
    title(slide, "Carbohydrates", "Carbs without confusion", "Carbohydrates are not automatically forbidden. The type, amount, and what you eat with them matter.");
    cards(slide, [["Grains", "rice, oats, bread, pasta, tortillas", P.blueSoft], ["Starchy vegetables", "potatoes, corn, peas, winter squash", P.softGreen], ["Fruit", "berries, apples, bananas, mango", P.coralSoft], ["Milk and yogurt", "plain milk, yogurt, kefir", P.blueSoft], ["Beans and lentils", "black beans, chickpeas, dal, lentils", P.softGreen], ["Sweets and drinks", "desserts, soda, sweet tea, juice", P.coralSoft]], 66, 280, 2, 318, 82, 28, 24);
    bullets(slide, ["Pair carbohydrate foods with protein, fiber-rich foods, vegetables, and satisfying flavor when possible.", "Total carbohydrate and added sugar can both be useful label checks."], 80, 816, 620, { gap: 40 });
    callout(slide, "Try this", "Choose one carbohydrate you eat often. Keep the food, but experiment with portion and pairing.", 66, 905, 684, 62, "green");
  });

  addPage("Protein", (slide) => {
    title(slide, "Protein", "Protein helps a meal hold together", "Protein foods can support fullness and help make a meal feel more steady. They may come from animal or plant sources, and budget options count.");
    cards(slide, [["Eggs or fish", "eggs, tuna, salmon, sardines", P.blueSoft], ["Poultry or lean meat", "chicken, turkey, lean beef", P.softGreen], ["Tofu or tempeh", "soy options, edamame", P.softGreen], ["Beans or lentils", "also contain carbohydrate", P.coralSoft], ["Plain yogurt", "Greek yogurt, cottage cheese", P.blueSoft], ["Nuts and seeds", "satisfying add-ins", P.softGreen]], 66, 280, 2, 318, 92, 28, 22);
    text(slide, "Beans and lentils are both protein and carbohydrate foods. That does not make them wrong; it just means portion and pairing are useful.", 78, 776, 630, 48, { size: 13.5, color: P.ink, leading: 1.2 });
    callout(slide, "Budget note", "Canned tuna, eggs, beans, lentils, tofu, and plain yogurt can be practical lower-cost protein anchors.", 66, 875, 684, 70, "green");
  });

  addPage("Fiber", (slide) => {
    title(slide, "Fiber", "Fiber is quiet but useful", "Fiber is a type of carbohydrate the body does not fully digest. Many fiber-rich foods can support fullness, bowel regularity, cholesterol patterns, and steadier meals.");
    const ladder = [["Add one vegetable", P.softGreen], ["Add beans or lentils", P.blueSoft], ["Choose oats or whole grains", P.softGreen], ["Add berries, nuts, or seeds", P.blueSoft], ["Drink fluids and notice comfort", P.coralSoft]];
    ladder.forEach((r, i) => {
      addShape(slide, "roundRect", 80 + i * 28, 292 + i * 86, 320, 50, r[1], "#C8DAD2", 8);
      text(slide, r[0], 105 + i * 28, 306 + i * 86, 270, 20, { size: 14, bold: true, color: P.navy });
    });
    text(slide, "The FDA Daily Value for fiber is 28 grams per day based on a 2,000-calorie diet, but individual needs vary.", 452, 310, 250, 84, { size: 15, color: P.ink, leading: 1.2 });
    bullets(slide, ["Add fiber gradually and drink fluids.", "Ask for guidance if fiber worsens symptoms or you have a digestive or kidney condition."], 456, 442, 270, { gap: 62 });
    callout(slide, "Gentle pace", "A sudden jump in fiber can feel uncomfortable. Add one food at a time.", 66, 864, 684, 66, "green");
  });

  addPage("Dietary fat", (slide) => {
    title(slide, "Dietary fat", "Fat adds flavor, texture, and staying power", "Dietary fat is an essential nutrient. The type and food source matter.");
    addShape(slide, "roundRect", 66, 290, 318, 300, P.softGreen, "#B8D8C8", 14);
    addShape(slide, "roundRect", 432, 290, 318, 300, P.coralSoft, "#F3B499", 14);
    text(slide, "Choose more often", 94, 324, 250, 24, { size: 18, bold: true, color: P.green, face: "Lora" });
    bullets(slide, ["Avocado", "Nuts and seeds", "Olive or canola oil", "Fish such as salmon or sardines"], 100, 374, 240, { gap: 38, dot: P.green });
    text(slide, "Choose less often", 460, 324, 250, 24, { size: 18, bold: true, color: "#8F3519", face: "Lora" });
    bullets(slide, ["Butter and cream", "Processed meats", "Deep-fried foods", "Foods with trans fat"], 466, 374, 240, { gap: 38, dot: P.coral });
    text(slide, "A heart-health pattern usually emphasizes unsaturated fats from nuts, seeds, avocado, fish, and non-tropical liquid plant oils while limiting saturated fat and avoiding trans fat.", 84, 654, 640, 66, { size: 13.8, color: P.ink, leading: 1.22 });
    callout(slide, "More detail", "Use the Fats Without Fear guide for saturated, unsaturated, and trans fats in plain language.", 66, 855, 684, 70, "green");
  });

  addPage("Breakfasts", (slide) => {
    title(slide, "Breakfasts", "Breakfasts, if breakfast fits your day", "Not everyone wants or needs breakfast. If you do eat it, breakfast can be a useful place to add protein, fiber, and a lower-sugar drink.");
    cards(slide, [["Eggs + toast + vegetables", "protein, fiber, color, lower-sugar drink", P.blueSoft], ["Yogurt bowl", "plain yogurt, berries, nuts, oats", P.softGreen], ["Oatmeal", "oats, fruit, chia, nut butter", P.coralSoft], ["Beans + tortilla", "beans, egg or tofu, salsa, corn tortilla", P.softGreen]], 66, 306, 2, 318, 126, 28, 30);
    text(slide, "A rushed morning can still count. Keep one shelf-stable backup, one fruit, and one protein option available when you can.", 78, 828, 630, 48, { size: 13.5, color: P.ink, leading: 1.2 });
    callout(slide, "Budget-friendly swaps", "Use store-brand oats, peanut butter, frozen berries, eggs, beans, tofu, or plain yogurt.", 66, 895, 684, 64, "green");
  });

  addPage("Lunches", (slide) => {
    title(slide, "Lunches", "Lunches that do not require a fresh start", "Lunch often happens between work, caregiving, school, appointments, errands, or breaks. It does not need to be a recipe.");
    cards(slide, [["Balanced leftovers bowl", "greens, beans, rice, tofu, salsa", P.softGreen], ["Sandwich", "whole-grain bread, hummus or turkey, vegetables", P.blueSoft], ["Soup", "lentil soup, vegetables, fruit", P.coralSoft], ["No-cook", "tuna, crackers, cucumber, fruit", P.softGreen], ["Greens upgrade", "leftovers plus greens and beans", P.blueSoft]], 66, 286, 1, 684, 80, 0, 18);
    callout(slide, "Restaurant note", "Choose one adjustment: add vegetables, choose water, share fries, or save part for later.", 66, 868, 684, 68, "green");
  });

  addPage("Dinners", (slide) => {
    title(slide, "Dinners", "Cultural dinners can still be balanced", "Healthy eating should not erase family food. Many traditional meals already include vegetables, beans, lentils, fish, lean meats, yogurt, grains, herbs, spices, and shared routines.");
    cards(slide, [["Tacos", "beans or grilled protein, cabbage, salsa, avocado, corn tortillas", P.softGreen], ["Dal", "dal with vegetables, cucumber salad, rice", P.blueSoft], ["Stir-fry", "tofu, chicken, shrimp, or beef, vegetables, rice", P.coralSoft], ["Mediterranean plate", "fish, beans, greens, yogurt sauce, whole grains", P.softGreen], ["Pasta night", "pasta, vegetables, beans or lean protein", P.blueSoft]], 66, 306, 1, 684, 80, 0, 18);
    callout(slide, "Pattern over perfection", "A higher-carbohydrate food can often fit better when the rest of the plate supports it.", 66, 886, 684, 62, "green");
  });

  addPage("Snacks", (slide) => {
    title(slide, "Snacks", "Snacks are optional", "Some people feel better with planned snacks. Others do not need them. Snacks may be useful if meals are far apart, activity changes glucose, medication timing matters, or hunger makes the next meal harder.");
    cards(slide, [["Apple + peanut butter", "fruit plus satisfying fat", P.coralSoft], ["Yogurt + berries", "plain yogurt and fruit", P.blueSoft], ["Hummus + vegetables", "fiber and flavor", P.softGreen], ["Egg + fruit", "simple protein and carbohydrate", P.blueSoft], ["Edamame or chickpeas", "plant-based snack", P.softGreen], ["Nuts + fruit", "portable option", P.coralSoft]], 66, 304, 2, 318, 92, 28, 22);
    callout(slide, "Medication safety", "If you use insulin or medicines that can cause low blood sugar, ask your care team how snacks, activity, and low readings should be handled.", 66, 872, 684, 78, "orange");
  });

  addPage("Drinks", (slide) => {
    title(slide, "Drinks", "Drinks and hidden sugars", "Sugary drinks can raise blood glucose quickly because they are easy to drink fast and do not bring much fiber or fullness.");
    const drinks = [["Water", "No added sugar", P.softGreen], ["Sparkling water", "Check labels if flavored", P.blueSoft], ["Unsweet tea or coffee", "Add-ons can change it", P.softGreen], ["Sweet drink", "Try smaller size or less syrup", P.coralSoft]];
    drinks.forEach((d, i) => {
      const x = 86 + i * 172;
      addShape(slide, "roundRect", x, 310, 114, 190, d[2], "#C8DAD2", 16);
      addShape(slide, "roundRect", x + 33, 352, 48, 88, P.white, "#AFCAC0", 12);
      text(slide, d[0], x - 10, 528, 134, 22, { size: 13, bold: true, color: P.navy, align: "center" });
      text(slide, d[1], x - 10, 556, 134, 34, { size: 10.5, color: P.muted, align: "center", leading: 1.05 });
    });
    bullets(slide, ["The FDA Daily Value for added sugars is 50 grams per day based on a 2,000-calorie diet.", "Start by improving one drink you have often."], 80, 682, 650, { gap: 44 });
    callout(slide, "Try this", "Make one drink change: smaller size, less syrup, unsweet tea, sparkling water, infused water, or water beside the drink.", 66, 876, 684, 74, "green");
  });

  addPage("Portions", (slide) => {
    title(slide, "Portions", "Portions without weighing", "Portions do not need to be exact to be useful. The plate method gives a visual estimate. Labels give serving sizes. Cups, bowls, and hand-based estimates can help when measuring is not realistic.");
    const items = [["Fist", "rough estimate for about one cup of some foods"], ["Palm", "rough estimate for cooked protein"], ["Thumb", "rough guide for a small amount of fat"], ["Label serving", "the amount used for the numbers on a package label"]];
    items.forEach((it, i) => {
      const x = i % 2 ? 430 : 84;
      const y = i > 1 ? 555 : 326;
      addShape(slide, "ellipse", x, y, 120, 120, i % 2 ? P.blueSoft : P.softGreen, "#B8D8C8");
      text(slide, it[0], x + 14, y + 36, 92, 26, { size: 18, bold: true, color: P.navy, align: "center", face: "Lora" });
      text(slide, it[1], x + 150, y + 30, 210, 54, { size: 13, color: P.ink, leading: 1.15 });
    });
    callout(slide, "Keep it kind", "Portion awareness is a tool, not a judgment. If measuring food feels stressful or unsafe, ask for support.", 66, 864, 684, 70, "orange");
  });

  addPage("Sample menu", (slide) => {
    title(slide, "Sample menu", "Three days of flexible ideas", "These are examples, not a prescription. Your calorie, carbohydrate, protein, sodium, kidney, allergy, pregnancy, medication, and glucose needs may be different.");
    const cols = [54, 148, 148, 176, 158];
    const rows = [42, 58, 58, 58];
    const x0 = 66, y0 = 314;
    const values = [
      ["Day", "Breakfast", "Lunch", "Dinner", "Snack"],
      ["1", "Yogurt bowl", "Bean soup", "Fish, greens,\nrice", "Apple +\npeanut butter"],
      ["2", "Eggs + toast", "Hummus\nsandwich", "Tacos with\nbeans", "Yogurt + nuts"],
      ["3", "Oatmeal", "Leftover bowl", "Dal with\nvegetables", "Carrots +\nhummus"],
    ];
    let yy = y0;
    for (let r = 0; r < rows.length; r++) {
      let xx = x0;
      for (let c = 0; c < cols.length; c++) {
        addShape(slide, "rect", xx, yy, cols[c], rows[r], r === 0 ? P.softGreen : P.white, "#D6DED8");
        text(slide, values[r][c], xx + 8, yy + 9, cols[c] - 16, rows[r] - 14, { size: r === 0 ? 11.5 : 11, bold: r === 0, color: P.ink, leading: 1.1 });
        xx += cols[c];
      }
      yy += rows[r];
    }
    text(slide, "Use this page for ideas, then trade foods in and out. Canned, frozen, dried, and leftover foods can all help build a balanced plate.", 78, 642, 620, 52, { size: 13.5, color: P.ink, leading: 1.18 });
    callout(slide, "Vegetarian swap", "Use beans, lentils, tofu, tempeh, edamame, eggs, yogurt, nuts, and seeds when they fit your needs.", 66, 852, 684, 68, "green");
  });

  addPage("Worksheet", (slide) => {
    title(slide, "Worksheet", "Build your own meal", "Choose one meal you already eat. Write down what you could add, reduce, swap, or prepare ahead.");
    worksheetLine(slide, "1/2 plate vegetables", 72, 270, 670, 58);
    worksheetLine(slide, "1/4 plate protein", 72, 350, 670, 58);
    worksheetLine(slide, "1/4 plate carbohydrate", 72, 430, 670, 58);
    worksheetLine(slide, "Drink", 72, 510, 670, 58);
    worksheetLine(slide, "Flavor or fat", 72, 590, 670, 58);
    worksheetLine(slide, "What I can prep ahead", 72, 670, 670, 58);
    worksheetLine(slide, "One change to try this week", 72, 774, 670, 86);
    text(slide, "Small enough to try. Useful enough to notice.", 72, 894, 640, 32, { size: 15, bold: true, color: P.green, face: "Lora", align: "center" });
  });

  addPage("Shopping", (slide) => {
    title(slide, "Shopping", "Grocery starter list", "Use this as a starter list, not a rule. Frozen, canned, dried, and store-brand foods can be practical.");
    cards(slide, [["Vegetables", "fresh, frozen, canned", P.softGreen], ["Fruit", "fresh or frozen", P.blueSoft], ["Protein", "eggs, beans, fish, tofu", P.coralSoft], ["Carbs", "oats, rice, potatoes, bread", P.softGreen], ["Fats", "nuts, seeds, avocado, oils", P.blueSoft], ["Flavor", "garlic, herbs, vinegar, salsa", P.softGreen]], 66, 294, 2, 318, 86, 28, 20);
    bullets(slide, ["Rinse canned beans or vegetables when you want less sodium.", "Frozen produce can reduce waste and cost.", "Store-brand staples can be just as useful."], 80, 792, 630, { gap: 38 });
    callout(slide, "Budget note", "Frozen, canned, dried, and store-brand foods can reduce waste and cost.", 66, 900, 684, 60, "green");
  });

  addPage("Questions and myths", (slide) => {
    title(slide, "Questions and myths", "A few food questions people ask all the time", "Food questions are normal because nutrition advice can be noisy. These short answers are designed to reduce fear, not replace personal guidance.");
    cards(slide, [["Do I stop carbohydrates?", "No. Type, amount, and pairing matter.", P.coralSoft], ["Is fruit too sugary?", "Whole fruit can fit for many people.", P.softGreen], ["Are potatoes forbidden?", "No. Preparation and portion matter.", P.blueSoft], ["Do I need expensive food?", "No. Basic pantry foods count.", P.softGreen], ["Can I keep cultural foods?", "Yes. Adapt portions, sides, and drinks.", P.coralSoft]], 66, 300, 1, 684, 88, 0, 18);
    text(slide, "If a food question is connected to medication, kidney disease, pregnancy, allergies, gastrointestinal symptoms, or disordered eating, ask for personal guidance.", 78, 858, 630, 52, { size: 13.5, color: P.ink, leading: 1.18 });
  });

  addPage("Next steps", (slide) => {
    slide.background.fill = P.green;
    addShape(slide, "rect", 0, 0, W, H, P.green, "none");
    slide.images.add({ blob: logoBytes, contentType: "image/jpeg", alt: "Mindful Diabetes Inc. logo", fit: "cover", geometry: "roundRect", borderRadius: 10, position: { left: 66, top: 70, width: 58, height: 62 } });
    text(slide, "The Mindful Plate", 66, 188, 640, 72, { size: 48, bold: true, color: P.white, face: "Lora" });
    text(slide, "Pick one page to use this week. You might build one balanced dinner, improve one drink, or complete the meal worksheet.", 70, 278, 620, 62, { size: 17, color: "#E6F2EC", leading: 1.2 });
    const buttons = [["Explore free guides", "mindfuldiabetes.org/free-guides/"], ["Join the newsletter", "mindfuldiabetes.org/newsletter/"], ["Visit Health Tools", "mindfuldiabetes.org/health-tools/"], ["Support free education", "mindfuldiabetes.org/donation/"]];
    buttons.forEach((b, i) => {
      const y = 392 + i * 92;
      addShape(slide, "roundRect", 82, y, 560, 56, i === 3 ? P.coral : P.white, "none", 14);
      text(slide, b[0], 108, y + 14, 225, 22, { size: 15, bold: true, color: i === 3 ? P.white : P.green });
      text(slide, b[1], 356, y + 15, 250, 20, { size: 12, color: i === 3 ? "#FFF4EC" : P.muted, align: "right" });
    });
    callout(slide, "Medical disclaimer", "This guide is general education, not medical advice, diagnosis, or treatment. Do not change medication, insulin, or glucose targets based on this guide.", 82, 792, 560, 88, "orange");
    text(slide, "Mindful Diabetes Inc. | 501(c)(3) nonprofit | Free to share for education", 82, 942, 600, 24, { size: 11.5, color: "#DDEBE5" });
  });

  addPage("References and safety", addReferencePage);

  const inspect = await presentation.inspect({ kind: "slide,textbox,shape,image,table,notes", maxChars: 20000 });
  await fs.writeFile(path.join(TMP_DIR, "final-inspect.ndjson"), inspect.ndjson);

  for (const [index, slide] of presentation.slides.items.entries()) {
    const stem = `page-${String(index + 1).padStart(2, "0")}`;
    await writeBlob(path.join(RENDER_DIR, `${stem}.png`), await presentation.export({ slide, format: "png", scale: 2 }));
    await fs.writeFile(path.join(LAYOUT_DIR, `${stem}.json`), await (await slide.export({ format: "layout" })).text());
  }
  await writeBlob(path.join(TMP_DIR, "contact-sheet.webp"), await presentation.export({ format: "webp", montage: true, scale: 0.6 }));
  const pptx = await PresentationFile.exportPptx(presentation);
  await pptx.save(FINAL_PPTX);
  await fs.writeFile(path.join(TMP_DIR, "source-notes.txt"), `Mindful Plate rebuilt source.\nOutput PPTX: ${FINAL_PPTX}\nGenerated image assets: ${COVER_PHOTO}, ${WELCOME_PHOTO}\nPrimary sources:\n${refs.map((r, i) => `${i + 1}. ${r.join(" | ")}`).join("\n")}\n`);
  console.log(JSON.stringify({ FINAL_PPTX, RENDER_DIR, LAYOUT_DIR }, null, 2));
}

main().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});
