"""OpenBB product course assembly (GRS-0126, rebuilt by GRS-0216; ADR-0028).

**This module is now assembly only.** The course content lives in `openbb_slides.py` — eight
sections rebuilt to the GRS-0215 depth standard, 196 slides, one section test each. What is left
here is the `ProductCourseSpec` for the GRS-0123 template spine (relevance, white-label, sell
motion, and the commission lesson that resolves LIVE from the Earnings v7 schedule) plus the
ordering of the two.

The four "superseded reference" modules that used to live in this file — roughly 370 lines of
paragraph-lessons from 2026-07 — were **deleted on 2026-07-30**, alongside Benzinga's. They were
kept while the rebuild was in flight so the course would not be thinner in the meantime; once all
eight sections existed they were four locked modules of exactly the "basic" content the founder
objected to, still shipping.

Two anchors from the original research pass went with them, and that was a decision rather than an
oversight: **MCP** was not colour — the Workspace MCP endpoint letting the firm's existing agents
work over governed data is the sharpest enterprise hook in the product — so it was written into
rebuilt section 1. "Gamestonk" (the sunset free terminal's origin) and "Snowflake" (one named
example of connecting an internal database) were colour; the pivot is covered by the two-products
slide and the Bloomberg positioning, and internal-database connection is covered generically.
`test_content_covers_the_key_sellable_facts` records which is which.

Slug is `product-openbb` so completing the course counts toward the `product:openbb` certification
(GRS-0127).
"""

from __future__ import annotations

from bcap_contracts.commissions import ProductCommissionCarrot
from bcap_contracts.learning import CourseTree

from grassmarket.workbench.content.openbb_slides import rebuilt_sections
from grassmarket.workbench.content.product_course import ProductCourseSpec, build_product_course

OPENBB_PRODUCT_ID = "openbb"
OPENBB_SLUG = "product-openbb"


# (key, title, body, drill_topic, measurement) for each deep lesson. Bodies are grounded in the
# public research; keep them factual, not hype.
_TEMPLATE_CHECKS: dict[str, tuple[str, str]] = {
    "relevance": (
        "Across retail brokerage, wealth, and exchange, what gap does OpenBB fix?",
        "A research/data-infrastructure/AI-governance gap: research tooling for a broker, branded "
        "client reporting + governed AI for a wealth manager, vendor-agnostic consolidation for an "
        "exchange/data team — recommended against the Platform Power read, or sold on its own.",
    ),
    "white-label": (
        "Where does OpenBB white-labelling happen, and where must it NOT?",
        "In the proprietary Workspace (brand the UI, ship apps.json apps, custom widgets, custom "
        "backend) — NOT by forking the AGPLv3 Platform, which would trigger source disclosure "
        "without the commercial license.",
    ),
    "sell-motion": (
        "What do you lead with — and explicitly not — when selling OpenBB?",
        "Lead with governed AI over the firm's own data and vendor-agnostic consolidation; NOT "
        "'Bloomberg killer'. Qualify on a real data/AI-governance gap, demo on the client's own "
        "data, price on seat-reduction + IP-ownership + AI-governance.",
    ),
    "commission": (
        "How is the commission you earn on OpenBB determined, and over what window?",
        "By the Earnings v7 schedule's Year-1 / Year-2 rates for the attribution window from sale —"
        "read live from the schedule, never a typed-in figure, so the carrot always matches the "
        "real"
        "rate. Sold as an assessment-gap fix or a commission product in its own right.",
    ),
}


def openbb_course(carrot: ProductCommissionCarrot) -> CourseTree:
    """Build the deep OpenBB course: the GRS-0123 template spine (relevance / white-label /
    sell-motion / live commission) plus four research-grounded modules. The `carrot` must be for
    the 'openbb' product so the commission lesson resolves live."""
    spec = ProductCourseSpec(
        product_id=OPENBB_PRODUCT_ID,
        slug=OPENBB_SLUG,
        display_name="OpenBB",
        relevance=(
            "OpenBB is an open-source financial-data + enterprise AI research workspace. Relevant "
            "to a retail broker (research tooling), a wealth manager (branded client reporting + "
            "governed AI), and an exchange/data team (vendor-agnostic consolidation) — a solution "
            "you recommend against a research / data-infrastructure / AI-governance gap the "
            "Platform Power assessment surfaces, or sold as a commission product in its own right."
        ),
        white_label=(
            "White-labelling happens in the proprietary OpenBB Workspace (brand the UI, ship "
            "`apps.json` apps, embed custom/HTML widgets, plug in the firm's own data via a custom "
            "backend) — NOT by forking the AGPLv3 open-source Platform. A genuinely client-facing "
            "or hosted build on the open-source code needs OpenBB's commercial license "
            "(licensing@openbb.co) to escape AGPL's source-disclosure obligation."
        ),
        sell_motion=(
            "Lead with governed AI over the firm's own data and vendor-agnostic consolidation "
            "(where OpenBB is strongest), NOT 'Bloomberg killer'. Qualify on a real "
            "data/AI-governance gap, run a scoped Workspace demo on the client's own data, and "
            "price on seat-reduction + IP-ownership + AI-governance — the cost is always a scoped "
            "quote."
        ),
    )
    base = build_product_course(
        spec,
        carrot,
        _TEMPLATE_CHECKS,
        # GRS-0239 scope 4: these two tail paragraphs are retired because this course's rebuilt
        # sections cover them at depth — `who-buys-and-why` and `how-and-when-to-sell`.
        covered_by_rebuilt=frozenset({"relevance", "sell-motion"}),
    )  # 1 module (4 canonical sections incl. live commission)

    # The GRS-0216 rebuild. These sections are written to the GRS-0215 depth standard: a lesson of
    # 20 to 40 slides and a test the advisor passes before the next section opens. They come FIRST,
    # because they are the course now.
    rebuilt = rebuilt_sections()

    # Two sources, one sequence. Each numbered itself from zero, which once put the canonical
    # product module on the same `order` as the first rebuilt section. The unlock rule reads
    # `order`, so that duplicate opened section 2 to an advisor who had passed nothing — the gate
    # was reading a tie. Reading order is the only authority on section number, so it is applied
    # here, once, to the assembled tree rather than guessed at by each source.
    #
    # The four "superseded reference" modules that used to sit at the end are GONE (2026-07-30).
    # They were kept so the course would not be thinner while the rebuild was in flight; the eight
    # rebuilt sections replace them completely, and four locked modules of paragraph-lessons at the
    # end of a finished course is exactly the "basic" the founder objected to, still shipping. Their
    # lesson ids are not reused, so any historical completion rows simply no longer match a lesson
    # in the tree — harmless, because completeness is a subset check over the CURRENT tree.
    assembled = rebuilt + base.modules
    numbered = tuple(m.model_copy(update={"order": i}) for i, m in enumerate(assembled))
    return base.model_copy(update={"modules": numbered})
