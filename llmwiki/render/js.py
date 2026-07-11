"""Site JavaScript as Python string constants — dark emerald three-panel design."""

PRE_PAINT_SCRIPT = (
    "(function(){"
    "var t=localStorage.getItem('llmwiki-theme');"
    "if(t==='light')document.documentElement.setAttribute('data-theme','light');"
    "else if(t==='system'||!t){"
    "if(window.matchMedia('(prefers-color-scheme:light)').matches)"
    "document.documentElement.setAttribute('data-theme','light');}"
    "})()"
)

JS = """\
(function() {
"use strict";

/* ===== Theme Toggle ===== */
var THEME_KEY = "llmwiki-theme";

function getSystemTheme() {
  return window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
}

function getEffectiveTheme() {
  var stored = localStorage.getItem(THEME_KEY);
  if (stored === "dark" || stored === "light") return stored;
  return getSystemTheme();
}

function applyTheme(theme) {
  if (theme === "light") {
    document.documentElement.setAttribute("data-theme", "light");
  } else {
    document.documentElement.removeAttribute("data-theme");
  }
  var btn = document.querySelector(".theme-toggle");
  if (btn) {
    btn.textContent = theme === "dark" ? "\\u2600\\ufe0f" : "\\ud83c\\udf19";
    btn.setAttribute("aria-label", "Theme: " + theme);
  }
}

function cycleTheme() {
  var stored = localStorage.getItem(THEME_KEY);
  var next;
  if (!stored || stored === "system") {
    next = "dark";
  } else if (stored === "dark") {
    next = "light";
  } else {
    next = "system";
  }
  if (next === "system") {
    localStorage.removeItem(THEME_KEY);
    applyTheme(getSystemTheme());
  } else {
    localStorage.setItem(THEME_KEY, next);
    applyTheme(next);
  }
}

applyTheme(getEffectiveTheme());

/* ===== Sidebar Toggle ===== */
function toggleSidebar() {
  var layout = document.querySelector(".app-layout");
  if (!layout) return;
  var isCollapsed = layout.classList.contains("sidebar-collapsed");
  if (window.innerWidth < 1280) {
    layout.classList.toggle("sidebar-open");
  } else {
    layout.classList.toggle("sidebar-collapsed");
  }
}

/* ===== Graph Panel Toggle ===== */
function toggleGraph() {
  var layout = document.querySelector(".app-layout");
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
      paletteInput = paletteEl.querySelector(".palette-input");
      paletteResults = paletteEl.querySelector(".palette-results");
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

  // Structured queries
  var typeMatch = q.match(/^type:\\s*(\\S+)\\s*(.*)$/i);
  var catMatch = q.match(/^category:\\s*(\\S+)\\s*(.*)$/i);
  var tagMatch = q.match(/^tag:\\s*(\\S+)\\s*(.*)$/i);

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

  // Fuzzy search with scoring
  var scored = searchIndex.map(function(e) {
    var titleScore = scoreMatch(e.title || "", q);
    var bodyScore = scoreMatch((e.body || "").substring(0, 200), q) * 0.5;
    return { entry: e, score: titleScore + bodyScore };
  }).filter(function(s) { return s.score > 0; });

  scored.sort(function(a, b) { return b.score - a.score; });
  return scored.map(function(s) { return s.entry; }).slice(0, 30);
}

var TYPE_ICONS = {
  "rule": "\\u2699",
  "workflow": "\\u21c4",
  "application": "\\u26a1",
  "task": "\\u23f0",
  "report": "\\ud83d\\udcca",
  "custom": "\\u2b21",
  "default": "\\ud83d\\udcc4"
};

function getTypeIcon(type) {
  if (!type) return TYPE_ICONS["default"];
  var base = type.split("/")[0].toLowerCase();
  return TYPE_ICONS[base] || TYPE_ICONS["default"];
}

function renderResults(entries) {
  if (!paletteResults) return;
  if (!entries || entries.length === 0) {
    paletteResults.innerHTML = '<div class="palette-empty">No results found</div>';
    return;
  }
  var html = "";
  for (var i = 0; i < entries.length; i++) {
    var e = entries[i];
    var cls = i === selectedIdx ? "palette-result selected" : "palette-result";
    var icon = getTypeIcon(e.type || e.category);
    var cat = e.category || "";
    html += '<div class="' + cls + '" data-url="' + escapeAttr(e.url || "#") + '" data-idx="' + i + '">';
    html += '<span class="result-icon">' + icon + '</span>';
    html += '<span class="result-title">' + escapeHtml(e.title || e.id || "") + '</span>';
    if (cat) html += '<span class="result-category">' + escapeHtml(cat) + '</span>';
    html += '</div>';
  }
  paletteResults.innerHTML = html;
  // Scroll selected into view
  var sel = paletteResults.querySelector(".selected");
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
    if (e.key === "Escape") {
      e.target.blur();
      closePalette();
    }
    return;
  }

  // Cmd+K / Ctrl+K
  if ((e.metaKey || e.ctrlKey) && e.key === "k") {
    e.preventDefault();
    if (getPalette() && !getPalette().hidden) closePalette();
    else openPalette();
    return;
  }

  // "/" focus search
  if (e.key === "/") { e.preventDefault(); openPalette(); return; }

  // "?" keyboard help
  if (e.key === "?" && !e.ctrlKey && !e.metaKey) {
    e.preventDefault(); toggleKeyboardHelp(); return;
  }

  // Escape
  if (e.key === "Escape") { closePalette(); hideKeyboardHelp(); return; }

  // j/k table navigation
  if (e.key === "j" || e.key === "k") { navigateTableRows(e.key === "j" ? 1 : -1); return; }

  // g-prefixed
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
  overlay.className = "kbd-help-overlay";
  overlay.innerHTML =
    '<div class="kbd-help-dialog">' +
    '<h2>Keyboard Shortcuts</h2><dl>' +
    '<dt><kbd>/</kbd> or <kbd>\\u2318K</kbd></dt><dd>Open search</dd>' +
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
  var rows = document.querySelectorAll(".pages-table tbody tr:not(.hidden)");
  if (!rows.length) return;
  var current = document.querySelector(".pages-table tbody tr.row-focus");
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
  var blocks = document.querySelectorAll("pre");
  for (var i = 0; i < blocks.length; i++) {
    var pre = blocks[i];
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
          btnEl.classList.add("copied");
          setTimeout(function() {
            btnEl.textContent = "Copy";
            btnEl.classList.remove("copied");
          }, 2000);
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
  var input = document.querySelector(".filter-input");
  if (!input) return;
  input.addEventListener("input", function() {
    var query = input.value.toLowerCase();
    var rows = document.querySelectorAll(".pages-table tbody tr");
    var cards = document.querySelectorAll(".card-grid .card");
    for (var i = 0; i < rows.length; i++) {
      var row = rows[i];
      var text = row.textContent.toLowerCase();
      var tags = (row.getAttribute("data-tags") || "").toLowerCase();
      row.classList.toggle("hidden", query && text.indexOf(query) === -1 && tags.indexOf(query) === -1);
    }
    for (var j = 0; j < cards.length; j++) {
      var card = cards[j];
      var cText = card.textContent.toLowerCase();
      var cTags = (card.getAttribute("data-tags") || "").toLowerCase();
      card.style.display = (!query || cText.indexOf(query) !== -1 || cTags.indexOf(query) !== -1) ? "" : "none";
    }
  });
}

/* ===== Table Sorting ===== */
function initTableSorting() {
  var tables = document.querySelectorAll(".pages-table");
  for (var t = 0; t < tables.length; t++) {
    var table = tables[t];
    var headers = table.querySelectorAll("thead th");
    for (var h = 0; h < headers.length; h++) {
      (function(th, colIdx, tbl) {
        th.addEventListener("click", function() {
          sortTable(tbl, colIdx, th);
        });
      })(headers[h], h, table);
    }
  }
}

function sortTable(table, colIdx, th) {
  var tbody = table.querySelector("tbody");
  if (!tbody) return;
  var rows = Array.prototype.slice.call(tbody.querySelectorAll("tr"));
  var dir = th.getAttribute("data-sort-dir") === "asc" ? "desc" : "asc";

  // Reset all headers
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

  // Highlight active item based on URL
  var path = window.location.pathname;
  var items = document.querySelectorAll(".sidebar-tree-item");
  for (var j = 0; j < items.length; j++) {
    var href = items[j].getAttribute("href") || items[j].getAttribute("data-href");
    if (href && path.indexOf(href) !== -1) {
      items[j].classList.add("active");
    }
  }
}

/* ===== Scroll Spy ===== */
function initScrollSpy() {
  var mainContent = document.querySelector(".main-content");
  if (!mainContent) return;
  var items = document.querySelectorAll(".sidebar-tree-item[data-href]");
  if (!items.length) return;

  mainContent.addEventListener("scroll", debounce(function() {
    var headings = mainContent.querySelectorAll("h1, h2, h3");
    if (!headings.length) return;
    // Simple: highlight the sidebar item matching closest heading
  }, 100));
}

function debounce(fn, ms) {
  var timer;
  return function() {
    clearTimeout(timer);
    timer = setTimeout(fn, ms);
  };
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

/* ===== Event Delegation ===== */
function initEventDelegation() {
  document.addEventListener("click", function(e) {
    // Theme toggle
    if (e.target.closest(".theme-toggle")) { cycleTheme(); return; }
    // Search triggers
    if (e.target.closest(".search-trigger") || e.target.closest(".sidebar-search")) {
      openPalette(); return;
    }
    // Sidebar toggle
    if (e.target.closest(".sidebar-toggle")) { toggleSidebar(); return; }
    // Graph toggle
    if (e.target.closest(".graph-toggle")) { toggleGraph(); return; }
    // Palette overlay click
    if (e.target.closest("#command-palette") && e.target.id === "command-palette") {
      closePalette(); return;
    }
    // Palette result click
    var resultEl = e.target.closest(".palette-result");
    if (resultEl && resultEl.dataset.url) {
      window.location.href = resultEl.dataset.url; return;
    }
  });
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
  initScrollSpy();
  initBottomTabs();
  initEventDelegation();
  initPaletteInput();
});

document.addEventListener("keydown", handleGlobalKeys);

})();
"""
