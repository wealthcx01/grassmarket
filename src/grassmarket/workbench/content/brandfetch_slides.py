"""The Brandfetch course, rebuilt to the GRS-0215 depth standard (GRS-0217).

Third and last of the product-course rebuilds. Brandfetch is lower-commission than OpenBB and
Benzinga, and it is the one the founder specifically corrected us on: **we were conflating two
products.** From GRS-0185 —

    "Both Brandfetch variants currently carry identical fit stanzas and `profiles: [retail]`, so a
    retail report can be recommended either. The founder's correction: distribution suits retail
    brokerages; redistribution suits exchanges and information vendors."

So this course is organised around that boundary rather than around the product list. Section 2 is
the boundary itself, sections 5 and 6 take one side each, and section 8 makes the advisor qualify
which side a deal is on before forecasting anything.

## What this course deliberately does not claim

The GRS-0125 research pass left guardrails, and they are kept because every one of them is still a
way an advisor can damage a regulated client:

- **Brandfetch does not own the logos.** They belong to their trademark owners; Brandfetch provides
  access. The client carries the fair-use and trademark risk. Paying for access transfers nobody's
  rights, and for a financial firm misusing another institution's mark is a real exposure.
- **The display-versus-redistribute line is not publicly bright-lined.** No slide states where it
  falls. The advisor's job is to spot that the question exists and get the answer in writing.
- Founded 2020 in Switzerland. The "2006" that appears in some scraped profiles is an artefact.
- **No priced VC round is public** — only the Adobe Fund for Design grant. Do not cite a valuation,
  a round or an investor list.
- Client names (Morningstar, Envestnet | Yodlee, Typeform) and the 50M-plus company figure are
  Brandfetch's own published claims. Attribute them; never assert them.
- Pricing anchors are public and quoted as approximate, because they are a vendor's published
  numbers and those move.

Commission rates are NEVER written into a slide. Both tiers resolve live from the Earnings v7
schedule, and a number typed into content is a number that goes stale silently.

Slug is `product-brandfetch-distribution` (course slugs forbid underscores), matching the existing
`product:brandfetch_distribution` certification subject.
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

from grassmarket.workbench.content.brandfetch_diagrams import SVG

_NS = "grassmarket:academy:product-brandfetch"


def _id(kind: str, key: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"{_NS}:{kind}:{key}")


# --- Sources, declared once so a link is fixed in one place -------------------------------

SITE = SourceRef(
    title="Brandfetch product site",
    url="https://brandfetch.com/",
    kind=SourceRefKind.DOCS,
)
DOCS = SourceRef(
    title="Brandfetch developer documentation",
    url="https://docs.brandfetch.com/",
    kind=SourceRefKind.DOCS,
)
DOCS_BRAND_API = SourceRef(
    title="Brandfetch Brand API reference",
    url="https://docs.brandfetch.com/reference/retrieve-brand",
    kind=SourceRefKind.DOCS,
)
DOCS_SEARCH = SourceRef(
    title="Brandfetch Brand Search API reference",
    url="https://docs.brandfetch.com/reference/search-brands",
    kind=SourceRefKind.DOCS,
)
DOCS_LOGO_LINK = SourceRef(
    title="Brandfetch Logo Link",
    url="https://docs.brandfetch.com/docs/logo-link",
    kind=SourceRefKind.DOCS,
)
DOCS_TRANSACTION = SourceRef(
    title="Brandfetch Transaction API",
    url="https://brandfetch.com/developers/transaction-api",
    kind=SourceRefKind.DOCS,
)
PRICING = SourceRef(
    title="Brandfetch pricing (public tiers)",
    url="https://brandfetch.com/pricing",
    kind=SourceRefKind.DOCS,
)
TERMS = SourceRef(
    title="Brandfetch terms of service",
    url="https://brandfetch.com/terms",
    kind=SourceRefKind.DOCS,
)
REGISTRY = SourceRef(
    title="The Brandfetch brand registry (public directory)",
    url="https://brandfetch.com/brands",
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
    `design/motion/courses/brandfetch/`; the caption and alt text are written here, beside the slide
    they belong to, because they are prose and a generator has no business writing them.

    `SVG[key]` raises on an unknown key rather than returning a placeholder — a slide that silently
    lost its diagram would still render, and look finished."""
    return LessonAsset(caption=caption, alt=alt, svg=SVG[key])


# --- Section 1 — What Brandfetch is, and who owns the logos ---------------------------------

_S1_BODY = (
    "By the end of this lesson you can say what Brandfetch sells, why its data is better than a "
    "scraper's, and who actually owns the logos. That last question is not a footnote: it is the "
    "single fastest way to lose a regulated client's compliance team, and volunteering the answer "
    "before they ask is what makes you the advisor they are willing to deal with."
)

_SECTION_1_SLIDES: tuple[Slide, ...] = (
    _s(
        0,
        SlideKind.CONCEPT,
        "The one-sentence version",
        "Brandfetch is a brand-data platform: give it an identifier and it returns a company's "
        "visual identity — logos in every variant and format, colour palette, fonts — plus "
        "firmographics like employee count, founding year, headquarters and industry. Financial "
        "platforms buy it so every company on their screens looks like itself.",
        refs=(SITE,),
    ),
    _s(
        1,
        SlideKind.CONCEPT,
        "One registry, two sides",
        "There is a **public registry** where a company claims and verifies its own brand profile, "
        "and a **developer API** that serves what was claimed. You sell the second. The first is "
        "the reason the second is worth buying, and an advisor who cannot explain that has no "
        "answer to the only objection that really matters here.",
        refs=(REGISTRY, DOCS),
        asset=_diagram(
            "two_sides",
            "The registry is maintained by the brands themselves. That is the moat.",
            "Two panels. On the left, the public registry: a company claims its own profile and "
            "verifies it, holding logos, colours, fonts and firmographics. An arrow feeds into the "
            "right-hand panel, filled dark green: the developer API, one identifier in and brand "
            "identity out, labelled as the thing you sell. A line beneath reads: a scraper has no "
            "one maintaining it, and that is the whole argument.",
        ),
    ),
    _s(
        2,
        SlideKind.CONCEPT,
        "Why that beats scraping, concretely",
        "A scraped logo is whatever was on a website the day the scraper ran. When a company "
        "rebrands, the scrape is wrong and nobody notices until a client does. In the registry the "
        "brand owner updates its own profile and every platform pulling the API gets the change. "
        "You are not selling images, you are selling the fact that somebody maintains them.",
        refs=(REGISTRY,),
    ),
    _s(
        3,
        SlideKind.CONCEPT,
        "The scale claim, attributed",
        "Brandfetch describes an index of more than 50 million companies. That is their published "
        'figure rather than an audited one, so say "Brandfetch reports" and move on. The number '
        "is rarely the thing that closes anyway — coverage of the specific names a client holds "
        "matters far more, and that is a question you can actually test in a demo.",
        refs=(SITE,),
    ),
    _s(
        4,
        SlideKind.CONCEPT,
        "Who owns the logos, and who carries the risk",
        "Brandfetch does **not** own the logos. They remain the property of their trademark "
        "owners; Brandfetch provides access to them. Your client carries the fair-use and "
        "trademark risk: assets must be used without implying endorsement, misrepresentation, "
        "alteration or false affiliation. Paying a vendor for access does not transfer anybody's "
        "rights.",
        refs=(TERMS,),
        asset=_diagram(
            "who_owns_the_mark",
            "Three parties, and the risk does not sit where a buyer assumes it does.",
            "Three boxes in a row connected by arrows. The trademark owner owns the mark. "
            "Brandfetch provides access to it. Your client, filled dark green, carries the "
            "fair-use risk. A warning beneath reads: paying for access does not transfer anybody's "
            "rights. A second line adds: say this before the compliance officer asks.",
        ),
    ),
    _s(
        5,
        SlideKind.CONCEPT,
        "Why that matters more here than elsewhere",
        "A retail brokerage showing another bank's logo on a comparison screen is using a "
        "competitor's registered mark in a regulated context. That is a real exposure, and it is "
        "theirs rather than Brandfetch's. You are selling access to brand data, not indemnity for "
        "how the marks get used, and being clear about that is the difference between a short "
        "compliance review and a dead deal.",
        refs=(TERMS,),
    ),
    _s(
        6,
        SlideKind.EXAMPLE,
        "The sentence to say in the first meeting",
        '"One thing worth flagging now rather than in legal: Brandfetch gives you access to brand '
        "assets, it does not own them. The trademark owners do, and the usage obligations sit with "
        "you. Most firms are already handling that for other marks they display, but your "
        'compliance team will want to see it written down." Thirty seconds, and it changes the '
        "tone of everything after it.",
    ),
    _s(
        7,
        SlideKind.CONCEPT,
        "Where the company came from, carefully",
        "Founded in 2020 in Switzerland by Amin Kasimov, Nuri Kasimov and Jérémy Jaques, out of a "
        "designer's frustration that brand assets are scattered and hunting them wastes hours. If "
        "you see 2006 on a scraped profile somewhere, that is an artefact rather than a fact.",
        refs=(SITE,),
    ),
    _s(
        8,
        SlideKind.CONCEPT,
        "The funding question, and the honest answer",
        "It was backed early by the **Adobe Fund for Design**. There is no public priced round, no "
        "published valuation and no investor list, so do not cite one. Largely grant-supported and "
        "bootstrapped is the accurate description, and for an infrastructure vendor it reads as "
        "discipline rather than as weakness — say it that way.",
    ),
    _s(
        9,
        SlideKind.CONCEPT,
        "Peer proof, and how to use it",
        "Brandfetch names Morningstar (keeping financial-institution assets current), Envestnet | "
        "Yodlee (improving merchant identification) and Typeform (a reported 5% free-to-paid lift "
        "after adding it to onboarding). Those are the company's published claims about its own "
        "customers. They are strong and they are worth citing — attributed, in that form.",
        refs=(SITE,),
    ),
    _s(
        10,
        SlideKind.CONCEPT,
        "What Brandfetch is NOT",
        "It is not a market-data vendor, not a fundamentals source, not an entity-reference master "
        "and not a KYC provider. It carries brand identity and light firmographics. If a client "
        "needs legal entity hierarchies, LEIs or sanctions screening, this is the wrong vendor and "
        "saying so costs you nothing.",
        refs=(SITE,),
    ),
    _s(
        11,
        SlideKind.WALKTHROUGH,
        "Look one company up, yourself",
        "Open a browser and hit `cdn.brandfetch.io/nike.com`. A current Nike logo comes back from "
        "a URL with no key and no integration. That is the entire land motion in one line, and it "
        "is also why the free surface is a demo rather than a deal — you have just proved the "
        "product works and sold nothing.",
        refs=(DOCS_LOGO_LINK,),
    ),
    _s(
        12,
        SlideKind.WALKTHROUGH,
        "Now look one up the way finance would",
        "Read the Brand API reference and find the lookup paths. Note that it takes a stock ticker "
        "and an ISIN, not just a domain: `/v2/brands/ticker/NKE` and `/v2/brands/isin/"
        "US6541061031`. Write both down. Section 4 is entirely about why that is the most sellable "
        "fact in the product.",
        refs=(DOCS_BRAND_API,),
    ),
    _s(
        13,
        SlideKind.WALKTHROUGH,
        "Read the terms far enough to find the boundary",
        "Skim the terms of service for two things: who owns the assets, and what the licence says "
        "about passing data to third parties. You are not looking for a legal conclusion — you are "
        "confirming that the second question exists and is not answered in a public page. That is "
        "the whole basis of the next section.",
        refs=(TERMS,),
    ),
    _s(
        14,
        SlideKind.WALKTHROUGH,
        "Find one company the registry does not have well",
        "Search the public registry for a small or private firm your target would care about. "
        "Coverage of large listed names is excellent; the long tail is thinner. Knowing where it "
        "thins out means you can answer a coverage question honestly instead of promising the 50 "
        "million and discovering the gap during a pilot.",
        refs=(REGISTRY,),
    ),
    _s(
        15,
        SlideKind.EXAMPLE,
        "A meeting that goes wrong in one sentence",
        '"It has every logo you will ever need and you are fully covered on the licensing." Two '
        "claims, both unsupportable: the long tail is genuinely thinner than the headline figure, "
        "and the licensing obligations are the client's. When either surfaces later it surfaces as "
        "you having misled them.",
    ),
    _s(
        16,
        SlideKind.EXAMPLE,
        "The same meeting, done properly",
        '"Coverage of listed names is strong — test your own universe in the demo, that is the '
        "honest way to check. On licensing, you get access and the usage obligations stay with "
        'you, same as any other mark you display." Both true, both checkable, and neither creates '
        "a problem for month three.",
    ),
    _s(
        17,
        SlideKind.CONCEPT,
        "The objection you will hear first",
        "\"Can't we just scrape logos?\" Scraping is barred by most sites' terms, gets an IP "
        'blocked, and produces assets that go stale silently. The registry answer is not "ours are '
        'prettier", it is "ours are maintained by the brand owner and yours are a snapshot". '
        "That is a structural argument rather than a quality claim.",
        refs=(REGISTRY, TERMS),
    ),
    _s(
        18,
        SlideKind.CONCEPT,
        "The objection you will hear second",
        '"Isn\'t it just logos?" No: colours, fonts, firmographics, and identifier lookups by '
        "ticker, ISIN and crypto symbol that no generic logo service offers. If the conversation "
        "stays on logos you will end up arguing about a free image URL, which is a conversation "
        "with no revenue in it.",
        refs=(DOCS_BRAND_API,),
    ),
    _s(
        19,
        SlideKind.CONCEPT,
        "One question that opens the account",
        '"Where in your product does a company appear as just a ticker or a name?" Every '
        "platform has several places, and each one is a surface this product improves. It also "
        "gets the client describing their own screens, which is more useful than anything you can "
        "say about the catalogue.",
    ),
    _s(
        20,
        SlideKind.CONCEPT,
        "What the next seven sections do",
        "Section 2 is the boundary that decides which of two products a deal is — the most "
        "important thing in this course. Section 3 is the four surfaces and the order to meet them "
        "in. Section 4 is the identifier hook. Sections 5 and 6 take one side of the boundary "
        "each. Section 7 is licensing and compliance. Section 8 is the sale.",
    ),
    _s(
        21,
        SlideKind.CHECKPOINT,
        "Say the ownership sentence out loud",
        "Without looking: who owns the logos, what Brandfetch provides, and who carries the "
        "fair-use risk. Then say the thirty-second version you would use in a first meeting. If "
        "you cannot produce it cold, you will not produce it under pressure — and this is the one "
        "you most need under pressure.",
        checkpoint=(
            "Say who owns the marks, what Brandfetch provides, who carries the risk, and your "
            "thirty-second version, all from memory."
        ),
    ),
    _s(
        22,
        SlideKind.CHECKPOINT,
        "Write your opening four sentences",
        "One sentence on what Brandfetch is, one on the registry versus a scraper, one on "
        "ownership, and one question back to them. Keep it — you will extend it in section 8 once "
        "you know which of the two products you are selling and to whom.",
        checkpoint="Write your four-sentence opening and keep it for section 8.",
    ),
    _s(
        23,
        SlideKind.CONCEPT,
        "The one thing to carry into section 2",
        "Everything so far has described one product. There are two, they are licensed "
        "differently, they are sold to different segments and they pay different commission. The "
        "founder's correction to this course was that we were treating them as interchangeable. "
        "The next section is that correction.",
    ),
)

SECTION_1_TEST = SectionTest(
    pass_mark=0.8,
    questions=(
        TestQuestion(
            prompt="Who owns the logos Brandfetch serves, and who carries the usage risk?",
            options=(
                "Brandfetch owns them and indemnifies the client",
                "The trademark owners own them; Brandfetch provides access; the client\n"
                " carries the fair-use and trademark risk",
                "The client owns them once licensed",
                "Ownership transfers on the Enterprise tier",
            ),
            answer_index=1,
            explanation=(
                "Paying a vendor for access transfers nobody's rights. For a regulated firm "
                "displaying another institution's mark this is a real exposure, and volunteering "
                "it makes the compliance review short."
            ),
        ),
        TestQuestion(
            prompt='What is the structural answer to "can\'t we just scrape logos?"',
            options=(
                "Brandfetch's assets are higher resolution",
                "The brand owner maintains its own profile in the registry, so it stays current;\n"
                " a scrape is a snapshot that goes stale silently",
                "Scraping is illegal everywhere",
                "Brandfetch is cheaper than building a scraper",
            ),
            answer_index=1,
            explanation=(
                "It is a maintenance argument, not a quality claim. You are not selling images, "
                "you are selling the fact that somebody keeps them right."
            ),
        ),
        TestQuestion(
            prompt="How should you handle Brandfetch's funding history?",
            options=(
                "Cite the most recent valuation",
                "Say it was backed by the Adobe Fund for Design, with no public priced round,\n"
                " and describe it as grant-supported and bootstrapped",
                "Avoid the subject",
                "Describe it as venture-backed",
            ),
            answer_index=1,
            explanation=(
                "No priced round, valuation or investor list is public, so citing one invents a "
                "fact. For infrastructure, bootstrapped reads as discipline rather than weakness."
            ),
        ),
        TestQuestion(
            prompt="Which of these is Brandfetch NOT?",
            options=(
                "A source of logos, colours and fonts",
                "A source of light firmographics",
                "An entity-reference master or KYC provider",
                "A brand registry the owners maintain",
            ),
            answer_index=2,
            explanation=(
                "No legal entity hierarchies, LEIs or sanctions screening. If that is the need, it "
                "is the wrong vendor and saying so costs nothing."
            ),
        ),
        TestQuestion(
            prompt="Why is the 50-million-company figure a weak thing to lead with?",
            options=(
                "It is untrue",
                "It is Brandfetch's own published claim, and coverage of the specific names a\n"
                " client holds matters more and can be tested in a demo",
                "Competitors quote higher numbers",
                "It only counts listed companies",
            ),
            answer_index=1,
            explanation=(
                "Attribute it, then move to the thing that actually decides the deal. The long "
                "tail is genuinely thinner than the headline, so promising the headline creates a "
                "pilot problem."
            ),
        ),
        TestQuestion(
            prompt="What is the best opening question for this product?",
            options=(
                "What is your logo budget?",
                "Where in your product does a company appear as just a ticker or a name?",
                "Do you currently scrape logos?",
                "How many API calls would you need?",
            ),
            answer_index=1,
            explanation=(
                "Every platform has several such places, each one a surface this improves, and the "
                "question gets the client describing their own screens."
            ),
        ),
    ),
)


def section_1() -> CourseModule:
    """Section 1: what Brandfetch is, and the ownership disclosure that comes first."""
    return CourseModule(
        id=_id("module", "what-it-is"),
        title="What Brandfetch is, and who owns the logos",
        order=0,
        lessons=(
            Lesson(
                id=_id("lesson", "what-it-is"),
                title="The registry, the API and the marks",
                body=_S1_BODY,
                order=0,
                slides=_SECTION_1_SLIDES,
                drill_topics=("product:brandfetch:what-it-is",),
                measurement=(
                    "You can explain the registry-versus-scraper argument and state who owns the "
                    "marks and who carries the risk, without notes."
                ),
            ),
        ),
        section_test=SECTION_1_TEST,
    )


# --- Section 2 — The boundary: distribution or redistribution -------------------------------

_S2_BODY = (
    "This is the most important section in the course and the reason the course was rebuilt. "
    "Brandfetch is two products, not one. They differ in what the client may do with the data, in "
    "which licence they need, in which segment buys them, and in what you earn. By the end of this "
    "lesson you can tell which of the two a deal is from one question, and you will know why you "
    "must never answer that question on the client's behalf."
)

_SECTION_2_SLIDES: tuple[Slide, ...] = (
    _s(
        0,
        SlideKind.CONCEPT,
        "One boundary decides the whole deal",
        "The question is simply: **does the brand data stop inside the client's own product, or "
        "does it travel further?** If it stops, that is distribution. If it goes on to their "
        "customers, that is redistribution. Everything else — the licence, the contract shape, the "
        "segment, your rate — follows from which side of that line you are on.",
        refs=(TERMS,),
        asset=_diagram(
            "two_licences",
            "Distribution and redistribution differ in licence, buyer and commission. One "
            "question separates them.",
            "A vertical boundary with two panels. On the left, DISTRIBUTION: the data is "
            "shown inside the client's own product, under the standard paid API, bought by "
            "retail brokerages. On the right, filled dark green, REDISTRIBUTION: the data is "
            "passed on to their customers, under enterprise custom licensing only, bought by "
            "exchanges and information vendors. A warning beneath reads: the line is not "
            "publicly bright-lined, never decide it yourself.",
        ),
    ),
    _s(
        1,
        SlideKind.CONCEPT,
        "Distribution, precisely",
        "In-product use. The client adopts the standard paid API and **displays** brand data "
        "inside its own product to its own users. Self-serve to sign up, a caching rule to "
        "respect, no attribution requirement. This is the higher-volume, faster motion, and it is "
        "the one you can actually drive without a legal negotiation.",
        refs=(DOCS_BRAND_API, TERMS),
    ),
    _s(
        2,
        SlideKind.CONCEPT,
        "Redistribution, precisely",
        "Passing Brandfetch's brand **data** onward — to third parties, to the client's own "
        "end-clients, or under a white-label or reseller arrangement. This is barred under the "
        "standard licence. It needs Enterprise custom licensing, with its own delivery mechanics "
        "(bulk file transfer, webhooks) and its own legal terms.",
        refs=(TERMS,),
    ),
    _s(
        3,
        SlideKind.CONCEPT,
        "Why the two rates differ, and in which direction",
        "Distribution pays the **higher** rate. That surprises advisors who assume the enterprise "
        "deal pays more. It pays more because it is the motion you can drive: self-serve adoption "
        "you can influence, at volume. Redistribution is a lower-rate, enterprise-negotiated model "
        "where the contracting is done by others. Read both live off the Earnings page.",
    ),
    _s(
        4,
        SlideKind.CONCEPT,
        "The windows differ too",
        "The two tiers do not just pay different percentages — they run over different attribution "
        "windows, and one steps down after year one while the other does not. That changes which "
        "deal is worth more to you over its life, and it is not something you can work out from "
        "the headline rate. Look at both numbers on the Earnings page, not one.",
    ),
    _s(
        5,
        SlideKind.CONCEPT,
        "The segments are scoped, deliberately",
        "The two variants are scoped to different operating-model profiles in the fit map, so the "
        "sell panel will not offer you both on the same report. Distribution surfaces for retail "
        "brokerages. Redistribution surfaces for exchanges. That was a correction: both used to be "
        "scoped to retail, and a retail report could recommend either.",
    ),
    _s(
        6,
        SlideKind.CONCEPT,
        "Why the founder corrected it",
        "Because offering a venue the retail variant, or a brokerage the enterprise one, is a "
        "credibility loss you do not recover in the same meeting. The two products answer "
        "different motives: a brokerage wants its own app to look right, and a venue wants to "
        "enrich what it already licenses onward. Same data, different job.",
    ),
    _s(
        7,
        SlideKind.CONCEPT,
        "The line is not publicly bright, and that is the point",
        "Brandfetch's public terms do not draw a precise boundary between displaying and "
        "redistributing. Real cases sit in the middle: an adviser-facing portal, a co-branded "
        "widget, a report a client emails to their own customer. You are not the person who "
        "decides those, and pretending to be is how a deal gets re-papered six months in.",
        refs=(TERMS,),
    ),
    _s(
        8,
        SlideKind.CONCEPT,
        "What you do instead of deciding",
        "You spot that the question exists, you name it in the room, and you get the answer in "
        'writing for that specific use case before anything is signed. "That may cross into '
        'redistribution and I would rather we confirm it than assume" is a sentence that makes '
        "you more credible, not less. Nobody has ever lost a deal by asking it.",
    ),
    _s(
        9,
        SlideKind.EXAMPLE,
        "A clear case of distribution",
        "A retail brokerage shows each holding's logo on its own app's portfolio screen. The data "
        "is rendered to their own logged-in users inside their own product and goes nowhere else. "
        "Standard paid API, self-serve, no legal negotiation. This is the majority of what you "
        "will sell.",
        refs=(DOCS_BRAND_API,),
    ),
    _s(
        10,
        SlideKind.EXAMPLE,
        "A clear case of redistribution",
        "An exchange adds brand identity as a field on the instrument reference file it already "
        "ships to its data customers. The data leaves their building and lands in someone else's "
        "system. Enterprise licensing, bulk delivery, custom terms. Nothing about that is "
        "self-serve.",
        refs=(TERMS,),
    ),
    _s(
        11,
        SlideKind.EXAMPLE,
        "A case that is genuinely unclear",
        "A wealth platform generates a branded quarterly PDF, with holding logos, that the adviser "
        "emails to the end client. Is that display inside their product, or data reaching a third "
        "party? Reasonable people differ. **Do not answer it.** Name it, and get it confirmed in "
        "writing for that use case.",
    ),
    _s(
        12,
        SlideKind.EXAMPLE,
        "Another one, and why it matters commercially",
        "A B2B fintech powers a white-labelled portal for twelve bank clients, each seeing their "
        "own customers' data with logos. That is very likely redistribution, which means a "
        "different licence, a different contract path and a different rate. Getting this wrong "
        "does not just misprice the deal — it promises a self-serve signup that does not exist.",
        refs=(TERMS,),
    ),
    _s(
        13,
        SlideKind.WALKTHROUGH,
        "Write the one question down",
        "Write it in the words you would actually use, not the licence's words. Something like: "
        "\"Does anyone outside your own product ever see this data — your clients' clients, a "
        'partner, an exported file?" Notice it asks about people rather than about licensing, '
        "which is why it gets an answer.",
    ),
    _s(
        14,
        SlideKind.WALKTHROUGH,
        "Sort five scenarios yourself",
        "Take the four examples above plus one from your own pipeline and sort each into "
        "distribution, redistribution, or genuinely unclear. Getting a scenario into the third "
        "bucket is a correct answer, not a failure — the third bucket is the one this section "
        "exists to teach you to recognise.",
    ),
    _s(
        15,
        SlideKind.WALKTHROUGH,
        "Look up both rates and both windows",
        "Open the Earnings page and read all four numbers: the two rates and the two windows. Note "
        "which tier steps down and which does not. Do this now so that the shape is in your head, "
        "and do it again before every forecast, because the schedule is the source and this course "
        "deliberately is not.",
    ),
    _s(
        16,
        SlideKind.WALKTHROUGH,
        "Check which variant your target's segment sees",
        "Open a live assessment for a retail brokerage and one for an exchange, and look at what "
        "the sell panel offers. You should see distribution on one and redistribution on the "
        "other, never both on either. If you see both, that is a bug worth reporting rather than "
        "an opportunity.",
    ),
    _s(
        17,
        SlideKind.CONCEPT,
        "The objection this section creates",
        '"Can we resell the data to our clients?" Now you know the answer: only under Enterprise '
        "custom licensing, never under the standard tier, and there is no public self-serve "
        "reseller programme. Say that plainly. An advisor who hedges here creates exactly the "
        "expectation the contract will refuse.",
        refs=(TERMS,),
    ),
    _s(
        18,
        SlideKind.CONCEPT,
        "What never to say",
        "Never say the standard tier covers redistribution. Never guess where the line falls. "
        "Never quote a rate from memory. And never forecast a commission before you know which of "
        "the two products the deal is, because the two numbers are different and the windows are "
        "different too.",
    ),
    _s(
        19,
        SlideKind.CONCEPT,
        "Why this is the whole course in one idea",
        "Sections 3 and 4 describe the products. Sections 5 and 6 take one side of this boundary "
        "each. Section 7 is the licensing detail underneath it, and section 8 makes you qualify it "
        "before forecasting. If you only remember one thing from this course, remember the "
        "question: does the data leave their product?",
    ),
    _s(
        20,
        SlideKind.CONCEPT,
        "A useful way to hold it",
        'Distribution is "your app, on-brand". Redistribution is "license brand data to serve '
        'your customers". Six words each. If you can say which of those two a prospect is asking '
        "for, you have qualified the deal, chosen the segment and identified the contract path in "
        "one move.",
    ),
    _s(
        21,
        SlideKind.CHECKPOINT,
        "Say the boundary question cold",
        "From memory: the one question, both answers, which segment goes with each, and which of "
        "the two pays the higher rate. Four facts. If the rate direction surprises you, that is "
        "exactly why it is on the list — most advisors guess it the wrong way round.",
        checkpoint=(
            "State the boundary question, both sides, both segments, and which tier pays more, "
            "all from memory."
        ),
    ),
    _s(
        22,
        SlideKind.CHECKPOINT,
        "Rehearse the unclear case out loud",
        "Say what you would actually say when a use case sits in the middle. It must name the "
        "uncertainty and propose getting it in writing, without sounding like you do not know your "
        "own product. That distinction is entirely in the delivery, which is why this is a "
        "say-it-aloud exercise rather than a reading one.",
        checkpoint="Say your handling of an unclear use case aloud, once.",
    ),
    _s(
        23,
        SlideKind.CONCEPT,
        "Where this goes next",
        "You now know which product a deal is. Section 3 is what is actually in the product — four "
        "surfaces and the order you meet them in — because knowing the boundary does not yet tell "
        "you what to demo on a Tuesday afternoon.",
    ),
)

SECTION_2_TEST = SectionTest(
    pass_mark=0.8,
    questions=(
        TestQuestion(
            prompt="What single question separates distribution from redistribution?",
            options=(
                "How many API calls per month will they make?",
                "Does the brand data stop inside the client's own product, or travel on to\n"
                " their customers?",
                "Are they on the free tier or the paid tier?",
                "Do they need a service-level agreement?",
            ),
            answer_index=1,
            explanation=(
                "Licence, contract shape, segment and your rate all follow from which side of that "
                "line the deal sits on. It is the one thing to carry out of this course."
            ),
        ),
        TestQuestion(
            prompt="Which tier pays the higher rate, and why?",
            options=(
                "Redistribution, because enterprise deals are larger",
                "Distribution, because it is the self-serve motion at volume that you can\n"
                " actually influence; redistribution is enterprise-negotiated by others",
                "They pay the same",
                "It depends on the segment",
            ),
            answer_index=1,
            explanation=(
                "Most advisors guess this the wrong way round. The higher rate follows the motion "
                "you can drive, not the size of the contract."
            ),
        ),
        TestQuestion(
            prompt=(
                "A wealth platform emails advisers a branded PDF with holding logos. Which is it?"
            ),
            options=(
                "Clearly distribution",
                "Clearly redistribution",
                "Genuinely unclear: name it and get it confirmed in writing for that use case",
                "It depends on the PDF size",
            ),
            answer_index=2,
            explanation=(
                "The public terms do not draw a precise line and reasonable people differ here. "
                "Recognising the third bucket is a correct answer, not a failure."
            ),
        ),
        TestQuestion(
            prompt='"Can we resell the data to our clients?" What do you say?',
            options=(
                "Yes, on the paid tier",
                "Only under Enterprise custom licensing, never the standard tier, and there is\n"
                " no public self-serve reseller programme",
                "Yes, with attribution",
                "That you will need to check",
            ),
            answer_index=1,
            explanation=(
                "Hedging here creates exactly the expectation the contract will refuse. This one "
                "you can and should answer plainly."
            ),
        ),
        TestQuestion(
            prompt="Why were the two variants re-scoped to different segments?",
            options=(
                "To simplify the fit map",
                "Because both were scoped to retail, so a retail report could recommend either —\n"
                " and offering a venue the retail variant is a credibility loss",
                "Because redistribution was discontinued for retail",
                "To match the commission windows",
            ),
            answer_index=1,
            explanation=(
                "The two answer different motives: a brokerage wants its own app to look right, a "
                "venue wants to enrich what it already licenses onward."
            ),
        ),
        TestQuestion(
            prompt="What must you never do about the display-versus-redistribute boundary?",
            options=(
                "Raise it in a first meeting",
                "Decide where it falls yourself",
                "Ask for it in writing",
                "Mention that the terms are not explicit",
            ),
            answer_index=1,
            explanation=(
                "The other three are all correct behaviour. Deciding it yourself is how a deal "
                "gets re-papered six months in, and nobody has ever lost a deal by asking."
            ),
        ),
    ),
)


def section_2() -> CourseModule:
    """Section 2: the boundary that decides licence, segment and commission."""
    return CourseModule(
        id=_id("module", "the-boundary"),
        title="The boundary: distribution or redistribution",
        order=1,
        lessons=(
            Lesson(
                id=_id("lesson", "the-boundary"),
                title="Two products, one question",
                body=_S2_BODY,
                order=0,
                slides=_SECTION_2_SLIDES,
                drill_topics=("product:brandfetch:the-boundary",),
                measurement=(
                    "You can sort an unseen use case into distribution, redistribution or "
                    "genuinely unclear, and you never decide the boundary yourself."
                ),
            ),
        ),
        section_test=SECTION_2_TEST,
    )


# --- Section 3 — The four surfaces, and the order you meet them -----------------------------

_S3_BODY = (
    "Four products, and the order matters more than the list. Two are free and exist to get you in "
    "the room; two are paid and are where the deal is. By the end of this lesson you can demo the "
    "free surface in under a minute and know exactly why that demo is not the sale, which is the "
    "mistake this section exists to prevent."
)

_SECTION_3_SLIDES: tuple[Slide, ...] = (
    _s(
        0,
        SlideKind.CONCEPT,
        "Land free, expand into the paid data",
        "The motion is a ladder rather than a menu. **Logo Link** and **Brand Search** are free at "
        "meaningful volume and take minutes to adopt. The **Brand API** is the paid enrichment "
        "layer. The **Transaction API** is Enterprise. You land on a free surface and expand into "
        "the paid one, and the expansion is the revenue.",
        refs=(PRICING,),
        asset=_diagram(
            "four_surfaces",
            "The four surfaces as a ladder. Height is commitment, and only the top two are "
            "revenue.",
            "Four rising bars. Logo Link, an image URL, free tier. Brand Search, a "
            "type-ahead, free tier. Brand API, identity by ticker, paid, filled dark green. "
            "Transaction API, messy descriptors, enterprise, also dark green and tallest. A "
            "line beneath reads: demo the free surface, sell the paid one, they are not the "
            "same conversation.",
        ),
    ),
    _s(
        1,
        SlideKind.CONCEPT,
        "Logo Link: an image URL, and nothing else",
        "A CDN URL keyed by domain — or by ticker or ISIN — that you drop straight into an image "
        "tag. `cdn.brandfetch.io/nike.com` and the logo stays current forever. Free to roughly 500 "
        "thousand requests a month, no attribution required. No API key, no integration, no "
        "procurement.",
        refs=(DOCS_LOGO_LINK, PRICING),
    ),
    _s(
        2,
        SlideKind.CONCEPT,
        "Why that is both the best and worst thing you have",
        "Best, because it is the fastest credible demo in the entire product catalogue: one URL, "
        "live, in a browser, in front of anyone. Worst, because a client who adopts only this has "
        "taken something free and you have earned nothing. Demo it; never let it be the whole "
        "conversation.",
        refs=(DOCS_LOGO_LINK,),
    ),
    _s(
        3,
        SlideKind.CONCEPT,
        "Brand Search: the type-ahead",
        "Company autocomplete. Per keystroke it returns matching companies with domain, logo and "
        "colours, so a form field becomes a picker with visual confirmation. Also free to roughly "
        "500 thousand requests a month. This is the onboarding surface, and it is where the "
        "Typeform conversion story sits.",
        refs=(DOCS_SEARCH, PRICING),
    ),
    _s(
        4,
        SlideKind.CONCEPT,
        "The Brand API: the paid layer, and the real product",
        "One identifier in, a structured object out: logos in every variant and format, colour "
        "palette, fonts, description, and firmographics — employees, founding year, headquarters, "
        "industry, social links. Public pricing starts around $99 a month with roughly $0.10 "
        "per-request overage. This is the one that carries the commission.",
        refs=(DOCS_BRAND_API, PRICING),
    ),
    _s(
        5,
        SlideKind.CONCEPT,
        "The Transaction API: the newest, and the most specific",
        "Enterprise tier. It turns raw card and bank statement descriptors into clean merchant "
        "brand data: send something like `STARBUCKS 1523 OMAHA NE` with a country code and get "
        "Starbucks back, with name, domain, logo, industry and metadata. Brandfetch cites "
        "Envestnet | Yodlee using it for exactly this merchant-identification problem.",
        refs=(DOCS_TRANSACTION,),
    ),
    _s(
        6,
        SlideKind.CONCEPT,
        "Who the Transaction API is actually for",
        "Neobanks, budgeting and personal-finance apps, expense management, card issuers, "
        "open-banking aggregators. Anyone whose users look at a statement and cannot recognise "
        "their own spending. It is not for a brokerage — a holdings screen has tickers, not "
        "merchant descriptors — so do not reach for it in a retail pitch.",
        refs=(DOCS_TRANSACTION,),
    ),
    _s(
        7,
        SlideKind.CONCEPT,
        "The brand layer for AI, mentioned carefully",
        "Brandfetch also positions a Brand Context API and gen-AI integrations, and the "
        "Transaction API is recent. Worth knowing because a buyer may ask, and worth being brief "
        "about because it is direction rather than the thing you are selling this quarter. Lead "
        "with the Brand API; mention the rest as evidence the vendor is not standing still.",
        refs=(SITE,),
    ),
    _s(
        8,
        SlideKind.CONCEPT,
        "The pricing anchors, and how to quote them",
        "Free to roughly 500 thousand a month on the two free surfaces. Brand API from around $99 "
        "a month with roughly $0.10 overage. Enterprise is a custom quote with unlimited volume, a "
        "99.9% availability commitment, webhooks and bulk file transfer. Quote all of those as "
        "approximate published figures, because that is what they are.",
        refs=(PRICING,),
    ),
    _s(
        9,
        SlideKind.CONCEPT,
        "There is no self-serve reseller programme",
        "Worth stating alongside the pricing, because it is the thing a commercially minded buyer "
        "will assume exists. Redistribution rights are bespoke Enterprise contracting. If a "
        "prospect starts describing a reseller model, you are not on the pricing page any more — "
        "you are in section 2's right-hand column.",
        refs=(PRICING, TERMS),
    ),
    _s(
        10,
        SlideKind.CONCEPT,
        "The caching rule, and why it exists",
        "The standard licence expects cached brand assets to be refreshed rather than held "
        "indefinitely. That is not bureaucratic: the entire value proposition is that the data "
        "stays current, and a client who caches forever has silently converted the product back "
        "into a scrape. Mention it as a design note, not a restriction.",
        refs=(TERMS,),
    ),
    _s(
        11,
        SlideKind.WALKTHROUGH,
        "Do the sixty-second demo",
        "In a browser: `cdn.brandfetch.io/` plus a domain your prospect cares about. Then the same "
        "with a ticker. Two URLs, no setup, and you have shown the product works on their own "
        "names. Practise it until it takes under a minute, because a demo that needs a screen "
        "share and a login is a demo you will not get to give.",
        refs=(DOCS_LOGO_LINK,),
    ),
    _s(
        12,
        SlideKind.WALKTHROUGH,
        "Read one full Brand API response",
        "Find a sample response in the Brand API reference and read every field. Note how much is "
        "not a logo: colours with their usage, fonts, description, employee count, founding year, "
        'headquarters, industry. That list is your answer to "isn\'t it just logos?", and it is '
        "much more convincing read out than summarised.",
        refs=(DOCS_BRAND_API,),
    ),
    _s(
        13,
        SlideKind.WALKTHROUGH,
        "Work out one client's rough volume",
        "Take a target platform and estimate calls: how many companies on a screen, how many "
        "screen loads a day, how much can be cached within the refresh rule. You will usually find "
        "the free tier covers a small platform entirely, which tells you the paid conversation is "
        "about the enrichment fields rather than about volume.",
        refs=(PRICING,),
    ),
    _s(
        14,
        SlideKind.WALKTHROUGH,
        "Write the expand sentence",
        'Write what you will say when a client is happy on the free tier. Something like: "The '
        "URL gets you the mark. What it does not get you is the colour palette to theme against, "
        'the firmographics, or lookup by ISIN — that is the Brand API." Have it ready, because '
        "this moment arrives in every deal.",
        refs=(DOCS_BRAND_API,),
    ),
    _s(
        15,
        SlideKind.EXAMPLE,
        "A deal that stalled on the free tier",
        "An advisor demos Logo Link, the client's engineer drops it in that afternoon, everyone is "
        "delighted, and there is no reason to talk again. The product worked perfectly and the "
        "advisor earned nothing. The demo was right; the absence of an expand sentence was the "
        "mistake.",
    ),
    _s(
        16,
        SlideKind.EXAMPLE,
        "The same deal, expanded",
        'Same demo, then: "Now, your holdings are keyed by ISIN and half your universe is '
        "non-US — the free URL is domain-first. Lookup by ISIN, plus the palette so the cards "
        'theme to each issuer, is the paid tier. Shall we size it?" One sentence, and the '
        "conversation has moved to the product that pays.",
        refs=(DOCS_BRAND_API,),
    ),
    _s(
        17,
        SlideKind.EXAMPLE,
        '"Is it free?", answered properly',
        '"The logo URL and the company search are free at real volume — genuinely, not as a '
        "trial. The enrichment data behind them is paid, and that is the part that does the work "
        'in your product." Both halves matter: the honesty about free buys you the credibility to '
        "charge for the rest.",
        refs=(PRICING,),
    ),
    _s(
        18,
        SlideKind.CONCEPT,
        "What each surface tells you about the buyer",
        "If they want Logo Link, they have a cosmetic gap and a small budget. Brand Search means "
        "an onboarding or conversion problem. Brand API means they have records keyed by "
        "identifiers and want them enriched. Transaction API means their users cannot read their "
        "own statements. The surface they reach for is a diagnosis.",
    ),
    _s(
        19,
        SlideKind.CONCEPT,
        "What never to promise about the surfaces",
        "Do not promise the free tiers will stay free at their volume, do not promise coverage of "
        "a specific long-tail universe you have not tested, and do not promise the Transaction API "
        "to anyone whose data is not merchant descriptors. All three are checkable, and all three "
        "are checked by an engineer rather than by you.",
    ),
    _s(
        20,
        SlideKind.CONCEPT,
        "Where the boundary from section 2 shows up here",
        "The Transaction API and Enterprise are where redistribution conversations live, because "
        "Enterprise is the only tier under which redistribution is licensed at all. So a prospect "
        "asking about bulk file delivery or webhooks has told you which side of the boundary they "
        "are on, before you asked.",
        refs=(TERMS, PRICING),
    ),
    _s(
        21,
        SlideKind.CHECKPOINT,
        "Give the demo out loud, timed",
        "Actually do it: sixty seconds, two URLs, on a company your next prospect cares about, out "
        "loud as though someone is watching. Then immediately say your expand sentence. Those two "
        "things back to back are the whole of this section.",
        checkpoint="Run the sixty-second demo aloud, then say your expand sentence, back to back.",
    ),
    _s(
        22,
        SlideKind.CHECKPOINT,
        "Name the four and their tier from memory",
        "Four surfaces, which two are free, roughly where the paid tier starts, and what "
        "Enterprise adds. If you cannot place a surface on the ladder you will end up quoting the "
        "wrong thing in a pricing conversation, which is the one place a vague answer costs you "
        "the deal.",
        checkpoint="Name all four surfaces, their tiers, and what Enterprise adds, from memory.",
    ),
    _s(
        23,
        SlideKind.CONCEPT,
        "Where this goes next",
        "You can now demo the product and price it roughly. Section 4 is the single fact that "
        "makes the Brand API worth more to a financial platform than any generic logo service — "
        "and it is one line of a URL.",
    ),
)

SECTION_3_TEST = SectionTest(
    pass_mark=0.8,
    questions=(
        TestQuestion(
            prompt="Which two surfaces are free at meaningful volume, and why does that matter?",
            options=(
                "Brand API and Transaction API, because enterprise pricing is bundled",
                "Logo Link and Brand Search — they are the fastest credible demo, and also the\n"
                " reason a deal can stall with nothing earned",
                "Logo Link and Brand API, because logos are commodity data",
                "None of them; all four are paid",
            ),
            answer_index=1,
            explanation=(
                "Best and worst thing you have. Demo them, then move deliberately to the paid tier "
                "with a prepared expand sentence."
            ),
        ),
        TestQuestion(
            prompt="Who is the Transaction API for, and who is it NOT for?",
            options=(
                "Any financial platform",
                "Neobanks, budgeting apps, expense management, card issuers — NOT a brokerage,\n"
                " whose screens carry tickers rather than merchant descriptors",
                "Exchanges and information vendors only",
                "Research and analytics platforms",
            ),
            answer_index=1,
            explanation=(
                "It resolves statement descriptors to merchants. Reaching for it in a retail "
                "brokerage pitch shows you have not understood their screens."
            ),
        ),
        TestQuestion(
            prompt="A client is happy on the free tier. What is the expand move?",
            options=(
                "Warn them the free tier will not last",
                "Name what the free URL does not give them: the colour palette, the\n"
                " firmographics, and lookup by ISIN",
                "Offer a discount on the paid tier",
                "Escalate to Enterprise",
            ),
            answer_index=1,
            explanation=(
                "The demo was right; the absence of a prepared expand sentence is what leaves an "
                "advisor delighted and unpaid."
            ),
        ),
        TestQuestion(
            prompt="Why does the standard licence expect cached assets to be refreshed?",
            options=(
                "To increase billable request volume",
                "Because the value proposition is that the data stays current — caching forever\n"
                " silently converts the product back into a scrape",
                "For trademark compliance",
                "To support the free tier's rate limits",
            ),
            answer_index=1,
            explanation=(
                "It is a design note rather than a restriction, and framing it that way is more "
                "honest and more persuasive."
            ),
        ),
        TestQuestion(
            prompt=(
                "A prospect asks about bulk file delivery and webhooks. What have they told you?"
            ),
            options=(
                "That they have a large engineering team",
                "Which side of the distribution/redistribution boundary they are on, because\n"
                " Enterprise is the only tier under which redistribution is licensed",
                "That they want the free tier",
                "That they need the Transaction API",
            ),
            answer_index=1,
            explanation=(
                "They have qualified themselves before you asked. That is worth noticing rather "
                "than answering as a delivery question."
            ),
        ),
        TestQuestion(
            prompt="How should the public pricing anchors be quoted?",
            options=(
                "As fixed prices",
                "As approximate published figures — free to roughly 500k a month, Brand API from\n"
                " around $99 with roughly $0.10 overage, Enterprise a custom quote",
                "Not at all",
                "Only the Enterprise tier",
            ),
            answer_index=1,
            explanation=(
                "They are a vendor's published numbers and those move. Approximate and attributed "
                "is both accurate and enough to have a real conversation."
            ),
        ),
    ),
)


def section_3() -> CourseModule:
    """Section 3: the four surfaces, and why the free demo is not the sale."""
    return CourseModule(
        id=_id("module", "the-four-surfaces"),
        title="The four surfaces, and the order you meet them",
        order=2,
        lessons=(
            Lesson(
                id=_id("lesson", "the-four-surfaces"),
                title="Logo Link to Enterprise, in order",
                body=_S3_BODY,
                order=0,
                slides=_SECTION_3_SLIDES,
                drill_topics=("product:brandfetch:surfaces",),
                measurement=(
                    "You can run the sixty-second demo and follow it immediately with an expand "
                    "sentence, and you can place any surface on the pricing ladder from memory."
                ),
            ),
        ),
        section_test=SECTION_3_TEST,
    )


# --- Section 4 — The identifier hook --------------------------------------------------------

_S4_BODY = (
    "One section for one fact, because this is the fact that makes Brandfetch worth paying for "
    "rather than a nice-to-have. The Brand API does not only take a domain. It takes a stock "
    "ticker, an ISIN, an ETF ticker and a crypto symbol — which are exactly the keys a financial "
    "platform's records are already held by. By the end of this lesson you can explain why that "
    "single design choice is the difference between an integration and a data-mapping project."
)

_SECTION_4_SLIDES: tuple[Slide, ...] = (
    _s(
        0,
        SlideKind.CONCEPT,
        "Four keys, one endpoint",
        "Send a **domain**, a **stock ticker**, an **ISIN**, an **ETF ticker** or a **crypto "
        "symbol**, and get the same shape of brand identity back. `/v2/brands/ticker/NKE`. "
        "`/v2/brands/isin/US6541061031`. That is the whole hook, and it is one line of a URL.",
        refs=(DOCS_BRAND_API,),
        asset=_diagram(
            "the_ticker_hook",
            "Four different keys, one endpoint, one shape of answer. A generic logo API takes "
            "only the first.",
            "Four input cards on the left: a domain (nike.com), a stock ticker (NKE), an ISIN "
            "(US6541061031) and a crypto symbol (BTC). Each has an arrow pointing right into "
            "a single dark green panel: one brand identity, holding the logo in every "
            "variant, colours and fonts, and firmographics. A line beneath reads: a generic "
            "logo API takes a domain, and that is the wrong key for a holdings table.",
        ),
    ),
    _s(
        1,
        SlideKind.CONCEPT,
        "Why a domain is the wrong key",
        "A brokerage's holdings table has tickers. A custody file has ISINs. A research screen has "
        "both. None of them has a domain. So a generic logo API forces the client to build and "
        "maintain a mapping from their identifiers to company websites — for their entire "
        "universe, forever, including corporate actions and renames.",
    ),
    _s(
        2,
        SlideKind.CONCEPT,
        "What that mapping actually costs them",
        "It is not a lookup table you write once. Companies rename, get acquired, change domain, "
        "list in a second venue. A mapping is a dataset somebody has to own, and owning it is a "
        "job nobody at a mid-size platform wants. Brandfetch taking the identifier directly "
        "removes that job rather than shrinking it.",
    ),
    _s(
        3,
        SlideKind.CONCEPT,
        "Which is why this is the sentence that sells",
        '"Your holdings are keyed by ticker and ISIN. This takes ticker and ISIN." Two clauses. '
        "It lands with an engineer immediately because they have already thought about the mapping "
        "problem, and it lands with a product owner because it turns a project into an "
        "integration.",
        refs=(DOCS_BRAND_API,),
    ),
    _s(
        4,
        SlideKind.CONCEPT,
        "ISIN is the one that matters outside the US",
        "A US-only platform can get a long way on tickers. A European or global platform runs on "
        "ISINs, and ISIN lookup is the thing that makes this usable for them at all. If your "
        "target is not US-first, lead with ISIN rather than with ticker — it is the same fact, "
        "aimed correctly.",
        refs=(DOCS_BRAND_API,),
    ),
    _s(
        5,
        SlideKind.CONCEPT,
        "ETF tickers, and why they are their own case",
        "An ETF is not a company, and a naive logo service either misses it or returns the wrong "
        "entity. Getting the fund's own identity back matters for any platform whose users hold "
        "funds — which is most wealth platforms, and almost every robo-adviser.",
        refs=(DOCS_BRAND_API,),
    ),
    _s(
        6,
        SlideKind.CONCEPT,
        "Crypto symbols, mentioned without over-claiming",
        "Crypto symbols work as a lookup key too. Useful for a platform with a crypto tab, and "
        "worth one sentence rather than a pitch: the coverage question there is more open than for "
        "listed equities, so it is a thing to test in a demo rather than assert in a meeting.",
        refs=(DOCS_BRAND_API,),
    ),
    _s(
        7,
        SlideKind.CONCEPT,
        "Logo Link takes the identifiers too",
        "The free image URL is not domain-only — it accepts ticker and ISIN as well. So the "
        "sixty-second demo can be done on the client's own identifiers, which makes it "
        "dramatically more convincing than a demo on `nike.com`. Use their tickers, not the "
        "vendor's example.",
        refs=(DOCS_LOGO_LINK,),
    ),
    _s(
        8,
        SlideKind.CONCEPT,
        "What comes back, beyond the mark",
        "Logos in multiple variants and formats — light, dark, icon, wordmark — which matters "
        "because a platform has a dark mode and a favicon slot and a print stylesheet. Plus the "
        "colour palette, which lets a card theme itself to the issuer. That is the part a client "
        "does not anticipate and immediately wants.",
        refs=(DOCS_BRAND_API,),
    ),
    _s(
        9,
        SlideKind.CONCEPT,
        "Firmographics, and the second use case they unlock",
        "Employee count, founding year, headquarters, industry, social links. Individually "
        "unremarkable; collectively they turn a logo integration into an enrichment one, which is "
        "a different budget line. A screener or a company profile page needs these, and the client "
        "may be buying them elsewhere already.",
        refs=(DOCS_BRAND_API,),
    ),
    _s(
        10,
        SlideKind.WALKTHROUGH,
        "Look up one of your prospect's own holdings",
        "Take a real ticker from a real target's platform and hit Logo Link with it. Then find the "
        "equivalent Brand API path in the reference. You now have a demo built on their universe "
        "rather than on a vendor example, which takes the same sixty seconds and is a completely "
        "different conversation.",
        refs=(DOCS_LOGO_LINK, DOCS_BRAND_API),
    ),
    _s(
        11,
        SlideKind.WALKTHROUGH,
        "Try one that will fail",
        "Now try a small-cap or a non-US listing you expect to be thin. Find where coverage runs "
        "out. Knowing your own product's edges is what lets you answer a coverage question with a "
        "number instead of a hope, and a client will trust the whole pitch more for it.",
        refs=(REGISTRY,),
    ),
    _s(
        12,
        SlideKind.WALKTHROUGH,
        "Write the two-clause sentence",
        'Write it for one specific prospect, using their actual identifier type. "Your positions '
        'are keyed by ISIN; this resolves ISIN directly." Say it out loud. If it takes more than '
        "two clauses you have added something that is not the hook.",
    ),
    _s(
        13,
        SlideKind.WALKTHROUGH,
        "Find out what they use today",
        "Ask a target how company logos get onto their screens now. The answers are usually: "
        "nothing, a hand-curated folder, or a scraper somebody built. Each has a different "
        "follow-up and all three are openings. The hand-curated folder is the best one — somebody "
        "is already paying for this in salary.",
    ),
    _s(
        14,
        SlideKind.EXAMPLE,
        "The pitch that lands with an engineer",
        '"You will not need to maintain a ticker-to-domain map. It takes the ticker." That is '
        "the whole thing. An engineer has either already built that map and resents it, or has "
        "scoped it and deferred it. Either way you have just removed the reason the project "
        "stalled.",
    ),
    _s(
        15,
        SlideKind.EXAMPLE,
        "The pitch that lands with a product owner",
        "\"Every holding gets its issuer's mark and colour, from the identifier you already store. "
        'No new data for your team to own." Product owners buy the absence of work more reliably '
        "than they buy features, and this genuinely is an absence of work.",
    ),
    _s(
        16,
        SlideKind.EXAMPLE,
        "A demo that misses the point",
        "An advisor demos `cdn.brandfetch.io/nike.com` to a European wealth platform. It works, "
        "and it demonstrates the one key that platform does not use. The prospect's honest "
        'reaction is "our positions are ISINs" — which the product handles, and which the demo '
        "just failed to show.",
    ),
    _s(
        17,
        SlideKind.CONCEPT,
        "How this connects to the boundary",
        "It does not change it. Identifier lookup is a capability of the Brand API and it is "
        "available on both sides of the distribution line. A venue redistributing brand identity "
        "on a reference record cares about ISIN lookup for exactly the same reason a brokerage "
        "does — so this section serves both segments.",
    ),
    _s(
        18,
        SlideKind.CONCEPT,
        "What not to claim about coverage",
        "Do not claim complete coverage of any identifier type. The published index figure is "
        'large and the long tail is thinner than it implies. "Test your own universe in the demo" '
        "is a better answer than any number, and it is an answer that survives the pilot.",
        refs=(SITE,),
    ),
    _s(
        19,
        SlideKind.CONCEPT,
        "Why one section for one fact",
        "Because this is the fact that moves the product from cosmetic to structural. Everything "
        "else Brandfetch does, something else also does. Taking a ticker or an ISIN as the lookup "
        "key is the thing a generic logo service cannot match, and it is the reason a financial "
        "platform pays rather than improvising.",
        refs=(DOCS_BRAND_API,),
    ),
    _s(
        20,
        SlideKind.CONCEPT,
        "The one-line version to memorise",
        '"It resolves brand identity from the identifiers you already have — ticker, ISIN, ETF, '
        'crypto — not from a domain you would have to map." If you can only remember one sentence '
        "from this entire course besides the boundary question, remember that one.",
    ),
    _s(
        21,
        SlideKind.CHECKPOINT,
        "Name the four keys, then the two-clause pitch",
        "From memory: the four identifier types, and then your two-clause sentence for a specific "
        "prospect using their identifier type. Say both aloud. The four keys are the fact; the two "
        "clauses are the thing you actually use.",
        checkpoint="Name all four identifier types and say your two-clause pitch aloud.",
    ),
    _s(
        22,
        SlideKind.CHECKPOINT,
        "Rebuild your demo on their identifiers",
        "Go back to the sixty-second demo from section 3 and redo it using a real identifier from "
        "a real target — their ticker or their ISIN, not nike.com. Time it again. This is the "
        "version you will actually give.",
        checkpoint="Redo the sixty-second demo using a live target's own ticker or ISIN.",
    ),
    _s(
        23,
        SlideKind.CONCEPT,
        "Where this goes next",
        "Sections 5 and 6 take the two sides of section 2's boundary and turn each into a segment "
        "you can walk into: what they already have, what is wrong with it, what you show them, and "
        "what has to have happened for them to buy this quarter.",
    ),
)

SECTION_4_TEST = SectionTest(
    pass_mark=0.8,
    questions=(
        TestQuestion(
            prompt="Why is a domain the wrong lookup key for a financial platform?",
            options=(
                "Domains change too often",
                "Their records are keyed by ticker and ISIN, so a domain-only API forces them to\n"
                " build and forever maintain an identifier-to-domain mapping",
                "Domains are not unique per company",
                "It is slower to resolve",
            ),
            answer_index=1,
            explanation=(
                "That mapping is a dataset somebody has to own, through renames, acquisitions and "
                "second listings. Taking the identifier directly removes the job rather than "
                "shrinking it."
            ),
        ),
        TestQuestion(
            prompt="Which identifier should you lead with for a European platform?",
            options=(
                "The stock ticker",
                "ISIN, because a non-US-first platform runs on ISINs and that is what makes the\n"
                " product usable for them at all",
                "The domain, as the most universal",
                "The ETF ticker",
            ),
            answer_index=1,
            explanation=(
                "Same fact, aimed correctly. Demoing on nike.com to a European wealth platform "
                "shows the one key they do not use."
            ),
        ),
        TestQuestion(
            prompt="What is the pitch that lands with an engineer?",
            options=(
                "It has 50 million companies indexed",
                "You will not need to maintain a ticker-to-domain map — it takes the ticker",
                "It is free up to 500k requests a month",
                "The assets are verified by the brand owners",
            ),
            answer_index=1,
            explanation=(
                "They have either built that map and resent it, or scoped it and deferred it. "
                "Either way you have removed the reason the project stalled."
            ),
        ),
        TestQuestion(
            prompt="Beyond the logo itself, what does the Brand API return that clients want?",
            options=(
                "Real-time share prices",
                "Multiple logo variants for dark mode and favicons, the colour palette so cards\n"
                " can theme to the issuer, and firmographics",
                "Legal entity hierarchies and LEIs",
                "Sanctions screening data",
            ),
            answer_index=1,
            explanation=(
                "The palette is the part clients do not anticipate and immediately want; the "
                "firmographics turn a logo integration into an enrichment one, which is a "
                "different budget line."
            ),
        ),
        TestQuestion(
            prompt="How should you answer a coverage question?",
            options=(
                "Quote the published index figure",
                "Invite them to test their own universe in the demo, because the long tail is\n"
                " thinner than the headline figure implies",
                "Guarantee complete coverage of listed equities",
                "Decline to answer",
            ),
            answer_index=1,
            explanation=(
                "An answer that survives the pilot is worth more than a number that does not. "
                "Knowing where your own coverage thins makes the whole pitch more credible."
            ),
        ),
        TestQuestion(
            prompt=(
                "Does identifier lookup change which side of the licensing boundary a deal is on?"
            ),
            options=(
                "Yes, ISIN lookup is Enterprise only",
                "No — it is a Brand API capability available on both sides, so this fact serves\n"
                " both segments equally",
                "Yes, ticker lookup implies redistribution",
                "Only for crypto symbols",
            ),
            answer_index=1,
            explanation=(
                "A venue redistributing brand identity on a reference record wants ISIN lookup for "
                "exactly the same reason a brokerage does."
            ),
        ),
    ),
)


def section_4() -> CourseModule:
    """Section 4: the identifier hook, the one fact that makes this structural."""
    return CourseModule(
        id=_id("module", "the-identifier-hook"),
        title="The identifier hook: ticker, ISIN, ETF, crypto",
        order=3,
        lessons=(
            Lesson(
                id=_id("lesson", "the-identifier-hook"),
                title="One line of a URL, and why it sells",
                body=_S4_BODY,
                order=0,
                slides=_SECTION_4_SLIDES,
                drill_topics=("product:brandfetch:identifiers",),
                measurement=(
                    "You can name all four identifier types and give the two-clause pitch using a "
                    "real target's own identifier type, without notes."
                ),
            ),
        ),
        section_test=SECTION_4_TEST,
    )


# --- Section 5 — Distribution: the retail brokerage -----------------------------------------

_S5_BODY = (
    "The left-hand side of the boundary, and the majority of what you will sell. A retail "
    "brokerage or wealth platform wants its own product to look right to its own users. By the end "
    "of this lesson you can walk into that meeting knowing which four screens to ask about, what "
    "the demo is, and what has to have happened inside the firm for them to buy this quarter."
)

_SECTION_5_SLIDES: tuple[Slide, ...] = (
    _s(
        0,
        SlideKind.CONCEPT,
        "The motive: your app, on-brand",
        "Six words, and they are the whole segment. A retail brokerage is not buying brand data as "
        "data. It is buying the fact that its own screens stop looking like a spreadsheet. That is "
        "a front-end and content-consistency problem, and the assessment surfaces it under exactly "
        "those headings.",
    ),
    _s(
        1,
        SlideKind.CONCEPT,
        "The same holdings table",
        "The clearest demonstration in the product. A list of tickers is a wall of symbols a user "
        "scans slowly and recognises poorly. The same list with each issuer's mark beside it is "
        "scannable at a glance. Nothing else on the screen changes, which is what makes it an easy "
        "yes.",
        refs=(DOCS_LOGO_LINK,),
        asset=_diagram(
            "holdings_before_after",
            "The same holdings table, unbranded and branded. This is the whole retail demo.",
            "Two panels showing the same three holdings, NKE, MSFT and VOD.L. On the left, without "
            "the product: just the ticker symbols, described as a wall of symbols. On the right, "
            "outlined in green, the same tickers each preceded by a brand mark, described as "
            "scannable in one look. A line beneath reads: one image URL keyed on the ticker, and "
            "this is the whole retail demo.",
        ),
    ),
    _s(
        2,
        SlideKind.CONCEPT,
        "The four screens to ask about",
        "Holdings and watchlists. Search and instrument lookup. Order tickets and confirmations. "
        "Research and company profile pages. Every retail platform has all four, every one of them "
        "shows companies, and most of them show companies as text. Ask about each by name.",
    ),
    _s(
        3,
        SlideKind.CONCEPT,
        "Onboarding, which is the highest-value one",
        "Corporate onboarding means typing a company name into a bare form: errors, drop-off, no "
        "visual confirmation. Brand Search turns it into a picker with logos, and the Brand API "
        "pre-fills domain, headquarters and industry on selection. Brandfetch cites Typeform "
        "reporting a 5% free-to-paid lift after adding it to onboarding.",
        refs=(DOCS_SEARCH, SITE),
    ),
    _s(
        4,
        SlideKind.CONCEPT,
        "Why onboarding beats the holdings screen commercially",
        "The holdings screen is a polish argument. Onboarding is a conversion argument, and "
        "conversion has an owner with a number. If you can find the person who owns activation or "
        "funded-account rate, you have found a budget that the front-end tidy-up does not have "
        "access to.",
        refs=(DOCS_SEARCH,),
    ),
    _s(
        5,
        SlideKind.CONCEPT,
        "The palette, and the thing they did not expect",
        "The Brand API returns each company's colour palette, not just its mark. So a holding card "
        "can theme itself to the issuer. Clients consistently do not anticipate this and "
        "consistently want it once shown — it is the single best moment in a retail demo, and it "
        "comes free with the paid tier they were already considering.",
        refs=(DOCS_BRAND_API,),
    ),
    _s(
        6,
        SlideKind.CONCEPT,
        "Dark mode, favicons and print",
        "Logos come in multiple variants and formats. That matters more than it sounds: a platform "
        "with a dark theme needs a light mark, a tab needs an icon, a statement PDF needs "
        "something that prints. A single-format logo source creates three follow-on problems, and "
        "this one does not.",
        refs=(DOCS_BRAND_API,),
    ),
    _s(
        7,
        SlideKind.CONCEPT,
        "Where the assessment surfaces this",
        "In the fit map, distribution is scoped to the retail profile and targeted at "
        "content-management and front-end coverage, with the Branding power alongside. So it "
        "appears as the fix for exactly the gaps that cheapen a retail interface — which means the "
        "sell panel has already made the argument before you open your mouth.",
    ),
    _s(
        8,
        SlideKind.CONCEPT,
        "What triggers a retail brokerage",
        "A redesign of the stock detail page or the app. Somebody newly owning an activation or "
        "retention number. A competitor shipping something visibly better. An expansion into "
        "international listings, where the identifier problem gets worse. Or a design system "
        "project, which is the cleanest trigger of all.",
    ),
    _s(
        9,
        SlideKind.CONCEPT,
        "Why a design system project is the best trigger",
        "Because somebody has already decided the interface matters and has budget to prove it. "
        "Brand assets are a component in every design system and almost nobody has a source for "
        "them. Walking in mid-project means you are answering a question the team has already "
        "asked itself.",
    ),
    _s(
        10,
        SlideKind.CONCEPT,
        "The volume conversation, honestly",
        "Many retail platforms fit inside the free tier for the image URL alone. Say so. The paid "
        "conversation is about the enrichment fields and the identifier lookup, not about request "
        "volume, and pretending otherwise gets you caught by an engineer with a calculator in week "
        "two.",
        refs=(PRICING,),
    ),
    _s(
        11,
        SlideKind.WALKTHROUGH,
        "Open a real retail app and count",
        "Take a brokerage app you can actually open and count the places a company appears as text "
        "with no mark. Do it screen by screen. You will typically find four to six. That count is "
        "your opening, and it is specific to them, which is what makes it land.",
    ),
    _s(
        12,
        SlideKind.WALKTHROUGH,
        "Build the before-and-after on their names",
        "Take three tickers from that app and build the two-column comparison — bare tickers on "
        "one side, Logo Link URLs on the other. You now have the diagram from this section "
        "rendered with their own holdings, which takes five minutes and is worth more than any "
        "slide.",
        refs=(DOCS_LOGO_LINK,),
    ),
    _s(
        13,
        SlideKind.WALKTHROUGH,
        "Find who owns conversion there",
        "Work out who at that firm owns activation, onboarding completion or funded-account rate. "
        "That person is a different buyer from whoever owns the front end, and the onboarding "
        "pitch is aimed at them. Two buyers, two pitches, one product.",
    ),
    _s(
        14,
        SlideKind.WALKTHROUGH,
        "Check the sell panel for a retail assessment",
        "Open a finalised retail-brokerage assessment and look at what the sell panel offers for "
        "Brandfetch. You should see the distribution variant only. Read its stanza — it is written "
        "for this segment's motive, and it is a better first sentence than one you would "
        "improvise.",
    ),
    _s(
        15,
        SlideKind.EXAMPLE,
        "A first meeting that works",
        '"I counted five places in your app where a company is just text — holdings, watchlist, '
        "search, the order ticket and the research tab. Here are three of your own tickers "
        "rendering as marks, from one URL. And separately: who owns your onboarding completion "
        'rate?" Specific, demonstrated, and it opens a second budget.',
    ),
    _s(
        16,
        SlideKind.EXAMPLE,
        "The objection you will get, and the answer",
        '"We could do this ourselves with a scraper." "You could, and then you own it — through '
        "every rebrand, every acquisition, every new listing. The registry is maintained by the "
        'brand owners, so the version you get is the version they publish." A maintenance '
        "argument, not a quality one.",
        refs=(REGISTRY,),
    ),
    _s(
        17,
        SlideKind.EXAMPLE,
        "The objection that is harder",
        '"Our users don\'t care what it looks like." Sometimes true. Move to the conversion '
        "argument: onboarding drop-off is measurable in a way aesthetics are not. If they have no "
        "conversion problem either, this may genuinely not be their quarter — and saying so keeps "
        "the relationship.",
    ),
    _s(
        18,
        SlideKind.CONCEPT,
        "What to be careful about in this segment",
        "A retail brokerage showing competitor marks on a comparison screen is using registered "
        "marks in a regulated context, and the obligations are theirs. Raise it. This segment is "
        "where the ownership disclosure from section 1 most often actually matters, because "
        "comparison screens are common here.",
        refs=(TERMS,),
    ),
    _s(
        19,
        SlideKind.CONCEPT,
        "Stay on the left of the boundary",
        "Everything in this section is display inside their own product. If the conversation turns "
        "to a white-labelled portal for partner firms, or an exported file, or a PDF the client "
        "sends onward, you have crossed into section 6's territory and the licence changes. Notice "
        "the turn when it happens.",
        refs=(TERMS,),
    ),
    _s(
        20,
        SlideKind.CONCEPT,
        "What a good pilot looks like here",
        "One screen, one metric, one date. The holdings table with marks, and either a qualitative "
        "read from user testing or the onboarding completion number. Not four screens at once — a "
        "broad pilot produces an inconclusive result and a stalled renewal.",
    ),
    _s(
        21,
        SlideKind.CHECKPOINT,
        "Count the screens, out loud",
        "From memory: the four screens every retail platform has where a company shows as text, "
        "plus the fifth surface that is a conversion argument rather than a polish one. Then say "
        "which of those you would lead with and why.",
        checkpoint=(
            "Name the four screens plus onboarding from memory, and say which you would lead with."
        ),
    ),
    _s(
        22,
        SlideKind.CHECKPOINT,
        "Give the retail opening on a real target",
        "Say your opening aloud for a specific retail brokerage: your screen count, your "
        "before-and-after, and your conversion question. Three moves. If you have not opened their "
        "app to get the count, the opening is generic and will sound it.",
        checkpoint="Say the three-move retail opening aloud for a named real target.",
    ),
    _s(
        23,
        SlideKind.CONCEPT,
        "Where this goes next",
        "Section 6 is the other side of the boundary: the exchange or information vendor, whose "
        "motive is not their own interface at all. Same data, completely different sale, and a "
        "licence that has to be negotiated rather than signed up for.",
    ),
)

SECTION_5_TEST = SectionTest(
    pass_mark=0.8,
    questions=(
        TestQuestion(
            prompt="What is the retail brokerage's motive, in six words?",
            options=(
                "License brand data to serve customers",
                "Your app, on-brand",
                "Reduce data vendor spend",
                "Enrich the reference master",
            ),
            answer_index=1,
            explanation=(
                "They are not buying brand data as data. They are buying the fact that their own "
                "screens stop looking like a spreadsheet."
            ),
        ),
        TestQuestion(
            prompt="Why does the onboarding pitch beat the holdings-screen pitch commercially?",
            options=(
                "It needs fewer API calls",
                "Holdings is a polish argument; onboarding is a conversion argument, and\n"
                " conversion has an owner with a number and a budget",
                "It is covered by the free tier",
                "It avoids the trademark question",
            ),
            answer_index=1,
            explanation=(
                "Two buyers, two pitches, one product. Find whoever owns activation or "
                "funded-account rate and you have found a budget the front-end tidy-up cannot "
                "reach."
            ),
        ),
        TestQuestion(
            prompt="What is the best moment in a retail demo, and why is it unexpected?",
            options=(
                "The 50-million-company index",
                "The colour palette: cards can theme to the issuer, and clients consistently do\n"
                " not anticipate it but want it once shown",
                "The 99.9% availability commitment",
                "The free tier limit",
            ),
            answer_index=1,
            explanation=(
                "It comes free with the paid tier they were already considering, which makes it "
                "the cheapest persuasion available in this segment."
            ),
        ),
        TestQuestion(
            prompt='"We could do this ourselves with a scraper." What is the answer?',
            options=(
                "Scraping is illegal",
                "You could, and then you own it through every rebrand, acquisition and new\n"
                " listing — the registry is maintained by the brand owners",
                "Our assets are higher resolution",
                "It would cost more in engineering time",
            ),
            answer_index=1,
            explanation=(
                "A maintenance argument, not a quality one. The version you get is the version the "
                "brand owner publishes."
            ),
        ),
        TestQuestion(
            prompt="Which turn in the conversation means you have crossed the licensing boundary?",
            options=(
                "They ask about dark mode variants",
                "A white-labelled portal for partner firms, an exported file, or a PDF the\n"
                " client sends onward",
                "They ask about ISIN lookup",
                "They ask about the colour palette",
            ),
            answer_index=1,
            explanation=(
                "All three involve the data reaching someone outside their own product, which is "
                "section 6's territory and a different licence."
            ),
        ),
        TestQuestion(
            prompt="What does a good pilot look like in this segment?",
            options=(
                "Four screens at once, to prove breadth",
                "One screen, one metric they already care about, and a date",
                "A full design-system integration",
                "Whatever their engineers propose",
            ),
            answer_index=1,
            explanation=(
                "A broad pilot produces an inconclusive result and a stalled renewal. A narrow one "
                "either works or does not, and both are useful."
            ),
        ),
    ),
)


def section_5() -> CourseModule:
    """Section 5: distribution, and the retail brokerage that buys it."""
    return CourseModule(
        id=_id("module", "distribution-retail"),
        title="Distribution: the retail brokerage",
        order=4,
        lessons=(
            Lesson(
                id=_id("lesson", "distribution-retail"),
                title="Your app, on-brand",
                body=_S5_BODY,
                order=0,
                slides=_SECTION_5_SLIDES,
                drill_topics=("product:brandfetch:distribution",),
                measurement=(
                    "You can count the surfaces in a real retail app, build the before-and-after "
                    "on their own tickers, and name who owns the conversion number."
                ),
            ),
        ),
        section_test=SECTION_5_TEST,
    )


# --- Section 6 — Redistribution: the exchange and information vendor ------------------------

_S6_BODY = (
    "The right-hand side of the boundary. An exchange or information vendor is not buying a nicer "
    "interface — it is buying a field to add to data it already licenses onward. Same brand data, "
    "completely different sale: a longer path, a negotiated licence, a lower rate over a longer "
    "window, and a buyer who thinks in reference-data terms rather than in screens."
)

_SECTION_6_SLIDES: tuple[Slide, ...] = (
    _s(
        0,
        SlideKind.CONCEPT,
        "The motive: license brand data to serve your customers",
        "This segment already redistributes data for a living. An exchange ships instrument "
        "reference files. An information vendor ships enriched records. Brand identity is one more "
        "field on something they already send out, which is why the pitch needs almost no "
        "explaining once framed that way.",
    ),
    _s(
        1,
        SlideKind.CONCEPT,
        "One more field on a record they already ship",
        "Their reference record already carries ISIN, legal name, SEDOL, MIC, currency. Adding "
        "brand identity to it is a product extension rather than a new capability. And because the "
        "record leaves their building, the licence has to be different — the arrow off the edge of "
        "their boundary *is* the licence question.",
        refs=(TERMS,),
        asset=_diagram(
            "reference_data_shelf",
            "Brand identity as one more field on a record the venue already redistributes.",
            "A card labelled their reference record, holding ISIN, legal name, and SEDOL, MIC and "
            "currency, with a fourth row highlighted in dark green: brand identity. An arrow "
            "leaves the card and points to a second panel, their customers, noting that the data "
            "leaves their building. A warning beneath reads: that arrow is the licence question, "
            "and it is why this tier exists.",
        ),
    ),
    _s(
        2,
        SlideKind.CONCEPT,
        "Why they want it at all",
        "Because their customers are platforms with the retail problem from section 5. A venue "
        "that can ship brand identity alongside its reference data saves every downstream platform "
        "from sourcing it separately — which makes the venue's own feed more valuable. You are "
        "selling them an upgrade to their product, not a fix to their interface.",
    ),
    _s(
        3,
        SlideKind.CONCEPT,
        "The identifier hook matters more here, not less",
        "A venue's records are ISINs and MICs. If brand identity could only be resolved by domain, "
        "the venue would have to build the mapping for its entire listed universe before it could "
        "ship anything. ISIN lookup is what makes this a field they can add rather than a project "
        "they have to fund.",
        refs=(DOCS_BRAND_API,),
    ),
    _s(
        4,
        SlideKind.CONCEPT,
        "The delivery mechanics are different too",
        "Enterprise adds bulk file transfer and webhooks, which is what a venue actually needs — "
        "it is not making per-instrument API calls at render time, it is building a file. If a "
        "conversation is about flat files and delivery windows, you are in this segment whether "
        "anyone has said so.",
        refs=(PRICING,),
    ),
    _s(
        5,
        SlideKind.CONCEPT,
        "There is no self-serve path here",
        "Redistribution rights are bespoke Enterprise contracting. There is no public reseller "
        "programme to point at and no signup page that grants these rights. Say that early: a "
        "commercially minded buyer will assume a programme exists, and letting them assume it "
        "wastes everyone's time.",
        refs=(PRICING, TERMS),
    ),
    _s(
        6,
        SlideKind.CONCEPT,
        "Which changes what you are actually doing",
        "In section 5 you were driving an adoption you could influence. Here you are originating "
        "and qualifying a deal that somebody else will contract. Your job is to find the "
        "opportunity, frame it correctly, and hand it over cleanly — not to negotiate terms you "
        "have no authority over.",
    ),
    _s(
        7,
        SlideKind.CONCEPT,
        "And why the rate is lower",
        "Because the motion is not yours to drive. The commission on this tier is lower than on "
        "distribution and runs over a different window, and that is a rational split rather than a "
        "slight. Read both off the Earnings page before you forecast — the windows differ as much "
        "as the rates do.",
    ),
    _s(
        8,
        SlideKind.CONCEPT,
        "The information-vendor case, and a scoping caveat",
        "Data vendors, research platforms and analytics providers have the same motive as a venue: "
        "enrich records they redistribute. In the fit map the redistribution variant is currently "
        "scoped to the exchange profile only, because no information-vendor profile key exists in "
        "the registry yet. When one is added it joins that list.",
    ),
    _s(
        9,
        SlideKind.CONCEPT,
        "What that means practically today",
        "If you are working an information vendor, the fit map will not surface this variant for "
        "you from an assessment — the segment exists commercially but not yet as a profile. "
        "Qualify it by hand, and know that the sell panel's silence is a registry gap rather than "
        "a judgement about the fit.",
    ),
    _s(
        10,
        SlideKind.CONCEPT,
        "What triggers a venue or vendor",
        "A reference-data product refresh. A competitor venue shipping richer records. A push into "
        "retail-facing or API-first distribution, where their customers are consumer platforms. Or "
        "a client of theirs asking for exactly this, which is the strongest trigger there is "
        "because the demand is already documented.",
    ),
    _s(
        11,
        SlideKind.WALKTHROUGH,
        "Read a real reference-data specification",
        "Find a published instrument reference file spec from any venue and read its field list. "
        "Note how it is organised, how fields get added between versions, and that nothing in it "
        "is visual. That absence is the opportunity, and reading one spec makes you credible in "
        "this conversation in a way no summary will.",
    ),
    _s(
        12,
        SlideKind.WALKTHROUGH,
        "Write the one-sentence framing",
        'Write it in their language rather than ours. "Brand identity as a field on your '
        'instrument reference record, resolved by ISIN, delivered as a file." Three clauses, all '
        "in reference-data terms, none of them about interfaces. That sentence is the section's "
        "deliverable.",
        refs=(DOCS_BRAND_API,),
    ),
    _s(
        13,
        SlideKind.WALKTHROUGH,
        "Identify who to talk to",
        "Not the design team. You want whoever owns the market-data or reference-data product line "
        "— the person with a roadmap for what the feed contains. Find that title at one real venue "
        "and write it down, because it is a different person from every buyer in section 5.",
    ),
    _s(
        14,
        SlideKind.WALKTHROUGH,
        "Rehearse the hand-over",
        'Practise saying where your part ends: "This needs Enterprise licensing because the data '
        "goes to your customers. I will bring in the licensing conversation rather than guess at "
        'terms." Saying that confidently is a strength; improvising terms you cannot commit to is '
        "the failure mode here.",
        refs=(TERMS,),
    ),
    _s(
        15,
        SlideKind.EXAMPLE,
        "A framing that works",
        '"Your reference file has ISIN, name, SEDOL, MIC. It has nothing visual, so every '
        "downstream platform sources logos separately and inconsistently. Brand identity resolved "
        'by ISIN, delivered in your file, makes your feed the place they get it." Their product, '
        "their customers, their language.",
    ),
    _s(
        16,
        SlideKind.EXAMPLE,
        "A framing that fails",
        '"It will make your website look much better." A venue\'s website is not the product and '
        "nobody there is measured on it. You have pitched section 5's motive to section 6's buyer, "
        "which is precisely the conflation the founder corrected — and it reads as not "
        "understanding their business.",
    ),
    _s(
        17,
        SlideKind.EXAMPLE,
        "The objection specific to this segment",
        '"Our customers can just get this themselves." True, and that is the argument: they get '
        "it inconsistently, keyed differently, each maintaining their own mapping. A venue's whole "
        "value is normalising things so its customers do not each solve them badly. This is one "
        "more of those.",
    ),
    _s(
        18,
        SlideKind.CONCEPT,
        "The compliance question is bigger on this side",
        "In section 5 the client displays marks to its own users. Here the client passes marks "
        "onward, so the trademark obligations travel with the data and touch their customers too. "
        "That is a materially larger conversation, and it is a reason the licence is negotiated "
        "rather than clicked through.",
        refs=(TERMS,),
    ),
    _s(
        19,
        SlideKind.CONCEPT,
        "What never to say in this segment",
        "Never suggest the standard tier would cover it. Never propose terms, a delivery mechanism "
        "or a price. Never state what their customers may do with the marks. All four are somebody "
        "else's to answer, and answering them yourself is how a promising deal becomes a "
        "re-papering exercise.",
    ),
    _s(
        20,
        SlideKind.CONCEPT,
        "How to tell the two segments apart in ten seconds",
        "Ask what their product is. If the answer describes screens their users look at, that is "
        "section 5. If it describes data they send to customers, that is section 6. One question, "
        "and you have the segment, the licence, the buyer and the rate.",
    ),
    _s(
        21,
        SlideKind.CHECKPOINT,
        "Say the reference-data framing out loud",
        "Three clauses, in their language: the field, the identifier it resolves by, and the "
        'delivery mechanism. No mention of interfaces. If your sentence contains the word "looks", '
        "you have reverted to section 5 and should rewrite it.",
        checkpoint=(
            "Say the three-clause reference-data framing aloud, with no reference to how anything "
            "looks."
        ),
    ),
    _s(
        22,
        SlideKind.CHECKPOINT,
        "Say where your part ends",
        "Out loud: the sentence in which you name Enterprise licensing and hand the terms "
        "conversation on. Then say the two segments' motives back to back in six words each. If "
        "the two motives blur together, go back to section 2 — that blurring is the whole thing "
        "this course was rebuilt to fix.",
        checkpoint=(
            "Say your hand-over sentence aloud, then both segments' six-word motives back to back."
        ),
    ),
    _s(
        23,
        SlideKind.CONCEPT,
        "Where this goes next",
        "Section 7 is the licensing and trademark detail that sits under both sides — what the "
        "client may and may not do, who carries what, and the four things you never decide. Then "
        "section 8 assembles all of it into a first meeting.",
    ),
)

SECTION_6_TEST = SectionTest(
    pass_mark=0.8,
    questions=(
        TestQuestion(
            prompt="What is the exchange or information vendor's motive?",
            options=(
                "Your app, on-brand",
                "License brand data to serve their customers: one more field on a record they\n"
                " already redistribute",
                "Reduce their own data spend",
                "Improve their website",
            ),
            answer_index=1,
            explanation=(
                "They already redistribute data for a living. Framed as a product extension it "
                "needs almost no explaining; framed as an interface improvement it reads as not "
                "understanding their business."
            ),
        ),
        TestQuestion(
            prompt="Why does ISIN lookup matter MORE for this segment than for retail?",
            options=(
                "Their volumes are higher",
                "Their records are ISINs and MICs, so domain-only resolution would force them to\n"
                " map their entire listed universe before shipping anything",
                "Retail platforms do not use ISINs",
                "It is required by the Enterprise licence",
            ),
            answer_index=1,
            explanation=(
                "It is what makes this a field they can add rather than a project they have to "
                "fund."
            ),
        ),
        TestQuestion(
            prompt=(
                "A conversation turns to flat files and delivery windows. What does that tell you?"
            ),
            options=(
                "They want the free tier",
                "You are in the redistribution segment, whether or not anyone has said so",
                "They need the Transaction API",
                "They have a small engineering team",
            ),
            answer_index=1,
            explanation=(
                "A venue is not making per-instrument API calls at render time, it is building a "
                "file. Bulk transfer and webhooks are Enterprise mechanics."
            ),
        ),
        TestQuestion(
            prompt="Why is the commission lower on this tier?",
            options=(
                "The deals are smaller",
                "The motion is not yours to drive — you originate and qualify, somebody else\n"
                " contracts. A rational split, not a slight",
                "Enterprise clients negotiate harder",
                "The attribution window is shorter",
            ),
            answer_index=1,
            explanation=(
                "And the windows differ as much as the rates do, so read both off the Earnings "
                "page before forecasting either."
            ),
        ),
        TestQuestion(
            prompt=(
                "Why does the fit map not currently surface this variant for an information vendor?"
            ),
            options=(
                "Because information vendors are a poor fit",
                "Because no information-vendor profile key exists in the registry yet, so the\n"
                " variant is scoped to the exchange profile only",
                "Because they buy the distribution variant instead",
                "Because redistribution is retail-scoped",
            ),
            answer_index=1,
            explanation=(
                "The segment exists commercially but not yet as a profile. The sell panel's "
                "silence is a registry gap rather than a judgement about the fit."
            ),
        ),
        TestQuestion(
            prompt="Which question separates the two segments in ten seconds?",
            options=(
                "What is your data budget?",
                "What is your product? Screens their users look at means distribution; data they\n"
                " send to customers means redistribution",
                "Do you have an API?",
                "How many customers do you have?",
            ),
            answer_index=1,
            explanation=(
                "One question gives you the segment, the licence, the buyer and the rate at the "
                "same time."
            ),
        ),
    ),
)


def section_6() -> CourseModule:
    """Section 6: redistribution, and the venue or vendor that buys it."""
    return CourseModule(
        id=_id("module", "redistribution-venue"),
        title="Redistribution: the exchange and information vendor",
        order=5,
        lessons=(
            Lesson(
                id=_id("lesson", "redistribution-venue"),
                title="License brand data to serve your customers",
                body=_S6_BODY,
                order=0,
                slides=_SECTION_6_SLIDES,
                drill_topics=("product:brandfetch:redistribution",),
                measurement=(
                    "You can frame this in reference-data language with no mention of interfaces, "
                    "and you hand the licensing conversation on rather than improvising terms."
                ),
            ),
        ),
        section_test=SECTION_6_TEST,
    )


# --- Section 7 — Licensing, trademark and the lines you do not cross ------------------------

_S7_BODY = (
    "The compliance section, and the one where an advisor can do damage that outlives the deal. "
    "Brandfetch does not own the logos, the boundary between displaying and redistributing is not "
    "publicly drawn, and both of those facts land on your client rather than on the vendor. By the "
    "end of this lesson you know what to disclose, what to get in writing, and the four things you "
    "never decide."
)

_SECTION_7_SLIDES: tuple[Slide, ...] = (
    _s(
        0,
        SlideKind.CONCEPT,
        "Three parties, and the risk is not where they think",
        "The trademark owner owns the mark. Brandfetch provides access to it. **Your client "
        "carries the fair-use risk.** The misconception is about position rather than about "
        "detail: buyers assume paying a vendor for access transfers the vendor's rights, and it "
        "does not, because the vendor never had them.",
        refs=(TERMS,),
        asset=_diagram(
            "who_owns_the_mark",
            "The same diagram as section 1, back where the full detail lives. It is the one "
            "worth seeing twice.",
            "Three boxes in a row connected by arrows. The trademark owner owns the mark. "
            "Brandfetch provides access to it. Your client, filled dark green, carries the "
            "fair-use risk. A warning beneath reads: paying for access does not transfer "
            "anybody's rights. A second line adds: say this before the compliance officer "
            "asks.",
        ),
    ),
    _s(
        1,
        SlideKind.CONCEPT,
        "Why this diagram appears twice",
        "It was in section 1 as a disclosure to make early, and it is here because this is where "
        "the detail underneath it lives. Repeating one drawing in a course is usually padding; "
        "repeating this one is deliberate, because it is the single fact most likely to be "
        "forgotten under pressure and most expensive when it is.",
    ),
    _s(
        2,
        SlideKind.CONCEPT,
        "What the client actually undertakes",
        "That assets are used without implying endorsement, without misrepresentation, without "
        "alteration, and without suggesting an affiliation that does not exist. Four constraints, "
        "and all four are ordinary — a firm displaying any third-party mark is already subject to "
        "them. The point is not that they are onerous, it is that they are the client's.",
        refs=(TERMS,),
    ),
    _s(
        3,
        SlideKind.CONCEPT,
        "Alteration is the one that catches people",
        "A design team will want to recolour a mark to fit a palette, crop it to a circle, or put "
        "it on a coloured tile. Some of that is fine and some of it is alteration. It is worth "
        "naming specifically, because it is the constraint most likely to be broken by someone "
        "with good intentions and a style guide.",
        refs=(TERMS,),
    ),
    _s(
        4,
        SlideKind.CONCEPT,
        "Why a financial firm cares more than most",
        "Because the marks in question are frequently competitors' or counterparties'. A brokerage "
        "putting a rival bank's logo on a comparison screen, or a venue shipping issuer marks to "
        "third parties, is using registered marks in a regulated context. That is a real exposure "
        "rather than a theoretical one.",
    ),
    _s(
        5,
        SlideKind.CONCEPT,
        "The boundary, restated as a licensing fact",
        "The standard licence covers in-product display. It does **not** cover passing brand data "
        "to third parties, white-labelling it, or reselling it. Those need Enterprise custom "
        "licensing. There is no public self-serve reseller programme, so there is no page you can "
        "point at that grants those rights.",
        refs=(TERMS, PRICING),
    ),
    _s(
        6,
        SlideKind.CONCEPT,
        "And the honest part: the line is not drawn publicly",
        "Brandfetch's public terms do not bright-line where display ends and redistribution "
        "begins. That is not evasion on their part — it depends on the use case. It does mean that "
        "any advisor who states the boundary confidently is inventing it, and inventing it is "
        "worse than saying you will confirm.",
        refs=(TERMS,),
    ),
    _s(
        7,
        SlideKind.CONCEPT,
        "The caching rule, as a licence term rather than a design note",
        "Section 3 framed the refresh expectation as a design note, which is how you present it. "
        "As a licence term it also means a client cannot take a bulk copy and keep it indefinitely "
        "— doing so is closer to holding a dataset than to displaying it, which is a different "
        "licence again. Worth knowing in that form.",
        refs=(TERMS,),
    ),
    _s(
        8,
        SlideKind.CONCEPT,
        "The four things you never decide",
        "Where the display-versus-redistribute line falls. What the client may redistribute. "
        "Whether a specific alteration is permitted. What their own customers may do with the "
        "marks. Every one is somebody else's to answer, and every one of them is answerable in "
        "writing if you ask for it.",
    ),
    _s(
        9,
        SlideKind.CONCEPT,
        "What you do instead: three moves",
        "Disclose the ownership position early, unprompted. Name the boundary question when a use "
        "case gets near it. Get the specific answer in writing before anything is signed. Those "
        "three moves cover every compliance situation this product creates, and none of them "
        "requires you to be a lawyer.",
    ),
    _s(
        10,
        SlideKind.CONCEPT,
        "Why disclosing early actually helps you",
        "A compliance officer who hears the ownership position from you treats the rest of your "
        "claims as more reliable. One who finds it themselves in month two treats everything you "
        "said as suspect. The disclosure is thirty seconds and it is the cheapest credibility "
        "available in this product.",
    ),
    _s(
        11,
        SlideKind.WALKTHROUGH,
        "Read the terms properly, once",
        "Read Brandfetch's terms of service end to end. Once, properly, not skimmed. You are "
        "looking for the ownership language, the usage constraints, and what it says and does not "
        "say about third parties. Doing this once means you never have to guess, and guessing is "
        "the only real risk here.",
        refs=(TERMS,),
    ),
    _s(
        12,
        SlideKind.WALKTHROUGH,
        "Write your disclosure sentence",
        "Write the thirty-second version you will actually say, unprompted, in a first meeting. It "
        "must cover who owns the marks, what Brandfetch provides, and where the obligations sit — "
        'without sounding like a warning. "Worth flagging now rather than in legal" is a better '
        'opening than "you should be aware that".',
    ),
    _s(
        13,
        SlideKind.WALKTHROUGH,
        "Write your escalation sentence",
        "Now write the one for a use case near the boundary. It has to name the uncertainty, "
        "propose confirming it, and not undermine your own credibility. Practise it, because the "
        "natural instinct in the moment is to reassure, and reassuring is the wrong move.",
    ),
    _s(
        14,
        SlideKind.WALKTHROUGH,
        "Take one live opportunity through both",
        "Pick a real prospect and write out what you would disclose and what you would escalate "
        "for their specific use case. If nothing needs escalating, say why — that is a valid "
        "answer and arriving at it deliberately is the skill.",
    ),
    _s(
        15,
        SlideKind.EXAMPLE,
        "The disclosure, in the words to use",
        '"One thing worth flagging now rather than in legal: this is access to brand assets, not '
        "ownership of them. The trademark owners own the marks and the usage obligations sit with "
        "you — same as any other mark you display. Your compliance team will want that written "
        'down, and it should be."',
    ),
    _s(
        16,
        SlideKind.EXAMPLE,
        "The escalation, in the words to use",
        '"That one I would not want to answer off the cuff. Sending it on to your clients may '
        "cross from display into redistribution, and those are different licences. Let me get you "
        'a definitive answer for that exact use case rather than guess." Confident, specific, and '
        "it does not pretend.",
    ),
    _s(
        17,
        SlideKind.EXAMPLE,
        "What going wrong sounds like",
        '"You are covered, it is all in the licence." Two problems: the licence probably does '
        "not cover what they just described, and you have given a legal assurance you have no "
        "standing to give. When it unwinds it unwinds as you having told them something untrue, "
        "which outlives the deal.",
    ),
    _s(
        18,
        SlideKind.CONCEPT,
        "Compliance obligations travel with redistribution",
        "On the distribution side the client's obligations are the client's. On the redistribution "
        "side they reach the client's customers too, because the marks arrive in someone else's "
        "system. That is a materially bigger conversation and part of why that licence is "
        "negotiated rather than clicked.",
        refs=(TERMS,),
    ),
    _s(
        19,
        SlideKind.CONCEPT,
        "What Bruntsfield's position is",
        "We resell access. We do not indemnify how marks are used, we do not interpret the "
        "boundary, and we do not vary Brandfetch's terms. Being clear about the limits of what we "
        "are selling is part of selling it well, and it is the difference between a reseller and a "
        "broker of vague assurances.",
    ),
    _s(
        20,
        SlideKind.CONCEPT,
        "The shortest possible summary",
        "You sell access to brand data. You do not sell the marks, and you do not sell indemnity "
        "for how they are used. Disclose it, escalate the unclear cases, and get the specific "
        "answers in writing. That is the entire compliance posture for this product.",
    ),
    _s(
        21,
        SlideKind.CHECKPOINT,
        "Recite the four things you never decide",
        "From memory: all four. Then the three moves you make instead. Seven items, and they are "
        "the content of this section. An advisor who can produce them cold is safe in front of a "
        "regulated client unaccompanied; one who cannot, is not.",
        checkpoint=(
            "Recite the four things you never decide and the three moves you make instead, from "
            "memory."
        ),
    ),
    _s(
        22,
        SlideKind.CHECKPOINT,
        "Say both sentences aloud",
        "The disclosure and the escalation, out loud, in your own words. Then say them again as "
        "though a compliance officer is listening — because eventually one is. If the two versions "
        "differ, the second is the one to learn.",
        checkpoint=(
            "Say your disclosure and escalation sentences aloud, in the compliance-safe version."
        ),
    ),
    _s(
        23,
        SlideKind.CONCEPT,
        "Where this goes next",
        "Section 8 assembles everything: the boundary question, the identifier hook, the right "
        "segment framing, the disclosure, and the order to do them in. One first meeting, run "
        "without notes.",
    ),
)

SECTION_7_TEST = SectionTest(
    pass_mark=0.8,
    questions=(
        TestQuestion(
            prompt="Why does paying Brandfetch not transfer any rights in the marks?",
            options=(
                "Because the licence excludes it explicitly",
                "Because Brandfetch never had those rights — the trademark owners do, and\n"
                " Brandfetch provides access",
                "Because only the Enterprise tier transfers rights",
                "Because trademark rights are non-transferable in general",
            ),
            answer_index=1,
            explanation=(
                "The misconception is about position rather than detail. A vendor cannot pass on "
                "rights it does not hold."
            ),
        ),
        TestQuestion(
            prompt=(
                "Which of the client's four undertakings most often gets broken by good intentions?"
            ),
            options=(
                "Implying endorsement",
                "Alteration — a design team recolouring or cropping a mark to fit a style guide",
                "Misrepresentation",
                "Suggesting false affiliation",
            ),
            answer_index=1,
            explanation=(
                "Worth naming specifically, because it is the constraint most likely to be "
                "broken by someone with a palette and no ill intent."
            ),
        ),
        TestQuestion(
            prompt="What are the four things you never decide?",
            options=(
                "Price, timeline, delivery method, coverage",
                "Where the display/redistribute line falls; what the client may redistribute;\n"
                " whether an alteration is permitted; what their customers may do with the marks",
                "Which segment they are; which tier they need; which API; which identifier",
                "Anything the compliance team asks about",
            ),
            answer_index=1,
            explanation=(
                "All four are somebody else's to answer, and all four are answerable in writing if "
                "you ask for it."
            ),
        ),
        TestQuestion(
            prompt="Why does disclosing the ownership position early help YOU?",
            options=(
                "It is legally required of the reseller",
                "A compliance officer who hears it from you treats your other claims as more\n"
                " reliable; one who finds it themselves treats everything as suspect",
                "It shortens the contract",
                "It transfers the risk to Brandfetch",
            ),
            answer_index=1,
            explanation=(
                "Thirty seconds, and it is the cheapest credibility available in this product."
            ),
        ),
        TestQuestion(
            prompt="A prospect describes sending brand data on to their clients. What do you say?",
            options=(
                "You are covered, it is all in the licence",
                "That it may cross from display into redistribution, that those are different\n"
                " licences, and that you will get a definitive answer for that exact use case",
                "That it requires the Transaction API",
                "That the standard tier permits it with attribution",
            ),
            answer_index=1,
            explanation=(
                "Giving a legal assurance you have no standing to give unwinds as you having told "
                "them something untrue, which outlives the deal."
            ),
        ),
        TestQuestion(
            prompt="How do compliance obligations differ between the two sides of the boundary?",
            options=(
                "They are identical",
                "On distribution they are the client's; on redistribution they reach the client's\n"
                " customers too, because the marks arrive in someone else's system",
                "Redistribution removes them via the Enterprise licence",
                "Distribution carries no obligations",
            ),
            answer_index=1,
            explanation=(
                "That is a materially bigger conversation, and part of why that licence is "
                "negotiated rather than clicked through."
            ),
        ),
    ),
)


def section_7() -> CourseModule:
    """Section 7: licensing, trademark, and the four things you never decide."""
    return CourseModule(
        id=_id("module", "licensing-and-trademark"),
        title="Licensing, trademark and the lines you do not cross",
        order=6,
        lessons=(
            Lesson(
                id=_id("lesson", "licensing-and-trademark"),
                title="What to disclose, and what to get in writing",
                body=_S7_BODY,
                order=0,
                slides=_SECTION_7_SLIDES,
                drill_topics=("product:brandfetch:licensing",),
                measurement=(
                    "You can recite the four things you never decide and the three moves you make "
                    "instead, and deliver both the disclosure and the escalation without hedging."
                ),
            ),
        ),
        section_test=SECTION_7_TEST,
    )


# --- Section 8 — How to sell it -------------------------------------------------------------

_S8_BODY = (
    "The last section, and it assembles the previous seven into something you say out loud. By the "
    "end of it you have a first meeting you can run without notes, the right framing for either "
    "segment, an answer to each objection, and a clear rule about the one thing you must qualify "
    "before you forecast anything."
)

_SECTION_8_SLIDES: tuple[Slide, ...] = (
    _s(
        0,
        SlideKind.CONCEPT,
        "Qualify the licence before you forecast",
        "One question decides the product, the segment, the contract path and your rate: **does "
        "the data leave the client's own product?** No means distribution. Yes means "
        "redistribution. Forecasting before you know the answer means forecasting the wrong "
        "number, because the two tiers pay differently over different windows.",
        asset=_diagram(
            "qualify_before_you_forecast",
            "The commission decision. Qualify first, then read the live rate — never the "
            "other way round.",
            "A decision box asking whether the data leaves the client's own product. A No "
            "branch leads to distribution, the standard paid API. A Yes branch, filled dark "
            "green, leads to redistribution, enterprise licensing. Beneath, in green: "
            "different rate, different window, read yours off the Earnings page. A final line "
            "adds: never from memory and never from a slide, the schedule is the only source.",
        ),
    ),
    _s(
        1,
        SlideKind.CONCEPT,
        "Why no rate appears anywhere in this course",
        "Because a number written into content is a number that goes stale silently and gets "
        "quoted anyway. Both tiers resolve live from the Earnings v7 schedule. Read them there, "
        "every time, including the windows — which differ, and which change which deal is worth "
        "more to you over its life.",
    ),
    _s(
        2,
        SlideKind.CONCEPT,
        "The first meeting, in four moves",
        "One: where does a company appear as just text in your product? Two: which side of the "
        "boundary are you — your screens, or data you send onward? Three: the demo, on their own "
        "identifiers. Four: the disclosure, unprompted. In that order, and the order matters.",
    ),
    _s(
        3,
        SlideKind.CONCEPT,
        "Why move one comes first",
        "Because it makes them describe their own product, and their answer tells you the segment "
        "before you have named a single feature. A brokerage answers with screens. A venue answers "
        "with a file. You have qualified the deal by listening rather than by asking a licensing "
        "question nobody enjoys.",
    ),
    _s(
        4,
        SlideKind.CONCEPT,
        "Why move three is a demo and not a deck",
        "Because the demo is sixty seconds, needs no login, and works on their own tickers. There "
        "is almost no other product in the catalogue where you can prove the thing works inside a "
        "first meeting. Use that. A deck about brand data is far less convincing than one URL that "
        "returns their own issuer's mark.",
        refs=(DOCS_LOGO_LINK,),
    ),
    _s(
        5,
        SlideKind.CONCEPT,
        "Why move four is unprompted",
        "The ownership disclosure costs thirty seconds and buys the credibility that carries "
        "everything else. Volunteered, it is professionalism. Extracted later by their compliance "
        "team, it is something you failed to mention. Same fact, opposite effect, and the only "
        "difference is who says it first.",
        refs=(TERMS,),
    ),
    _s(
        6,
        SlideKind.CONCEPT,
        "The two framings, and never mix them",
        'For a brokerage: "your app, on-brand". For a venue or vendor: "license brand data to '
        'serve your customers". Six words each. Using the wrong one is the specific error the '
        "founder corrected in this course, and it reads as not having understood their business.",
    ),
    _s(
        7,
        SlideKind.CONCEPT,
        "The expand sentence, because the free tier is a trap",
        "A client who adopts only Logo Link has taken something free and you have earned nothing. "
        "Have the sentence ready: what the free URL does not give them is the palette, the "
        "firmographics, and lookup by ISIN. Say it in the same meeting as the demo, not the next "
        "one.",
        refs=(DOCS_BRAND_API, PRICING),
    ),
    _s(
        8,
        SlideKind.CONCEPT,
        "The four objections, and where each was answered",
        '"Can\'t we scrape it?" — section 1, a maintenance argument. "Isn\'t it just logos?" — '
        'section 4, the palette and firmographics. "Is it free?" — section 3, both halves '
        'honestly. "Can we resell it?" — section 2, only under Enterprise, never the standard '
        "tier.",
    ),
    _s(
        9,
        SlideKind.CONCEPT,
        "Pricing: what you may and may not say",
        "You may quote the public anchors as approximate: free to roughly 500 thousand a month, "
        "Brand API from around $99 with roughly $0.10 overage, Enterprise a custom quote. You may "
        "not quote a commission, invent an Enterprise number, or imply a reseller programme "
        "exists. The public page is public; everything else is a scoped quote.",
        refs=(PRICING,),
    ),
    _s(
        10,
        SlideKind.CONCEPT,
        "What a good pilot looks like",
        "One surface, one metric they already care about, one date. The holdings table with marks "
        "and a user-testing read, or onboarding with the completion rate. Not the whole app. A "
        "broad pilot produces an inconclusive result, and an inconclusive pilot does not renew.",
    ),
    _s(
        11,
        SlideKind.CONCEPT,
        "Where this sits against the other products",
        "Brandfetch is the smallest of the three product courses by commission and the easiest to "
        "demo. That makes it a good opener into an account you want for something bigger: it is "
        "quick to prove, cheap to adopt, and it puts you in the room with the people who own the "
        "interface and the data feed.",
    ),
    _s(
        12,
        SlideKind.WALKTHROUGH,
        "Write the whole first meeting out",
        "Take the four-sentence opening from section 1, add the boundary question, your demo on "
        "their identifiers, and your disclosure. One page. This is the deliverable of the entire "
        "course and the thing you will actually use.",
    ),
    _s(
        13,
        SlideKind.WALKTHROUGH,
        "Write it twice, once per segment",
        "Do the whole page again for the other segment. The demo is the same; the framing, the "
        "buyer, the contract path and the objections all change. Having both written is what stops "
        "you reaching for the retail pitch in a venue meeting out of habit.",
    ),
    _s(
        14,
        SlideKind.WALKTHROUGH,
        "Read both rates and both windows now",
        "Open the Earnings page and read all four numbers. Note which tier steps down after year "
        "one and which does not, and which runs longer. Then say out loud which of two equal-sized "
        "deals is worth more to you over its life — that is not obvious from the headline rate "
        "alone.",
    ),
    _s(
        15,
        SlideKind.WALKTHROUGH,
        "Rehearse against the harder segment",
        "Run your page against a venue, which is the segment most advisors are least comfortable "
        "in: no interface argument, a negotiated licence, a lower rate, and a buyer who thinks in "
        "field lists. If it survives that, the brokerage version will be easy.",
    ),
    _s(
        16,
        SlideKind.EXAMPLE,
        "A first meeting, run properly",
        '"Where does a company show up as just a name or a ticker in your product?" — '
        '"Holdings, search, and the research tab." — "Does any of that leave your app? Exports, '
        'partner portals?" — "No, all in-app." — "Then here are three of your own tickers '
        'returning marks from one URL." Segment, licence and demo in four exchanges.',
    ),
    _s(
        17,
        SlideKind.EXAMPLE,
        "The same meeting, closed",
        '"What does it cost?" — "The image URL is genuinely free at your volume. The paid tier '
        "is the palette, the firmographics and ISIN lookup, and public pricing starts around $99 a "
        "month. I will get you a scoped quote. One thing to flag now rather than in legal: this is "
        'access to marks, not ownership."',
        refs=(PRICING, TERMS),
    ),
    _s(
        18,
        SlideKind.EXAMPLE,
        "The meeting that goes wrong in one sentence",
        '"You can resell this to your own clients and you are covered on the licensing." Two '
        "inventions in one breath: the standard tier does not cover redistribution, and you have "
        "no standing to give a licensing assurance. Both surface later, and both surface as you "
        "having misled them.",
    ),
    _s(
        19,
        SlideKind.CONCEPT,
        "The four lines you never cross",
        "Never quote a commission rate from memory or from a slide. Never state where the "
        "display-versus-redistribute line falls. Never tell a client what they may redistribute. "
        "Never present a Brandfetch claim — the index size, a customer name, a conversion figure — "
        "as independently verified fact.",
    ),
    _s(
        20,
        SlideKind.CONCEPT,
        "And the one sentence that handles all four",
        '"I will get you that in writing." It covers the rate, the boundary, the redistribution '
        "question and the unverified claim. It is also, consistently, the most credible thing an "
        "advisor can say — which is convenient, because it is the only correct answer to all four.",
    ),
    _s(
        21,
        SlideKind.CHECKPOINT,
        "Run the four moves out loud",
        "From memory, no page: the four moves in order, as you would actually say them, for a "
        "named real prospect. Then have someone ask what it costs and answer without quoting a "
        "commission. If you can do both, you are finished with this course.",
        checkpoint=(
            "Run all four moves aloud from memory for a named prospect, then answer a price "
            "question without quoting a commission."
        ),
    ),
    _s(
        22,
        SlideKind.CHECKPOINT,
        "Say both six-word framings and the boundary question",
        "Out loud: the distribution framing, the redistribution framing, and the question that "
        "separates them. Then the four lines you never cross. If the two framings blur, go back to "
        "section 2 — that blurring is the whole reason this course exists in this form.",
        checkpoint=(
            "Say both six-word framings, the boundary question, and the four lines you never cross."
        ),
    ),
    _s(
        23,
        SlideKind.CONCEPT,
        "What you should be able to do now",
        "Explain what Brandfetch is and who owns the marks. Tell which of two products a deal is "
        "from one question. Demo it in sixty seconds on a client's own identifiers. Frame it "
        "correctly for either segment. Disclose the compliance position unprompted. And qualify "
        "the licence before you forecast a single number.",
    ),
)

SECTION_8_TEST = SectionTest(
    pass_mark=0.8,
    questions=(
        TestQuestion(
            prompt="What must you qualify before forecasting a commission, and why?",
            options=(
                "The client's request volume, because pricing is per-request",
                "Which side of the licensing boundary the deal is on, because the two tiers pay\n"
                " different rates over different windows",
                "The segment, because rates are segment-specific",
                "The identifier type they use",
            ),
            answer_index=1,
            explanation=(
                "Forecasting before you know means forecasting the wrong number. Read both rates "
                "and both windows off the Earnings page."
            ),
        ),
        TestQuestion(
            prompt="What are the four moves of a first meeting, in order?",
            options=(
                "Demo, price, disclose, close",
                "Where does a company appear as just text; which side of the boundary; the demo\n"
                " on their own identifiers; the disclosure, unprompted",
                "Qualify budget, name the tier, negotiate, contract",
                "Disclose, demo, price, follow up",
            ),
            answer_index=1,
            explanation=(
                "Move one makes them describe their own product, which tells you the segment "
                "before you have named a single feature."
            ),
        ),
        TestQuestion(
            prompt="Why should the ownership disclosure be volunteered rather than waited for?",
            options=(
                "It is a contractual requirement on the reseller",
                "Volunteered it is professionalism; extracted later by compliance it is something\n"
                " you failed to mention — same fact, opposite effect",
                "It shortens the legal review",
                "It shifts the risk to Brandfetch",
            ),
            answer_index=1,
            explanation=(
                "Thirty seconds, and the only difference between the two outcomes is who says it "
                "first."
            ),
        ),
        TestQuestion(
            prompt="Which pricing statements are you allowed to make?",
            options=(
                "Any figure from the public pricing page, plus an Enterprise estimate",
                "The public anchors as approximate — free to roughly 500k a month, Brand API from\n"
                " around $99 with roughly $0.10 overage, Enterprise a custom quote",
                "No pricing at all",
                "Only your commission rate",
            ),
            answer_index=1,
            explanation=(
                "The public page is public. Inventing an Enterprise number, quoting a commission, "
                "or implying a reseller programme are all out."
            ),
        ),
        TestQuestion(
            prompt="A client is happy on the free Logo Link tier. What is the risk and the fix?",
            options=(
                "No risk; adoption always leads to expansion",
                "They have taken something free and you have earned nothing — say in the same\n"
                " meeting what the free URL lacks: palette, firmographics, ISIN lookup",
                "Warn them the free tier will be withdrawn",
                "Escalate to Enterprise licensing",
            ),
            answer_index=1,
            explanation=(
                "The demo is right; the absence of a prepared expand sentence, said in the same "
                "meeting rather than the next one, is the mistake."
            ),
        ),
        TestQuestion(
            prompt="Which single sentence handles all four lines you never cross?",
            options=(
                "Let me check with the vendor",
                "I will get you that in writing",
                "That is outside my remit",
                "It depends on the licence",
            ),
            answer_index=1,
            explanation=(
                "It covers the rate, the boundary, the redistribution question and the unverified "
                "claim — and it is consistently the most credible thing an advisor can say."
            ),
        ),
    ),
)


def section_8() -> CourseModule:
    """Section 8: the sale, and the licence you qualify before forecasting."""
    return CourseModule(
        id=_id("module", "how-to-sell-it"),
        title="How to sell it",
        order=7,
        lessons=(
            Lesson(
                id=_id("lesson", "how-to-sell-it"),
                title="Four moves, two framings, four lines",
                body=_S8_BODY,
                order=0,
                slides=_SECTION_8_SLIDES,
                drill_topics=("product:brandfetch:selling",),
                measurement=(
                    "You can run all four moves from memory for a named prospect, use the right "
                    "framing per segment, and answer a price question without quoting a commission."
                ),
            ),
        ),
        section_test=SECTION_8_TEST,
    )


def rebuilt_sections() -> tuple[CourseModule, ...]:
    """The sections rebuilt to the GRS-0215 standard, in order. All eight are written."""
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


SECTIONS_AUTHORED: tuple[str, ...] = (
    "what-it-is",
    "the-boundary",
    "the-four-surfaces",
    "the-identifier-hook",
    "distribution-retail",
    "redistribution-venue",
    "licensing-and-trademark",
    "how-to-sell-it",
)
# All eight are written (2026-07-30). The tuple stays, empty, because the test that guards it reads
# it, and because it is the shape the next rebuilt course would start from.
SECTIONS_PLANNED: tuple[str, ...] = ()
