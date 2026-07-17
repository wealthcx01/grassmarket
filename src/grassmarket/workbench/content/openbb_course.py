"""OpenBB product course (GRS-0126, ADR-0028) — a deep, use-case-aligned sell-enablement course,
authored through the GRS-0121 CMS on top of the GRS-0123 product-course template.

Grounded in public research (July 2026): OpenBB's site, docs, blog, the founder Didier Rodrigues
Lopes's writing, and a hands-on run of the open-source Platform (`pip install openbb`,
`obb.equity.price.historical(...)`). It is NOT partner-confidential — only public product facts. The
commission figures are NOT authored here; the template's commission lesson resolves them live from
the Earnings v7 schedule (ADR-0026). Because the course is versioned, the founder can deepen or
correct it later as a new published version.

Accuracy notes baked into the content (flagged by the research pass): "Terminal Pro" is legacy — the
current enterprise product is OpenBB Workspace; the Platform is AGPLv3 (confirmed from the GitHub
LICENSE), so any client-facing / white-labelled build needs a commercial license; OpenBB does NOT
claim Bloomberg parity — sell the open + governed-AI-over-your-own-data story.

Slug is `product-openbb` so completing the course counts toward the `product:openbb` certification
(GRS-0127). IDs are derived (uuid5) so re-seeding is idempotent.
"""

from __future__ import annotations

from uuid import NAMESPACE_URL, UUID, uuid5

from bcap_contracts.commissions import ProductCommissionCarrot
from bcap_contracts.learning import CourseModule, CourseTree, Lesson, LessonAuthor

from grassmarket.workbench.content.product_course import ProductCourseSpec, build_product_course

OPENBB_PRODUCT_ID = "openbb"
OPENBB_SLUG = "product-openbb"
_NS = "grassmarket:academy:product-openbb"


def _id(kind: str, key: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"{_NS}:{kind}:{key}")


# (key, title, body, drill_topic, measurement) for each deep lesson. Bodies are grounded in the
# public research; keep them factual, not hype.
_WHAT_IT_IS: tuple[tuple[str, str, str, str, str], ...] = (
    (
        "pivot",
        "The pivot: Terminal → Platform → Workspace",
        "OpenBB started as the viral open-source 'Gamestonk Terminal' CLI (the free 'Bloomberg "
        "alternative'), but that free Terminal was sunset — 500+ dependencies and no rights to "
        "the underlying data made it un-monetisable. The company deliberately moved through "
        "three stages: the Terminal, then the open-source Open Data Platform (the data layer), "
        "then OpenBB Workspace (the commercial AI research product). Sell the Workspace, not "
        "the legacy 'Terminal Pro' name — and never lead with 'Bloomberg killer', which "
        "sophisticated buyers and OpenBB itself have walked away from.",
        "product:openbb:pivot",
        "You can name the three stages and state the current commercial product (Workspace).",
    ),
    (
        "workspace",
        "OpenBB Workspace — the commercial flagship",
        "Workspace (pro.openbb.co) is a browser-based, AI-powered research and analytics "
        "environment where investment teams build interactive dashboards and put an AI copilot "
        "on top of governed data. Its core unit is the widget — a self-contained data "
        "component; analysts assemble widgets into dashboards and shareable apps with no "
        "front-end team. It integrates any data source (public feeds, licensed vendors like "
        "FactSet/LSEG/CapIQ, and a firm's own internal databases) and can run entirely on the "
        "firm's infrastructure, so proprietary data never leaves their environment — the "
        "central pitch to compliance-sensitive firms.",
        "product:openbb:workspace",
        "You can explain what a widget is and why 'data never leaves your environment' matters.",
    ),
    (
        "platform",
        "The Open Data Platform — connect once, consume everywhere",
        "Underneath Workspace is the open-source Open Data Platform (ODP): `pip install "
        "openbb`, then one unified Python API over close to 100 data providers and 100+ "
        "standardised endpoints. Integrate a source ONCE and it is available across five "
        "surfaces — Python, the Workspace UI, Excel, MCP servers (AI agents), and a REST API. "
        "Because outputs are standardised, a firm can swap one data vendor for another with a "
        "one-word `provider=` change — a real escape from vendor lock-in. The Platform is "
        "AGPLv3 (see the licensing lesson), which shapes every white-label conversation.",
        "product:openbb:platform",
        "You can state the 'connect once, consume everywhere' thesis and the five consuming "
        "surfaces.",
    ),
    (
        "copilot-mcp",
        "OpenBB Copilot & MCP — governed AI agents",
        "The flagship 2026 thesis: AI agents will run inside a firm whether it plans for them "
        "or not, and their output otherwise lands ungoverned and untraceable. OpenBB Copilot "
        "runs on the firm's own data with function-calling (it picks the right widget) and "
        "citations; firms can bring their own model (OpenAI/Azure) or agent. The Workspace MCP "
        "endpoint lets external agents (Claude Code, Codex, Cursor) work over the firm's "
        "governed data with permissions, lineage, and credential vaulting enforced. This "
        "'govern the agents you already have' angle is OpenBB's sharpest, most "
        "enterprise-relevant hook.",
        "product:openbb:copilot-mcp",
        "You can articulate the 'govern the AI agents already loose in the firm' pitch.",
    ),
)

_USE_CASES: tuple[tuple[str, str, str, str, str], ...] = (
    (
        "buy-side-research",
        "Sell it for: buy-side research consolidation",
        "Research teams juggle disconnected tools — filings in one place, prices in another, AI "
        "somewhere else — and building a thesis takes hours of data-wrangling. In Workspace an "
        "analyst extracts guidance from a SEC filing via Copilot, cross-references news, prices "
        "and targets, runs peer comparisons, and exports a thesis in minutes. Buyer segment: "
        "hedge funds, asset managers, equity-research teams. Tie to the assessment: this is the "
        "fix you recommend when a **retail brokerage** or **wealth** firm's Platform Power read "
        "surfaces a research/tooling infrastructure gap.",
        "product:openbb:uc-research",
        "You can name the buyer segment and the assessment gap this use case answers.",
    ),
    (
        "portfolio-risk",
        "Sell it for: portfolio analytics & risk monitoring",
        "Portfolio state is scattered across custodians, vendors and internal models, and every "
        "new view waits on the data team. OpenBB connects custodian feeds, vendors and internal "
        "DBs into no-code dashboards analysts self-serve, and risk/breach dashboards are built "
        "centrally and distributed firm-wide with role-based access. Buyer segment: asset "
        "managers, multi-strategy and risk teams. Tie to the assessment: a fix for an "
        "operations/risk-infrastructure bottleneck an assessment surfaces — strongest for "
        "**wealth** and **exchange** operating models.",
        "product:openbb:uc-risk",
        "You can map this use case to a risk/ops bottleneck the assessment surfaces.",
    ),
    (
        "client-reporting",
        "Sell it for: branded client reporting & research portals",
        "Quarterly client reports are assembled by hand and go stale the moment data changes. "
        "Workspace produces auto-refreshing, **branded** (white-labelled) reports and "
        "dashboards, shareable as interactive dashboards or PDFs. Buyer segment: wealth "
        "managers, private banks, IR/advisory teams. Tie to the assessment: pairs with a "
        "**brand** or **switching-cost** finding — a polished, sticky client-facing surface "
        "deepens the client relationship the assessment is pricing.",
        "product:openbb:uc-reporting",
        "You can connect client-reporting to a brand/switching-cost finding in the assessment.",
    ),
    (
        "governed-ai",
        "Sell it for: governed AI copilots over the firm's own data (flagship)",
        "Analysts already spin up personal AI tools, risking proprietary-data leakage the firm "
        "can't govern. OpenBB runs the copilot on firm data, in the firm's VPC, with "
        "bring-your-own model and MCP for any agent — output governed as it is created "
        "(entitlements, lineage, vaulting). This is OpenBB's real differentiator and where "
        "incumbents are weakest; lead with it for AI-forward funds, quant/data teams, and banks "
        "with private LLMs. Tie to the assessment: the answer to a **process-power** or "
        "data-governance weakness a rigorous read exposes.",
        "product:openbb:uc-ai",
        "You can lead a pitch with the governed-AI angle instead of a feature bake-off.",
    ),
    (
        "quant-consolidation",
        "Sell it for: quant workflows & vendor-agnostic consolidation",
        "Quants rebuild the same vendor integrations repeatedly and want data in code, not a "
        "GUI; leadership wants to end multi-vendor sprawl and vendor lock-in. ODP gives one "
        "Python interface across equities, crypto, futures, options, macro and fixed income, "
        "and one governed layer that integrates FactSet/LSEG/CapIQ + internal DBs + alt-data, "
        "preserving workflows when analysts leave. Buyer segment: quant funds, data-engineering "
        "teams, enterprise CTO/CDO. This is the 'own your infrastructure' story a "
        "**cornered-resource** or **scale** assessment finding sets up.",
        "product:openbb:uc-quant",
        "You can pitch the 'connect once, own your infrastructure' consolidation story.",
    ),
    (
        "vs-bloomberg",
        "The honest 'vs Bloomberg' positioning",
        "Be precise — it builds trust. OpenBB genuinely wins on cost (a one-time team license "
        "vs ~$25k/user/year), openness/customisation, AI-native architecture, and bringing your "
        "OWN data in. It does NOT replace Bloomberg's messaging network, fixed-income depth, "
        "real-time options flow, or execution — third parties estimate ~30–40% of Bloomberg's "
        "surface. Sell it as complementary infrastructure that retires some light-user seats "
        "and unifies proprietary data + AI, not a rip-and-replace. Saying this plainly is "
        "itself a sales advantage.",
        "product:openbb:uc-vs-bloomberg",
        "You can state, unprompted, what OpenBB does and does NOT replace.",
    ),
)

_WHITE_LABEL: tuple[tuple[str, str, str, str, str], ...] = (
    (
        "licensing",
        "Licensing: AGPLv3 and the commercial-license trigger",
        "The open-source Platform is AGPLv3 (confirmed from the GitHub LICENSE; it was "
        "relicensed from MIT). AGPL's network clause means offering the software as a service, "
        "or embedding it in a client-facing / white-labelled product, counts as distribution — "
        "the firm would have to publish its own source. Internal, unmodified use needs no "
        "license; a client-facing, hosted, or white-labelled build needs a COMMERCIAL license "
        "(licensing@openbb.co), which lifts the copyleft. Raise this early — AGPL will "
        "otherwise block the deal or force source disclosure. (Confirm exact FAQ wording live "
        "before quoting clauses.)",
        "product:openbb:licensing",
        "You can explain when a client build needs OpenBB's commercial license and why.",
    ),
    (
        "white-label",
        "White-labelling Workspace",
        "Practical white-labelling happens in the proprietary Workspace, NOT by forking the "
        "repo — which also keeps you clear of the AGPL trap. Levers: brand the UI (logo, "
        "favicon, colours, light/dark themes, applied instantly to all sessions); ship curated, "
        "branded 'Apps' via an `apps.json` spec; and embed proprietary tools with custom/HTML "
        "widgets (HTML/CSS on cloud; full JavaScript on enterprise/on-prem). The framing to "
        "sell: white-labelling is configuration + extension of Workspace — fast to deploy and "
        "license-clean.",
        "product:openbb:white-label",
        "You can list the branding levers and why white-labelling avoids the AGPL trap.",
    ),
    (
        "custom-backend",
        "Custom backends — surface the firm's own data (the key deliverable)",
        "This is the highest-value, most repeatable consulting deliverable. A 'custom backend' "
        "is just any web API returning JSON plus one `widgets.json` endpoint describing the "
        "widgets; Workspace is a pure consumer (any language/DB, CORS enabled, header auth). "
        "The reference is a small FastAPI app, or `openbb-api` auto-exposes the whole Platform "
        "as a Workspace backend. The firm keeps its data in its own infrastructure and only "
        "exposes a thin API — a Bloomberg-grade UI over its OWN data, self-hosted, with the "
        "consultancy owning the integration and the app templates.",
        "product:openbb:custom-backend",
        "You can describe the custom-backend pattern (JSON + widgets.json) at a whiteboard.",
    ),
    (
        "enterprise",
        "Enterprise deployment & the Snowflake angle",
        "Enterprise runs on-prem, in a VPC (AWS/Azure/GCP), or hybrid — data, models and "
        "prompts never leave the firm's environment. Controls: SOC 2 Type II (verify the exact "
        "scope with OpenBB before quoting), SSO (Azure/Google/any SAML), MFA, four-layer RBAC "
        "(application / widget / data source / AI feature), audit logs, no external product "
        "analytics. The standout OEM motion is the Snowflake Native App — Workspace running "
        "inside the customer's Snowflake on Cortex AI, inheriting Snowflake permissions, "
        "per-seat and self-serve. Enterprise deployments run ~4–8 weeks.",
        "product:openbb:enterprise",
        "You can name the deployment models + the four RBAC layers, and flag SOC 2 scope to "
        "verify.",
    ),
    (
        "dev-experience",
        "The developer experience (what building actually feels like)",
        "Hands-on: `pip install openbb`, then `from openbb import obb` gives a namespaced "
        "object over every asset class (equity, crypto, currency, derivatives, economy, "
        "fixedincome, etf, index, news, regulators). `obb.equity.price.historical('AAPL', "
        "provider='yfinance')` returns clean data you `.to_dataframe()`; keyless providers "
        "(yfinance, FRED, SEC) need no setup, premium ones (FMP, Intrinio, Polygon, Benzinga) "
        "take an API key set once. Adding a client's in-house warehouse as a first-class "
        "`provider=` source is a provider-extension engagement (the 'TET' Fetcher pattern). "
        "Credible technical selling starts from having actually run it.",
        "product:openbb:dev-experience",
        "You have personally run a live OpenBB query and can walk a buyer through the flow.",
    ),
)

_CONVICTION: tuple[tuple[str, str, str, str, str], ...] = (
    (
        "origin",
        "The origin story",
        "Founder Didier Rodrigues Lopes is a Portuguese control-systems engineer, not a finance "
        "insider. Frustrated by how manual his own 2020 investment research was — 'I couldn't "
        "understand why I couldn't automate this' — he built a terminal over a cancelled "
        "Christmas 2020 flight and open-sourced it as Gamestonk Terminal (named for the "
        "GameStop frenzy). He expected ~20 GitHub stars; it hit 4,000 in 24 hours and went "
        "viral. Renamed OpenBB in 2022 — the 'BB' is a self-deprecating nod to the BlackBerry "
        "(ticker BB) stock he and his co-founder were losing money on, NOT Bloomberg.",
        "product:openbb:origin",
        "You can tell the origin story (Gamestonk, 4,000 stars, BB = BlackBerry) in 60 seconds.",
    ),
    (
        "thesis",
        "The thesis & traction",
        "The founding vision: 'an open ecosystem for research, where users could bring their "
        "own data and build any type of features on top of it' — structurally impossible for a "
        "closed terminal. The north star: 'Analysts shouldn't need a data scientist to get an "
        "answer. The firms that fix that first will have a structural advantage.' Traction to "
        "cite: an $8.5M seed (OSS Capital; angels Naval Ravikant, Elad Gil, Ram Shriram), 50k+ "
        "GitHub stars, named enterprise customers (Pangaea Logistics; an unnamed $6.4B-AUM "
        "firm), SOC 2 Type II, and the 2026 Snowflake Native App + hosted Workspace MCP.",
        "product:openbb:thesis",
        "You can cite three conviction points (openness, governed AI, traction) from real sources.",
    ),
    (
        "objections",
        "Objection handling",
        "'Isn't this the free open-source thing?' — the sellable product is Workspace "
        "Pro/Enterprise (VPC, RBAC, audit, BYO-agent, support), a different product and buyer. "
        "'Can it replace our Bloomberg seats?' — not wholesale; it retires some light-user "
        "seats and unifies your data + AI. 'Is our data safe with your AI?' — enterprise runs "
        "in your VPC, data never leaves, BYO model. 'What does it cost?' — a scoped quote "
        "(Community is free, Copilot capped at 20 queries/day); sell on seat-reduction + "
        "IP-ownership + AI-governance, not a sticker price. 'We already have FactSet/Snowflake' "
        "— good, OpenBB sits on top and integrates them.",
        "product:openbb:objections",
        "You have a grounded, honest answer to each of the five most common buyer objections.",
    ),
)


def _lessons(specs: tuple[tuple[str, str, str, str, str], ...], start: int) -> tuple[Lesson, ...]:
    return tuple(
        Lesson(
            id=_id("lesson", key),
            title=title,
            body=body,
            order=start + i,
            author=LessonAuthor.HUMAN,
            drill_topics=(drill,),
            measurement=measurement,
        )
        for i, (key, title, body, drill, measurement) in enumerate(specs)
    )


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
        spec, carrot
    )  # 1 module (4 canonical sections incl. live commission)
    deep = (
        CourseModule(
            id=_id("module", "what-it-is"),
            title="What OpenBB actually is",
            order=1,
            lessons=_lessons(_WHAT_IT_IS, 0),
        ),
        CourseModule(
            id=_id("module", "use-cases"),
            title="Use cases you can sell for",
            order=2,
            lessons=_lessons(_USE_CASES, 0),
        ),
        CourseModule(
            id=_id("module", "white-label-build"),
            title="The white-label & build angle",
            order=3,
            lessons=_lessons(_WHITE_LABEL, 0),
        ),
        CourseModule(
            id=_id("module", "conviction"),
            title="Conviction & the founder thesis",
            order=4,
            lessons=_lessons(_CONVICTION, 0),
        ),
    )
    return base.model_copy(update={"modules": base.modules + deep})
