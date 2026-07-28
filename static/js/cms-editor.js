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
    return `<div class="cms-block cms-image-placeholder">Reusable section</div>`;
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
    blockSettings.querySelectorAll("[data-block-content], [data-block-setting]").forEach((field) => {
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
    return "<p class='admin-muted'>No settings for this block yet.</p>";
  }

  function updateBlockFromField(block, field) {
    commitChange();
    const value = field.type === "checkbox" ? field.checked : field.value;
    if (field.dataset.blockContent) block.content[field.dataset.blockContent] = value;
    if (field.dataset.blockSetting) block.settings[field.dataset.blockSetting] = field.dataset.blockSetting === "level" ? Number(value) : value;
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
