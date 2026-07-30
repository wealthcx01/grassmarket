"""Print-resolution figures for the client report PDF (GRS-0219, scope item 4).

"A chart that only works in colour is a chart that fails in a boardroom printout." So nothing here
is encoded by hue alone. Every series carries a luminance step AND a hatch pattern AND a direct
numeric label, which means each figure survives three different degradations: greyscale printing,
photocopying (which flattens luminance but keeps hatch), and a reader who is colour-blind.

`GREYSCALE_PALETTE` is the contract those guarantees rest on, and it is asserted in tests rather
than eyeballed — pairwise luminance separation is a number, so it is checked as one.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from io import BytesIO
from typing import Any, cast

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

#: Print resolution. 300dpi is the floor for a figure that will be printed rather than viewed.
PRINT_DPI = 300

#: The minimum luminance gap between any two fills in a figure. Below ~0.12 two greys are hard to
#: tell apart on an office laser printer; 0.15 leaves margin.
MIN_LUMINANCE_SEPARATION = 0.15

#: Ordered fills for multi-series figures: a luminance ramp, not a hue wheel. Index 0 is the accent
#: (Bottle Green) because the first series is usually the headline one; the rest are green-tinted
#: neutrals spaced ~0.19 apart in luminance.
#:
#: The spacing is solved, not chosen by eye. A first attempt picked plausible-looking greens whose
#: first two steps were only 0.101 apart — they read as different colours on screen and as the same
#: grey on a printer, which is the exact failure this palette exists to prevent. The test caught it.
GREYSCALE_PALETTE: tuple[str, ...] = ("#1a3b26", "#7a857d", "#a1b0a5", "#bfd0c3")

#: Paired with the palette by index. Hatch survives a photocopy that flattens luminance.
HATCHES: tuple[str, ...] = ("", "///", "...", "xxx")

_INK = "#17191f"
_MUTED = "#6e7079"
_RULE = "#dddbd6"


def relative_luminance(hex_colour: str) -> float:
    """WCAG relative luminance of a hex colour, 0 (black) to 1 (white).

    This is what "legible in greyscale" reduces to: two fills a printer renders as the same grey are
    two fills a reader cannot separate, whatever their hues were.
    """
    raw = hex_colour.lstrip("#")
    channels = [int(raw[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _png(fig: Any) -> bytes:
    """PNG bytes at print resolution, with matplotlib's version stamp stripped so a rebuild on a
    pinned toolchain is byte-identical (the same discipline as `charts._render_png`)."""
    buffer = BytesIO()
    fig.savefig(
        buffer,
        format="png",
        dpi=PRINT_DPI,
        metadata={"Software": None},
        facecolor="white",
        bbox_inches="tight",
    )
    return buffer.getvalue()


def maturity_radar(*, labels: Sequence[str], values: Sequence[float]) -> bytes:
    """Module maturity (q_m, 0–100) as a radar.

    Pass only modules with an assessed score. A module with `q_m is None` is Not Assessed, and
    plotting it at zero would draw a firm as broken where it is merely unmeasured (defect D9).
    """
    if len(labels) != len(values):
        raise ValueError("labels and values must be the same length.")
    if len(labels) < 3:
        raise ValueError("a radar needs at least 3 axes.")

    count = len(labels)
    angles = [2.0 * math.pi * i / count for i in range(count)]
    closed_angles = [*angles, angles[0]]
    closed_values = [*values, values[0]]

    fig, raw_ax = plt.subplots(figsize=(5.4, 5.4), subplot_kw={"polar": True})
    ax = cast(Any, raw_ax)  # PolarAxes methods are absent from matplotlib's base Axes stub
    try:
        ax.set_theta_offset(math.pi / 2)
        ax.set_theta_direction(-1)
        ax.set_thetagrids([math.degrees(a) for a in angles], labels, fontsize=7.5, color=_INK)
        ax.set_ylim(0, 100)
        ax.set_yticks([25, 50, 75, 100])
        ax.set_yticklabels(["25", "50", "75", "100"], fontsize=6.5, color=_MUTED)
        ax.grid(color=_RULE, linewidth=0.6)
        ax.spines["polar"].set_color(_RULE)
        ax.plot(closed_angles, closed_values, color=GREYSCALE_PALETTE[0], linewidth=1.8)
        ax.fill(closed_angles, closed_values, color=GREYSCALE_PALETTE[0], alpha=0.16)
        # The value at each vertex, so the shape is readable even printed small.
        for angle, value in zip(angles, values, strict=True):
            ax.annotate(
                f"{value:.0f}",
                xy=(angle, value),
                fontsize=6.5,
                color=_INK,
                ha="center",
                va="bottom",
            )
        fig.tight_layout()
        return _png(fig)
    finally:
        plt.close(fig)


def value_buildup(*, labels: Sequence[str], values: Sequence[float]) -> bytes:
    """How Platform Value builds up — B → P → L → V as a labelled bar sequence.

    Each bar gets a distinct luminance AND hatch AND its own printed value, so the comparison
    survives greyscale.
    """
    if len(labels) != len(values):
        raise ValueError("labels and values must be the same length.")
    if not labels:
        raise ValueError("value build-up needs at least one term.")

    fig, ax = plt.subplots(figsize=(6.2, 3.4))
    try:
        positions = range(len(labels))
        for index, (position, value) in enumerate(zip(positions, values, strict=True)):
            ax.bar(
                position,
                value,
                width=0.62,
                color=GREYSCALE_PALETTE[index % len(GREYSCALE_PALETTE)],
                hatch=HATCHES[index % len(HATCHES)],
                edgecolor="white",
                linewidth=0.8,
            )
            ax.annotate(
                f"{value:.0f}",
                xy=(position, value),
                xytext=(0, 3),
                textcoords="offset points",
                ha="center",
                fontsize=8.5,
                color=_INK,
            )
        ax.set_xticks(list(positions))
        ax.set_xticklabels(list(labels), fontsize=8.5, color=_INK)
        ax.set_ylim(0, 100)
        ax.set_ylabel("0–100", fontsize=8, color=_MUTED)
        ax.tick_params(axis="y", labelsize=7.5, colors=_MUTED)
        ax.grid(axis="y", color=_RULE, linewidth=0.6, linestyle=":")
        ax.set_axisbelow(True)
        for edge in ("top", "right"):
            ax.spines[edge].set_visible(False)
        for edge in ("left", "bottom"):
            ax.spines[edge].set_color(_RULE)
        fig.tight_layout()
        return _png(fig)
    finally:
        plt.close(fig)


def module_breakdown(*, labels: Sequence[str], values: Sequence[float]) -> bytes:
    """Every assessed module, weakest first — the figure an advisor points at.

    One series, so hue carries nothing: each bar is labelled with its own score and ordered, which
    is what makes the ranking legible in any rendering.
    """
    if len(labels) != len(values):
        raise ValueError("labels and values must be the same length.")
    if not labels:
        raise ValueError("module breakdown needs at least one module.")

    ordered = sorted(zip(labels, values, strict=True), key=lambda pair: pair[1])
    ordered_labels = [pair[0] for pair in ordered]
    ordered_values = [pair[1] for pair in ordered]

    height = max(2.6, 0.32 * len(ordered_labels) + 1.0)
    fig, ax = plt.subplots(figsize=(6.2, height))
    try:
        positions = range(len(ordered_labels))
        ax.barh(
            list(positions),
            ordered_values,
            height=0.62,
            color=GREYSCALE_PALETTE[0],
            edgecolor="white",
            linewidth=0.6,
        )
        for position, value in zip(positions, ordered_values, strict=True):
            ax.annotate(
                f"{value:.0f}",
                xy=(value, position),
                xytext=(4, 0),
                textcoords="offset points",
                va="center",
                fontsize=8,
                color=_INK,
            )
        ax.set_yticks(list(positions))
        ax.set_yticklabels(ordered_labels, fontsize=8, color=_INK)
        ax.set_xlim(0, 108)
        ax.set_xticks([0, 25, 50, 75, 100])
        ax.tick_params(axis="x", labelsize=7.5, colors=_MUTED)
        ax.grid(axis="x", color=_RULE, linewidth=0.6, linestyle=":")
        ax.set_axisbelow(True)
        for edge in ("top", "right"):
            ax.spines[edge].set_visible(False)
        for edge in ("left", "bottom"):
            ax.spines[edge].set_color(_RULE)
        fig.tight_layout()
        return _png(fig)
    finally:
        plt.close(fig)
