import fs from "node:fs/promises";
import path from "node:path";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const ROOT = "/Users/jerrismacbook/Desktop/Mindful-Diabetes-Site";
const OUT_DIR = path.join(ROOT, "Mindful_Diabetes_Free_Guides/03_Fats_Without_Fear");
const ASSET_DIR = path.join(OUT_DIR, "Editable_Source/Rebuilt_Assets");
const TMP_DIR = path.join(ROOT, "tmp_fats_rebuild");
const FINAL_PPTX = path.join(OUT_DIR, "Editable_Source/mindful-diabetes-fats-without-fear-2026-redesigned-corrected.pptx");
const RENDER_DIR = path.join(TMP_DIR, "rendered_pages");
const LAYOUT_DIR = path.join(TMP_DIR, "layouts");
const LOGO = path.join(ROOT, "Mindful_Diabetes_Free_Guides/01_Brand_Assets/Logos/mdi-logo.jpg");
const COVER_PHOTO = path.join(ASSET_DIR, "cover-unsaturated-fat-sources.png");
const BUDGET_PHOTO = path.join(ASSET_DIR, "budget-friendly-fat-sources.png");

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
  ["American Heart Association", "The Facts on Fats", "AHA", "2025", "https://www.heart.org/en/healthy-living/healthy-eating/eat-smart/fats/the-facts-on-fats"],
  ["American Heart Association", "Fats in Foods", "AHA", "2026", "https://www.heart.org/en/healthy-living/healthy-eating/eat-smart/fats/fats-in-foods"],
  ["U.S. Food and Drug Administration", "How to Understand and Use the Nutrition Facts Label", "FDA", "2024", "https://www.fda.gov/food/nutrition-facts-label/how-understand-and-use-nutrition-facts-label"],
  ["U.S. Food and Drug Administration", "Daily Value on the Nutrition and Supplement Facts Labels", "FDA", "2024", "https://www.fda.gov/food/nutrition-facts-label/daily-value-nutrition-and-supplement-facts-labels"],
  ["U.S. Food and Drug Administration and U.S. Environmental Protection Agency", "Advice About Eating Fish", "FDA/EPA", "2024", "https://www.fda.gov/food/consumers/advice-about-eating-fish"],
  ["NIH Office of Dietary Supplements", "Omega-3 Fatty Acids: Fact Sheet for Consumers", "NIH ODS", "2022", "https://ods.od.nih.gov/factsheets/Omega3FattyAcids-Consumer/"],
  ["National Institute on Aging", "What Do We Know About Diet and Prevention of Alzheimer's Disease?", "NIA", "2023", "https://www.nia.nih.gov/health/alzheimers-and-dementia/what-do-we-know-about-diet-and-prevention-alzheimers-disease"],
  ["American Heart Association", "Life's Essential 8", "AHA", "2026", "https://www.heart.org/en/healthy-living/healthy-lifestyle/lifes-essential-8"],
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
    line: { style: "solid", fill: line, width: line === "none" ? 0 : 1.1 },
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
  return s;
}

function title(slide, section, headline, support = "") {
  const long = headline.length > 43;
  text(slide, section.toUpperCase(), 66, 83, 320, 22, { size: 12, bold: true, color: P.coral });
  text(slide, headline, 62, 112, 690, long ? 96 : 76, { size: long ? 31 : 34, bold: true, color: P.navy, face: "Lora", leading: 1.03 });
  if (support) text(slide, support, 66, long ? 218 : 196, 670, 60, { size: 15, color: P.muted, leading: 1.24 });
}

function chrome(slide, page, section) {
  if (page === 1 || page === 20) return;
  slide.images.add({ blob: logoBytes, contentType: "image/jpeg", alt: "Mindful Diabetes Inc. logo", fit: "cover", geometry: "roundRect", borderRadius: 8, position: { left: 58, top: 30, width: 27, height: 29 } });
  text(slide, "Fats Without Fear", 92, 35, 210, 18, { size: 10.5, bold: true, color: P.green, face: "Lora" });
  text(slide, section, 92, 51, 260, 15, { size: 8.8, color: P.muted });
  shape(slide, "line", 58, 75, 700, 0, "none", P.rule);
  shape(slide, "line", 58, 1009, 700, 0, "none", P.rule);
  text(slide, "Mindful Diabetes Inc.", 58, 1020, 185, 18, { size: 8.8, color: P.muted });
  text(slide, "mindfuldiabetes.org", 332, 1020, 155, 18, { size: 8.8, color: P.muted, align: "center" });
  text(slide, `${page}`, 723, 1020, 35, 18, { size: 8.8, color: P.coral, align: "right" });
}

function notes(slide, assetNote = "") {
  slide.speakerNotes.textFrame.setText(`[Sources]\n${refs.map((r, i) => `- [${i + 1}] ${r[0]}, ${r[1]}: ${r[4]}`).join("\n")}\n${assetNote ? `- Asset note: ${assetNote}\n` : ""}`);
}

function bullets(slide, items, x, y, w, opts = {}) {
  items.forEach((item, i) => {
    const yy = y + i * (opts.gap ?? 38);
    shape(slide, "ellipse", x, yy + 5, 10, 10, opts.dot ?? P.coral, "none");
    text(slide, item, x + 22, yy, w - 22, opts.lineH ?? 34, { size: opts.size ?? 13, color: opts.color ?? P.ink, leading: 1.18 });
  });
}

function callout(slide, heading, body, x, y, w, h, tone = "green") {
  const fill = tone === "orange" ? P.coralSoft : P.softGreen;
  const line = tone === "orange" ? "#F3B499" : "#B8D8C8";
  shape(slide, "roundRect", x, y, w, h, fill, line, 10);
  text(slide, heading, x + 17, y + 14, w - 34, 22, { size: 13, bold: true, color: tone === "orange" ? "#8F3519" : P.green });
  text(slide, body, x + 17, y + 42, w - 34, h - 52, { size: 12, color: P.ink, leading: 1.17 });
}

function image(slide, imagePath, alt, x, y, w, h, fit = "cover") {
  slide.images.add({ blob: imageBytes[imagePath], contentType: "image/png", alt, fit, geometry: "roundRect", borderRadius: 14, position: { left: x, top: y, width: w, height: h } });
}

function card(slide, heading, body, x, y, w, h, fill = P.white, accent = P.green) {
  shape(slide, "roundRect", x, y, w, h, fill, P.rule, 10);
  shape(slide, "ellipse", x + 16, y + 18, 18, 18, fill === P.coralSoft ? P.coralSoft : P.softGreen, accent);
  text(slide, heading, x + 48, y + 14, w - 64, 22, { size: 13.5, bold: true, color: P.navy });
  text(slide, body, x + 48, y + 40, w - 64, h - 48, { size: 10.8, color: P.muted, leading: 1.1 });
}

function twoColCards(slide, entries, x, y, cardW = 318, cardH = 88) {
  entries.forEach((e, i) => {
    card(slide, e[0], e[1], x + (i % 2) * (cardW + 28), y + Math.floor(i / 2) * (cardH + 22), cardW, cardH, e[2] ?? P.white, e[3] ?? P.green);
  });
}

function labelBox(slide, name, value, x, y, w, h, fill = P.white) {
  shape(slide, "roundRect", x, y, w, h, fill, P.rule, 10);
  text(slide, name, x + 14, y + 13, w - 28, 22, { size: 13, bold: true, color: P.navy });
  text(slide, value, x + 14, y + 40, w - 28, h - 48, { size: 11.5, color: P.ink, leading: 1.12 });
}

function swapPair(slide, leftTitle, leftItems, rightTitle, rightItems, quote) {
  shape(slide, "roundRect", 66, 310, 310, 365, P.coralSoft, "#F3B499", 12);
  shape(slide, "roundRect", 438, 310, 310, 365, P.softGreen, "#B8D8C8", 12);
  text(slide, leftTitle, 94, 338, 250, 24, { size: 17, bold: true, color: "#8F3519", face: "Lora" });
  bullets(slide, leftItems, 100, 390, 235, { gap: 42, dot: P.coral, size: 12 });
  text(slide, rightTitle, 466, 338, 250, 24, { size: 17, bold: true, color: P.green, face: "Lora" });
  bullets(slide, rightItems, 472, 390, 235, { gap: 42, dot: P.green, size: 12 });
  if (quote) callout(slide, quote[0], quote[1], 66, 742, 682, 80, "green");
}

function oilMatrix(slide) {
  const x = 66, y = 300, widths = [112, 150, 208, 214], rows = [38, 42, 42, 42, 42, 42, 42, 42, 42, 42];
  const data = [
    ["Oil", "Common fit", "Notes", "Remember"],
    ["Olive", "dressings, saute", "flavor varies; often unsaturated", "measure if portions matter"],
    ["Canola", "baking, saute", "neutral taste; usually lower cost", "recipe and access count"],
    ["Soybean/corn", "everyday cooking", "common liquid plant oils", "not all oils taste alike"],
    ["Sunflower", "saute, dressings", "varies by type", "check label if needed"],
    ["Avocado", "higher-heat cooking", "often higher cost", "not required"],
    ["Peanut", "stir-fry", "allergy issue for some people", "choose safely"],
    ["Coconut", "traditional uses", "higher in saturated fat", "not a miracle food"],
    ["Palm", "packaged foods", "higher in saturated fat", "look at frequency"],
    ["Any oil", "flavor and cooking", "all oils are calorie-dense", "use without moralizing"],
  ];
  let yy = y;
  for (let r = 0; r < data.length; r++) {
    let xx = x;
    for (let c = 0; c < data[r].length; c++) {
      shape(slide, "rect", xx, yy, widths[c], rows[r], r === 0 ? P.softGreen : (r % 2 ? P.white : "#FAFCFA"), "#D6DED8");
      text(slide, data[r][c], xx + 8, yy + 9, widths[c] - 16, rows[r] - 12, { size: r === 0 ? 10.7 : 9.8, bold: r === 0, color: P.ink, leading: 1.05 });
      xx += widths[c];
    }
    yy += rows[r];
  }
}

function nutritionLabel(slide) {
  const x = 94, y = 286, w = 315;
  shape(slide, "rect", x, y, w, 500, P.white, P.ink);
  text(slide, "Nutrition Facts", x + 12, y + 12, 220, 34, { size: 25, bold: true, color: P.ink });
  const lines = [
    ["Serving size", "1 cup", true],
    ["Calories", "240", true],
    ["Total Fat", "12g   15%", true],
    ["Saturated Fat", "4g   20%", false],
    ["Trans Fat", "0g", false],
    ["Sodium", "480mg   21%", true],
    ["Total Carbohydrate", "34g   12%", true],
    ["Dietary Fiber", "4g   14%", false],
    ["Added Sugars", "8g   16%", false],
  ];
  let yy = y + 62;
  lines.forEach((l, i) => {
    shape(slide, "line", x + 10, yy - 4, w - 20, 0, "none", i === 1 ? P.ink : P.rule);
    text(slide, l[0], x + 12 + (l[2] ? 0 : 18), yy, 180, 22, { size: l[2] ? 13 : 11.8, bold: l[2], color: P.ink });
    text(slide, l[1], x + 196, yy, 94, 22, { size: l[2] ? 13 : 11.8, bold: l[2], color: P.ink, align: "right" });
    yy += i === 1 ? 50 : 40;
  });
  const callouts = [
    ["1", "Start with serving size.", 454, 306],
    ["2", "Compare saturated fat across similar foods.", 454, 394],
    ["3", "Trans fat has no %DV, but still matters.", 454, 494],
    ["4", "Use %DV: 5% is low, 20% is high.", 454, 594],
    ["5", "For diabetes, carbs and added sugar may also matter.", 454, 696],
  ];
  callouts.forEach((c) => {
    shape(slide, "ellipse", c[2], c[3], 30, 30, P.coral, "none");
    text(slide, c[0], c[2] + 6, c[3] + 5, 18, 16, { size: 11, bold: true, color: P.white, align: "center" });
    text(slide, c[1], c[2] + 42, c[3] + 2, 232, 42, { size: 12, color: P.ink, leading: 1.1 });
  });
}

function worksheet(slide) {
  const fields = ["Meal or eating occasion", "What I usually choose", "One realistic change I could try", "Cost or availability", "Taste and satisfaction", "Use again?", "Notes"];
  const x = 66, y = 282;
  fields.forEach((f, i) => {
    const yy = y + i * 88;
    text(slide, f, x, yy + 18, 205, 24, { size: 12.5, bold: true, color: P.navy });
    shape(slide, "roundRect", x + 225, yy, 456, 60, P.white, "#D6DED8", 8);
  });
  callout(slide, "Keep it printable", "Use one meal at a time. A useful swap should be realistic for your budget, schedule, taste, and health needs.", 66, 912, 682, 64, "green");
}

function addReferencePage(slide) {
  title(slide, "References and safety", "References and medical disclaimer", "Every numbered citation in this guide appears here.");
  text(slide, "Medical disclaimer", 66, 226, 680, 22, { size: 14, bold: true, color: P.coral });
  text(slide, "This guide provides general health education. It is not medical advice, diagnosis, treatment, nutrition therapy, or a medication plan. Do not change insulin, diabetes medication, cholesterol medication, glucose targets, pregnancy care, kidney-disease care, or any prescribed medical diet because of this guide. For urgent symptoms, seek medical care.", 66, 252, 680, 82, { size: 12, color: P.ink, leading: 1.17 });
  text(slide, "References", 66, 368, 680, 24, { size: 14, bold: true, color: P.green });
  const refText = refs.map((r, i) => `${i + 1}. ${r[0]}. ${r[1]}. ${r[2]}; ${r[3]}. ${r[4]}`).join("\n");
  text(slide, refText, 66, 400, 680, 420, { size: 10.1, color: P.ink, leading: 1.18 });
  callout(slide, "Publication information", "Published July 30, 2026 | Next scheduled review July 2027 | Mindful Diabetes Inc., 501(c)(3) nonprofit health education.", 66, 856, 682, 78, "green");
}

async function main() {
  await fs.mkdir(RENDER_DIR, { recursive: true });
  await fs.mkdir(LAYOUT_DIR, { recursive: true });
  logoBytes = await bytes(LOGO);
  for (const p of [COVER_PHOTO, BUDGET_PHOTO]) imageBytes[p] = await bytes(p);

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
  }

  addPage("Cover", (slide) => {
    slide.background.fill = P.cream;
    image(slide, COVER_PHOTO, "Unsaturated fat food sources including salmon, avocado, nuts, seeds, and olive oil", 0, 0, W, 590);
    shape(slide, "rect", 0, 0, W, 590, "#032D28/54", "none");
    slide.images.add({ blob: logoBytes, contentType: "image/jpeg", alt: "Mindful Diabetes Inc. logo", fit: "cover", geometry: "roundRect", borderRadius: 10, position: { left: 62, top: 60, width: 54, height: 58 } });
    text(slide, "Mindful Diabetes Free Guides", 128, 65, 340, 24, { size: 15, bold: true, color: P.white, face: "Lora" });
    text(slide, "501(c)(3) nonprofit health education", 128, 91, 320, 20, { size: 10.5, color: "#E6F2EC" });
    shape(slide, "roundRect", 62, 484, 102, 32, P.coral, "none", 16);
    text(slide, "FREE GUIDE", 76, 492, 78, 16, { size: 10, bold: true, color: P.white, align: "center" });
    text(slide, "Fats Without Fear", 62, 625, 660, 78, { size: 57, bold: true, color: P.navy, face: "Lora", leading: 0.98 });
    text(slide, "A Plain-English Guide to Dietary Fats, Heart Health, and Brain Health", 66, 716, 630, 54, { size: 19, color: P.green, bold: true, leading: 1.14 });
    text(slide, "Learn which fat sources appear most often, what they replace, and how the overall eating pattern fits your health needs.", 66, 792, 650, 58, { size: 15, color: P.ink, leading: 1.22 });
    callout(slide, "Inside", "Fat types, heart and brain context, oil choices, fish and omega-3 notes, label reading, realistic swaps, budget tips, and a printable planner.", 66, 878, 660, 82, "green");
    text(slide, "Published July 30, 2026 | Next review July 2027", 66, 988, 500, 18, { size: 10.5, color: P.muted });
    text(slide, "mindfuldiabetes.org", 594, 988, 140, 18, { size: 10.5, color: P.green, bold: true, align: "right" });
    notes(slide, "Cover photograph generated for this project and visually inspected for no text, no watermarks, and recognizable food sources.");
  });

  addPage("Welcome", (slide) => {
    title(slide, "Welcome", "Fat is not something to fear", "The useful question is not whether fat is allowed. It is which sources show up most often, what they replace, and how the overall pattern fits your needs.");
    image(slide, COVER_PHOTO, "Food sources of dietary fat on a table", 66, 270, 684, 230);
    const goals = [["Know the types", "Saturated, monounsaturated, polyunsaturated, and trans fats."], ["Read labels", "Serving size, saturated fat, trans fat, sodium, added sugar, and %DV."], ["Try swaps", "Replace more often, rather than simply subtracting."], ["Stay personal", "Health conditions, culture, access, and taste all matter."]];
    twoColCards(slide, goals, 66, 536, 318, 88);
    callout(slide, "Individual guidance matters", "Ask for personalized advice if you have pancreatitis, gallbladder disease, very high triglycerides, kidney disease, pregnancy, allergies, an eating disorder history, or a prescribed diet.", 66, 874, 684, 82, "orange");
  });

  addPage("What fat does", (slide) => {
    title(slide, "What fat does", "What dietary fat does in the body", "Fat is an essential nutrient, but it does not act alone. Source, portion, and the rest of the meal still matter.");
    twoColCards(slide, [["Cell membranes", "Fats help form flexible cell structures.", P.softGreen], ["Vitamins A, D, E, K", "Fat helps absorb these fat-soluble vitamins.", P.blueSoft], ["Flavor and texture", "Fat carries flavor and changes mouthfeel.", P.coralSoft], ["Meal satisfaction", "Fat can help a meal feel satisfying, especially with fiber and protein.", P.softGreen], ["Essential fats", "Some fatty acids must come from food.", P.blueSoft]], 66, 300, 318, 95);
    callout(slide, "Simple takeaway", "Fat is useful. The pattern is the point: food source, replacement, frequency, and personal medical needs.", 66, 870, 684, 70, "green");
  });

  addPage("Fat types", (slide) => {
    title(slide, "Fat types", "Saturated, unsaturated, and trans fats", "Foods usually contain mixtures of fats, but their main fat sources can guide everyday choices.");
    twoColCards(slide, [["Saturated fat", "Common in butter, cheese, fatty meats, coconut oil, and palm oil. Limit where appropriate. [1]", P.coralSoft, P.coral], ["Monounsaturated fat", "Common in olive oil, avocado, peanuts, and some nuts. Choose more often. [1]", P.softGreen], ["Polyunsaturated fat", "Common in walnuts, seeds, soybean oil, and fatty fish. Choose more often. [1]", P.blueSoft], ["Industrial trans fat", "Avoid partially hydrogenated oils. Check labels and ingredients. [2]", P.coralSoft, P.coral]], 66, 300, 318, 132);
    callout(slide, "Nuance", "This is not a food purity list. It is a practical pattern: choose unsaturated-fat sources more often, limit saturated-fat sources where appropriate, and avoid trans fat.", 66, 872, 684, 78, "green");
  });

  addPage("Replacement", (slide) => {
    title(slide, "Replacement", "Swap, do not simply subtract", "Reducing saturated fat helps most when it is replaced with unsaturated fats or fiber-rich foods, rather than refined starch or added sugar. [1]");
    swapPair(slide, "Less supportive default", ["Butter-heavy cooking", "Fatty processed meat", "Creamy dressing", "Refined snack alone"], "More supportive replacement", ["Olive oil or avocado when it fits", "Beans, fish, tofu, poultry", "Vinaigrette or yogurt-based option", "Nuts and fruit or hummus and vegetables"], ["Pattern message", "The replacement is the intervention. A meal should still be satisfying enough to repeat."]);
  });

  addPage("Blood fats", (slide) => {
    title(slide, "Blood fats", "LDL, HDL, and triglycerides", "Lab numbers are useful clues, not a complete story. Ask your clinician what your own results mean.");
    labelBox(slide, "LDL cholesterol", "An important cardiovascular-risk marker. Lower targets may be recommended for some people.", 70, 310, 210, 220, P.softGreen);
    labelBox(slide, "HDL cholesterol", "Part of the overall picture. It should not be treated as a simple protective score.", 303, 310, 210, 220, P.blueSoft);
    labelBox(slide, "Triglycerides", "Can be influenced by genetics, diabetes, alcohol, medicines, weight, and dietary pattern.", 536, 310, 210, 220, P.coralSoft);
    text(slide, "No single lab value explains all cardiovascular risk. Blood pressure, smoking status, kidney health, age, family history, glucose, medications, and other factors matter too.", 80, 615, 640, 58, { size: 14, color: P.ink, leading: 1.2 });
    callout(slide, "Medication safety", "Do not change cholesterol treatment, diabetes medicine, insulin, or supplements because of this guide.", 66, 850, 684, 70, "orange");
  });

  addPage("Cooking oils", (slide) => {
    title(slide, "Cooking oils", "Cooking oils are tools, not trophies", "No oil is perfect for every recipe, budget, allergy, or health need. Non-tropical liquid plant oils are generally useful unsaturated-fat sources. [2]");
    oilMatrix(slide);
    callout(slide, "Kitchen note", "Coconut and palm oils are plant-based but higher in saturated fat. Natural does not automatically mean heart-supportive.", 66, 866, 684, 88, "green");
  });

  addPage("Nuts and avocado", (slide) => {
    title(slide, "Nuts and avocado", "Nuts, seeds, and avocado add more than fat", "These foods can bring unsaturated fats, fiber, minerals, texture, and satisfaction. They are calorie-dense, which is a neutral fact, not a moral warning.");
    image(slide, COVER_PHOTO, "Nuts, seeds, avocado, fish, and oil on a table", 66, 282, 310, 285);
    twoColCards(slide, [["Peanuts", "Often lower cost than many tree nuts."], ["Walnuts", "A plant source of omega-3 ALA."], ["Seeds", "Sunflower, pumpkin, chia, and flax can add crunch."], ["Avocado", "Useful in small amounts for texture and flavor."]], 414, 288, 150, 118);
    bullets(slide, ["Buy small amounts if food waste is a concern.", "Store nuts and seeds tightly sealed; refrigerate or freeze when needed.", "Use portions that fit appetite, glucose goals, and overall needs."], 82, 670, 630, { gap: 42 });
  });

  addPage("Fish", (slide) => {
    title(slide, "Fish", "Fish and omega-3 fats need nuance", "Fish can be a useful protein source, and fatty fish provides omega-3 fats. Eating fish is different from assuming everyone needs a supplement.");
    twoColCards(slide, [["Salmon", "Fresh, frozen, or canned can fit."], ["Sardines", "Often budget-friendly and rich in omega-3 fats."], ["Tuna", "Consider mercury guidance, especially in pregnancy. [5]"], ["Plant pattern", "Beans, tofu, nuts, seeds, and oils can support plant-forward meals."]], 66, 300, 318, 100);
    callout(slide, "Supplement caution", "Omega-3 supplements are not universally needed and may interact with medicines such as blood thinners. Ask your clinician what is safe for you. [6]", 66, 808, 684, 86, "orange");
    text(slide, "Pregnancy or breastfeeding: FDA/EPA guidance emphasizes lower-mercury seafood choices and individualized advice. [5]", 78, 918, 620, 32, { size: 12.5, color: P.ink });
  });

  addPage("Dairy fats", (slide) => {
    title(slide, "Dairy fats", "Butter, cheese, cream, and dairy fats", "You do not have to ban familiar foods. It helps to notice frequency, portion, added sugar, and what the food replaces.");
    swapPair(slide, "Current default", ["Butter as the only spread", "Cream-heavy sauce", "Large mild-cheese portion", "Sweetened dairy item"], "Possible swap", ["Avocado, olive oil, or nut butter sometimes", "Tomato-, broth-, or yogurt-based sauce", "Smaller amount of stronger cheese", "Plain or lower-added-sugar option"], ["Keep it realistic", "The point is not to erase pleasure. Use flavor intentionally and choose what fits your health needs."]);
  });

  addPage("Tropical oils", (slide) => {
    title(slide, "Tropical oils", "Plant-based does not always mean low in saturated fat", "Coconut and palm oils are plant-based, but they are higher in saturated fat than many non-tropical liquid plant oils. [2]");
    twoColCards(slide, [["Claims to question", "Miracle fat, metabolism booster, detox, or brain cure."], ["Context matters", "Traditional foods can matter culturally. Frequency and amount still count."], ["When to choose another oil", "If LDL cholesterol or heart risk is a concern, ask what fits your plan."], ["What to use instead", "Olive, canola, soybean, sunflower, corn, avocado, or peanut oil when appropriate."]], 66, 306, 318, 126);
    callout(slide, "Nonjudgmental note", "No single ingredient defines a whole diet. Look at the pattern, the portion, and what happens most often.", 66, 878, 684, 68, "green");
  });

  addPage("Fried foods", (slide) => {
    title(slide, "Fried foods", "The issue is the repeated pattern", "Fried and many ultra-processed foods can combine refined starch, sodium, saturated fat, added sugar, and large portions. One meal is not the whole story.");
    swapPair(slide, "Frequent pattern", ["Fried entree", "Fries", "Sugary drink", "Few vegetables"], "More supportive adjustment", ["Smaller or shared fried portion", "Vegetable side", "Water or lower-sugar drink", "Different cooking method next time"], ["No shame", "Food is not a character test. Patterns can change without turning one meal into a failure."]);
  });

  addPage("Label reading", (slide) => {
    title(slide, "Label reading", "Reading the Nutrition Facts label", "The fastest label check starts with serving size, then saturated fat, trans fat, sodium, added sugars, carbohydrates, and % Daily Value. [3]");
    nutritionLabel(slide);
    callout(slide, "Fast rule of thumb", "For many nutrients, 5% DV or less is low and 20% DV or more is high. The goal may be lower for saturated fat, sodium, and added sugars. [4]", 66, 858, 684, 78, "green");
  });

  addPage("Breakfast swaps", (slide) => {
    title(slide, "Breakfast swaps", "Try one change while keeping breakfast familiar", "Swaps work best when the meal still feels like yours.");
    swapPair(slide, "Current choice", ["Pastry and sweet coffee", "Butter-heavy toast", "Fried processed-meat side", "Sugary cereal"], "Possible swap", ["Plain yogurt, berries, and nuts", "Whole-grain avocado or nut-butter toast", "Eggs with vegetables", "Oats with seeds and fruit"], ["Flexible language", "These are ideas, not assignments. Start with one change that feels doable."]);
  });

  addPage("Meal swaps", (slide) => {
    title(slide, "Meal swaps", "Swap frequency, not identity", "Lunch and dinner changes should respect culture, taste, time, and budget.");
    swapPair(slide, "Current choice", ["Creamy dressing most days", "Meat-centered plate", "Fried side", "Heavy cream sauce"], "Possible swap", ["Olive-oil vinaigrette sometimes", "Beans, fish, tofu, or poultry with vegetables", "Roasted or sauteed vegetable side", "Tomato-, broth-, or yogurt-based option"], ["Featured idea", "You can keep familiar foods while changing what shows up most often."]);
  });

  addPage("Snack swaps", (slide) => {
    title(slide, "Snack swaps", "Snacks are optional", "Not everyone needs snacks. If you use them, keep the pairing practical and satisfying.");
    twoColCards(slide, [["Nuts + fruit", "Portable crunch and sweetness."], ["Hummus + vegetables", "Fiber, flavor, and texture."], ["Yogurt + berries", "Check saturated fat and added sugar."], ["Roasted chickpeas", "Shelf-stable crunch."], ["Popcorn", "A crunchy option; notice butter and salt."], ["Tuna + crackers", "Protein with carbohydrate."]], 66, 300, 318, 92);
    callout(slide, "Medication safety", "If you use insulin or medicines that can cause low blood sugar, ask your care team how snacks and activity should be handled.", 66, 888, 684, 70, "orange");
  });

  addPage("Budget", (slide) => {
    title(slide, "Budget", "Budget-friendly fats count", "Wellness branding is not required for nutritious food. Buy foods you will actually use.");
    image(slide, BUDGET_PHOTO, "Budget-friendly fat sources including peanuts, seeds, eggs, canned fish, oil, nut butter, and beans", 66, 282, 684, 260);
    twoColCards(slide, [["Often practical", "Peanuts, sunflower seeds, canola oil, eggs, canned fish, store-brand nut butter."], ["Reduce waste", "Frozen and canned options may help."], ["Compare carefully", "Use unit price when possible; do not assume premium means better."], ["Store well", "Seal nuts and seeds; refrigerate or freeze when needed."]], 66, 588, 318, 100);
    notes(slide, "Budget food photograph generated for this project and visually inspected for no text, labels, or watermarks.");
  });

  addPage("Myths", (slide) => {
    title(slide, "Myths", "Common fat claims need context", "Nutrition claims can be loud. A calmer answer is usually more useful.");
    twoColCards(slide, [["Fat-free is always healthier", "Not always. Added sugar, sodium, portion, and food quality still matter."], ["Keto supports every heart", "Not automatically. Lab numbers and food sources matter."], ["Coconut oil is a miracle", "No single oil is a cure-all."], ["Everyone needs omega-3 pills", "Food and supplements are different. Ask about safety. [6]"], ["Eating fat equals body fat", "Body weight is more complex than one nutrient."], ["All fats affect cholesterol the same", "Different fats and replacements matter. [1]"]], 66, 300, 318, 92);
  });

  addPage("Planner", (slide) => {
    title(slide, "Planner", "Personal fat-swap planner", "Choose one meal where a change feels realistic. Keep it small enough to try and satisfying enough to repeat.");
    worksheet(slide);
  });

  addPage("Next steps", (slide) => {
    slide.background.fill = P.green;
    shape(slide, "rect", 0, 0, W, H, P.green, "none");
    slide.images.add({ blob: logoBytes, contentType: "image/jpeg", alt: "Mindful Diabetes Inc. logo", fit: "cover", geometry: "roundRect", borderRadius: 10, position: { left: 66, top: 70, width: 58, height: 62 } });
    text(slide, "Heart and brain health summary", 66, 188, 680, 72, { size: 43, bold: true, color: P.white, face: "Lora", leading: 1.03 });
    text(slide, "Dietary-fat choices work inside a larger pattern: vegetables, fiber-rich foods, blood pressure care, cholesterol care, glucose care, movement, sleep, tobacco avoidance, and medical guidance. [7,8]", 70, 286, 640, 72, { size: 16.5, color: "#E6F2EC", leading: 1.18 });
    const buttons = [["Explore The Mindful Plate", "mindfuldiabetes.org/free-guides/"], ["Visit Health Tools", "mindfuldiabetes.org/health-tools/"], ["Try JEIR", "mindfuldiabetes.org/research/"], ["Support free education", "mindfuldiabetes.org/donation/"]];
    buttons.forEach((b, i) => {
      const y = 416 + i * 92;
      shape(slide, "roundRect", 82, y, 560, 56, i === 3 ? P.coral : P.white, "none", 14);
      text(slide, b[0], 108, y + 14, 250, 22, { size: 15, bold: true, color: i === 3 ? P.white : P.green });
      text(slide, b[1], 356, y + 15, 250, 20, { size: 12, color: i === 3 ? "#FFF4EC" : P.muted, align: "right" });
    });
    callout(slide, "Medical disclaimer", "This guide is general education, not medical advice, diagnosis, or treatment. Do not change medication, insulin, cholesterol treatment, or supplements based on this guide.", 82, 800, 560, 90, "orange");
    text(slide, "Mindful Diabetes Inc. | 501(c)(3) nonprofit | Free to share for education", 82, 948, 600, 24, { size: 11.5, color: "#DDEBE5" });
  });

  addPage("References and safety", addReferencePage);

  const inspect = await presentation.inspect({ kind: "slide,textbox,shape,image,table,notes", maxChars: 22000 });
  await fs.writeFile(path.join(TMP_DIR, "final-inspect.ndjson"), inspect.ndjson);
  for (const [index, slide] of presentation.slides.items.entries()) {
    const stem = `page-${String(index + 1).padStart(2, "0")}`;
    await writeBlob(path.join(RENDER_DIR, `${stem}.png`), await presentation.export({ slide, format: "png", scale: 2 }));
    await fs.writeFile(path.join(LAYOUT_DIR, `${stem}.json`), await (await slide.export({ format: "layout" })).text());
  }
  await writeBlob(path.join(TMP_DIR, "contact-sheet.webp"), await presentation.export({ format: "webp", montage: true, scale: 0.6 }));
  const pptx = await PresentationFile.exportPptx(presentation);
  await pptx.save(FINAL_PPTX);
  await fs.writeFile(path.join(TMP_DIR, "source-notes.txt"), `Fats Without Fear rebuilt source.\nOutput PPTX: ${FINAL_PPTX}\nGenerated assets: ${COVER_PHOTO}; ${BUDGET_PHOTO}\nReferences:\n${refs.map((r, i) => `${i + 1}. ${r.join(" | ")}`).join("\n")}\n`);
  console.log(JSON.stringify({ FINAL_PPTX, RENDER_DIR, LAYOUT_DIR }, null, 2));
}

main().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});
