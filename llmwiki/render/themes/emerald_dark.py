"""Emerald Dark theme — the default llmwiki theme.

Inspired by Supabase/VoltAgent. Dark-first with emerald accent.
"""

from llmwiki.render.themes import Theme, register_theme

register_theme(Theme(
    name="emerald-dark",
    display_name="Emerald Dark",
    description="Dark-first with emerald accent. Inspired by Supabase/VoltAgent.",

    accent="#10b981",
    accent_hover="#34d399",
    accent_muted="#065f46",
    accent_subtle="#022c22",
    canvas="#0a0a0f",
    surface_0="#12121a",
    surface_1="#1a1a25",
    surface_2="#22222e",
    surface_3="#2a2a38",
    ink="#e4e4e7",
    ink_muted="#a1a1aa",
    ink_subtle="#71717a",
    ink_faint="#52525b",
    hairline="#27272a",
    hairline_strong="#3f3f46",
))
