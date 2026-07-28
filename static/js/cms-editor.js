(function () {
  const root = document.querySelector(".cms-editor");
  if (!root) return;

  const initialScript = document.getElementById("cms-editor-initial");
  const initial = JSON.parse(initialScript.textContent);
  const state = {
    id: initial.id,
    content_type: initial.content_type || "page",
    title: initial.title || "Untitled",
    slug: initial.slug || "",
    status: initial.status || "draft",
    excerpt: initial.excerpt || "",
    featured_image: initial.featured_image || "",
    author: initial.author || "",
    blocks: initial.blocks || [],
    settings: initial.settings || {},
    seo: initial.seo || {},
  };
  const history = { undo: [], redo: [] };
  let selectedBlockId = state.blocks[0] ? state.blocks[0].id : "";
  let draggedBlockType = "";
  let draggedExistingBlockId = "";
  let autosaveTimer = null;
  let unsaved = false;
  let slugTouched = Boolean(state.slug && !state.slug.startsWith("untitled"));

  const canvas = root.querySelector("[data-canvas]");
  const canvasShell = root.querySelector("[data-canvas-shell]");
  const blockSettings = root.querySelector("[data-block-settings]");
  const noBlockMessage = root.querySelector("[data-no-block-message]");
  const saveState = root.querySelector("[data-save-state]");
  const statusLabel = root.querySelector("[data-status-label]");
  const previewLink = root.querySelector("[data-preview-link]");

  const defaults = {
    heading: () => ({ settings: { level: 2, alignment: "left", accent: false, color: "navy" }, content: { text: "New heading" } }),
    rich_text: () => ({ settings: {}, content: { html: "<p>Add your text.</p>" } }),
    image: () => ({ settings: { alignment: "center", width: "standard", frame: false }, content: { src: "", alt: "", caption: "", decorative: false } }),
    button: () => ({ settings: { alignment: "left", style: "green", new_tab: false }, content: { label: "Learn more", url: "/" } }),
    two_columns: () => ({ settings: { ratio: "50-50" }, content: { columns: [{ id: makeId("col"), blocks: [] }, { id: makeId("col"), blocks: [] }] } }),
    three_columns: () => ({ settings: { ratio: "equal" }, content: { columns: [{ id: makeId("col"), blocks: [] }, { id: makeId("col"), blocks: [] }, { id: makeId("col"), blocks: [] }] } }),
    video: () => ({ settings: { frame: false }, content: { url: "" } }),
    callout: () => ({ settings: { tone: "green" }, content: { title: "Helpful note", text: "", icon: "" } }),
    divider: () => ({ settings: { style: "line" }, content: {} }),
    spacer: () => ({ settings: { size: "medium" }, content: {} }),
    quote: () => ({ settings: {}, content: { quote: "Add a quote.", author: "", role: "" } }),
    donation_cta: () => ({ settings: {}, content: { heading: "Support prevention education", body: "Your gift supports Mindful Diabetes education, tools, and community work.", button: "Donate" } }),
    newsletter_signup: () => ({ settings: {}, content: { heading: "Stay up to date", description: "Get new articles and updates from Mindful Diabetes." } }),
  };

  Object.assign(defaults, {
    faq: () => ({ settings: { style: "green", multiple_open: false, faq_schema: true }, content: { heading: "Frequently asked questions", items: [{ first: "Question", second: "<p>Answer</p>" }] } }),
    card_grid: () => ({ settings: { columns: 3, equal_height: true, mobile_horizontal: false }, content: { cards: [{ heading: "Helpful resource", description: "Add a short description.", button: "Learn more", url: "" }] } }),
    statistics: () => ({ settings: { count_up: false }, content: { items: [{ prefix: "", number: "12,500", suffix: "+", label: "People reached through diabetes education", icon: "" }] } }),
    table_of_contents: () => ({ settings: { sticky: false, collapse_mobile: true, highlight_current: true }, content: { heading: "On this page" } }),
    related_posts: () => ({ settings: { count: 3, layout: "cards", show_image: true, show_date: true, show_excerpt: true }, content: { heading: "Related reading", category: "", tags: [], slugs: [] } }),
    featured_content: () => ({ settings: { layout: "image_left" }, content: { slug: "", eyebrow: "Featured", title_override: "", description_override: "", image_override: "", button: "Read more" } }),
    resource_download: () => ({ settings: { email_required: false }, content: { title: "Resource download", description: "", file_url: "", file_type: "PDF", file_size: "", preview_image: "", button: "Download" } }),
    citation: () => ({ settings: { display: "compact" }, content: { authors: "", title: "Article title", journal: "", year: "", doi: "", pubmed_url: "", number: "" } }),
    alert_notice: () => ({ settings: { type: "information" }, content: { heading: "Note", message: "<p>This information is educational.</p>" } }),
    icon_list: () => ({ settings: {}, content: { heading: "", items: [{ icon: "", title: "Practical support", description: "Add a short description.", url: "" }] } }),
    process_steps: () => ({ settings: { layout: "vertical" }, content: { heading: "Step by step", steps: [{ title: "Step", text: "Add a short description." }] } }),
    definition: () => ({ settings: {}, content: { term: "Term", definition: "Simple definition.", explanation: "", source: "" } }),
    comparison_table: () => ({ settings: { highlight_column: 0 }, content: { headers: ["Option A", "Option B"], rows: [{ cells: ["Add comparison text", "Add comparison text"] }] } }),
    side_by_side: () => ({ settings: {}, content: { left_label: "Before", left_title: "Problem", left_text: "", right_label: "After", right_title: "Solution", right_text: "" } }),
    myth_fact: () => ({ settings: {}, content: { myth: "Add the myth.", fact: "Add the fact." } }),
    quiz: () => ({ settings: {}, content: { question: "Knowledge check", answers: [{ text: "Answer A", correct: true }, { text: "Answer B", correct: false }], explanation: "" } }),
    sponsor_logo_grid: () => ({ settings: { grayscale: false }, content: { sponsors: [{ logo: "", name: "Sponsor name", url: "", level: "" }] } }),
    team_profile: () => ({ settings: {}, content: { photo: "", name: "Team member", role: "", credentials: "", bio: "", profile_url: "" } }),
    donation_progress: () => ({ settings: {}, content: { campaign: "Fundraising campaign", raised: 0, goal: 1000, donors: 0, button: "Donate", url: "/donation/" } }),
    volunteer_cta: () => ({ settings: {}, content: { title: "Volunteer with Mindful Diabetes", description: "", time_commitment: "", location: "Remote", button: "Volunteer", url: "/volunteer/" } }),
    event: () => ({ settings: {}, content: { title: "Event", date: "", time: "", timezone: "", location: "", description: "", registration_url: "", calendar_url: "" } }),
    newsletter_archive: () => ({ settings: { count: 3 }, content: { heading: "Newsletter archive", items: [{ title: "Newsletter issue", date: "", description: "Add a short description.", url: "" }] } }),
    author_bio: () => ({ settings: {}, content: { photo: "", name: "", credentials: "", bio: "", profile_url: "" } }),
    article_metadata: () => ({ settings: { show_author: true, show_dates: true, show_category: true, show_reading_time: true }, content: { reviewed_by: "" } }),
    medical_reviewer: () => ({ settings: {}, content: { name: "Medical reviewer", credentials: "", review_date: "", profile_url: "", statement: "Reviewed for educational clarity and accuracy." } }),
    social_sharing: () => ({ settings: { facebook: true, linkedin: true, x: true, email: true, copy: true }, content: { heading: "Share this" } }),
    post_navigation: () => ({ settings: {}, content: { heading: "Keep reading" } }),
    footnotes: () => ({ settings: {}, content: { heading: "Footnotes", notes: ["Add a note."] } }),
    hero_section: () => ({ settings: { height: "compact", alignment: "left", overlay: false }, content: { title: "Hero title", subtitle: "", image: "", primary_label: "", primary_url: "", secondary_label: "", secondary_url: "" } }),
    section_container: () => ({ settings: { width: "standard", background: "soft", spacing: "medium", frame: false }, content: { blocks: [] } }),
    tabs: () => ({ settings: {}, content: { tabs: [{ title: "Overview", body: "<p>Add tab content.</p>" }] } }),
    image_gallery: () => ({ settings: { columns: 3, ratio: "natural", frame: false }, content: { images: [{ src: "", alt: "", caption: "" }] } }),
    image_text: () => ({ settings: { image_position: "left", vertical_alignment: "center" }, content: { image: "", alt: "", heading: "Image and text", text: "", button: "", url: "" } }),
    logo_badge_row: () => ({ settings: {}, content: { badges: [{ image: "", label: "Badge", url: "" }] } }),
    embed: () => ({ settings: { provider: "google_maps" }, content: { url: "" } }),
    recipe_card: () => ({ settings: {}, content: { title: "Recipe", image: "", prep_time: "", cook_time: "", servings: "", ingredients: ["Add an ingredient"], steps: ["Add a step"], nutrition: "", tags: [] } }),
    nutrition_facts: () => ({ settings: {}, content: { serving_size: "", calories: "", carbohydrates: "", fiber: "", protein: "", fat: "", sodium: "", estimated: true } }),
    glucose_tip: () => ({ settings: {}, content: { heading: "Glucose-friendly tip", explanation: "", example: "", source: "" } }),
    meal_swap: () => ({ settings: {}, content: { heading: "Meal swap", swaps: [{ first: "Instead of", second: "Consider" }] } }),
    health_tool_card: () => ({ settings: {}, content: { tool: "health_tools", title_override: "", description: "", button: "Open tool", image: "" } }),
    research_summary: () => ({ settings: {}, content: { question: "Research question", methods: "", finding: "", why_it_matters: "", limitations: "", source: "" } }),
    study_snapshot: () => ({ settings: {}, content: { study_type: "", participants: "", duration: "", population: "", outcome: "", publication: "" } }),
    community_story: () => ({ settings: { permission_confirmed: false }, content: { name: "Anonymous community member", anonymous: true, photo: "", story: "", pull_quote: "", consent_reference: "" } }),
  });

  function makeId(prefix) {
    return `${prefix}_${Math.random().toString(36).slice(2, 10)}`;
  }

  function makeBlock(type) {
    const preset = defaults[type] ? defaults[type]() : defaults.rich_text();
    return { id: makeId("blk"), type, version: 1, settings: preset.settings, content: preset.content };
  }

  function escapeHtml(value) {
    return String(value || "").replace(/[&<>"']/g, (char) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    }[char]));
  }

  function slugify(value) {
    return String(value || "untitled").toLowerCase().trim().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "") || "untitled";
  }

  function snapshot() {
    return JSON.stringify(state);
  }

  function restore(serialized) {
    const next = JSON.parse(serialized);
    Object.keys(state).forEach((key) => delete state[key]);
    Object.assign(state, next);
    selectedBlockId = findBlockById(state.blocks, selectedBlockId) ? selectedBlockId : (state.blocks[0] ? state.blocks[0].id : "");
    syncFields();
    render();
  }

  function commitChange() {
    history.undo.push(snapshot());
    if (history.undo.length > 60) history.undo.shift();
    history.redo = [];
    markUnsaved();
    updateHistoryButtons();
  }

  function markUnsaved() {
    unsaved = true;
    saveState.textContent = "Unsaved";
    clearTimeout(autosaveTimer);
    autosaveTimer = setTimeout(() => saveDraft(false), 25000);
  }

  function markSaved(message) {
    unsaved = false;
    saveState.textContent = message || "Saved";
    clearTimeout(autosaveTimer);
  }

  function updateHistoryButtons() {
    root.querySelector("[data-action='undo']").disabled = history.undo.length === 0;
    root.querySelector("[data-action='redo']").disabled = history.redo.length === 0;
  }

  function findBlockById(blocks, id) {
    for (const block of blocks) {
      if (block.id === id) return block;
      for (const column of block.content?.columns || []) {
        const found = findBlockById(column.blocks || [], id);
        if (found) return found;
      }
      const nested = findBlockById(block.content?.blocks || [], id);
      if (nested) return nested;
    }
    return null;
  }

  function findBlockParent(blocks, id, parent = null) {
    for (let index = 0; index < blocks.length; index += 1) {
      const block = blocks[index];
      if (block.id === id) return { blocks, index, parent };
      for (const column of block.content?.columns || []) {
        const found = findBlockParent(column.blocks || [], id, block);
        if (found) return found;
      }
      const nested = findBlockParent(block.content?.blocks || [], id, block);
      if (nested) return nested;
    }
    return null;
  }

  function removeBlock(id) {
    const location = findBlockParent(state.blocks, id);
    if (!location) return null;
    const [removed] = location.blocks.splice(location.index, 1);
    return removed;
  }

  function duplicateBlock(block) {
    const cloned = JSON.parse(JSON.stringify(block));
    function renew(item) {
      item.id = makeId("blk");
      for (const column of item.content?.columns || []) {
        column.id = makeId("col");
        (column.blocks || []).forEach(renew);
      }
      (item.content?.blocks || []).forEach(renew);
    }
    renew(cloned);
    return cloned;
  }

  function addBlock(type, targetZone = "root", beforeId = "") {
    commitChange();
    const block = makeBlock(type);
    const target = targetBlocks(targetZone);
    if (beforeId) {
      const index = target.findIndex((item) => item.id === beforeId);
      target.splice(index >= 0 ? index : target.length, 0, block);
    } else {
      target.push(block);
    }
    selectedBlockId = block.id;
    render();
  }

  function targetBlocks(zoneId) {
    if (!zoneId || zoneId === "root") return state.blocks;
    for (const block of flattenBlocks(state.blocks)) {
      for (const column of block.content?.columns || []) {
        if (column.id === zoneId) return column.blocks;
      }
      if (block.id === zoneId && Array.isArray(block.content?.blocks)) return block.content.blocks;
    }
    return state.blocks;
  }

  function flattenBlocks(blocks) {
    const all = [];
    for (const block of blocks) {
      all.push(block);
      for (const column of block.content?.columns || []) {
        all.push(...flattenBlocks(column.blocks || []));
      }
      all.push(...flattenBlocks(block.content?.blocks || []));
    }
    return all;
  }

  function moveSelected(direction) {
    const location = findBlockParent(state.blocks, selectedBlockId);
    if (!location) return;
    const nextIndex = location.index + direction;
    if (nextIndex < 0 || nextIndex >= location.blocks.length) return;
    commitChange();
    const [block] = location.blocks.splice(location.index, 1);
    location.blocks.splice(nextIndex, 0, block);
    render();
  }

  function deleteSelected() {
    if (!selectedBlockId) return;
    const block = findBlockById(state.blocks, selectedBlockId);
    if (!block || !window.confirm("Delete this block?")) return;
    commitChange();
    removeBlock(selectedBlockId);
    selectedBlockId = state.blocks[0] ? state.blocks[0].id : "";
    render();
  }

  function render() {
    canvas.innerHTML = "";
    canvas.classList.toggle("is-empty", state.blocks.length === 0);
    if (state.blocks.length === 0) {
      canvas.innerHTML = "<p>Drag a block here to start building.</p>";
    } else {
      state.blocks.forEach((block) => canvas.appendChild(renderEditorBlock(block)));
    }
    syncSettingsPanel();
  }

  function renderEditorBlock(block) {
    const wrapper = document.createElement("section");
    wrapper.className = `cms-editor-block ${block.id === selectedBlockId ? "is-selected" : ""}`;
    wrapper.dataset.blockId = block.id;
    wrapper.innerHTML = toolbarHtml(block) + renderBlockBody(block);
    wrapper.addEventListener("click", (event) => {
      if (!event.target.closest("[data-block-command]")) {
        selectedBlockId = block.id;
        render();
      }
    });
    bindInlineEditing(wrapper, block);
    bindDropZones(wrapper);
    return wrapper;
  }

  function toolbarHtml(block) {
    return `
      <div class="cms-block-toolbar" aria-label="Block controls">
        <button type="button" data-drag-handle draggable="true" data-drag-block-id="${block.id}">Move</button>
        <button type="button" data-block-command="select">Edit</button>
        <button type="button" data-block-command="duplicate">Duplicate</button>
        <button type="button" data-block-command="up">Up</button>
        <button type="button" data-block-command="down">Down</button>
        <button type="button" data-block-command="delete">Delete</button>
      </div>
    `;
  }

  function renderBlockBody(block) {
    const settings = block.settings || {};
    const content = block.content || {};
    if (block.type === "heading") {
      const level = settings.level || 2;
      return `<div class="cms-block cms-block-heading cms-align-${settings.alignment || "left"} cms-color-${settings.color || "navy"}"><h${level} contenteditable="true" data-inline="content.text" class="${settings.accent ? "cms-heading-accent" : ""}">${escapeHtml(content.text || "Heading")}</h${level}></div>`;
    }
    if (block.type === "rich_text") {
      return `<div class="cms-block cms-rich-text" contenteditable="true" data-inline-html="content.html">${content.html || "<p>Add your text.</p>"}</div>`;
    }
    if (block.type === "image") {
      return `<figure class="cms-block cms-image cms-image--${settings.width || "standard"} cms-align-${settings.alignment || "center"} ${settings.frame ? "cms-image--framed" : ""}">
        ${content.src ? `<img src="${escapeHtml(content.src)}" alt="${escapeHtml(content.decorative ? "" : content.alt)}">` : `<div class="cms-image-placeholder">Image</div>`}
        ${content.caption ? `<figcaption>${escapeHtml(content.caption)}</figcaption>` : ""}
      </figure>`;
    }
    if (block.type === "button") {
      return `<div class="cms-block cms-button-row cms-align-${settings.alignment || "left"}"><a class="cms-button cms-button--${settings.style || "green"}" href="${escapeHtml(content.url || "/")}">${escapeHtml(content.label || "Learn more")}</a></div>`;
    }
    if (block.type === "two_columns" || block.type === "three_columns") {
      const className = block.type === "two_columns" ? `cms-columns--two cms-columns--${settings.ratio || "50-50"}` : "cms-columns--three";
      return `<div class="cms-block cms-columns ${className}">
        ${(content.columns || []).map((column) => `<div class="cms-column cms-drop-zone" data-drop-zone="${column.id}">${(column.blocks || []).map((nested) => renderEditorBlock(nested).outerHTML).join("") || "<p class='admin-muted'>Drop blocks here</p>"}</div>`).join("")}
      </div>`;
    }
    if (block.type === "video") {
      return `<div class="cms-block cms-video ${settings.frame ? "cms-video--framed" : ""}"><div class="cms-image-placeholder">${content.url ? "Video preview available after saving" : "Video"}</div></div>`;
    }
    if (block.type === "callout") {
      return `<aside class="cms-block cms-callout cms-callout--${settings.tone || "green"}">${content.icon ? `<span class="cms-callout__icon">${escapeHtml(content.icon)}</span>` : ""}<div><h3>${escapeHtml(content.title || "Helpful note")}</h3><p>${escapeHtml(content.text || "")}</p></div></aside>`;
    }
    if (block.type === "divider") return `<hr class="cms-block cms-divider">`;
    if (block.type === "spacer") return `<div class="cms-block cms-spacer cms-spacer--${settings.size || "medium"}"></div>`;
    if (block.type === "quote") {
      return `<figure class="cms-block cms-quote"><blockquote contenteditable="true" data-inline="content.quote">${escapeHtml(content.quote || "Add a quote.")}</blockquote><figcaption><strong>${escapeHtml(content.author || "")}</strong><span>${escapeHtml(content.role || "")}</span></figcaption></figure>`;
    }
    if (block.type === "donation_cta") {
      return `<section class="cms-block cms-donation-cta"><div><h2>${escapeHtml(content.heading || "Support prevention education")}</h2><p>${escapeHtml(content.body || "")}</p></div><a class="cms-button cms-button--orange" href="/donation/">${escapeHtml(content.button || "Donate")}</a></section>`;
    }
    if (block.type === "newsletter_signup") {
      return `<section class="cms-block cms-newsletter-signup"><div><h2>${escapeHtml(content.heading || "Stay up to date")}</h2><p>${escapeHtml(content.description || "")}</p></div><div class="cms-image-placeholder">Newsletter form</div></section>`;
    }
    if (block.type === "faq") {
      return `<section class="cms-block cms-faq"><h2>${escapeHtml(content.heading || "FAQ")}</h2>${(content.items || []).map((item) => `<details><summary>${escapeHtml(item.first || item.question)}</summary><div>${item.second || item.answer || ""}</div></details>`).join("")}</section>`;
    }
    if (block.type === "card_grid") {
      return `<section class="cms-block cms-card-grid cms-card-grid--${settings.columns || 3}">${(content.cards || []).map((card) => `<article class="cms-resource-card"><h3>${escapeHtml(card.heading)}</h3><p>${escapeHtml(card.description)}</p></article>`).join("")}</section>`;
    }
    if (block.type === "statistics") {
      return `<section class="cms-block cms-statistics">${(content.items || []).map((item) => `<article><strong>${escapeHtml(item.prefix)}${escapeHtml(item.number)}${escapeHtml(item.suffix)}</strong><p>${escapeHtml(item.label)}</p></article>`).join("")}</section>`;
    }
    if (block.type === "table_of_contents") return `<nav class="cms-block cms-table-of-contents"><h2>${escapeHtml(content.heading || "On this page")}</h2><p class="admin-muted">Generated from H2 and H3 headings after saving.</p></nav>`;
    if (block.type === "related_posts") return `<section class="cms-block cms-related-posts"><h2>${escapeHtml(content.heading || "Related reading")}</h2><div class="cms-image-placeholder">Dynamic related posts</div></section>`;
    if (block.type === "featured_content") return `<section class="cms-block cms-featured-content"><div><p class="eyebrow">${escapeHtml(content.eyebrow || "Featured")}</p><h2>${escapeHtml(content.title_override || content.slug || "Featured content")}</h2><p>${escapeHtml(content.description_override || "Pulls from a selected page or post after saving.")}</p></div></section>`;
    if (block.type === "resource_download") return `<section class="cms-block cms-resource-download"><div><h2>${escapeHtml(content.title || "Resource download")}</h2><p>${escapeHtml(content.description || "")}</p><span class="cms-button cms-button--orange">${escapeHtml(content.button || "Download")}</span></div></section>`;
    if (block.type === "citation") return `<aside class="cms-block cms-citation"><p><strong>${escapeHtml(content.title || "Article title")}</strong> ${escapeHtml(content.journal || "")} ${escapeHtml(content.year || "")}</p></aside>`;
    if (block.type === "alert_notice") return `<aside class="cms-block cms-alert cms-alert--${settings.type || "information"}"><h2>${escapeHtml(content.heading || "Note")}</h2><div>${content.message || ""}</div></aside>`;
    if (block.type === "icon_list") return `<section class="cms-block cms-icon-list"><h2>${escapeHtml(content.heading || "Icon list")}</h2><div>${(content.items || []).map((item) => `<article><span>${escapeHtml(item.icon || "✓")}</span><h3>${escapeHtml(item.title)}</h3><p>${escapeHtml(item.description)}</p></article>`).join("")}</div></section>`;
    if (block.type === "process_steps") return `<section class="cms-block cms-process"><h2>${escapeHtml(content.heading || "Step by step")}</h2><ol>${(content.steps || []).map((step, index) => `<li><span>${index + 1}</span><div><h3>${escapeHtml(step.title)}</h3><p>${escapeHtml(step.text)}</p></div></li>`).join("")}</ol></section>`;
    if (block.type === "definition") return `<section class="cms-block cms-definition"><h2>${escapeHtml(content.term || "Term")}</h2><p>${escapeHtml(content.definition || "")}</p></section>`;
    if (block.type === "comparison_table") return `<div class="cms-block cms-comparison-table"><table><thead><tr>${(content.headers || []).map((header) => `<th>${escapeHtml(header)}</th>`).join("")}</tr></thead><tbody>${(content.rows || []).map((row) => `<tr>${(row.cells || []).map((cell) => `<td>${escapeHtml(cell)}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
    if (block.type === "side_by_side") return `<section class="cms-block cms-side-by-side"><article><p class="eyebrow">${escapeHtml(content.left_label)}</p><h3>${escapeHtml(content.left_title)}</h3><p>${escapeHtml(content.left_text)}</p></article><article><p class="eyebrow">${escapeHtml(content.right_label)}</p><h3>${escapeHtml(content.right_title)}</h3><p>${escapeHtml(content.right_text)}</p></article></section>`;
    if (block.type === "myth_fact") return `<section class="cms-block cms-myth-fact"><article><p class="eyebrow">Myth</p><p>${escapeHtml(content.myth)}</p></article><article><p class="eyebrow">Fact</p><p>${escapeHtml(content.fact)}</p></article></section>`;
    if (block.type === "quiz") return `<section class="cms-block cms-quiz"><h2>${escapeHtml(content.question)}</h2><div class="cms-quiz__answers">${(content.answers || []).map((answer) => `<button type="button">${escapeHtml(answer.text)}</button>`).join("")}</div></section>`;
    if (block.type === "section_container") return `<section class="cms-block cms-section-container cms-drop-zone" data-drop-zone="${block.id}">${(content.blocks || []).map((nested) => renderEditorBlock(nested).outerHTML).join("") || "<p class='admin-muted'>Drop blocks into this section</p>"}</section>`;
    if (block.type === "tabs") return `<section class="cms-block cms-tabs">${(content.tabs || []).map((tab) => `<details open><summary>${escapeHtml(tab.title)}</summary><div>${tab.body || ""}</div></details>`).join("")}</section>`;
    if (block.type === "hero_section") return `<section class="cms-block cms-hero-section cms-hero-section--${settings.height || "compact"}"><div><h2>${escapeHtml(content.title)}</h2><p>${escapeHtml(content.subtitle)}</p></div></section>`;
    const title = content.title || content.heading || content.name || content.campaign || content.question || content.term || block.type.replace(/_/g, " ");
    const summary = content.description || content.text || content.bio || content.story || content.explanation || content.finding || "";
    return `<section class="cms-block cms-component-preview"><p class="eyebrow">${escapeHtml(block.type.replace(/_/g, " "))}</p><h2>${escapeHtml(title)}</h2>${summary ? `<p>${escapeHtml(summary)}</p>` : ""}</section>`;
  }

  function bindInlineEditing(wrapper, block) {
    wrapper.querySelectorAll("[contenteditable][data-inline], [contenteditable][data-inline-html]").forEach((element) => {
      element.addEventListener("focus", () => commitChange(), { once: true });
      element.addEventListener("input", () => {
        if (element.dataset.inline === "content.text") block.content.text = element.textContent.trim();
        if (element.dataset.inline === "content.quote") block.content.quote = element.textContent.trim();
        if (element.dataset.inlineHtml === "content.html") block.content.html = element.innerHTML;
        markUnsaved();
        syncSettingsPanel();
      });
    });
  }

  function bindDropZones(scope = document) {
    scope.querySelectorAll("[data-drop-zone]").forEach((zone) => {
      zone.addEventListener("dragover", (event) => {
        event.preventDefault();
        zone.classList.add("is-drop-target");
      });
      zone.addEventListener("dragleave", () => zone.classList.remove("is-drop-target"));
      zone.addEventListener("drop", (event) => {
        event.preventDefault();
        zone.classList.remove("is-drop-target");
        const zoneId = zone.dataset.dropZone || "root";
        if (draggedBlockType) addBlock(draggedBlockType, zoneId);
        if (draggedExistingBlockId) moveExistingBlock(draggedExistingBlockId, zoneId);
        draggedBlockType = "";
        draggedExistingBlockId = "";
      });
    });
  }

  function moveExistingBlock(blockId, zoneId) {
    const block = findBlockById(state.blocks, blockId);
    if (!block) return;
    commitChange();
    const removed = removeBlock(blockId);
    if (!removed) return;
    targetBlocks(zoneId).push(removed);
    selectedBlockId = blockId;
    render();
  }

  function syncSettingsPanel() {
    const block = findBlockById(state.blocks, selectedBlockId);
    noBlockMessage.hidden = Boolean(block);
    blockSettings.hidden = !block;
    if (!block) {
      blockSettings.innerHTML = "";
      return;
    }
    blockSettings.innerHTML = settingsHtml(block);
    blockSettings.querySelectorAll("[data-block-content], [data-block-setting], [data-block-json]").forEach((field) => {
      field.addEventListener("input", () => updateBlockFromField(block, field));
      field.addEventListener("change", () => updateBlockFromField(block, field));
    });
  }

  function settingsHtml(block) {
    const s = block.settings || {};
    const c = block.content || {};
    const textInput = (label, key, value, type = "text") => `<label>${label}<input type="${type}" value="${escapeHtml(value || "")}" data-block-content="${key}"></label>`;
    const textArea = (label, key, value) => `<label>${label}<textarea rows="4" data-block-content="${key}">${escapeHtml(value || "")}</textarea></label>`;
    const select = (label, key, value, options) => `<label>${label}<select data-block-setting="${key}">${options.map((option) => `<option value="${option}" ${value === option ? "selected" : ""}>${option.replace("_", " ")}</option>`).join("")}</select></label>`;
    const checkbox = (label, key, value, target = "setting") => `<label class="cms-checkbox-label"><input type="checkbox" ${value ? "checked" : ""} data-block-${target}="${key}">${label}</label>`;
    if (block.type === "heading") return [
      textInput("Text", "text", c.text),
      select("Level", "level", String(s.level || 2), ["1", "2", "3", "4"]),
      select("Alignment", "alignment", s.alignment || "left", ["left", "center", "right"]),
      select("Color", "color", s.color || "navy", ["navy", "green", "orange", "body"]),
      checkbox("Accent line", "accent", s.accent),
    ].join("");
    if (block.type === "rich_text") return textArea("Rich text", "html", c.html);
    if (block.type === "image") return [
      textInput("Image URL", "src", c.src, "url"),
      textInput("Alt text", "alt", c.alt),
      textInput("Caption", "caption", c.caption),
      checkbox("Decorative image", "decorative", c.decorative, "content"),
      select("Alignment", "alignment", s.alignment || "center", ["left", "center", "right"]),
      select("Width", "width", s.width || "standard", ["narrow", "standard", "wide", "full"]),
      checkbox("Decorative frame", "frame", s.frame),
    ].join("");
    if (block.type === "button") return [
      textInput("Label", "label", c.label),
      textInput("Destination URL", "url", c.url, "url"),
      select("Style", "style", s.style || "green", ["green", "orange"]),
      select("Alignment", "alignment", s.alignment || "left", ["left", "center", "right"]),
      checkbox("Open in new tab", "new_tab", s.new_tab),
    ].join("");
    if (block.type === "two_columns") return select("Column ratio", "ratio", s.ratio || "50-50", ["50-50", "60-40", "40-60"]);
    if (block.type === "video") return [textInput("YouTube or Vimeo URL", "url", c.url, "url"), checkbox("Decorative frame", "frame", s.frame)].join("");
    if (block.type === "callout") return [textInput("Title", "title", c.title), textArea("Text", "text", c.text), textInput("Icon", "icon", c.icon), select("Tone", "tone", s.tone || "green", ["green", "orange", "neutral", "warning"])].join("");
    if (block.type === "spacer") return select("Size", "size", s.size || "medium", ["small", "medium", "large"]);
    if (block.type === "quote") return [textArea("Quote", "quote", c.quote), textInput("Author", "author", c.author), textInput("Role or organization", "role", c.role)].join("");
    if (block.type === "donation_cta") return [textInput("Heading", "heading", c.heading), textArea("Body", "body", c.body), textInput("Button", "button", c.button)].join("");
    if (block.type === "newsletter_signup") return [textInput("Heading", "heading", c.heading), textArea("Description", "description", c.description)].join("");
    return [
      "<p class='admin-muted'>Edit this structured block as JSON for now. Keep field names intact.</p>",
      `<label>Content JSON<textarea rows="10" data-block-json="content">${escapeHtml(JSON.stringify(c, null, 2))}</textarea></label>`,
      `<label>Settings JSON<textarea rows="6" data-block-json="settings">${escapeHtml(JSON.stringify(s, null, 2))}</textarea></label>`,
    ].join("");
  }

  function updateBlockFromField(block, field) {
    commitChange();
    const value = field.type === "checkbox" ? field.checked : field.value;
    if (field.dataset.blockContent) block.content[field.dataset.blockContent] = value;
    if (field.dataset.blockSetting) block.settings[field.dataset.blockSetting] = field.dataset.blockSetting === "level" ? Number(value) : value;
    if (field.dataset.blockJson) {
      try {
        block[field.dataset.blockJson] = JSON.parse(field.value || "{}");
      } catch (error) {
        saveState.textContent = "JSON needs a quick fix";
        return;
      }
    }
    render();
  }

  function syncFields() {
    root.querySelector("[data-field='title']").value = state.title;
    root.querySelector("[data-field='slug']").value = state.slug;
    root.querySelector("[data-field='content_type']").value = state.content_type;
    root.querySelector("[data-field='status']").value = state.status;
    root.querySelector("[data-field='author']").value = state.author;
    root.querySelector("[data-field='excerpt']").value = state.excerpt;
    root.querySelector("[data-field='featured_image']").value = state.featured_image;
    root.querySelector("[data-setting='template']").value = state.settings.template || "standard";
    Object.entries(state.seo || {}).forEach(([key, value]) => {
      const field = root.querySelector(`[data-seo='${key}']`);
      if (!field) return;
      if (field.type === "checkbox") field.checked = Boolean(value);
      else field.value = value || "";
    });
    statusLabel.textContent = state.status.charAt(0).toUpperCase() + state.status.slice(1);
    statusLabel.className = `admin-status admin-status--${state.status}`;
  }

  async function saveDraft(showMessage = true) {
    saveState.textContent = "Saving...";
    try {
      const response = await fetch(root.dataset.saveUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRF-Token": root.dataset.csrfToken },
        body: JSON.stringify(state),
      });
      const result = await response.json();
      if (!response.ok || !result.ok) throw new Error(result.message || "Could not save.");
      Object.assign(state, result.content);
      syncFields();
      markSaved(showMessage ? "Saved" : "Autosaved");
    } catch (error) {
      saveState.textContent = error.message;
      unsaved = true;
    }
  }

  async function publish() {
    if (!window.confirm("Publish this content?")) return;
    saveState.textContent = "Publishing...";
    try {
      const response = await fetch(root.dataset.publishUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRF-Token": root.dataset.csrfToken },
        body: JSON.stringify(state),
      });
      const result = await response.json();
      if (!response.ok || !result.ok) throw new Error(result.message || "Could not publish.");
      Object.assign(state, result.content);
      state.status = "published";
      previewLink.href = result.view_url || root.dataset.previewUrl;
      syncFields();
      markSaved("Published");
    } catch (error) {
      saveState.textContent = error.message;
    }
  }

  root.addEventListener("click", (event) => {
    const commandButton = event.target.closest("[data-block-command]");
    if (commandButton) {
      const blockId = commandButton.closest("[data-block-id]").dataset.blockId;
      selectedBlockId = blockId;
      const command = commandButton.dataset.blockCommand;
      if (command === "duplicate") {
        const location = findBlockParent(state.blocks, selectedBlockId);
        if (location) {
          commitChange();
          location.blocks.splice(location.index + 1, 0, duplicateBlock(location.blocks[location.index]));
          render();
        }
      } else if (command === "up") moveSelected(-1);
      else if (command === "down") moveSelected(1);
      else if (command === "delete") deleteSelected();
      else render();
      return;
    }
    const action = event.target.closest("[data-action]")?.dataset.action;
    if (action === "save") saveDraft();
    if (action === "publish") publish();
    if (action === "undo" && history.undo.length) {
      history.redo.push(snapshot());
      restore(history.undo.pop());
      updateHistoryButtons();
      markUnsaved();
    }
    if (action === "redo" && history.redo.length) {
      history.undo.push(snapshot());
      restore(history.redo.pop());
      updateHistoryButtons();
      markUnsaved();
    }
  });

  root.querySelectorAll("[data-preview-size]").forEach((button) => {
    button.addEventListener("click", () => {
      root.querySelectorAll("[data-preview-size]").forEach((item) => item.setAttribute("aria-pressed", "false"));
      button.setAttribute("aria-pressed", "true");
      canvasShell.dataset.size = button.dataset.previewSize;
    });
  });

  root.querySelectorAll("[data-field]").forEach((field) => {
    field.addEventListener("input", () => {
      commitChange();
      const key = field.dataset.field;
      state[key] = field.value;
      if (key === "slug") slugTouched = true;
      if (key === "title" && !slugTouched) {
        state.slug = slugify(field.value);
        root.querySelector("[data-field='slug']").value = state.slug;
      }
      syncFields();
    });
  });

  root.querySelectorAll("[data-setting]").forEach((field) => {
    field.addEventListener("change", () => {
      commitChange();
      state.settings[field.dataset.setting] = field.value;
    });
  });

  root.querySelectorAll("[data-seo]").forEach((field) => {
    field.addEventListener("input", () => {
      commitChange();
      state.seo[field.dataset.seo] = field.type === "checkbox" ? field.checked : field.value;
    });
    field.addEventListener("change", () => {
      state.seo[field.dataset.seo] = field.type === "checkbox" ? field.checked : field.value;
    });
  });

  root.querySelector("[data-image-upload]")?.addEventListener("change", async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append("image", file);
    saveState.textContent = "Uploading...";
    try {
      const response = await fetch(root.dataset.uploadUrl, {
        method: "POST",
        headers: { "X-CSRF-Token": root.dataset.csrfToken },
        body: formData,
      });
      const result = await response.json();
      if (!response.ok || !result.ok) throw new Error(result.message || "Could not upload.");
      root.querySelector("[data-field='featured_image']").value = result.asset.url;
      state.featured_image = result.asset.url;
      markUnsaved();
    } catch (error) {
      saveState.textContent = error.message;
    }
  });

  root.querySelector("[data-block-search]")?.addEventListener("input", (event) => {
    const query = event.target.value.toLowerCase();
    root.querySelectorAll(".cms-block-library button").forEach((button) => {
      button.hidden = !button.textContent.toLowerCase().includes(query);
    });
  });

  root.querySelectorAll(".cms-block-library button").forEach((button) => {
    button.addEventListener("click", () => addBlock(button.dataset.blockType));
    button.addEventListener("dragstart", () => {
      draggedBlockType = button.dataset.blockType;
      draggedExistingBlockId = "";
    });
  });

  root.addEventListener("dragstart", (event) => {
    const handle = event.target.closest("[data-drag-block-id]");
    if (!handle) return;
    draggedExistingBlockId = handle.dataset.dragBlockId;
    draggedBlockType = "";
  });

  root.querySelectorAll("[data-settings-tab]").forEach((button) => {
    button.addEventListener("click", () => {
      root.querySelectorAll("[data-settings-tab]").forEach((item) => item.setAttribute("aria-pressed", "false"));
      button.setAttribute("aria-pressed", "true");
      root.querySelectorAll("[data-settings-panel]").forEach((panel) => {
        panel.hidden = panel.dataset.settingsPanel !== button.dataset.settingsTab;
      });
    });
  });

  window.addEventListener("beforeunload", (event) => {
    if (!unsaved) return;
    event.preventDefault();
    event.returnValue = "";
  });

  document.addEventListener("submit", (event) => {
    const form = event.target.closest("[data-confirm]");
    if (form && !window.confirm(form.dataset.confirm)) event.preventDefault();
  });

  bindDropZones(document);
  syncFields();
  render();
  updateHistoryButtons();
})();
