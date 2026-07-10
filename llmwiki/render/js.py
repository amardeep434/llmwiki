"""Site JavaScript as Python string constants."""

PRE_PAINT_SCRIPT = (
    "var t=localStorage.getItem('llmwiki-theme');"
    "if(t!=='dark'&&t!=='light'){t=window.matchMedia('(prefers-color-scheme:light)').matches?'light':'dark'}"
    "document.documentElement.setAttribute('data-theme',t);"
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
  document.documentElement.setAttribute("data-theme", theme);
  var btn = document.querySelector(".theme-toggle");
  if (btn) {
    btn.textContent = theme === "dark" ? "\\u2600\\uFE0F" : "\\uD83C\\uDF19";
    btn.setAttribute("aria-label", "Current theme: " + theme + ". Click to toggle.");
  }
}

function cycleTheme() {
  var stored = localStorage.getItem(THEME_KEY);
  var next;
  if (stored === null || stored === "system") {
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

document.addEventListener("click", function(e) {
  if (e.target.closest(".theme-toggle")) {
    cycleTheme();
  }
});

/* ===== Command Palette ===== */
var paletteEl = document.getElementById("command-palette");
var paletteInput = paletteEl ? paletteEl.querySelector(".palette-input") : null;
var paletteResults = paletteEl ? paletteEl.querySelector(".palette-results") : null;
var searchIndex = null;
var selectedIdx = -1;

function openPalette() {
  if (!paletteEl) return;
  paletteEl.hidden = false;
  if (paletteInput) {
    paletteInput.value = "";
    paletteInput.focus();
  }
  selectedIdx = -1;
  if (paletteResults) paletteResults.innerHTML = "";
  if (!searchIndex) {
    fetchSearchIndex();
  }
}

function closePalette() {
  if (!paletteEl) return;
  paletteEl.hidden = true;
  selectedIdx = -1;
}

function fetchSearchIndex() {
  fetch("/search-index.json")
    .then(function(r) { return r.json(); })
    .then(function(data) {
      searchIndex = data.entries || [];
    })
    .catch(function() {
      searchIndex = [];
    });
}

function fuzzyMatch(text, query) {
  if (!query) return true;
  var lower = text.toLowerCase();
  var q = query.toLowerCase();
  return lower.indexOf(q) !== -1;
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

  // Fuzzy search on title + body
  return searchIndex.filter(function(e) {
    return fuzzyMatch(e.title + " " + (e.body || ""), q);
  }).slice(0, 30);
}

function renderResults(entries) {
  if (!paletteResults) return;
  if (entries.length === 0) {
    paletteResults.innerHTML = '<div class="palette-result"><span class="result-title">No results</span></div>';
    return;
  }
  var html = "";
  for (var i = 0; i < entries.length; i++) {
    var e = entries[i];
    var cls = i === selectedIdx ? "palette-result selected" : "palette-result";
    html += '<div class="' + cls + '" data-url="' + (e.url || "#") + '" data-idx="' + i + '">';
    html += '<span class="result-title">' + escapeHtml(e.title || e.id) + '</span>';
    html += '<span class="result-type">' + escapeHtml(e.type || "") + '</span>';
    html += '</div>';
  }
  paletteResults.innerHTML = html;
}

function escapeHtml(s) {
  var div = document.createElement("div");
  div.appendChild(document.createTextNode(s));
  return div.innerHTML;
}

function navigateResult(entries) {
  if (selectedIdx >= 0 && selectedIdx < entries.length) {
    var url = entries[selectedIdx].url;
    if (url) window.location.href = url;
  }
}

if (paletteInput) {
  var currentEntries = [];
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
      navigateResult(currentEntries);
    } else if (e.key === "Escape") {
      e.preventDefault();
      closePalette();
    }
  });
}

if (paletteEl) {
  paletteEl.addEventListener("click", function(e) {
    if (e.target === paletteEl) {
      closePalette();
    }
    var resultEl = e.target.closest(".palette-result");
    if (resultEl && resultEl.dataset.url) {
      window.location.href = resultEl.dataset.url;
    }
  });
}

document.addEventListener("click", function(e) {
  if (e.target.closest(".nav-search")) {
    openPalette();
  }
});

/* ===== Keyboard Shortcuts ===== */
var gPressed = false;
var gTimeout = null;

document.addEventListener("keydown", function(e) {
  var tag = (e.target.tagName || "").toLowerCase();
  if (tag === "input" || tag === "textarea" || tag === "select" || e.target.isContentEditable) {
    if (e.key === "Escape") {
      e.target.blur();
      closePalette();
    }
    return;
  }

  // Cmd+K / Ctrl+K
  if ((e.metaKey || e.ctrlKey) && e.key === "k") {
    e.preventDefault();
    if (paletteEl && !paletteEl.hidden) {
      closePalette();
    } else {
      openPalette();
    }
    return;
  }

  // "/" focus search
  if (e.key === "/") {
    e.preventDefault();
    openPalette();
    return;
  }

  // "?" show keyboard help
  if (e.key === "?" && !e.ctrlKey && !e.metaKey) {
    e.preventDefault();
    toggleKeyboardHelp();
    return;
  }

  // Escape
  if (e.key === "Escape") {
    closePalette();
    hideKeyboardHelp();
    return;
  }

  // j/k table row navigation
  if (e.key === "j" || e.key === "k") {
    navigateTableRows(e.key === "j" ? 1 : -1);
    return;
  }

  // g-prefixed shortcuts
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
    if (e.key === "h") {
      window.location.href = "/";
    } else if (e.key === "c") {
      window.location.href = "/categories/";
    }
    return;
  }
});

/* ===== Keyboard Help Modal ===== */
function toggleKeyboardHelp() {
  var el = document.getElementById("kbd-help");
  if (el) {
    el.hidden = !el.hidden;
    return;
  }
  var overlay = document.createElement("div");
  overlay.id = "kbd-help";
  overlay.className = "kbd-help-overlay";
  overlay.innerHTML =
    '<div class="kbd-help-dialog">' +
    '<h2>Keyboard Shortcuts</h2>' +
    '<dl>' +
    '<dt><kbd>/</kbd> or <kbd>Ctrl+K</kbd></dt><dd>Open search</dd>' +
    '<dt><kbd>j</kbd> / <kbd>k</kbd></dt><dd>Next / previous row</dd>' +
    '<dt><kbd>g</kbd> then <kbd>h</kbd></dt><dd>Go home</dd>' +
    '<dt><kbd>g</kbd> then <kbd>c</kbd></dt><dd>Go to categories</dd>' +
    '<dt><kbd>?</kbd></dt><dd>Show this help</dd>' +
    '<dt><kbd>Esc</kbd></dt><dd>Close dialogs</dd>' +
    '</dl></div>';
  overlay.addEventListener("click", function(e) {
    if (e.target === overlay) overlay.hidden = true;
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
    btn.setAttribute("aria-label", "Copy code to clipboard");
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
    for (var i = 0; i < rows.length; i++) {
      var row = rows[i];
      var text = row.textContent.toLowerCase();
      var tags = (row.getAttribute("data-tags") || "").toLowerCase();
      if (!query || text.indexOf(query) !== -1 || tags.indexOf(query) !== -1) {
        row.classList.remove("hidden");
      } else {
        row.classList.add("hidden");
      }
    }
  });
}

/* ===== Auto-Collapse Details ===== */
function initAutoCollapse() {
  var details = document.querySelectorAll("details");
  for (var i = 0; i < details.length; i++) {
    var el = details[i];
    var content = el.querySelector(":not(summary)");
    if (content) {
      var lineCount = (content.textContent || "").split("\\n").length;
      if (lineCount > 20) {
        el.removeAttribute("open");
      }
    }
  }
}

/* ===== Mobile Hamburger Menu ===== */
function initHamburger() {
  var nav = document.querySelector(".nav-bar");
  if (!nav) return;
  var links = nav.querySelector(".nav-links");
  if (!links) return;
  var existing = nav.querySelector(".hamburger");
  if (existing) return;
  var btn = document.createElement("button");
  btn.className = "hamburger";
  btn.setAttribute("aria-label", "Toggle navigation menu");
  btn.innerHTML = "<span></span><span></span><span></span>";
  btn.addEventListener("click", function() {
    links.classList.toggle("open");
  });
  // Insert before nav-links
  nav.insertBefore(btn, links);
}

/* ===== Highlight.js Init ===== */
function initHighlight() {
  if (typeof hljs !== "undefined") {
    hljs.highlightAll();
  }
}

/* ===== Reading Progress Bar ===== */
function initProgressBar() {
  if (!document.querySelector(".page-detail")) return;
  var bar = document.createElement("div");
  bar.className = "progress-bar";
  bar.style.width = "0%";
  document.body.appendChild(bar);
  window.addEventListener("scroll", function() {
    var h = document.documentElement.scrollHeight - window.innerHeight;
    if (h > 0) {
      var pct = Math.min(100, (window.scrollY / h) * 100);
      bar.style.width = pct + "%";
    }
  });
}

/* ===== Init ===== */
document.addEventListener("DOMContentLoaded", function() {
  initHighlight();
  initCopyButtons();
  initFilterBar();
  initAutoCollapse();
  initHamburger();
  initProgressBar();
});

})();
"""
