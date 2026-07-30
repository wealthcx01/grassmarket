"""Build the Benzinga course diagrams (GRS-0225 toolchain, GRS-0217 content).

    uv run python design/motion/courses/benzinga/build.py

Writes one JSON scene per diagram. Compiling and rendering is `design/motion/render.sh`, which runs
rive-cli over every scene here and refuses a blank frame.

Same rule as the OpenBB set: each diagram exists because the idea it carries is spatial rather than
verbal. If a diagram could be replaced by its own caption without loss, it should not be here. The
Benzinga catalogue is 32 products in four families, and almost every mistake an advisor makes with
it is a *structural* mistake — pitching the wrong family to the wrong buyer, or promising a delivery
method the client cannot consume. Those are exactly the mistakes a drawing prevents.
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
    arrow_right,
    card,
    line,
    scene,
    stack,
    text,
    write,
)

HERE = Path(__file__).resolve().parent


# --- 1. Two arms, one brand (section 1) ----------------------------------------------------


def two_arms() -> dict:
    """The first thing an advisor gets wrong: Benzinga is a name they have seen on a retail
    finance website, so they pitch the website. The commission is on the other arm entirely.

    Same shape as the OpenBB `two_products` diagram on purpose — an advisor learning a second
    product should recognise the layout and spend their attention on what differs, not on
    re-reading a new diagram grammar."""
    return scene(
        "TwoArms",
        960,
        420,
        stack(
            text("Title", 480, 46, "Benzinga is two businesses", 30, INK),
            text("LeftName", 256, 148, "The media business", 22, MUTED),
            text("LeftKind", 256, 184, "benzinga.com, ~14M users/mo", 15, MUTED),
            text("LeftWho", 256, 240, "read by retail investors", 15, MUTED),
            text("LeftCmd", 256, 274, "not what you sell", 15, WARN),
            text("RightName", 704, 148, "The data business", 22, ON_GREEN),
            text("RightKind", 704, 184, "32 products, licensed by API", 15, ON_GREEN_MUTED),
            text("RightWho", 704, 240, "bought by platforms", 15, ON_GREEN_MUTED),
            text("RightCmd", 704, 274, "this is the 15%", 15, SIGNAL),
            text(
                "Foot",
                480,
                368,
                "The audience on the left is why the data on the right is worth buying.",
                16,
                MUTED,
            ),
            card("LeftCard", 256, 216, 380, 200, PAPER, stroke=RULE),
            card("RightCard", 704, 216, 380, 200, GREEN),
            card("Bg", 480, 210, 960, 420, PAPER, radius=0),
        ),
    )


# --- 2. The catalogue in four families (section 2) -----------------------------------------


def four_families() -> dict:
    """32 products is too many to hold, and an advisor who tries to remember the list will sell
    none of them. Four families, each with one job and one buyer, is holdable — and the family is
    what you qualify for in the room, never the individual product.

    The counts are the real ones from the committed catalogue, so the drawing is also the fastest
    way to see that Calendar is the biggest family and Market Data the smallest."""
    families = [
        ("Newswire", "& Content", "8", "what a user READS", 152),
        ("Calendar", "", "11", "what a user PLANS around", 372),
        ("Alternative", "Data", "9", "what a desk TRADES on", 592),
        ("Market", "Data", "4", "what a screen NEEDS", 812),
    ]
    layers: list = []
    for name, second, count, job, x in families:
        layers.append(text(f"{name}Count", x, 138, count, 40, GREEN))
        layers.append(text(f"{name}Name", x, 190, name, 19, INK))
        if second:
            layers.append(text(f"{name}Name2", x, 214, second, 19, INK))
        layers.append(text(f"{name}Job", x, 262, job, 14, MUTED))
        layers.append(card(f"{name}Card", x, 196, 196, 176, GREEN_TINT, stroke=RULE))
    return scene(
        "FourFamilies",
        960,
        380,
        stack(
            text("Title", 480, 44, "32 products, four families", 30, INK),
            text(
                "Sub",
                480,
                76,
                "Qualify the family in the room. Never recite the product list.",
                16,
                MUTED,
            ),
            *layers,
            # No em dash: the vendored Inter subset is printable ASCII only, and a missing glyph
            # renders as a silent blank space. `test_course_diagrams.py` now refuses one.
            text(
                "Foot",
                480,
                340,
                "Each family has its own buyer, budget and objection.",
                16,
                MUTED,
            ),
            card("Bg", 480, 190, 960, 380, PAPER, radius=0),
        ),
    )


# --- 3. Three ways it arrives (section 3) --------------------------------------------------


def delivery_paths() -> dict:
    """The question that decides whether a deal is a six-week integration or a six-month one, and
    the advisor is usually the first person in a position to ask it.

    Drawn as three lanes because the client's engineering answer differs per lane: a REST pull is a
    cron job, a TCP stream needs a always-on consumer and a reconnect strategy, and a flat file
    needs somewhere to put it. Promising the wrong one is the most expensive small mistake here."""
    lanes = [
        ("Rest", "REST (pull)", "you ask, on your schedule", "a scheduled job", 168, GREEN_TINT),
        ("Stream", "TCP (push)", "it arrives, as it happens", "an always-on consumer", 270, GREEN),
        ("File", "FTP / S3", "a file lands, in buckets", "somewhere to put it", 372, GREEN_TINT),
    ]
    layers: list = []
    for name, how, what, cost, y, fill in lanes:
        on_green = fill == GREEN
        layers.append(text(f"{name}How", 176, y - 14, how, 19, ON_GREEN if on_green else INK))
        layers.append(
            text(f"{name}What", 176, y + 14, what, 14, ON_GREEN_MUTED if on_green else MUTED)
        )
        layers.append(text(f"{name}Cost", 720, y, cost, 17, INK))
        layers.append(card(f"{name}Card", 176, y, 280, 78, fill, stroke=RULE))
        # `card` and `line` both centre on x, so the arrow is placed by its midpoint. The first cut
        # used the card's right edge as the arrow's START and the stem ran back underneath the card,
        # invisible only because the card happened to be painted on top of it.
        layers.extend(arrow_right(f"{name}Arrow", 468, y, 250, MUTED))
    return scene(
        "DeliveryPaths",
        960,
        500,
        stack(
            text("Title", 480, 44, "How the data actually arrives", 30, INK),
            text(
                "Sub",
                480,
                78,
                "Three delivery methods. Each one is a different build for the client.",
                16,
                MUTED,
            ),
            text("ColA", 176, 116, "BENZINGA OFFERS", 12, MUTED, letter_spacing=1.4),
            text("ColB", 720, 116, "CLIENT MUST HAVE", 12, MUTED, letter_spacing=1.4),
            *layers,
            line("Rule", 480, 438, 700, 1, RULE),
            text(
                "Foot",
                480,
                468,
                "Ask which one they can consume before you promise a timeline.",
                16,
                WARN,
            ),
            card("Bg", 480, 250, 960, 500, PAPER, radius=0),
        ),
    )


# --- 4. The WIIM moment (section 4) --------------------------------------------------------


def the_wiim_moment() -> dict:
    """Why the content family is bought, in one scene. A number alone produces a support ticket or
    a panic sale; the same number with one sentence beside it produces an informed user who stays.

    This is the diagram that makes an engagement product legible to an advisor who thinks of data
    as a cost line. The left panel is what the platform has without Benzinga; the right is what it
    has with. Nothing else about the screen changes, which is the point."""
    return scene(
        "WiimMoment",
        960,
        440,
        stack(
            text("Title", 480, 44, "The same screen, one sentence apart", 30, INK),
            text("LeftLabel", 256, 92, "WITHOUT", 12, MUTED, letter_spacing=1.6),
            text("RightLabel", 704, 92, "WITH", 12, GREEN, letter_spacing=1.6),
            # Left: the bare number
            text("LeftTicker", 256, 152, "ACME", 20, INK),
            text("LeftMove", 256, 196, "-6.2%", 34, WARN),
            text("LeftGap1", 256, 250, "The user does not know", 15, MUTED),
            text("LeftGap2", 256, 274, "if this is a catastrophe", 15, MUTED),
            text("LeftGap3", 256, 298, "or a dividend.", 15, MUTED),
            # Right: the number plus the one-liner
            text("RightTicker", 704, 152, "ACME", 20, INK),
            text("RightMove", 704, 196, "-6.2%", 34, WARN),
            text("RightWiim1", 704, 248, "Trading lower after the", 15, INK),
            text("RightWiim2", 704, 272, "company cut full-year", 15, INK),
            text("RightWiim3", 704, 296, "guidance.", 15, INK),
            card("LeftCard", 256, 232, 380, 216, PAPER, stroke=RULE),
            card("RightCard", 704, 232, 380, 216, GREEN_TINT, stroke=GREEN),
            text(
                "Foot",
                480,
                396,
                "One human-written sentence. It is why this family is bought.",
                16,
                MUTED,
            ),
            card("Bg", 480, 220, 960, 440, PAPER, radius=0),
        ),
    )


# --- 5. The forward calendar (section 5) ---------------------------------------------------


def event_horizon() -> dict:
    """The calendar family sells a tense, not a dataset. Everything else Benzinga licenses
    describes what has happened; the calendars describe what is *going to*, with a date on it.

    Drawn as a forward timeline because that is the product: a platform that can only show the
    past is a rear-view mirror, and a user with a dated horizon has a reason to come back."""
    events = [
        ("Earn", "earnings", "tomorrow", 150),
        ("Div", "ex-dividend", "in 3 days", 320),
        ("Fda", "PDUFA date", "in 2 weeks", 490),
        ("Lock", "lockup expiry", "in 90 days", 660),
    ]
    layers: list = []
    for name, what, when, x in events:
        layers.append(text(f"{name}What", x, 178, what, 17, INK))
        layers.append(text(f"{name}When", x, 204, when, 14, GREEN))
        layers.append(card(f"{name}Card", x, 190, 150, 74, GREEN_TINT, stroke=RULE))
        # The tick reaches down to the axis rather than floating above it.
        layers.append(line(f"{name}Tick", x, 253, 2, 38, MUTED))
    return scene(
        "EventHorizon",
        900,
        390,
        stack(
            text("Title", 450, 44, "The calendars sell a tense", 30, INK),
            text(
                "Sub",
                450,
                78,
                "Every other family says what happened. These say what is about to.",
                16,
                MUTED,
            ),
            *layers,
            line("Axis", 450, 272, 700, 2, MUTED),
            # BELOW the axis. Sharing its y put the rule straight through both words, which reads
            # as strikethrough text and is the kind of thing only the still shows you.
            text("Now", 104, 302, "today", 14, MUTED),
            text("Later", 796, 302, "forward", 14, MUTED),
            text(
                "Foot",
                450,
                350,
                "A platform with no forward calendar is a rear-view mirror.",
                16,
                MUTED,
            ),
            card("Bg", 450, 195, 900, 390, PAPER, radius=0),
        ),
    )


# --- 6. Attention before volume (section 6) ------------------------------------------------


def attention_before_volume() -> dict:
    """The one genuinely unique asset in the catalogue, and the hardest for an advisor to explain.

    Every vendor sells prices and filings. Almost nobody can sell what retail investors were
    *reading about* before the volume arrived, because that needs an owned audience, and Benzinga
    has one.

    Drawn as two bar series mirrored about a shared baseline: attention above, volume below, same
    time axis. The first version plotted both as scattered dots and it failed its own rule — the
    dots read as noise and the offset had to be asserted in a caption instead of being visible.
    Mirrored bars make the two humps peak at visibly different x, which is the entire idea, and the
    guide lines measure the gap rather than describe it."""
    step, first = 54, 227
    attention = [12, 30, 54, 76, 66, 48, 34, 24, 18, 12]
    volume = [8, 12, 16, 26, 42, 62, 78, 64, 44, 28]
    baseline = 295
    peak_att = first + step * attention.index(max(attention))
    peak_vol = first + step * volume.index(max(volume))

    # radius=3, not the 14 default: at these heights a rounded rectangle reads as a lozenge and the
    # series stops looking like bars at all.
    bars: list = []
    for i, height in enumerate(attention):
        bars.append(
            card(
                f"Att{i}", first + step * i, baseline - height / 2 - 2, 26, height, GREEN, radius=3
            )
        )
    for i, height in enumerate(volume):
        bars.append(
            card(
                f"Vol{i}", first + step * i, baseline + height / 2 + 2, 26, height, MUTED, radius=3
            )
        )

    return scene(
        "AttentionBeforeVolume",
        940,
        470,
        stack(
            text("Title", 470, 44, "Attention arrives before volume", 30, INK),
            text(
                "Sub",
                470,
                78,
                "First-party page views, in 10-minute buckets, from an owned audience.",
                16,
                MUTED,
            ),
            text("LagLabel", 470, 130, "views peak here, trading peaks later", 16, INK),
            # `arrow_right` centres on x rather than starting there, so the midpoint of the two
            # peaks is what makes the arrow actually span the gap it is measuring.
            *arrow_right("Lag", (peak_att + peak_vol) / 2, 160, peak_vol - peak_att, GREEN),
            text("AttLabel", 126, 244, "ticker views", 15, GREEN),
            text("VolLabel", 126, 348, "traded volume", 15, MUTED),
            # Bars in front of the guide lines: declared first means painted on top.
            *bars,
            line("PeakAtt", peak_att, 268, 2, 200, RULE),
            line("PeakVol", peak_vol, 268, 2, 200, RULE),
            line("Base", 470, baseline, 552, 2, INK),
            text(
                "Foot",
                470,
                434,
                "Anyone can sell you the volume. Almost nobody can sell you the gap.",
                16,
                MUTED,
            ),
            card("Bg", 470, 235, 940, 470, PAPER, radius=0),
        ),
    )


# --- 7. Who buys which family (section 7) --------------------------------------------------


def who_buys_what() -> dict:
    """The qualifying question, drawn. An advisor who knows this grid stops pitching alternative
    data to a media buyer and stops pitching logos to a quant fund.

    A grid rather than a list because the useful information is in the *pattern*: the content
    family sells to almost everyone, alternative data sells narrowly and at the highest price, and
    a retail brokerage is the only segment that plausibly buys all four."""
    segments = [
        ("Retail brokerage", 250),
        ("Wealth platform", 400),
        ("Quant fund", 550),
        ("Media", 700),
    ]
    # Rows start well below the two-line column headers. The first cut put them 20px higher and the
    # second header line ("brokerage", "platform", "fund") was clipped by the top row of cells —
    # which every structural check passed, and which is obvious the moment you look at the still.
    families = [("Content", 176), ("Calendar", 226), ("Alt data", 276), ("Market data", 326)]
    # Which cells are a real fit. Deliberately not all of them: a grid with every box ticked
    # teaches nothing and is also untrue.
    fit = {
        ("Content", "Retail brokerage"),
        ("Content", "Wealth platform"),
        ("Content", "Media"),
        ("Calendar", "Retail brokerage"),
        ("Calendar", "Wealth platform"),
        ("Calendar", "Media"),
        ("Alt data", "Retail brokerage"),
        ("Alt data", "Quant fund"),
        ("Market data", "Retail brokerage"),
        ("Market data", "Wealth platform"),
    }
    layers: list = []
    for fam, y in families:
        layers.append(text(f"Row{fam.replace(' ', '')}", 130, y, fam, 16, INK))
        for seg, x in segments:
            key = f"Cell{fam.replace(' ', '')}{seg.split()[0]}"
            if (fam, seg) in fit:
                layers.append(card(key, x, y, 96, 34, GREEN, radius=8))
            else:
                layers.append(card(key, x, y, 96, 34, PAPER, stroke=RULE, radius=8))
    for seg, x in segments:
        layers.append(text(f"Col{seg.split()[0]}", x, 116, seg.split()[0], 14, MUTED))
        if len(seg.split()) > 1:
            layers.append(text(f"Col{seg.split()[0]}b", x, 138, seg.split()[1], 14, MUTED))
    return scene(
        "WhoBuysWhat",
        860,
        450,
        stack(
            text("Title", 430, 44, "Who buys which family", 30, INK),
            text("Sub", 430, 78, "Filled means a real fit, not a maybe.", 16, MUTED),
            *layers,
            text(
                "Foot",
                430,
                400,
                "Only a retail brokerage plausibly buys all four. Everyone else is narrower.",
                15,
                MUTED,
            ),
            card("Bg", 430, 225, 860, 450, PAPER, radius=0),
        ),
    )


# --- 8. The first meeting (section 8) ------------------------------------------------------


def the_first_meeting() -> dict:
    """The sale, as a sequence, with the one step advisors skip marked.

    Ordering matters and is the teaching: naming a family before you know what the client can
    consume produces a promise engineering cannot keep, and quoting anything at all is out of
    scope because Benzinga pricing is per-contract. The skipped step is the delivery question,
    which is why it is the one drawn in the accent."""
    # Card 190 wide on a 232 step, which leaves a real 42px gutter for the connector. The first cut
    # used a 30px gutter and both arrowheads landed inside the cards they pointed at — legible only
    # because the cards painted over them.
    width, step, first = 190, 232, 152
    steps = [
        ("One", "1", "What do their", "users already ask?", False),
        ("Two", "2", "Which family", "answers it?", False),
        ("Three", "3", "What can they", "actually consume?", True),
        ("Four", "4", "Scoped quote,", "in writing.", False),
    ]
    layers: list = []
    for i, (name, num, line1, line2, accent) in enumerate(steps):
        x = first + step * i
        fill = GREEN if accent else GREEN_TINT
        on_green = accent
        layers.append(text(f"{name}Num", x, 148, num, 26, ON_GREEN if on_green else GREEN))
        layers.append(text(f"{name}L1", x, 200, line1, 16, ON_GREEN if on_green else INK))
        layers.append(text(f"{name}L2", x, 224, line2, 16, ON_GREEN if on_green else INK))
        layers.append(
            card(f"{name}Card", x, 192, width, 148, fill, stroke=None if accent else RULE)
        )
        if i < len(steps) - 1:
            gutter_mid = x + step / 2
            layers.extend(arrow_right(f"{name}Arrow", gutter_mid, 192, step - width, MUTED))
    return scene(
        "TheFirstMeeting",
        1000,
        420,
        stack(
            text("Title", 500, 44, "The first meeting, in four moves", 30, INK),
            text("Sub", 500, 78, "Step 3 is the one advisors skip.", 16, MUTED),
            *layers,
            text(
                "Foot",
                500,
                326,
                "Never quote a price. Benzinga pricing is per-contract, always.",
                17,
                WARN,
            ),
            text(
                "Foot2",
                500,
                368,
                "Skip step 3 and you promise a timeline engineering cannot keep.",
                15,
                MUTED,
            ),
            card("Bg", 500, 210, 1000, 420, PAPER, radius=0),
        ),
    )


DIAGRAMS = {
    "two_arms": two_arms,
    "four_families": four_families,
    "delivery_paths": delivery_paths,
    "the_wiim_moment": the_wiim_moment,
    "event_horizon": event_horizon,
    "attention_before_volume": attention_before_volume,
    "who_buys_what": who_buys_what,
    "the_first_meeting": the_first_meeting,
}


def main() -> None:
    for name, build in DIAGRAMS.items():
        path = write(build(), HERE / f"{name}.json")
        print(f"wrote {path.relative_to(Path.cwd()) if path.is_relative_to(Path.cwd()) else path}")


if __name__ == "__main__":
    main()
