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
from bcap_contracts.learning import CourseModule, CourseTree, Lesson, LessonAuthor

from grassmarket.workbench.content.product_course import ProductCourseSpec, build_product_course

BRANDFETCH_PRODUCT_ID = "brandfetch_distribution"
BRANDFETCH_REDIST_ID = "brandfetch_redistribution"
BRANDFETCH_SLUG = "product-brandfetch-distribution"
_NS = "grassmarket:academy:product-brandfetch"


def _id(kind: str, key: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"{_NS}:{kind}:{key}")


def _pct(bps: int) -> str:
    return f"{bps / 100:g}%"


_WHAT_IT_IS: tuple[tuple[str, str, str, str, str], ...] = (
    (
        "platform",
        "The brand-data platform",
        "Brandfetch is the internet's largest brand-data platform — a single, always-current "
        "index of tens of millions of companies (they say 50M+) and their brand identity: logos "
        "in every variant/format, colour palettes, fonts, description, and firmographics "
        "(employees, founded year, HQ, industry, social links). It has two sides: a public "
        "brand directory where a company claims and verifies its own profile (the quality moat "
        "vs scraping), and the developer API layer you sell to fintechs — give it an "
        "identifier, get a company's polished brand identity to display in your own app.",
        "product:brandfetch:platform",
        "You can explain the directory-plus-API model and why first-party verification matters.",
    ),
    (
        "brand-api",
        "The Brand API — the finance hook",
        "The flagship data product: send one identifier and get a structured JSON object with "
        "the company's full identity. Uniquely for finance it accepts not just a domain but a "
        "stock TICKER, an ISIN, an ETF ticker, or a crypto symbol as the lookup key — e.g. "
        "api.brandfetch.io/v2/brands/ticker/NKE or .../isin/US6541061031. That ticker/ISIN "
        "lookup is the single most sellable thing a generic logo API cannot match: it maps "
        "straight onto holdings, watchlists and research screens keyed by ticker or ISIN.",
        "product:brandfetch:brand-api",
        "You can name the four Brand API lookup keys (domain, ticker, ISIN, crypto).",
    ),
    (
        "logo-search",
        "Logo Link & Brand Search — the low-friction land",
        "Two easy-adopt surfaces that get a foot in the door. Logo Link is a pure image CDN URL "
        "keyed by domain (or ticker/ISIN) — drop cdn.brandfetch.io/nike.com into an <img> tag "
        "and the logo stays current forever, free up to ~500k requests/month, no attribution. "
        "Brand Search API is type-ahead company autocomplete (returns domain + logo + colours "
        "per keystroke), also free to ~500k/month. These are the demo-in-five-minutes products "
        "that land the account before the paid Brand API expands it.",
        "product:brandfetch:logo-search",
        "You can demo Logo Link in an <img> tag and explain the land-and-expand motion.",
    ),
    (
        "transaction-api",
        "The Transaction API — the fintech expansion",
        "The newest, most fintech-specific product (Enterprise tier): it turns raw, cryptic "
        "bank/card statement descriptors into clean merchant brand data. Send 'STARBUCKS 1523 "
        "OMAHA NE' + a country code and get Starbucks back — name, domain, logo, industry, "
        "metadata — resolving merchants worldwide in real time. This is the answer to messy "
        "transaction feeds and is squarely aimed at neobanks, budgeting apps, and card-issuing "
        "fintechs; Envestnet | Yodlee used Brandfetch to improve exactly this "
        "merchant-identification problem.",
        "product:brandfetch:transaction-api",
        "You can explain the Transaction API's descriptor→merchant job and who buys it.",
    ),
)

_USE_CASES: tuple[tuple[str, str, str, str, str], ...] = (
    (
        "onboarding-kyb",
        "Sell it for: KYB / client onboarding UIs",
        "Onboarding a corporate client means typing a company name into a bare form — no visual "
        "confirmation, more errors, more drop-off. Brand Search powers a type-ahead company "
        "picker with logos; on selection, the Brand API pulls domain, HQ, industry and identity "
        "to pre-fill and visually confirm the entity. Typeform reported a 5% free-to-paid lift "
        "adding Brandfetch to onboarding. Buyer: fintech onboarding/KYB teams, business "
        "banking, neobanks. Tie to the assessment: the fix for an onboarding-friction or "
        "conversion gap a Platform Power read surfaces in a **retail brokerage** or fintech.",
        "product:brandfetch:uc-onboarding",
        "You can connect the onboarding picker to a conversion gap in the assessment.",
    ),
    (
        "portfolio-dashboards",
        "Sell it for: portfolio & watchlist dashboards",
        "Holdings tables are walls of tickers and ISINs — hard to scan, visually flat. The "
        "Brand API's ticker/ISIN/crypto lookup returns each issuer's logo and identity, so "
        "every holding shows its brand mark; Logo Link does it with one <img> URL keyed on the "
        "ticker. Morningstar uses Brandfetch to keep financial-institution assets current in "
        "its product. Buyer: wealth platforms, brokerages, robo-advisors, research/analytics "
        "tools. Tie to the assessment: a polish/branding layer that deepens a **wealth** "
        "client-facing surface a brand or switching-cost finding is pricing.",
        "product:brandfetch:uc-portfolio",
        "You can pitch ticker/ISIN logo lookup for a holdings dashboard, citing Morningstar.",
    ),
    (
        "transaction-feeds",
        "Sell it for: transaction feeds & spend categorisation",
        "Bank statements show garbage descriptors users can't recognise. The Transaction API "
        "maps each descriptor to a real merchant with logo, domain and industry — recognisable "
        "feeds and cleaner categorisation. Buyer: neobanks, personal-finance/budgeting apps, "
        "expense-management and card-issuing fintechs, open-banking aggregators. Tie to the "
        "assessment: an answer to a data-quality or user-experience weakness surfaced for an "
        "**exchange**/fintech operating model.",
        "product:brandfetch:uc-transactions",
        "You can map the Transaction API to a spend-feed data-quality gap.",
    ),
    (
        "enrichment-research",
        "Sell it for: data enrichment & research platforms",
        "Company profiles, screeners and CRM/marketing records need consistent branding and "
        "firmographics across millions of entities. Batch Brand API lookups enrich records with "
        "logos plus employee count, founded year, HQ and industry — ISIN/ticker-addressable and "
        "current. This is also the practical post-Clearbit enrichment path. Buyer: "
        "financial-data providers, research platforms, BI/analytics vendors, RevOps/marketing "
        "teams. Tie to the assessment: a scale/consistency fix a **cornered-resource** or "
        "process finding sets up.",
        "product:brandfetch:uc-enrichment",
        "You can pitch batch enrichment (logos + firmographics) at scale.",
    ),
)

_COMMERCIAL: tuple[tuple[str, str, str, str, str], ...] = (
    (
        "two-tier",
        "Distribution vs redistribution — the two commercial models",
        "This is the pivot for Brandfetch, and it maps to two commission tiers. DISTRIBUTION is "
        "in-product use: you drive a firm to adopt the standard paid API and DISPLAY brand data "
        "inside its own product (self-serve, a 30-day cache rule, no attribution). "
        "REDISTRIBUTION is passing Brandfetch's brand DATA out to third parties / end-clients, "
        "or a white-label / reseller model — this is barred under the standard licence and "
        "needs Enterprise custom licensing (flat-file/webhook data delivery, custom terms). "
        "Distribution pays the higher rate; redistribution is the lower, enterprise-negotiated "
        "tier. (The exact display-vs-redistribute line is not publicly bright — confirm per use "
        "case.)",
        "product:brandfetch:two-tier",
        "You can explain distribution vs redistribution and which commission tier each is.",
    ),
    (
        "trademark",
        "Trademark & compliance — the disclosure you must make",
        "Brandfetch does NOT own the logos — they remain the property of their trademark "
        "owners; Brandfetch only provides access. The customer carries the fair-use / trademark "
        "risk: assets must be used without endorsement, misrepresentation, alteration, or "
        "implying false affiliation. For a regulated financial firm this is a real compliance "
        "exposure (misusing another institution's mark), so make it an explicit disclosure in "
        "any deal — you sell access to brand data, not indemnity for how the marks are used.",
        "product:brandfetch:trademark",
        "You proactively disclose that the buyer owns trademark/fair-use compliance, not "
        "Brandfetch.",
    ),
    (
        "pricing-motion",
        "Pricing & the land-and-expand motion",
        "The public anchors: Logo API and Brand Search are free to ~500k requests/month (no "
        "attribution); the Brand API starts around $99/month with ~$0.10 per-request overage; "
        "Enterprise is custom (unlimited, 99.9% SLA, webhooks, flat-file transfer, custom legal "
        "terms). The motion: LAND with a free Logo Link / Brand Search demo, EXPAND to the paid "
        "Brand API as usage grows, then move to Enterprise where redistribution / white-label / "
        "SLA / bulk data are needed. There is no public self-serve reseller program — "
        "redistribution rights are bespoke Enterprise contracting; say that plainly.",
        "product:brandfetch:pricing-motion",
        "You can walk the free→Brand API→Enterprise land-and-expand path with real price anchors.",
    ),
)

_CONVICTION: tuple[tuple[str, str, str, str, str], ...] = (
    (
        "origin",
        "Origin & the company",
        "Brandfetch was founded in 2020 in Switzerland by Amin Kasimov, Nuri Kasimov and Jérémy "
        "Jaques, out of a simple frustration: brand assets are scattered and designers wasted "
        "hours hunting a client's logos, colours and fonts. Their conviction — 'all brands "
        "should live in one central source of truth accessible to anyone, anywhere' — became a "
        "public brand registry. It was backed early by the Adobe Fund for Design (do NOT cite a "
        "priced VC round or investor list — none is public); it is largely "
        "grant-supported/bootstrapped, which is itself a credibility, not a weakness, story.",
        "product:brandfetch:origin",
        "You can tell the origin story accurately (2020, Switzerland, Adobe Fund — no VC $ claim).",
    ),
    (
        "conviction",
        "Conviction: peer proof, the registry flywheel & AI",
        "Three grounded conviction points. (1) Financial-data leaders already run on it — "
        "Morningstar keeps institution assets current with it, and Envestnet | Yodlee used it "
        "to improve merchant identification: direct peer proof for a financial buyer. (2) The "
        "registry flywheel — brands claim and control their own profile, hundreds of platforms "
        "pull it via the Brand API, so it stays canonical everywhere: it is the source of "
        "truth, not a scraper you bolt on. (3) It is already the 'brand layer for AI' — a Brand "
        "Context API and MCP/gen-AI integrations, plus the 2025 Transaction API — future-proof "
        "infrastructure, not a point tool.",
        "product:brandfetch:conviction",
        "You can cite two financial-firm reference customers and the registry-flywheel thesis.",
    ),
    (
        "objections",
        "Objection handling",
        "'Can't we just scrape logos?' — scraping is barred and gets you blocked; Brandfetch is "
        "verified, current, and legally cleaner. 'Isn't it just logos?' — no: colours, fonts, "
        "firmographics, and ticker/ISIN/merchant lookups a scraper can't do. 'Is it free?' — "
        "Logo Link/Search are free to ~500k/month; the enrichment-grade Brand API and "
        "Transaction API are paid — sell the paid data, not the free image URL. 'Who owns the "
        "logos?' — the brands do; the firm owns its own trademark compliance. 'Can we resell "
        "the data to our clients?' — only under Enterprise custom licensing, not the standard "
        "tier.",
        "product:brandfetch:objections",
        "You have a grounded, honest answer to each of the five most common buyer objections.",
    ),
)


def _lessons(specs: tuple[tuple[str, str, str, str, str], ...]) -> tuple[Lesson, ...]:
    return tuple(
        Lesson(
            id=_id("lesson", key),
            title=title,
            body=body,
            order=i,
            author=LessonAuthor.HUMAN,
            drill_topics=(drill,),
            measurement=measurement,
        )
        for i, (key, title, body, drill, measurement) in enumerate(specs)
    )


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
        f"the commission."
    )
    return Lesson(
        id=_id("lesson", "two-tier-rates"),
        title="Your two commission tiers, live",
        body=body,
        order=len(_COMMERCIAL),
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
    base = build_product_course(spec, dist_carrot)  # spine incl. the live distribution commission
    commercial_lessons = _lessons(_COMMERCIAL) + (
        _two_tier_commission_lesson(dist_carrot, redist_carrot),
    )
    deep = (
        CourseModule(
            id=_id("module", "what-it-is"),
            title="What Brandfetch actually is",
            order=1,
            lessons=_lessons(_WHAT_IT_IS),
        ),
        CourseModule(
            id=_id("module", "use-cases"),
            title="Use cases you can sell for",
            order=2,
            lessons=_lessons(_USE_CASES),
        ),
        CourseModule(
            id=_id("module", "commercial"),
            title="The commercial & licensing angle",
            order=3,
            lessons=commercial_lessons,
        ),
        CourseModule(
            id=_id("module", "conviction"),
            title="Conviction & the company",
            order=4,
            lessons=_lessons(_CONVICTION),
        ),
    )
    return base.model_copy(update={"modules": base.modules + deep})
