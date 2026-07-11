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
  initMiniGraph();
});

document.addEventListener("keydown", handleGlobalKeys);

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
    .catch(function() { container.innerHTML = '<p class="text-muted" style="padding:8px;font-size:12px;">Graph unavailable</p>'; });
}

function renderMiniGraph(container, graph, pageId) {
  var nodes = graph.nodes || [];
  var edges = graph.edges || [];

  // Find current node
  var currentNode = nodes.find(function(n) { return n.id === pageId; });
  if (!currentNode) {
    container.innerHTML = '<p class="text-muted" style="padding:8px;font-size:12px;">No graph data</p>';
    return;
  }

  // Find 2-hop neighborhood
  var neighborIds = new Set();
  neighborIds.add(pageId);
  // 1-hop
  edges.forEach(function(e) {
    if (e.from === pageId) neighborIds.add(e.to);
    if (e.to === pageId) neighborIds.add(e.from);
  });
  // 2-hop
  var hop1 = new Set(neighborIds);
  edges.forEach(function(e) {
    if (hop1.has(e.from)) neighborIds.add(e.to);
    if (hop1.has(e.to)) neighborIds.add(e.from);
  });

  // Cap at 40 nodes for readability
  var neighborArr = Array.from(neighborIds).slice(0, 40);
  var neighborSet = new Set(neighborArr);

  var localNodes = nodes.filter(function(n) { return neighborSet.has(n.id); });
  var localEdges = edges.filter(function(e) { return neighborSet.has(e.from) && neighborSet.has(e.to); });

  if (localNodes.length < 2) {
    container.innerHTML = '<p class="text-muted" style="padding:8px;font-size:12px;">No connections</p>';
    return;
  }

  // Canvas render
  var canvas = document.createElement("canvas");
  var w = container.clientWidth || 260;
  var h = 240;
  canvas.width = w * 2; canvas.height = h * 2;
  canvas.style.width = w + "px"; canvas.style.height = h + "px";
  container.appendChild(canvas);
  var ctx = canvas.getContext("2d");
  ctx.scale(2, 2);

  // Simple force-directed layout (few iterations)
  var positions = {};
  var TYPE_COLORS = {
    "rule": "#f59e0b", "workflow": "#6366f1", "beanshell": "#ec4899",
    "connector-guides": "#14b8a6", "iiq-docs": "#f59e0b", "config": "#8b5cf6",
  };

  localNodes.forEach(function(n, i) {
    var angle = (2 * Math.PI * i) / localNodes.length;
    positions[n.id] = {
      x: w/2 + (w/3) * Math.cos(angle) + (Math.random() - 0.5) * 20,
      y: h/2 + (h/3) * Math.sin(angle) + (Math.random() - 0.5) * 20,
      node: n
    };
  });

  // Simple spring simulation (30 iterations)
  for (var iter = 0; iter < 30; iter++) {
    // Repulsion between all nodes
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
    // Attraction along edges
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
    // Center gravity
    localNodes.forEach(function(n) {
      var p = positions[n.id];
      p.x += (w/2 - p.x) * 0.01;
      p.y += (h/2 - p.y) * 0.01;
      // Bounds
      p.x = Math.max(20, Math.min(w - 20, p.x));
      p.y = Math.max(20, Math.min(h - 20, p.y));
    });
  }

  // Draw edges
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

  // Draw nodes
  var nodePositions = []; // for click detection
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

  // Click handler
  canvas.addEventListener("click", function(evt) {
    var rect = canvas.getBoundingClientRect();
    var mx = (evt.clientX - rect.left) * 2;
    var my = (evt.clientY - rect.top) * 2;
    // Scale back since we ctx.scale(2,2)
    mx /= 2; my /= 2;
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

  // Node count label
  var countEl = document.createElement("div");
  countEl.style.cssText = "font-size:11px;color:var(--ink-subtle);padding:4px 8px;";
  countEl.textContent = localNodes.length + " nodes · " + localEdges.length + " edges";
  container.appendChild(countEl);
}

})();
"""
