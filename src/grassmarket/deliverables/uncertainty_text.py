"""Uncertainty statement text (GRS-0015, ADR-0008 / Methodology §7).

Every index statement honours the band's ``modelled`` flag. A modelled index prints as
``V = 51.1 (range 48.4–53.9)``; an **unmodelled** index prints as a labelled POINT —
``B = 67.9 (uncertainty not modelled)`` — never a false-tight band. This is the same honesty
guarantee the wizard renders, restated for the document layer.
"""

from __future__ import annotations

from grassmarket.atlas.montecarlo import Band

NOT_MODELLED_LABEL = "uncertainty not modelled"


def to_display(value: float) -> float:
    """Scale a stored [0,1] score to the 0–100 display convention (ADR-0001 §4)."""
    return value * 100


def format_index_statement(name: str, band: Band) -> str:
    """A one-line honest statement. Modelled → a range; unmodelled → a labelled point."""
    mid = to_display(band.p50)
    if not band.modelled:
        return f"{name} = {mid:.1f} ({NOT_MODELLED_LABEL})"
    low = to_display(band.p10)
    high = to_display(band.p90)
    return f"{name} = {mid:.1f} (range {low:.1f}–{high:.1f})"
