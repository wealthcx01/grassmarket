"""Build the Sales Egoist course diagrams (GRS-0225, GRS-0218).

    uv run python design/motion/courses/sales_egoist/build.py

Writes one JSON scene per diagram. Compiling and rendering is `design/motion/render.sh`, which runs
rive-cli over every scene here and refuses a blank frame.

One diagram per section, and each earns its place by being spatial rather than verbal. The doctrine
is unusually visual for a sales course — it is built on contrasts (placeholder against principal),
maps (the committee, the account), sequences (tool to weapon to formula) and a dated calendar (the
battlefield). Those are drawings. The parts that are argument, and there are many, stay as prose.

The vendored font is ASCII-only. Curly quotes, en-dashes and the like render blank and do so
silently, so every string here is plain ASCII on purpose.
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
    WARN,
    arrow_right,
    card,
    scene,
    stack,
    text,
    write,
)

HERE = Path(__file__).resolve().parent


# --- 1. Placeholder or principal (section 1) ----------------------------------------------


def placeholder_or_principal() -> dict:
    """The doctrine's founding contrast, and the reason it is a drawing rather than a list: the
    two columns are the same five situations answered two ways, and reading across a row is the
    teaching. A bulleted list loses the pairing, which is the whole point."""
    rows = (
        ("Waits for inbound and RFPs", "Engineers the reason to engage"),
        ("Hopes relationships mature", "Turns trust into real leverage"),
        ("Reports activity", "Reports territory taken"),
        ("Moves on the buyer's timeline", "Sets the timeline"),
        ("Is interchangeable", "Is irreplaceable"),
    )
    children = [
        text("Title", 560, 48, "The same five situations, answered two ways", 28, INK),
        text("LeftHead", 300, 122, "THE PLACEHOLDER", 19, MUTED, letter_spacing=1.5),
        # GREEN, not ON_GREEN. The column headers sit on PAPER *above* the cards, so the
        # readable-on-Bottle-Green colour rendered a near-white heading on a near-white
        # background — legible in the JSON, invisible in the frame.
        text("RightHead", 820, 122, "THE PRINCIPAL", 19, GREEN, letter_spacing=1.5),
    ]
    y = 196
    for i, (left, right) in enumerate(rows):
        children.append(text(f"L{i}", 300, y, left, 17, INK))
        children.append(text(f"R{i}", 820, y, right, 17, ON_GREEN))
        y += 64
    children.append(
        text(
            "Foot",
            560,
            548,
            "A seller who waits becomes a placeholder. Interchangeable, and easily replaced.",
            16,
            MUTED,
        )
    )
    # Sized from the row geometry, not by eye: rows run 196 to 196 + 4*64 = 452, so a 300-tall
    # card centred at 288 stopped at 438 and left the fifth row ("Is interchangeable" / "Is
    # irreplaceable") stranded outside both panels — and the right-hand one outside its green
    # background, which made it white text on paper.
    children.append(card("LeftCard", 300, 324, 460, 330, PAPER, stroke=RULE))
    children.append(card("RightCard", 820, 324, 460, 330, GREEN))
    children.append(card("Bg", 560, 300, 1120, 600, PAPER, radius=0))
    return scene("PlaceholderOrPrincipal", 1120, 600, stack(*children))


# --- 2. The battlefield: dated catalysts (section 2) ---------------------------------------


def the_battlefield() -> dict:
    """The trigger calendar. This one has to be a drawing because the teaching is the ORDER and
    the gaps: the confirmations milestone lands a year before the settlement deadline, and the AI
    Act obligations bite between them. An advisor who cannot place these on a line cannot work
    backwards from one, which is the drill in section 2."""
    marks = (
        (150, "May 2024", "US moves to T+1", MUTED),
        (390, "Aug 2026", "EU AI Act obligations\nbegin to bite", INK),
        (630, "Dec 2026", "T+0 allocations and\nconfirmations mandated", GREEN),
        (930, "11 Oct 2027", "UK, EU and Switzerland\nmove to T+1", GREEN),
    )
    children = [
        text("Title", 560, 46, "The dated catalysts an egoist works backwards from", 27, INK),
        text(
            "Sub",
            560,
            84,
            "Budgets thaw when a board-level deadline forces them to.",
            16,
            MUTED,
        ),
    ]
    for i, (x, when, what, colour) in enumerate(marks):
        children.append(text(f"When{i}", x, 214, when, 18, colour))
        for j, part in enumerate(what.split("\n")):
            children.append(text(f"What{i}_{j}", x, 268 + j * 26, part, 15, MUTED))
        children.append(card(f"Dot{i}", x, 320, 16, 16, colour, radius=8))
    children.append(card("Axis", 560, 320, 900, 3, RULE, radius=0))
    children.append(
        text(
            "Undated",
            560,
            410,
            "UNDATED, AND INEVITABLE",
            16,
            WARN,
            letter_spacing=1.4,
        )
    )
    children.append(
        text(
            "UndatedBody",
            560,
            448,
            "The incumbent outage in a bursty session. Position as though it is a when.",
            16,
            MUTED,
        )
    )
    children.append(card("Bg", 560, 250, 1120, 500, PAPER, radius=0))
    return scene("TheBattlefield", 1120, 500, stack(*children))


# --- 3. The armoury by purpose (section 3) -------------------------------------------------


def the_armoury() -> dict:
    """Six purposes, not sixteen names. The armoury is wide enough that a list of methodologies
    reads as noise; grouped by what you are trying to DO, it becomes selectable. That grouping is
    the drawing's only job."""
    cells = (
        (260, 220, "Discovery\nand diagnosis", "SPIN . Solution\nConceptual . Gap"),
        (560, 220, "Insight\nand reframing", "Challenger . Provocation\nCommand of the Message"),
        (860, 220, "Value\nand economics", "Value / ROI Selling\nMutual Action Plan"),
        (260, 440, "Qualification\nand deal control", "MEDDIC / MEDDPICC\nSandler . NEAT / SNAP"),
        (560, 440, "Committee\nand account", "Miller Heiman Blue Sheet\nTarget Account Selling"),
        (860, 440, "Timing\nand presence", "Social and Digital\nThe Timing Layer"),
    )
    children = [
        text("Title", 560, 46, "The armoury, organised by what you need it to do", 27, INK),
        text(
            "Sub",
            560,
            84,
            "Wide on purpose: not so you use everything, so you choose with knowledge.",
            16,
            MUTED,
        ),
    ]
    for i, (x, y, head, body) in enumerate(cells):
        for j, part in enumerate(head.split("\n")):
            children.append(text(f"H{i}_{j}", x, y - 44 + j * 28, part, 19, INK))
        for j, part in enumerate(body.split("\n")):
            children.append(text(f"B{i}_{j}", x, y + 24 + j * 26, part, 15, MUTED))
    for i, (x, y, _, _) in enumerate(cells):
        children.append(card(f"Cell{i}", x, y, 272, 176, PAPER, stroke=RULE))
    children.append(card("Bg", 560, 280, 1120, 560, PAPER, radius=0))
    return scene("TheArmoury", 1120, 560, stack(*children))


# --- 4. Tool, weapon, formula (section 4) --------------------------------------------------


def tool_to_weapon() -> dict:
    """Three boxes and two arrows, and the reason it is worth a drawing is that the distinction
    collapses the moment it is written as a sentence. A method you know, a method you chose, and
    the equation for when it strikes are three different things; the arrows are the argument."""
    children = [
        text("Title", 560, 48, "A tool is not a weapon", 30, INK),
        text(
            "Sub",
            560,
            88,
            "A method becomes a weapon only when you define the formula for how it strikes.",
            16,
            MUTED,
        ),
        text("N1", 230, 178, "01", 15, MUTED),
        text("T1", 230, 224, "TOOL", 22, INK, letter_spacing=1.6),
        text("B1", 230, 272, "A methodology you", 15, MUTED),
        text("B1b", 230, 296, "happen to know.", 15, MUTED),
        text("N2", 560, 178, "02", 15, MUTED),
        text("T2", 560, 224, "WEAPON", 22, INK, letter_spacing=1.6),
        text("B2", 560, 272, "That tool, chosen", 15, MUTED),
        text("B2b", 560, 296, "deliberately as your one edge.", 15, MUTED),
        text("N3", 890, 178, "03", 15, ON_GREEN_MUTED),
        text("T3", 890, 224, "FORMULA", 22, ON_GREEN, letter_spacing=1.6),
        text("B3", 890, 272, "The repeatable equation for", 15, ON_GREEN_MUTED),
        text("B3b", 890, 296, "when and how it wins.", 15, ON_GREEN_MUTED),
        text(
            "Foot",
            560,
            416,
            "When I do X to buyer Y, I produce outcome Z.",
            19,
            GREEN,
        ),
        text("FootLabel", 560, 456, "A FORMULA, NOT A FEATURE LIST", 14, MUTED, letter_spacing=1.4),
    ]
    children.extend(arrow_right("Arrow1", 372, 240, 46, MUTED))
    children.extend(arrow_right("Arrow2", 702, 240, 46, MUTED))
    children.append(card("Card1", 230, 250, 260, 190, PAPER, stroke=RULE))
    children.append(card("Card2", 560, 250, 260, 190, GREEN_TINT, stroke=RULE))
    children.append(card("Card3", 890, 250, 260, 190, GREEN))
    children.append(card("Bg", 560, 250, 1120, 500, PAPER, radius=0))
    return scene("ToolToWeapon", 1120, 500, stack(*children))


# --- 5. The deal equation (section 5) ------------------------------------------------------


def the_deal_equation() -> dict:
    """Five levers up, one down. Drawn because the asymmetry is the lesson: a weak deal is rarely
    weak on all five, so the work is diagnosing which term is dragging rather than pushing harder
    on all of them. The downward arrow on switching cost is the one advisors forget they can move
    at all -- they can, by absorbing the migration risk."""
    ups = (
        (200, "Trigger", "the dated catalyst\nyou are riding"),
        (380, "Reach", "access to the\neconomic buyer"),
        (560, "Insight", "differentiation of\nyour thesis"),
        (740, "Proof", "fidelity of what\nyou can show"),
        (920, "Consensus", "agreement across\nthe committee"),
    )
    children = [
        text("Title", 560, 46, "Win probability is five levers and one drag", 27, INK),
        text(
            "Sub",
            560,
            84,
            "Every variable is a lever, not a given. Diagnose which term is dragging.",
            16,
            MUTED,
        ),
        text("RaiseLabel", 560, 140, "RAISES WIN PROBABILITY", 14, GREEN, letter_spacing=1.4),
    ]
    for i, (x, head, body) in enumerate(ups):
        children.append(text(f"U{i}", x, 216, head, 19, INK))
        for j, part in enumerate(body.split("\n")):
            children.append(text(f"UB{i}_{j}", x, 254 + j * 24, part, 14, MUTED))
        children.append(card(f"UCard{i}", x, 240, 164, 132, PAPER, stroke=RULE))
    # No per-lever arrows. The first version hung five downward arrows off the cards pointing at
    # nothing, which read as decoration; the two section labels already carry the direction.
    children.append(text("LowerLabel", 560, 356, "LOWERS IT", 14, WARN, letter_spacing=1.4))
    children.append(text("Switch", 560, 412, "The incumbent's switching cost", 19, WARN))
    children.append(
        text(
            "SwitchBody",
            560,
            448,
            "Millions in cost, contracts in years. Absorb it and you have raised the odds.",
            14,
            MUTED,
        )
    )
    children.append(card("SwitchCard", 560, 424, 620, 96, PAPER, stroke=WARN))
    children.append(
        text(
            "Foot",
            560,
            530,
            "Doubling your reach rate does as much as doubling your win rate.",
            16,
            GREEN,
        )
    )
    children.append(card("Bg", 560, 300, 1120, 600, PAPER, radius=0))
    return scene("TheDealEquation", 1120, 600, stack(*children))


# --- 6. The committee, and the weapon each one answers to (section 6) ----------------------


def the_committee() -> dict:
    """The single highest-value drawing in the course, for the same reason the AGPL decision tree
    is in OpenBB's: it is the thing an advisor gets wrong under pressure. Six seats, six different
    fears, six different weapons. Bringing the wrong one is an instant disqualification, and that
    sentence is much easier to believe as a table than as a paragraph."""
    seats = (
        ("Head of Trading", "wants speed", "Challenger insight"),
        ("The quant", "wants elegant data access", "A working demo"),
        ("Head of Architecture", "wants resilience, no lock-in", "Strangler-gateway story"),
        ("The CRO", "wants real-time risk", "Trust plus regulatory case"),
        ("Compliance", "wants explainability", "Governance narrative"),
        ("Procurement", "wants price and terms", "Mutual action plan"),
    )
    children = [
        text("Title", 560, 46, "One committee, six appetites, six weapons", 27, INK),
        text(
            "Sub",
            560,
            84,
            "No single message satisfies all of them. The wrong weapon is a disqualification.",
            16,
            MUTED,
        ),
        text("ColWho", 240, 146, "THE SEAT", 14, MUTED, letter_spacing=1.4),
        text("ColWant", 560, 146, "WHAT THEY WANT", 14, MUTED, letter_spacing=1.4),
        text("ColWeapon", 880, 146, "WHAT MOVES THEM", 14, GREEN, letter_spacing=1.4),
    ]
    y = 208
    for i, (who, want, weapon) in enumerate(seats):
        children.append(text(f"Who{i}", 240, y, who, 17, INK))
        children.append(text(f"Want{i}", 560, y, want, 16, MUTED))
        children.append(text(f"Weapon{i}", 880, y, weapon, 16, GREEN))
        if i:
            children.append(card(f"Rule{i}", 560, y - 30, 900, 1, RULE, radius=0))
        y += 58
    # Spans every row, header to last. Sized from the row geometry rather than by eye: the first
    # row sits at 208 and the sixth at 208 + 5*58 = 498, so a 380-tall column centred at 292 ended
    # at 482 and left Procurement outside the very column that is meant to group them.
    children.append(card("WeaponCol", 880, 322, 300, 420, GREEN_TINT))
    children.append(card("Bg", 560, 290, 1120, 580, PAPER, radius=0))
    return scene("TheCommittee", 1120, 580, stack(*children))


# --- 7. The flow channel (section 7) -------------------------------------------------------


def the_flow_channel() -> dict:
    """Challenge against skill, with the diagonal. Genuinely spatial: the point is that flow is a
    band and not a point, and that the two failure modes sit on either side of it. Every attempt
    to write this as a sentence produces something that sounds like a horoscope."""
    # 1400x660, and the extra room is a fix rather than a preference. At 1120 the three clusters
    # and the flow band did not fit inside the plot: "Fear drives over-discounting" ran under the
    # band's left edge, the BOREDOM cluster overflowed the plot's right side, and the SKILL axis
    # label sat ON the plot's bottom rule so the border struck through it. All three rendered
    # perfectly happily and all three were obvious in the still, which is why the still gets looked
    # at. Geometry now: plot 1080x420 centred at (720, 350) spans x 180-1260 and y 140-560; the
    # axis labels sit OUTSIDE that box; the three clusters are placed on the diagonal with a
    # 40px gap from the band.
    children = [
        text("Title", 700, 46, "Boredom, flow, anxiety: calibrate the room", 27, INK),
        text(
            "Sub",
            700,
            84,
            "Peak performance sits where challenge meets skill. It is engineered, not awaited.",
            16,
            MUTED,
        ),
        text("YAxis", 96, 350, "CHALLENGE", 14, MUTED, letter_spacing=1.4),
        text("XAxis", 720, 596, "SKILL", 14, MUTED, letter_spacing=1.4),
        text("Anxiety", 396, 206, "ANXIETY", 20, WARN, letter_spacing=1.4),
        text("AnxietyB", 396, 244, "The Tier-1 procurement battle", 14, MUTED),
        text("AnxietyC", 396, 268, "you sent a junior into.", 14, MUTED),
        text("AnxietyD", 396, 292, "Fear drives over-discounting.", 14, MUTED),
        text("Flow", 720, 352, "FLOW", 22, GREEN, letter_spacing=1.6),
        text("FlowB", 720, 388, "Difficulty matched to the seller,", 14, MUTED),
        text("FlowC", 720, 412, "with one demanding goal.", 14, MUTED),
        text("Boredom", 1046, 458, "BOREDOM", 20, MUTED, letter_spacing=1.4),
        text("BoredomB", 1046, 496, "The trivial renewal given", 14, MUTED),
        text("BoredomC", 1046, 520, "to your best seller.", 14, MUTED),
    ]
    children.append(card("FlowBand", 720, 380, 340, 130, GREEN_TINT))
    children.append(card("Plot", 720, 350, 1080, 420, PAPER, stroke=RULE))
    children.append(card("Bg", 700, 330, 1400, 660, PAPER, radius=0))
    return scene("TheFlowChannel", 1400, 660, stack(*children))


# --- 8. The campaign on one account (section 8) --------------------------------------------


def the_campaign() -> dict:
    """The eight convictions as one loop rather than eight skills, mapped onto the phases of an
    ATLAS engagement. This is the drawing that answers 'what do I actually do on Monday', and it
    is spatial because the convictions do not run in their numbered order -- II and VI happen
    before the trigger fires, and VIII runs the whole way through."""
    # This scene is 1400 wide where the rest are 1120, and that is the fix rather than shorter
    # labels: at 1120 the four cards fit but their body lines did not fit INSIDE them, so the text
    # overran into the arrows. Widening the board keeps the sentences whole, which matters here
    # because each line is a conviction and abbreviating it is exactly the compression this course
    # exists to undo. Four 300-wide cards at 190/540/890/1240 span 40-1390 with 50px gaps.
    phases = (
        (
            190,
            "BEFORE",
            "Choose the hard account (I)\nEnter with one weapon (II)\nBe present early (VI)",
        ),
        (540, "THE TRIGGER", "Run the documented play (III)\nSeek the hardest room (IV)"),
        (890, "THE ENGAGEMENT", "Orchestrate the committee (V)\nDrop the script (VII)"),
        (1240, "THE CLOSE", "Pre-emptive strike (VIII)\nbefore an RFP exists"),
    )
    children = [
        text("Title", 700, 46, "Eight convictions, one campaign", 28, INK),
        text(
            "Sub",
            700,
            84,
            "They are not eight skills practised apart. Run end to end they look like this.",
            16,
            MUTED,
        ),
    ]
    for i, (x, head, body) in enumerate(phases):
        children.append(
            text(f"P{i}", x, 172, head, 17, GREEN if i == 3 else INK, letter_spacing=1.3)
        )
        for j, part in enumerate(body.split("\n")):
            children.append(text(f"PB{i}_{j}", x, 226 + j * 26, part, 14, MUTED))
    # Arrows live in the 40px gaps BETWEEN cards. Anchored off the card edge (centre + half-width)
    # rather than a guessed offset, which is what drove the first version's arrows through the
    # neighbouring card's body text.
    for i in range(3):
        children.extend(arrow_right(f"Arrow{i}", phases[i][0] + 158, 224, 32, MUTED))
    children.append(
        text(
            "Through",
            700,
            394,
            "VIII . TOTAL ACCOUNT AWARENESS RUNS THE WHOLE WAY THROUGH",
            15,
            ON_GREEN,
            letter_spacing=1.3,
        )
    )
    children.append(card("ThroughBar", 700, 394, 1200, 54, GREEN))
    for i, (x, _, _) in enumerate(phases):
        children.append(card(f"PCard{i}", x, 224, 300, 168, PAPER, stroke=RULE))
    children.append(
        text(
            "Foot",
            700,
            462,
            "That is the Bruntsfield playbook: a closed loop from conviction to ownership.",
            16,
            MUTED,
        )
    )
    children.append(card("Bg", 700, 250, 1400, 500, PAPER, radius=0))
    return scene("TheCampaign", 1400, 500, stack(*children))


SCENES = {
    "placeholder_or_principal": placeholder_or_principal,
    "the_battlefield": the_battlefield,
    "the_armoury": the_armoury,
    "tool_to_weapon": tool_to_weapon,
    "the_deal_equation": the_deal_equation,
    "the_committee": the_committee,
    "the_flow_channel": the_flow_channel,
    "the_campaign": the_campaign,
}


def main() -> None:
    for key, fn in SCENES.items():
        path = write(fn(), HERE / f"{key}.json")
        print(f"wrote {path.relative_to(Path.cwd())}")


if __name__ == "__main__":
    main()
