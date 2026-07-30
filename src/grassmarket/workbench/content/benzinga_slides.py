"""The Benzinga course, rebuilt to the GRS-0215 depth standard (GRS-0217).

GRS-0216 established the shape with OpenBB. This applies it to the highest-commission product left
in the catalogue: Benzinga sits at the same 1500 bps year-one advisor share as OpenBB, and unlike
OpenBB it comes with a committed, structured source of truth — `data/gtm/sources/
benzinga-product-catalog.xlsx`, 32 products across four families with delivery method, coverage
universe, update frequency, key fields and differentiators for each.

That catalogue is the reason this course can be specific. Every product claim below traces to a row
in it, and where the catalogue is silent the slide says so rather than filling the gap.

**Eight sections, in the order an advisor needs them**, not the order the catalogue is printed in:
what the company is, how its 32 products are actually organised, how the data physically arrives,
then one section per family, then who buys which family, then how to sell it.

## What this course deliberately does not claim

The prior version of this course (GRS-0124) already carried a set of accuracy guardrails from its
research pass, and they are kept because they are still true and still the things an advisor gets
wrong under pressure:

- Founded circa 2009-2010. Public sources conflict on the year, so no slide states one.
- Benzinga is a news, events and signals layer. It is **not** a terminal, **not** a fundamentals
  engine, and **not** a real-time tick or quote source. Saying so early is what stops a deal dying
  later on an expectation set in the first meeting.
- Named brokerage clients and audience figures are Benzinga's own published claims. Slides attribute
  them; they never assert them as independent fact.
- Redistribution, attribution and entitlement terms are per-contract and were not publicly
  readable. No slide states what a client may redistribute.
- "Unusual options activity often precedes moves in the underlying" is Benzinga's framing of its own
  product, not validated alpha, and the course labels it as such.
- Pricing is per-contract throughout. There is no public rate card, and the course tells the advisor
  never to quote one.

The advisor's 15% is the Bruntsfield share of the reseller margin and resolves LIVE from the
Earnings v7 schedule — it is never written into a slide, because a number written into content is a
number that goes stale silently.
"""

from __future__ import annotations

from uuid import NAMESPACE_URL, UUID, uuid5

from bcap_contracts.learning import (
    CourseModule,
    Lesson,
    LessonAsset,
    SectionTest,
    Slide,
    SlideKind,
    SourceRef,
    SourceRefKind,
    TestQuestion,
)

from grassmarket.workbench.content.benzinga_diagrams import SVG

_NS = "grassmarket:academy:product-benzinga"


def _id(kind: str, key: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"{_NS}:{kind}:{key}")


# --- Sources, declared once so a link is fixed in one place -------------------------------

CATALOGUE = SourceRef(
    title="Benzinga full product catalogue (committed GTM source, 32 products)",
    url="https://www.benzinga.com/apis/data/",
    kind=SourceRefKind.DOCS,
)
DOCS_INTRO = SourceRef(
    title="Benzinga API reference: introduction",
    url="https://docs.benzinga.com/api-reference/introduction",
    kind=SourceRefKind.DOCS,
)
DOCS_NEWS = SourceRef(
    title="Benzinga News API: overview",
    url="https://docs.benzinga.com/api-reference/news-api/overview",
    kind=SourceRefKind.DOCS,
)
DOCS_WIIM = SourceRef(
    title="Benzinga News API: Why Is It Moving (WIIM)",
    url="https://docs.benzinga.com/api-reference/news-api/wiims/overview",
    kind=SourceRefKind.DOCS,
)
DOCS_PRESS = SourceRef(
    title="Benzinga News API: press releases",
    url="https://docs.benzinga.com/api-reference/news-api/press-releases/overview",
    kind=SourceRefKind.DOCS,
)
DOCS_EARNINGS = SourceRef(
    title="Benzinga Calendar API: earnings",
    url="https://docs.benzinga.com/api-reference/calendar-api/get-earnings",
    kind=SourceRefKind.DOCS,
)
DOCS_RATINGS = SourceRef(
    title="Benzinga Calendar API: analyst ratings",
    url="https://docs.benzinga.com/api-reference/calendar-api/get-ratings",
    kind=SourceRefKind.DOCS,
)
DOCS_FDA = SourceRef(
    title="Benzinga Calendar API: FDA calendar",
    url="https://docs.benzinga.com/api-reference/calendar-api/get-fda",
    kind=SourceRefKind.DOCS,
)
DOCS_ECONOMICS = SourceRef(
    title="Benzinga Calendar API: economics calendar",
    url="https://docs.benzinga.com/api-reference/calendar-api/get-economics",
    kind=SourceRefKind.DOCS,
)
DOCS_IPO = SourceRef(
    title="Benzinga Calendar API: IPO calendar",
    url="https://docs.benzinga.com/api-reference/calendar-api/get-ipos",
    kind=SourceRefKind.DOCS,
)
DOCS_OPTIONS = SourceRef(
    title="Benzinga Calendar API: unusual options activity",
    url="https://docs.benzinga.com/api-reference/calendar-api/get-optionactivity",
    kind=SourceRefKind.DOCS,
)
DOCS_INSIDER = SourceRef(
    title="Benzinga Calendar API: insider transactions",
    url="https://docs.benzinga.com/api-reference/calendar-api/insider-transaction/get-insider-transaction-filing",
    kind=SourceRefKind.DOCS,
)
DOCS_GOVERNMENT = SourceRef(
    title="Benzinga Calendar API: government trades",
    url="https://docs.benzinga.com/api-reference/calendar-api/government-trades/get-government-trades",
    kind=SourceRefKind.DOCS,
)
DOCS_TRENDS = SourceRef(
    title="Benzinga Ticker Trends API",
    url="https://docs.benzinga.com/api-reference/ticker-trends-api/get-ticker-trend-data",
    kind=SourceRefKind.DOCS,
)
DOCS_SHORT = SourceRef(
    title="Benzinga Market Data: short interest",
    url="https://docs.benzinga.com/api-reference/market-data/get-short-interest-data",
    kind=SourceRefKind.DOCS,
)
DOCS_QUOTES = SourceRef(
    title="Benzinga delayed quotes API",
    url="https://docs.benzinga.com/api-reference/quotedelayed/get-delayed-quotes",
    kind=SourceRefKind.DOCS,
)
DOCS_BARS = SourceRef(
    title="Benzinga historical bars API",
    url="https://docs.benzinga.com/api-reference/bars/get-bars",
    kind=SourceRefKind.DOCS,
)
DOCS_LOGOS = SourceRef(
    title="Benzinga Logos API: overview",
    url="https://docs.benzinga.com/api-reference/logos-api/overview",
    kind=SourceRefKind.DOCS,
)
SITE_TRANSCRIPTS = SourceRef(
    title="Benzinga conference call transcripts product page",
    url="https://www.benzinga.com/apis/cloud-product/conference-call-transcripts/",
    kind=SourceRefKind.DOCS,
)
SITE_CLICKSTREAM = SourceRef(
    title="Benzinga trending tickers product page",
    url="https://www.benzinga.com/apis/cloud-product/trending-tickers/",
    kind=SourceRefKind.DOCS,
)


def _s(
    order: int,
    kind: SlideKind,
    title: str,
    body: str,
    *,
    refs: tuple[SourceRef, ...] = (),
    checkpoint: str | None = None,
    asset: LessonAsset | None = None,
) -> Slide:
    return Slide(
        order=order,
        kind=kind,
        title=title,
        body=body,
        references=refs,
        checkpoint_prompt=checkpoint,
        asset=asset,
    )


def _diagram(key: str, caption: str, alt: str) -> LessonAsset:
    """A course diagram (GRS-0225 toolchain). The drawing is generated from the SceneSpec under
    `design/motion/courses/benzinga/`; the caption and alt text are written here, beside the slide
    they belong to, because they are prose and a generator has no business writing them.

    `SVG[key]` raises on an unknown key rather than returning a placeholder — a slide that silently
    lost its diagram would still render, and look finished."""
    return LessonAsset(caption=caption, alt=alt, svg=SVG[key])


# --- Section 1 — What Benzinga is, and what it is not --------------------------------------

_S1_BODY = (
    "By the end of this lesson you can say, without notes, what Benzinga sells, which half of the "
    "company your commission comes from, and three things it explicitly does not do. That last part"
    "is the one that earns you credibility: Benzinga is a name most people in finance have seen on "
    "a retail website, so a buyer's first assumption is usually wrong, and correcting it yourself "
    "is far better than having their engineering team correct it in month three."
)

_SECTION_1_SLIDES: tuple[Slide, ...] = (
    _s(
        0,
        SlideKind.CONCEPT,
        "The one-sentence version",
        "Benzinga licenses financial news, market events and alternative datasets to platforms, by "
        "API. A brokerage, a wealth app or a bank embeds Benzinga's content and data into its own "
        "product so its users get news, calendars and signals without the platform employing a "
        "newsroom. Hold on to the words *to platforms*: the customer is a business, not an "
        "investor.",
        refs=(CATALOGUE,),
    ),
    _s(
        1,
        SlideKind.CONCEPT,
        "Two businesses, and only one is yours",
        "Benzinga runs a **media business** (benzinga.com, which Benzinga reports at roughly 14 "
        "million monthly users) and a **data-licensing business** (32 products sold by API). Your "
        "commission is on the second. Advisors who have read the website tend to pitch the "
        "website, which is a conversation with no product and no budget attached to it.",
        refs=(CATALOGUE,),
        asset=_diagram(
            "two_arms",
            "Two businesses, one brand, and only the right-hand one is a commission conversation.",
            "Two panels side by side. On the left, the media business: benzinga.com, around 14 "
            "million monthly users, read by retail investors, labelled 'not what you sell'. On the "
            "right and filled in dark green, the data business: 32 products licensed by API, bought"
            "by platforms, labelled 'this is the 15%'. A line beneath reads: the audience on the "
            "left is why the data on the right is worth buying.",
        ),
    ),
    _s(
        2,
        SlideKind.CONCEPT,
        "Why the media half still matters commercially",
        "The audience is not a distraction, it is the moat. Two of the datasets Benzinga sells "
        "exist only because it owns a large retail readership: ticker-level clickstream and "
        "trending-ticker attention data are derived from page views on its own properties. A "
        "competitor with no audience cannot manufacture those, at any price. So the media business "
        "is what makes part of the data business impossible to copy.",
        refs=(SITE_CLICKSTREAM,),
    ),
    _s(
        3,
        SlideKind.CONCEPT,
        "The newsroom is the other thing being sold",
        "Benzinga's flagship newsfeed is written by its own staff journalists rather than "
        "aggregated from other wires. The catalogue is explicit that this is the differentiator: "
        "originating content in-house means no duplication and no aggregation lag. When a buyer "
        "asks why they should not just take a cheaper aggregated feed, this is the answer.",
        refs=(DOCS_NEWS,),
    ),
    _s(
        4,
        SlideKind.CONCEPT,
        "What Benzinga is NOT, part one: a terminal",
        "It has no desktop application, no chat, no order routing, no analytics workbench. It is a "
        "layer that goes *inside* somebody else's product. If a prospect starts comparing it to "
        "Bloomberg or FactSet, they have misunderstood the category, and the comparison will make "
        "Benzinga look thin against products that cost twenty times more.",
        refs=(CATALOGUE,),
    ),
    _s(
        5,
        SlideKind.CONCEPT,
        "What Benzinga is NOT, part two: a fundamentals engine",
        "There are no company financial statements, no normalised ratio history, no estimates "
        "database of its own. Benzinga carries analyst *actions* and corporate *events*. If a "
        "client needs ten years of restated segment revenue, that is a different vendor entirely, "
        "and saying so costs you nothing while pretending otherwise costs you the account.",
        refs=(CATALOGUE,),
    ),
    _s(
        6,
        SlideKind.CONCEPT,
        "What Benzinga is NOT, part three: a real-time quote source",
        "The market-data family tops out at **15-minute delayed quotes**. The catalogue is direct "
        "about why that is a feature for some buyers: no per-user exchange fees, which is a large "
        "cost line for a young platform. But it is not a real-time tick feed, and a trading "
        "platform that needs live quotes needs an exchange feed alongside.",
        refs=(DOCS_QUOTES,),
    ),
    _s(
        7,
        SlideKind.EXAMPLE,
        "The three sentences that make you credible",
        '"Benzinga is a news, events and signals layer you embed in your own product. It is not a '
        "terminal, it does not carry company fundamentals, and its quotes are 15-minute delayed "
        "rather than real-time. What it is unusually good at is editorial coverage at speed and "
        'event data you can put on a forward calendar." Say that in the first ten minutes.',
        refs=(CATALOGUE,),
    ),
    _s(
        8,
        SlideKind.CONCEPT,
        "How Bruntsfield sits in the deal",
        "Bruntsfield is a reseller. The client contracts through us, we take the reseller margin, "
        "and your share of it comes off the Earnings schedule rather than out of a slide. Check "
        "your live rate on the Earnings page before any pricing conversation, because a rate you "
        "remembered from a course is a rate that has already changed once.",
    ),
    _s(
        9,
        SlideKind.CONCEPT,
        "Where the company came from, carefully",
        "Benzinga was founded in Detroit around 2009 to 2010 — public sources disagree on the "
        "year, so do not state one. It was acquired by Beringer Capital; the reported figure is "
        "roughly $300 million and the actual terms were undisclosed. If a prospect asks, "
        '"reportedly around'
        '$300 million, terms were not disclosed" is the honest answer and it is enough.',
    ),
    _s(
        10,
        SlideKind.CONCEPT,
        "Attribute, never assert",
        "Benzinga publishes audience figures, client names and accuracy statistics. Some are "
        "audited and say so; most are the company's own claims. In a regulated firm the difference "
        'matters, and an advisor who says "Benzinga reports" rather than "it is" is the '
        "advisor the"
        "compliance officer trusts on the second call.",
    ),
    _s(
        11,
        SlideKind.WALKTHROUGH,
        "Open the catalogue and orient yourself",
        "Open `data/gtm/sources/benzinga-product-catalog.xlsx`. One sheet, `Full Catalog`, 32 "
        "product rows and fourteen columns. Read the column headers before any of the rows: "
        "Category, Product Name, Description, Update Frequency, History, Coverage Universe, Daily "
        "Volume, Key Data Fields, Delivery Method, Output Format, Use Case, Key Differentiators, "
        "and two URLs. Those columns are the shape of every product conversation you will have.",
        refs=(CATALOGUE,),
    ),
    _s(
        12,
        SlideKind.WALKTHROUGH,
        "Find the four category bands",
        "Scroll the Category column. You will see four banded groups: Newswire & Content, "
        "Calendar, Alternative Data, Market Data. Every one of the 32 products sits in exactly "
        "one. Count how many rows fall in each band and write the four numbers down — you will use "
        "them constantly and they are the subject of the next section.",
        refs=(CATALOGUE,),
    ),
    _s(
        13,
        SlideKind.WALKTHROUGH,
        "Read one product row properly",
        "Find `Why is it Moving Feed` and read every column. Note the shape of the answer: about "
        "100 items a day covering about 200 stocks, human-written, strict SLAs for NYSE and Nasdaq "
        "listings, REST and streaming, JSON or XML. That is a complete product understanding in "
        "thirty seconds of reading, and it is the level of specificity a buyer expects from you.",
        refs=(DOCS_WIIM,),
    ),
    _s(
        14,
        SlideKind.WALKTHROUGH,
        "Check a claim against the docs",
        "Take the earnings-calendar accuracy figure from the catalogue and find it in Benzinga's "
        "own documentation. Doing this once teaches you where the docs live and how they are "
        "organised, and it is the habit that keeps you from repeating a number you cannot source.",
        refs=(DOCS_EARNINGS,),
    ),
    _s(
        15,
        SlideKind.EXAMPLE,
        "A first meeting that went wrong",
        'An advisor opens with "Benzinga is like a cheaper Bloomberg for your platform." The Head '
        "of Product asks whether it carries real-time quotes and ten-year fundamentals. Both "
        "answers are no. The meeting is now about what the product lacks, and every genuine "
        "strength — the newsroom, the calendars, the attention data — never gets said.",
    ),
    _s(
        16,
        SlideKind.EXAMPLE,
        "The same meeting, done properly",
        '"You employ two people to write market commentary and you still only cover your top forty '
        "tickers. Benzinga's newsroom writes 200 to 250 full articles a day with images and ticker "
        "tagging, and a one-sentence explanation for roughly 200 moving stocks. It goes into your "
        'app under your brand." Now the conversation is about their problem.',
        refs=(DOCS_NEWS, DOCS_WIIM),
    ),
    _s(
        17,
        SlideKind.CONCEPT,
        "The two objections you will hear first",
        'One: "we already have a news feed." Two: "our users do not read news." Both are '
        "answerable"
        "and neither is answered by listing products. The first is answered by asking *which* feed "
        "and whether it is aggregated. The second is answered by moving off news entirely and onto "
        "calendars or attention data, which are not news at all.",
    ),
    _s(
        18,
        SlideKind.CONCEPT,
        'Why "we already have a feed" is usually an opening',
        "Most platforms have an aggregated wire — the same press releases everyone else has. That "
        "is a different product from an in-house newsroom, and it explains why their news section "
        'reads identically to their competitors\'. Asking "is it originated or aggregated?" is a '
        "better move than asserting anything.",
        refs=(DOCS_NEWS, DOCS_PRESS),
    ),
    _s(
        19,
        SlideKind.CONCEPT,
        "The compliance question, asked before they ask it",
        "Any platform embedding third-party content will ask what they are allowed to do with it: "
        "can they redistribute, must they attribute, do they need per-user entitlements. Those "
        "terms are per-contract and were not publicly readable. Say that plainly and get it in "
        "writing per deal. Guessing here creates a promise the contract will not support.",
    ),
    _s(
        20,
        SlideKind.CONCEPT,
        "Two questions that qualify an account fast",
        '"What do your users ask you that you cannot currently answer?" and "what can your '
        "engineering team actually consume — a scheduled pull, an always-on stream, or a "
        'file?" The'
        "first finds the product. The second finds out whether the deal is a six-week integration "
        "or a six-month one. Section 3 is entirely about the second question.",
    ),
    _s(
        21,
        SlideKind.CHECKPOINT,
        "Say the negative version out loud",
        "Before the section test, say the three things Benzinga is not, out loud, without looking. "
        "Not a terminal. No company fundamentals. Quotes are 15-minute delayed, not real-time. If "
        "you cannot produce all three from memory, you will not produce them under pressure in a "
        "meeting, which is exactly where they earn their value.",
        checkpoint=("Say all three 'is not' statements aloud from memory."),
    ),
    _s(
        22,
        SlideKind.CHECKPOINT,
        "Write your own opening",
        "Write four sentences you would actually say to a mid-size retail brokerage in the first "
        "five minutes. One sentence on what Benzinga is, one on what it is not, one on the newsroom"
        "or the audience-derived data, and one question back to them. Keep it; you will refine it "
        "in section 8 once you know the families.",
        checkpoint=("Write your four-sentence opening and keep it for section 8."),
    ),
    _s(
        23,
        SlideKind.CONCEPT,
        "What the next seven sections do",
        "Section 2 gives you the four families so 32 products become four ideas. Section 3 is how "
        "the data physically arrives, which is where deals get scoped. Sections 4, 5 and 6 take one"
        "family each. Section 7 maps families to buyers. Section 8 is the sale. You do not need to "
        "memorise the catalogue; you need to know which family answers a question.",
    ),
)


SECTION_1_TEST = SectionTest(
    pass_mark=0.8,
    questions=(
        TestQuestion(
            prompt=("Which half of Benzinga does your commission come from?"),
            options=(
                "benzinga.com advertising revenue",
                "The data-licensing business, sold by API to platforms",
                "Retail subscriptions to Benzinga Pro",
                "Both equally",
            ),
            answer_index=1,
            explanation=(
                "The media business is the moat, not the product. It is why the clickstream data "
                "exists and why the newsroom is credible, but the commission is on data licensing."
            ),
        ),
        TestQuestion(
            prompt=("A prospect asks whether Benzinga can replace their real-time quote feed."),
            options=(
                "Yes, the market-data family covers it",
                "No. Benzinga tops out at 15-minute delayed quotes, which avoids\n"
                " per-user exchange fees but is not a real-time feed",
                "Yes, if they licence the streaming delivery option",
                "Only for NYSE and Nasdaq listings",
            ),
            answer_index=1,
            explanation=(
                "Delayed quotes are a genuine cost advantage for a young platform and a genuine gap"
                "for a trading one. Streaming changes how data arrives, never what it is."
            ),
        ),
        TestQuestion(
            prompt=("Why can no competitor replicate Benzinga's ticker clickstream dataset?"),
            options=(
                "It is patented",
                "It is derived from page views on Benzinga's own large retail audience,\n"
                " which a vendor without an audience cannot manufacture",
                "It is licensed exclusively from the exchanges",
                "It requires FINRA authorisation",
            ),
            answer_index=1,
            explanation=(
                "This is the strongest structural argument in the catalogue. The media business "
                "most advisors dismiss is what makes this part of the data business uncopyable."
            ),
        ),
        TestQuestion(
            prompt=("How should you answer a question about the Beringer acquisition price?"),
            options=(
                "State $300 million as fact",
                "Say it was reportedly around $300 million and that terms were not\n disclosed",
                "Refuse to discuss it",
                "Say the figure is confidential",
            ),
            answer_index=1,
            explanation=(
                "Attribute, never assert. The figure is reported and the terms were undisclosed; "
                "saying both is honest, sufficient, and makes you more credible on everything else."
            ),
        ),
        TestQuestion(
            prompt=("What is Benzinga's flagship newsfeed differentiator?"),
            options=(
                "It aggregates more wires than anyone else",
                "Content is written in-house by Benzinga staff journalists rather than\n"
                " aggregated, so there is no duplication and no aggregation lag",
                "It is the cheapest feed available",
                "It includes real-time pricing alongside each story",
            ),
            answer_index=1,
            explanation=(
                "Originated versus aggregated is the distinction that answers 'we already have a "
                "news feed', which is the first objection you will hear."
            ),
        ),
        TestQuestion(
            prompt=(
                "A client asks what they may redistribute to their own users. What do you say?"
            ),
            options=(
                "Anything in the licensed feed",
                "That redistribution, attribution and entitlement terms are per-contract,\n"
                " and you will get the answer in writing for their deal",
                "Nothing may be redistributed",
                "Only headlines, not article bodies",
            ),
            answer_index=1,
            explanation=(
                "These terms were not publicly readable and vary per contract. Guessing creates a "
                "promise the contract will not support, which is the expensive kind of mistake."
            ),
        ),
    ),
)


def section_1() -> CourseModule:
    '"""Section 1: What Benzinga is, and what it is not."""'
    return CourseModule(
        id=_id("module", "what-it-is"),
        title="What Benzinga is, and what it is not",
        order=0,
        lessons=(
            Lesson(
                id=_id("lesson", "what-it-is"),
                title="What Benzinga actually sells",
                body=_S1_BODY,
                order=0,
                slides=_SECTION_1_SLIDES,
                drill_topics=("product:benzinga:what-it-is",),
                measurement=(
                    "You can describe Benzinga to a platform buyer in four sentences, including "
                    "three things it does not do, without notes."
                ),
            ),
        ),
        section_test=SECTION_1_TEST,
    )


_S2_BODY = (
    "Thirty-two products is too many to hold in your head, and an advisor who tries to "
    "remember the"
    "list will sell none of them. By the end of this lesson you will hold four ideas instead, each "
    "with its own job, its own buyer and its own objection. In a meeting you qualify the family, "
    "never the product: the product is a detail you look up once you know which of the four "
    "questions the client is actually asking."
)

_SECTION_2_SLIDES: tuple[Slide, ...] = (
    _s(
        0,
        SlideKind.CONCEPT,
        "Four families, and the numbers matter",
        "The catalogue bands its 32 products into four categories: **Newswire & Content** (8), "
        "**Calendar** (11), **Alternative Data** (9) and **Market Data** (4). Calendar is the "
        "biggest family and Market Data the smallest, which is the opposite of what most people "
        "assume about a company they think of as a news site.",
        refs=(CATALOGUE,),
        asset=_diagram(
            "four_families",
            "Thirty-two products become four ideas, each with one job.",
            "Four cards in a row, each showing a count and the job that family does. Newswire and "
            "Content, eight products, what a user READS. Calendar, eleven products, what a user "
            "PLANS around. Alternative Data, nine products, what a desk TRADES on. Market Data, "
            "four products, what a screen NEEDS. A line beneath reads: each family has its own "
            "buyer, budget and objection.",
        ),
    ),
    _s(
        1,
        SlideKind.CONCEPT,
        "The one-word job of each family",
        "Content is what a user **reads**. Calendar is what a user **plans around**. Alternative "
        "data is what a desk **trades on**. Market data is what a screen **needs** in order to look"
        "like a finance product at all. Four verbs. If you can map a client's problem onto one of "
        "those verbs you have found the family without opening the catalogue.",
        refs=(CATALOGUE,),
    ),
    _s(
        2,
        SlideKind.CONCEPT,
        "Why the family is the unit of the conversation",
        'A buyer does not want a product list, they want their problem solved. "Your users keep '
        'asking why a stock moved" is a content problem. "Your users cannot see what is '
        "coming this"
        'week" is a calendar problem. Naming the family shows you understood the problem; reciting '
        "products shows you did not listen.",
    ),
    _s(
        3,
        SlideKind.CONCEPT,
        "Family one: Newswire & Content, in outline",
        "Eight products, all editorial or editorial-derived: the flagship US equities newsfeed, "
        "aggregated press releases, the one-sentence Why Is It Moving feed, video news, AI-assisted"
        "bull and bear summaries, structured analyst-report insights, and two newer sector feeds "
        "covering prediction markets and private markets. Section 4 takes these one by one.",
        refs=(DOCS_NEWS,),
    ),
    _s(
        4,
        SlideKind.CONCEPT,
        "Family two: Calendar, in outline",
        "Eleven products, and every one is a dated event: earnings, analyst ratings, guidance, FDA "
        "decisions, macro releases, mergers, IPOs, secondary offerings, dividends, splits, and live"
        "conference-call transcripts. This is the family that lets a platform show a user what is "
        "*about to happen*, which almost nothing else in the catalogue does. Section 5.",
        refs=(DOCS_EARNINGS,),
    ),
    _s(
        5,
        SlideKind.CONCEPT,
        "Family three: Alternative Data, in outline",
        "Nine products, and the least homogeneous family. Options flow and block trades, insider "
        "and congressional trades, short interest, and three audience-derived datasets built from "
        "Benzinga's own traffic. Highest price per product, narrowest buyer, and the family where "
        "you must be most careful about what you claim. Section 6.",
        refs=(DOCS_OPTIONS,),
    ),
    _s(
        6,
        SlideKind.CONCEPT,
        "Family four: Market Data, in outline",
        "Four products, and the least glamorous: market movers, corporate logos, historical OHLCV "
        "bars, and 15-minute delayed quotes. Nobody buys a platform *because* of these, and every "
        "platform needs them. They are what makes a build possible rather than what makes it "
        "compelling.",
        refs=(DOCS_QUOTES, DOCS_LOGOS),
    ),
    _s(
        7,
        SlideKind.EXAMPLE,
        "Corporate logos: the least interesting, most bought",
        "A single API call returns a CDN-hosted logo URL for a ticker, covering international "
        "equities, ETFs, funds and the top 100 cryptocurrencies. It is unexciting and it removes "
        "weeks of engineering plus an asset-hosting problem. Products like this close deals because"
        "they are trivially easy to say yes to.",
        refs=(DOCS_LOGOS,),
    ),
    _s(
        8,
        SlideKind.CONCEPT,
        "The families have very different histories",
        "Depth of history varies enormously and it matters to a quant buyer: insider trades and "
        "congressional trades run back to 2003, historical bars to 2000, splits and the newsfeed to"
        "2010, earnings to 2012, options flow to 2019, clickstream and block trades to 2021, "
        "transcripts to 2023, prediction markets to 2024. A backtest needs history; a display "
        "widget does not.",
        refs=(CATALOGUE,),
    ),
    _s(
        9,
        SlideKind.CONCEPT,
        "Coverage universe is the other axis",
        "Most US-equity products cover the Wilshire 5000 plus roughly a thousand additional names. "
        "Conference-call transcripts cover the Russell 3000 including LSE listings. The economics "
        'calendar is global across 50-plus countries. Corporate logos are international. So "does '
        'it cover our market?" has a different answer per product, and the catalogue column is the '
        "place to check rather than guess.",
        refs=(CATALOGUE,),
    ),
    _s(
        10,
        SlideKind.CONCEPT,
        "Volume tells you what a product actually is",
        "Look at daily volume before you pitch anything. The press-release feed carries 1,000 to "
        "2,000 items a day; Why Is It Moving carries about 100. One is a firehose for a machine, "
        "the other is a curated layer for a human. Same family, completely different integration, "
        "completely different pitch.",
        refs=(DOCS_PRESS, DOCS_WIIM),
    ),
    _s(
        11,
        SlideKind.WALKTHROUGH,
        "Sort the catalogue by category and count",
        "In the spreadsheet, group the rows by the Category column and confirm the four counts: "
        "eight, eleven, nine, four. If your numbers differ, you have miscounted a banded header row"
        "as a product. Getting this right matters because you will quote these counts in meetings "
        "as shorthand for the shape of the offer.",
        refs=(CATALOGUE,),
    ),
    _s(
        12,
        SlideKind.WALKTHROUGH,
        "Build your own one-line-per-family crib",
        "Write four lines, one per family: the count, the verb, and the single product you would "
        'lead with. Something like "Calendar, 11, plans around, lead with earnings." Four lines is '
        "a thing you can hold; a 32-row spreadsheet is not. This crib is the actual deliverable of "
        "this section.",
        refs=(CATALOGUE,),
    ),
    _s(
        13,
        SlideKind.WALKTHROUGH,
        "Find the two products that are not APIs",
        "Filter the Delivery Method column. Two products — the ticker clickstream and the "
        "logos-plus-analytics engagement dataset — are delivered by FTP or S3 as flat files, not "
        "by REST. Note which two. Promising an API for a product that ships as a file is the kind "
        "of detail that surfaces in week three of an integration.",
        refs=(CATALOGUE,),
    ),
    _s(
        14,
        SlideKind.WALKTHROUGH,
        "Find the one product that is CSV only",
        "Check the Output Format column across the calendar family. The mergers and acquisitions "
        "dataset is listed as CSV where its siblings offer JSON and XML. A client whose pipeline "
        "only ingests JSON has a small piece of work to do, and it is much better that you raise it"
        "than that they discover it.",
        refs=(CATALOGUE,),
    ),
    _s(
        15,
        SlideKind.EXAMPLE,
        "Mapping a real request to a family",
        'A wealth platform says: "our clients log in once a quarter and we have nothing to tell '
        'them." That is not a news problem, it is a calendar problem — dividends, ex-dates, '
        "earnings dates for their holdings give a reason to return. Reaching for the newsfeed here "
        "is the obvious answer and the wrong one.",
        refs=(DOCS_EARNINGS,),
    ),
    _s(
        16,
        SlideKind.EXAMPLE,
        "Mapping a harder request",
        'A quant fund says: "we want retail sentiment." Careful. Alternative data has three '
        "audience-derived products and they are not interchangeable: trending tickers gives scaled "
        "and smoothed metrics ready for a factor model, the raw clickstream gives 10-minute buckets"
        "of page views, and the partner-network dataset attributes interest to an anonymised "
        "platform. Ask which shape they need.",
        refs=(DOCS_TRENDS, SITE_CLICKSTREAM),
    ),
    _s(
        17,
        SlideKind.EXAMPLE,
        "A request that is two families",
        '"When a stock moves we want to show users what happened and what is coming." That is Why '
        "Is It Moving from content plus the earnings and dividends calendars. Two families, one "
        "user story, and a materially bigger deal than either half. Noticing the pairing is where "
        "the value of knowing the families shows up.",
        refs=(DOCS_WIIM, DOCS_EARNINGS),
    ),
    _s(
        18,
        SlideKind.CONCEPT,
        "Products that pair, by design",
        "The catalogue names its own pairings, and they are worth knowing because they are natural "
        "upsells. Unusual options activity pairs with insider trades to track smart money across "
        "two dimensions. Bull and bear summaries pair with analyst ratings for full coverage. "
        "Market movers pair with Why Is It Moving so a mover has an explanation beside it.",
        refs=(DOCS_OPTIONS, DOCS_RATINGS),
    ),
    _s(
        19,
        SlideKind.CONCEPT,
        "The objection is different per family",
        'Content: "we already have a feed." Calendar: "can we trust the dates?" Alternative data: '
        '"can you prove it works?" Market data: "why not just use the free source?" Four families, '
        "four objections, and each has an honest answer you will learn in its own section. "
        "Preparing the wrong one is why meetings stall.",
    ),
    _s(
        20,
        SlideKind.CONCEPT,
        "What is deliberately absent from all four",
        "No fundamentals. No real-time quotes. No order routing, no custody, no research reports in"
        "full, no ESG scores, no credit data. If a client's need falls outside the four verbs, "
        "Benzinga is not the answer and telling them so early is worth more than the deal you would"
        "have lost anyway.",
    ),
    _s(
        21,
        SlideKind.CHECKPOINT,
        "Recite the four families cold",
        "Without looking: name the four families, their counts, and their verb. Then name one "
        "product from each. If any of the four is missing, go back to your crib — this is the "
        "single piece of recall the rest of the course assumes you have.",
        checkpoint=(
            "Recite all four families, counts and verbs from memory, plus one product each."
        ),
    ),
    _s(
        22,
        SlideKind.CHECKPOINT,
        "Route five requests without the catalogue",
        "Route each of these to a family, from memory: (1) users ask why a stock dropped; (2) we "
        "need company logos; (3) we want to flag congressional trading; (4) users want to know when"
        "their holdings report; (5) we need 20 years of daily bars to backtest. Write your five "
        "answers down before checking.",
        checkpoint=("Route all five requests to a family from memory, then check yourself."),
    ),
    _s(
        23,
        SlideKind.CONCEPT,
        "Where this goes next",
        "You now have the map. Before the three family sections, section 3 covers how the data "
        "physically arrives, because that question decides the size and length of every deal and "
        "the advisor is usually the first person in the room in a position to ask it.",
    ),
)


SECTION_2_TEST = SectionTest(
    pass_mark=0.8,
    questions=(
        TestQuestion(
            prompt=("Which is the largest of the four product families?"),
            options=(
                "Newswire & Content, with 8",
                "Calendar, with 11",
                "Alternative Data, with 9",
                "Market Data, with 4",
            ),
            answer_index=1,
            explanation=(
                "Calendar is the biggest family, which surprises people who think of Benzinga as a "
                "news site. Event data is the larger half of what it actually licenses."
            ),
        ),
        TestQuestion(
            prompt=(
                "A wealth platform says clients log in once a quarter with nothing to see. Which "
                "family?"
            ),
            options=(
                "Newswire & Content, for the newsfeed",
                "Calendar, so holdings have dated upcoming events to return for",
                "Alternative Data, for sentiment",
                "Market Data, for delayed quotes",
            ),
            answer_index=1,
            explanation=(
                "Reaching for news is the obvious answer and the wrong one. The problem is a lack "
                "of forward-looking reasons to return, which is precisely what calendars provide."
            ),
        ),
        TestQuestion(
            prompt=("Two products are delivered as flat files rather than by REST API. Which?"),
            options=(
                "Historical bars and delayed quotes",
                "The ticker clickstream and the partner-network engagement dataset,\n"
                " both by FTP or S3",
                "Corporate logos and market movers",
                "SEC filings and short interest",
            ),
            answer_index=1,
            explanation=(
                "Both audience-derived flat-file products. Promising an API for a product that "
                "ships as a file is the kind of thing that surfaces in week three of an "
                "integration."
            ),
        ),
        TestQuestion(
            prompt=("Why qualify the family rather than the product in a first meeting?"),
            options=(
                "Because product names change",
                "Because the buyer wants their problem solved, and naming the family shows\n"
                " you understood it where reciting products shows you did not listen",
                "Because pricing is set per family",
                "Because only families are covered by the reseller agreement",
            ),
            answer_index=1,
            explanation=(
                "Four verbs — reads, plans around, trades on, needs — map a client's problem to a "
                "family without opening the catalogue. The product is a detail you look up after."
            ),
        ),
        TestQuestion(
            prompt=(
                "Which pair does the catalogue itself suggest selling together for smart-money "
                "tracking?"
            ),
            options=(
                "Corporate logos and market movers",
                "Unusual options activity and insider trades",
                "Earnings calendar and dividends calendar",
                "Delayed quotes and historical bars",
            ),
            answer_index=1,
            explanation=(
                "The catalogue names this pairing explicitly. Knowing the designed pairings is "
                "where family knowledge turns into a materially bigger deal."
            ),
        ),
        TestQuestion(
            prompt=("A quant fund asks for 'retail sentiment'. What is the right next move?"),
            options=(
                "Quote the trending-tickers product",
                "Ask which shape they need, because three audience-derived products differ:\n"
                " scaled model-ready metrics, raw 10-minute clickstream, or partner-attributed",
                "Explain that Benzinga has no sentiment data",
                "Offer the newsfeed with sentiment tagging",
            ),
            answer_index=1,
            explanation=(
                "The three are not interchangeable. Picking one before asking is how you deliver a "
                "dataset the client's pipeline cannot use."
            ),
        ),
    ),
)


def section_2() -> CourseModule:
    '"""Section 2: The catalogue, in four families."""'
    return CourseModule(
        id=_id("module", "four-families"),
        title="The catalogue, in four families",
        order=1,
        lessons=(
            Lesson(
                id=_id("lesson", "four-families"),
                title="Thirty-two products, four ideas",
                body=_S2_BODY,
                order=0,
                slides=_SECTION_2_SLIDES,
                drill_topics=("product:benzinga:families",),
                measurement=(
                    "You can name the four families, their counts and their verb from memory, and "
                    "route an unseen client request to the right family without the catalogue."
                ),
            ),
        ),
        section_test=SECTION_2_TEST,
    )


# --- Section 3 — How the data arrives, and what that costs to build ------------------------

_S3_BODY = (
    "This is the least glamorous section in the course and the one that saves the most deals. By "
    "the end of it you will know the three ways Benzinga data physically reaches a client, what "
    "each one obliges the client's engineers to build, and the three questions to ask before you "
    "ever put a timeline in an email. An advisor who skips this promises six weeks and delivers "
    "six months, and the damage lands on the account rather than on the calendar."
)

_SECTION_3_SLIDES: tuple[Slide, ...] = (
    _s(
        0,
        SlideKind.CONCEPT,
        "The question that sizes the deal",
        "Two clients can buy the same product and have completely different projects. What "
        "separates them is not the data, it is how the data arrives and whether they already "
        "have somewhere to put it. You are usually the first person in the room in a position "
        "to ask, and asking early is the difference between a scoped deal and a slipped one.",
        refs=(DOCS_INTRO,),
    ),
    _s(
        1,
        SlideKind.CONCEPT,
        "Three delivery methods, three different builds",
        "Benzinga delivers by **REST** (you pull, on your own schedule), by **TCP streaming** "
        "(it pushes, as things happen), and by **FTP or S3** (a file lands in a bucket). Those "
        "are not three flavours of the same integration. They are a scheduled job, an "
        "always-on service, and a storage location, and the client may have none of them.",
        refs=(DOCS_INTRO,),
        asset=_diagram(
            "delivery_paths",
            "Three delivery methods, and what each one obliges the client to build.",
            "Three lanes. REST, described as you ask on your schedule, requires a scheduled "
            "job. TCP push, highlighted in dark green and described as it arrives as it "
            "happens, requires an always-on consumer. FTP or S3, a file lands in buckets, "
            "requires somewhere to put it. A warning beneath reads: ask which one they can "
            "consume before you promise a timeline.",
        ),
    ),
    _s(
        2,
        SlideKind.CONCEPT,
        "REST: the default, and the cheapest to adopt",
        "Almost every product in the catalogue offers a REST endpoint. The client calls it on a "
        "schedule they choose, which means their side is a cron job and a database write. This "
        "is the path a small engineering team can ship in days, and it is the right answer far "
        "more often than a streaming pitch suggests.",
        refs=(DOCS_INTRO,),
    ),
    _s(
        3,
        SlideKind.CONCEPT,
        "TCP streaming: real speed, real obligation",
        "The newsfeed, press releases, Why Is It Moving and analyst ratings also offer a push "
        "stream. The data arrives as it happens, with no polling delay. The cost is on the "
        "client: an always-on consumer process, a reconnect strategy, and somewhere for "
        "messages to go when their consumer is down. That is a service, not a script.",
        refs=(DOCS_NEWS, DOCS_RATINGS),
    ),
    _s(
        4,
        SlideKind.CONCEPT,
        "When streaming is genuinely worth it",
        "Push earns its complexity when latency changes a user's behaviour or a machine's "
        "decision: a trading platform surfacing a catalyst, an event-driven strategy acting on "
        "a press release, an alerting product. If the client displays news on a page a user "
        "refreshes anyway, a five-minute pull is indistinguishable and far cheaper.",
        refs=(DOCS_PRESS,),
    ),
    _s(
        5,
        SlideKind.CONCEPT,
        "Flat files: the two products that are not APIs",
        "The ticker clickstream and the partner-network engagement dataset ship by **FTP or "
        "S3** as flat files, in ten-minute buckets. There is no REST endpoint. A client "
        "expecting to call an API for these has to build a file pipeline instead, and that is "
        "the kind of surprise that surfaces in week three rather than week one.",
        refs=(SITE_CLICKSTREAM,),
    ),
    _s(
        6,
        SlideKind.CONCEPT,
        "Why those two are files, not endpoints",
        "It follows from what they are. Both are continuous, high-volume, time-bucketed "
        "aggregates rather than discrete events with an identity. A file per bucket is the "
        "honest shape for that, and a REST endpoint over it would be a worse product wearing a "
        "more familiar interface. Understanding this stops it sounding like a limitation.",
        refs=(DOCS_TRENDS,),
    ),
    _s(
        7,
        SlideKind.CONCEPT,
        "Webhooks and alerts, on two products",
        "Conference-call transcripts add webhook and email alerts, and the SEC filings product "
        "offers customisable alerts by company and filing type. Both matter because they let a "
        "client react without polling: the platform is told, rather than having to keep asking. "
        "It is a smaller commitment than a stream and often enough.",
        refs=(SITE_TRANSCRIPTS,),
    ),
    _s(
        8,
        SlideKind.CONCEPT,
        "Output formats, and the one exception",
        "Most products offer JSON, many offer XML, a few offer CSV. Corporate logos return a "
        "CDN URL in JSON plus the PNG or SVG itself. The flat-file products are flat files. "
        "There is one product whose only listed format is CSV, and it is worth knowing which "
        "before a client tells you their pipeline is JSON-only.",
        refs=(CATALOGUE,),
    ),
    _s(
        9,
        SlideKind.EXAMPLE,
        "The CSV-only product",
        "The mergers and acquisitions dataset is listed as **CSV**, where its calendar siblings "
        "offer JSON and XML. For a client whose ingestion is JSON end to end this is a small "
        "piece of work, not a blocker — but it is much better that you raise it than that their "
        "engineer finds it. Raising a small problem yourself buys credibility cheaply.",
        refs=(CATALOGUE,),
    ),
    _s(
        10,
        SlideKind.CONCEPT,
        '"Real-time" is not one thing',
        "Read the update-frequency column carefully. Some products are real-time intraday. "
        "Short interest is bi-monthly from FINRA with an optional daily estimate. Historical "
        "bars update end of day. Corporate logos are static. Bulls Say Bears Say is "
        "event-driven, refreshed when new analyst reports appear. All four are honest; none "
        "means the same thing.",
        refs=(CATALOGUE, DOCS_SHORT),
    ),
    _s(
        11,
        SlideKind.CONCEPT,
        "The 15-minute delay is a pricing decision",
        "Delayed quotes carry **no per-user exchange fees**, which for a platform with many "
        "users is a large cost line removed. That is why the catalogue positions them as the "
        "starting point for a new build rather than a compromise. It is also why they are not "
        "the answer for a trading product, and you should say both halves.",
        refs=(DOCS_QUOTES,),
    ),
    _s(
        12,
        SlideKind.CONCEPT,
        "History depth is a scoping question too",
        "A client backtesting needs years, not a live feed. Historical bars run from 2000, "
        "insider and congressional trades from 2003, splits and the newsfeed from 2010, options "
        "flow from 2019, transcripts from 2023. Ask what they intend to do with it: a backfill "
        "is a different delivery conversation from a subscription.",
        refs=(DOCS_BARS, DOCS_INSIDER),
    ),
    _s(
        13,
        SlideKind.WALKTHROUGH,
        "Read the delivery column across one family",
        "Open the catalogue and read Delivery Method for all eleven calendar products. Note how "
        "many are REST-only, which add streaming, and which add alerts. You will see that the "
        "calendar family is overwhelmingly pull-based, which tells you something real: dated "
        "events do not need pushing, because the date is known in advance.",
        refs=(CATALOGUE,),
    ),
    _s(
        14,
        SlideKind.WALKTHROUGH,
        "Find every product with more than one path",
        "Filter for products offering both REST and streaming. There are only a handful, and "
        "they are all in the content family plus analyst ratings. That is the shortlist for any "
        "client who says latency matters, and knowing it means you never promise a stream for a "
        "product that does not have one.",
        refs=(CATALOGUE, DOCS_RATINGS),
    ),
    _s(
        15,
        SlideKind.WALKTHROUGH,
        "Write down the three integration questions",
        "Write these where you will see them before a first meeting. One: can you consume a "
        "push stream, or is a scheduled pull simpler for you? Two: does your pipeline take "
        "anything other than JSON? Three: do you need history, and how far back? Three "
        "questions, two minutes, and they size the project.",
    ),
    _s(
        16,
        SlideKind.WALKTHROUGH,
        "Rehearse asking them without sounding technical",
        'Say them out loud in a version a Head of Product will answer rather than defer. "Would '
        'your team rather call us on a schedule, or have it pushed to you?" gets an answer. '
        '"Do you support TCP streaming ingestion?" gets "I will have to check", which costs '
        "you a week.",
    ),
    _s(
        17,
        SlideKind.EXAMPLE,
        "A deal that slipped three months",
        'An advisor sells a retail platform on the clickstream dataset as "an API for retail '
        'attention". Their engineers scope a REST integration. Two weeks in they discover it is '
        "an S3 flat-file drop in ten-minute buckets and they have no file ingestion at all. The "
        "product was right; the delivery assumption was never checked.",
        refs=(SITE_CLICKSTREAM,),
    ),
    _s(
        18,
        SlideKind.EXAMPLE,
        "The same deal scoped in one question",
        '"This one ships as files to S3 rather than as an endpoint, in ten-minute buckets. Do '
        'you already ingest files anywhere, or would this be the first?" Asked in the first '
        "meeting, that either confirms a short project or surfaces a real piece of work while "
        "there is still time to price and plan it.",
    ),
    _s(
        19,
        SlideKind.CONCEPT,
        "What never to promise",
        "Do not promise a delivery method you have not read in the catalogue. Do not promise a "
        "latency figure at all. Do not promise a format conversion on Benzinga's side. And do "
        "not promise a timeline: you can promise to get a scoped answer, which is both more "
        "useful and something you can actually deliver.",
    ),
    _s(
        20,
        SlideKind.CONCEPT,
        "Coverage universe, before anyone builds",
        "Most US-equity products cover the Wilshire 5000 plus roughly a thousand more names. "
        "Transcripts cover the Russell 3000 including LSE listings. The economics calendar is "
        'global across more than fifty countries. Logos are international. "Does it cover our '
        'market?" has a per-product answer, and the column is there to be read.',
        refs=(CATALOGUE, SITE_TRANSCRIPTS),
    ),
    _s(
        21,
        SlideKind.CONCEPT,
        "Volume, before anyone sizes storage",
        "The press-release feed carries 1,000 to 2,000 items a day. Why Is It Moving carries "
        "about 100. Unusual options activity is tens of thousands of signals a day. Those are "
        "three completely different storage and rate-limit conversations, and quoting the wrong "
        "order of magnitude makes the rest of your scoping look like guesswork.",
        refs=(DOCS_PRESS, DOCS_WIIM, DOCS_OPTIONS),
    ),
    _s(
        22,
        SlideKind.CHECKPOINT,
        "Name the three paths and their cost, cold",
        "Without looking: the three delivery methods, and for each one the thing the client must "
        "have. Then name the two products that ship as files rather than endpoints. If either "
        "half is missing, you will make the promise this section exists to prevent.",
        checkpoint=(
            "Name the three delivery paths, what each obliges the client to build, and the two "
            "flat-file products, all from memory."
        ),
    ),
    _s(
        23,
        SlideKind.CHECKPOINT,
        "Add the delivery question to your opening",
        "Take the four-sentence opening you wrote in section 1 and add one of the three "
        "integration questions to it. Keep it to five sentences. You are building the thing you "
        "will actually say, one section at a time, rather than a set of notes.",
        checkpoint=(
            "Extend your section-1 opening with a delivery question, still under six sentences."
        ),
    ),
)

SECTION_3_TEST = SectionTest(
    pass_mark=0.8,
    questions=(
        TestQuestion(
            prompt=("Which two products ship as flat files rather than through a REST endpoint?"),
            options=(
                "Historical bars and delayed quotes",
                "The ticker clickstream and the partner-network engagement dataset,\n"
                " by FTP or S3 in ten-minute buckets",
                "Corporate logos and market movers",
                "SEC filings and short interest",
            ),
            answer_index=1,
            explanation=(
                "Both are continuous time-bucketed aggregates rather than discrete events, so a "
                "file per bucket is the honest shape. A client expecting an API has to build a "
                "file pipeline instead."
            ),
        ),
        TestQuestion(
            prompt=("A client says latency matters. What does choosing the push stream cost them?"),
            options=(
                "Nothing, it is the same integration",
                "An always-on consumer, a reconnect strategy, and somewhere for messages\n"
                " to go while their consumer is down",
                "A higher licence fee only",
                "Loss of historical backfill",
            ),
            answer_index=1,
            explanation=(
                "Push is a service on the client's side, not a script. It earns that complexity "
                "when latency changes a user's behaviour or a machine's decision, and not "
                "otherwise."
            ),
        ),
        TestQuestion(
            prompt=(
                "Why does the catalogue position 15-minute delayed quotes as a starting point?"
            ),
            options=(
                "Because real-time is not technically available",
                "Because they carry no per-user exchange fees, removing a large cost line\n"
                " for a platform with many users",
                "Because they are more accurate",
                "Because exchanges require a delay for new platforms",
            ),
            answer_index=1,
            explanation=(
                "It is a pricing advantage, not a compromise — and it is still not the answer for "
                "a trading product. Say both halves."
            ),
        ),
        TestQuestion(
            prompt="Which product's only listed output format is CSV?",
            options=(
                "The earnings calendar",
                "The mergers and acquisitions dataset",
                "Short interest",
                "The IPO calendar",
            ),
            answer_index=1,
            explanation=(
                "Its calendar siblings offer JSON and XML. For a JSON-only pipeline that is a "
                "small piece of work, and raising it yourself buys credibility cheaply."
            ),
        ),
        TestQuestion(
            prompt=(
                "Which phrasing of the delivery question actually gets you an answer in the room?"
            ),
            options=(
                "Do you support TCP streaming ingestion?",
                "Would your team rather call us on a schedule, or have it pushed to you?",
                "What is your message broker?",
                "Can you handle real-time data?",
            ),
            answer_index=1,
            explanation=(
                'The technical phrasing gets "I will have to check", which costs a week. The '
                "plain one gets an answer from the person in front of you."
            ),
        ),
        TestQuestion(
            prompt='"Real-time" appears across the catalogue. What should you check per product?',
            options=(
                "Nothing, it means the same everywhere",
                "The update-frequency column, because it also holds bi-monthly, end-of-day,\n"
                " static and event-driven products",
                "Only whether streaming is offered",
                "The coverage universe instead",
            ),
            answer_index=1,
            explanation=(
                "Short interest is bi-monthly, bars are end-of-day, logos are static, Bulls Say "
                "Bears Say is event-driven. All honest; none the same thing."
            ),
        ),
    ),
)


def section_3() -> CourseModule:
    """Section 3: how the data arrives, and what that obliges the client to build."""
    return CourseModule(
        id=_id("module", "how-it-arrives"),
        title="How it arrives, and what that costs to build",
        order=2,
        lessons=(
            Lesson(
                id=_id("lesson", "how-it-arrives"),
                title="Delivery, formats and the three questions",
                body=_S3_BODY,
                order=0,
                slides=_SECTION_3_SLIDES,
                drill_topics=("product:benzinga:delivery",),
                measurement=(
                    "You can name the three delivery paths and what each obliges the client to "
                    "build, and you ask the delivery question before quoting any timeline."
                ),
            ),
        ),
        section_test=SECTION_3_TEST,
    )


# --- Section 4 — The content layer: what a user reads ---------------------------------------

_S4_BODY = (
    "Eight products, and the family a platform buys to change what its users see. By the end of "
    "this lesson you can name all eight, say which two are the ones you actually lead with, and "
    "answer the objection you will hear more than any other in this course: we already have a news "
    "feed. That objection has a good answer and it is not a louder claim, it is a question."
)

_SECTION_4_SLIDES: tuple[Slide, ...] = (
    _s(
        0,
        SlideKind.CONCEPT,
        "What this family is for",
        "Content is what a user reads. Everything in this family exists to put words on a "
        "screen that a person understands: a story, an explanation, a summary, a video. That "
        "makes it the family with the widest buyer — almost any platform with users has a use "
        "for it — and the one with the most crowded competition.",
        refs=(DOCS_NEWS,),
    ),
    _s(
        1,
        SlideKind.CONCEPT,
        "The flagship: the Premium US Equities Newsfeed",
        "Benzinga's own newsroom, writing 200 to 250 full articles a day with images and ticker "
        "tagging, plus 800 to 1,200 real-time headlines. History from 2010. Coverage is the "
        "Wilshire 5000 plus around a thousand more names, with TSX also available. Fields "
        "include the full article body, the image URL, tickers, channels and sentiment.",
        refs=(DOCS_NEWS,),
    ),
    _s(
        2,
        SlideKind.CONCEPT,
        "Originated, not aggregated, and why that is the pitch",
        "The catalogue's stated differentiator is that this content is written in-house by "
        "Benzinga staff journalists rather than pulled from other wires. That means no "
        "duplication, no aggregation lag, and a feed that does not read identically to every "
        'competitor\'s. It is the whole answer to "we already have a news feed".',
        refs=(DOCS_NEWS,),
    ),
    _s(
        3,
        SlideKind.CONCEPT,
        "Why Is It Moving: the highest-leverage product here",
        "One sentence explaining why a stock or crypto is trading up or down today, written by "
        "Benzinga analysts who read the filings and call the company. Around 100 items a day "
        "covering roughly 200 stocks, with strict SLAs for NYSE and Nasdaq listings and the top "
        "twenty cryptocurrencies by market cap. History from 2019.",
        refs=(DOCS_WIIM,),
        asset=_diagram(
            "the_wiim_moment",
            "The same screen, one sentence apart. This is why the content family gets bought.",
            "Two panels showing the same stock quote. On the left, without the product: a "
            "ticker and minus 6.2 per cent, and the note that the user does not know if this is "
            "a catastrophe or a dividend. On the right, with the product: the same ticker and "
            "the same minus 6.2 per cent, plus one sentence saying it is trading lower after "
            "the company cut full-year guidance. A line beneath reads: one human-written "
            "sentence, and it is why this family is bought.",
        ),
    ),
    _s(
        4,
        SlideKind.CONCEPT,
        "Why one sentence is worth more than ten articles",
        "A number alone produces a support ticket or a panic sale. The same number with one "
        "sentence beside it produces an informed user who stays. Nothing else about the "
        "platform's screen changes. That is an unusually clean value story, and it is why this "
        "product converts in demos where the newsfeed alone does not.",
        refs=(DOCS_WIIM,),
    ),
    _s(
        5,
        SlideKind.CONCEPT,
        "The catalogue's own claim about it, stated carefully",
        "The catalogue says no other vendor provides structured one-sentence catalyst "
        "explanations at this speed and coverage. That is Benzinga's claim about its own "
        "product, and you should attribute it that way. It is a strong claim and it is "
        "plausible; it is still theirs and not an audited fact.",
        refs=(DOCS_WIIM,),
    ),
    _s(
        6,
        SlideKind.CONCEPT,
        "Press releases: the firehose, and a different buyer",
        "Aggregated, real-time, 1,000 to 2,000 items a day from five wires — Business Wire, PR "
        "Newswire, GlobeNewswire, AccessWire and Newsfile — normalised into one endpoint, with "
        "history from 2010. Note the word aggregated: this one is explicitly not originated, and "
        "pretending otherwise undermines the point you made about the newsfeed.",
        refs=(DOCS_PRESS,),
    ),
    _s(
        7,
        SlideKind.CONCEPT,
        "Who actually buys the press-release feed",
        "Not a display buyer. Five wires in one normalised endpoint with raw source text is a "
        "product for machines: event-driven trading, compliance monitoring, corporate-action "
        "detection, quant backtesting. If a client wants something for users to read, this is "
        "the wrong product in the right family.",
        refs=(DOCS_PRESS,),
    ),
    _s(
        8,
        SlideKind.CONCEPT,
        "Bulls Say, Bears Say",
        "AI-assisted summaries of analyst reports, distilled into a structured bull case and "
        "bear case per stock, refreshed when new reports are published, history from 2022. Two "
        "things make it sell: the format is balanced by construction, and it turns sell-side "
        "research into something a retail user can read without training.",
        refs=(CATALOGUE,),
    ),
    _s(
        9,
        SlideKind.CONCEPT,
        "Say the AI part out loud",
        "The catalogue describes these summaries as AI-assisted. In a regulated firm that is a "
        "material detail, and volunteering it is what makes the compliance conversation short "
        "instead of long. It also pairs naturally with the analyst-ratings calendar, which is "
        "structured fact rather than summary.",
        refs=(DOCS_RATINGS,),
    ),
    _s(
        10,
        SlideKind.CONCEPT,
        "Analyst Report Insights",
        "Structured, qualitative summaries of sell-side research: the action taken, the rating, "
        "the price target, the firm and analyst, plus insight text. Around twenty records a day, "
        "history from 2022. It sits between the ratings calendar and Bulls Say Bears Say: more "
        "context than a rating action, less interpretation than a summary.",
        refs=(CATALOGUE,),
    ),
    _s(
        11,
        SlideKind.CONCEPT,
        "Video news",
        "Structured metadata and embed links for Benzinga's own video programming — market open "
        "and close wraps, stock-specific analysis, breaking clips — 5 to 15 a day, ticker "
        "tagged, history from 2018. Delivery is REST only. It is an engagement product for "
        "platforms that already know video works for their audience.",
        refs=(CATALOGUE,),
    ),
    _s(
        12,
        SlideKind.CONCEPT,
        "The two newest feeds, and why they exist",
        "Prediction markets (from 2024, around ten articles a day, covering Kalshi, Polymarket "
        "and similar) and private markets (from 2023, around ten a day, funding rounds, "
        "secondaries, pre-IPO). Both are small and both are early. They are for a platform "
        "expanding past public equities, and they are a reason to talk to one.",
        refs=(CATALOGUE,),
    ),
    _s(
        13,
        SlideKind.CONCEPT,
        "Small volume is not the same as low value",
        "Ten articles a day sounds thin next to two thousand press releases. But the catalogue "
        "notes these are among the first structured API feeds covering a rapidly "
        "institutionalising asset class, and a platform that wants coverage there has almost "
        "nowhere else to get it. Scarcity, not volume, is the argument.",
        refs=(CATALOGUE,),
    ),
    _s(
        14,
        SlideKind.WALKTHROUGH,
        "Read the two lead products side by side",
        "In the catalogue, put the Premium Newsfeed row next to the Why Is It Moving row and "
        "compare volume, coverage, delivery and differentiator. One is 200-plus long articles, "
        "the other around 100 single sentences. Notice that the smaller product is the one with "
        "the SLA, and think about why that is.",
        refs=(DOCS_NEWS, DOCS_WIIM),
    ),
    _s(
        15,
        SlideKind.WALKTHROUGH,
        "Sort the family by daily volume",
        "Order all eight by daily volume and read the list top to bottom: press releases, the "
        "newsfeed, Why Is It Moving, analyst insights, video, then the two sector feeds. That "
        "ordering is also roughly an ordering from machine-facing to human-facing, which is a "
        "useful thing to have in your head.",
        refs=(CATALOGUE,),
    ),
    _s(
        16,
        SlideKind.WALKTHROUGH,
        "Draft the originated-versus-aggregated question",
        "Write the exact sentence you will use when a prospect says they already have news. "
        'Something close to: "Is your current feed originated or aggregated — is somebody '
        'writing it, or is it the same wire everyone else carries?" Then stop and let them '
        "answer. The question does the work; you do not need the claim.",
        refs=(DOCS_NEWS,),
    ),
    _s(
        17,
        SlideKind.EXAMPLE,
        "The objection, handled badly",
        '"Ours is better quality." You have now made an unverifiable claim about a product you '
        "have not seen, against one they chose. Even if you are right, you have moved the "
        "conversation to a comparison you cannot win in the room, and you have implied their "
        "judgement was poor.",
    ),
    _s(
        18,
        SlideKind.EXAMPLE,
        "The objection, handled well",
        '"Is it originated or aggregated?" — "I think aggregated, why?" — "That is usually '
        "why a news section reads the same as a competitor's. Benzinga's newsroom writes its own, "
        "200-plus articles a day, and there is a separate one-sentence explainer for stocks that "
        'move. Would the explainer be more useful to your users than more articles?"',
        refs=(DOCS_NEWS, DOCS_WIIM),
    ),
    _s(
        19,
        SlideKind.EXAMPLE,
        "The second objection: our users do not read",
        "This one is often true, and arguing is a mistake. The right move is to leave the family "
        'entirely: "Then this may be the wrong half of the catalogue. Do your users know what '
        'is coming up for the things they hold?" You have just moved to calendars, which is '
        "section 5, and you did it without losing the meeting.",
        refs=(DOCS_EARNINGS,),
    ),
    _s(
        20,
        SlideKind.CONCEPT,
        "What to be careful about across this whole family",
        "Everything here is content somebody else wrote, so everything here has redistribution, "
        "attribution and entitlement questions attached — and those are per-contract and were "
        "not publicly readable. Say what the product is, never what the client may do with it. "
        "That is the single discipline that matters most in this family.",
    ),
    _s(
        21,
        SlideKind.CONCEPT,
        "What this family does not do",
        "It does not carry company fundamentals, full research reports, or price data. A "
        "sentiment tag on an article is not a sentiment dataset. If a client wants a signal "
        "rather than something to display, they want the alternative-data family and you should "
        "take them there rather than stretching this one.",
    ),
    _s(
        22,
        SlideKind.CHECKPOINT,
        "Name all eight, then name your two",
        "From memory: all eight products in this family. Then say which two you would lead with "
        "for a retail brokerage and why. If your two are not the newsfeed and Why Is It Moving, "
        "be able to justify it — that is a fine answer if you can.",
        checkpoint=(
            "Name all eight content products from memory, then the two you would lead with and why."
        ),
    ),
    _s(
        23,
        SlideKind.CHECKPOINT,
        "Rehearse both objections out loud",
        'Say your handling of "we already have a feed" and "our users do not read news", out '
        "loud, once each. You will hear both of these more than anything else in this course, and "
        "a rehearsed question sounds like curiosity where an unrehearsed one sounds like a "
        "script.",
        checkpoint="Say both objection handlings aloud, once each, before moving on.",
    ),
)

SECTION_4_TEST = SectionTest(
    pass_mark=0.8,
    questions=(
        TestQuestion(
            prompt="What is the correct first move when a prospect says they already have news?",
            options=(
                "Say Benzinga's quality is higher",
                "Ask whether their current feed is originated or aggregated, and let them\n answer",
                "Offer a discount",
                "Move straight to the calendar family",
            ),
            answer_index=1,
            explanation=(
                "Claiming higher quality is unverifiable, implies their judgement was poor, and "
                "moves the conversation to a comparison you cannot win in the room. The question "
                "does the work."
            ),
        ),
        TestQuestion(
            prompt="Which content product is explicitly aggregated rather than originated?",
            options=(
                "The Premium US Equities Newsfeed",
                "The press-release feed, normalising five wires into one endpoint",
                "Why Is It Moving",
                "Benzinga Video News",
            ),
            answer_index=1,
            explanation=(
                "Pretending otherwise undermines the originated-versus-aggregated point you just "
                "made about the newsfeed. It is also a machine-facing product, not a display one."
            ),
        ),
        TestQuestion(
            prompt="Why does Why Is It Moving convert in demos where the newsfeed alone does not?",
            options=(
                "It is cheaper",
                "A bare number leaves a user guessing; one sentence beside it produces an\n"
                " informed user, and nothing else on the screen has to change",
                "It covers more tickers",
                "It arrives by streaming",
            ),
            answer_index=1,
            explanation=(
                "An unusually clean value story: the platform's screen is unchanged, and the "
                "user's experience of it is completely different."
            ),
        ),
        TestQuestion(
            prompt="A client says their users do not read news. What is the best response?",
            options=(
                "Explain that engagement data shows otherwise",
                "Accept it and move to another family: ask whether their users know what is\n"
                " coming up for the things they hold",
                "Offer the video product instead",
                "Ask for their engagement metrics",
            ),
            answer_index=1,
            explanation=(
                "This objection is often simply true. Arguing loses the meeting; moving to "
                "calendars keeps it and lands on a product that fits."
            ),
        ),
        TestQuestion(
            prompt="What must you volunteer about Bulls Say, Bears Say in a regulated firm?",
            options=(
                "That it is refreshed weekly",
                "That the summaries are AI-assisted",
                "That coverage depends on analyst report availability",
                "That it pairs with the ratings calendar",
            ),
            answer_index=1,
            explanation=(
                "All four are true, but the AI provenance is the material one for compliance, and "
                "volunteering it is what makes that conversation short instead of long."
            ),
        ),
        TestQuestion(
            prompt=(
                "The prediction-markets feed carries only around ten articles a day. What is the"
                " argument for it?"
            ),
            options=(
                "That volume will grow",
                "Scarcity, not volume: it is among the first structured API feeds covering the\n"
                " sector, so a platform wanting coverage has few alternatives",
                "That it is bundled with the newsfeed",
                "That it needs no integration work",
            ),
            answer_index=1,
            explanation=(
                "Ten a day is thin next to two thousand press releases, and irrelevant if nobody "
                "else sells it at all. Sell the scarcity."
            ),
        ),
    ),
)


def section_4() -> CourseModule:
    """Section 4: the content layer, and the objection you will hear most."""
    return CourseModule(
        id=_id("module", "the-content-layer"),
        title="The content layer: what a user reads",
        order=3,
        lessons=(
            Lesson(
                id=_id("lesson", "the-content-layer"),
                title="Eight content products, and two objections",
                body=_S4_BODY,
                order=0,
                slides=_SECTION_4_SLIDES,
                drill_topics=("product:benzinga:content",),
                measurement=(
                    "You can name all eight content products, lead with the right two, and handle "
                    "both standard objections without making a claim you cannot support."
                ),
            ),
        ),
        section_test=SECTION_4_TEST,
    )


# --- Section 5 — The event layer: what a user plans around ----------------------------------

_S5_BODY = (
    "Eleven products, the largest family in the catalogue, and the one most advisors "
    "under-sell because calendars sound boring. They are not boring: they are the only family "
    "that tells a user what is going to happen. Everything else Benzinga licenses describes the "
    "past. By the end of this lesson you can name all eleven, explain why a forward calendar "
    "changes a platform's retention, and answer the objection this family actually attracts."
)

_SECTION_5_SLIDES: tuple[Slide, ...] = (
    _s(
        0,
        SlideKind.CONCEPT,
        "The calendars sell a tense",
        "This is the whole idea of the family. News says what happened. Signals say what is "
        "happening. Calendars say what is *about to*, with a date on it. A platform that can "
        "only show the past is a rear-view mirror, and a user with a dated horizon has a reason "
        "to come back before anything has even happened.",
        refs=(DOCS_EARNINGS,),
        asset=_diagram(
            "event_horizon",
            "The calendars are the only family in the catalogue with a future tense.",
            "A forward timeline running left to right from today. Four dated events sit above "
            "it: earnings tomorrow, an ex-dividend date in three days, a PDUFA decision in two "
            "weeks, a lockup expiry in ninety days. A line beneath reads: a platform with no "
            "forward calendar is a rear-view mirror.",
        ),
    ),
    _s(
        1,
        SlideKind.CONCEPT,
        "Why that matters commercially, not just conceptually",
        "Retention is the metric this family moves. A wealth platform whose users log in once a "
        "quarter has no recurring reason to be opened; the same platform showing each holding's "
        "next earnings date, next ex-dividend date and any pending corporate action has one "
        "several times a month. Nothing else in the catalogue does that.",
        refs=(DOCS_EARNINGS,),
    ),
    _s(
        2,
        SlideKind.CONCEPT,
        "Earnings, and the accuracy number",
        "Upcoming and historical earnings dates with actuals, estimates, surprise figures and "
        "EPS and revenue detail. History from 2012, roughly 100 to 500 records a day in season. "
        "Benzinga states 99.975% accuracy, audited in Q2 2022, achieved through a three-step "
        "reconciliation that includes calling sell-side analysts each quarter.",
        refs=(DOCS_EARNINGS,),
    ),
    _s(
        3,
        SlideKind.CONCEPT,
        "How to use an accuracy figure honestly",
        'Say it as it is: "Benzinga reports 99.975%, audited in Q2 2022." Naming the quarter is '
        "what makes it credible rather than a marketing number, and it also pre-empts the "
        "obvious follow-up. This is the strongest verifiable quality claim in the whole "
        "catalogue, so it is worth stating precisely.",
        refs=(DOCS_EARNINGS,),
    ),
    _s(
        4,
        SlideKind.CONCEPT,
        "Why earnings-date accuracy is a real problem",
        "Companies move their dates, announce late, and confirm through channels that are not "
        "machine-readable. A platform showing a wrong earnings date has told its user something "
        "false about their own holding, which is a support ticket and a trust problem. That is "
        "why a reconciliation process is a product feature rather than housekeeping.",
        refs=(DOCS_EARNINGS,),
    ),
    _s(
        5,
        SlideKind.CONCEPT,
        "Analyst ratings, and the importance score",
        "Every sell-side rating action: upgrades, downgrades, initiations, reiterations, price "
        "target changes. History from 2013, 100 to 500 actions a day, with streaming available. "
        "Overnight ratings publish about three hours before market open. It carries an "
        "importance score from 0 to 5, which is how a platform filters noise.",
        refs=(DOCS_RATINGS,),
    ),
    _s(
        6,
        SlideKind.CONCEPT,
        "Ratings are NOT normalised, and that is deliberate",
        "The feed reflects each firm's actual language — Buy, Overweight, Sector Perform — "
        "rather than mapping everything onto one scale. For a display product that is more "
        "honest. For a quant model it is work. Knowing which of those two your client is tells "
        "you whether this is a feature or a task.",
        refs=(DOCS_RATINGS,),
    ),
    _s(
        7,
        SlideKind.CONCEPT,
        "Guidance",
        "Corporate forward guidance: EPS ranges, revenue targets, operating margin estimates, "
        "captured as initial guidance and then as revisions and withdrawals. History from 2011, "
        "10 to 20 updates a day. The differentiator is that it holds ranges rather than point "
        "estimates, which is what guidance actually is.",
        refs=(CATALOGUE,),
    ),
    _s(
        8,
        SlideKind.CONCEPT,
        "The FDA calendar, and why it sells narrowly and well",
        "PDUFA decision dates, NDA and BLA filing schedules, advisory committee meetings, "
        "clinical trial readouts. History from 2018, 5 to 30 events a day. It covers the whole "
        "FDA pipeline lifecycle rather than just decision dates. For a biotech-focused desk it "
        "is close to essential; for a generalist platform it is a nice-to-have.",
        refs=(DOCS_FDA,),
    ),
    _s(
        9,
        SlideKind.CONCEPT,
        "The economics calendar is the global one",
        "Macro events across more than fifty countries with actual, forecast and prior values: "
        "GDP, CPI, non-farm payrolls, FOMC decisions, PMIs and hundreds more. History from 2014, "
        "20 to 100 events a day. It carries an impact level and a related-instruments field, and "
        "it is the one product here that is not US-equity shaped.",
        refs=(DOCS_ECONOMICS,),
    ),
    _s(
        10,
        SlideKind.CONCEPT,
        "Which makes it the answer to a specific objection",
        'When a non-US platform says "most of this is US equities", they are right, and the '
        "economics calendar is where you go. Fifty-plus countries of macro events with impact "
        "scoring is genuinely relevant to an FX desk or a European wealth platform in a way the "
        "newsfeed is not. Know this before you need it.",
        refs=(DOCS_ECONOMICS,),
    ),
    _s(
        11,
        SlideKind.CONCEPT,
        "Conference call transcripts, live",
        "Real-time audio and live transcription of earnings calls as they happen, plus the "
        "calendar of upcoming ones. Russell 3000 including LSE listings, 50 to 200 calls a day "
        "in season, history from 2023. Speaker-tagged with CEO and CFO attribution, and "
        "summaries generated progressively during the call rather than after it.",
        refs=(SITE_TRANSCRIPTS,),
    ),
    _s(
        12,
        SlideKind.CONCEPT,
        "Why live rather than post-call matters",
        "A transcript published an hour after the call is a record. A transcript streaming "
        "during the call is a tool. The catalogue calls this out as the differentiator, and it "
        "is also the product in this family most obviously aimed at LLM and NLP pipelines rather "
        "than at a screen — which makes it an institutional conversation.",
        refs=(SITE_TRANSCRIPTS,),
    ),
    _s(
        13,
        SlideKind.CONCEPT,
        "The corporate-action four",
        "Dividends (history from 2013, with a proprietary algorithm predicting future ex-dates, "
        "cross-checked by analysts), splits (from 2010, including reverse splits and OTC), IPOs "
        "(from 2012), and secondary offerings (from 2014). Unglamorous, universally needed, and "
        "the reason a portfolio view can be correct rather than approximately correct.",
        refs=(CATALOGUE,),
    ),
    _s(
        14,
        SlideKind.CONCEPT,
        "Two details in there that sell on their own",
        "The IPO calendar carries **lockup expiration and quiet-period expiration dates**, which "
        "is what makes lockup-expiry strategies possible at all. The splits calendar covers "
        "reverse splits, which the catalogue notes competitors often miss and which options desks "
        "need for adjustment workflows. Specifics like these close deals.",
        refs=(DOCS_IPO,),
    ),
    _s(
        15,
        SlideKind.CONCEPT,
        "Mergers and acquisitions, rumour to close",
        "Deal tracking across the full lifecycle: rumour, announced, pending, completed, with "
        "deal type, payment type, size and expected close date. History from August 2019, 5 to "
        "30 updates a day. Remember from section 3 that this is the CSV-only product, and raise "
        "that yourself rather than letting an engineer find it.",
        refs=(CATALOGUE,),
    ),
    _s(
        16,
        SlideKind.WALKTHROUGH,
        "Group the eleven by who cares",
        "In the catalogue, group the eleven calendars into three buckets: everybody (earnings, "
        "dividends, splits), specialist (FDA, economics, M&A, secondaries), and institutional "
        "(transcripts, guidance, ratings, IPO). Your grouping may differ from mine — the point is "
        "to have one, because eleven products is too many to pitch flat.",
        refs=(CATALOGUE,),
    ),
    _s(
        17,
        SlideKind.WALKTHROUGH,
        "Find the two with the deepest history",
        "Read the History column across the family and find the two oldest. Splits go back to "
        "2010 and earnings to 2012; transcripts only to 2023. Now say why that matters: a client "
        "backtesting an earnings-surprise strategy has a decade to work with, and one wanting to "
        "backtest call sentiment has three years.",
        refs=(CATALOGUE,),
    ),
    _s(
        18,
        SlideKind.WALKTHROUGH,
        "Write the retention sentence",
        "Write one sentence you would say to a wealth platform about why calendars change "
        'retention. Do not use the word retention. Something closer to: "Right now your users '
        "have no reason to open the app between statements. If they could see the next earnings "
        'and ex-dividend date for everything they hold, they would have several a month."',
        refs=(DOCS_EARNINGS,),
    ),
    _s(
        19,
        SlideKind.EXAMPLE,
        "The objection this family attracts",
        '"Can we trust the dates?" It is the right question and it deserves the specific '
        "answer, not reassurance: earnings is audited at 99.975% as of Q2 2022 with a three-step "
        "reconciliation including analyst calls, and ex-dividend dates are algorithmically "
        "predicted and then cross-checked by analysts. Detail is what answers this.",
        refs=(DOCS_EARNINGS,),
    ),
    _s(
        20,
        SlideKind.EXAMPLE,
        "A calendar deal that got bigger in the room",
        "A retail brokerage asks for the earnings calendar. You ask what they show a user who "
        "holds a biotech, and whether they flag pending corporate actions. Neither. Now the "
        "conversation covers FDA, dividends and splits, because you asked about the user rather "
        "than confirming the order.",
        refs=(DOCS_FDA,),
    ),
    _s(
        21,
        SlideKind.CONCEPT,
        "What this family does not do",
        "It carries dates and the figures attached to them, not analysis. There is no view on "
        "whether an earnings beat is good, no valuation, no recommendation. And the accuracy "
        "figure belongs to earnings specifically — do not quote 99.975% as though it covers all "
        "eleven products, because it does not.",
    ),
    _s(
        22,
        SlideKind.CHECKPOINT,
        "Name eleven, then name your three",
        "From memory: all eleven calendars. Then pick the three you would lead with for a "
        "mainstream retail brokerage and say why those three. If you cannot get to eleven, use "
        "your grouping from the walkthrough — buckets are easier to hold than a list.",
        checkpoint=(
            "Name all eleven calendars from memory, then the three you would lead with and why."
        ),
    ),
    _s(
        23,
        SlideKind.CHECKPOINT,
        "Say the accuracy answer precisely",
        'Say out loud, without notes, how you would answer "can we trust the dates?". It must '
        "include the figure, the quarter it was audited in, and the reconciliation process. "
        "Vague reassurance loses this one; precision wins it, and this is the one place in the "
        "course where a number is your friend.",
        checkpoint=(
            "Say the trust-the-dates answer aloud, including the figure, the quarter and the "
            "reconciliation."
        ),
    ),
)

SECTION_5_TEST = SectionTest(
    pass_mark=0.8,
    questions=(
        TestQuestion(
            prompt="What makes the calendar family structurally different from every other family?",
            options=(
                "It is the largest",
                "It is the only family with a future tense: it says what is about to happen,\n"
                " with a date on it",
                "It is the cheapest",
                "It is the only one delivered by REST",
            ),
            answer_index=1,
            explanation=(
                "Everything else describes the past or the present. A platform that can only show "
                "the past is a rear-view mirror, and a dated horizon is a reason to return."
            ),
        ),
        TestQuestion(
            prompt="How should you state the earnings-calendar accuracy figure?",
            options=(
                "As 99.975% accurate",
                "As Benzinga reporting 99.975%, audited in Q2 2022, via a three-step\n"
                " reconciliation that includes calling sell-side analysts",
                "As industry-leading accuracy",
                "Avoid quoting it at all",
            ),
            answer_index=1,
            explanation=(
                "Naming the quarter and the method is what makes it credible rather than a "
                "marketing number, and it pre-empts the obvious follow-up. It is the strongest "
                "verifiable quality claim in the catalogue."
            ),
        ),
        TestQuestion(
            prompt="A non-US platform says most of the catalogue is US equities. Where do you go?",
            options=(
                "The press-release feed, which has global wire coverage",
                "The economics calendar: macro events across 50-plus countries with impact\n"
                " scoring and a related-instruments field",
                "Corporate logos, which are international",
                "Concede the point and requalify",
            ),
            answer_index=1,
            explanation=(
                "They are right about the shape of the catalogue, and the economics calendar is "
                "the product genuinely relevant to an FX desk or a European wealth platform."
            ),
        ),
        TestQuestion(
            prompt="Analyst ratings are not normalised onto one scale. For whom is that a problem?",
            options=(
                "A display buyer, who needs consistency",
                "A quant buyer, who has mapping work to do — for a display buyer, reflecting\n"
                " each firm's actual language is more honest",
                "Nobody, it is purely a benefit",
                "Both equally",
            ),
            answer_index=1,
            explanation=(
                "Knowing which of the two your client is tells you whether this is a feature or a "
                "task, and it is the sort of detail that decides whether a pilot goes well."
            ),
        ),
        TestQuestion(
            prompt=(
                "Which detail in the IPO calendar enables a strategy that could not exist"
                " without it?"
            ),
            options=(
                "The pricing range",
                "Lockup expiration and quiet-period expiration dates",
                "The lead underwriter roster",
                "The deal status field",
            ),
            answer_index=1,
            explanation=(
                "Lockup-expiry trading needs the lockup date. Specifics like this close deals in a "
                "way a product summary never does."
            ),
        ),
        TestQuestion(
            prompt="What must you NOT do with the 99.975% figure?",
            options=(
                "Name the quarter it was audited in",
                "Quote it as though it covers all eleven calendar products",
                "Mention the reconciliation process",
                "Attribute it to Benzinga",
            ),
            answer_index=1,
            explanation=(
                "It belongs to the earnings calendar specifically. Stretching one product's "
                "audited figure across a family is the kind of overreach that costs you the "
                "compliance conversation."
            ),
        ),
    ),
)


def section_5() -> CourseModule:
    """Section 5: the event layer, the only family with a future tense."""
    return CourseModule(
        id=_id("module", "the-event-layer"),
        title="The event layer: what a user plans around",
        order=4,
        lessons=(
            Lesson(
                id=_id("lesson", "the-event-layer"),
                title="Eleven calendars, and the tense they sell",
                body=_S5_BODY,
                order=0,
                slides=_SECTION_5_SLIDES,
                drill_topics=("product:benzinga:calendars",),
                measurement=(
                    "You can name all eleven calendars, explain why a forward calendar changes "
                    "retention, and answer 'can we trust the dates?' with the precise figure."
                ),
            ),
        ),
        section_test=SECTION_5_TEST,
    )


# --- Section 6 — The signal layer: what a desk trades on ------------------------------------

_S6_BODY = (
    "Nine products, the highest price per product, the narrowest buyer, and the family where "
    "what you must NOT claim matters more than what you can. By the end of this lesson you can "
    "name all nine, explain the one asset in the whole catalogue that no competitor can copy, and "
    "state the alpha caveat in your own words. An advisor who oversells this family in a "
    "regulated firm does damage that survives the deal."
)

_SECTION_6_SLIDES: tuple[Slide, ...] = (
    _s(
        0,
        SlideKind.CONCEPT,
        "What this family is for",
        "Alternative data is what a desk trades on, or what a retail platform uses to make "
        "something feel like an edge. It is the least homogeneous family in the catalogue: nine "
        "products with almost nothing in common except that each one is a signal somebody wants "
        "to act on rather than something to read.",
        refs=(DOCS_OPTIONS,),
    ),
    _s(
        1,
        SlideKind.CONCEPT,
        "The three audience-derived products are the interesting ones",
        "Six of the nine are normalised public or exchange-adjacent data — options flow, block "
        "trades, insider filings, congressional filings, SEC filings, short interest. Anyone with "
        "engineering can build those. Three are derived from Benzinga's own traffic, and those "
        "cannot be built by anyone without an audience.",
        refs=(SITE_CLICKSTREAM,),
    ),
    _s(
        2,
        SlideKind.CONCEPT,
        "Attention arrives before volume",
        "Ticker Trends is retail attention derived from page views on Benzinga's own properties: "
        "scaled metrics from 0 to 100, four-week trailing averages, anomaly detection, history "
        "from 2021. The value is not the views. The value is that the views move *before* the "
        "volume does, and the gap is what a quant is paying for.",
        refs=(DOCS_TRENDS,),
        asset=_diagram(
            "attention_before_volume",
            "The lag between attention and volume is the product, and nobody without an "
            "audience can sell it.",
            "Two bar series mirrored about a shared time axis. Above the line, ticker views in "
            "dark green, rising to a peak early. Below the line, traded volume in grey, rising "
            "to its own peak later. Two vertical guides mark the two peaks and an arrow spans "
            "the gap between them, labelled: views peak here, trading peaks later. A line "
            "beneath reads: anyone can sell you the volume, almost nobody can sell you the gap.",
        ),
    ),
    _s(
        3,
        SlideKind.CONCEPT,
        "Why the shape of that data matters",
        "Ticker Trends is deliberately model-ready: scaled 0 to 100 with a four-week moving "
        "average already computed. A quant can drop it into a factor model without building a "
        "normalisation layer first. That is a product decision, and it is the difference between "
        "a dataset a fund evaluates and one it actually adopts.",
        refs=(DOCS_TRENDS,),
    ),
    _s(
        4,
        SlideKind.CONCEPT,
        "The raw clickstream, and who wants raw",
        "The clickstream product is the unscaled version: ticker, click count, ISIN, ten-minute "
        "time bucket, shipped as flat files by FTP or S3. Benzinga describes it as a first-party "
        "dataset from roughly 14 million monthly users. A fund that wants to build its own "
        "features takes this one; a platform that wants a trending widget takes Ticker Trends.",
        refs=(SITE_CLICKSTREAM,),
    ),
    _s(
        5,
        SlideKind.CONCEPT,
        "The partner-network dataset, and why it is different again",
        "The third audience product measures ticker interest across Benzinga's *partner* "
        "platforms — brokerages and banks — with an anonymised partner identifier attached. So "
        "it segments where interest originates, not only what is trending. That attribution is "
        "the thing you cannot get from any public source at all.",
        refs=(CATALOGUE,),
    ),
    _s(
        6,
        SlideKind.CONCEPT,
        "Unusual options activity",
        "Real-time alerts for options flow that is statistically unusual against open interest "
        "and historical norms. Tens of thousands of signals a day, history from 2019, and each "
        "signal carries a human-readable description field — which is what lets a retail platform "
        "display it rather than only feed it to a model.",
        refs=(DOCS_OPTIONS,),
    ),
    _s(
        7,
        SlideKind.CONCEPT,
        "The alpha caveat, and say it before they ask",
        'The catalogue says this activity "often precedes moves in the underlying stock". That '
        "is Benzinga's framing of its own product. It is **not validated alpha**, there is no "
        "published study attached, and in a regulated firm implying otherwise is the mistake that "
        "ends the relationship rather than the meeting.",
        refs=(DOCS_OPTIONS,),
    ),
    _s(
        8,
        SlideKind.CONCEPT,
        "How to sell a signal without claiming it works",
        'Sell the observation, not the outcome. "This surfaces options activity that is '
        "statistically unusual against open interest, in real time, with a description your users "
        'can read." Every word of that is verifiable. "This predicts moves" is not, and you do '
        "not need it — the buyer will do their own backtest anyway.",
        refs=(DOCS_OPTIONS,),
    ),
    _s(
        9,
        SlideKind.CONCEPT,
        "Block trades, and why they are a separate product",
        "Outsized single-print options block trades: symbol, strike, expiry, type, contract size "
        "and total premium. 100 to 300 records a day, history from 2021. The catalogue "
        "distinguishes it from unusual options activity — this one is about individual large "
        "prints, and it flags recurring activity in the same name, strike and expiry.",
        refs=(CATALOGUE,),
    ),
    _s(
        10,
        SlideKind.CONCEPT,
        "Insider trades: the deep-history one",
        "SEC Form 4 transactions by officers, directors and holders above 10%, normalised and "
        "delivered as filings hit EDGAR, with full derivative and non-derivative coverage. "
        "History back to **2003**, which the catalogue calls out as one of the deepest insider "
        "histories available — and depth is exactly what a backtest buyer is shopping for.",
        refs=(DOCS_INSIDER,),
    ),
    _s(
        11,
        SlideKind.CONCEPT,
        "Government trades, and the claim attached to it",
        "Congressional trading disclosed under the STOCK Act, both chambers, both parties, "
        "history from 2003. The catalogue notes politicians outperformed the S&P by more than "
        "17% in 2022 and calls this one of its most engaging consumer datasets. Attribute that "
        "figure to Benzinga; it is a retention argument, not a research finding.",
        refs=(DOCS_GOVERNMENT,),
    ),
    _s(
        12,
        SlideKind.CONCEPT,
        "Why that one sells to retail rather than to quants",
        "A congressional trade is interesting rather than statistically useful: the volume is "
        "low, the reporting lag is long, and the sample is small. But users find it compelling, "
        "which makes it an engagement product wearing an alternative-data label. Selling it as "
        "engagement is both more honest and more likely to land.",
        refs=(DOCS_GOVERNMENT,),
    ),
    _s(
        13,
        SlideKind.CONCEPT,
        "SEC filings and short interest",
        "SEC filings: every EDGAR filing type with real-time alerts and history from 2003, 100 to "
        "1,000 a day. Short interest: bi-monthly official FINRA releases with optional daily "
        "estimates, days-to-cover and the short interest ratio, history from 2010. Both are "
        "normalisations of public data, and both are bought to avoid building that normalisation.",
        refs=(DOCS_SHORT,),
    ),
    _s(
        14,
        SlideKind.CONCEPT,
        "The honest pitch for a public-data product",
        "Never pretend a public-data product is proprietary. The pitch is the work you are not "
        'doing: "FINRA publishes this; keeping it clean, backfilled to 2010 and available '
        'through one endpoint is a job somebody on your team currently owns." That is a real '
        "argument and it does not require a claim you cannot support.",
        refs=(DOCS_SHORT,),
    ),
    _s(
        15,
        SlideKind.CONCEPT,
        "The designed pairing in this family",
        "The catalogue points at it directly: unusual options activity pairs with insider trades "
        "to track smart money across two independent dimensions. Institutional positioning on one "
        "side, corporate insiders on the other. Two products, one story, and a materially larger "
        "deal than either alone.",
        refs=(DOCS_OPTIONS, DOCS_INSIDER),
    ),
    _s(
        16,
        SlideKind.WALKTHROUGH,
        "Split the nine into copyable and not",
        "In the catalogue, sort the nine into two lists: products built from public or "
        "exchange-adjacent sources, and products derived from Benzinga's own audience. You should "
        "get six and three. That split is the most useful thing in this section, because it tells "
        "you where the price and the defensibility actually are.",
        refs=(CATALOGUE,),
    ),
    _s(
        17,
        SlideKind.WALKTHROUGH,
        "Compare the three audience products field by field",
        "Read the Key Data Fields column for Ticker Trends, the clickstream and the "
        "partner-network dataset. Note that only one is scaled and smoothed, only one carries "
        "partner attribution, and two ship as flat files. Then write one line each on who buys "
        'which — that is the answer you will need when a client says "retail sentiment".',
        refs=(DOCS_TRENDS, SITE_CLICKSTREAM),
    ),
    _s(
        18,
        SlideKind.WALKTHROUGH,
        "Write the caveat in your own words",
        "Write one sentence you would actually say about options-flow predictiveness. It has to "
        "be something you would be comfortable seeing quoted back to you by a compliance officer "
        'six months later. If your sentence contains the word "predicts", rewrite it.',
        refs=(DOCS_OPTIONS,),
    ),
    _s(
        19,
        SlideKind.EXAMPLE,
        "The pitch that ends a relationship",
        '"Our options flow data front-runs institutional moves — the funds using it are seeing '
        'trades before the market does." Every clause there is a claim about outcomes, none is '
        "supported by anything in the catalogue, and in a regulated firm it invites a question "
        "about inducement that you cannot answer.",
    ),
    _s(
        20,
        SlideKind.EXAMPLE,
        "The pitch that survives diligence",
        '"It surfaces options activity that is statistically unusual against open interest, in '
        "real time, with a plain-English description per signal. Benzinga's own framing is that "
        "this often precedes moves; that is their framing rather than a published study, and your "
        'quant team will want to test it themselves." That sentence has never lost a deal.',
        refs=(DOCS_OPTIONS,),
    ),
    _s(
        21,
        SlideKind.EXAMPLE,
        "The attention pitch, which needs no caveat at all",
        '"Benzinga has around 14 million monthly readers, and it sells what those readers were '
        "looking at, in ten-minute buckets, before the volume showed up. No vendor without an "
        'audience can sell you that at any price." Every word is a fact about provenance rather '
        "than a claim about returns, which is why this is the strongest pitch in the family.",
        refs=(SITE_CLICKSTREAM,),
    ),
    _s(
        22,
        SlideKind.CHECKPOINT,
        "Name the nine, and the three that matter",
        "From memory: all nine, then the three audience-derived ones. Then say, in one sentence, "
        "why those three are the only genuinely uncopyable assets in the entire 32-product "
        "catalogue. If you can only do the last part, you can still sell this family.",
        checkpoint=(
            "Name all nine signal products and the three audience-derived ones, then say why "
            "those three cannot be copied."
        ),
    ),
    _s(
        23,
        SlideKind.CHECKPOINT,
        "Say your caveat out loud",
        "Say your options-flow sentence aloud, once. Then say it as though a compliance officer "
        "is in the room, because eventually one will be. If the two versions differ, the second "
        "one is the one to learn — an advisor who only has the confident version has no version "
        "at all in the meeting that matters.",
        checkpoint="Say your alpha caveat aloud in the version a compliance officer would accept.",
    ),
)

SECTION_6_TEST = SectionTest(
    pass_mark=0.8,
    questions=(
        TestQuestion(
            prompt="Which products in this family cannot be replicated by a competitor?",
            options=(
                "The options-flow products, because of the description field",
                "The three derived from Benzinga's own audience: Ticker Trends, the raw\n"
                " clickstream, and the partner-network engagement dataset",
                "Insider and congressional trades, because of the 2003 history",
                "Short interest, because of the FINRA relationship",
            ),
            answer_index=1,
            explanation=(
                "Six of the nine normalise public or exchange-adjacent data, which anyone with "
                "engineering can do. Three need an owned audience, which cannot be bought."
            ),
        ),
        TestQuestion(
            prompt="How should you describe unusual options activity to a regulated buyer?",
            options=(
                "As data that front-runs institutional moves",
                "As activity statistically unusual against open interest, in real time, with\n"
                " Benzinga's 'often precedes moves' noted as their framing rather than a study",
                "As validated alpha with a published backtest",
                "Avoid the product entirely",
            ),
            answer_index=1,
            explanation=(
                "Sell the observation, not the outcome. Every word of the observation is "
                "verifiable, and the buyer will run their own backtest regardless."
            ),
        ),
        TestQuestion(
            prompt="What is actually being sold in the Ticker Trends product?",
            options=(
                "The page-view counts themselves",
                "The lag: views move before volume does, and the gap is what a quant pays for",
                "Coverage of every US-listed ticker",
                "A sentiment score per ticker",
            ),
            answer_index=1,
            explanation=(
                "Anyone can sell the volume. The offset between attention and volume is the "
                "product, which is why the diagram has to show the offset rather than assert it."
            ),
        ),
        TestQuestion(
            prompt="A client asks for 'retail sentiment'. Which of the three do you propose?",
            options=(
                "Always Ticker Trends",
                "It depends: Ticker Trends is scaled and model-ready, the clickstream is raw\n"
                " ten-minute buckets, and the partner dataset adds anonymised attribution",
                "Always the raw clickstream, since it has the most detail",
                "The newsfeed's sentiment tagging",
            ),
            answer_index=1,
            explanation=(
                "They are not interchangeable. A fund building its own features wants raw; a "
                "platform wanting a trending widget wants scaled. Ask before proposing."
            ),
        ),
        TestQuestion(
            prompt="How should the congressional-trading product be positioned, and why?",
            options=(
                "As a quant signal, given the 2003 history",
                "As an engagement product: low volume, long reporting lag and a small sample\n"
                " make it compelling to users rather than statistically useful",
                "As a compliance dataset",
                "As a substitute for insider trades",
            ),
            answer_index=1,
            explanation=(
                "Benzinga's own 17%-outperformance figure is a retention argument, not a research "
                "finding. Selling it as engagement is both more honest and more likely to land."
            ),
        ),
        TestQuestion(
            prompt="What is the honest pitch for short interest, which is public FINRA data?",
            options=(
                "That Benzinga's version is proprietary",
                "The work the client is not doing: kept clean, backfilled to 2010, and\n"
                " available through one endpoint instead of a job somebody owns",
                "That it includes daily estimates nobody else has",
                "That it predicts short squeezes",
            ),
            answer_index=1,
            explanation=(
                "Never pretend public data is proprietary. The maintenance burden you remove is a "
                "real argument and needs no claim you cannot support."
            ),
        ),
    ),
)


def section_6() -> CourseModule:
    """Section 6: the signal layer, and the discipline of not overclaiming."""
    return CourseModule(
        id=_id("module", "the-signal-layer"),
        title="The signal layer: what a desk trades on",
        order=5,
        lessons=(
            Lesson(
                id=_id("lesson", "the-signal-layer"),
                title="Nine signal products, and what not to claim",
                body=_S6_BODY,
                order=0,
                slides=_SECTION_6_SLIDES,
                drill_topics=("product:benzinga:signals",),
                measurement=(
                    "You can name all nine, identify the three uncopyable audience-derived ones, "
                    "and state the alpha caveat in a form a compliance officer would accept."
                ),
            ),
        ),
        section_test=SECTION_6_TEST,
    )


# --- Section 7 — Who buys which family, and what triggers it --------------------------------

_S7_BODY = (
    "You now know the four families and what is in them. This lesson is about the other half of "
    "the qualifying question: which kind of firm buys which family, and what has to have happened "
    "inside that firm before they will buy anything at all. A product that fits and a firm with no "
    "trigger is a pipeline entry that never closes, and recognising that early is worth more than "
    "another meeting."
)

_SECTION_7_SLIDES: tuple[Slide, ...] = (
    _s(
        0,
        SlideKind.CONCEPT,
        "Fit and trigger are two different questions",
        "Fit asks whether the product solves a problem they have. Trigger asks whether anything "
        "has happened that makes them act this quarter. Most stalled deals in a pipeline have "
        "good fit and no trigger, and an advisor who cannot tell the two apart spends months on "
        "accounts that were never going to move.",
    ),
    _s(
        1,
        SlideKind.CONCEPT,
        "Four segments worth naming",
        "Retail brokerage, wealth platform, quant fund, and media or fintech publisher. Those "
        "four cover most of what you will meet. Banks exist too and behave like a slower wealth "
        "platform with a longer compliance path. Naming the segment first is what stops you "
        "pitching alternative data to a media buyer.",
        refs=(CATALOGUE,),
    ),
    _s(
        2,
        SlideKind.CONCEPT,
        "The grid, and what its pattern tells you",
        "Content sells to almost everyone. Calendars sell to almost everyone. Alternative data "
        "sells narrowly and at the highest price. Market data sells to whoever is still building. "
        "Only a retail brokerage plausibly buys all four, which is why a retail brokerage is the "
        "largest deal shape in this catalogue.",
        refs=(CATALOGUE,),
        asset=_diagram(
            "who_buys_what",
            "Fit by segment and family. Filled means a real fit, not a maybe.",
            "A grid with four families down the side, content, calendar, alt data and market "
            "data, and four segments across the top, retail brokerage, wealth platform, quant "
            "fund and media. Filled dark green cells mark a real fit. Retail brokerage is filled "
            "on all four rows; wealth platform on content, calendar and market data; quant fund "
            "only on alternative data; media on content and calendar. A line beneath reads: only "
            "a retail brokerage plausibly buys all four, everyone else is narrower.",
        ),
    ),
    _s(
        3,
        SlideKind.CONCEPT,
        "Retail brokerage: the widest buyer",
        "They have users who ask why things moved, holdings with dated events, an appetite for "
        "anything that looks like an edge, and screens that need logos and quotes. All four "
        "families have a home. The constraint is rarely fit and almost always attention: they are "
        "building six things and you are competing with the other five.",
        refs=(DOCS_WIIM, DOCS_EARNINGS),
    ),
    _s(
        4,
        SlideKind.CONCEPT,
        "What triggers a retail brokerage",
        "A redesign of the stock detail page. A retention or engagement target somebody now owns. "
        "A competitor shipping something visible. An expansion into options, crypto or "
        "international. Or a support burden — users repeatedly asking a question the platform "
        "cannot answer. That last one is the cleanest trigger in this whole section.",
        refs=(DOCS_WIIM,),
    ),
    _s(
        5,
        SlideKind.CONCEPT,
        "Wealth platform: narrower, and calendar-led",
        "Long horizons, infrequent logins, holdings rather than trades. Content is useful and "
        "calendars are the argument: dated events per holding are the only thing here that "
        "reliably brings a user back. Alternative data is usually a poor fit — their users are "
        "not looking for signals and their compliance team will say so.",
        refs=(DOCS_EARNINGS,),
    ),
    _s(
        6,
        SlideKind.CONCEPT,
        "What triggers a wealth platform",
        "A new client-portal build. A pressure to look less like a statement and more like a "
        "product. An adviser-facing tool where the adviser needs to know what is coming up "
        "across a book. Regulatory or reporting change that forces a portal update — when the "
        "portal is being touched anyway, adding to it is cheap.",
    ),
    _s(
        7,
        SlideKind.CONCEPT,
        "Quant fund: one family, highest price",
        "They want alternative data and essentially nothing else. History depth and field shape "
        "decide everything: 2003 for insider and congressional trades, 2000 for bars, scaled "
        "model-ready metrics for attention. They will not buy a display product and they will "
        "backtest before they buy anything at all.",
        refs=(DOCS_INSIDER, DOCS_TRENDS),
    ),
    _s(
        8,
        SlideKind.CONCEPT,
        "What triggers a quant fund, and what a trial means",
        "A new strategy, a new analyst with a thesis, or a data budget cycle. The trigger is "
        "usually a person rather than an event. Expect a trial, expect it to be evaluated against "
        "their own returns, and expect the audience-derived products to survive that better than "
        "the public-data ones, because those they can already build.",
        refs=(SITE_CLICKSTREAM,),
    ),
    _s(
        9,
        SlideKind.CONCEPT,
        "Media and fintech publisher: content and calendars",
        "They need volume and breadth rather than depth: articles, press releases, video, and a "
        "calendar to build pages around. They will not buy alternative data because they have no "
        "desk. They are often the fastest deal in the catalogue because there is no compliance "
        "path and no user entitlement question.",
        refs=(DOCS_NEWS, DOCS_PRESS),
    ),
    _s(
        10,
        SlideKind.CONCEPT,
        "What triggers a publisher",
        "A traffic target, an SEO strategy that needs page volume, or a launch into a new "
        "coverage area. This is also the segment where the two newest feeds — prediction markets "
        "and private markets — land best, because a publisher wants coverage of an emerging "
        "sector before it is crowded.",
        refs=(CATALOGUE,),
    ),
    _s(
        11,
        SlideKind.CONCEPT,
        "The segment that looks like a fit and is not",
        "A pure execution broker with no research surface has nowhere to put any of this. So does "
        "a robo-adviser whose entire proposition is that the user does not look. Both will take "
        "the meeting and neither will buy. Recognising them saves more time than any other "
        "judgement in this section.",
    ),
    _s(
        12,
        SlideKind.CONCEPT,
        "Segment also decides the compliance path",
        "A publisher has none. A retail brokerage has a real one. A bank has a long one. That "
        "changes the deal length far more than the product does, and it is why the same product "
        "can be a six-week close in one segment and a two-quarter close in another. Price the "
        "time, not just the licence.",
    ),
    _s(
        13,
        SlideKind.WALKTHROUGH,
        "Fill in the grid yourself, then compare",
        "Before looking at the diagram again, draw the four-by-four grid and mark where you think "
        "the real fits are. Then compare. Where you disagree with it, work out which of you is "
        "right — the grid is a judgement rather than data, and disagreeing with it thoughtfully "
        "is better than memorising it.",
        refs=(CATALOGUE,),
    ),
    _s(
        14,
        SlideKind.WALKTHROUGH,
        "Write one trigger question per segment",
        "Four questions, one per segment, each designed to surface whether a trigger exists. For "
        'a brokerage: "what are your users asking support that you cannot answer?" For a wealth '
        'platform: "what brings someone back between statements?" Write your own for the other '
        "two.",
    ),
    _s(
        15,
        SlideKind.WALKTHROUGH,
        "Go through your own pipeline",
        "Take the prospects you currently have and label each with a segment and a trigger. Any "
        "entry where you cannot name the trigger is the entry to either qualify properly or stop "
        "working. That is the actual output of this section, and it usually shortens a pipeline "
        "before it lengthens it.",
    ),
    _s(
        16,
        SlideKind.WALKTHROUGH,
        "Match one real prospect to one family",
        "Pick one live prospect, name their segment, name the single family you would lead with, "
        "and name the one product inside it. One family and one product — not a catalogue tour. "
        "If you cannot narrow to one product, you have not qualified them yet.",
        refs=(CATALOGUE,),
    ),
    _s(
        17,
        SlideKind.EXAMPLE,
        "Good fit, no trigger",
        "A mid-size brokerage loves Why Is It Moving in the demo. Nobody there owns an engagement "
        "target, the stock page is not being touched this year, and no competitor has shipped "
        "anything. It will not close, and it is not your pitch that is wrong. Log it, set a "
        "reminder, and spend the quarter elsewhere.",
    ),
    _s(
        18,
        SlideKind.EXAMPLE,
        "Weak fit, strong trigger",
        "A wealth platform is rebuilding its client portal this quarter and has budget. "
        "Alternative data is a poor fit for their users, but calendars are not, and the portal is "
        "already open on somebody's desk. This closes faster than the better-fit account above, "
        "because the trigger is what moves a deal.",
        refs=(DOCS_EARNINGS,),
    ),
    _s(
        19,
        SlideKind.EXAMPLE,
        "The support-burden trigger, in full",
        '"How often does support get asked why a stock dropped?" — "Constantly, on any big down '
        'day." — "What do they answer?" — "They cannot, really." That is fit and trigger '
        "identified in three questions, and you have not described a product yet. This is the best "
        "opening in the course.",
        refs=(DOCS_WIIM,),
    ),
    _s(
        20,
        SlideKind.CONCEPT,
        "One question that works on every segment",
        '"What do your users ask you that you currently cannot answer?" It finds the family, it '
        "finds the trigger, and it makes the prospect describe their own problem in their own "
        "words. Nothing you can say about the catalogue is worth more than their answer to that.",
    ),
    _s(
        21,
        SlideKind.CONCEPT,
        "Segment tells you the objection you will get",
        'A brokerage says "we already have a feed". A wealth platform says "our users do not '
        'read news". A quant fund says "prove it works". A publisher says "what does it cost '
        'per article?". Knowing the segment means you have prepared the right answer instead of '
        "the wrong three.",
    ),
    _s(
        22,
        SlideKind.CHECKPOINT,
        "Reconstruct the grid from memory",
        "Draw the four-by-four grid and fill it in without looking. Then, for each of the four "
        "segments, name the family you would lead with and the objection you expect. Eight "
        "answers. This is the section's whole content, and it should fit on one side of paper.",
        checkpoint=(
            "Reconstruct the fit grid from memory, then name the lead family and expected "
            "objection for all four segments."
        ),
    ),
    _s(
        23,
        SlideKind.CHECKPOINT,
        "Label your pipeline honestly",
        "Go back to the pipeline labelling you did earlier and be honest about how many entries "
        "have no trigger. Then decide what you are going to do about those specifically. An "
        "advisor who does this once a quarter has a shorter pipeline and a better close rate than "
        "one who does not.",
        checkpoint=(
            "Count the pipeline entries with no identifiable trigger, and decide what happens to "
            "each."
        ),
    ),
)

SECTION_7_TEST = SectionTest(
    pass_mark=0.8,
    questions=(
        TestQuestion(
            prompt="What is the difference between fit and trigger?",
            options=(
                "They are the same thing described two ways",
                "Fit asks whether the product solves a problem they have; trigger asks whether\n"
                " anything has happened that makes them act this quarter",
                "Fit is about the product, trigger is about the price",
                "Fit applies to segments, trigger applies to individuals",
            ),
            answer_index=1,
            explanation=(
                "Most stalled pipeline entries have good fit and no trigger. Telling them apart is "
                "what stops months going into accounts that were never going to move."
            ),
        ),
        TestQuestion(
            prompt="Which segment plausibly buys all four families, and why does that matter?",
            options=(
                "A quant fund, because it has the largest budget",
                "A retail brokerage: users asking why things moved, holdings with dated events,\n"
                " appetite for an edge, and screens needing logos and quotes",
                "A media publisher, because it needs volume",
                "A bank, because it has the most users",
            ),
            answer_index=1,
            explanation=(
                "It is the largest deal shape in the catalogue. The constraint there is rarely fit "
                "and almost always attention — you are competing with their other five projects."
            ),
        ),
        TestQuestion(
            prompt="Why is alternative data usually a poor fit for a wealth platform?",
            options=(
                "The price is too high",
                "Their users are not looking for signals, and their compliance team will say so",
                "The delivery method is incompatible",
                "It does not cover their holdings",
            ),
            answer_index=1,
            explanation=(
                "Long horizons and infrequent logins make calendars the argument for this segment. "
                "Pushing signals here wastes the meeting and the compliance goodwill."
            ),
        ),
        TestQuestion(
            prompt=(
                "Which closes faster: good fit with no trigger, or weak fit with a strong trigger?"
            ),
            options=(
                "Good fit, no trigger",
                "Weak fit with a strong trigger, because the trigger is what moves a deal",
                "They close at the same rate",
                "Neither closes",
            ),
            answer_index=1,
            explanation=(
                "A wealth platform already rebuilding its portal with budget in hand closes faster "
                "than a brokerage that loved the demo and has no reason to act this year."
            ),
        ),
        TestQuestion(
            prompt="Which two segments will take the meeting and never buy?",
            options=(
                "Quant funds and banks",
                "A pure execution broker with no research surface, and a robo-adviser whose\n"
                " proposition is that the user does not look",
                "Media publishers and fintech startups",
                "Wealth platforms and retail brokerages",
            ),
            answer_index=1,
            explanation=(
                "Neither has anywhere to put the data. Recognising them saves more time than any "
                "other judgement in this section."
            ),
        ),
        TestQuestion(
            prompt="Which single question works across every segment?",
            options=(
                "What is your data budget this year?",
                "What do your users ask you that you currently cannot answer?",
                "Who else have you evaluated?",
                "Can you consume a push stream?",
            ),
            answer_index=1,
            explanation=(
                "It finds the family and the trigger at once, and it makes the prospect describe "
                "their own problem in their own words."
            ),
        ),
    ),
)


def section_7() -> CourseModule:
    """Section 7: who buys which family, and what has to have happened first."""
    return CourseModule(
        id=_id("module", "who-buys-which-family"),
        title="Who buys which family, and what triggers it",
        order=6,
        lessons=(
            Lesson(
                id=_id("lesson", "who-buys-which-family"),
                title="Four segments, four families, and the trigger",
                body=_S7_BODY,
                order=0,
                slides=_SECTION_7_SLIDES,
                drill_topics=("product:benzinga:segments",),
                measurement=(
                    "You can reconstruct the fit grid from memory, and every live prospect in your "
                    "pipeline has a named segment and a named trigger or a decision about it."
                ),
            ),
        ),
        section_test=SECTION_7_TEST,
    )


# --- Section 8 — How to sell it -------------------------------------------------------------

_S8_BODY = (
    "The last section, and the one that assembles everything before it into something you say out "
    "loud. By the end of it you will have a first meeting you can run without notes, an answer to "
    "each of the four objections, and a clear line you never cross on pricing. The founder's "
    "standard for the OpenBB course was that an advisor should know exactly how and when to sell "
    "it. This is the Benzinga version of that, and it is the section the rest exists to support."
)

_SECTION_8_SLIDES: tuple[Slide, ...] = (
    _s(
        0,
        SlideKind.CONCEPT,
        "The first meeting has four moves",
        "One: what do their users already ask that they cannot answer? Two: which family answers "
        "it? Three: what can they actually consume? Four: a scoped quote, in writing, from "
        "Bruntsfield. In that order. The order is the teaching, because three of the four are "
        "commonly skipped and each skip costs something specific.",
        asset=_diagram(
            "the_first_meeting",
            "The first meeting in four moves, with the step advisors skip marked.",
            "Four numbered boxes connected left to right. One, what do their users already ask? "
            "Two, which family answers it? Three, highlighted in dark green, what can they "
            "actually consume? Four, scoped quote in writing. A warning beneath reads: never "
            "quote a price, Benzinga pricing is per-contract always. A second line reads: skip "
            "step three and you promise a timeline engineering cannot keep.",
        ),
    ),
    _s(
        1,
        SlideKind.CONCEPT,
        "Move one, and why it comes first",
        "Their problem in their words, before any product is named. Ask what users ask support "
        "that support cannot answer. Ask what brings someone back between statements. You are "
        "listening for a family, and you are also finding out whether a trigger exists, which is "
        "the thing that decides whether this deal happens at all.",
        refs=(DOCS_WIIM,),
    ),
    _s(
        2,
        SlideKind.CONCEPT,
        "Move two: name a family, then one product",
        "Not the catalogue. One family, then the single product inside it that answers what they "
        "just told you. Thirty-two products is a menu; one product is a proposal. If you cannot "
        "narrow to one, you have not understood their answer to move one and should go back "
        "rather than forward.",
    ),
    _s(
        3,
        SlideKind.CONCEPT,
        "Move three: the step advisors skip",
        "Ask what they can consume: a scheduled pull, an always-on stream, or a file. This is the "
        "step that gets skipped because it feels technical and premature, and skipping it is how "
        "an advisor promises six weeks on a product that ships as an S3 flat file to a team with "
        "no file pipeline. Ask it in the first meeting, every time.",
        refs=(DOCS_INTRO,),
    ),
    _s(
        4,
        SlideKind.CONCEPT,
        "Move four: never quote a price",
        "Benzinga pricing is **per-contract**. There is no public rate card, no per-product list "
        "price, and no number you are authorised to say. What you offer is a scoped quote in "
        'writing from Bruntsfield, and "I will get you a scoped quote" is a better answer than '
        "any figure, because it is one you can actually deliver.",
    ),
    _s(
        5,
        SlideKind.CONCEPT,
        "What to do when they push for a number anyway",
        'They will. "Ballpark?" is the standard move and it is reasonable. The answer is a shape '
        "rather than a figure: it depends on which products, the delivery method, the coverage and "
        "the user count, and those are exactly the four things we will pin down to get you a real "
        "number this week. That answers the question without inventing one.",
    ),
    _s(
        6,
        SlideKind.CONCEPT,
        "The four objections, one per family",
        'Content: "we already have a feed." Calendar: "can we trust the dates?" Alternative '
        'data: "can you prove it works?" Market data: "why not use the free source?" You have '
        "answered the first three already in their own sections. The fourth is the one left, and "
        "it is the easiest.",
    ),
    _s(
        7,
        SlideKind.CONCEPT,
        "The market-data objection, answered",
        '"Why not use a free source?" Because free sources have no SLA, no support, no backfill '
        "guarantee, and no coverage commitment, and because somebody on their team currently owns "
        "keeping them working. The pitch is the maintenance you remove, and for logos it is also "
        "the asset hosting you remove.",
        refs=(DOCS_LOGOS,),
    ),
    _s(
        8,
        SlideKind.CONCEPT,
        "The compliance conversation, started by you",
        "Raise redistribution, attribution and entitlement before they do. Those terms are "
        "per-contract and were not publicly readable, so the honest position is that you will get "
        "them in writing for this deal. Volunteering the question is what makes you the advisor "
        "their compliance officer is willing to deal with.",
    ),
    _s(
        9,
        SlideKind.CONCEPT,
        "Attribute every claim that is Benzinga's",
        "Three claims will come up and all three are theirs, not yours: the audience figure, the "
        'options-flow framing, and the congressional outperformance number. "Benzinga reports" '
        "costs you one word and buys you the benefit of the doubt on everything else you say in "
        "the room.",
        refs=(DOCS_OPTIONS, DOCS_GOVERNMENT),
    ),
    _s(
        10,
        SlideKind.CONCEPT,
        "The one number you should quote precisely",
        "The earnings-calendar accuracy figure, because it is audited and the quarter is known: "
        "99.975%, audited Q2 2022, via a three-step reconciliation including analyst calls. It is "
        "the strongest verifiable quality claim in the catalogue. Quote it exactly, and do not "
        "stretch it across the other ten calendars.",
        refs=(DOCS_EARNINGS,),
    ),
    _s(
        11,
        SlideKind.CONCEPT,
        "What a good pilot looks like",
        "One product, one surface, one metric they already care about, and a date. Not three "
        "products across two teams. A brokerage putting Why Is It Moving on its stock detail page "
        "and watching support volume on down days is a pilot that either works or does not; "
        "anything broader produces an inconclusive result and a stalled renewal.",
        refs=(DOCS_WIIM,),
    ),
    _s(
        12,
        SlideKind.CONCEPT,
        "The expansion path, planned from the start",
        "Land on one family and expand through the designed pairings: Why Is It Moving pulls in "
        "market movers so a mover has an explanation beside it; earnings pulls in dividends and "
        "splits; unusual options pulls in insider trades. Knowing the pairing at the start means "
        "the second conversation is already scoped.",
        refs=(DOCS_WIIM, DOCS_INSIDER),
    ),
    _s(
        13,
        SlideKind.CONCEPT,
        "Where Bruntsfield's own service sits alongside",
        "Benzinga is a product sale, not an assessment. But a platform choosing a data layer is "
        "usually mid-way through a broader build, and that is a conversation about their operating "
        "model — which is what the rest of the studio is for. Notice the opening; do not force it "
        "in the same meeting.",
    ),
    _s(
        14,
        SlideKind.WALKTHROUGH,
        "Write the whole first meeting out",
        "Take the opening you have been building since section 1 and write the full four moves "
        "underneath it: your question, the family you expect, your delivery question, and your "
        "closing sentence about a scoped quote. One page. This is the deliverable of the entire "
        "course.",
    ),
    _s(
        15,
        SlideKind.WALKTHROUGH,
        "Rehearse it against the hardest segment",
        "Run your one page against a quant fund, which is the segment least served by most of "
        "what you have learned. Only one family applies, they will want a backtest, and they can "
        "already build six of the nine products themselves. If your page survives that, it will "
        "survive a brokerage.",
        refs=(SITE_CLICKSTREAM,),
    ),
    _s(
        16,
        SlideKind.WALKTHROUGH,
        "Write your four objection answers on one card",
        "One line each, four lines total, in the words you would actually use. Keep the card. The "
        "point is not that you will read it in a meeting — it is that writing them down is what "
        "turns four things you have read into four things you can say.",
    ),
    _s(
        17,
        SlideKind.WALKTHROUGH,
        "Check your live commission rate",
        "Open the Earnings page and read your current Benzinga rate before you next talk about "
        "money. It resolves live from the schedule and is deliberately not written into this "
        "course, because a rate typed into content is a rate that goes stale silently. Look it up "
        "each time.",
    ),
    _s(
        18,
        SlideKind.EXAMPLE,
        "A first meeting, run properly, in six lines",
        '"What do your users ask support that support cannot answer?" — "Why a stock dropped." '
        '— "How often?" — "Every big down day." — "Benzinga writes a one-sentence explanation '
        "for around 200 moving stocks a day, human-written, with an SLA on NYSE and Nasdaq names. "
        'Would your team rather pull that on a schedule or have it pushed?"',
        refs=(DOCS_WIIM,),
    ),
    _s(
        19,
        SlideKind.EXAMPLE,
        "The same meeting, closed",
        '"That is useful. What does it cost?" — "It depends on the products, the delivery '
        "method, your coverage and your user count. Give me those four and I will have a scoped "
        'quote to you this week." No number invented, no timeline promised, and a next step that '
        "exists.",
    ),
    _s(
        20,
        SlideKind.EXAMPLE,
        "The meeting that goes wrong in one sentence",
        '"It is usually somewhere around thirty thousand a year and we could have you live in six '
        'weeks." Two invented numbers in one breath. If either is wrong — and both are, because '
        "you had not asked about delivery — you have created an expectation that the contract and "
        "the engineering team will both contradict.",
    ),
    _s(
        21,
        SlideKind.CONCEPT,
        "The four lines you never cross",
        "Never quote a price. Never promise a timeline. Never state what a client may "
        "redistribute. "
        "Never present a Benzinga claim as an independent fact. Every one of those four is "
        'avoidable by saying "I will get you that in writing", which is also the most credible '
        "sentence available to you.",
    ),
    _s(
        22,
        SlideKind.CHECKPOINT,
        "Run the whole first meeting out loud",
        "From memory, no page: the four moves, in order, as you would actually say them. Then have "
        "someone push you for a price and answer without giving one. If you can do both, you are "
        "finished with this course in the way the founder meant.",
        checkpoint=(
            "Run all four moves aloud from memory, then answer a price push without quoting a "
            "figure."
        ),
    ),
    _s(
        23,
        SlideKind.CHECKPOINT,
        "Say the four lines you never cross",
        "Out loud, from memory: the four things you never do. Price, timeline, redistribution, "
        "attribution. These are the four that cause damage lasting past the deal, and an advisor "
        "who can recite them is the advisor who is safe to put in front of a regulated client "
        "unaccompanied.",
        checkpoint="Recite the four lines you never cross, from memory, out loud.",
    ),
)

SECTION_8_TEST = SectionTest(
    pass_mark=0.8,
    questions=(
        TestQuestion(
            prompt="What are the four moves of a first meeting, in order?",
            options=(
                "Introduce the catalogue, demo, price, close",
                "What do their users already ask; which family answers it; what can they\n"
                " actually consume; a scoped quote in writing",
                "Qualify budget, name products, negotiate, contract",
                "Demo, trial, pilot, renewal",
            ),
            answer_index=1,
            explanation=(
                "The order is the teaching. Naming a family before you know what they can consume "
                "produces a promise engineering cannot keep."
            ),
        ),
        TestQuestion(
            prompt="A prospect asks for a ballpark price. What do you say?",
            options=(
                "A rough annual figure, flagged as approximate",
                "A shape not a figure: it depends on products, delivery method, coverage and\n"
                " user count, and those four are what we pin down to get a real number",
                "That you cannot discuss pricing",
                "The list price minus a discount",
            ),
            answer_index=1,
            explanation=(
                "Pricing is per-contract with no public rate card. Answering with the shape "
                "answers the question honestly without inventing a number."
            ),
        ),
        TestQuestion(
            prompt="Which step is most commonly skipped, and what does skipping it cost?",
            options=(
                "The demo, which costs engagement",
                "Asking what they can consume — skip it and you promise a timeline that\n"
                " engineering cannot keep",
                "The pricing conversation, which delays the close",
                "The compliance question, which delays legal",
            ),
            answer_index=1,
            explanation=(
                "It feels technical and premature, which is exactly why it gets skipped. Two of "
                "the 32 products ship as flat files, and that changes the project entirely."
            ),
        ),
        TestQuestion(
            prompt="Which is the one number you should quote precisely, and how?",
            options=(
                "The audience figure of around 14 million monthly users",
                "The earnings accuracy: 99.975%, audited Q2 2022, via a three-step\n"
                " reconciliation — and not stretched across the other ten calendars",
                "The congressional outperformance figure of 17% in 2022",
                "The 15-minute quote delay",
            ),
            answer_index=1,
            explanation=(
                "It is audited and the quarter is known, which makes it the strongest verifiable "
                "quality claim in the catalogue. The other three are Benzinga's own claims."
            ),
        ),
        TestQuestion(
            prompt="What does a good pilot look like?",
            options=(
                "Three products across two teams, to prove breadth",
                "One product, one surface, one metric they already care about, and a date",
                "A free trial of the whole catalogue",
                "Whatever their engineering team proposes",
            ),
            answer_index=1,
            explanation=(
                "Anything broader produces an inconclusive result and a stalled renewal. A narrow "
                "pilot either works or does not, and both outcomes are useful."
            ),
        ),
        TestQuestion(
            prompt="What are the four lines you never cross?",
            options=(
                "Discounting, undercutting, over-promising, over-delivering",
                "Never quote a price; never promise a timeline; never state what a client may\n"
                " redistribute; never present a Benzinga claim as independent fact",
                "Never demo, never discount, never guess, never rush",
                "Never contact engineering, legal, compliance or procurement directly",
            ),
            answer_index=1,
            explanation=(
                "All four are avoidable with 'I will get you that in writing', which is also the "
                "most credible sentence available to you."
            ),
        ),
    ),
)


def section_8() -> CourseModule:
    """Section 8: how to sell it, and the four lines you never cross."""
    return CourseModule(
        id=_id("module", "how-to-sell-it"),
        title="How to sell it",
        order=7,
        lessons=(
            Lesson(
                id=_id("lesson", "how-to-sell-it"),
                title="The first meeting, the objections and the limits",
                body=_S8_BODY,
                order=0,
                slides=_SECTION_8_SLIDES,
                drill_topics=("product:benzinga:selling",),
                measurement=(
                    "You can run all four moves of a first meeting from memory, answer a price "
                    "push without quoting a figure, and recite the four lines you never cross."
                ),
            ),
        ),
        section_test=SECTION_8_TEST,
    )


def rebuilt_sections() -> tuple[CourseModule, ...]:
    """The sections rebuilt to the GRS-0215 standard, in order. Grows as GRS-0217 progresses."""
    return (
        section_1(),
        section_2(),
        section_3(),
        section_4(),
        section_5(),
        section_6(),
        section_7(),
        section_8(),
    )


# Sections written so far, and sections still to write. `tests/test_benzinga_course.py` asserts the
# course is UNFINISHED while anything is in SECTIONS_PLANNED, so a half-rebuilt course can never
# read as done. That mechanism exists because GRS-0191 shipped a renderer with no content and still
# read as progress; the same trap is available to a course with two sections out of eight.
SECTIONS_AUTHORED: tuple[str, ...] = (
    "what-it-is",
    "four-families",
    "how-it-arrives",
    "the-content-layer",
    "the-event-layer",
    "the-signal-layer",
    "who-buys-which-family",
    "how-to-sell-it",
)
# All eight are written (2026-07-30). The tuple stays, empty, because the test that guards it reads
# it and because the next course to be rebuilt starts from this file as its pattern.
SECTIONS_PLANNED: tuple[str, ...] = ()
