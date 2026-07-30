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
        "The catalogue bands its 32 products into four categories: **Newswire & Content** (9), "
        "**Calendar** (11), **Alternative Data** (8) and **Market Data** (4). Calendar is the "
        "biggest family and Market Data the smallest, which is the opposite of what most people "
        "assume about a company they think of as a news site.",
        refs=(CATALOGUE,),
        asset=_diagram(
            "four_families",
            "Thirty-two products become four ideas, each with one job.",
            "Four cards in a row, each showing a count and the job that family does. Newswire and "
            "Content, nine products, what a user READS. Calendar, eleven products, what a user "
            "PLANS around. Alternative Data, eight products, what a desk TRADES on. Market Data, "
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
        "Nine products, all editorial or editorial-derived: the flagship US equities newsfeed, "
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
        "Eight products, and the least homogeneous family. Options flow and block trades, insider "
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
        "nine, eleven, eight, four. If your numbers differ, you have miscounted a banded header row"
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
                "Newswire & Content, with 9",
                "Calendar, with 11",
                "Alternative Data, with 8",
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


def rebuilt_sections() -> tuple[CourseModule, ...]:
    """The sections rebuilt to the GRS-0215 standard, in order. Grows as GRS-0217 progresses."""
    return (
        section_1(),
        section_2(),
    )


# Sections written so far, and sections still to write. `tests/test_benzinga_course.py` asserts the
# course is UNFINISHED while anything is in SECTIONS_PLANNED, so a half-rebuilt course can never
# read as done. That mechanism exists because GRS-0191 shipped a renderer with no content and still
# read as progress; the same trap is available to a course with two sections out of eight.
SECTIONS_AUTHORED: tuple[str, ...] = (
    "what-it-is",
    "four-families",
)
SECTIONS_PLANNED: tuple[str, ...] = (
    "how-it-arrives",
    "the-content-layer",
    "the-event-layer",
    "the-signal-layer",
    "who-buys-which-family",
    "how-to-sell-it",
)
