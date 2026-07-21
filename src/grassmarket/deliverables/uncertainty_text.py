"""Uncertainty statement text (GRS-0015, ADR-0008 / Methodology §7).

The HEADLINE figure is the deterministic index `point` — the immutable finalised score stored on the
scoring run (non-negotiable #6) and the same number the portfolio shows, so the two surfaces never
disagree (GRS-0161). The band is the MODELLED P10–P90 uncertainty around it. A modelled index prints
as ``V = 60.5 (modelled range 56.1–61.1)``; an **unmodelled** index prints as a labelled POINT —
``B = 67.9 (uncertainty not modelled)`` — never a false-tight band. The range is clamped to contain
the point, so a downward-skewed distribution never renders the score outside its own range.
"""

from __future__ import annotations

from grassmarket.atlas.montecarlo import Band

NOT_MODELLED_LABEL = "uncertainty not modelled"


def to_display(value: float) -> float:
    """Scale a stored [0,1] score to the 0–100 display convention (ADR-0001 §4)."""
    return value * 100


def format_index_statement(name: str, point: float, band: Band) -> str:
    """A one-line honest statement. Headline = the deterministic `point` (the stored score);
    modelled → a clamped P10–P90 range around it; unmodelled → a labelled point."""
    val = to_display(point)
    if not band.modelled:
        return f"{name} = {val:.1f} ({NOT_MODELLED_LABEL})"
    low = min(to_display(band.p10), val)
    high = max(to_display(band.p90), val)
    return f"{name} = {val:.1f} (modelled range {low:.1f}–{high:.1f})"
