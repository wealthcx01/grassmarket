"""Build the Sales Operations Playbook diagrams (GRS-0225 toolchain, GRS-0217 content).

    uv run python design/motion/courses/sales_ops/build.py

Writes one JSON scene per diagram. Compiling and rendering is `design/motion/render.sh`, which runs
rive-cli over every scene here and refuses a blank frame.

This course differs from the three product courses: it teaches a *process* rather than a product,
and a process is inherently spatial — it has an order, forks and exits. So these diagrams carry more
of the teaching than a product course's do, and `the_ten_stages` is the one an advisor should be
able to redraw from memory.

`score_and_price_never_mix` is the highest-stakes drawing in the whole Academy. Non-negotiable #7
and ADR-0002 say score-points and currency never appear in one equation, and the contracts enforce
it — `total_lever_npv` sums Money and Money only. An advisor who divides a score into pounds has
invented a number the methodology refuses to produce, and no amount of prose has ever stopped
anyone doing that as reliably as two columns with a wall between them.
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


# --- 1. The ten stages (section 1) ---------------------------------------------------------


def the_ten_stages() -> dict:
    """The whole motion on one artboard, because an advisor who cannot draw the pipeline cannot run
    it. Eight stages on the main path and two exits below, since Closed and Nurture are outcomes
    rather than steps — drawing them in line would imply every deal passes through them.

    The stage names are the real `PipelineStage` values. That is deliberate: the process the CRM
    enables and the process the Academy teaches have to be the same thing, and using the enum's own
    words is what keeps them from drifting apart."""
    # The enum's OWN names, including the two compound ones. The first cut shortened
    # `workshop_scheduled` to "workshop" and `workshop_delivered` to "delivered" — which put two
    # boxes reading "delivered" on one path meaning different things, while the subtitle claimed
    # these were the CRM's names rather than a paraphrase. Compound names get two lines.
    main = [
        ("Pros", "prospect", "", 118),
        ("Sched", "workshop", "scheduled", 268),
        ("Deliv", "workshop", "delivered", 418),
        ("Qual", "qualified", "", 568),
        ("Scope", "scoped", "", 718),
        ("Contr", "contracted", "", 868),
        ("Act", "active", "", 1018),
        ("Done", "delivered", "", 1168),
    ]
    layers: list = []
    for i, (name, line1, line2, x) in enumerate(main):
        accent = line1 in ("qualified", "contracted")
        colour = ON_GREEN if accent else INK
        if line2:
            layers.append(text(f"{name}L", x, 186, line1, 14, colour))
            layers.append(text(f"{name}L2", x, 208, line2, 14, colour))
        else:
            layers.append(text(f"{name}L", x, 196, line1, 14, colour))
        layers.append(
            card(f"{name}Card", x, 196, 128, 56, GREEN if accent else GREEN_TINT, stroke=RULE)
        )
        if i < len(main) - 1:
            layers.extend(arrow_right(f"{name}Arrow", x + 75, 196, 22, MUTED))
    return scene(
        "TheTenStages",
        1280,
        420,
        stack(
            text("Title", 640, 46, "The motion, stage by stage", 30, INK),
            text(
                "Sub",
                640,
                82,
                "These are the CRM's own stage names, not a paraphrase of them.",
                16,
                MUTED,
            ),
            *layers,
            text("Money1", 568, 142, "Stream A opens", 12, GREEN),
            text("Money2", 868, 142, "Stream B opens", 12, GREEN),
            # The two exits, below the line because they are outcomes rather than steps.
            text("ExitLabel", 640, 268, "and two exits, from almost anywhere", 14, MUTED),
            text("ClosedL", 500, 322, "closed", 15, INK),
            text("NurtL", 780, 322, "nurture", 15, INK),
            card("ClosedCard", 500, 322, 168, 50, PAPER, stroke=RULE),
            card("NurtCard", 780, 322, 168, 50, PAPER, stroke=RULE),
            text(
                "Foot",
                640,
                384,
                "Neither exit is a failure. Both are recorded outcomes you re-open later.",
                16,
                MUTED,
            ),
            card("Bg", 640, 210, 1280, 420, PAPER, radius=0),
        ),
    )


# --- 2. What a prospect record needs (section 2) -------------------------------------------


def what_a_prospect_needs() -> dict:
    """Two fields decide whether a prospect is a deal or a business card, and one of them decides
    money nine months later. Drawn as a record with the two that matter filled, because the failure
    is not omitting a field — it is filling in the easy ones and calling the record done."""
    fields = [
        ("Name", "company and contact", False, 158),
        ("Sector", "sector", False, 202),
        ("Pain", "the growth pain, verbatim", True, 246),
        ("Source", "who sourced it", True, 290),
        ("Next", "a dated next step", True, 334),
    ]
    layers: list = []
    for name, label, required, y in fields:
        layers.append(text(f"{name}L", 330, y, label, 16, ON_GREEN if required else INK))
        if required:
            layers.append(card(f"{name}Row", 330, y, 400, 36, GREEN, radius=6))
    return scene(
        "WhatAProspectNeeds",
        1000,
        460,
        stack(
            text("Title", 500, 46, "A prospect record, or a business card", 30, INK),
            text(
                "Sub",
                500,
                82,
                "Anyone fills in the top two. The bottom three are the deal.",
                16,
                MUTED,
            ),
            *layers,
            card("RecordCard", 330, 246, 460, 240, PAPER, stroke=RULE),
            text("Why1", 800, 208, "no pain,", 15, MUTED),
            text("Why2", 800, 232, "no reason to meet", 15, MUTED),
            text("Why3", 800, 288, "sourcing decides", 15, INK),
            text("Why4", 800, 312, "your rate later", 15, INK),
            text(
                "Foot",
                500,
                418,
                "Log who sourced it on day one. Nobody can reconstruct it in month nine.",
                16,
                WARN,
            ),
            card("Bg", 500, 230, 1000, 460, PAPER, radius=0),
        ),
    )


# --- 3. The workshop is the advancing action (section 3) -----------------------------------


def the_workshop_is_the_demo() -> dict:
    """Two meetings that look identical in a calendar and are not the same event at all. The
    difference is who is doing the work: in one you describe a methodology, in the other the client
    watches their own moat get scored.

    Same before/after grammar as the product courses use, because it is the same shape of idea."""
    return scene(
        "TheWorkshopIsTheDemo",
        1000,
        450,
        stack(
            text("Title", 500, 46, "Two meetings, one calendar entry", 30, INK),
            text("HeadL", 270, 112, "A COURTESY CALL", 12, MUTED, letter_spacing=1.5),
            text("HeadR", 730, 112, "AN ADVANCING ACTION", 12, GREEN, letter_spacing=1.5),
            text("L1", 270, 172, "you describe the", 16, MUTED),
            text("L2", 270, 196, "methodology", 16, MUTED),
            text("L3", 270, 244, "they say it sounds", 16, MUTED),
            text("L4", 270, 268, "interesting", 16, MUTED),
            text("L5", 270, 316, "no dated next step", 16, WARN),
            text("R1", 730, 172, "they watch their own", 16, INK),
            text("R2", 730, 196, "moat get scored", 16, INK),
            text("R3", 730, 244, "on their own numbers,", 16, INK),
            text("R4", 730, 268, "in ninety minutes", 16, INK),
            text("R5", 730, 316, "a finding, and a date", 16, GREEN),
            card("LeftCard", 270, 244, 380, 220, PAPER, stroke=RULE),
            card("RightCard", 730, 244, 380, 220, GREEN_TINT, stroke=GREEN),
            text(
                "Foot",
                500,
                408,
                "The workshop IS the demo. Book it off a pain you actually heard.",
                16,
                MUTED,
            ),
            card("Bg", 500, 225, 1000, 450, PAPER, radius=0),
        ),
    )


# --- 4. Qualify or nurture (section 4) -----------------------------------------------------


def qualify_or_nurture() -> dict:
    """The fork, and the third outcome that is actually the bug: a deal left sitting at Delivered.
    Two honest answers and one silent failure, so the silent one is drawn in the warning colour
    below the fork rather than as a third branch — it is not a decision anybody makes, it is a
    decision nobody made."""
    return scene(
        "QualifyOrNurture",
        1000,
        460,
        stack(
            text("Title", 500, 46, "Every workshop ends in one of two states", 30, INK),
            text("Q", 500, 128, "Is there a real, addressable bottleneck?", 21, INK),
            card("QBox", 500, 128, 540, 58, PAPER, stroke=INK, thickness=2),
            text("YesL", 300, 184, "Yes", 15, MUTED),
            text("NoL", 700, 184, "No", 15, MUTED),
            text("LeftT", 270, 248, "Qualified", 20, ON_GREEN),
            text("LeftB", 270, 282, "advance, with the", 14, ON_GREEN_MUTED),
            text("LeftB2", 270, 304, "finding recorded", 14, ON_GREEN_MUTED),
            text("RightT", 730, 248, "Nurture", 20, INK),
            text("RightB", 730, 282, "say so honestly, with", 14, MUTED),
            text("RightB2", 730, 304, "a dated reason to return", 14, MUTED),
            card("LeftBox", 270, 276, 320, 116, GREEN),
            card("RightBox", 730, 276, 320, 116, GREEN_TINT, stroke=RULE),
            *arrow_down("DownL", 270, 172, 40, MUTED),
            *arrow_down("DownR", 730, 172, 40, MUTED),
            text(
                "Warn",
                500,
                382,
                "Left at Delivered is not a third answer. It is nobody having decided.",
                17,
                WARN,
            ),
            text(
                "Foot",
                500,
                424,
                '"It went well" is not a qualification. A named bottleneck is.',
                15,
                MUTED,
            ),
            card("Bg", 500, 230, 1000, 460, PAPER, radius=0),
        ),
    )


# --- 5. The score and the price never mix (section 5) --------------------------------------


def score_and_price_never_mix() -> dict:
    """The highest-stakes drawing in the Academy. Non-negotiable #7 and ADR-0002: score-points and
    currency never appear in one equation, and the contracts enforce it — `total_lever_npv` sums
    Money and Money only, and a value bridge citing an assumption outside its register refuses to
    construct at all.

    Drawn as two columns with a solid wall between them, and the wall labelled. The temptation this
    prevents is specific and constant: dividing a score into pounds to produce a price. That number
    feels defensible and the methodology refuses to produce it."""
    left = [
        ("what it measures", "how weak the moat is"),
        ("its unit", "score points"),
        ("what it answers", "how bad is this?"),
    ]
    right = [
        ("what it measures", "what fixing it is worth"),
        ("its unit", "pounds, traceable to an assumption"),
        ("what it answers", "what is it worth doing?"),
    ]
    rows = [186, 254, 322]
    layers: list = []
    for i, ((_, lv), (_, rv)) in enumerate(zip(left, right, strict=True)):
        y = rows[i]
        layers.append(text(f"L{i}", 320, y, lv, 15, INK))
        layers.append(text(f"R{i}", 860, y, rv, 15, ON_GREEN))
    for label, y in zip(("MEASURES", "UNIT", "ANSWERS"), rows, strict=True):
        layers.append(text(f"Row{y}", 90, y, label, 11, MUTED, letter_spacing=1.2))
    return scene(
        "ScoreAndPriceNeverMix",
        1180,
        480,
        stack(
            text("Title", 590, 46, "Two numbers, and a wall between them", 30, INK),
            text("HeadL", 320, 130, "THE SCORE", 18, INK, letter_spacing=1.4),
            text("HeadR", 860, 130, "THE VALUE BRIDGE", 18, GREEN, letter_spacing=1.4),
            *layers,
            card("RightPanel", 860, 254, 440, 230, GREEN),
            card("LeftPanel", 320, 254, 440, 230, GREEN_TINT, stroke=RULE),
            line("Wall", 590, 254, 4, 270, INK),
            text("WallLabel", 590, 396, "never one equation", 16, INK),
            text(
                "Warn",
                590,
                440,
                "Dividing a score into pounds invents a number the methodology refuses to produce.",
                16,
                WARN,
            ),
            card("Bg", 590, 240, 1180, 480, PAPER, radius=0),
        ),
    )


# --- 6. The two streams (section 6) --------------------------------------------------------


def two_streams() -> dict:
    """Where each stream of commission enters, and what decides its rate. Two facts an advisor
    routinely gets wrong: that both streams open at the same moment (they do not), and that the rate
    is a single number (it is a cell in a two-by-two).

    No rates. They live in the v7 schedule and resolve live; a figure in a diagram goes stale
    silently and gets quoted anyway."""
    layers: list = []
    # Stream entry points
    layers += [
        text("AT", 280, 158, "Stream A: product", 19, INK),
        text("AB", 280, 194, "opens when a product", 14, MUTED),
        text("AB2", 280, 216, "answers the finding", 14, MUTED),
        text("AW", 280, 254, "at Qualified", 14, GREEN),
        card("ACard", 280, 206, 380, 150, GREEN_TINT, stroke=RULE),
        text("BT", 740, 158, "Stream B: consultancy", 19, ON_GREEN),
        text("BB", 740, 194, "opens when the work", 14, ON_GREEN_MUTED),
        text("BB2", 740, 216, "is contracted", 14, ON_GREEN_MUTED),
        text("BW", 740, 254, "at Contracted", 14, SIGNAL),
        card("BCard", 740, 206, 380, 150, GREEN),
    ]
    # A real 2x2, not two lists. The first cut printed four labels in two columns and it read as
    # two unrelated lists — the whole idea is that the rate is a CELL, so the grid has to be a grid.
    # The cells say "rate" rather than carrying figures: there are four different ones and they
    # resolve live, which is exactly what four labelled empty cells communicates.
    rows = [("bruntsfield-led", 412), ("consultant-led", 460)]
    cols = [("self-sourced", 620), ("firm-sourced", 830)]
    for label, y in rows:
        layers.append(text(f"R{label.replace('-', '')}", 400, y, label, 15, INK))
    for label, x in cols:
        layers.append(text(f"C{label.replace('-', '')}", x, 372, label, 14, MUTED))
    for rlabel, y in rows:
        for clabel, x in cols:
            key = f"Cell{rlabel[:4]}{clabel[:4]}"
            layers.append(text(f"{key}T", x, y, "rate", 14, GREEN))
            layers.append(card(key, x, y, 180, 40, GREEN_TINT, stroke=RULE, radius=8))
    return scene(
        "TwoStreams",
        1020,
        560,
        stack(
            text("Title", 510, 46, "Two streams, entering at different stages", 30, INK),
            text("Sub", 510, 84, "And one of them is priced by a two-by-two.", 16, MUTED),
            *layers,
            text("GridT", 510, 330, "delivery type  x  sourcing  sets the Stream B rate", 16, INK),
            text(
                "Foot",
                510,
                522,
                "Self-sourced always pays more. Read the live cell off the Earnings page.",
                16,
                MUTED,
            ),
            card("Bg", 510, 280, 1020, 560, PAPER, radius=0),
        ),
    )


# --- 7. One timeline (section 7) -----------------------------------------------------------


def one_timeline() -> dict:
    """Why the comms log matters, drawn as the thing it replaces. Scattered touches in four places
    mean nobody can see the deal's true state, including you in three months.

    The left panel is deliberately disordered and the right is a single column, because the argument
    is about legibility rather than about record-keeping discipline."""
    scattered = [
        ("A", 168, 176),
        ("B", 300, 214),
        ("C", 210, 262),
        ("D", 330, 296),
        ("E", 180, 330),
    ]
    ordered = [(y) for y in (176, 214, 252, 290, 328)]
    layers: list = []
    for name, x, y in scattered:
        layers.append(card(f"S{name}", x, y, 74, 22, MUTED, radius=5))
    for i, y in enumerate(ordered):
        layers.append(card(f"O{i}", 740, y, 240, 22, GREEN, radius=5))
    return scene(
        "OneTimeline",
        1000,
        450,
        stack(
            text("Title", 500, 46, "One account, one timeline", 30, INK),
            text(
                "HeadL", 260, 118, "AN INBOX, A CHAT AND A NOTEBOOK", 11, MUTED, letter_spacing=1.2
            ),
            text("HeadR", 740, 118, "THE ACCOUNT'S ACTIVITY LOG", 11, GREEN, letter_spacing=1.2),
            *layers,
            card("LeftCard", 260, 252, 340, 220, PAPER, stroke=RULE),
            card("RightCard", 740, 252, 340, 220, GREEN_TINT, stroke=RULE),
            text("LNote", 260, 386, "nobody can see the state", 15, MUTED),
            text("RNote", 740, 386, "anyone can, including you", 15, INK),
            text(
                "Foot",
                500,
                424,
                "You will not remember this deal in three months. The log will.",
                16,
                MUTED,
            ),
            card("Bg", 500, 225, 1000, 450, PAPER, radius=0),
        ),
    )


# --- 8. The recovery fee (section 8) -------------------------------------------------------


def the_recovery_fee() -> dict:
    """The money most advisors leave on the table, drawn as the fork it actually is. A delivered
    workshop that never contracted is not a loss unless you let the window close in silence.

    Two endings from one situation, with the wrong one drawn in the warning colour because it is
    the default — it is what happens when nobody does anything."""
    return scene(
        "TheRecoveryFee",
        1020,
        460,
        stack(
            text("Title", 510, 46, "A workshop delivered, and no contract", 30, INK),
            text("Q", 510, 122, "The attribution window closes.", 20, INK),
            card("QBox", 510, 122, 440, 54, PAPER, stroke=INK, thickness=2),
            # Offset clear of the arrow stems. The first cut centred each label on its own arrow
            # and both rendered with the stem straight through the word.
            text("BadL", 372, 176, "do nothing", 14, MUTED),
            text("GoodL", 632, 176, "resolve it", 14, MUTED),
            text("BadT", 280, 244, "Written off", 19, INK),
            text("BadB", 280, 278, "the effort is gone and", 14, MUTED),
            text("BadB2", 280, 300, "the lead goes cold", 14, MUTED),
            text("GoodT", 740, 244, "Recovery fee", 19, ON_GREEN),
            text("GoodB", 740, 278, "the workshop effort is", 14, ON_GREEN_MUTED),
            text("GoodB2", 740, 300, "recovered, deal to Nurture", 14, ON_GREEN_MUTED),
            card("BadBox", 280, 272, 340, 120, PAPER, stroke=RULE),
            card("GoodBox", 740, 272, 340, 120, GREEN),
            *arrow_down("DownBad", 280, 164, 40, MUTED),
            *arrow_down("DownGood", 720, 164, 40, MUTED),
            text(
                "Warn",
                510,
                382,
                "Written off is the default. It is what happens when nobody does anything.",
                17,
                WARN,
            ),
            text(
                "Foot",
                510,
                424,
                "A scored moat that was not ready today is a warm lead in two quarters.",
                15,
                MUTED,
            ),
            card("Bg", 510, 230, 1020, 460, PAPER, radius=0),
        ),
    )


DIAGRAMS = {
    "the_ten_stages": the_ten_stages,
    "what_a_prospect_needs": what_a_prospect_needs,
    "the_workshop_is_the_demo": the_workshop_is_the_demo,
    "qualify_or_nurture": qualify_or_nurture,
    "score_and_price_never_mix": score_and_price_never_mix,
    "two_streams": two_streams,
    "one_timeline": one_timeline,
    "the_recovery_fee": the_recovery_fee,
}


def main() -> None:
    for name, build in DIAGRAMS.items():
        path = write(build(), HERE / f"{name}.json")
        print(f"wrote {path.relative_to(Path.cwd()) if path.is_relative_to(Path.cwd()) else path}")


if __name__ == "__main__":
    main()
