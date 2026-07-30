"""The course diagrams and the SVG export (GRS-0225).

What this suite can and cannot prove is worth being precise about, because the last round of
diagram work shipped a check that passed on a broken render.

It **can** prove that every committed scene exports, that the generated content module has not
drifted from the scenes it came from, that the SVG only uses constructs the frontend sanitiser
accepts, and that the emitter refuses input it would otherwise render wrongly.

It **cannot** prove the drawing is right. Compiling with `rive-cli` and comparing the two renders
pixel-region by pixel-region needs a Rust toolchain and headless Chromium, neither of which is in
CI; `design/motion/render.sh` and the procedure in `design/motion/README.md` are that gate, run
locally. The committed stills exist so a human can see a wrong drawing in review.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from grassmarket.workbench.content.openbb_slides import rebuilt_sections

ROOT = Path(__file__).resolve().parents[1]
COURSES_DIR = ROOT / "design/motion/courses"

# Every course with authored scenes, discovered rather than listed: a second course whose diagrams
# nothing checked would be exactly the drift this suite exists to catch. GRS-0217 adds Benzinga.
COURSE_NAMES = sorted(p.name for p in COURSES_DIR.iterdir() if p.is_dir())


def _svg_for(course: str) -> dict[str, str]:
    """The generated `SVG` dict for one course, imported by name."""
    module = importlib.import_module(f"grassmarket.workbench.content.{course}_diagrams")
    return module.SVG


# (course, scene path) for every authored diagram in the repo.
SCENES = [
    (course, scene)
    for course in COURSE_NAMES
    for scene in sorted((COURSES_DIR / course).glob("*.json"))
]


def _build_dir(course: str) -> Path:
    return ROOT / "design/motion/build" / course


def _svg_export():
    """Import the emitter by path: `design/` is not a package, deliberately — it is authoring
    tooling that the application must never import."""
    spec = importlib.util.spec_from_file_location(
        "svg_export", ROOT / "design/motion/svg_export.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


svg_export = _svg_export()


def test_there_are_scenes_to_check() -> None:
    """A glob that silently matched nothing would make every test below vacuously pass."""
    assert len(SCENES) >= 9
    assert COURSE_NAMES, "no course scene directories found at all"


@pytest.mark.parametrize(("course", "scene"), SCENES, ids=lambda v: getattr(v, "stem", v))
def test_every_scene_exports(course: str, scene: Path) -> None:
    svg = svg_export.scene_to_svg(json.loads(scene.read_text()))
    assert svg.startswith('<svg xmlns="http://www.w3.org/2000/svg"')
    assert svg.endswith("</svg>")
    # A scene that emitted only its wrapper drew nothing at all.
    assert svg.count("<") > 10


@pytest.mark.parametrize(("course", "scene"), SCENES, ids=lambda v: getattr(v, "stem", v))
def test_the_generated_module_has_not_drifted(course: str, scene: Path) -> None:
    """The content module is generated, so the failure mode is editing a scene and shipping the old
    drawing. Regenerate with `uv run python design/motion/svg_export.py`."""
    svg = _svg_for(course)
    assert scene.stem in svg, f"{scene.stem} has no entry in {course}_diagrams.SVG"
    assert svg[scene.stem] == svg_export.scene_to_svg(json.loads(scene.read_text()))


@pytest.mark.parametrize(("course", "scene"), SCENES, ids=lambda v: getattr(v, "stem", v))
def test_the_committed_svg_matches_too(course: str, scene: Path) -> None:
    committed = _build_dir(course) / f"{scene.stem}.svg"
    assert committed.exists(), f"{committed} is missing; run design/motion/svg_export.py"
    assert committed.read_text().strip() == _svg_for(course)[scene.stem]


@pytest.mark.parametrize(("course", "scene"), SCENES, ids=lambda v: getattr(v, "stem", v))
def test_the_riv_and_the_still_are_committed_beside_the_source(course: str, scene: Path) -> None:
    """A binary whose source is not beside it is not reviewable, and a diagram with no still cannot
    be checked by eye in a PR."""
    build = _build_dir(course)
    assert (build / f"{scene.stem}.riv").exists()
    assert (build / scene.stem / "frame_00000.png").exists()


# --- The sanitiser's allowlist -------------------------------------------------------------
#
# The frontend refuses a whole diagram rather than stripping part of it, so an SVG using anything
# outside `frontend/lib/svg.ts` renders as an error message instead of a drawing. These mirror that
# allowlist for the constructs the emitter can actually produce; `LessonBody.test.tsx` is where the
# sanitiser itself is tested.

_ALLOWED_ELEMENTS = {"svg", "g", "rect", "polygon", "ellipse", "text"}
_ALLOWED_ATTRIBUTES = {
    "xmlns",
    "viewBox",
    "width",
    "height",
    "x",
    "y",
    "rx",
    "cx",
    "cy",
    "ry",
    "points",
    "transform",
    "fill",
    "stroke",
    "stroke-width",
    "opacity",
    "font-size",
    "font-family",
    "font-weight",
    "letter-spacing",
    "text-anchor",
    "dominant-baseline",
}


@pytest.mark.parametrize(("course", "scene"), SCENES, ids=lambda v: getattr(v, "stem", v))
def test_the_svg_only_uses_constructs_the_sanitiser_accepts(course: str, scene: Path) -> None:
    import re

    name = scene.stem
    svg = _svg_for(course)[name]
    elements = set(re.findall(r"<\s*/?\s*([a-zA-Z][a-zA-Z0-9-]*)", svg))
    assert elements <= _ALLOWED_ELEMENTS, f"{name}: {elements - _ALLOWED_ELEMENTS}"

    attributes = set(re.findall(r'([a-zA-Z][-a-zA-Z0-9]*)\s*=\s*"', svg))
    assert attributes <= _ALLOWED_ATTRIBUTES, f"{name}: {attributes - _ALLOWED_ATTRIBUTES}"

    # Every one of these is refused outright by the sanitiser, and each has been a real SVG attack.
    assert "<script" not in svg.lower()
    assert "url(" not in svg
    assert "href" not in svg
    assert "<!--" not in svg


# --- Fail loud rather than draw the wrong thing ---------------------------------------------


def _minimal_scene(children: list[dict]) -> dict:
    return {
        "scene_format_version": 1,
        "artboard": {"name": "T", "width": 10, "height": 10, "children": children},
    }


def test_an_unknown_node_type_is_refused() -> None:
    """Not skipped. A node the emitter does not understand means the drawing is incomplete, and an
    incomplete drawing that renders looks finished."""
    with pytest.raises(svg_export.SceneError, match="no SVG mapping"):
        svg_export.scene_to_svg(_minimal_scene([{"type": "image", "name": "X"}]))


def test_an_unknown_property_on_a_known_type_is_refused() -> None:
    with pytest.raises(svg_export.SceneError, match="does not"):
        svg_export.scene_to_svg(
            _minimal_scene(
                [
                    {
                        "type": "shape",
                        "name": "S",
                        "x": 5,
                        "y": 5,
                        "blend_mode": "multiply",
                        "children": [
                            {"type": "rectangle", "name": "R", "width": 4, "height": 4},
                            {
                                "type": "fill",
                                "name": "F",
                                "children": [
                                    {"type": "solid_color", "name": "C", "color": "#1A3B26"}
                                ],
                            },
                        ],
                    }
                ]
            )
        )


def test_an_animated_property_the_emitter_cannot_resolve_is_refused() -> None:
    """A keyframed rotation would silently export a still of the wrong picture."""
    scene = _minimal_scene([])
    scene["artboard"]["animations"] = [
        {
            "name": "spin",
            "fps": 60,
            "duration": 60,
            "keyframes": [
                {"object": "S", "property": "rotation", "frames": [{"frame": 0, "value": 0}]}
            ],
        }
    ]
    with pytest.raises(svg_export.SceneError, match="cannot resolve it into a"):
        svg_export.scene_to_svg(scene)


def test_multi_line_text_is_refused_rather_than_run_together() -> None:
    with pytest.raises(svg_export.SceneError, match="multi-line"):
        svg_export.scene_to_svg(
            _minimal_scene(
                [
                    {
                        "type": "text",
                        "name": "T",
                        "x": 5,
                        "y": 5,
                        "children": [
                            {
                                "type": "text_style",
                                "name": "TS",
                                "font_size": 10,
                                "children": [
                                    {
                                        "type": "fill",
                                        "name": "TF",
                                        "children": [
                                            {
                                                "type": "solid_color",
                                                "name": "TC",
                                                "color": "#1A1A18",
                                            }
                                        ],
                                    }
                                ],
                            },
                            {
                                "type": "text_value_run",
                                "name": "TR",
                                "style": "TS",
                                "text": "one\ntwo",
                            },
                        ],
                    }
                ]
            )
        )


# --- Only characters the vendored font can actually draw -------------------------------------

# `design/motion/assets/fonts/Inter-Bold-Subset.ttf` is a 95-glyph subset: printable ASCII and
# nothing else. Verified against its cmap, not assumed. This matters because a character outside
# the subset does not fail, warn or fall back — Rive draws nothing at all and leaves a gap the
# width of a space. GRS-0217 shipped exactly that: an em dash in a diagram footer that read
# correctly in the source, passed every structural check, and rendered as a hole.
_FONT_SUBSET = frozenset(chr(c) for c in range(32, 127))


@pytest.mark.parametrize(("course", "scene"), SCENES, ids=lambda v: getattr(v, "stem", v))
def test_every_character_is_in_the_vendored_font_subset(course: str, scene: Path) -> None:
    spec = json.loads(scene.read_text())
    offenders: dict[str, str] = {}

    def walk(node: object) -> None:
        if isinstance(node, dict):
            if node.get("type") == "text_value_run":
                body = str(node.get("text", ""))
                missing = "".join(sorted({c for c in body if c not in _FONT_SUBSET}))
                if missing:
                    offenders[body] = missing
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(spec)
    assert not offenders, (
        f"{scene.stem}: these strings use characters the font subset cannot draw, so they render "
        f"as blank gaps: {offenders}. Use ASCII, or extend the subset deliberately."
    )


def test_the_font_subset_really_is_ascii_only() -> None:
    """The rule above is only worth anything if the premise holds. If the vendored font is ever
    re-subset with a wider range, this fails and says to widen `_FONT_SUBSET` — rather than the
    check silently becoming stricter than the font."""
    try:
        from fontTools.ttLib import TTFont
    except ImportError:  # pragma: no cover - fontTools is a dev dependency
        pytest.skip("fontTools not installed")

    font = TTFont(ROOT / "design/motion/assets/fonts/Inter-Bold-Subset.ttf")
    covered = set()
    for table in font["cmap"].tables:
        covered |= set(table.cmap)
    printable = {c for c in covered if c >= 32}
    assert {chr(c) for c in printable} == _FONT_SUBSET, (
        "the vendored font's coverage no longer matches _FONT_SUBSET; update the constant"
    )


# --- Nothing off the edge of the artboard ---------------------------------------------------


@pytest.mark.parametrize(("course", "scene"), SCENES, ids=lambda v: getattr(v, "stem", v))
def test_nothing_is_drawn_outside_the_artboard(course: str, scene: Path) -> None:
    """GRS-0225 shipped a diagram whose right-hand box ran off the artboard and into its
    neighbour, and the non-blank render check passed it happily. "It rendered" is not "it is
    right", so this is the cheap structural half of that gate: every rectangle must lie inside the
    viewBox. Text is checked separately and only approximately, because exact metrics need a font
    engine."""
    import re

    svg = _svg_for(course)[scene.stem]
    box = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg)
    assert box, f"{scene.stem} has no viewBox"
    width, height = float(box.group(1)), float(box.group(2))

    groups = re.finditer(
        r'<g transform="translate\(([-\d.]+),([-\d.]+)\)[^"]*">(.*?)</g>', svg, re.S
    )
    seen = 0
    for group in groups:
        gx, gy, inner = float(group.group(1)), float(group.group(2)), group.group(3)
        for rect in re.finditer(
            r'<rect x="([-\d.]+)" y="([-\d.]+)" width="([\d.]+)" height="([\d.]+)"', inner
        ):
            seen += 1
            x0, y0 = gx + float(rect.group(1)), gy + float(rect.group(2))
            x1, y1 = x0 + float(rect.group(3)), y0 + float(rect.group(4))
            assert x0 >= -0.5 and y0 >= -0.5, f"{scene.stem}: rect starts off-artboard at {x0},{y0}"
            assert x1 <= width + 0.5, f"{scene.stem}: rect right edge {x1} exceeds {width}"
            assert y1 <= height + 0.5, f"{scene.stem}: rect bottom edge {y1} exceeds {height}"
    # Every scene has at least a background card, so zero rects means the regex stopped matching
    # the emitter's output and this test has quietly become a no-op.
    assert seen, f"{scene.stem}: no rectangles found — the bounds check is not looking at anything"


@pytest.mark.parametrize(("course", "scene"), SCENES, ids=lambda v: getattr(v, "stem", v))
def test_no_text_is_estimated_to_overflow_the_artboard(course: str, scene: Path) -> None:
    """Approximate by design. Rive and the browser both lay text out themselves, so the exact
    width is not knowable here; what is knowable is whether a centred string is so long that no
    plausible metric keeps it on the artboard. That is the failure worth catching automatically —
    a caption written two words too long, which reads fine in the source and clips in the render."""
    import re

    svg = _svg_for(course)[scene.stem]
    box = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg)
    assert box
    width = float(box.group(1))

    for group in re.finditer(
        r'<g transform="translate\(([-\d.]+),([-\d.]+)\)[^"]*">(.*?)</g>', svg, re.S
    ):
        gx, inner = float(group.group(1)), group.group(3)
        for node in re.finditer(r'<text[^>]*font-size="([\d.]+)"[^>]*>(.*?)</text>', inner, re.S):
            size = float(node.group(1))
            content = re.sub(r"<[^>]+>", "", node.group(2))
            # ~0.56em is a generous average advance for Inter Bold across mixed-case text.
            half = 0.56 * size * len(content) / 2
            assert gx - half >= -2, f"{scene.stem}: {content[:40]!r} overflows the left edge"
            assert gx + half <= width + 2, (
                f"{scene.stem}: {content[:40]!r} overflows the right edge"
            )


# --- The two rules that are silent when you get them wrong ----------------------------------


def test_paint_order_is_inverted_so_the_background_ends_up_at_the_back() -> None:
    """Rive paints the FIRST declared sibling on top; SVG paints the LAST. Every scene declares its
    background card last, so an emitter that did not invert would produce one flat rectangle of
    paper — and would still render, validate and look like nothing had broken."""
    for course, path in SCENES:
        name, scene = path.stem, json.loads(path.read_text())
        children = [c for c in scene["artboard"]["children"] if c["type"] != "font_asset"]
        assert children[-1]["name"] == "Bg", f"{name} does not end with its background"
        svg = _svg_for(course)[name]
        # The background is the first thing drawn in the SVG, immediately after the root tag.
        first_element = svg.index("<g", 1)
        assert svg.index('fill="#F7F5EF"') < svg.index("<text"), name
        assert first_element < svg.index("<text"), name


def test_the_still_is_the_animation_at_frame_zero_not_the_authored_values() -> None:
    """`linked_parameters` cross-fades two text runs stacked at one position. A still that ignored
    opacity would draw both on top of each other, which is a legible diagram turning into mush and
    exactly what the first export did."""
    scene = json.loads((ROOT / "design/motion/courses/openbb/linked_parameters.json").read_text())
    tracks = {
        (k["object"], k["property"]): k["frames"]
        for k in scene["artboard"]["animations"][0]["keyframes"]
    }
    assert tracks[("FieldValueA", "opacity")][0]["value"] == 1.0
    assert tracks[("FieldValueB", "opacity")][0]["value"] == 0.0

    svg = _svg_for("openbb")["linked_parameters"]
    # Exactly one of the two stacked runs is hidden, and it is the one frame 0 says is hidden.
    assert svg.count('opacity="0"') == 1
    hidden = svg[svg.index('opacity="0"') : svg.index("</text>", svg.index('opacity="0"'))]
    assert "NDAQ" in hidden and "LSEG" not in hidden


# --- The diagrams are actually in the course ------------------------------------------------


def test_every_openbb_section_carries_at_least_one_diagram() -> None:
    """The depth standard enforces this for any course; this is the one that would have caught the
    original gap, where nine diagrams existed on disk and no advisor could see one."""
    for module in rebuilt_sections():
        for lesson in module.lessons:
            assets = [s.asset for s in lesson.slides if s.asset]
            assert assets, f"{module.title}: no diagram on any slide"


def test_every_diagram_in_the_course_is_a_real_generated_one() -> None:
    """A hand-written SVG pasted into the content would not be regenerable, and would drift the
    moment the scene changed."""
    known = set(_svg_for("openbb").values())
    for module in rebuilt_sections():
        for lesson in module.lessons:
            for slide in lesson.slides:
                if slide.asset:
                    assert slide.asset.svg in known, f"{slide.title}: SVG is not from a scene"


def test_every_scene_is_used_by_the_course() -> None:
    """An authored diagram nobody sees is the failure this ticket exists to fix, one level up."""
    used = {
        slide.asset.svg
        for module in rebuilt_sections()
        for lesson in module.lessons
        for slide in lesson.slides
        if slide.asset
    }
    unused = sorted(name for name, svg in _svg_for("openbb").items() if svg not in used)
    assert not unused, f"authored but not on any slide: {unused}"
