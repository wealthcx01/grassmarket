"""Render a SceneSpec to SVG (GRS-0225).

Why this exists rather than an export flag on the toolchain: `rive-cli` has no vector output. Its
`render` drives headless Chromium and writes PNG, and `SVGAsset` appears in its object registry only
as an *input* — an SVG you embed into a scene, never one you get back out. Checked against
`rive-cli --help`, `render --help` and the crate source on 2026-07-29.

The scene specs are ours, written by `authoring.py`, so the second renderer reads the same source
rather than the compiled artefact. That keeps one source of truth: a diagram is its JSON, and both
the `.riv` and the `.svg` are outputs of it. It also means `LessonAsset` takes these unchanged —
the contract wants an inline SVG string and now that is what the pipeline produces, so no contract
amendment and no raster data URI.

**This is a second renderer of the same source, so it can disagree with the first.** The committed
`.riv` stills are the reference: `tests/test_course_diagrams.py` renders both and compares ink
coverage per region. Text metrics are where they will differ — Rive lays out text itself, a browser
lays out SVG text — so the comparison is deliberately structural, not per-pixel.

Two rules that are not preference:

1. **Sibling order inverts.** Rive paints the FIRST declared sibling on top; SVG paints the LAST.
   Every child list is reversed on the way out. Getting this wrong is silent — the background card
   is declared last in every scene, so a non-inverting emitter produces one flat rectangle of
   paper and nothing else.
2. **Unknown input is refused, never skipped.** An unrecognised node type, or a known type carrying
   a property this emitter does not implement, raises. A silently dropped `opacity` would render a
   diagram that looks finished and is wrong, which is the failure mode #3 exists to prevent.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

# The font the vendored asset actually is. Rive renders with the Inter Bold subset under
# `assets/fonts/`; the page has Inter from the design system, so the SVG names it and gives the
# weight explicitly rather than relying on a default.
FONT_FAMILY = "Inter, system-ui, sans-serif"
FONT_WEIGHT = "700"

# Every property this emitter understands, per node type. A key outside these sets is an error —
# see rule 2 above. `name` is universal and carries no visual meaning.
_KNOWN: dict[str, set[str]] = {
    "font_asset": {"source"},
    "shape": {"x", "y", "rotation"},
    "rectangle": {"width", "height", "corner_radius", "origin_x", "origin_y"},
    "triangle": {"width", "height", "origin_x", "origin_y"},
    "ellipse": {"width", "height", "origin_x", "origin_y"},
    "fill": set(),
    "stroke": {"thickness"},
    "solid_color": {"color"},
    "text": {"x", "y", "origin_x", "origin_y", "sizing_value"},
    "text_style": {"font_asset", "font_size", "letter_spacing"},
    "text_value_run": {"style", "text"},
}

_GEOMETRY = {"rectangle", "triangle", "ellipse"}

# Animated properties this emitter can resolve into a still. Anything else animated is refused:
# a scene whose rotation is keyframed would otherwise export a still of the wrong picture, and
# quietly.
_ANIMATABLE = {"opacity", "color", "scale_x", "scale_y"}


class SceneError(ValueError):
    """A scene this emitter cannot render faithfully. Never raised for something it could guess."""


def _check(node: dict[str, Any]) -> str:
    kind = node.get("type")
    if not isinstance(kind, str):
        raise SceneError(f"Node with no type: {node.get('name', node)!r}")
    if kind not in _KNOWN:
        raise SceneError(
            f"{kind!r} has no SVG mapping. Add one to svg_export.py rather than letting the "
            f"diagram render without it."
        )
    unknown = set(node) - _KNOWN[kind] - {"type", "name", "children"}
    if unknown:
        raise SceneError(
            f"{kind!r} ({node.get('name')}) carries {sorted(unknown)}, which this emitter does not "
            f"implement. A dropped property renders a diagram that looks finished and is wrong."
        )
    return kind


def _at_frame(artboard: dict[str, Any], frame: int) -> dict[str, dict[str, Any]]:
    """Animated property values at `frame`, keyed by object name then property.

    The still is the reduced-motion fallback, so it has to be the scene as the loop starts rather
    than the scene with every animated property at its authored value. In `linked_parameters` those
    are not the same picture: the ticker cross-fade stacks two text runs at one position, and a
    still that ignored opacity would render both on top of each other.

    Only keyframes at or before `frame` apply — a track that starts later has not begun, so the
    authored value stands. No interpolation: frame 0 is always a keyframe boundary or nothing.
    """
    animations = artboard.get("animations") or []
    if len(animations) > 1:
        raise SceneError(
            f"{len(animations)} animations on one artboard; which drives the still is ambiguous"
        )
    out: dict[str, dict[str, Any]] = {}
    for track in animations[0].get("keyframes", []) if animations else []:
        prop = track["property"]
        if prop not in _ANIMATABLE:
            raise SceneError(
                f"{track['object']}.{prop} is animated and this emitter cannot resolve it into a "
                f"still. Implement it rather than exporting a still of the wrong picture."
            )
        applicable = [kf for kf in track["frames"] if kf["frame"] <= frame]
        if applicable:
            out.setdefault(track["object"], {})[prop] = max(applicable, key=lambda kf: kf["frame"])[
                "value"
            ]
    return out


def _num(value: float) -> str:
    """Trim float noise. 3 decimals is well below a pixel at these artboard sizes."""
    rounded = round(float(value), 3)
    return str(int(rounded)) if rounded == int(rounded) else str(rounded)


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _colour_of(node: dict[str, Any], over: dict[str, dict[str, Any]]) -> str:
    """The `solid_color` inside a fill or stroke. Anything else is refused: a gradient would need a
    `<defs>` entry and a reference, and no scene has one yet."""
    children = node.get("children") or []
    if len(children) != 1:
        raise SceneError(
            f"{node.get('name')}: expected exactly one paint child, got {len(children)}"
        )
    child = children[0]
    if _check(child) != "solid_color":
        raise SceneError(f"{node.get('name')}: only solid_color paint is supported")
    colour = over.get(str(child.get("name")), {}).get("color", child.get("color"))
    if not isinstance(colour, str) or not colour.startswith("#"):
        raise SceneError(f"{child.get('name')}: colour must be a hex string, got {colour!r}")
    return colour


def _paint_attrs(children: list[dict[str, Any]], over: dict[str, dict[str, Any]]) -> str:
    """Fill and stroke for one shape, as SVG attributes.

    In Rive these are siblings of the geometry inside the shape rather than properties of it, which
    is why they are gathered here and pushed down onto the emitted element.
    """
    fill = "none"
    stroke = ""
    for child in children:
        kind = _check(child)
        if kind == "fill":
            fill = _colour_of(child, over)
        elif kind == "stroke":
            colour = _colour_of(child, over)
            thickness = child.get("thickness", 1)
            stroke = f' stroke="{colour}" stroke-width="{_num(thickness)}"'
    return f' fill="{fill}"{stroke}'


def _geometry_svg(node: dict[str, Any], paint: str) -> str:
    kind = _check(node)
    width = float(node["width"])
    height = float(node["height"])
    # Origin is a fraction of the box, defaulting to its centre — the convention every helper in
    # authoring.py uses. Left/top are relative to the parent shape's own origin.
    left = -width * float(node.get("origin_x", 0.5))
    top = -height * float(node.get("origin_y", 0.5))

    if kind == "rectangle":
        radius = float(node.get("corner_radius", 0) or 0)
        rx = f' rx="{_num(radius)}"' if radius else ""
        return (
            f'<rect x="{_num(left)}" y="{_num(top)}" width="{_num(width)}" '
            f'height="{_num(height)}"{rx}{paint}/>'
        )
    if kind == "ellipse":
        return (
            f'<ellipse cx="{_num(left + width / 2)}" cy="{_num(top + height / 2)}" '
            f'rx="{_num(width / 2)}" ry="{_num(height / 2)}"{paint}/>'
        )
    # Triangle: points up, which is the default the arrow helpers rotate away from.
    apex = f"{_num(left + width / 2)},{_num(top)}"
    right = f"{_num(left + width)},{_num(top + height)}"
    bottom_left = f"{_num(left)},{_num(top + height)}"
    return f'<polygon points="{apex} {right} {bottom_left}"{paint}/>'


def _shape_svg(node: dict[str, Any], over: dict[str, dict[str, Any]]) -> str:
    children = node.get("children") or []
    geometry = [c for c in children if c.get("type") in _GEOMETRY]
    if len(geometry) != 1:
        raise SceneError(
            f"shape {node.get('name')}: expected one geometry child, got {len(geometry)}"
        )
    paint = _paint_attrs([c for c in children if c.get("type") not in _GEOMETRY], over)
    body = _geometry_svg(geometry[0], paint)

    mine = over.get(str(node.get("name")), {})
    transform = f"translate({_num(node.get('x', 0))},{_num(node.get('y', 0))})"
    rotation = float(node.get("rotation", 0) or 0)
    if rotation:
        # The spec carries radians; SVG rotate() is degrees.
        transform += f" rotate({_num(math.degrees(rotation))})"
    scale_x, scale_y = mine.get("scale_x", 1.0), mine.get("scale_y", 1.0)
    if (scale_x, scale_y) != (1.0, 1.0):
        transform += f" scale({_num(scale_x)},{_num(scale_y)})"
    return f'<g transform="{transform}"{_opacity_attr(mine)}>{body}</g>'


def _opacity_attr(overrides: dict[str, Any]) -> str:
    opacity = overrides.get("opacity")
    return "" if opacity is None or float(opacity) == 1.0 else f' opacity="{_num(opacity)}"'


def _text_svg(node: dict[str, Any], over: dict[str, dict[str, Any]]) -> str:
    children = node.get("children") or []
    styles = {c.get("name"): c for c in children if c.get("type") == "text_style"}
    runs = [c for c in children if c.get("type") == "text_value_run"]
    for child in children:
        _check(child)
    if len(runs) != 1:
        raise SceneError(f"text {node.get('name')}: expected one value run, got {len(runs)}")
    run = runs[0]
    style = styles.get(run.get("style"))
    if style is None:
        raise SceneError(f"text run {run.get('name')}: no style named {run.get('style')!r}")

    content = run.get("text")
    if not isinstance(content, str):
        raise SceneError(f"text run {run.get('name')}: text must be a string")
    if "\n" in content:
        # Faithful multi-line needs tspans with an explicit line height, and no scene has one.
        raise SceneError(f"text run {run.get('name')}: multi-line text is not implemented")

    colour = _colour_of(
        next(c for c in style.get("children") or [] if c.get("type") == "fill"), over
    )
    spacing = style.get("letter_spacing")
    spacing_attr = f' letter-spacing="{_num(spacing)}"' if spacing is not None else ""

    # origin 0.5/0.5 is the authoring convention: x,y is the centre of the run in both axes.
    anchor = {0.0: "start", 0.5: "middle", 1.0: "end"}.get(float(node.get("origin_x", 0.5)))
    if anchor is None:
        raise SceneError(f"text {node.get('name')}: only 0, 0.5 and 1 origin_x are mapped")
    baseline = "central" if float(node.get("origin_y", 0.5)) == 0.5 else "auto"

    return (
        f'<text x="{_num(node.get("x", 0))}" y="{_num(node.get("y", 0))}" '
        f'font-family="{FONT_FAMILY}" font-weight="{FONT_WEIGHT}" '
        f'font-size="{_num(style["font_size"])}"{spacing_attr} fill="{colour}" '
        f'text-anchor="{anchor}" dominant-baseline="{baseline}"'
        f"{_opacity_attr(over.get(str(node.get('name')), {}))}>{_escape(content)}</text>"
    )


def _node_svg(node: dict[str, Any], over: dict[str, dict[str, Any]]) -> str | None:
    kind = _check(node)
    if kind == "font_asset":
        return None  # The page supplies the font; there is nothing to draw.
    if kind == "shape":
        return _shape_svg(node, over)
    if kind == "text":
        return _text_svg(node, over)
    raise SceneError(f"{kind!r} is not valid as an artboard child")


def scene_svg_parts(spec: dict[str, Any], *, frame: int = 0) -> list[str]:
    """The SVG as a list of pieces: the open tag, one entry per drawn element, the close tag.

    Split rather than joined because the generated content module writes one element per line, so a
    diagram edit shows up in review as the shapes that changed rather than as one re-flowed
    5KB line.
    """
    artboard = spec.get("artboard")
    if not isinstance(artboard, dict):
        raise SceneError("Scene has no artboard")
    width = float(artboard["width"])
    height = float(artboard["height"])
    over = _at_frame(artboard, frame)

    children = artboard.get("children") or []
    # Rive paints the first sibling on top; SVG paints the last. See rule 1 in the module docstring.
    parts = [svg for svg in (_node_svg(c, over) for c in reversed(children)) if svg is not None]

    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {_num(width)} {_num(height)}" '
        f'width="{_num(width)}" height="{_num(height)}">',
        *parts,
        "</svg>",
    ]


def scene_to_svg(spec: dict[str, Any], *, frame: int = 0) -> str:
    """One SceneSpec dict to one SVG document string, as the scene stands at `frame`."""
    return "".join(scene_svg_parts(spec, frame=frame))


def export(scene_path: Path, out_path: Path) -> Path:
    spec = json.loads(scene_path.read_text())
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(scene_to_svg(spec) + "\n")
    return out_path


# Where the SVG lives once exported. It is a Python module rather than a directory of `.svg` files
# read at import time, for the reason `LessonAsset` gives: a published `CourseVersion` is an
# immutable snapshot, so the content has to BE the string rather than point at a file that could
# change or fail to ship in a wheel. `tests/test_course_diagrams.py` regenerates and compares, so
# the module cannot drift from the scenes it came from.
CONTENT_DIR = Path(__file__).resolve().parents[2] / "src/grassmarket/workbench/content"

# The proper name of each course, for the generated module's docstring. A course with no entry is
# refused rather than given a title guessed from its directory name: these modules are read by
# people, and "Sales_ops_playbook course diagrams" is the kind of detail that says nobody looked.
COURSE_TITLES: dict[str, str] = {
    "openbb": "OpenBB",
    "benzinga": "Benzinga",
    "brandfetch": "Brandfetch",
    "sales_ops": "Sales Operations Playbook",
    "sales_egoist": "The Sales Egoist",
}


def content_module_path(course: str) -> Path:
    """The generated module for one course's diagrams."""
    return CONTENT_DIR / f"{course}_diagrams.py"


def _header(course: str) -> str:
    """The generated module's docstring. Names the course, its scene directory and its slides
    module, so the file says where to make a change rather than only where not to."""
    if course not in COURSE_TITLES:
        raise KeyError(
            f"No display title registered for course {course!r}. Add it to COURSE_TITLES — a "
            "generated module nobody can read is not a generated module."
        )
    title = COURSE_TITLES[course]
    return f'''"""{title} course diagrams as inline SVG (GRS-0225). GENERATED — DO NOT EDIT.

Regenerate with `uv run python design/motion/svg_export.py`. The source is the SceneSpec JSON under
`design/motion/courses/{course}/`; edit that, not this. `tests/test_course_diagrams.py` fails if
this file and those scenes disagree.

Captions and alt text are NOT here: they are authored prose and live beside the slide they explain,
in `{course}_slides.py`. Only the drawing is generated.
"""

from __future__ import annotations

SVG: dict[str, str] = {{
'''


def _literal(text: str) -> str:
    """A Python string literal quoted the way `ruff format` would quote it.

    Ruff's rule is whichever quote character needs fewer escapes, with double quotes winning ties.
    That matters here because an SVG element is full of `"` and occasionally contains an
    apostrophe. Matching the rule is what keeps the generated file format-clean, so CI does not
    fail every time the diagrams are regenerated.
    """
    if any(ord(c) < 0x20 for c in text) or "\\" in text:
        # Control characters or backslashes need real escaping; hand that to the library and
        # accept whatever quoting it picks.
        return json.dumps(text)
    if text.count('"') > text.count("'"):
        return "'" + text.replace("'", "\\'") + "'"
    return '"' + text.replace('"', '\\"') + '"'


def scene_dir(course: str) -> Path:
    return Path(__file__).parent / "courses" / course


def courses() -> list[str]:
    """Every course with at least one authored scene, in a stable order."""
    return sorted(p.name for p in (Path(__file__).parent / "courses").iterdir() if p.is_dir())


def write_content_module(course: str) -> Path:
    """Write the generated SVG constants one course's content imports."""
    entries = []
    for scene in sorted(scene_dir(course).glob("*.json")):
        parts = scene_svg_parts(json.loads(scene.read_text()))
        # Implicit concatenation joins the lines with no separator, so the string at runtime is
        # byte-for-byte the document `export()` writes.
        lines = "\n".join(f"        {_literal(part)}" for part in parts)
        entries.append(f'    "{scene.stem}": (\n{lines}\n    ),\n')
    out = content_module_path(course)
    out.write_text(_header(course) + "".join(entries) + "}\n")
    return out


def main() -> None:
    here = Path(__file__).parent
    total = 0
    for course in courses():
        count = 0
        for scene in sorted(scene_dir(course).glob("*.json")):
            out = export(scene, here / "build" / course / f"{scene.stem}.svg")
            print(f"{course}/{scene.stem}  {out.stat().st_size:>6} bytes")
            count += 1
        module = write_content_module(course)
        rel = module.relative_to(Path.cwd()) if module.is_relative_to(Path.cwd()) else module
        print(f"  {count} diagram(s) → {rel}")
        total += count
    print(f"{total} diagrams exported across {len(courses())} course(s).")


if __name__ == "__main__":
    main()
