"""Deliverable charts (GRS-0016). Matplotlib on the Agg backend — headless, offline, no display.

The one chart Loop 4 needs is the priority-vs-cost scatter: the Upgrade Priority Index (ΔV, score
domain) on one axis and the indicative cost (currency) on the other. They are plotted on SEPARATE
axes and never combined into a ratio — the ADR-0002 boundary, drawn rather than divided. The
function takes plain floats (no `Score`, no `Money` in its signature) so the AST guard stays green.
"""

from __future__ import annotations

from collections.abc import Sequence
from io import BytesIO
from typing import Any, cast

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
        return _render_png(fig)
    finally:
        plt.close(fig)


def _render_png(fig) -> bytes:
    """Deterministic PNG bytes: strip matplotlib's version stamp so the same inputs render
    byte-identical (reproducibility — a deliverable regenerates the same on any host, GRS-0018)."""
    buffer = BytesIO()
    fig.savefig(buffer, format="png", dpi=150, metadata={"Software": None})
    return buffer.getvalue()


def module_radar(*, labels: Sequence[str], values: Sequence[float]) -> bytes:
    """A radar of module maturity (q_m on the 0–100 display scale). Deterministic. Modules with no
    assessed subcomponent are the caller's concern — pass only scoreable modules (never a 0.0 for an
    empty module: that is defect D9)."""
    if len(labels) != len(values):
        raise ValueError("labels and values must be the same length.")
    if len(labels) < 3:
        raise ValueError("a radar needs at least 3 axes.")
    n = len(labels)
    # Close the polygon by repeating the first point.
    angles = [2.0 * 3.141592653589793 * i / n for i in range(n)]
    angles_closed = [*angles, angles[0]]
    values_closed = [*values, values[0]]
    fig, ax_ = plt.subplots(figsize=(6.0, 6.0), subplot_kw={"polar": True})
    ax = cast(Any, ax_)  # PolarAxes methods aren't on matplotlib's base Axes stub
    try:
        ax.set_theta_offset(3.141592653589793 / 2)
        ax.set_theta_direction(-1)
        ax.set_thetagrids([a * 180 / 3.141592653589793 for a in angles], labels, fontsize=8)
        ax.set_ylim(0, 100)
        ax.plot(angles_closed, values_closed, color="#1A3B26", linewidth=2)
        ax.fill(angles_closed, values_closed, color="#1A3B26", alpha=0.20)
        ax.set_title("Module maturity (q_m, 0–100)")
        fig.tight_layout()
        return _render_png(fig)
    finally:
        plt.close(fig)


def evolution_lines(*, run_labels: Sequence[str], series: dict[str, Sequence[float]]) -> bytes:
    """One line per index (V/B/P/L) across successive runs. Deterministic from the stored runs."""
    if len(run_labels) < 2:
        raise ValueError("score evolution needs at least 2 runs to plot.")
    fig, ax = plt.subplots(figsize=(7.0, 4.0))
    try:
        x = list(range(len(run_labels)))
        for name, ys in series.items():
            if len(ys) != len(run_labels):
                raise ValueError(f"series '{name}' length does not match run_labels.")
            ax.plot(x, list(ys), marker="o", label=name)
        ax.set_xticks(x)
        ax.set_xticklabels(list(run_labels), fontsize=8)
        ax.set_ylabel("Index (points, 0–100)")
        ax.set_title("Score evolution")
        ax.grid(True, linestyle=":", alpha=0.4)
        ax.legend(fontsize=8)
        fig.tight_layout()
        return _render_png(fig)
    finally:
        plt.close(fig)


def index_tornado(
    *,
    labels: Sequence[str],
    lows: Sequence[float],
    mids: Sequence[float],
    highs: Sequence[float],
) -> bytes:
    """Horizontal P10–P90 range bars per index — the uncertainty at a glance (Methodology §7). An
    unmodelled index passes low==mid==high (a point), so it reads honestly as a zero-width bar."""
    if not (len(labels) == len(lows) == len(mids) == len(highs)):
        raise ValueError("labels, lows, mids and highs must be the same length.")
    if not labels:
        raise ValueError("index_tornado needs at least one index.")
    fig, ax = plt.subplots(figsize=(7.0, 0.6 * len(labels) + 1.5))
    try:
        y = list(range(len(labels)))
        for yi, low, mid, high in zip(y, lows, mids, highs, strict=True):
            ax.plot([low, high], [yi, yi], color="#1A3B26", linewidth=6, solid_capstyle="round")
            ax.plot([mid], [yi], marker="|", markersize=14, color="#8A2020")
        ax.set_yticks(y)
        ax.set_yticklabels(list(labels))
        ax.set_xlim(0, 100)
        ax.set_xlabel("Index (points, 0–100) — P10–P90 range, P50 marked")
        ax.set_title("Uncertainty ranges")
        ax.grid(True, axis="x", linestyle=":", alpha=0.4)
        fig.tight_layout()
        return _render_png(fig)
    finally:
        plt.close(fig)
