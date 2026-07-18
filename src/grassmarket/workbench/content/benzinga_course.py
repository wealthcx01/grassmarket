"""Benzinga product course (GRS-0124, ADR-0028) — a deep, use-case-aligned sell-enablement course,
authored through the GRS-0121 CMS on the GRS-0123 product-course template.

Grounded in public research (July 2026): Benzinga's public product/API pages, docs, partnership
press releases, and third-party reviews. Only public product facts — the confidential reseller
agreement is NOT reproduced here; the advisor's commission (15% — Bruntsfield takes the Benzinga
reseller's 30% and shares half with the advisor) resolves LIVE from the Earnings v7 schedule.

Slug is `product-benzinga` so completing the course counts toward the `product:benzinga` cert
(GRS-0127). IDs are derived (uuid5) so re-seeding is idempotent.

Accuracy guardrails baked in (flagged by the research pass): founded ~2009–2010 (sources conflict);
the Beringer valuation is reportedly ~$300M (terms were undisclosed); named brokerage clients and
scale stats are Benzinga's own claims — attribute, don't assert; redistribution / attribution /
entitlement terms are per-contract and were not publicly readable — confirm in writing per deal;
options-flow "precedes moves" is Benzinga's framing, not validated alpha; Benzinga is a news/events/
signals layer, NOT a terminal, a fundamentals engine, or a real-time tick/quote source.
"""

from __future__ import annotations

from uuid import NAMESPACE_URL, UUID, uuid5

from bcap_contracts.commissions import ProductCommissionCarrot
from bcap_contracts.learning import CourseModule, CourseTree, Lesson, LessonAuthor

from grassmarket.workbench.content.product_course import ProductCourseSpec, build_product_course

BENZINGA_PRODUCT_ID = "benzinga"
BENZINGA_SLUG = "product-benzinga"
_NS = "grassmarket:academy:product-benzinga"


def _id(kind: str, key: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"{_NS}:{kind}:{key}")


_WHAT_IT_IS: tuple[tuple[str, str, str, str, str], ...] = (
    (
        "two-arms",
        "Media company, data-licensing product",
        "Benzinga is a financial-media company with two arms. The consumer arm is benzinga.com "
        "and Benzinga Pro (a real-time news terminal for traders). The arm you sell is the "
        "data-licensing business — Benzinga APIs / Benzinga Cloud — which packages its newsroom "
        "output and proprietary datasets into structured feeds (JSON/XML) that brokerages, "
        "fintechs and aggregators embed in their OWN products. Benzinga self-describes as 'the "
        "largest news vendor to North American brokerages' (its own claim — attribute it). You "
        "are selling infrastructure, not an app.",
        "product:benzinga:two-arms",
        "You can distinguish the consumer arm (Pro) from the data-licensing arm (the APIs) you "
        "sell.",
    ),
    (
        "news-feeds",
        "The news feeds — and WIIM, the signature product",
        "The flagship is the Premium US Equities Newsfeed: real-time articles + short "
        "headlines, fully embeddable so users never leave the app. Its signature product is "
        "'Why Is It Moving' (WIIM) — a one-sentence explanation of why a stock is up or down "
        "today, dug out of filings and news by analysts. Also: Press Release feed, Bulls Say / "
        "Bears Say (the two-sided case per stock), Analyst Insights, a video news feed, and "
        "newer Prediction-Markets and Private-Markets newswires. Benzinga even licenses "
        "datasets for training LLMs. This originate-in-house newsroom is the provenance you "
        "sell — content that already moves markets.",
        "product:benzinga:news-feeds",
        "You can pitch WIIM as the snackable 'why it moved' feed for alerts and notifications.",
    ),
    (
        "signals-ratings",
        "Signals & ratings — the tradable data",
        "The structured, machine-readable layer. Analyst Ratings deliver every individual "
        "rating action with price targets (rating/pt current vs prior, "
        "upgrade/downgrade/initiate, analyst + firm) — un-normalised, so the analyst's own "
        "language is preserved. Unusual Options Activity flags large/aggressive sweeps and "
        "blocks that Benzinga says 'often precede a move' (that's marketing framing, not "
        "validated alpha — sell it as signal/engagement content). Plus Movers, Insider Trades, "
        "Government (congressional) Trades, Short Interest, Block Trades and Ticker Trends — "
        "the 'smart-money' content most cheap vendors lack.",
        "product:benzinga:signals-ratings",
        "You can name three signal datasets and honestly frame options-flow as signal, not alpha.",
    ),
    (
        "calendars-delivery",
        "Calendars, reference data & delivery",
        "Structured forward-looking event feeds: Earnings, Guidance, FDA, Economics, M&A, IPO, "
        "Dividends, Splits, Secondary Offerings, and Conference-Call transcripts + calendar. "
        "Plus reference data: Corporate Logos, SEC Filings, Security Master, Historical Bars "
        "(OHLCV) and 15-minute delayed quotes. Delivery is multi-protocol — REST (token auth, "
        "JSON/XML), WebSocket and raw TCP for low-latency engines, webhooks for push, "
        "flat-file/S3 for bulk — marketed at sub-0.1s latency, ~99.9% availability on AWS, "
        "covering the Wilshire 5000 (100% of the US market) plus ~1,000 extra tickers and TSX. "
        "A firm gets an API key and integrates in days.",
        "product:benzinga:calendars-delivery",
        "You can list the calendar suite and the delivery protocols (REST / WebSocket / webhook).",
    ),
)

_USE_CASES: tuple[tuple[str, str, str, str, str], ...] = (
    (
        "power-brokerage",
        "Sell it for: powering a retail brokerage / trading app",
        "A retail brokerage or trading app (Webull/Robinhood-class) needs a credible real-time "
        "news and research layer on every ticker page — a bare price chart doesn't retain "
        "traders, and building a newsroom in-house isn't viable. One Benzinga vendor supplies "
        "breaking news, analyst ratings + price targets, WIIM explainers and options signals, "
        "by whichever protocol the stack needs. Buyer: retail brokerages, self-directed trading "
        "apps, neobrokers. Tie to the assessment: the fix for a product-depth / engagement gap "
        "a Platform Power read surfaces in a **retail brokerage**.",
        "product:benzinga:uc-brokerage",
        "You can pitch Benzinga as the news/ratings/signals layer on a brokerage's ticker pages.",
    ),
    (
        "advisor-platforms",
        "Sell it for: wealth / advisor platforms",
        "Wealth and advisor platforms want to show clients professional context on their "
        "holdings — analyst ratings, price targets, earnings dates, relevant news — inside the "
        "client portal, to look institutional without a Bloomberg-per-seat bill. Benzinga's "
        "aggregated ratings, calendars and curated news embed into an advisor UI; the Apex "
        "Fintech partnership (2026) is exactly this shape (Stock News, WIIM, Analyst Report "
        "Insights, Bulls/Bears Say, earnings + IPO tracking across the Wilshire 5000). Buyer: "
        "wealth/advisor platforms, RIAs' tech vendors, digital-wealth and clearing-embedded "
        "platforms. Tie to the assessment: deepens a **wealth** client-facing surface a "
        "brand/switching-cost finding is pricing.",
        "product:benzinga:uc-advisor",
        "You can describe the advisor-portal embed and cite the Apex integration shape.",
    ),
    (
        "signals-quant",
        "Sell it for: signals & alerts for algo/quant",
        "Quant/algo shops and alerting products want machine-readable smart-money and momentum "
        "events — unusual options sweeps, movers, new highs/lows, analyst-rating changes — "
        "timestamped and low-latency. Benzinga's signals dataset (with UNIX timestamps, an "
        "importance score on ratings, raw-TCP/WebSocket delivery) targets automated engines. "
        "Buyer: algo/quant funds, systematic-trading tools, options-flow alerting products. Tie "
        "to the assessment: an answer to a data/tooling gap for an **exchange**/quant operating "
        "model — but sell it as signal + engagement content, never as proven alpha.",
        "product:benzinga:uc-signals",
        "You can pitch the signals feed to an algo buyer without overclaiming predictive edge.",
    ),
    (
        "fintech-engagement",
        "Sell it for: fintech engagement & retention",
        "A fintech's biggest churn problem is a dead home screen: users open the app, see "
        "nothing new, and leave. A steady stream of breaking news, WIIM, trending tickers, "
        "movers and Bulls/Bears Say gives an always-fresh feed and per-ticker content — "
        "Benzinga explicitly markets its APIs as helping firms 'delight and retain' customers, "
        "with a free Basic News API on AWS Marketplace as a low-friction on-ramp. Buyer: "
        "early-stage fintechs, neobanks adding investing, engagement/retention teams. Tie to "
        "the assessment: the fix for a retention/engagement weakness a fintech assessment "
        "surfaces.",
        "product:benzinga:uc-engagement",
        "You can connect an always-fresh feed to a retention/engagement gap in the assessment.",
    ),
)

_COMMERCIAL: tuple[tuple[str, str, str, str, str], ...] = (
    (
        "redistribution",
        "Redistribution IS the model",
        "Benzinga's entire enterprise business is redistribution: its content reaches millions "
        "of end investors THROUGH brokerages and distribution partners. Two patterns exist — a "
        "direct enterprise redistribution licence (a brokerage licenses feeds and displays them "
        "to its own users, the model behind the major online brokers), and distribution-partner "
        "rails (Apex embeds Benzinga into its clearing stack so Apex's downstream clients can "
        "use it; Nasdaq Data Link and Massive resell datasets). So 'can we show this to our "
        "clients?' is a yes in principle — redistribution is what Benzinga is built for.",
        "product:benzinga:redistribution",
        "You can explain that redistribution is Benzinga's core model, not an exception.",
    ),
    (
        "licence-attribution",
        "Licensing & attribution — scope the rights, in writing",
        "Sell the capability, scope the rights. Redistribution rights, re-branding / "
        "white-label, attribution ('Powered by Benzinga' / link-back), per-end-user "
        "entitlements and territory are ALL set in the enterprise contract, not the public or "
        "marketplace tiers (a $99/mo marketplace tier is individual-use, NOT a redistribution "
        "licence). The free Basic News API requires a link back to Benzinga.com — a strong "
        "signal that attribution obligations exist. Do not promise a buyer they can strip "
        "attribution or redistribute freely until the signed contract says so; scope every deal "
        "via licensing@benzinga.com.",
        "product:benzinga:licence",
        "You proactively scope redistribution/attribution rights to the signed contract, per deal.",
    ),
    (
        "positioning",
        "The honest competitive frame",
        "Where Benzinga wins: real-time, retail-flavoured breaking news + alerting (ranked #1 "
        "for speed/price), structured analyst ratings + price targets, accessible options-flow "
        "signals, fintech-ready event calendars, and cost — custom-priced and multi-protocol vs "
        "a ~$25–28k/seat terminal. Where it is NOT the answer, say plainly: it is not a full "
        "institutional terminal (no Bloomberg-class analytics/chat/fixed-income), not a deep "
        "fundamentals engine (FactSet/LSEG/Morningstar win there), not global multi-asset, and "
        "not your real-time tick/quote source (Polygon/Databento win there; Benzinga quotes are "
        "delayed). Sell it as the engagement + context layer, paired with a quotes/fundamentals "
        "vendor where the buyer needs depth.",
        "product:benzinga:positioning",
        "You can state where Benzinga wins AND where it is not the answer, unprompted.",
    ),
)

_CONVICTION: tuple[tuple[str, str, str, str, str], ...] = (
    (
        "origin",
        "Origin & mission",
        "Benzinga was founded around 2009–2010 (sources conflict — use '~2009–2010, out of the "
        "Great Recession') by Jason Raznick, in metro Detroit — famously in a basement with "
        "about $3,000 in the bank and a baby on the way. The mission is the whole pitch: during "
        "the Recession 'inequality of information was rampant', so Benzinga set out to 'level "
        "the playing field for individual investors' — giving retail the actionable, real-time "
        "intelligence once reserved for Wall Street. Early backers included Dan Gilbert "
        "(Rocket) and Brad Keywell (Groupon); the founder won EY Entrepreneur of the Year.",
        "product:benzinga:origin",
        "You can tell the origin/mission story (Raznick, Detroit, ~2009–2010, 'level the field').",
    ),
    (
        "conviction",
        "Conviction: provenance, reach & durability",
        "Three grounded conviction points. (1) Provenance — Benzinga runs a real newsroom "
        "breaking hundreds of market-moving stories a year and reaching a claimed ~25M+ "
        "investors monthly across 125+ countries; you license content that already moves "
        "markets. (2) It is already the plumbing — Benzinga positions itself as the largest "
        "news vendor to North American brokerages, its content embedded across major platforms "
        "(Benzinga's own claim — attribute it); if it's good enough inside their apps, it "
        "de-risks yours. (3) Durability — founder-led since ~2009, majority-owned since 2021 by "
        "Beringer Capital (reportedly ~$300M; terms undisclosed), and host of its own Fintech "
        "Day & Awards convening 1,000+ industry leaders.",
        "product:benzinga:conviction",
        "You can cite three conviction points and attribute the company-reported ones honestly.",
    ),
    (
        "objections",
        "Objection handling",
        "'Is it institutional-grade?' — it's the news backbone behind major brokerages and "
        "distributed via Apex/Nasdaq/AWS, but it's retail-FLAVOURED and fast; sell engagement + "
        "context, not deep analytics. 'We have Bloomberg.' — different job; Benzinga is the "
        "feed you show END USERS in your app with a redistribution licence, not the analyst's "
        "terminal. 'Can we white-label / redistribute?' — yes in principle, but "
        "rights/attribution/entitlements are per-contract — confirm in writing. 'What does it "
        "cost?' — no public enterprise price; a free Basic News API to prototype, then a scoped "
        "quote. 'Does it replace our quotes/fundamentals?' — no, pair it with Polygon/Databento "
        "and Morningstar/FactSet.",
        "product:benzinga:objections",
        "You have a grounded, honest answer to each of the five most common buyer objections.",
    ),
)


# Comprehension checks (GRS-0140): (question, answer) per lesson key, for the active-recall gate.
_DEEP_CHECKS: dict[str, tuple[str, str]] = {
    "two-arms": (
        "Distinguish Benzinga's two arms — and which one you actually sell.",
        "The consumer arm (Benzinga Pro, the subscription terminal) versus the data-licensing arm "
        "(the news / signals / calendar APIs). You sell the licensed data products, not Pro.",
    ),
    "news-feeds": (
        "What is WIIM, and how do you pitch it?",
        "'Why Is It Moving' — snackable, plain-English explanations of price moves. Pitch it "
        "as the feed that powers alerts and notifications: the instant 'why' behind every "
        "ticker move.",
    ),
    "signals-ratings": (
        "Name a few signal datasets, and how do you honestly frame options flow?",
        "Analyst ratings, options-flow, and unusual-activity signals. Frame options-flow as "
        "engagement/signal content, NOT validated alpha — honesty about that is the sell, "
        "not a hole.",
    ),
    "calendars-delivery": (
        "What's in the calendar suite, and how is the data delivered?",
        "Earnings, economics, dividends, IPOs, splits, guidance calendars — delivered over REST, "
        "WebSocket (streaming), and webhooks, so a firm integrates the shape it needs.",
    ),
    "power-brokerage": (
        "How do you pitch Benzinga to a brokerage?",
        "As the news / ratings / signals layer on the brokerage's ticker pages — turning a bare "
        "quote screen into an engaging, always-fresh research surface.",
    ),
    "advisor-platforms": (
        "Describe the advisor-portal use case and the integration shape.",
        "Embed Benzinga's feed into an advisor/client portal for timely, branded market context; "
        "cite the Apex integration as the reference embed pattern.",
    ),
    "signals-quant": (
        "How do you pitch the signals feed to an algo buyer without overclaiming?",
        "Sell it as clean, structured signal/engagement data to enrich models — never as "
        "predictive alpha. The honest framing is what an algo buyer trusts.",
    ),
    "fintech-engagement": (
        "Which assessment gap does an always-fresh Benzinga feed answer?",
        "A retention/engagement bottleneck — fresh, relevant market content keeps users returning, "
        "the fix you recommend when the Platform Power read surfaces weak engagement.",
    ),
    "redistribution": (
        "Is redistributing Benzinga's data an exception or the model?",
        "It's the core model — Benzinga licenses data expressly for a firm to redistribute to its "
        "own users; that's the product, not a special case.",
    ),
    "licence-attribution": (
        "What must you scope per deal, and why?",
        "The specific redistribution and attribution rights in the signed contract — proactively, "
        "per deal — so the client's usage stays inside what was licensed.",
    ),
    "positioning": (
        "State, unprompted, where Benzinga wins and where it is not the answer.",
        "It wins on fast retail-facing news, ratings and engagement signals; it is NOT deep "
        "institutional fundamentals or a Bloomberg-grade terminal — saying so builds trust.",
    ),
    "origin": (
        "Tell the Benzinga origin/mission story briefly.",
        "Founded by Jason Raznick in Detroit around 2009–2010 to 'level the playing field' — give "
        "retail investors the fast market information institutions had.",
    ),
    "conviction": (
        "Cite three conviction points, attributing company-reported ones honestly.",
        "Breadth of real-time coverage, the redistribution-first licensing model, and adoption "
        "by brokerages/fintechs — flagging which figures are company-reported rather than "
        "independent.",
    ),
    "objections": (
        "Give an honest answer to 'isn't this just retail news noise?'",
        "It's structured, redistributable, attributable market data — news, ratings, signals "
        "and calendars via API — built to embed and engage, not a noise feed; and it's honest "
        "about not being institutional fundamentals.",
    ),
}

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


def _lessons(
    specs: tuple[tuple[str, str, str, str, str], ...],
    checks: dict[str, tuple[str, str]] = _DEEP_CHECKS,
) -> tuple[Lesson, ...]:
    return tuple(
        Lesson(
            id=_id("lesson", key),
            title=title,
            body=body,
            order=i,
            author=LessonAuthor.HUMAN,
            drill_topics=(drill,),
            measurement=measurement,
            check_question=checks.get(key, (None, None))[0],
            check_answer=checks.get(key, (None, None))[1],
        )
        for i, (key, title, body, drill, measurement) in enumerate(specs)
    )


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
    deep = (
        CourseModule(
            id=_id("module", "what-it-is"),
            title="What Benzinga actually is",
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
            title="The reseller & commercial angle",
            order=3,
            lessons=_lessons(_COMMERCIAL),
        ),
        CourseModule(
            id=_id("module", "conviction"),
            title="Conviction & the company",
            order=4,
            lessons=_lessons(_CONVICTION),
        ),
    )
    return base.model_copy(update={"modules": base.modules + deep})
