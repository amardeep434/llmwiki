"""Site JavaScript as Python string constants — dark emerald three-panel design."""

PRE_PAINT_SCRIPT = (
    "(function(){"
    "var m=localStorage.getItem('llmwiki-mode');"
    "var c=localStorage.getItem('llmwiki-color');"
    "if(m==='light')document.documentElement.setAttribute('data-theme','light');"
    "else if(!m||m==='system'){"
    "if(window.matchMedia('(prefers-color-scheme:light)').matches)"
    "document.documentElement.setAttribute('data-theme','light');}"
    "})()"
)

JS = r"""
(function() {
"use strict";

/* ===== Unified Theme Engine ===== */
/* Two independent axes: color (emerald/vodafone) x mode (dark/light) */

var LLMWIKI_THEMES = window.LLMWIKI_THEMES || {};
var LLMWIKI_THEME_LABELS = window.LLMWIKI_THEME_LABELS || {};

var currentColor = localStorage.getItem("llmwiki-color") || "emerald";
var currentMode = localStorage.getItem("llmwiki-mode") || "dark";

/* Extract color name from stored value */
function getColorName() {
  return currentColor || "emerald";
}

function applyTheme() {
  var colorName = getColorName();
  var key = colorName + "-" + currentMode;
  var vars = LLMWIKI_THEMES[key];
  if (vars) {
    var root = document.documentElement;
    for (var k in vars) {
      if (vars.hasOwnProperty(k)) root.style.setProperty(k, vars[k]);
    }
  }
  document.documentElement.setAttribute("data-theme", currentMode);

  var label = document.getElementById("theme-label");
  if (label) label.textContent = LLMWIKI_THEME_LABELS[key] || key;

  var sel = document.getElementById("theme-select");
  if (sel) sel.value = colorName;

  var btn = document.getElementById("theme-toggle");
  if (btn) btn.textContent = currentMode === "dark" ? "\u25D0" : "\u25D1";
}

function setColorTheme(name) {
  currentColor = name;
  localStorage.setItem("llmwiki-color", name);
  applyTheme();
}

function toggleMode() {
  currentMode = currentMode === "dark" ? "light" : "dark";
  localStorage.setItem("llmwiki-mode", currentMode);
  applyTheme();
}

applyTheme();

/* ===== Sidebar Toggle ===== */
function toggleSidebar() {
  var layout = document.querySelector(".shell");
  if (!layout) return;
  if (window.innerWidth < 1280) {
    layout.classList.toggle("sidebar-open");
  } else {
    layout.classList.toggle("sidebar-collapsed");
  }
}

/* ===== Graph Panel Toggle ===== */
function toggleGraph() {
  var layout = document.querySelector(".shell");
  if (!layout) return;
  if (window.innerWidth < 1280) {
    layout.classList.toggle("graph-open");
  } else {
    layout.classList.toggle("graph-collapsed");
  }
}

/* ===== Command Palette ===== */
var paletteEl = null;
var paletteInput = null;
var paletteResults = null;
var searchIndex = null;
var selectedIdx = -1;
var currentEntries = [];

function getPalette() {
  if (!paletteEl) {
    paletteEl = document.getElementById("command-palette");
    if (paletteEl) {
      paletteInput = paletteEl.querySelector(".palette__input");
      paletteResults = paletteEl.querySelector(".palette__results");
    }
  }
  return paletteEl;
}

function openPalette() {
  var el = getPalette();
  if (!el) return;
  el.hidden = false;
  if (paletteInput) {
    paletteInput.value = "";
    paletteInput.focus();
  }
  selectedIdx = -1;
  currentEntries = [];
  if (paletteResults) paletteResults.innerHTML = "";
  if (!searchIndex) fetchSearchIndex();
}

function closePalette() {
  var el = getPalette();
  if (!el) return;
  el.hidden = true;
  selectedIdx = -1;
}

function fetchSearchIndex() {
  fetch("../search-index.json").catch(function() {
    return fetch("/search-index.json");
  }).then(function(r) { return r.ok ? r.json() : fetch("/search-index.json").then(function(r2) { return r2.json(); }); })
    .then(function(data) { searchIndex = data.entries || data || []; })
    .catch(function() { searchIndex = []; });
}

function fuzzyMatch(text, query) {
  if (!query) return true;
  var lower = text.toLowerCase();
  var q = query.toLowerCase();
  var qi = 0;
  for (var i = 0; i < lower.length && qi < q.length; i++) {
    if (lower[i] === q[qi]) qi++;
  }
  return qi === q.length;
}

function scoreMatch(text, query) {
  if (!query) return 0;
  var lower = text.toLowerCase();
  var q = query.toLowerCase();
  if (lower.indexOf(q) === 0) return 100;
  if (lower.indexOf(q) !== -1) return 80;
  return fuzzyMatch(text, query) ? 50 : 0;
}

function filterEntries(query) {
  if (!searchIndex) return [];
  var q = query.trim();
  if (!q) return searchIndex.slice(0, 20);

  var typeMatch = q.match(/^type:\s*(\S+)\s*(.*)$/i);
  var catMatch = q.match(/^category:\s*(\S+)\s*(.*)$/i);
  var tagMatch = q.match(/^tag:\s*(\S+)\s*(.*)$/i);

  if (typeMatch) {
    var tVal = typeMatch[1].toLowerCase();
    var rest = typeMatch[2];
    return searchIndex.filter(function(e) {
      return e.type && e.type.toLowerCase().indexOf(tVal) !== -1 &&
        (!rest || fuzzyMatch(e.title + " " + (e.body || ""), rest));
    }).slice(0, 30);
  }
  if (catMatch) {
    var cVal = catMatch[1].toLowerCase();
    var cRest = catMatch[2];
    return searchIndex.filter(function(e) {
      return e.category && e.category.toLowerCase().indexOf(cVal) !== -1 &&
        (!cRest || fuzzyMatch(e.title + " " + (e.body || ""), cRest));
    }).slice(0, 30);
  }
  if (tagMatch) {
    var gVal = tagMatch[1].toLowerCase();
    var gRest = tagMatch[2];
    return searchIndex.filter(function(e) {
      var tags = (e.tags || []).join(" ").toLowerCase();
      return tags.indexOf(gVal) !== -1 &&
        (!gRest || fuzzyMatch(e.title + " " + (e.body || ""), gRest));
    }).slice(0, 30);
  }

  var scored = searchIndex.map(function(e) {
    var titleScore = scoreMatch(e.title || "", q);
    var bodyScore = scoreMatch((e.body || "").substring(0, 200), q) * 0.5;
    return { entry: e, score: titleScore + bodyScore };
  }).filter(function(s) { return s.score > 0; });
  scored.sort(function(a, b) { return b.score - a.score; });
  return scored.map(function(s) { return s.entry; }).slice(0, 30);
}

var TYPE_ICONS = {
  "rule": "\u2699", "workflow": "\u21c4", "application": "\u26a1",
  "task": "\u23f0", "report": "\ud83d\udcca", "custom": "\u2b21",
  "default": "\ud83d\udcc4"
};

function getTypeIcon(type) {
  if (!type) return TYPE_ICONS["default"];
  var base = type.split("/")[0].toLowerCase();
  return TYPE_ICONS[base] || TYPE_ICONS["default"];
}

var TYPE_BADGE_MAP = {
  "rule": "beanshell", "beanshell": "beanshell",
  "workflow": "xml", "application": "config",
  "task": "java", "report": "java", "custom": "config",
  "connector-guides": "docs", "iiq-docs": "docs", "docs": "docs",
  "config": "config", "java": "java", "xml": "xml", "tokens": "tokens"
};

function getTypeBadgeClass(type) {
  if (!type) return "config";
  var base = type.split("/")[0].toLowerCase();
  return TYPE_BADGE_MAP[base] || "config";
}

function renderResults(entries) {
  if (!paletteResults) return;
  if (!entries || entries.length === 0) {
    paletteResults.innerHTML = '<div style="padding:16px 20px;font-size:13px;color:var(--ink-subtle);">No results found</div>';
    return;
  }
  var html = "";
  for (var i = 0; i < entries.length; i++) {
    var e = entries[i];
    var cls = i === selectedIdx ? "palette__result palette__result--active" : "palette__result";
    var icon = getTypeIcon(e.type || e.category);
    var cat = e.category || "";
    var badgeCls = getTypeBadgeClass(e.type || e.category);
    html += '<div class="' + cls + '" data-url="' + escapeAttr(e.url || "#") + '" data-idx="' + i + '">';
    html += '<span class="palette__result-icon">' + icon + '</span>';
    html += '<div class="palette__result-info"><span class="palette__result-title">' + escapeHtml(e.title || e.id || "") + '</span>';
    if (cat) html += '<span class="palette__result-path">' + escapeHtml(cat) + '</span>';
    html += '</div>';
    html += '<span class="palette__result-badge"><span class="badge badge--' + badgeCls + '">' + escapeHtml(badgeCls.toUpperCase()) + '</span></span>';
    html += '</div>';
  }
  paletteResults.innerHTML = html;
  var sel = paletteResults.querySelector(".palette__result--active");
  if (sel) sel.scrollIntoView({ block: "nearest" });
}

function escapeHtml(s) {
  var d = document.createElement("div");
  d.appendChild(document.createTextNode(s));
  return d.innerHTML;
}

function escapeAttr(s) {
  return s.replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;");
}

function navigateResult() {
  if (selectedIdx >= 0 && selectedIdx < currentEntries.length) {
    var url = currentEntries[selectedIdx].url;
    if (url) window.location.href = url;
  }
}

/* ===== Keyboard Shortcuts ===== */
var gPressed = false;
var gTimeout = null;

function handleGlobalKeys(e) {
  var tag = (e.target.tagName || "").toLowerCase();
  var inInput = tag === "input" || tag === "textarea" || tag === "select" || e.target.isContentEditable;

  if (inInput) {
    if (e.key === "Escape") { e.target.blur(); closePalette(); }
    return;
  }

  if ((e.metaKey || e.ctrlKey) && e.key === "k") {
    e.preventDefault();
    if (getPalette() && !getPalette().hidden) closePalette();
    else openPalette();
    return;
  }
  if (e.key === "/") { e.preventDefault(); openPalette(); return; }
  if (e.key === "?" && !e.ctrlKey && !e.metaKey) { e.preventDefault(); toggleKeyboardHelp(); return; }
  if (e.key === "Escape") { closePalette(); hideKeyboardHelp(); return; }
  if (e.key === "j" || e.key === "k") { navigateTableRows(e.key === "j" ? 1 : -1); return; }

  if (e.key === "g") {
    if (gPressed) return;
    gPressed = true;
    clearTimeout(gTimeout);
    gTimeout = setTimeout(function() { gPressed = false; }, 800);
    return;
  }
  if (gPressed) {
    gPressed = false;
    clearTimeout(gTimeout);
    if (e.key === "h") window.location.href = "/";
    else if (e.key === "c") window.location.href = "/categories/";
    else if (e.key === "g") window.location.href = "/graph.html";
    return;
  }
}

/* ===== Keyboard Help Modal ===== */
function toggleKeyboardHelp() {
  var el = document.getElementById("kbd-help");
  if (el) { el.hidden = !el.hidden; return; }
  var overlay = document.createElement("div");
  overlay.id = "kbd-help";
  overlay.className = "palette-overlay";
  overlay.innerHTML =
    '<div class="palette" style="padding:var(--sp-6);max-width:420px;">' +
    '<h2 style="font-size:16px;font-weight:600;margin-bottom:var(--sp-4);">Keyboard Shortcuts</h2><dl style="display:grid;grid-template-columns:auto 1fr;gap:8px 16px;font-size:13px;">' +
    '<dt><kbd>/</kbd> or <kbd>\u2318K</kbd></dt><dd>Open search</dd>' +
    '<dt><kbd>j</kbd> / <kbd>k</kbd></dt><dd>Next / prev row</dd>' +
    '<dt><kbd>g</kbd> <kbd>h</kbd></dt><dd>Go home</dd>' +
    '<dt><kbd>g</kbd> <kbd>c</kbd></dt><dd>Categories</dd>' +
    '<dt><kbd>g</kbd> <kbd>g</kbd></dt><dd>Graph</dd>' +
    '<dt><kbd>?</kbd></dt><dd>This help</dd>' +
    '<dt><kbd>Esc</kbd></dt><dd>Close</dd>' +
    '</dl></div>';
  overlay.addEventListener("click", function(ev) {
    if (ev.target === overlay) overlay.hidden = true;
  });
  document.body.appendChild(overlay);
}

function hideKeyboardHelp() {
  var el = document.getElementById("kbd-help");
  if (el) el.hidden = true;
}

/* ===== Table Row Navigation ===== */
function navigateTableRows(direction) {
  var rows = document.querySelectorAll("table tbody tr:not(.hidden)");
  if (!rows.length) return;
  var current = document.querySelector("table tbody tr.row-focus");
  var idx = -1;
  if (current) {
    for (var i = 0; i < rows.length; i++) {
      if (rows[i] === current) { idx = i; break; }
    }
    current.classList.remove("row-focus");
  }
  idx += direction;
  if (idx < 0) idx = 0;
  if (idx >= rows.length) idx = rows.length - 1;
  rows[idx].classList.add("row-focus");
  rows[idx].scrollIntoView({ block: "nearest" });
}

/* ===== Copy Code Buttons ===== */
function initCopyButtons() {
  var copyBtns = document.querySelectorAll(".code-block__copy");
  for (var i = 0; i < copyBtns.length; i++) {
    (function(btn) {
      btn.addEventListener("click", function() {
        var block = btn.closest(".code-block");
        if (!block) return;
        var pre = block.querySelector("pre");
        if (!pre) return;
        var text = pre.textContent;
        navigator.clipboard.writeText(text).then(function() {
          btn.textContent = "Copied!";
          setTimeout(function() { btn.textContent = "Copy"; }, 1500);
        }).catch(function() {
          btn.textContent = "Failed";
          setTimeout(function() { btn.textContent = "Copy"; }, 1500);
        });
      });
    })(copyBtns[i]);
  }

  /* Also add copy buttons to bare pre>code blocks */
  var blocks = document.querySelectorAll("pre");
  for (var j = 0; j < blocks.length; j++) {
    var pre = blocks[j];
    if (pre.closest(".code-block")) continue;
    if (pre.querySelector(".copy-btn")) continue;
    var btn = document.createElement("button");
    btn.className = "copy-btn";
    btn.textContent = "Copy";
    btn.setAttribute("aria-label", "Copy code");
    btn.addEventListener("click", (function(preEl, btnEl) {
      return function() {
        var code = preEl.querySelector("code");
        var text = code ? code.textContent : preEl.textContent;
        navigator.clipboard.writeText(text).then(function() {
          btnEl.textContent = "Copied!";
          setTimeout(function() { btnEl.textContent = "Copy"; }, 2000);
        }).catch(function() {
          btnEl.textContent = "Failed";
          setTimeout(function() { btnEl.textContent = "Copy"; }, 2000);
        });
      };
    })(pre, btn));
    pre.appendChild(btn);
  }
}

/* ===== Filter Bar ===== */
function initFilterBar() {
  var input = document.querySelector(".filter-bar__input");
  if (!input) return;
  var countEl = document.querySelector(".filter-bar__count");
  input.addEventListener("input", function() {
    var query = input.value.toLowerCase();
    var rows = document.querySelectorAll("table tbody tr");
    var cards = document.querySelectorAll(".cards-grid .card");
    var visible = 0;
    for (var i = 0; i < rows.length; i++) {
      var row = rows[i];
      var text = row.textContent.toLowerCase();
      var tags = (row.getAttribute("data-tags") || "").toLowerCase();
      var show = !query || text.indexOf(query) !== -1 || tags.indexOf(query) !== -1;
      row.classList.toggle("hidden", !show);
      if (show) visible++;
    }
    for (var j = 0; j < cards.length; j++) {
      var card = cards[j];
      var cText = card.textContent.toLowerCase();
      var cTags = (card.getAttribute("data-tags") || "").toLowerCase();
      var cShow = !query || cText.indexOf(query) !== -1 || cTags.indexOf(query) !== -1;
      card.style.display = cShow ? "" : "none";
      if (cShow) visible++;
    }
    if (countEl) countEl.textContent = visible + " items";
  });
}

/* ===== Table Sorting ===== */
function initTableSorting() {
  var headers = document.querySelectorAll("thead th");
  for (var h = 0; h < headers.length; h++) {
    (function(th, colIdx) {
      th.addEventListener("click", function() {
        var table = th.closest("table");
        if (!table) return;
        sortTable(table, colIdx, th);
      });
    })(headers[h], h);
  }
}

function sortTable(table, colIdx, th) {
  var tbody = table.querySelector("tbody");
  if (!tbody) return;
  var rows = Array.prototype.slice.call(tbody.querySelectorAll("tr"));
  var dir = th.getAttribute("data-sort-dir") === "asc" ? "desc" : "asc";
  var allTh = table.querySelectorAll("thead th");
  for (var i = 0; i < allTh.length; i++) allTh[i].removeAttribute("data-sort-dir");
  th.setAttribute("data-sort-dir", dir);
  rows.sort(function(a, b) {
    var aVal = (a.cells[colIdx] || {}).textContent || "";
    var bVal = (b.cells[colIdx] || {}).textContent || "";
    var aNum = parseFloat(aVal);
    var bNum = parseFloat(bVal);
    if (!isNaN(aNum) && !isNaN(bNum)) {
      return dir === "asc" ? aNum - bNum : bNum - aNum;
    }
    var cmp = aVal.localeCompare(bVal);
    return dir === "asc" ? cmp : -cmp;
  });
  for (var j = 0; j < rows.length; j++) tbody.appendChild(rows[j]);
}

/* ===== Sidebar Category Tree ===== */
function initSidebarTree() {
  var headers = document.querySelectorAll(".sidebar-section-header");
  for (var i = 0; i < headers.length; i++) {
    headers[i].addEventListener("click", function() {
      this.parentElement.classList.toggle("collapsed");
    });
  }
  var path = window.location.pathname;
  var items = document.querySelectorAll(".sidebar__item[data-href]");
  for (var j = 0; j < items.length; j++) {
    var href = items[j].getAttribute("data-href");
    if (href && path.indexOf(href) !== -1) {
      items[j].classList.add("sidebar__item--active");
    }
  }
}

/* ===== Bottom Tab Bar (Mobile) ===== */
function initBottomTabs() {
  var tabs = document.querySelectorAll(".bottom-tabs a");
  for (var i = 0; i < tabs.length; i++) {
    tabs[i].addEventListener("click", function(e) {
      var action = this.getAttribute("data-action");
      if (action === "search") { e.preventDefault(); openPalette(); }
      else if (action === "sidebar") { e.preventDefault(); toggleSidebar(); }
      else if (action === "graph") { e.preventDefault(); toggleGraph(); }
    });
  }
}

/* ===== Highlight.js ===== */
function initHighlight() {
  if (typeof hljs !== "undefined") hljs.highlightAll();
}

/* ===== Graph View Toggle ===== */
function initGraphToggle() {
  var btns = document.querySelectorAll("[data-gview]");
  if (!btns.length) return;
  for (var i = 0; i < btns.length; i++) {
    btns[i].addEventListener("click", function() {
      for (var j = 0; j < btns.length; j++) btns[j].classList.remove("active");
      this.classList.add("active");
      var view = this.getAttribute("data-gview");
      var forceEl = document.getElementById("graph-force");
      var neuralEl = document.getElementById("graph-neural");
      if (forceEl) forceEl.style.display = view === "force" ? "block" : "none";
      if (neuralEl) neuralEl.style.display = view === "neural" ? "block" : "none";
      if (view === "neural" && neuralEl && !neuralEl.getAttribute("data-init")) {
        neuralEl.setAttribute("data-init", "1");
        initNeuralGraph(neuralEl);
      }
    });
  }
}

/* ===== Neural Network Graph (Canvas-based) ===== */
function initNeuralGraph(container) {
  if (!container) return;
  fetch("/cross-references.json")
    .then(function(r) { return r.json(); })
    .then(function(graph) { renderNeuralGraph(container, graph); })
    .catch(function() {
      container.innerHTML = '<p style="padding:40px;text-align:center;color:var(--ink-subtle);">Neural graph unavailable</p>';
    });
}

function renderNeuralGraph(container, graph) {
  var nodes = graph.nodes || [];
  var edges = graph.edges || [];
  if (nodes.length < 2) {
    container.innerHTML = '<p style="padding:40px;text-align:center;color:var(--ink-subtle);">Not enough nodes for neural view</p>';
    return;
  }

  /* Use content type columns from embedded data, or fall back to category grouping */
  var ctColumns = window.LLMWIKI_CT_COLUMNS;

  /* Content type detection matching Python _detect_content_type */
  var SOURCE_LANGS = {java:1,python:1,javascript:1,typescript:1,go:1,rust:1,csharp:1,ruby:1,kotlin:1,swift:1,scala:1,php:1,c:1,cpp:1};
  var XML_EXTS = {".xml":1,".xsl":1,".xsd":1,".wsdl":1};
  var DOC_EXTS = {".md":1,".mdx":1,".rst":1};
  var CFG_LANGS = {properties:1,json:1,yaml:1,toml:1,ini:1,cfg:1};
  var CFG_EXTS = {".properties":1,".json":1,".yaml":1,".yml":1,".toml":1,".ini":1,".env":1,".cfg":1};

  function detectContentType(n) {
    var cat = (n.type || "").toLowerCase();
    /* Detect from category path (the only reliable field on graph nodes) */
    if (cat.indexOf("beanshell") === 0) return "Inline Scripts";
    if (cat === "tokens") return "Token Registry";
    if (cat.indexOf("connector-guides") === 0 || cat.indexOf("iiq-docs") === 0 || cat === "docs") return "Documentation";
    if (cat.indexOf("com/") === 0 || cat.indexOf("sailpoint/") === 0 || cat.indexOf("bsh/") === 0) return "Source Code";
    if (cat === "config" || cat.indexOf("xml") === 0) return "Configuration";
    /* Everything else (Rule, Workflow, EmailTemplate, Form, Task, SSF, Application, etc.) */
    return "XML / Markup";
  }

  /* Color mapping for content type CSS variables */
  var CT_COLOR_MAP = {
    "node-java": "#f59e0b", "node-xml": "#6366f1", "node-beanshell": "#ec4899",
    "node-config": "#8b5cf6", "node-tokens": "#f97316", "node-docs": "#10b981"
  };

  /* Build columns from content type groups or detect automatically */
  var columns = [];
  if (ctColumns && ctColumns.length > 0) {
    ctColumns.forEach(function(col) {
      columns.push({
        name: col.name, icon: col.icon,
        expectedCount: col.count,
        color: CT_COLOR_MAP[col.color] || "#71717a",
        nodes: []
      });
    });
  } else {
    /* Fallback: auto-detect columns */
    var autoGroups = {};
    nodes.forEach(function(n) {
      var ct = detectContentType(n);
      if (!autoGroups[ct]) autoGroups[ct] = { name: ct, nodes: [], color: "#71717a" };
      autoGroups[ct].nodes.push(n);
    });
    var sorted = Object.keys(autoGroups).sort(function(a, b) {
      return autoGroups[b].nodes.length - autoGroups[a].nodes.length;
    });
    sorted.forEach(function(k) { columns.push(autoGroups[k]); });
  }

  /* Assign nodes to columns */
  nodes.forEach(function(n) {
    var ct = detectContentType(n);
    var placed = false;
    for (var i = 0; i < columns.length; i++) {
      if (columns[i].name === ct) { columns[i].nodes.push(n); placed = true; break; }
    }
    if (!placed) {
      /* Find or create Other column */
      var otherCol = null;
      for (var j = 0; j < columns.length; j++) {
        if (columns[j].name === "Other") { otherCol = columns[j]; break; }
      }
      if (!otherCol) {
        otherCol = { name: "Other", icon: "\uD83D\uDCE6", color: "#71717a", nodes: [] };
        columns.push(otherCol);
      }
      otherCol.nodes.push(n);
    }
  });

  /* Sort nodes in each column by importance */
  columns.forEach(function(col) {
    col.nodes.sort(function(a, b) { return (b.importance || 0) - (a.importance || 0); });
  });

  /* Remove empty columns */
  columns = columns.filter(function(col) { return col.nodes.length > 0; });

  /* Canvas setup — fill full container height */
  var canvas = document.createElement("canvas");
  var w = container.clientWidth || 1200;
  var h = container.clientHeight || 700;
  if (h < 400) h = 700;
  var dpr = window.devicePixelRatio || 1;
  canvas.width = w * dpr;
  canvas.height = h * dpr;
  canvas.style.width = w + "px";
  canvas.style.height = h + "px";
  canvas.style.display = "block";
  container.innerHTML = "";
  container.appendChild(canvas);
  var ctx = canvas.getContext("2d");
  ctx.scale(dpr, dpr);

  /* Layout: columns across the width */
  var marginX = 80, marginTop = 85, marginBottom = 30;
  var colSpacing = columns.length > 1 ? (w - 2 * marginX) / (columns.length - 1) : 0;
  var usableH = h - marginTop - marginBottom;
  var maxNodesPerCol = Math.max(30, Math.floor(usableH / 18));

  var nodePositions = {};
  columns.forEach(function(col, ci) {
    var colX = columns.length > 1 ? marginX + ci * colSpacing : w / 2;
    var showCount = Math.min(col.nodes.length, maxNodesPerCol);
    var ySpacing = Math.min(usableH / Math.max(showCount, 1), 28);
    var startY = marginTop + (usableH - showCount * ySpacing) / 2;

    for (var ni = 0; ni < showCount; ni++) {
      var n = col.nodes[ni];
      var jitter = Math.sin(ni * 7 + ci * 3) * 10;
      var imp = n.importance || 0;
      nodePositions[n.id] = {
        x: colX + jitter,
        y: startY + ni * ySpacing,
        node: n,
        colName: col.name,
        color: col.color,
        r: 2.5 + imp * 8
      };
    }
  });

  /* Draw cosmic background */
  var isDark = document.documentElement.getAttribute("data-theme") !== "light";
  var bgFrom = isDark ? "#0e0e1a" : "#f5f5f5";
  var bgTo = isDark ? "#06060f" : "#e8e8e8";
  var labelBg = isDark ? "#06060f" : "#e0e0e0";
  var labelAlpha = isDark ? 0.7 : 0.5;
  var edgeBaseAlpha = isDark ? 0.06 : 0.1;
  var fontClr = isDark ? "#e4e4e7" : "#27272a";

  var bgGrad = ctx.createRadialGradient(w/2, h/2, 0, w/2, h/2, w * 0.6);
  bgGrad.addColorStop(0, bgFrom);
  bgGrad.addColorStop(1, bgTo);
  ctx.fillStyle = bgGrad;
  ctx.fillRect(0, 0, w, h);

  /* Star-field background for cosmic feel */
  if (isDark) {
    for (var si = 0; si < 120; si++) {
      var sx = (Math.sin(si * 127.1 + 0.5) * 0.5 + 0.5) * w;
      var sy = (Math.cos(si * 83.3 + 0.7) * 0.5 + 0.5) * h;
      var sr = 0.3 + (si % 5) * 0.15;
      ctx.beginPath();
      ctx.arc(sx, sy, sr, 0, 2 * Math.PI);
      ctx.fillStyle = "#ffffff";
      ctx.globalAlpha = 0.08 + (si % 3) * 0.04;
      ctx.fill();
    }
    ctx.globalAlpha = 1;
  }

  /* Draw edges as bezier curves with glow */
  var posIdSet = {};
  Object.keys(nodePositions).forEach(function(id) { posIdSet[id] = true; });

  var edgeCount = 0;
  edges.forEach(function(e) {
    var pa = nodePositions[e.from];
    var pb = nodePositions[e.to];
    if (!pa || !pb) return;
    edgeCount++;
    var cpx1 = pa.x + (pb.x - pa.x) * 0.4;
    var cpx2 = pa.x + (pb.x - pa.x) * 0.6;
    var imp = Math.max(pa.node.importance || 0, pb.node.importance || 0);

    /* Outer glow pass for important edges */
    if (imp > 0.2) {
      ctx.beginPath();
      ctx.moveTo(pa.x, pa.y);
      ctx.bezierCurveTo(cpx1, pa.y, cpx2, pb.y, pb.x, pb.y);
      ctx.strokeStyle = pa.color;
      ctx.globalAlpha = (edgeBaseAlpha * 0.4) + imp * 0.08;
      ctx.lineWidth = 2.5 + imp * 3;
      ctx.stroke();
    }

    /* Core edge */
    ctx.beginPath();
    ctx.moveTo(pa.x, pa.y);
    ctx.bezierCurveTo(cpx1, pa.y, cpx2, pb.y, pb.x, pb.y);
    ctx.strokeStyle = pa.color;
    ctx.globalAlpha = edgeBaseAlpha + imp * 0.25;
    ctx.lineWidth = 0.3 + imp * 0.8;
    ctx.stroke();
  });
  ctx.globalAlpha = 1;

  /* Draw column labels */
  var fontSans = "sans-serif";
  try { fontSans = getComputedStyle(document.documentElement).getPropertyValue("--font-sans") || "sans-serif"; } catch(e) {}

  columns.forEach(function(col, ci) {
    var colX = columns.length > 1 ? marginX + ci * colSpacing : w / 2;
    var icon = col.icon || "";
    var label = icon + " " + col.name + " \u00b7 " + col.nodes.length;

    ctx.font = "bold 10px " + fontSans;
    var tw = ctx.measureText(label).width;
    ctx.fillStyle = labelBg;
    ctx.globalAlpha = labelAlpha;
    var rx = colX - tw/2 - 10, ry = 42, rw = tw + 20, rh = 22, rr = 5;
    ctx.beginPath();
    ctx.moveTo(rx + rr, ry); ctx.lineTo(rx + rw - rr, ry);
    ctx.quadraticCurveTo(rx + rw, ry, rx + rw, ry + rr);
    ctx.lineTo(rx + rw, ry + rh - rr);
    ctx.quadraticCurveTo(rx + rw, ry + rh, rx + rw - rr, ry + rh);
    ctx.lineTo(rx + rr, ry + rh);
    ctx.quadraticCurveTo(rx, ry + rh, rx, ry + rh - rr);
    ctx.lineTo(rx, ry + rr);
    ctx.quadraticCurveTo(rx, ry, rx + rr, ry);
    ctx.fill();
    ctx.globalAlpha = 0.4;
    ctx.strokeStyle = col.color;
    ctx.lineWidth = 1;
    ctx.stroke();
    ctx.globalAlpha = 1;

    ctx.fillStyle = col.color;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(label, colX, 53);
  });

  /* Draw nodes with multi-layer glow */
  var clickTargets = [];
  Object.keys(nodePositions).forEach(function(id) {
    var p = nodePositions[id];
    var imp = p.node.importance || 0;

    /* Outer ambient glow */
    if (imp > 0.15) {
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r * 4, 0, 2 * Math.PI);
      ctx.fillStyle = p.color;
      ctx.globalAlpha = 0.03 + imp * 0.05;
      ctx.fill();
    }

    /* Inner glow halo */
    if (imp > 0.05) {
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r * 2.2, 0, 2 * Math.PI);
      ctx.fillStyle = p.color;
      ctx.globalAlpha = 0.08 + imp * 0.12;
      ctx.fill();
    }

    /* Core node */
    ctx.beginPath();
    ctx.arc(p.x, p.y, p.r, 0, 2 * Math.PI);
    ctx.fillStyle = p.color;
    ctx.globalAlpha = 0.5 + imp * 0.5;
    ctx.fill();

    /* Bright center dot for high-importance nodes */
    if (imp > 0.4) {
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r * 0.4, 0, 2 * Math.PI);
      ctx.fillStyle = "#ffffff";
      ctx.globalAlpha = 0.3 + imp * 0.3;
      ctx.fill();
    }
    ctx.globalAlpha = 1;

    clickTargets.push({ id: id, x: p.x, y: p.y, r: p.r, type: p.colName, title: p.node.title, cat: (p.node.type || "uncategorized").toLowerCase() });
  });

  /* Edge count label in corner */
  ctx.font = "11px " + fontSans;
  ctx.fillStyle = fontClr;
  ctx.globalAlpha = 0.4;
  ctx.textAlign = "right";
  ctx.textBaseline = "bottom";
  ctx.fillText(edgeCount + " edges rendered", w - 16, h - 10);
  ctx.globalAlpha = 1;

  /* Click to navigate */
  canvas.addEventListener("click", function(evt) {
    var rect = canvas.getBoundingClientRect();
    var mx = (evt.clientX - rect.left) * (canvas.width / rect.width) / dpr;
    var my = (evt.clientY - rect.top) * (canvas.height / rect.height) / dpr;
    for (var i = 0; i < clickTargets.length; i++) {
      var ct = clickTargets[i];
      var dx = mx - ct.x, dy = my - ct.y;
      if (dx*dx + dy*dy <= (ct.r + 6) * (ct.r + 6)) {
        var slug = ct.id.split("/").pop();
        var cat = ct.cat;
        window.location.href = "/categories/" + cat + "/" + slug + ".html";
        break;
      }
    }
  });

  /* Hover tooltip */
  var tooltip = document.createElement("div");
  tooltip.style.cssText = "position:absolute;padding:6px 10px;background:var(--surface-1);border:1px solid var(--hairline);border-radius:6px;font-size:12px;color:var(--ink);pointer-events:none;display:none;z-index:10;white-space:nowrap;box-shadow:0 4px 12px rgba(0,0,0,0.3);";
  container.style.position = "relative";
  container.appendChild(tooltip);

  canvas.addEventListener("mousemove", function(evt) {
    var rect = canvas.getBoundingClientRect();
    var mx = (evt.clientX - rect.left) * (canvas.width / rect.width) / dpr;
    var my = (evt.clientY - rect.top) * (canvas.height / rect.height) / dpr;
    var found = false;
    for (var i = 0; i < clickTargets.length; i++) {
      var ct = clickTargets[i];
      var dx = mx - ct.x, dy = my - ct.y;
      if (dx*dx + dy*dy <= (ct.r + 6) * (ct.r + 6)) {
        tooltip.textContent = (ct.title || ct.id) + " \u2014 " + ct.type;
        tooltip.style.display = "block";
        tooltip.style.left = (evt.clientX - rect.left + 14) + "px";
        tooltip.style.top = (evt.clientY - rect.top - 10) + "px";
        canvas.style.cursor = "pointer";
        found = true;
        break;
      }
    }
    if (!found) {
      tooltip.style.display = "none";
      canvas.style.cursor = "default";
    }
  });

  /* Subtle pulse animation using an overlay canvas for breathing glow */
  var highImpNodes = Object.keys(nodePositions).filter(function(id) {
    return (nodePositions[id].node.importance || 0) > 0.3;
  });
  if (highImpNodes.length > 0 && isDark) {
    var overlay = document.createElement("canvas");
    overlay.width = canvas.width;
    overlay.height = canvas.height;
    overlay.style.cssText = "position:absolute;top:0;left:0;width:" + w + "px;height:" + h + "px;pointer-events:none;";
    container.appendChild(overlay);
    var octx = overlay.getContext("2d");
    octx.scale(dpr, dpr);
    var pulsePhase = 0;
    (function animatePulse() {
      pulsePhase += 0.02;
      var breath = 0.5 + 0.5 * Math.sin(pulsePhase);
      octx.clearRect(0, 0, w, h);
      highImpNodes.forEach(function(id) {
        var p = nodePositions[id];
        var imp = p.node.importance || 0;
        octx.beginPath();
        octx.arc(p.x, p.y, p.r * 3.5 + breath * 4, 0, 2 * Math.PI);
        octx.fillStyle = p.color;
        octx.globalAlpha = 0.03 + breath * 0.04 * imp;
        octx.fill();
        octx.globalAlpha = 1;
      });
      requestAnimationFrame(animatePulse);
    })();
  }
}

/* ===== Event Delegation ===== */
function initEventDelegation() {
  document.addEventListener("click", function(e) {
    if (e.target.closest("#theme-toggle")) { toggleMode(); return; }
    var themeSelect = e.target.closest("#theme-select");
    if (themeSelect) return; /* handled by onchange */

    if (e.target.closest(".topbar__search") || e.target.closest(".sidebar-search")) {
      openPalette(); return;
    }
    if (e.target.closest(".sidebar-toggle")) { toggleSidebar(); return; }
    if (e.target.closest(".graph-toggle")) { toggleGraph(); return; }

    /* Palette overlay dismiss */
    if (e.target.closest("#command-palette") && (e.target.id === "command-palette" || e.target.classList.contains("palette-overlay"))) {
      closePalette(); return;
    }
    /* Palette result click */
    var resultEl = e.target.closest(".palette__result");
    if (resultEl && resultEl.dataset.url) {
      window.location.href = resultEl.dataset.url; return;
    }
  });

  /* Theme select dropdown */
  var sel = document.getElementById("theme-select");
  if (sel) {
    sel.addEventListener("change", function() {
      setColorTheme(sel.value);
    });
  }
}

/* ===== Palette Input Handler ===== */
function initPaletteInput() {
  var el = getPalette();
  if (!el || !paletteInput) return;

  paletteInput.addEventListener("input", function() {
    currentEntries = filterEntries(paletteInput.value);
    selectedIdx = currentEntries.length > 0 ? 0 : -1;
    renderResults(currentEntries);
  });

  paletteInput.addEventListener("keydown", function(e) {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      if (selectedIdx < currentEntries.length - 1) selectedIdx++;
      renderResults(currentEntries);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      if (selectedIdx > 0) selectedIdx--;
      renderResults(currentEntries);
    } else if (e.key === "Enter") {
      e.preventDefault();
      navigateResult();
    } else if (e.key === "Escape") {
      e.preventDefault();
      closePalette();
    }
  });
}

/* ===== Init ===== */
document.addEventListener("DOMContentLoaded", function() {
  initHighlight();
  initCopyButtons();
  initFilterBar();
  initTableSorting();
  initSidebarTree();
  initBottomTabs();
  initEventDelegation();
  initPaletteInput();
  initMiniGraph();
  initGraphToggle();
});

document.addEventListener("keydown", handleGlobalKeys);

/* Make theme functions global for inline handlers */
window.setColorTheme = setColorTheme;
window.toggleMode = toggleMode;

// ==========================================================================
// MINI GRAPH (Local page neighborhood — 2-hop canvas render)
// ==========================================================================

function initMiniGraph() {
  var container = document.getElementById("mini-graph");
  if (!container) return;
  var pageId = container.getAttribute("data-page");
  if (!pageId) return;

  fetch("/cross-references.json")
    .then(function(r) { return r.json(); })
    .then(function(graph) { renderMiniGraph(container, graph, pageId); })
    .catch(function() { container.innerHTML = '<p style="padding:8px;font-size:12px;color:var(--ink-subtle);">Graph unavailable</p>'; });
}

function renderMiniGraph(container, graph, pageId) {
  var nodes = graph.nodes || [];
  var edges = graph.edges || [];

  var currentNode = nodes.find(function(n) { return n.id === pageId; });
  if (!currentNode) {
    container.innerHTML = '<p style="padding:8px;font-size:12px;color:var(--ink-subtle);">No graph data</p>';
    return;
  }

  var neighborIds = new Set();
  neighborIds.add(pageId);
  edges.forEach(function(e) {
    if (e.from === pageId) neighborIds.add(e.to);
    if (e.to === pageId) neighborIds.add(e.from);
  });
  var hop1 = new Set(neighborIds);
  edges.forEach(function(e) {
    if (hop1.has(e.from)) neighborIds.add(e.to);
    if (hop1.has(e.to)) neighborIds.add(e.from);
  });

  var neighborArr = Array.from(neighborIds).slice(0, 40);
  var neighborSet = new Set(neighborArr);
  var localNodes = nodes.filter(function(n) { return neighborSet.has(n.id); });
  var localEdges = edges.filter(function(e) { return neighborSet.has(e.from) && neighborSet.has(e.to); });

  if (localNodes.length < 2) {
    container.innerHTML = '<p style="padding:12px;font-size:12px;text-align:center;color:var(--ink-subtle);">'
      + 'No cross-references detected for this page yet.</p>';
    return;
  }

  var canvas = document.createElement("canvas");
  var w = container.clientWidth || 260;
  var h = 240;
  canvas.width = w * 2; canvas.height = h * 2;
  canvas.style.width = w + "px"; canvas.style.height = h + "px";
  container.appendChild(canvas);
  var ctx = canvas.getContext("2d");
  ctx.scale(2, 2);

  var TYPE_COLORS = {
    "rule": "#f59e0b", "workflow": "#6366f1", "beanshell": "#ec4899",
    "connector-guides": "#14b8a6", "iiq-docs": "#f59e0b", "config": "#8b5cf6",
    "docs": "#10b981", "tokens": "#f97316", "java": "#f59e0b", "xml": "#6366f1"
  };

  var positions = {};
  localNodes.forEach(function(n, i) {
    var angle = (2 * Math.PI * i) / localNodes.length;
    positions[n.id] = {
      x: w/2 + (w/3) * Math.cos(angle) + (Math.random() - 0.5) * 20,
      y: h/2 + (h/3) * Math.sin(angle) + (Math.random() - 0.5) * 20,
      node: n
    };
  });

  for (var iter = 0; iter < 30; iter++) {
    localNodes.forEach(function(a) {
      localNodes.forEach(function(b) {
        if (a.id === b.id) return;
        var pa = positions[a.id], pb = positions[b.id];
        var dx = pa.x - pb.x, dy = pa.y - pb.y;
        var dist = Math.sqrt(dx*dx + dy*dy) || 1;
        var force = 800 / (dist * dist);
        pa.x += (dx / dist) * force;
        pa.y += (dy / dist) * force;
      });
    });
    localEdges.forEach(function(e) {
      var pa = positions[e.from], pb = positions[e.to];
      if (!pa || !pb) return;
      var dx = pb.x - pa.x, dy = pb.y - pa.y;
      var dist = Math.sqrt(dx*dx + dy*dy) || 1;
      var force = (dist - 60) * 0.01;
      pa.x += (dx / dist) * force;
      pb.x -= (dx / dist) * force;
      pa.y += (dy / dist) * force;
      pb.y -= (dy / dist) * force;
    });
    localNodes.forEach(function(n) {
      var p = positions[n.id];
      p.x += (w/2 - p.x) * 0.01;
      p.y += (h/2 - p.y) * 0.01;
      p.x = Math.max(20, Math.min(w - 20, p.x));
      p.y = Math.max(20, Math.min(h - 20, p.y));
    });
  }

  ctx.strokeStyle = "#3f3f46";
  ctx.lineWidth = 0.5;
  localEdges.forEach(function(e) {
    var pa = positions[e.from], pb = positions[e.to];
    if (!pa || !pb) return;
    ctx.beginPath();
    ctx.moveTo(pa.x, pa.y);
    ctx.lineTo(pb.x, pb.y);
    ctx.stroke();
  });

  var nodePositions = [];
  localNodes.forEach(function(n) {
    var p = positions[n.id];
    var isCurrent = n.id === pageId;
    var baseColor = "#71717a";
    var cat = (n.type || "").split("/")[0].toLowerCase();
    if (TYPE_COLORS[cat]) baseColor = TYPE_COLORS[cat];
    if (isCurrent) baseColor = "#10b981";
    var radius = isCurrent ? 7 : 4 + (n.importance || 0) * 4;
    ctx.beginPath();
    ctx.arc(p.x, p.y, radius, 0, 2 * Math.PI);
    ctx.fillStyle = baseColor;
    ctx.fill();
    if (isCurrent) {
      ctx.strokeStyle = "#34d399";
      ctx.lineWidth = 2;
      ctx.stroke();
    }
    nodePositions.push({ id: n.id, x: p.x, y: p.y, r: radius, type: n.type, title: n.title });
  });

  canvas.addEventListener("click", function(evt) {
    var rect = canvas.getBoundingClientRect();
    var mx = (evt.clientX - rect.left) * 2 / 2;
    var my = (evt.clientY - rect.top) * 2 / 2;
    for (var i = 0; i < nodePositions.length; i++) {
      var np = nodePositions[i];
      var dx = mx - np.x, dy = my - np.y;
      if (dx*dx + dy*dy <= (np.r + 4) * (np.r + 4)) {
        var cat = (np.type || "uncategorized").toLowerCase();
        var slug = np.id.split("/").pop();
        window.location.href = "/categories/" + cat + "/" + slug + ".html";
        break;
      }
    }
  });

  var countEl = document.createElement("div");
  countEl.style.cssText = "font-size:11px;color:var(--ink-subtle);padding:4px 8px;";
  countEl.textContent = localNodes.length + " nodes \u00b7 " + localEdges.length + " edges";
  container.appendChild(countEl);
}

})();
"""
