"""Deliverable charts (GRS-0016). Matplotlib on the Agg backend — headless, offline, no display.

The one chart Loop 4 needs is the priority-vs-cost scatter: the Upgrade Priority Index (ΔV, score
domain) on one axis and the indicative cost (currency) on the other. They are plotted on SEPARATE
axes and never combined into a ratio — the ADR-0002 boundary, drawn rather than divided. The
function takes plain floats (no `Score`, no `Money` in its signature) so the AST guard stays green.
"""

from __future__ import annotations

from collections.abc import Sequence
from io import BytesIO

import matplotlib

matplotlib.use("Agg")  # headless: set before pyplot is imported

import matplotlib.pyplot as plt  # noqa: E402  (must follow the backend selection)


def priority_cost_scatter(
    *,
    labels: Sequence[str],
    costs_major: Sequence[float],
    priority_points: Sequence[float],
    currency_symbol: str,
) -> bytes:
    """Render the priority-vs-cost scatter to PNG bytes.

    ``priority_points`` is ΔV on the 0–100 display scale (score domain); ``costs_major`` is the
    indicative cost in major currency units (currency domain). One point per intervention, each
    annotated with its label. The two quantities share a plot but never an equation.
    """
    if not (len(labels) == len(costs_major) == len(priority_points)):
        raise ValueError("labels, costs_major and priority_points must be the same length.")
    if not labels:
        raise ValueError("priority_cost_scatter needs at least one intervention to plot.")

    fig, ax = plt.subplots(figsize=(6.2, 4.0))
    try:
        ax.scatter(costs_major, priority_points, s=80, color="#1A3B26", zorder=3)
        for label, x, y in zip(labels, costs_major, priority_points, strict=True):
            ax.annotate(
                label,
                (x, y),
                textcoords="offset points",
                xytext=(6, 4),
                fontsize=8,
                color="#333333",
            )
        ax.set_xlabel(f"Indicative cost ({currency_symbol})")
        ax.set_ylabel("Upgrade Priority Index — ΔV (points, 0–100)")
        ax.set_title("Priority vs cost")
        ax.grid(True, linestyle=":", alpha=0.4, zorder=0)
        ax.margins(0.18)
        fig.tight_layout()
        buffer = BytesIO()
        # metadata={"Software": None} strips matplotlib's version stamp so the same inputs render
        # byte-identical PNGs within a pinned matplotlib/freetype (glyph rasterisation can differ
        # across those versions, so this is not a cross-host guarantee — the run's DATA is the
        # reproducibility contract; the chart image is a rendering of it).
        fig.savefig(buffer, format="png", dpi=150, metadata={"Software": None})
        return buffer.getvalue()
    finally:
        plt.close(fig)
