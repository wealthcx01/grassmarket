"""Build the OpenBB course diagrams (GRS-0225, GRS-0216).

    uv run python design/motion/courses/openbb/build.py

Writes one JSON scene per diagram. Compiling and rendering is `design/motion/render.sh`, which
runs rive-cli over every scene here and refuses a blank frame.

Each diagram exists because the idea it carries is spatial rather than verbal. If a diagram could
be replaced by its own caption without loss, it should not be here.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from authoring import (  # noqa: E402
    GREEN,
    GREEN_TINT,
    INK,
    MUTED,
    ON_GREEN,
    ON_GREEN_MUTED,
    PAPER,
    RULE,
    SIGNAL,
    WARN,
    arrow_down,
    arrow_right,
    card,
    line,
    scene,
    stack,
    text,
    write,
)

HERE = Path(__file__).resolve().parent


# --- 1. Two products, one company (section 1) ---------------------------------------------


def two_products() -> dict:
    return scene(
        "TwoProducts",
        960,
        420,
        stack(
            text("Title", 480, 46, "OpenBB sells two things", 30, INK),
            text("LeftName", 256, 150, "Open Data Platform", 22, ON_GREEN),
            text("LeftKind", 256, 186, "open source, AGPLv3", 16, ON_GREEN_MUTED),
            text("LeftWho", 256, 244, "a quant, in code", 16, ON_GREEN_MUTED),
            text("LeftCmd", 256, 280, "pip install openbb", 16, SIGNAL),
            text("RightName", 704, 150, "OpenBB Workspace", 22, INK),
            text("RightKind", 704, 186, "commercial, in the browser", 16, MUTED),
            text("RightWho", 704, 244, "an investment team", 16, MUTED),
            text("RightCmd", 704, 280, "pro.openbb.co", 16, GREEN),
            text(
                "Foot",
                480,
                372,
                "Almost every commission conversation is about the right-hand box.",
                17,
                MUTED,
            ),
            card("LeftCard", 256, 220, 380, 210, GREEN),
            card("RightCard", 704, 220, 380, 210, PAPER, stroke=RULE),
            card("Bg", 480, 210, 960, 420, PAPER, radius=0),
        ),
    )


# --- 2. The AGPL decision (section 6) ------------------------------------------------------


def agpl_decision() -> dict:
    """The highest-value drawing in the course, because it is the one an advisor gets wrong under
    pressure. Two questions, three endings. The shape of it is the teaching: only the bottom-right
    path needs a commercial conversation, and an advisor who knows that stops over-promising and
    stops panicking.

    Laid out on a 1120-wide artboard so the right-hand ending clears the edge with a real margin.
    The first version of this ran the box off the artboard and into its neighbour, which the
    non-blank check happily passed — a reminder that "it rendered" is not "it is right"."""
    return scene(
        "AgplDecision",
        1120,
        640,
        stack(
            text("Title", 560, 46, "Can the client build on the open-source platform?", 28, INK),
            text(
                "Sub",
                560,
                82,
                "The Open Data Platform is AGPLv3. Two questions decide the answer.",
                16,
                MUTED,
            ),
            # Question 1
            text("Q1", 560, 158, "Are they MODIFYING the platform?", 20, INK),
            text("Q1No", 214, 218, "No", 15, MUTED),
            text("Q1Yes", 890, 218, "Yes", 15, MUTED),
            # Left ending
            text("EndA1", 200, 306, "Using it as published", 18, GREEN),
            text("EndA2", 200, 338, "No AGPL obligation to", 15, MUTED),
            text("EndA3", 200, 360, "publish anything.", 15, MUTED),
            # Question 2
            text("Q2", 780, 312, "Are they SERVING it to others", 18, INK),
            text("Q2b", 780, 338, "over a network?", 18, INK),
            text("Q2No", 616, 402, "No", 15, MUTED),
            text("Q2Yes", 952, 402, "Yes", 15, MUTED),
            # Middle ending
            text("EndB1", 640, 480, "Internal use only", 17, GREEN),
            text("EndB2", 640, 510, "Modify freely. The network", 14, MUTED),
            text("EndB3", 640, 530, "clause is not triggered.", 14, MUTED),
            # Right ending — the one that matters
            text("EndC1", 940, 480, "Source disclosure bites", 17, ON_GREEN),
            text("EndC2", 940, 510, "This is what a commercial", 14, ON_GREEN_MUTED),
            text("EndC3", 940, 530, "arrangement is for.", 14, ON_GREEN_MUTED),
            text(
                "Rule",
                560,
                602,
                "Name the licence. Say the commercial route exists. Never advise on it yourself.",
                16,
                WARN,
            ),
            # Boxes
            card("Q1Box", 560, 158, 470, 58, PAPER, stroke=INK, thickness=2),
            card("Q2Box", 780, 324, 420, 80, PAPER, stroke=INK, thickness=2),
            card("EndABox", 200, 336, 320, 118, GREEN_TINT, stroke=RULE),
            card("EndBBox", 640, 508, 270, 118, GREEN_TINT, stroke=RULE),
            card("EndCBox", 940, 508, 290, 118, GREEN),
            # Connectors. The stem into a split line carries NO head: an arrowhead landing on a
            # horizontal rule reads as a third branch that does not exist.
            line("A1", 560, 208, 2.5, 34, MUTED),
            line("Split", 560, 226, 690, 2.5, MUTED),
            arrow_down("A2", 215, 252, 44, MUTED),
            arrow_down("A3", 905, 252, 38, MUTED),
            line("B1", 780, 382, 2.5, 26, MUTED),
            line("Split2", 780, 396, 300, 2.5, MUTED),
            arrow_down("B2", 630, 424, 36, MUTED),
            arrow_down("B3", 930, 424, 36, MUTED),
            card("Bg", 560, 320, 1120, 640, PAPER, radius=0),
        ),
    )


# --- 3. Widget anatomy (section 3) ---------------------------------------------------------


def widget_anatomy() -> dict:
    """Four labelled parts of one object. An advisor who knows these four can follow any demo and
    can answer the compliance question, because source attribution lives in the metadata layer."""
    rows = [
        ("Data source", "a feed, a database, their own data, a static file", 178),
        ("Metadata layer", "title, category, and the source attribution", 248),
        ("Visual layer", "table, chart, PDF, or a custom view", 318),
        ("Parameters", "the interactive part: ticker, date range", 388),
    ]
    labels: list[dict] = []
    boxes: list[dict] = []
    for i, (name, detail, y) in enumerate(rows):
        labels.append(text(f"R{i}Name", 300, y - 11, name, 19, INK))
        labels.append(text(f"R{i}Detail", 300, y + 15, detail, 15, MUTED))
        boxes.append(card(f"R{i}Box", 300, y, 470, 58, PAPER, stroke=RULE))
    return scene(
        "WidgetAnatomy",
        960,
        500,
        stack(
            text("Title", 480, 44, "What a widget is made of", 30, INK),
            text(
                "Sub",
                480,
                78,
                "OpenBB calls it a data container built to answer one analytical question.",
                16,
                MUTED,
            ),
            *labels,
            text("Callout1", 730, 250, "This is your answer", 17, ON_GREEN),
            text("Callout2", 730, 278, "when compliance asks", 15, ON_GREEN_MUTED),
            text("Callout3", 730, 300, "where a number came from.", 15, ON_GREEN_MUTED),
            *boxes,
            card("Callout", 730, 276, 300, 108, GREEN),
            arrow_right("ToCallout", 545, 248, 60, GREEN),
            card("Bg", 480, 250, 960, 500, PAPER, radius=0),
        ),
    )


# --- 4. Linked parameters (sections 3 and 4) -----------------------------------------------


def linked_parameters() -> dict:
    """The demo the advisor actually gives. One field moves, three widgets follow. This is the one
    worth animating later; as a still it still carries the point."""
    widgets = [
        ("Price chart", 200),
        ("Fundamentals", 480),
        ("News and filings", 760),
    ]
    labels = [text(f"W{i}", x, 372, name, 17, INK) for i, (name, x) in enumerate(widgets)]
    boxes = [
        card(f"W{i}Box", x, 372, 240, 96, PAPER, stroke=RULE) for i, (_, x) in enumerate(widgets)
    ]
    arrows: list[dict] = []
    for i, (_, x) in enumerate(widgets):
        arrows.extend(arrow_down(f"D{i}", x, 288, 46, GREEN))
    return scene(
        "LinkedParameters",
        960,
        470,
        stack(
            text("Title", 480, 44, "One field moves everything", 30, INK),
            text(
                "Sub",
                480,
                78,
                "Widgets that share a parameter name update together. This is the demo.",
                16,
                MUTED,
            ),
            text("FieldLabel", 480, 152, "ticker", 15, ON_GREEN_MUTED),
            text("FieldValue", 480, 186, "LSEG", 30, ON_GREEN),
            *labels,
            *boxes,
            # The stem from the field down to the bus. Its absence in the first render left the
            # ticker box floating, which read as three widgets that happen to be near a box.
            line("Feed", 480, 251, 2.5, 74, GREEN),
            line("Bus", 480, 288, 560, 2.5, GREEN),
            *arrows,
            card("Field", 480, 172, 260, 84, GREEN),
            text(
                "Foot",
                480,
                442,
                "A prospect does not care that you have three widgets. They care about this.",
                16,
                MUTED,
            ),
            card("Bg", 480, 235, 960, 470, PAPER, radius=0),
        ),
    )


# --- 5. Dashboard to app (section 4) -------------------------------------------------------


def dashboard_to_app() -> dict:
    """How one person's good dashboard becomes the desk's standard, which is the answer to "how do
    we roll this out?" — a buying question dressed as a technical one."""
    steps = [
        ("Dashboard", "you configured a blank canvas", 168, PAPER, INK, MUTED, RULE),
        ("Export apps.json", "the configuration, as a file", 480, GREEN_TINT, INK, MUTED, RULE),
        ("App", "curated widgets, an agent, prompts", 792, GREEN, ON_GREEN, ON_GREEN_MUTED, None),
    ]
    labels: list[dict] = []
    boxes: list[dict] = []
    for i, (name, detail, x, fill, fg, sub, stroke) in enumerate(steps):
        labels.append(text(f"S{i}Name", x, 226, name, 20, fg))
        labels.append(text(f"S{i}Detail", x, 258, detail, 14, sub))
        boxes.append(card(f"S{i}Box", x, 240, 268, 130, fill, stroke=stroke))
    return scene(
        "DashboardToApp",
        960,
        420,
        stack(
            text("Title", 480, 44, "From your dashboard to the desk's standard", 28, INK),
            text(
                "Sub",
                480,
                78,
                "One person's work becomes everyone's, without rebuilding it.",
                16,
                MUTED,
            ),
            *labels,
            # Connectors before the boxes: Rive paints the first sibling on top, so an arrow
            # declared after a box has its head hidden by it and reads as a plain line.
            arrow_right("A1", 324, 240, 40, MUTED),
            arrow_right("A2", 636, 240, 40, MUTED),
            *boxes,
            text(
                "Foot",
                480,
                368,
                "Sharing is the commercial hinge. Most business cases lean on it, not on a widget.",
                16,
                MUTED,
            ),
            card("Bg", 480, 210, 960, 420, PAPER, radius=0),
        ),
    )


# --- 6. Segment to trigger (section 7) -----------------------------------------------------


def segment_triggers() -> dict:
    """Five segments, five different irritations. Treating them as one market is the fastest way to
    waste a quarter, so the drawing separates them."""
    rows = [
        ("Retail brokerage", "research cost", "head of research", 150),
        ("Wealth manager", "consistency and supervision", "compliance-adjacent", 214),
        ("Exchange", "product insight on their own feeds", "data product manager", 278),
        ("Bank", "consolidation and AI governance", "the architect", 342),
        ("Information vendor", "distribution, not consumption", "commercial lead", 406),
    ]
    cells: list[dict] = []
    boxes: list[dict] = []
    for i, (segment, trigger, who, y) in enumerate(rows):
        cells.append(text(f"T{i}Seg", 176, y, segment, 17, INK))
        cells.append(text(f"T{i}Trig", 500, y, trigger, 17, GREEN))
        cells.append(text(f"T{i}Who", 806, y, who, 15, MUTED))
        if i % 2 == 0:
            boxes.append(card(f"T{i}Row", 480, y, 880, 52, GREEN_TINT, radius=8))
    return scene(
        "SegmentTriggers",
        960,
        500,
        stack(
            text("Title", 480, 44, "Sell to the trigger, not to the product", 30, INK),
            text("HSeg", 176, 104, "SEGMENT", 13, MUTED, letter_spacing=1.4),
            text("HTrig", 500, 104, "WHAT OPENS IT", 13, MUTED, letter_spacing=1.4),
            text("HWho", 806, 104, "WHO FEELS IT", 13, MUTED, letter_spacing=1.4),
            *cells,
            line("HeadRule", 480, 122, 880, 2, RULE),
            *boxes,
            text(
                "Foot",
                480,
                462,
                "Nobody buys a workspace. They buy the end of one specific irritation.",
                16,
                MUTED,
            ),
            card("Bg", 480, 250, 960, 500, PAPER, radius=0),
        ),
    )


# --- 7. The sale (section 8) ---------------------------------------------------------------


def the_sale() -> dict:
    """Five stages and the good outcome at each. The outcomes are the point: anything vaguer means
    you are one stage behind where you think you are."""
    stages = [
        ("First meeting", "a number\nand a name", 128),
        ("Demo", "a question you\ncould not answer", 304),
        ("Technical", "an introduction\nto the engineer", 480),
        ("Pilot", "a date", 656),
        ("Price", "a scoped quote\nfrom OpenBB", 832),
    ]
    labels: list[dict] = []
    boxes: list[dict] = []
    arrows: list[dict] = []
    for i, (name, outcome, x) in enumerate(stages):
        labels.append(text(f"P{i}Name", x, 170, name, 18, ON_GREEN if i == 3 else INK))
        first, _, second = outcome.partition("\n")
        labels.append(text(f"P{i}O1", x, 226, first, 14, ON_GREEN_MUTED if i == 3 else MUTED))
        if second:
            labels.append(text(f"P{i}O2", x, 246, second, 14, ON_GREEN_MUTED if i == 3 else MUTED))
        boxes.append(
            card(
                f"P{i}Box",
                x,
                206,
                156,
                126,
                GREEN if i == 3 else PAPER,
                stroke=None if i == 3 else RULE,
            )
        )
        if i:
            arrows.extend(arrow_right(f"S{i}", x - 88, 206, 20, MUTED))
    return scene(
        "TheSale",
        960,
        380,
        stack(
            text("Title", 480, 44, "The shape of the sale, and what good looks like", 27, INK),
            text(
                "Sub",
                480,
                78,
                "The pilot is the close. Pricing is not a stage you can skip to.",
                16,
                MUTED,
            ),
            *labels,
            *arrows,
            *boxes,
            text(
                "Foot",
                480,
                330,
                "Anything vaguer at any stage means you are one stage behind where you think.",
                16,
                MUTED,
            ),
            card("Bg", 480, 190, 960, 380, PAPER, radius=0),
        ),
    )


DIAGRAMS = {
    "two_products": two_products,
    "agpl_decision": agpl_decision,
    "widget_anatomy": widget_anatomy,
    "linked_parameters": linked_parameters,
    "dashboard_to_app": dashboard_to_app,
    "segment_triggers": segment_triggers,
    "the_sale": the_sale,
}


def main() -> None:
    for name, build in DIAGRAMS.items():
        path = write(build(), HERE / f"{name}.json")
        print(f"wrote {path.relative_to(Path.cwd()) if path.is_relative_to(Path.cwd()) else path}")


if __name__ == "__main__":
    main()
