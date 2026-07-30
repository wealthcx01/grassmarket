"""Benzinga product course assembly (GRS-0124, rebuilt by GRS-0217; ADR-0028).

**This module is now assembly only.** The course content lives in `benzinga_slides.py` — eight
sections rebuilt to the GRS-0215 depth standard, 192 slides, one section test each. What is left
here is the `ProductCourseSpec` for the GRS-0123 template spine (relevance, sell motion, and the
commission lesson that resolves LIVE from the Earnings v7 schedule) plus the ordering of the two.

The four "superseded reference" modules that used to live in this file — roughly 300 lines of
paragraph-lessons from 2026-07 — were **deleted on 2026-07-30**. They were kept while the rebuild
was in flight so the course would not be thinner in the meantime; once all eight sections existed
they were four locked modules of exactly the "basic" content the founder objected to, still
shipping. The research anchors they carried that were genuinely sellable (Raznick, the Beringer
figure, the alpha caveat, redistribution) were written into the rebuilt slides instead, and
`test_content_covers_the_key_facts_and_caveats` asserts they are still there.

Slug is `product-benzinga` so completing the course counts toward the `product:benzinga` cert
(GRS-0127). The accuracy guardrails from the original research pass now live at the top of
`benzinga_slides.py`, beside the content they constrain.
"""

from __future__ import annotations

from bcap_contracts.commissions import ProductCommissionCarrot
from bcap_contracts.learning import CourseTree

from grassmarket.workbench.content.benzinga_slides import rebuilt_sections
from grassmarket.workbench.content.product_course import ProductCourseSpec, build_product_course

BENZINGA_PRODUCT_ID = "benzinga"
BENZINGA_SLUG = "product-benzinga"


_TEMPLATE_CHECKS: dict[str, tuple[str, str]] = {
    "relevance": (
        "Across retail brokerage, wealth, and exchange, what gap does Benzinga fill?",
        "A market-content / engagement gap — news, ratings and signals to enrich ticker pages, "
        "advisor portals and apps — recommended against the Platform Power read, or sold on "
        "its own.",
    ),
    "white-label": (
        "How is Benzinga white-labelled?",
        "By embedding its licensed feeds under the firm's own brand in the firm's surfaces "
        "(portals, apps, ticker pages) — the redistribution rights are scoped in the contract.",
    ),
    "sell-motion": (
        "What do you lead with when selling Benzinga?",
        "A real engagement/market-content gap: run the assessment, show how a fresh news/ratings/"
        "signals layer lifts engagement, and scope the redistribution/attribution per deal.",
    ),
    "commission": (
        "How is your Benzinga commission determined, and over what window?",
        "By the Earnings v7 schedule's Year-1 / Year-2 advisor rates for the attribution window "
        "from sale — read live from the schedule, never a typed-in figure.",
    ),
}


def benzinga_course(carrot: ProductCommissionCarrot) -> CourseTree:
    """Build the deep Benzinga course: the GRS-0123 template spine (with the live advisor
    commission) plus four research-grounded modules. The `carrot` must be for 'benzinga'."""
    spec = ProductCourseSpec(
        product_id=BENZINGA_PRODUCT_ID,
        slug=BENZINGA_SLUG,
        display_name="Benzinga",
        relevance=(
            "Benzinga licenses real-time financial news, analyst ratings, event calendars and "
            "options signals as embeddable APIs. Relevant to a retail broker (news + ratings + "
            "signals on ticker pages), a wealth platform (analyst context in the client portal), "
            "and a fintech/exchange (engagement feed + quant signals) — a solution against a "
            "product-depth / engagement / data gap the assessment surfaces, or a commission "
            "product in its own right."
        ),
        white_label=(
            "Redistribution is Benzinga's core model — brokerages embed its feeds and display them "
            "to their own end-users at scale. But white-label / re-branding, attribution ('Powered "
            "by Benzinga'), per-end-user entitlements and territory are all set in the enterprise "
            "contract (not the public/marketplace tiers). Sell the capability; scope the rights to "
            "the signed contract — do not promise a buyer they can strip attribution or "
            "redistribute freely until it is confirmed in writing."
        ),
        sell_motion=(
            "Land with the free Basic News API (a low-friction prototype), lead the pitch with "
            "WIIM and the analyst-ratings + options-signals feeds (Benzinga's differentiators), "
            "and pair it honestly with a quotes/fundamentals vendor where the buyer needs depth. "
            "Position it as the engagement + context layer at fintech pricing, not a terminal. "
            "Enterprise pricing is a scoped quote via licensing@benzinga.com."
        ),
    )
    base = build_product_course(
        spec, carrot, _TEMPLATE_CHECKS
    )  # spine incl. the live advisor commission (15%)
    # The GRS-0217 rebuild. Written to the GRS-0215 depth standard: a lesson of 20 to 40 slides and
    # a test the advisor passes before the next section opens. These come FIRST, because they are
    # the course now. All eight sections are written (2026-07-30): 192 slides, 48 test questions,
    # one diagram per section, every product claim traceable to the committed catalogue.
    rebuilt = rebuilt_sections()

    # One sequence, numbered once. Each source numbers itself from zero, and the unlock rule reads
    # `order`, so reading order is applied here rather than guessed at per source (see GRS-0226).
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
