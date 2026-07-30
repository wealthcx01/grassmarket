"""Brandfetch product course (GRS-0125, ADR-0028) — a deep, use-case-aligned sell-enablement course,
authored through the GRS-0121 CMS on the GRS-0123 product-course template.

Grounded in public research (July 2026): Brandfetch's site, developer docs, terms, and press. Only
public product facts — no partner-confidential data. Brandfetch has TWO commission tiers in the
Earnings v7 schedule that map to a real commercial split (see the commercial module): distribution
(in-product display/use of brand data — the standard paid API) vs redistribution (passing brand data
to third parties / white-label / reseller — Enterprise custom licensing). The template's commission
lesson resolves the distribution rate LIVE; a bespoke lesson shows both tiers live.

Slug is `product-brandfetch-distribution` (hyphenated — course slugs forbid underscores) so it
counts toward the `product:brandfetch_distribution` certification (GRS-0127). IDs are derived
(uuid5) so re-seeding is idempotent.

Accuracy guardrails baked in (flagged by the research pass): Brandfetch does NOT own the logos —
the buyer carries fair-use / trademark risk; founded 2020 in Switzerland (ignore the "2006" scraper
artifact); no priced VC round is public (only the Adobe Fund for Design grant); the exact
display-vs-redistribute licensing boundary is not publicly bright-lined — confirm per use case.
"""

from __future__ import annotations

from uuid import NAMESPACE_URL, UUID, uuid5

from bcap_contracts.commissions import ProductCommissionCarrot
from bcap_contracts.learning import CourseTree, Lesson, LessonAuthor

from grassmarket.workbench.content.brandfetch_slides import rebuilt_sections
from grassmarket.workbench.content.product_course import ProductCourseSpec, build_product_course

BRANDFETCH_PRODUCT_ID = "brandfetch_distribution"
BRANDFETCH_REDIST_ID = "brandfetch_redistribution"
BRANDFETCH_SLUG = "product-brandfetch-distribution"
_NS = "grassmarket:academy:product-brandfetch"


def _id(kind: str, key: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"{_NS}:{kind}:{key}")


def _pct(bps: int) -> str:
    return f"{bps / 100:g}%"


_TEMPLATE_CHECKS: dict[str, tuple[str, str]] = {
    "relevance": (
        "Across retail brokerage, wealth, and exchange, what gap does Brandfetch fill?",
        "A brand-data / UX gap — recognisable logos and firmographics for onboarding, "
        "holdings dashboards and transaction feeds — recommended against the Platform "
        "Power read, or sold on its own.",
    ),
    "white-label": (
        "How is Brandfetch used under the firm's own brand?",
        "Its logos and brand data are embedded inside the firm's own product surfaces; the "
        "distribution vs redistribution rights are scoped in the contract.",
    ),
    "sell-motion": (
        "What's the Brandfetch sell motion?",
        "Land free with Logo Link, prove the UX lift against an onboarding/engagement gap "
        "the assessment surfaces, then expand into the paid Brand API and Enterprise.",
    ),
    "commission": (
        "How is your Brandfetch commission determined, and over what window?",
        "By the Earnings v7 schedule's rates (distribution and redistribution tiers) for "
        "the attribution window from sale — read live, never a typed-in figure.",
    ),
}


def _two_tier_commission_lesson(
    dist: ProductCommissionCarrot, redist: ProductCommissionCarrot
) -> Lesson:
    """A bespoke lesson showing BOTH live commission tiers side by side (distribution earns more
    than redistribution), resolved from the Earnings v7 schedule — never typed in."""
    body = (
        f"Your live rates for the two models (from the {dist.schedule_version} schedule, not typed "
        f"in): DISTRIBUTION — driving standard in-product API adoption — earns "
        f"**{_pct(dist.yr1_bps)}** in Year 1 and **{_pct(dist.yr2_bps)}** in Year 2. "
        f"REDISTRIBUTION — the enterprise/white-label data pass-through — earns "
        f"**{_pct(redist.yr1_bps)}** ({_pct(redist.yr2_bps)} in Year 2). Distribution pays more "
        f"because it is the self-serve, higher-volume motion you can drive; redistribution is a "
        f"lower-rate, enterprise-negotiated model. Qualify which one a deal is before you forecast "
        f"the commission.\n\n"
        f"The two are also scoped to different segments (GRS-0185), so the sell panel will not "
        f"offer you both on the same report. DISTRIBUTION is for retail brokerages, where the "
        f"motive is keeping the client's own app on-brand. REDISTRIBUTION is for exchanges and "
        f"information vendors, where the motive is licensing brand data onward to their customers "
        f"as part of the reference data they already distribute."
    )
    return Lesson(
        id=_id("lesson", "two-tier-rates"),
        title="Your two commission tiers, live",
        body=body,
        order=99,  # appended to the spine; renumbered on assembly
        author=LessonAuthor.HUMAN,
        drill_topics=("product:brandfetch:tiers",),
        measurement="You can state both live tiers and why distribution pays more than redistrib.",
    )


def brandfetch_course(
    dist_carrot: ProductCommissionCarrot, redist_carrot: ProductCommissionCarrot
) -> CourseTree:
    """Build the deep Brandfetch course: the GRS-0123 template spine (with the distribution carrot's
    live commission) plus four research-grounded modules, including a bespoke two-tier commission
    lesson that shows both the distribution and redistribution rates live."""
    spec = ProductCourseSpec(
        product_id=BRANDFETCH_PRODUCT_ID,
        slug=BRANDFETCH_SLUG,
        display_name="Brandfetch",
        relevance=(
            "Brandfetch is the brand-data platform (logos, colours, fonts, firmographics "
            "for 50M+ companies) with a Brand API that looks up a company by domain, ticker, ISIN "
            "or crypto symbol. Relevant to a retail broker or wealth platform (branded holdings / "
            "onboarding UIs), and to a fintech/exchange (transaction-feed merchant enrichment) — a "
            "solution against a client-experience / data-quality gap the assessment surfaces, or a "
            "commission product in its own right."
        ),
        white_label=(
            "Embedding Brandfetch data as DISPLAY inside a client-facing product is permitted on "
            "the standard paid tier (hotlinked logos, brand records in your UI, no attribution). A "
            "true white-label or reseller model that passes the brand DATA to third parties is "
            "redistribution — barred under the standard licence and available only via Enterprise "
            "custom licensing (the lower commission tier). Note: Brandfetch does not own the logos "
            "— the firm carries the trademark/fair-use compliance."
        ),
        sell_motion=(
            "Land with a free Logo Link / Brand Search demo, expand to the paid "
            "Brand API as usage grows, and lead the finance pitch with the ticker/ISIN lookup and "
            "the Transaction API — the two things generic logo APIs can't match. Qualify "
            "distribution vs redistribution early, because it sets both the licence and your "
            "commission tier."
        ),
    )
    base = build_product_course(
        spec, dist_carrot, _TEMPLATE_CHECKS
    )  # spine incl. the live distribution commission
    # The GRS-0217 rebuild. Eight sections to the GRS-0215 depth standard: 192 slides, 48 test
    # questions, one diagram per section, organised around the distribution/redistribution boundary
    # because that boundary is what the founder corrected us on (GRS-0185). They come FIRST: they
    # are the course now.
    rebuilt = rebuilt_sections()

    # The four "superseded reference" modules that used to live in this file are GONE (2026-07-30),
    # on the same decision as OpenBB's and Benzinga's: they were kept only so the course would not
    # be thinner while the rebuild was in flight, and four locked modules of paragraph-lessons at
    # the end of a finished course is the "basic" the founder objected to, still shipping.
    #
    # `_two_tier_commission_lesson` is NOT superseded and is kept. It resolves BOTH live rates from
    # the Earnings schedule, which is the one thing the slides deliberately cannot do — no rate is
    # written into course content anywhere. It moves onto the spine, where the commission lesson
    # already lives, rather than keeping a module alive around it.
    spine = base.modules[0]
    spine_with_tiers = spine.model_copy(
        update={
            "lessons": tuple(spine.lessons)
            + (_two_tier_commission_lesson(dist_carrot, redist_carrot),)
        }
    )

    # One sequence, numbered once (see GRS-0226: the unlock rule reads `order`, so reading order is
    # the only authority on section number).
    assembled = rebuilt + (spine_with_tiers,) + tuple(base.modules[1:])
    numbered = tuple(m.model_copy(update={"order": i}) for i, m in enumerate(assembled))
    return base.model_copy(update={"modules": numbered})
