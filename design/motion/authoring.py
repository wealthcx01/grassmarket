"""Shared authoring helpers for Rive course diagrams (GRS-0225).

A scene is plain JSON, so it diffs and reviews like any other source. These helpers exist so the
seven OpenBB diagrams share one palette, one type scale, and one set of conventions rather than
seven slightly different ones.

Two conventions here are not preference, they are the tool's rules and both cost time to discover:

1. **Rive draws the FIRST declared sibling on top.** That is the reverse of SVG, HTML and every
   design tool. `stack()` exists so an author writes children in reading order — front first — and
   does not have to hold the inversion in their head.
2. **A font asset's `source` must resolve inside the project that owns the scene.** Hence the
   vendored Inter subset under `design/motion/assets/fonts/`, with its SIL OFL 1.1 licence beside
   it. A path out to the toolchain's own copy is rejected at generate time.

Geometry note, also the tool's rule: geometry does not move, the parent `shape` does. An `ellipse`
or `rectangle` carries width and height; its position comes from the enclosing `shape`.
"""

from __future__ import annotations

import json
from pathlib import Path

# --- The Bruntsfield palette, not the scaffold template's defaults ------------------------

PAPER = "#F7F5EF"
INK = "#1A1A18"
MUTED = "#6E6A60"
RULE = "#D8D3C7"
GREEN = "#1A3B26"  # Bottle Green, the single accent
GREEN_TINT = "#E4EBE5"
ON_GREEN = "#EDF2EE"  # readable on Bottle Green
ON_GREEN_MUTED = "#B9C7BC"
SIGNAL = "#7FD4A0"  # the "do this" green, used sparingly
WARN = "#A3502A"  # a warm, non-alarming caution; never a fire-engine red

FONT = "Display"
FONT_SOURCE = "../../assets/fonts/Inter-Bold-Subset.ttf"


def text(
    name: str,
    x: float,
    y: float,
    content: str,
    size: float,
    colour: str,
    *,
    letter_spacing: float | None = None,
) -> dict:
    """A centred text run. `text` has no x/y of its own in the spec, so the values here sit on the
    text object itself with a centred origin, which is the simplest form that stays readable."""
    style = f"{name}Style"
    style_node: dict = {
        "type": "text_style",
        "name": style,
        "font_asset": FONT,
        "font_size": size,
        "children": [
            {
                "type": "fill",
                "name": f"{style}Fill",
                "children": [{"type": "solid_color", "name": f"{style}Col", "color": colour}],
            }
        ],
    }
    if letter_spacing is not None:
        style_node["letter_spacing"] = letter_spacing
    return {
        "type": "text",
        "name": name,
        "x": x,
        "y": y,
        "origin_x": 0.5,
        "origin_y": 0.5,
        "sizing_value": 0,
        "children": [
            style_node,
            {"type": "text_value_run", "name": f"{name}Run", "style": style, "text": content},
        ],
    }


def card(
    name: str,
    x: float,
    y: float,
    w: float,
    h: float,
    fill: str,
    *,
    stroke: str | None = None,
    radius: float = 14,
    thickness: float = 2,
) -> dict:
    """A rounded panel. `x`/`y` are its centre, because the geometry uses a centred origin."""
    children: list[dict] = [
        {
            "type": "rectangle",
            "name": f"{name}Path",
            "width": w,
            "height": h,
            "corner_radius": radius,
            "origin_x": 0.5,
            "origin_y": 0.5,
        },
        {
            "type": "fill",
            "name": f"{name}Fill",
            "children": [{"type": "solid_color", "name": f"{name}Solid", "color": fill}],
        },
    ]
    if stroke:
        children.append(
            {
                "type": "stroke",
                "name": f"{name}Stroke",
                "thickness": thickness,
                "children": [{"type": "solid_color", "name": f"{name}StrokeCol", "color": stroke}],
            }
        )
    return {"type": "shape", "name": name, "x": x, "y": y, "children": children}


def line(name: str, x: float, y: float, w: float, h: float, colour: str) -> dict:
    """A rule or a connector. A thin filled rectangle rather than a stroked path, because a filled
    rectangle's thickness is animatable through scale where a stroke's is not."""
    return card(name, x, y, w, h, colour, radius=0)


def arrow_right(name: str, x: float, y: float, length: float, colour: str) -> list[dict]:
    """A horizontal connector with a head. Two shapes rather than one path: simple to position, and
    the head is a triangle whose parent shape carries the rotation."""
    head = 9.0
    return [
        {
            "type": "shape",
            "name": f"{name}Head",
            "x": x + length / 2,
            "y": y,
            "rotation": 1.5708,  # a triangle points up by default; a quarter turn points it right
            "children": [
                {
                    "type": "triangle",
                    "name": f"{name}HeadPath",
                    "width": head * 1.6,
                    "height": head * 1.6,
                    "origin_x": 0.5,
                    "origin_y": 0.5,
                },
                {
                    "type": "fill",
                    "name": f"{name}HeadFill",
                    "children": [
                        {"type": "solid_color", "name": f"{name}HeadCol", "color": colour}
                    ],
                },
            ],
        },
        line(f"{name}Stem", x, y, length - head, 2.5, colour),
    ]


def arrow_down(name: str, x: float, y: float, length: float, colour: str) -> list[dict]:
    head = 9.0
    return [
        {
            "type": "shape",
            "name": f"{name}Head",
            "x": x,
            "y": y + length / 2,
            "rotation": 3.14159,  # point it down
            "children": [
                {
                    "type": "triangle",
                    "name": f"{name}HeadPath",
                    "width": head * 1.6,
                    "height": head * 1.6,
                    "origin_x": 0.5,
                    "origin_y": 0.5,
                },
                {
                    "type": "fill",
                    "name": f"{name}HeadFill",
                    "children": [
                        {"type": "solid_color", "name": f"{name}HeadCol", "color": colour}
                    ],
                },
            ],
        },
        line(f"{name}Stem", x, y, 2.5, length - head, colour),
    ]


def stack(*layers: dict | list[dict]) -> list[dict]:
    """Flatten layers written FRONT FIRST into the child order Rive wants.

    Rive paints the first declared sibling on top, so front-first is already the tool's order. The
    function exists to make that explicit at every call site, because the inversion relative to SVG
    is the single most expensive mistake to make with this format and a silent one: the scene
    compiles, validates, and renders as one flat block of the last colour you declared.
    """
    out: list[dict] = []
    for layer in layers:
        if isinstance(layer, list):
            out.extend(layer)
        else:
            out.append(layer)
    return out


def scene(name: str, width: float, height: float, children: list[dict]) -> dict:
    return {
        "scene_format_version": 1,
        "artboard": {
            "name": name,
            "width": width,
            "height": height,
            "children": [
                {"type": "font_asset", "name": FONT, "source": FONT_SOURCE},
                *children,
            ],
        },
    }


def write(spec: dict, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(spec, indent=2) + "\n")
    return path
