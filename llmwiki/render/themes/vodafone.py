"""Vodafone theme — bold red accent on dark surfaces.

Inspired by Vodafone's brand identity: monumental, confident, red-driven.
"""

from llmwiki.render.themes import Theme, register_theme

register_theme(Theme(
    name="vodafone",
    display_name="Vodafone",
    description="Bold Vodafone Red on dark surfaces. Monumental and confident.",

    # Vodafone Red palette
    accent="#e60000",
    accent_hover="#ff1a1a",
    accent_muted="#7a0000",
    accent_subtle="#2d0000",

    # Dark surfaces
    canvas="#0a0a0a",
    surface_0="#141414",
    surface_1="#1c1c1c",
    surface_2="#262626",
    surface_3="#303030",

    # Text
    ink="#f5f5f5",
    ink_muted="#a3a3a3",
    ink_subtle="#737373",
    ink_faint="#525252",

    # Borders
    hairline="#262626",
    hairline_strong="#404040",

    # Semantic
    success="#22c55e",
    warning="#f59e0b",
    error="#e60000",
    info="#3b82f6",

    # Graph nodes (matching preview)
    node_java="#f59e0b",
    node_xml="#818cf8",
    node_beanshell="#f472b6",
    node_docs="#e60000",
    node_config="#a78bfa",
    node_tokens="#fb923c",

    # Light mode (matching preview vodafone-light)
    light_accent_hover="#cc0000",
    light_accent_muted="#fecaca",
    light_accent_subtle="#fef2f2",
    light_canvas="#ffffff",
    light_surface_0="#f9fafb",
    light_surface_1="#f3f4f6",
    light_surface_2="#e5e7eb",
    light_surface_3="#d1d5db",
    light_ink="#111827",
    light_ink_muted="#4b5563",
    light_ink_subtle="#6b7280",
    light_ink_faint="#9ca3af",
    light_hairline="#e5e7eb",
    light_hairline_strong="#d1d5db",
    light_node_java="#d97706",
    light_node_xml="#4f46e5",
    light_node_beanshell="#db2777",
    light_node_docs="#dc2626",
    light_node_config="#7c3aed",
    light_node_tokens="#ea580c",
))
