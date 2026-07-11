"""Vodafone theme — bold red accent on dark surfaces.

Inspired by Vodafone's brand identity: monumental, confident, red-driven.
"""

from llmwiki.render.themes import Theme, register_theme

register_theme(Theme(
    name="vodafone",
    display_name="Vodafone",
    description="Bold Vodafone Red on dark surfaces. Monumental and confident.",

    # Vodafone Red palette
    accent="#e60000",              # Vodafone Red
    accent_hover="#ff1a1a",        # Lighter red on hover
    accent_muted="#7a0000",        # Dark red for backgrounds
    accent_subtle="#2d0000",       # Very dark red tint

    # Dark surfaces (slightly warm)
    canvas="#0a0a0a",              # Pure near-black
    surface_0="#141414",           # Card background
    surface_1="#1c1c1c",           # Elevated surface
    surface_2="#262626",           # Hover state
    surface_3="#303030",           # Active/selected

    # Text (warm white)
    ink="#f5f5f5",                 # Primary text
    ink_muted="#a3a3a3",           # Secondary text
    ink_subtle="#737373",          # Tertiary
    ink_faint="#525252",           # Disabled

    # Borders
    hairline="#262626",            # Subtle
    hairline_strong="#404040",     # Prominent

    # Semantic (adjusted for red accent)
    success="#22c55e",             # Green (distinct from accent)
    warning="#f59e0b",             # Amber
    error="#e60000",               # Same as accent (intentional for Vodafone)
    info="#3b82f6",                # Blue

    # Graph nodes (adjusted to complement red)
    node_java="#f59e0b",           # Amber
    node_xml="#3b82f6",            # Blue
    node_beanshell="#a855f7",      # Purple
    node_docs="#22c55e",           # Green
    node_config="#06b6d4",         # Cyan
    node_tokens="#f97316",         # Orange

    # Light mode
    light_canvas="#ffffff",
    light_surface_0="#f9fafb",
    light_surface_1="#f3f4f6",
    light_surface_2="#e5e7eb",
    light_surface_3="#d1d5db",
    light_ink="#111827",
    light_ink_muted="#4b5563",
    light_ink_subtle="#6b7280",
    light_hairline="#e5e7eb",
    light_hairline_strong="#d1d5db",
))
