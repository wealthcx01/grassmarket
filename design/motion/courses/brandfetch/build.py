"""Build the Brandfetch course diagrams (GRS-0225 toolchain, GRS-0217 content).

    uv run python design/motion/courses/brandfetch/build.py

Writes one JSON scene per diagram. Compiling and rendering is `design/motion/render.sh`, which runs
rive-cli over every scene here and refuses a blank frame.

Same rule as the other two sets: a diagram exists because the idea it carries is spatial rather than
verbal. Brandfetch's defining problem is a *boundary* — the line between displaying brand data in
your own product and passing it on to your customers. That line decides the licence, the segment,
the contract and the commission, and it is not publicly bright. A boundary is the most spatial idea
there is, which is why the highest-value drawing here is `two_licences`.
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


# --- 1. Two sides of one platform (section 1) ----------------------------------------------


def two_sides() -> dict:
    """Why the data is good, drawn. Every competitor scrapes; Brandfetch has brands claim and
    verify their own profile, and the API serves what they claimed. The flywheel is the moat, and
    an advisor who cannot explain it has nothing to say to "why not just scrape it?".

    Deliberately NOT the two-panel layout used for OpenBB and Benzinga: those two diagrams compare
    two things you must not confuse, and this one shows one thing feeding another. Same grammar for
    the same idea, a different grammar for a different idea."""
    return scene(
        "TwoSides",
        960,
        440,
        stack(
            text("Title", 480, 46, "One registry, two sides", 30, INK),
            text(
                "Sub",
                480,
                80,
                "The brands maintain it. That is why the data is current.",
                16,
                MUTED,
            ),
            # Left: the public registry
            text("LeftName", 230, 168, "The public registry", 21, INK),
            text("LeftA", 230, 210, "a company claims its own", 15, MUTED),
            text("LeftB", 230, 234, "profile and verifies it", 15, MUTED),
            text("LeftC", 230, 274, "logos, colours, fonts,", 15, MUTED),
            text("LeftD", 230, 298, "firmographics", 15, MUTED),
            # Right: the API you sell
            text("RightName", 730, 168, "The developer API", 21, ON_GREEN),
            text("RightA", 730, 210, "one identifier in,", 15, ON_GREEN_MUTED),
            text("RightB", 730, 234, "brand identity out", 15, ON_GREEN_MUTED),
            text("RightC", 730, 274, "this is what you sell", 15, SIGNAL),
            *arrow_right("Feed", 480, 240, 120, MUTED),
            card("LeftCard", 230, 240, 380, 200, PAPER, stroke=RULE),
            card("RightCard", 730, 240, 380, 200, GREEN),
            text(
                "Foot",
                480,
                398,
                "A scraper has no one maintaining it. That is the whole argument.",
                16,
                MUTED,
            ),
            card("Bg", 480, 220, 960, 440, PAPER, radius=0),
        ),
    )


# --- 2. The boundary that decides everything (section 2) -----------------------------------


def two_licences() -> dict:
    """The highest-value drawing in this course, and the one the founder's correction is about: we
    were conflating two products that differ in licence, segment, contract shape and commission.

    Drawn as a vertical boundary with the client's own product on the left and the client's
    customers on the right, because that is literally what the line is: does the brand data stop
    inside their app, or does it travel further? Everything else follows from which side you are on,
    so the drawing puts the consequences under each side rather than describing them in prose.

    No rates. The commission resolves live from the Earnings schedule; a figure drawn into a
    diagram is a figure that goes stale silently and gets quoted anyway."""
    left = [
        ("Shown inside their", "own product"),
        ("Standard paid API,", "self-serve"),
        ("Retail brokerages", ""),
    ]
    right = [
        ("Passed on to their", "customers"),
        ("Enterprise custom", "licensing only"),
        ("Exchanges and", "information vendors"),
    ]
    # The label column gets its own space. The first cut centred it at x=100 with the left panel
    # starting at x=80, so every row label straddled the panel's edge — and the divider is centred
    # between the two PANELS rather than on the artboard, which is what makes that possible.
    rows = [("WHERE THE DATA GOES", 210), ("WHAT LICENCE", 288), ("WHO BUYS IT", 366)]
    layers: list = []
    for i, ((la, lb), (ra, rb)) in enumerate(zip(left, right, strict=True)):
        y = rows[i][1]
        layers.append(text(f"L{i}a", 420, y - 11, la, 16, INK))
        if lb:
            layers.append(text(f"L{i}b", 420, y + 11, lb, 16, INK))
        layers.append(text(f"R{i}a", 900, y - 11, ra, 16, ON_GREEN))
        if rb:
            layers.append(text(f"R{i}b", 900, y + 11, rb, 16, ON_GREEN_MUTED))
    for label, y in rows:
        layers.append(text(f"Row{y}", 108, y, label, 11, MUTED, letter_spacing=1.2))
    return scene(
        "TwoLicences",
        1180,
        500,
        stack(
            text("Title", 660, 46, "One boundary decides the whole deal", 30, INK),
            # Both headings sit on PAPER, above their cards, so both must be readable on paper.
            # ON_GREEN is a near-white for use ON the green card; on paper it is invisible, which is
            # exactly how the first render lost the word REDISTRIBUTION entirely.
            text("HeadL", 420, 138, "DISTRIBUTION", 18, INK, letter_spacing=1.4),
            text("HeadR", 900, 138, "REDISTRIBUTION", 18, GREEN, letter_spacing=1.4),
            *layers,
            card("RightPanel", 900, 288, 420, 260, GREEN),
            card("LeftPanel", 420, 288, 420, 260, GREEN_TINT, stroke=RULE),
            line("Divide", 660, 288, 2, 300, INK),
            text(
                "Warn",
                660,
                462,
                "The line is not publicly bright-lined. Never decide it yourself.",
                17,
                WARN,
            ),
            card("Bg", 590, 250, 1180, 500, PAPER, radius=0),
        ),
    )


# --- 3. The land-and-expand ladder (section 3) ---------------------------------------------


def four_surfaces() -> dict:
    """Four products, and the order you meet them in. Drawn as a rising ladder because the
    commercial motion is a sequence, not a menu: the free surfaces exist to get you in the room,
    and the paid ones are where the deal is. An advisor who leads with the free image URL has
    demonstrated the product and sold nothing.

    Heights encode commitment, which is the one thing a list cannot show."""
    steps = [
        # Sub-labels kept short on purpose: at 13px in a 196-wide card, "descriptors to merchants"
        # overflowed its own box in the first render. The card is the constraint, not the sentence.
        ("Logo", "Logo Link", "an image URL", "free tier", 150, 70),
        ("Search", "Brand Search", "a type-ahead", "free tier", 370, 110),
        ("Brand", "Brand API", "identity by ticker", "paid", 590, 160),
        ("Txn", "Transaction API", "messy descriptors", "enterprise", 810, 210),
    ]
    baseline = 372
    layers: list = []
    for name, title, what, tier, x, height in steps:
        top = baseline - height
        accent = tier != "free tier"
        layers.append(text(f"{name}T", x, top + 30, title, 17, ON_GREEN if accent else INK))
        layers.append(text(f"{name}W", x, top + 56, what, 13, ON_GREEN_MUTED if accent else MUTED))
        layers.append(text(f"{name}Tier", x, baseline + 26, tier, 13, GREEN if accent else MUTED))
        layers.append(
            card(
                f"{name}Card",
                x,
                baseline - height / 2,
                196,
                height,
                GREEN if accent else GREEN_TINT,
                stroke=None if accent else RULE,
            )
        )
    return scene(
        "FourSurfaces",
        960,
        470,
        stack(
            text("Title", 480, 44, "Land free, expand into the paid data", 30, INK),
            text("Sub", 480, 78, "Height is commitment, not price.", 16, MUTED),
            *layers,
            # Spans the bars, not an arbitrary width: the first cut ended the rule
            # mid-way through the last bar.
            line("Base", 480, baseline, 860, 2, INK),
            text(
                "Foot",
                480,
                430,
                "Demo the free surface. Sell the paid one. They are not the same conversation.",
                16,
                MUTED,
            ),
            card("Bg", 480, 235, 960, 470, PAPER, radius=0),
        ),
    )


# --- 4. The identifier hook (section 4) ----------------------------------------------------


def the_ticker_hook() -> dict:
    """The single most sellable fact in the product, and it is spatial: four different keys, one
    endpoint, one shape of answer. A generic logo API takes a domain and nothing else, which is
    exactly the wrong key for a system whose records are held by ticker or ISIN.

    Four inputs converging on one output is a funnel, so it is drawn as one."""
    keys = [
        ("Dom", "a domain", "nike.com", 148),
        ("Tick", "a stock ticker", "NKE", 222),
        ("Isin", "an ISIN", "US6541061031", 296),
        ("Crypto", "a crypto symbol", "BTC", 370),
    ]
    layers: list = []
    for name, label, example, y in keys:
        layers.append(text(f"{name}L", 190, y - 10, label, 15, INK))
        layers.append(text(f"{name}E", 190, y + 12, example, 13, MUTED))
        layers.append(card(f"{name}Card", 190, y, 300, 62, GREEN_TINT, stroke=RULE))
        layers.extend(arrow_right(f"{name}Arrow", 425, y, 90, MUTED))
    return scene(
        "TheTickerHook",
        1000,
        500,
        stack(
            text("Title", 500, 44, "Four keys, one endpoint", 30, INK),
            text(
                "Sub",
                500,
                78,
                "Your client's records are keyed by ticker or ISIN, not by domain.",
                16,
                MUTED,
            ),
            *layers,
            # The single output
            text("OutT", 745, 210, "One brand identity", 20, ON_GREEN),
            text("Out1", 745, 248, "logo in every variant", 14, ON_GREEN_MUTED),
            text("Out2", 745, 272, "colours and fonts", 14, ON_GREEN_MUTED),
            text("Out3", 745, 296, "firmographics", 14, ON_GREEN_MUTED),
            card("OutCard", 745, 259, 330, 150, GREEN),
            text(
                "Foot",
                500,
                452,
                "A generic logo API takes a domain. That is the wrong key for a holdings table.",
                16,
                MUTED,
            ),
            card("Bg", 500, 250, 1000, 500, PAPER, radius=0),
        ),
    )


# --- 5. The retail surface, before and after (section 5) -----------------------------------


def holdings_before_after() -> dict:
    """Distribution's value in one picture: the same holdings table, unbranded and branded. This is
    the demo an advisor should be able to describe from memory, because it is the entire pitch for
    the retail segment and it takes one sentence plus this drawing.

    Same before/after grammar as Benzinga's `the_wiim_moment`, on purpose — the two products solve
    the same shape of problem on the same screen, and an advisor who has learned one layout should
    recognise the other instantly."""
    rows = [("NKE", 172), ("MSFT", 216), ("VOD.L", 260)]
    layers: list = []
    for tickr, y in rows:
        layers.append(text(f"L{tickr}", 250, y, tickr, 16, MUTED))
        layers.append(card(f"LMark{tickr}", 640, y, 22, 22, GREEN, radius=5))
        layers.append(text(f"R{tickr}", 700, y, tickr, 16, INK))
    return scene(
        "HoldingsBeforeAfter",
        960,
        420,
        stack(
            text("Title", 480, 44, "The same holdings table", 30, INK),
            text("HeadL", 250, 118, "WITHOUT", 12, MUTED, letter_spacing=1.6),
            text("HeadR", 700, 118, "WITH", 12, GREEN, letter_spacing=1.6),
            *layers,
            text("LNote", 250, 314, "a wall of symbols", 15, MUTED),
            text("RNote", 700, 314, "scannable in one look", 15, INK),
            card("LeftCard", 250, 216, 340, 216, PAPER, stroke=RULE),
            card("RightCard", 700, 216, 340, 216, GREEN_TINT, stroke=GREEN),
            text(
                "Foot",
                480,
                382,
                "One image URL keyed on the ticker. This is the whole retail demo.",
                16,
                MUTED,
            ),
            card("Bg", 480, 210, 960, 420, PAPER, radius=0),
        ),
    )


# --- 6. Brand identity as a redistributed field (section 6) --------------------------------


def reference_data_shelf() -> dict:
    """Redistribution reframed as something an exchange or vendor already does. They ship reference
    data to their customers every day; brand identity is one more field on that record. Put that
    way it needs no explaining, and it also makes obvious why the licence has to be different — the
    data leaves their building.

    Drawn as a record with fields, one of which is new and highlighted, and an arrow leaving the
    boundary. The arrow crossing the edge IS the licence question."""
    fields = [
        ("Isin", "ISIN", False, 168),
        ("Name", "legal name", False, 206),
        ("Sedol", "SEDOL, MIC, currency", False, 244),
        ("Brand", "brand identity", True, 282),
    ]
    layers: list = []
    for name, label, new, y in fields:
        layers.append(text(f"{name}L", 250, y, label, 16, ON_GREEN if new else INK))
        if new:
            layers.append(card(f"{name}Row", 250, y, 320, 32, GREEN, radius=6))
    return scene(
        "ReferenceDataShelf",
        980,
        440,
        stack(
            text("Title", 490, 44, "One more field on a record they already ship", 30, INK),
            text(
                "Sub",
                490,
                78,
                "An exchange or vendor redistributes reference data every day.",
                16,
                MUTED,
            ),
            text("Card1", 250, 128, "THEIR REFERENCE RECORD", 11, MUTED, letter_spacing=1.2),
            *layers,
            card("RecordCard", 250, 225, 360, 220, PAPER, stroke=RULE),
            *arrow_right("Out", 560, 225, 130, GREEN),
            text("CustT", 800, 200, "Their customers", 19, INK),
            text("CustA", 800, 240, "the data leaves", 15, MUTED),
            text("CustB", 800, 264, "their building", 15, MUTED),
            card("CustCard", 800, 225, 260, 160, GREEN_TINT, stroke=RULE),
            text(
                "Warn",
                490,
                398,
                "That arrow is the licence question. It is why this tier exists.",
                17,
                WARN,
            ),
            card("Bg", 490, 220, 980, 440, PAPER, radius=0),
        ),
    )


# --- 7. Who owns the mark (section 7) ------------------------------------------------------


def who_owns_the_mark() -> dict:
    """The compliance landmine, and the one an advisor is most likely to walk a regulated client
    onto. Three parties, and the risk does not sit where a buyer assumes.

    Drawn as three boxes in a row with the risk marked on the one that carries it, because the
    misconception is precisely about *position*: buyers assume that paying a vendor for access
    transfers the vendor's rights, and it does not."""
    return scene(
        "WhoOwnsTheMark",
        1000,
        440,
        stack(
            text("Title", 500, 46, "Three parties, and the risk is not where they think", 30, INK),
            text("OwnT", 180, 178, "The trademark", 18, INK),
            text("OwnT2", 180, 202, "owner", 18, INK),
            text("OwnB", 180, 246, "owns the mark", 14, MUTED),
            text("BfT", 500, 178, "Brandfetch", 18, INK),
            text("BfB", 500, 224, "provides access", 14, MUTED),
            text("BfB2", 500, 248, "to it", 14, MUTED),
            text("CliT", 820, 178, "Your client", 18, ON_GREEN),
            text("CliB", 820, 224, "carries the", 14, ON_GREEN_MUTED),
            text("CliB2", 820, 248, "fair-use risk", 14, ON_GREEN_MUTED),
            *arrow_right("A1", 340, 212, 100, MUTED),
            *arrow_right("A2", 660, 212, 100, MUTED),
            card("OwnCard", 180, 212, 260, 170, GREEN_TINT, stroke=RULE),
            card("BfCard", 500, 212, 260, 170, PAPER, stroke=RULE),
            card("CliCard", 820, 212, 260, 170, GREEN),
            text(
                "Warn",
                500,
                348,
                "Paying for access does not transfer anybody's rights.",
                18,
                WARN,
            ),
            text(
                "Foot",
                500,
                396,
                "Say this before the compliance officer asks. It stays a short conversation.",
                15,
                MUTED,
            ),
            card("Bg", 500, 220, 1000, 440, PAPER, radius=0),
        ),
    )


# --- 8. Qualify before you forecast (section 8) --------------------------------------------


def qualify_before_you_forecast() -> dict:
    """The commission mistake, drawn as a decision rather than a table. The two tiers pay different
    rates over different windows, so an advisor who forecasts before qualifying which licence a
    deal is has forecast the wrong number.

    Deliberately carries NO rates and NO window lengths. Both live in the Earnings schedule and
    both resolve live; a figure drawn into a diagram is a figure that goes stale silently and gets
    quoted anyway. The drawing teaches the ORDER: qualify, then look it up."""
    return scene(
        "QualifyBeforeYouForecast",
        1000,
        420,
        stack(
            text("Title", 500, 46, "Qualify the licence before you forecast", 30, INK),
            text("Q", 500, 130, "Does the data leave the client's own product?", 21, INK),
            card("QBox", 500, 130, 560, 58, PAPER, stroke=INK, thickness=2),
            text("NoL", 300, 186, "No", 15, MUTED),
            text("YesL", 700, 186, "Yes", 15, MUTED),
            text("LeftT", 270, 246, "Distribution", 19, INK),
            text("LeftB", 270, 278, "standard paid API", 14, MUTED),
            text("RightT", 730, 246, "Redistribution", 19, ON_GREEN),
            text("RightB", 730, 278, "enterprise licensing", 14, ON_GREEN_MUTED),
            card("LeftBox", 270, 262, 300, 100, GREEN_TINT, stroke=RULE),
            card("RightBox", 730, 262, 300, 100, GREEN),
            *arrow_down("DownL", 270, 176, 36, MUTED),
            *arrow_down("DownR", 730, 176, 36, MUTED),
            # GREEN, not SIGNAL. SIGNAL is the light "do this" green for use ON the dark card;
            # on paper it is barely legible, which is how the first render of this line came out.
            text(
                "Rule",
                500,
                348,
                "Different rate, different window. Read yours off the Earnings page.",
                17,
                GREEN,
            ),
            text(
                "Foot",
                500,
                390,
                "Never from memory, and never from a slide: the schedule is the only source.",
                15,
                MUTED,
            ),
            card("Bg", 500, 210, 1000, 420, PAPER, radius=0),
        ),
    )


DIAGRAMS = {
    "two_sides": two_sides,
    "two_licences": two_licences,
    "four_surfaces": four_surfaces,
    "the_ticker_hook": the_ticker_hook,
    "holdings_before_after": holdings_before_after,
    "reference_data_shelf": reference_data_shelf,
    "who_owns_the_mark": who_owns_the_mark,
    "qualify_before_you_forecast": qualify_before_you_forecast,
}


def main() -> None:
    for name, build in DIAGRAMS.items():
        path = write(build(), HERE / f"{name}.json")
        print(f"wrote {path.relative_to(Path.cwd()) if path.is_relative_to(Path.cwd()) else path}")


if __name__ == "__main__":
    main()
