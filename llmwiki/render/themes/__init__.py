"""Theme registry for llmwiki UI.

Each theme defines CSS custom properties that override the defaults.
The layout, components, and JS stay identical — only colors/typography change.

Usage:
    from llmwiki.render.themes import get_theme, list_themes
    theme = get_theme("vodafone")
    css_vars = theme.to_css()
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Theme:
    """A theme is a named set of CSS custom properties."""

    name: str
    display_name: str
    description: str

    # Core colors (dark mode defaults)
    accent: str
    accent_hover: str
    accent_muted: str
    accent_subtle: str
    canvas: str
    surface_0: str
    surface_1: str
    surface_2: str
    surface_3: str
    ink: str
    ink_muted: str
    ink_subtle: str
    ink_faint: str
    hairline: str
    hairline_strong: str

    # Semantic
    success: str = "#10b981"
    warning: str = "#f59e0b"
    error: str = "#ef4444"
    info: str = "#6366f1"

    # Graph node colors
    node_java: str = "#f59e0b"
    node_xml: str = "#6366f1"
    node_beanshell: str = "#ec4899"
    node_docs: str = "#10b981"
    node_config: str = "#8b5cf6"
    node_tokens: str = "#f97316"

    # Light mode overrides
    light_canvas: str = "#fafafa"
    light_surface_0: str = "#ffffff"
    light_surface_1: str = "#f4f4f5"
    light_surface_2: str = "#e4e4e7"
    light_surface_3: str = "#d4d4d8"
    light_ink: str = "#18181b"
    light_ink_muted: str = "#52525b"
    light_ink_subtle: str = "#71717a"
    light_hairline: str = "#e4e4e7"
    light_hairline_strong: str = "#d4d4d8"

    # Typography (optional overrides)
    font_sans: str = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
    font_mono: str = "'SF Mono', 'Cascadia Code', 'JetBrains Mono', Consolas, 'Liberation Mono', monospace"

    def to_css(self) -> str:
        """Generate CSS custom properties block for this theme."""
        dark = f""":root {{
  /* Theme: {self.display_name} */
  --accent: {self.accent};
  --accent-hover: {self.accent_hover};
  --accent-muted: {self.accent_muted};
  --accent-subtle: {self.accent_subtle};
  --canvas: {self.canvas};
  --surface-0: {self.surface_0};
  --surface-1: {self.surface_1};
  --surface-2: {self.surface_2};
  --surface-3: {self.surface_3};
  --ink: {self.ink};
  --ink-muted: {self.ink_muted};
  --ink-subtle: {self.ink_subtle};
  --ink-faint: {self.ink_faint};
  --hairline: {self.hairline};
  --hairline-strong: {self.hairline_strong};
  --success: {self.success};
  --warning: {self.warning};
  --error: {self.error};
  --info: {self.info};
  --node-java: {self.node_java};
  --node-xml: {self.node_xml};
  --node-beanshell: {self.node_beanshell};
  --node-docs: {self.node_docs};
  --node-config: {self.node_config};
  --node-tokens: {self.node_tokens};
  --font-sans: {self.font_sans};
  --font-mono: {self.font_mono};
}}"""

        light = f"""[data-theme="light"] {{
  --canvas: {self.light_canvas};
  --surface-0: {self.light_surface_0};
  --surface-1: {self.light_surface_1};
  --surface-2: {self.light_surface_2};
  --surface-3: {self.light_surface_3};
  --ink: {self.light_ink};
  --ink-muted: {self.light_ink_muted};
  --ink-subtle: {self.light_ink_subtle};
  --hairline: {self.light_hairline};
  --hairline-strong: {self.light_hairline_strong};
}}"""

        return f"{dark}\n\n{light}\n"


# --- Theme Registry ---

_REGISTRY: dict[str, Theme] = {}


def register_theme(theme: Theme) -> Theme:
    """Register a theme in the registry."""
    _REGISTRY[theme.name] = theme
    return theme


def get_theme(name: str) -> Theme:
    """Get a theme by name. Falls back to 'emerald-dark' if not found."""
    _ensure_loaded()
    if name not in _REGISTRY:
        return _REGISTRY.get("emerald-dark", list(_REGISTRY.values())[0])
    return _REGISTRY[name]


def list_themes() -> list[dict]:
    """List all available themes."""
    _ensure_loaded()
    return [
        {"name": t.name, "display_name": t.display_name, "description": t.description}
        for t in _REGISTRY.values()
    ]


def _ensure_loaded() -> None:
    """Load all built-in themes."""
    if _REGISTRY:
        return
    from llmwiki.render.themes import emerald_dark, vodafone  # noqa: F401
