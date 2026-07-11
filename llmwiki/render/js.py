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
  fetch("/search-index.json")
    .then(function(r) { return r.ok ? r.json() : Promise.reject(); })
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
  var bar = input.closest(".filter-bar");

  /* Find the content area to inject results into (cards grid or table) */
  var mainEl = bar ? bar.parentElement : null;
  var cardsGrid = mainEl ? mainEl.querySelector(".cards-grid") : null;
  var isCardsPage = !!cardsGrid;

  /* Create inline results container (for cards pages like /categories/) */
  var inlineResults = null;
  if (isCardsPage && mainEl) {
    inlineResults = document.createElement("div");
    inlineResults.className = "search-results-inline";
    inlineResults.style.display = "none";
    /* Insert after the filter bar */
    bar.parentNode.insertBefore(inlineResults, bar.nextSibling);
  }

  function updateResults(query) {
    /* Filter table rows (for category detail pages with tables) */
    var rows = document.querySelectorAll("table tbody tr");
    var tableVisible = 0;
    for (var i = 0; i < rows.length; i++) {
      var row = rows[i];
      var text = row.textContent.toLowerCase();
      var tags = (row.getAttribute("data-tags") || "").toLowerCase();
      var show = !query || text.indexOf(query) !== -1 || tags.indexOf(query) !== -1;
      row.classList.toggle("hidden", !show);
      if (show) tableVisible++;
    }

    /* Cards-page behavior: show inline search results, hide cards grid */
    if (isCardsPage && inlineResults) {
      if (!query || query.length < 2) {
        /* No query — show cards, hide results */
        inlineResults.style.display = "none";
        /* Show all card sections */
        var sections = mainEl.querySelectorAll(".section");
        for (var s = 0; s < sections.length; s++) sections[s].style.display = "";
        if (countEl) countEl.textContent = "";
        return;
      }

      /* Have a query — hide card sections, show inline results */
      var sections = mainEl.querySelectorAll(".section");
      for (var s = 0; s < sections.length; s++) sections[s].style.display = "none";

      var results = filterEntries(query);
      if (countEl) countEl.textContent = results.length + " results";

      if (results.length === 0) {
        inlineResults.innerHTML = '<div class="search-results-inline__empty">No pages matching \u201c' + query.replace(/</g,"&lt;") + '\u201d</div>';
        inlineResults.style.display = "block";
        return;
      }

      var html = '<div class="search-results-inline__header">'
        + '<span class="search-results-inline__label">All pages matching \u201c' + query.replace(/</g,"&lt;") + '\u201d</span>'
        + '<span class="search-results-inline__count">' + results.length + ' results</span>'
        + '</div>';
      html += '<div class="table-wrap"><table><thead><tr>'
        + '<th>Name</th><th>Type</th><th>Tags</th><th>Refs</th><th>Importance</th>'
        + '</tr></thead><tbody>';
      results.forEach(function(entry) {
        var title = (entry.title || entry.id || "").replace(/</g, "&lt;");
        var cat = (entry.category || "").replace(/</g, "&lt;");
        var url = entry.url || "#";
        var imp = entry.importance || 0;
        var impPct = Math.round(imp * 100);
        var badgeBase = cat.split("/")[0].toLowerCase();
        var badgeMap = {rule:"beanshell",workflow:"xml",application:"config",task:"java",
          beanshell:"beanshell",config:"config",docs:"docs","connector-guides":"docs",
          "iiq-docs":"docs",java:"java",xml:"xml",tokens:"tokens"};
        var badgeCls = badgeMap[badgeBase] || "config";
        var badgeLabels = {java:"Java",xml:"XML",beanshell:"BSH",config:"Config",docs:"Docs",tokens:"Token"};
        var badgeLabel = badgeLabels[badgeCls] || badgeCls.toUpperCase();
        var tags = (entry.tags || []).filter(function(t) { return !t.startsWith("method:"); }).slice(0, 3).map(function(t) {
          return '<span class="tag">' + t.replace(/</g, "&lt;") + '</span>';
        }).join(" ");
        html += '<tr>'
          + '<td class="td-accent"><a href="' + url + '">' + title + '</a></td>'
          + '<td><span class="badge badge--' + badgeCls + '">' + badgeLabel + '</span></td>'
          + '<td>' + tags + '</td>'
          + '<td class="td-mono">' + (entry.importance ? Math.round((entry.importance || 0) * 1000) : 0) + '</td>'
          + '<td><div class="connected__bar" style="width:60px"><div class="connected__bar-fill" style="width:' + impPct + '%"></div></div></td>'
          + '</tr>';
      });
      html += '</tbody></table></div>';
      inlineResults.innerHTML = html;
      inlineResults.style.display = "block";
      return;
    }

    /* Non-cards pages: filter cards too */
    var cards = document.querySelectorAll(".cards-grid .card");
    for (var j = 0; j < cards.length; j++) {
      var card = cards[j];
      var cText = card.textContent.toLowerCase();
      var cTags = (card.getAttribute("data-tags") || "").toLowerCase();
      var cShow = !query || cText.indexOf(query) !== -1 || cTags.indexOf(query) !== -1;
      card.style.display = cShow ? "" : "none";
      if (cShow) tableVisible++;
    }
    if (countEl) countEl.textContent = tableVisible + " items";
  }

  input.addEventListener("input", function() {
    updateResults(input.value.toLowerCase().trim());
  });
  input.addEventListener("keydown", function(e) {
    if (e.key === "Escape") { input.value = ""; updateResults(""); input.blur(); }
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
        if (typeof initNeuralVis === "function") {
          initNeuralVis();
        } else if (typeof initNeuralGraph === "function") {
          initNeuralGraph(neuralEl);
        }
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

  /* ── Content type detection ── */
  function detectContentType(n) {
    var cat = (n.type || "").toLowerCase();
    if (cat.indexOf("beanshell") === 0) return "Inline Scripts";
    if (cat === "tokens") return "Token Registry";
    if (cat.indexOf("connector-guides") === 0 || cat.indexOf("iiq-docs") === 0 || cat === "docs") return "Documentation";
    if (cat.indexOf("com/") === 0 || cat.indexOf("sailpoint/") === 0 || cat.indexOf("bsh/") === 0) return "Source Code";
    if (cat === "config" || cat.indexOf("xml") === 0) return "Configuration";
    return "XML / Markup";
  }

  var COL_COLORS = {
    "Source Code": "#10b981", "XML / Markup": "#f97316", "Inline Scripts": "#ec4899",
    "Configuration": "#8b5cf6", "Documentation": "#06b6d4", "Token Registry": "#eab308", "Other": "#6366f1"
  };

  /* Build columns */
  var ctColumns = window.LLMWIKI_CT_COLUMNS;
  var columns = [];
  if (ctColumns && ctColumns.length > 0) {
    ctColumns.forEach(function(col) {
      columns.push({ name: col.name, icon: col.icon, color: COL_COLORS[col.name] || "#71717a", nodes: [] });
    });
  }
  nodes.forEach(function(n) {
    var ct = detectContentType(n);
    var placed = false;
    for (var i = 0; i < columns.length; i++) {
      if (columns[i].name === ct) { columns[i].nodes.push(n); placed = true; break; }
    }
    if (!placed) {
      for (var j = 0; j < columns.length; j++) {
        if (columns[j].name === "Other") { columns[j].nodes.push(n); placed = true; break; }
      }
      if (!placed) { columns.push({ name: "Other", icon: "", color: "#71717a", nodes: [n] }); }
    }
  });
  columns.forEach(function(col) { col.nodes.sort(function(a, b) { return (b.importance || 0) - (a.importance || 0); }); });
  columns = columns.filter(function(c) { return c.nodes.length > 0; });

  /* ── Canvas setup ── */
  var isDark = document.documentElement.getAttribute("data-theme") !== "light";
  var dpr = window.devicePixelRatio || 1;
  var viewW = container.clientWidth || 1200;
  var viewH = container.clientHeight || 700;
  if (viewH < 400) viewH = 700;
  var colSpacing = 220;
  var totalW = Math.max(viewW, columns.length * colSpacing + 200);
  var h = viewH;
  var scrollX = 0;

  var canvas = document.createElement("canvas");
  canvas.width = viewW * dpr;
  canvas.height = h * dpr;
  canvas.style.width = viewW + "px";
  canvas.style.height = h + "px";
  canvas.style.display = "block";
  canvas.style.cursor = "grab";
  container.innerHTML = "";
  container.appendChild(canvas);
  var ctx = canvas.getContext("2d");

  /* ── Node layout: horizontal columns, each a vertical strip ── */
  var maxNodesPerCol = Math.min(Math.max(40, Math.floor((h - 100) / 10)), 120);
  var marginTop = 70;
  var marginBot = 30;
  var usableH = h - marginTop - marginBot;
  var startX = 100;

  var nodePositions = {};
  columns.forEach(function(col, ci) {
    var colX = startX + ci * colSpacing;
    var showCount = Math.min(col.nodes.length, maxNodesPerCol);
    var ySpacing = Math.min(usableH / Math.max(showCount, 1), 14);
    var startY = marginTop + (usableH - showCount * ySpacing) / 2;
    for (var ni = 0; ni < showCount; ni++) {
      var n = col.nodes[ni];
      nodePositions[n.id] = {
        x: colX, y: startY + ni * ySpacing,
        node: n, colIdx: ci, color: col.color,
        r: 2 + (n.importance || 0) * 4
      };
    }
  });

  /* Build adjacency for click-to-isolate */
  var adjacency = {};
  edges.forEach(function(e) {
    if (!adjacency[e.from]) adjacency[e.from] = [];
    if (!adjacency[e.to]) adjacency[e.to] = [];
    adjacency[e.from].push(e.to);
    adjacency[e.to].push(e.from);
  });

  /* ── State ── */
  var selectedNodeId = null;
  var highlightedIds = null;

  /* Tooltip element */
  var tooltip = document.createElement("div");
  tooltip.style.cssText = "position:absolute;padding:6px 10px;background:var(--surface-1);border:1px solid var(--hairline);border-radius:6px;font-size:12px;color:var(--ink);pointer-events:none;display:none;z-index:10;white-space:nowrap;box-shadow:0 4px 12px rgba(0,0,0,0.3);";
  container.style.position = "relative";
  container.appendChild(tooltip);

  /* ── Render function (called on scroll, click) ── */
  function render() {
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, viewW, h);

    /* Background */
    var bgGrad = ctx.createRadialGradient(viewW / 2, h * 0.35, 0, viewW / 2, h * 0.35, viewW * 0.8);
    if (isDark) { bgGrad.addColorStop(0, "#0d0d1f"); bgGrad.addColorStop(0.6, "#080814"); bgGrad.addColorStop(1, "#04040c"); }
    else { bgGrad.addColorStop(0, "#f0f0f8"); bgGrad.addColorStop(1, "#e0e0ea"); }
    ctx.fillStyle = bgGrad;
    ctx.fillRect(0, 0, viewW, h);

    /* Star field */
    if (isDark) {
      for (var si = 0; si < 150; si++) {
        var sx = ((Math.sin(si * 127.1 + 0.5) * 0.5 + 0.5) * viewW * 1.5 + scrollX * 0.02) % viewW;
        var sy = (Math.cos(si * 83.3 + 0.7) * 0.5 + 0.5) * h;
        ctx.beginPath(); ctx.arc(sx, sy, 0.3 + (si % 3) * 0.15, 0, 2 * Math.PI);
        ctx.fillStyle = "#ffffff"; ctx.globalAlpha = 0.06 + (si % 4) * 0.02;
        ctx.fill();
      }
      ctx.globalAlpha = 1;
    }

    ctx.save();
    ctx.translate(-scrollX, 0);

    /* ── Column backdrops ── */
    columns.forEach(function(col, ci) {
      var colX = startX + ci * colSpacing;
      /* Halo circle */
      var haR = usableH * 0.45;
      var haY = marginTop + usableH / 2;
      ctx.beginPath(); ctx.arc(colX, haY, haR, 0, 2 * Math.PI);
      ctx.strokeStyle = col.color; ctx.globalAlpha = isDark ? 0.06 : 0.08;
      ctx.lineWidth = 1; ctx.stroke(); ctx.globalAlpha = 1;
      /* Dotted center line */
      ctx.beginPath(); ctx.setLineDash([3, 5]);
      ctx.moveTo(colX, marginTop - 5); ctx.lineTo(colX, marginTop + usableH + 5);
      ctx.strokeStyle = col.color; ctx.globalAlpha = 0.2;
      ctx.lineWidth = 1; ctx.stroke();
      ctx.setLineDash([]); ctx.globalAlpha = 1;
    });

    /* ── Draw edges: dual-chromatic green + red ── */
    var edgeCount = 0;
    edges.forEach(function(e) {
      var pa = nodePositions[e.from];
      var pb = nodePositions[e.to];
      if (!pa || !pb) return;
      var minEX = Math.min(pa.x, pb.x); var maxEX = Math.max(pa.x, pb.x);
      if (maxEX < scrollX - 50 || minEX > scrollX + viewW + 50) return;
      edgeCount++;
      var imp = Math.max(pa.node.importance || 0, pb.node.importance || 0);
      var dimmed = highlightedIds && !highlightedIds[e.from] && !highlightedIds[e.to];
      var highlighted = highlightedIds && (highlightedIds[e.from] || highlightedIds[e.to]);
      var cpx1 = pa.x + (pb.x - pa.x) * 0.35;
      var cpx2 = pa.x + (pb.x - pa.x) * 0.65;

      if (dimmed) {
        ctx.beginPath(); ctx.moveTo(pa.x, pa.y);
        ctx.bezierCurveTo(cpx1, pa.y, cpx2, pb.y, pb.x, pb.y);
        ctx.strokeStyle = isDark ? "#333" : "#ccc";
        ctx.globalAlpha = 0.03; ctx.lineWidth = 0.3; ctx.stroke(); ctx.globalAlpha = 1;
        return;
      }

      /* Green pass */
      ctx.beginPath(); ctx.moveTo(pa.x, pa.y);
      ctx.bezierCurveTo(cpx1, pa.y, cpx2, pb.y, pb.x, pb.y);
      ctx.strokeStyle = "#10b981";
      ctx.globalAlpha = highlighted ? (0.3 + imp * 0.5) : (0.08 + imp * 0.2);
      ctx.lineWidth = highlighted ? (1 + imp * 2) : (0.3 + imp * 1.2);
      ctx.stroke();

      /* Red/coral pass — slight offset for chromatic split */
      ctx.beginPath(); ctx.moveTo(pa.x + 0.5, pa.y + 0.5);
      ctx.bezierCurveTo(cpx1 + 0.5, pa.y - 0.5, cpx2 - 0.5, pb.y + 0.5, pb.x - 0.5, pb.y - 0.5);
      ctx.strokeStyle = "#f87171";
      ctx.globalAlpha = highlighted ? (0.2 + imp * 0.4) : (0.05 + imp * 0.12);
      ctx.lineWidth = highlighted ? (0.8 + imp * 1.5) : (0.2 + imp * 0.7);
      ctx.stroke();

      /* White glow for important/highlighted */
      if (imp > 0.15 || highlighted) {
        ctx.beginPath(); ctx.moveTo(pa.x, pa.y);
        ctx.bezierCurveTo(cpx1, pa.y, cpx2, pb.y, pb.x, pb.y);
        ctx.strokeStyle = "#ffffff";
        ctx.globalAlpha = highlighted ? (0.06 + imp * 0.15) : (0.01 + imp * 0.04);
        ctx.lineWidth = highlighted ? (2 + imp * 3) : (1 + imp * 2);
        ctx.stroke();
      }
      ctx.globalAlpha = 1;
    });

    /* ── Draw nodes ── */
    var clickTargets = [];
    Object.keys(nodePositions).forEach(function(id) {
      var p = nodePositions[id];
      var imp = p.node.importance || 0;
      var isSelected = (id === selectedNodeId);
      var isHigh = highlightedIds && highlightedIds[id];
      var dimmed = highlightedIds && !highlightedIds[id];
      if (p.x < scrollX - 20 || p.x > scrollX + viewW + 20) return;

      if (dimmed) {
        ctx.beginPath(); ctx.arc(p.x, p.y, p.r * 0.7, 0, 2 * Math.PI);
        ctx.fillStyle = isDark ? "#333" : "#ccc";
        ctx.globalAlpha = 0.15; ctx.fill(); ctx.globalAlpha = 1;
        clickTargets.push({ id: id, x: p.x, y: p.y, r: p.r });
        return;
      }

      /* Outer glow */
      if (imp > 0.05 || isHigh) {
        ctx.beginPath(); ctx.arc(p.x, p.y, p.r * (isHigh ? 5 : 3), 0, 2 * Math.PI);
        ctx.fillStyle = p.color; ctx.globalAlpha = isHigh ? 0.15 : (0.04 + imp * 0.08); ctx.fill();
      }
      /* Inner glow */
      ctx.beginPath(); ctx.arc(p.x, p.y, p.r * 1.8, 0, 2 * Math.PI);
      ctx.fillStyle = p.color; ctx.globalAlpha = isHigh ? 0.25 : (0.08 + imp * 0.15); ctx.fill();
      /* Core */
      ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, 2 * Math.PI);
      ctx.fillStyle = isSelected ? "#ffffff" : p.color;
      ctx.globalAlpha = isHigh ? 1 : (0.5 + imp * 0.5); ctx.fill();
      /* White center */
      if (isSelected || imp > 0.4) {
        ctx.beginPath(); ctx.arc(p.x, p.y, p.r * 0.35, 0, 2 * Math.PI);
        ctx.fillStyle = "#ffffff"; ctx.globalAlpha = isSelected ? 0.9 : (0.3 + imp * 0.3); ctx.fill();
      }
      ctx.globalAlpha = 1;
      clickTargets.push({ id: id, x: p.x, y: p.y, r: p.r });
    });

    /* ── Layer headers at top ── */
    var fontSans = "sans-serif";
    try { fontSans = getComputedStyle(document.documentElement).getPropertyValue("--font-sans") || "sans-serif"; } catch(e) {}

    columns.forEach(function(col, ci) {
      var colX = startX + ci * colSpacing;
      if (colX < scrollX - 80 || colX > scrollX + viewW + 80) return;
      var hbW = 150; var hbH = 44; var hbX = colX - hbW / 2; var hbY = 6;
      ctx.fillStyle = isDark ? "rgba(10,10,20,0.85)" : "rgba(240,240,245,0.85)";
      ctx.strokeStyle = col.color; ctx.lineWidth = 1; ctx.globalAlpha = 1;
      ctx.beginPath();
      var rr = 4;
      ctx.moveTo(hbX + rr, hbY); ctx.lineTo(hbX + hbW - rr, hbY);
      ctx.quadraticCurveTo(hbX + hbW, hbY, hbX + hbW, hbY + rr);
      ctx.lineTo(hbX + hbW, hbY + hbH - rr);
      ctx.quadraticCurveTo(hbX + hbW, hbY + hbH, hbX + hbW - rr, hbY + hbH);
      ctx.lineTo(hbX + rr, hbY + hbH);
      ctx.quadraticCurveTo(hbX, hbY + hbH, hbX, hbY + hbH - rr);
      ctx.lineTo(hbX, hbY + rr);
      ctx.quadraticCurveTo(hbX, hbY, hbX + rr, hbY);
      ctx.fill(); ctx.globalAlpha = 0.6; ctx.stroke(); ctx.globalAlpha = 1;

      ctx.fillStyle = col.color; ctx.font = "bold 10px " + fontSans;
      ctx.textAlign = "center"; ctx.textBaseline = "middle";
      ctx.fillText((col.icon || "") + " " + col.name, colX, hbY + 13);
      ctx.fillStyle = isDark ? "#a1a1aa" : "#52525b"; ctx.font = "9px " + fontSans;
      ctx.fillText("Nodes: " + col.nodes.length, colX, hbY + 27);
      ctx.fillStyle = "#f87171"; ctx.font = "8px " + fontSans;
      ctx.fillText("Refs: " + col.nodes.reduce(function(s, n) { return s + (n.in_degree || 0); }, 0), colX, hbY + 38);
    });

    /* ── Node labels (top 6 per column) ── */
    columns.forEach(function(col, ci) {
      var colX = startX + ci * colSpacing;
      if (colX < scrollX - 80 || colX > scrollX + viewW + 80) return;
      var showLabels = Math.min(col.nodes.length, 6);
      for (var li = 0; li < showLabels; li++) {
        var nd = col.nodes[li];
        var p = nodePositions[nd.id];
        if (!p) continue;
        ctx.font = "8px " + fontSans;
        ctx.textAlign = "right"; ctx.textBaseline = "middle";
        ctx.fillStyle = col.color;
        ctx.globalAlpha = (highlightedIds && !highlightedIds[nd.id]) ? 0.1 : 0.6;
        ctx.fillText((nd.title || nd.id).substring(0, 18), colX - 14, p.y);
        ctx.fillText("\u203a", colX - 8, p.y);
        ctx.globalAlpha = 1;
      }
    });

    /* Stats */
    ctx.font = "11px " + fontSans;
    ctx.fillStyle = isDark ? "#e4e4e7" : "#27272a";
    ctx.globalAlpha = 0.4; ctx.textAlign = "left"; ctx.textBaseline = "bottom";
    ctx.fillText(edgeCount + " edges \u00b7 " + Object.keys(nodePositions).length + " nodes \u00b7 " + columns.length + " layers", 12, h - 10);
    if (selectedNodeId) {
      ctx.fillStyle = "#10b981"; ctx.globalAlpha = 0.7;
      var selT = (nodePositions[selectedNodeId] && nodePositions[selectedNodeId].node.title) || selectedNodeId;
      ctx.fillText("Showing: " + selT + " \u00b7 click elsewhere to reset", 12, h - 26);
    }
    ctx.globalAlpha = 1;
    ctx.restore();
    canvas._clickTargets = clickTargets;
  }

  render();

  /* ── Pan / scroll ── */
  var isPanning = false; var panStartX = 0; var panScrollStart = 0;
  var maxScroll = Math.max(0, totalW - viewW);

  canvas.addEventListener("mousedown", function(evt) {
    isPanning = true; panStartX = evt.clientX; panScrollStart = scrollX;
    canvas.style.cursor = "grabbing";
  });
  canvas.addEventListener("mousemove", function(evt) {
    if (isPanning) {
      scrollX = Math.max(0, Math.min(maxScroll, panScrollStart + (panStartX - evt.clientX)));
      render(); return;
    }
    var rect = canvas.getBoundingClientRect();
    var mx = (evt.clientX - rect.left) * (canvas.width / rect.width) / dpr + scrollX;
    var my = (evt.clientY - rect.top) * (canvas.height / rect.height) / dpr;
    var targets = canvas._clickTargets || [];
    var found = false;
    for (var i = 0; i < targets.length; i++) {
      var ct = targets[i]; var dx = mx - ct.x, dy = my - ct.y;
      if (dx * dx + dy * dy <= (ct.r + 6) * (ct.r + 6)) {
        var nd = nodePositions[ct.id];
        tooltip.textContent = (nd.node.title || ct.id) + " \u2014 " + columns[nd.colIdx].name;
        tooltip.style.display = "block";
        tooltip.style.left = (evt.clientX - rect.left + 14) + "px";
        tooltip.style.top = (evt.clientY - rect.top - 10) + "px";
        canvas.style.cursor = "pointer"; found = true; break;
      }
    }
    if (!found) { tooltip.style.display = "none"; if (!isPanning) canvas.style.cursor = "grab"; }
  });
  canvas.addEventListener("mouseup", function() { isPanning = false; canvas.style.cursor = "grab"; });
  canvas.addEventListener("mouseleave", function() { isPanning = false; canvas.style.cursor = "grab"; tooltip.style.display = "none"; });
  canvas.addEventListener("wheel", function(evt) {
    evt.preventDefault();
    scrollX = Math.max(0, Math.min(maxScroll, scrollX + evt.deltaY));
    render();
  }, { passive: false });

  /* ── Click-to-isolate (single click) / Navigate (double click) ── */
  canvas.addEventListener("click", function(evt) {
    if (Math.abs(evt.clientX - panStartX) > 5) return;
    var rect = canvas.getBoundingClientRect();
    var mx = (evt.clientX - rect.left) * (canvas.width / rect.width) / dpr + scrollX;
    var my = (evt.clientY - rect.top) * (canvas.height / rect.height) / dpr;
    var targets = canvas._clickTargets || [];
    var clickedId = null;
    for (var i = 0; i < targets.length; i++) {
      var ct = targets[i]; var dx = mx - ct.x, dy = my - ct.y;
      if (dx * dx + dy * dy <= (ct.r + 6) * (ct.r + 6)) { clickedId = ct.id; break; }
    }
    if (clickedId && clickedId !== selectedNodeId) {
      selectedNodeId = clickedId;
      highlightedIds = {};
      highlightedIds[clickedId] = true;
      (adjacency[clickedId] || []).forEach(function(nid) { highlightedIds[nid] = true; });
    } else {
      selectedNodeId = null; highlightedIds = null;
    }
    render();
  });
  canvas.addEventListener("dblclick", function(evt) {
    var rect = canvas.getBoundingClientRect();
    var mx = (evt.clientX - rect.left) * (canvas.width / rect.width) / dpr + scrollX;
    var my = (evt.clientY - rect.top) * (canvas.height / rect.height) / dpr;
    var targets = canvas._clickTargets || [];
    for (var i = 0; i < targets.length; i++) {
      var ct = targets[i]; var dx = mx - ct.x, dy = my - ct.y;
      if (dx * dx + dy * dy <= (ct.r + 6) * (ct.r + 6)) {
        var nd = nodePositions[ct.id];
        var slug = ct.id.split("/").pop();
        var cat = (nd.node.type || "uncategorized").toLowerCase();
        window.location.href = "/categories/" + cat + "/" + slug + ".html";
        break;
      }
    }
  });

  /* ── Pulse animation overlay ── */
  var highImpNodes = Object.keys(nodePositions).filter(function(id) {
    return (nodePositions[id].node.importance || 0) > 0.3;
  });
  if (highImpNodes.length > 0 && isDark) {
    var overlay = document.createElement("canvas");
    overlay.width = canvas.width; overlay.height = canvas.height;
    overlay.style.cssText = "position:absolute;top:0;left:0;width:" + viewW + "px;height:" + h + "px;pointer-events:none;";
    container.appendChild(overlay);
    var octx = overlay.getContext("2d");
    var pulsePhase = 0;
    (function animatePulse() {
      pulsePhase += 0.015;
      var breath = 0.5 + 0.5 * Math.sin(pulsePhase);
      octx.setTransform(dpr, 0, 0, dpr, 0, 0);
      octx.clearRect(0, 0, viewW, h);
      octx.save(); octx.translate(-scrollX, 0);
      highImpNodes.forEach(function(id) {
        var p = nodePositions[id];
        if (p.x < scrollX - 30 || p.x > scrollX + viewW + 30) return;
        if (highlightedIds && !highlightedIds[id]) return;
        var imp = p.node.importance || 0;
        octx.beginPath();
        octx.arc(p.x, p.y, p.r * 5 + breath * 6, 0, 2 * Math.PI);
        octx.fillStyle = p.color;
        octx.globalAlpha = 0.02 + breath * 0.04 * imp;
        octx.fill(); octx.globalAlpha = 1;
      });
      octx.restore();
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
  fetchSearchIndex();
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
