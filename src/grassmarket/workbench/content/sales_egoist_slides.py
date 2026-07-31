"""The Sales Egoist, rebuilt to the GRS-0215 depth standard (GRS-0218).

The founder, on the first attempt at this course:

    "You have done nothing but generically summarize some of the content I gave you. I am beyond
    disappointed."

That attempt was written from a paraphrase because the source was not in the repository. It is now:
`data/reference/sales-egoist/Bruntsfield_TheSalesEgoist_Curriculum.docx` (the Master Curriculum,
three parts and eight convictions) and two authored lesson decks. Everything below is developed from
that text rather than compressed from it, and every lesson cites it.

**This is the methodology course, not a product course.** It is what makes an advisor good at the
job rather than knowledgeable about one vendor, so it carries more weight than any single product
course and, until now, had the least behind it.

Eight sections, each one lesson of 20 to 40 slides and a test the advisor passes before the next
opens. The shape follows the curriculum's own: Part One is the terrain, the battlefield and the
armoury (sections 1 to 3); Part Two is the eight convictions, two per section (4 to 7); Part Three
integrates them into one campaign, which section 8 then runs against an actual ATLAS engagement.

Two authoring decisions worth stating, because both could look like errors:

1. **The doctrine's own vocabulary is kept.** "Weapons", "the zero-sum pipeline", "the armoury" —
   this is internal training in the founder's voice, and neutering it would remove the force that
   makes it memorable. GRS-0148 finding 4 asks whether that naming survives on **client-adjacent**
   surfaces; that is founder decision D5b and is not this course's call. Nothing here leaks to a
   client surface: the course is advisor-only, and no slide text is reused in a deliverable.
2. **The capital-markets facts carry dates.** T+1, the December 2026 confirmations milestone, the
   October 2027 deadline, the August 2026 EU AI Act obligations. They are in the curriculum and they
   are the spine of the whole trigger discipline, so they are stated with their dates rather than
   softened into "upcoming regulation" — a course that will not name a date cannot teach a seller to
   work backwards from one.
"""

from __future__ import annotations

from uuid import NAMESPACE_URL, UUID, uuid5

from bcap_contracts.learning import (
    CourseModule,
    Lesson,
    LessonAsset,
    LessonAuthor,
    SectionTest,
    Slide,
    SlideKind,
    SourceRef,
    SourceRefKind,
    TestQuestion,
)

from grassmarket.workbench.content.sales_egoist_diagrams import SVG

_NS = "grassmarket:academy:sales-egoist"


def _id(kind: str, key: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"{_NS}:{kind}:{key}")


# --- Sources ------------------------------------------------------------------------------
#
# The source is committed material, not a public URL, so these point at the file in this
# repository. `SourceRef.url` is https-only at the contract, which is right for a product course
# citing vendor documentation and means a repo file has to be cited by its canonical blob URL. That
# is honest here: the link resolves to the exact committed artefact the lesson was written from.

_REPO_BLOB = "https://github.com/wealthcx01/grassmarket/blob/main/data/reference/sales-egoist"

CURRICULUM = SourceRef(
    title="The Sales Egoist: Master Curriculum (Bruntsfield, committed source)",
    url=f"{_REPO_BLOB}/Bruntsfield_TheSalesEgoist_Curriculum.docx",
    kind=SourceRefKind.DOCS,
)
DECK_01 = SourceRef(
    title="The Sales Egoist, Lesson 01: The Zero-Sum Pipeline (authored deck)",
    url=f"{_REPO_BLOB}/Bruntsfield_TheSalesEgoist_Lesson01.pptx",
    kind=SourceRefKind.DOCS,
)
DECK_02 = SourceRef(
    title="The Sales Egoist, Lesson 02: Your Unfair Advantage (authored deck)",
    url=f"{_REPO_BLOB}/Bruntsfield_TheSalesEgoist_Lesson02.pptx",
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
    """A course diagram (GRS-0225), generated from the SceneSpec under
    `design/motion/courses/sales_egoist/`. Caption and alt text are authored prose and live here,
    beside the slide they belong to. `SVG[key]` raises on an unknown key rather than returning a
    placeholder, because a slide that silently lost its drawing would still look finished."""
    return LessonAsset(caption=caption, alt=alt, svg=SVG[key])


# ==========================================================================================
# Section 1 — The doctrine: what a Sales Egoist is, and what it argues against
# ==========================================================================================

_S1_BODY = (
    "By the end of this lesson you can state what the Sales Egoist doctrine claims, defend the "
    "word "
    "'egoist' to a colleague who finds it distasteful, and identify — honestly — which of the five "
    "placeholder behaviours you currently exhibit. This is the foundational section: the seven "
    "that "
    "follow are applications of the belief set out here, and they will not land if this one is "
    "read "
    "as motivational language rather than as an argument about what selling is."
)

_SECTION_1_SLIDES: tuple[Slide, ...] = (
    _s(
        0,
        SlideKind.CONCEPT,
        "A belief, not a framework",
        "The curriculum opens by refusing a category. This is not a borrowed framework or a "
        "collection of techniques; it is a belief about what selling is. That distinction governs "
        "everything that follows, because a framework is something you apply to a deal and a "
        "belief "
        "is something you bring to a career. You can run MEDDIC badly and still have run MEDDIC. "
        "You cannot hold this doctrine badly — you either own the number or you do not.",
        refs=(CURRICULUM,),
    ),
    _s(
        1,
        SlideKind.CONCEPT,
        "Where the claim comes from",
        "The doctrine is not theory. It comes from years spent inside banks, brokers and fintechs, "
        "and its central observation is specific: the bottleneck to winning is rarely the product "
        "and almost always the seller's posture toward the outcome. Hold that sentence up against "
        "your last three losses. If you can name the product gap that lost each one, this course "
        "will be less use to you than the roadmap. Most sellers cannot.",
        refs=(CURRICULUM,),
    ),
    _s(
        2,
        SlideKind.CONCEPT,
        "Why 'egoist', and why the word is deliberate",
        "The word is chosen and it is not vanity. The curriculum is explicit: an egoist is meant "
        "'not in the small sense of vanity, but in the demanding sense of self-authorship'. An "
        "egoist does not wait to be chosen; they author the result. If the word still grates, hold "
        "the objection until section 8 — but notice that the discomfort is doing work, because a "
        "doctrine you can adopt without discomfort is one that asks nothing of you.",
        refs=(CURRICULUM,),
    ),
    _s(
        3,
        SlideKind.CONCEPT,
        "Who this is written for",
        "Not the beginner. The doctrine names its reader precisely: the experienced professional "
        "whose career has quietly drifted into management-by-queue — competent, well-liked, and "
        "waiting. The premise is not that such a seller lacks ability. It is that real ability has "
        "gone dormant under years of comfort. That is a more uncomfortable claim than "
        "incompetence, "
        "and it is the reason the first section is the hardest one to accept.",
        refs=(CURRICULUM,),
    ),
    _s(
        4,
        SlideKind.CONCEPT,
        "The drift, and how it happens",
        "Nobody decides to become passive. The deck puts it as a slow substitution: 'somewhere in "
        "a "
        "long career, selling quietly became waiting' — for the inbound lead, for the RFP, for the "
        "relationship to mature on its own. The seller stops choosing targets and starts "
        "administering a territory. What makes it hard to see from the inside is that activity "
        "stays high the entire time. Initiative dies quietly and the calendar stays full.",
        refs=(DECK_01, CURRICULUM),
    ),
    _s(
        5,
        SlideKind.CONCEPT,
        "The sentence the doctrine is built on",
        "'A seller who waits becomes a placeholder. Interchangeable, and easily replaced.' Every "
        "conviction in this course is a way of refusing that sentence. Read it as a commercial "
        "claim rather than a rebuke: a placeholder is interchangeable because nothing about the "
        "outcome depended on which placeholder was in the seat. If your accounts would have "
        "progressed identically under a competent stranger, the sentence is describing you.",
        refs=(DECK_01,),
    ),
    _s(
        6,
        SlideKind.CONCEPT,
        "Placeholder or principal: the five situations",
        "The contrast is not a personality test. It is five specific situations, each answered two "
        "ways, and the diagram is worth studying row by row rather than as a whole. Most sellers "
        "are principals in one or two rows and placeholders in the rest — which is useful, because "
        "it makes the work specific. You are not being asked to become a different person; you are "
        "being asked to change your answer to three of five recurring situations.",
        asset=_diagram(
            "placeholder_or_principal",
            "The doctrine's founding contrast, from Lesson 01 of the authored deck.",
            "A two-column comparison. On the left, in a plain panel headed THE PLACEHOLDER: waits "
            "for inbound and RFPs; hopes relationships mature; reports activity; moves on the "
            "buyer's timeline; is interchangeable. On the right, in a dark green panel headed THE "
            "PRINCIPAL, the same five situations answered differently: engineers the reason to "
            "engage; turns trust into real leverage; reports territory taken; sets the timeline; "
            "is "
            "irreplaceable. Beneath both, the line: a seller who waits becomes a placeholder, "
            "interchangeable and easily replaced.",
        ),
        refs=(DECK_01,),
    ),
    _s(
        7,
        SlideKind.EXAMPLE,
        "Row one, in practice: 'waits for inbound' versus 'engineers the reason'",
        "A regional broker's OEMS contract renews in fourteen months. The placeholder learns this "
        "when procurement issues an RFP, and joins a field of five. The principal knows the "
        "renewal "
        "date today, works backwards nine to twelve months, and arrives with a costed thesis about "
        "why the incumbent will not survive the 2027 settlement deadline — before any process "
        "exists. Same account, same product, same seller ability. Different posture, different "
        "odds.",
        refs=(CURRICULUM,),
    ),
    _s(
        8,
        SlideKind.EXAMPLE,
        "Row three, in practice: 'reports activity' versus 'reports territory taken'",
        "Two pipeline reviews. The first: 'forty-two touches, nine meetings, three demos booked.' "
        "The second: 'I have moved two accounts off the incumbent's renewal path and reached the "
        "economic buyer in both.' The first is a defence against the question. The second is an "
        "answer to it. Notice that the first seller may well have worked harder — activity is not "
        "the opposite of ownership, it is the most common substitute for it.",
        refs=(DECK_01,),
    ),
    _s(
        9,
        SlideKind.CONCEPT,
        "What the doctrine is arguing against",
        "Three comfortable fictions, named directly in the curriculum. That a deal can be lost "
        "gracefully. That a deal can be deferred safely. That a full territory is the same thing "
        "as "
        "a pipeline. Each is a way of describing an outcome you did not author as an outcome that "
        "happened to you. The doctrine's response is blunt: by the time the RFP is written, the "
        "outcome is usually already decided.",
        refs=(CURRICULUM,),
    ),
    _s(
        10,
        SlideKind.CONCEPT,
        "The terrain: you are not selling to a person",
        "Before any of this becomes actionable you need the minimum situational awareness the "
        "curriculum demands. An enterprise capital-markets purchase is decided by a committee of "
        "competing appetites, not a single buyer. Each member wants something different, fears "
        "something different, and is moved by a different weapon. Section 6 maps the committee "
        "properly; what matters here is that 'the buyer' is a fiction you must stop using.",
        refs=(CURRICULUM,),
    ),
    _s(
        11,
        SlideKind.CONCEPT,
        "The disqualifying move",
        "The curriculum states the consequence plainly: bringing the wrong weapon to the wrong "
        "stakeholder is an instant disqualification. Not a setback — a disqualification. A "
        "feature-tour to a quant, or a slide-deck of dashboards to a Head of Risk, ends the "
        "conversation before it starts, and it ends it silently. Nobody tells you that you lost "
        "the "
        "room in the first four minutes; they let the meeting run and do not reply.",
        refs=(CURRICULUM,),
    ),
    _s(
        12,
        SlideKind.CONCEPT,
        "The three phases of the programme",
        "The eight convictions are grouped, and the grouping is an argument. Phase I, the First "
        "Selection, deconstructs the seller: the zero-sum pipeline, the signature weapon, "
        "reproducibility, the hardest prospect. Phase II, the Second Selection, is the logic of "
        "joint execution: the committee, and engineered timing. Phase III is the peak: flow, and "
        "total account awareness. You cannot skip to Phase III; the curriculum says to read them "
        "in "
        "order because they compound.",
        refs=(DECK_01, CURRICULUM),
    ),
    _s(
        13,
        SlideKind.CONCEPT,
        "The maturity model this course moves you along",
        "Four stages, from Part Three. Most sellers begin as placeholders and, with discipline, "
        "become operators. The programme exists to carry the capable operator through to principal "
        "and, ultimately, to egoist — the seller who shapes the market rather than responding to "
        "it. Locate yourself honestly. An operator who believes they are a principal will find "
        "sections 5 through 8 unusable, because they are written for someone who has admitted the "
        "gap.",
        refs=(CURRICULUM,),
    ),
    _s(
        14,
        SlideKind.CONCEPT,
        "Why this course sits before the product courses",
        "The Academy makes this the mandatory first course, and the ordering is deliberate. A "
        "seller who knows OpenBB, Benzinga and Brandfetch in detail but waits to be invited into "
        "deals will sell none of them. Product knowledge is leverage applied to a posture; if the "
        "posture is passive, the leverage multiplies nothing. Everything you learn in the product "
        "courses is the 'proof' variable in section 5's equation — one term of five.",
        refs=(CURRICULUM,),
    ),
    _s(
        15,
        SlideKind.CONCEPT,
        "What this doctrine is not asking of you",
        "It is not asking you to be aggressive, to cold-call more, or to be unpleasant to buyers. "
        "Nothing in the curriculum recommends volume or pressure. Every conviction is about "
        "*direction* rather than *force*: choosing the target, choosing the weapon, choosing the "
        "moment. A seller who reads this as permission to push harder has taken the one reading "
        "the "
        "text does not support, and will be less effective, not more.",
        refs=(CURRICULUM,),
    ),
    _s(
        16,
        SlideKind.CHECKPOINT,
        "Locate yourself: the five rows, answered honestly",
        "Take the diagram from slide 6 and answer each row for your own book, in writing. For each "
        "of the five, write P (placeholder) or R (principal) and one sentence of evidence from the "
        "last quarter. The evidence is the part that matters — 'I set the timeline' is a claim; 'I "
        "moved the Nomura conversation forward two months by tying it to their October board "
        "review' is evidence. Rows where you cannot produce evidence are P.",
        checkpoint="Write your five P/R answers with one line of evidence each.",
        refs=(DECK_01,),
    ),
    _s(
        17,
        SlideKind.CHECKPOINT,
        "Name the drift in your own book",
        "List every live account you hold. Mark each as *chosen* (you decided to pursue it and can "
        "say why it, rather than another) or *inherited* (it arrived on your territory list). "
        "Count "
        "the two columns. This number is the most honest measure of the doctrine's first claim as "
        "it applies to you, and most experienced sellers are surprised by it — not because the "
        "ratio is bad, but because they have never counted.",
        checkpoint="Record your chosen-to-inherited ratio.",
        refs=(CURRICULUM,),
    ),
    _s(
        18,
        SlideKind.CHECKPOINT,
        "Write the objection you have to this course",
        "You have one. It may be the word 'egoist', the martial vocabulary, or the claim that your "
        "passivity is comfort rather than professionalism. Write it down in full, now, before the "
        "content that would soften it. In section 8 you will read it again and decide whether it "
        "survived. This is not a rhetorical device: an objection you never articulated cannot be "
        "answered, and will quietly reduce everything that follows to reading.",
        checkpoint="Write your strongest objection to the doctrine, in full.",
        refs=(CURRICULUM,),
    ),
    _s(
        19,
        SlideKind.EXAMPLE,
        "The doctrine applied to our own product",
        "Grassmarket's Platform Power assessment is, among other things, a selling instrument — "
        "section 8 develops this. Notice the doctrine operating in its design: it does not wait "
        "for "
        "a client to describe their problem, it measures the platform and tells them what the "
        "constraint is. That is the Challenger move made into software. You are being asked to "
        "adopt a posture the firm's product already takes.",
        refs=(CURRICULUM,),
    ),
    _s(
        20,
        SlideKind.CONCEPT,
        "The instruction underneath all eight convictions",
        "The closing of the curriculum reduces the whole doctrine to two words: stop waiting. Stop "
        "waiting for the RFP, for the relationship to mature, for the right moment, for permission "
        "to act. Every conviction is a way of converting one passive habit into a deliberate, "
        "repeatable, self-authored move. If you remember nothing else from this section, that is "
        "the sentence to keep.",
        refs=(CURRICULUM,),
    ),
    _s(
        21,
        SlideKind.CHECKPOINT,
        "Before you move on",
        "You should now be able to do three things without notes: state what the doctrine claims "
        "and what it argues against; explain the word 'egoist' in the self-authorship sense to a "
        "sceptical colleague; and name which of the five placeholder rows you occupy, with "
        "evidence. If any of the three is shaky, reread slides 2 to 9 — the remaining seven "
        "sections assume all three.",
        checkpoint="Confirm you can state the doctrine, defend the word, and locate yourself.",
        refs=(CURRICULUM, DECK_01),
    ),
)

SECTION_1_TEST = SectionTest(
    questions=(
        TestQuestion(
            prompt="In the doctrine, what does 'egoist' mean?",
            options=(
                "Self-authorship: the seller authors the outcome rather than waiting to be chosen",
                "Self-interest: the seller puts their commission ahead of the client's outcome",
                "Self-confidence: the seller projects certainty regardless of the evidence",
                "Self-sufficiency: the seller works deals alone rather than with a team",
            ),
            answer_index=0,
            explanation=(
                "The curriculum is explicit that the word is meant 'not in the small sense of "
                "vanity, but in the demanding sense of self-authorship'. Note that the third and "
                "fourth options are actively contradicted later: section 7 warns against "
                "projecting "
                "past the evidence, and section 5 insists no one wins an enterprise deal alone."
            ),
        ),
        TestQuestion(
            prompt="What does the doctrine identify as the usual bottleneck to winning?",
            options=(
                "The seller's posture toward the outcome",
                "The product's feature gaps against the competition",
                "Pricing, in a market that has commoditised",
                "The length of the enterprise procurement cycle",
            ),
            answer_index=0,
            explanation=(
                "Years inside banks, brokers and fintechs produced the observation that the "
                "bottleneck 'is rarely the product and almost always the seller's posture toward "
                "the outcome'. The other three are real constraints, but the doctrine's claim is "
                "that they are not usually the binding one."
            ),
        ),
        TestQuestion(
            prompt="Who is the doctrine written for?",
            options=(
                "The experienced seller whose career has drifted into management-by-queue",
                "The new graduate hire learning enterprise sales for the first time",
                "The sales manager building a team's operating cadence",
                "The technical pre-sales engineer supporting a quota-carrying seller",
            ),
            answer_index=0,
            explanation=(
                "The premise is specifically that ability has gone dormant under years of comfort "
                "— "
                "not that it is absent. That is why the first section is the hardest to accept: it "
                "asks a competent, well-liked professional to admit they have become passive."
            ),
        ),
        TestQuestion(
            prompt=(
                "An advisor says: 'I made forty-two touches and booked three demos this month.' "
                "Which row of the placeholder/principal contrast is this?"
            ),
            options=(
                "Reports activity, rather than territory taken",
                "Moves on the buyer's timeline, rather than setting it",
                "Hopes relationships mature, rather than turning trust into leverage",
                "Waits for inbound, rather than engineering the reason to engage",
            ),
            answer_index=0,
            explanation=(
                "Activity is the most common substitute for ownership, and the seller reporting it "
                "may genuinely have worked hardest. The principal's version answers the question "
                "instead of defending against it: which accounts moved, and how far."
            ),
        ),
        TestQuestion(
            prompt="What does bringing the wrong weapon to the wrong stakeholder cost you?",
            options=(
                "An instant disqualification, usually a silent one",
                "A delay while the stakeholder is re-educated",
                "Nothing, provided the economic buyer is still engaged",
                "A pricing concession to recover credibility",
            ),
            answer_index=0,
            explanation=(
                "The curriculum's word is disqualification, not setback. The silence is the "
                "dangerous part: nobody tells you the room was lost in the first four minutes, so "
                "the seller records a meeting that went fine and never learns otherwise."
            ),
        ),
        TestQuestion(
            prompt="Why does this course sit before the product courses in the Academy?",
            options=(
                "Product knowledge is leverage applied to a posture; a passive posture multiplies "
                "nothing",
                "It is shorter, so it makes a gentler introduction to the Academy",
                "The product courses depend on its certification credit",
                "Product content changes often, so the doctrine is safer to teach first",
            ),
            answer_index=0,
            explanation=(
                "A seller fluent in OpenBB, Benzinga and Brandfetch who waits to be invited into "
                "deals will sell none of them. In section 5's terms, everything the product "
                "courses "
                "teach is the 'proof' variable — one term of five."
            ),
        ),
    ),
    pass_mark=0.8,
)


def section_1() -> CourseModule:
    """Section 1: the doctrine, the word, and the terrain."""
    return CourseModule(
        id=_id("module", "the-doctrine"),
        title="The doctrine: self-authorship, and what it argues against",
        order=0,
        lessons=(
            Lesson(
                id=_id("lesson", "the-doctrine"),
                title="What a Sales Egoist is, and why the word is deliberate",
                body=_S1_BODY,
                order=0,
                author=LessonAuthor.HUMAN,
                slides=_SECTION_1_SLIDES,
                references=(CURRICULUM, DECK_01),
                drill_topics=("doctrine:self-authorship",),
                measurement=(
                    "You have written your five placeholder/principal answers with evidence, your "
                    "chosen-to-inherited account ratio, and your standing objection to the "
                    "doctrine."
                ),
            ),
        ),
        section_test=SECTION_1_TEST,
    )


# ==========================================================================================
# Section 2 — The battlefield: the forces that thaw a frozen budget
# ==========================================================================================

_S2_BODY = (
    "By the end of this lesson you can name the seven forces the curriculum identifies as creating "
    "urgency in capital markets right now, place the dated ones on a calendar without looking them "
    "up, and work backwards from one of them to a specific account in your own book. This is the "
    "section that turns the doctrine's 'stop waiting' into something operational: you cannot "
    "arrive "
    "before the RFP unless you know which deadline is going to cause it."
)

_SECTION_2_SLIDES: tuple[Slide, ...] = (
    _s(
        0,
        SlideKind.CONCEPT,
        "Budgets do not thaw on their own",
        "The curriculum's claim is narrow and useful: budgets thaw when a dated, board-level "
        "catalyst forces them to. Not when a seller is persuasive, not when a relationship "
        "matures, "
        "and not when a quarter ends. If you cannot name the catalyst behind an opportunity, you "
        "are looking at an interest, not a deal — and the forecast you have built on it is a hope "
        "with a date attached.",
        refs=(CURRICULUM,),
    ),
    _s(
        1,
        SlideKind.CONCEPT,
        "Why this market, specifically",
        "The curriculum's judgement is that the capital-markets environment of the mid-2020s is "
        "unusually rich in such catalysts. That is a claim about timing rather than about the "
        "market's permanent character, and it cuts both ways: the density of dated triggers "
        "available now is a window, and a seller who spends it waiting for inbound has wasted the "
        "most legible set of trigger events in a generation.",
        refs=(CURRICULUM,),
    ),
    _s(
        2,
        SlideKind.CONCEPT,
        "The seven forces, named",
        "The settlement squeeze. The move to always-on markets. Market-data burstiness. AI moving "
        "from pilot to production. Vendor and platform consolidation. Governance that ships with "
        "the use case. Cost compression and the modernisation mandate. Learn them as a list first; "
        "the rest of this section takes each one and turns it into an opening. Every one of them "
        "is "
        "a reason a buyer has to move that has nothing to do with liking you.",
        refs=(CURRICULUM,),
    ),
    _s(
        3,
        SlideKind.CONCEPT,
        "Force 1: the settlement squeeze, and the dates that matter",
        "The US moved to T+1 in May 2024. The UK, EU and Switzerland follow on 11 October 2027, "
        "with mandatory T+0 allocations and confirmations as early as December 2026. Those two "
        "dates are the most valuable facts in this course. The curriculum calls this the single "
        "largest, most legible trigger event in the market — a hard, dated deadline that forces "
        "budget whether or not anybody wants to spend it.",
        refs=(CURRICULUM,),
    ),
    _s(
        4,
        SlideKind.CONCEPT,
        "Why T+1 breaks things rather than merely tightening them",
        "T+1 removes roughly half the post-trade processing window, and by the SWIFT Institute's "
        "estimate up to 80% of the time for cross-border settlement once time zones and FX are "
        "accounted for. That is the difference between a squeeze and a break: manual, "
        "spreadsheet-bound workflows do not get slower, they stop working. A process that needs a "
        "human overnight has nowhere to put the human.",
        refs=(CURRICULUM,),
    ),
    _s(
        5,
        SlideKind.CONCEPT,
        "The calendar, and why the order matters",
        "The confirmations milestone lands a year before the settlement deadline, and the EU AI "
        "Act "
        "obligations bite between them in August 2026. That ordering is the seller's actual "
        "opportunity: firms that plan against October 2027 discover in testing that December 2026 "
        "arrives first. An advisor who can place these on a line — and work backwards nine to "
        "twelve months from the earliest — is early to a conversation everyone else reaches late.",
        asset=_diagram(
            "the_battlefield",
            "The dated catalysts, in the order they arrive.",
            "A horizontal timeline with four marked dates. May 2024, in muted grey: the US moves "
            "to "
            "T+1. August 2026, in ink: EU AI Act obligations begin to bite. December 2026, in "
            "green: T+0 allocations and confirmations mandated. 11 October 2027, in green: the UK, "
            "EU and Switzerland move to T+1. Below the line, in a warm caution colour, a heading "
            "reading UNDATED, AND INEVITABLE, with the note that the incumbent outage in a bursty "
            "session should be positioned for as a when rather than an if.",
        ),
        refs=(CURRICULUM,),
    ),
    _s(
        6,
        SlideKind.CONCEPT,
        "Force 2: always-on markets",
        "Major US exchanges are pushing toward 23 hours a day, five days a week, and venues are "
        "launching blockchain-based platforms for 24/7 trading of tokenised securities. The "
        "selling "
        "consequence is architectural and specific: always-on markets demand event-driven, "
        "resilient design and erase the overnight batch window that legacy systems were built "
        "around. A batch job is not a feature you can reschedule when there is no night.",
        refs=(CURRICULUM,),
    ),
    _s(
        7,
        SlideKind.CONCEPT,
        "Force 3: market-data burstiness",
        "Volumes keep rising, but the curriculum is careful about where the real problem sits: the "
        "sharper issue is variability — sudden, violent intraday spikes that strain systems "
        "designed for a calmer era. This matters for how you open. 'Your data volumes are growing' "
        "is a claim every vendor makes. 'Your capacity is provisioned for your mean and your "
        "failures happen at your peak' is a diagnosis, and it is usually true.",
        refs=(CURRICULUM,),
    ),
    _s(
        8,
        SlideKind.CONCEPT,
        "Force 4: AI from pilot to production, and where it actually jams",
        "AI is industrialising across trading, research, risk and the software lifecycle itself. "
        "The curriculum's insight is about the constraint: it is no longer model sophistication "
        "but "
        "data — fragmented, poorly governed estates are now the primary throttle, with a large "
        "share of agentic initiatives at risk of underperforming without clean, lineage-aware "
        "foundations. Sell the foundation, not the model.",
        refs=(CURRICULUM,),
    ),
    _s(
        9,
        SlideKind.CONCEPT,
        "Force 5: consolidation, which is displacement with a friendlier name",
        "On the buy-side, consolidating vendors and modernising data architecture are the top "
        "technology priorities. Read that commercially, as the curriculum does: every "
        "consolidation "
        "decision is a displacement opportunity for one vendor and an extinction event for "
        "another. "
        "There is no neutral position in a consolidation. If you are not the consolidator in an "
        "account, you are what is being consolidated.",
        refs=(CURRICULUM,),
    ),
    _s(
        10,
        SlideKind.CONCEPT,
        "Force 6: governance ships with the use case",
        "Controls can no longer sit beside delivery. Role-based permissions, segregation of "
        "duties, "
        "audit trails, deterministic fallbacks and continuous monitoring must ship with the "
        "product, and the EU AI Act's obligations begin to bite from August 2026. The curriculum's "
        "conclusion is the line to remember: defensibility is now a feature, not paperwork. "
        "Section 5 turns this into a weapon; here, just register that it moved.",
        refs=(CURRICULUM,),
    ),
    _s(
        11,
        SlideKind.CONCEPT,
        "Force 7: cost compression and the modernisation mandate",
        "Complexity costs rise faster than revenue on aging cores, so firms must modernise "
        "deliberately or be outpaced by platforms whose economics improve with scale. Note the "
        "tension the curriculum flags, because it decides your framing: IT budgets are rising, but "
        "scrutiny and selectivity are rising faster. There is money. There is much less patience "
        "for a business case that does not survive inspection.",
        refs=(CURRICULUM,),
    ),
    _s(
        12,
        SlideKind.CONCEPT,
        "The undated catalyst",
        "One trigger has no date and is not optional: the incumbent's outage during a volatile, "
        "bursty session. The curriculum treats this as inevitable rather than possible, and the "
        "instruction that follows is a positioning one — be the credible, present voice in that "
        "account beforehand, because the call goes to whoever is already trusted. Section 7 "
        "develops this into the whole discipline of engineering luck.",
        refs=(CURRICULUM,),
    ),
    _s(
        13,
        SlideKind.CONCEPT,
        "Working backwards: the nine-to-twelve month rule",
        "The field note from Lesson 01 is operationally the most useful line in the curriculum: "
        "the "
        "renewal date is public information, and you work backwards from it by nine to twelve "
        "months. Applied to the battlefield, this means a December 2026 confirmations milestone is "
        "a conversation to be having from roughly early 2026, and the October 2027 deadline is one "
        "to open in late 2026. If you wait for the deadline to feel close, you are late by a year.",
        refs=(CURRICULUM,),
    ),
    _s(
        14,
        SlideKind.CONCEPT,
        "'Why now' beats 'why us'",
        "The second field note reorders your opening. Lead with the catalyst, not the capability. "
        "'Why us' is a claim the buyer has heard from four vendors and has no way to adjudicate; "
        "'why now' is a fact about their world that they can verify independently and that creates "
        "the budget conversation you need. Capability arrives second, once there is a reason for "
        "it "
        "to matter.",
        refs=(CURRICULUM,),
    ),
    _s(
        15,
        SlideKind.EXAMPLE,
        "A worked opening, built from a force",
        "To a Head of Operations at a mid-tier asset manager, eighteen months out: 'Your "
        "confirmations have to be same-day from December 2026, not October 2027 — most firms plan "
        "against the settlement date and find the confirmation milestone lands first. On your "
        "current exception rate, that is roughly N breaks a day with no overnight window to clear "
        "them. Can I show you what the shadow-mode reconciliation looks like on your own volumes?' "
        "Catalyst, consequence, specific ask.",
        refs=(CURRICULUM,),
    ),
    _s(
        16,
        SlideKind.EXAMPLE,
        "The same account, opened badly",
        "'We're a leading post-trade automation platform trusted by tier-one institutions, and I'd "
        "love twenty minutes to walk you through our capabilities.' Nothing here is false and "
        "nothing is a reason to act. It leads with 'why us', names no catalyst, quantifies no "
        "consequence, and asks for time rather than offering a diagnosis. It will get a polite "
        "decline, and the seller will record it as a timing problem.",
        refs=(CURRICULUM,),
    ),
    _s(
        17,
        SlideKind.EXAMPLE,
        "A force applied to an exchange, not a broker",
        "The forces are not retail-brokerage-shaped. To an exchange: 23/5 trading erases the "
        "overnight window your surveillance batch depends on, and tokenised venues push toward "
        "24/7. That is not a capacity problem you can provision your way out of — it is an "
        "architectural one, and it lands on the same calendar as your data-burstiness spend. Match "
        "the force to the operating model or the opening sounds borrowed.",
        refs=(CURRICULUM,),
    ),
    _s(
        18,
        SlideKind.EXAMPLE,
        "The same forces, to a wealth manager",
        "Wealth is the third operating model we sell into and it reads the battlefield "
        "differently again. Consolidation and cost compression land as platform and custody "
        "economics; the AI force lands as suitability evidence a supervisor can audit rather than "
        "as trading alpha; and governance-with-the-use-case is the one a wealth board raises "
        "first, not last. Bring an exchange's 23/5 argument to a discretionary manager and you "
        "have proved you did not look them up.",
        refs=(CURRICULUM,),
    ),
    _s(
        19,
        SlideKind.CHECKPOINT,
        "Build your trigger watchlist",
        "Take your top ten accounts. For each, record: the incumbent, the renewal date if you can "
        "find it, which of the seven forces bears on them most directly, and the earliest dated "
        "milestone that forces their hand. Any account where all four cells are empty is not a "
        "target yet — it is a name. This watchlist is the artefact section 7 will ask you to "
        "operate, so build it properly now.",
        checkpoint=(
            "Produce a ten-account trigger watchlist with incumbent, renewal, force and date."
        ),
        refs=(CURRICULUM,),
    ),
    _s(
        20,
        SlideKind.CHECKPOINT,
        "Work one account backwards",
        "Choose the account on your watchlist with the earliest dated milestone. Count back nine "
        "to "
        "twelve months from that date and write the calendar month in which the conversation has "
        "to "
        "start. If that month is in the past, write that down too — that is the most useful thing "
        "this section can tell you, and it is a different kind of problem from the one you thought "
        "you had.",
        checkpoint="Name the month the conversation must start, and whether it has passed.",
        refs=(CURRICULUM,),
    ),
    _s(
        21,
        SlideKind.CHECKPOINT,
        "Write one catalyst-led opening",
        "For that same account, write the opening in the shape of slide 15: the dated catalyst, "
        "the "
        "consequence in their units, and one specific ask. Three sentences, no capabilities, no "
        "company boilerplate. Read it aloud. If it would survive being sent to someone who has "
        "never heard of us, it is doing the work; if it needs our name to make sense, rewrite it.",
        checkpoint="Draft a three-sentence catalyst-led opening for one real account.",
        refs=(CURRICULUM,),
    ),
    _s(
        22,
        SlideKind.CONCEPT,
        "What this section is not claiming",
        "Not that every deal has a dated catalyst — some genuinely do not, and forcing one "
        "produces "
        "the fabricated urgency buyers recognise instantly. The claim is narrower: where a "
        "catalyst "
        "exists, it is the strongest opening available and it is usually public. Where none "
        "exists, "
        "you are selling into discretionary spend against rising selectivity, and you should price "
        "your expectations accordingly.",
        refs=(CURRICULUM,),
    ),
    _s(
        23,
        SlideKind.CHECKPOINT,
        "Before you move on",
        "You should be able to name the seven forces without notes, state the three dates that "
        "anchor the calendar, and produce your ten-account watchlist on demand. The next section "
        "hands you the armoury — sixteen methodologies grouped by purpose — and it will read as a "
        "list of names unless you already know which force you are riding into which account.",
        checkpoint="Confirm the seven forces, the three dates, and your watchlist are in place.",
        refs=(CURRICULUM,),
    ),
)

SECTION_2_TEST = SectionTest(
    questions=(
        TestQuestion(
            prompt="When do the UK, EU and Switzerland move to T+1?",
            options=(
                "11 October 2027",
                "May 2024, at the same time as the US",
                "December 2026",
                "August 2026",
            ),
            answer_index=0,
            explanation=(
                "The US moved in May 2024; December 2026 is the T+0 allocations and confirmations "
                "milestone; August 2026 is when EU AI Act obligations begin to bite. Knowing which "
                "date is which is what lets you tell a client their confirmation deadline arrives "
                "first."
            ),
        ),
        TestQuestion(
            prompt="Why does T+1 break manual workflows rather than merely compress them?",
            options=(
                "It removes about half the processing window, and up to 80% for cross-border",
                "It increases trade volumes beyond what spreadsheets can hold",
                "It requires a new messaging protocol that replaces FIX",
                "It imposes penalties that make manual processing uneconomic",
            ),
            answer_index=0,
            explanation=(
                "The SWIFT Institute's estimate of up to 80% applies once time zones and FX are "
                "accounted for. A process that needs a human overnight has nowhere to put the "
                "human — that is a break, not a squeeze."
            ),
        ),
        TestQuestion(
            prompt=(
                "According to the curriculum, what is now the primary throttle on AI in production?"
            ),
            options=(
                "Fragmented, poorly governed data estates",
                "Model sophistication",
                "The cost of GPU capacity",
                "A shortage of quantitative engineers",
            ),
            answer_index=0,
            explanation=(
                "The constraint moved. A large share of agentic initiatives are at risk of "
                "underperforming without clean, lineage-aware foundations — which is why the sale "
                "is the foundation rather than the model."
            ),
        ),
        TestQuestion(
            prompt="What is the 'why now beats why us' field note instructing you to do?",
            options=(
                "Open with the dated catalyst, and let capability arrive second",
                "Open with the strongest differentiator before a competitor frames the deal",
                "Compress the sales cycle by asking for a decision date at first contact",
                "Lead with references from firms the buyer already respects",
            ),
            answer_index=0,
            explanation=(
                "'Why us' is a claim the buyer has heard from four vendors and cannot adjudicate. "
                "'Why now' is a fact about their world they can verify independently, and it is "
                "what creates the budget conversation."
            ),
        ),
        TestQuestion(
            prompt="How far back from a dated milestone does the curriculum say to work?",
            options=(
                "Nine to twelve months",
                "One full quarter",
                "Three to four months",
                "Two years, matching the budget cycle",
            ),
            answer_index=0,
            explanation=(
                "The renewal date is public information; working back nine to twelve months is "
                "what "
                "puts you in the conversation before a process exists. If the resulting month has "
                "already passed, you have learned something more useful than a forecast."
            ),
        ),
        TestQuestion(
            prompt="Which catalyst does the curriculum treat as inevitable rather than dated?",
            options=(
                "The incumbent's outage during a volatile, bursty session",
                "A leadership change at the client",
                "The next round of vendor consolidation",
                "An M&A event in the client's sector",
            ),
            answer_index=0,
            explanation=(
                "The others are real triggers but genuinely uncertain. The outage is treated as a "
                "when: the instruction is to be the credible, present voice in the account "
                "beforehand, because the call goes to whoever is already trusted."
            ),
        ),
    ),
    pass_mark=0.8,
)


def section_2() -> CourseModule:
    """Section 2: the seven forces, and the calendar to work backwards from."""
    return CourseModule(
        id=_id("module", "the-battlefield"),
        title="The battlefield: the forces that thaw a frozen budget",
        order=1,
        lessons=(
            Lesson(
                id=_id("lesson", "the-battlefield"),
                title="Seven forces, three dates, and the discipline of arriving early",
                body=_S2_BODY,
                order=0,
                author=LessonAuthor.HUMAN,
                slides=_SECTION_2_SLIDES,
                references=(CURRICULUM,),
                drill_topics=("doctrine:trigger-events",),
                measurement=(
                    "You hold a ten-account trigger watchlist with incumbent, renewal date, "
                    "governing force and earliest milestone, and one catalyst-led opening drafted "
                    "for the account whose milestone lands first."
                ),
            ),
        ),
        section_test=SECTION_2_TEST,
    )


# ==========================================================================================
# Section 3 — The armoury: sixteen methodologies, grouped by what they do
# ==========================================================================================

_S3_BODY = (
    "By the end of this lesson you can navigate the armoury by purpose rather than by name, say "
    "what each of the sixteen methodologies is actually for, and give the capital-markets cut of "
    "at "
    "least one from every group. The armoury is deliberately wide. The curriculum is explicit "
    "about "
    "why: not so that you use everything, but so that you choose with knowledge. Section 4 will "
    "ask "
    "you to select one and commit to it, and that choice is worthless if the field was never "
    "surveyed."
)

_SECTION_3_SLIDES: tuple[Slide, ...] = (
    _s(
        0,
        SlideKind.CONCEPT,
        "A method is only a tool",
        "The framing that governs this whole section: a method is only a tool, and it becomes a "
        "weapon when you choose it deliberately and define the formula for how it wins. Everything "
        "below is therefore inventory, not instruction. You are not being taught sixteen "
        "methodologies to run; you are being shown a field so that section 4's selection is made "
        "with knowledge rather than by habit or by whatever your last employer trained.",
        refs=(CURRICULUM,),
    ),
    _s(
        1,
        SlideKind.CONCEPT,
        "Organised by purpose, not by fame",
        "The armoury is grouped by what you are trying to do: diagnose, reframe, prove value, "
        "control the deal, navigate the committee, create timing. That grouping is the section's "
        "main contribution, because a flat list of sixteen names reads as noise and a grouped one "
        "is selectable. When a deal is stuck, you do not need 'a methodology' — you need to know "
        "which of those six jobs is not being done.",
        asset=_diagram(
            "the_armoury",
            "The armoury, grouped by the job you need it to do.",
            "A six-cell grid. Top row: Discovery and diagnosis, holding SPIN, Solution, Conceptual "
            "and Gap Selling; Insight and reframing, holding Challenger, Provocation-Based Selling "
            "and Command of the Message; Value and economics, holding Value or ROI Selling and the "
            "Mutual Action Plan. Bottom row: Qualification and deal control, holding MEDDIC or "
            "MEDDPICC, Sandler and NEAT or SNAP; Committee and account, holding the Miller Heiman "
            "Blue Sheet and Target Account Selling; Timing and presence, holding Social and "
            "Digital "
            "Selling and the Timing Layer.",
        ),
        refs=(CURRICULUM,),
    ),
    _s(
        2,
        SlideKind.CONCEPT,
        "Discovery and diagnosis: SPIN",
        "Neil Rackham's research across more than 35,000 calls found that in complex sales the "
        "buyer talks themselves into change through a sequence: Situation, Problem, Implication, "
        "Need-payoff. The curriculum names the weapon precisely — it is the Implication question, "
        "because that is the one that makes the cost of the problem felt. Situation questions "
        "gather; Implication questions hurt.",
        refs=(CURRICULUM,),
    ),
    _s(
        3,
        SlideKind.CONCEPT,
        "SPIN, in capital markets",
        "The capital-markets cut is specific: use Implication questions to make a 4-millisecond "
        "latency spike, or a future T+0 confirmation failure, viscerally expensive before you "
        "propose anything. 'How often does that happen?' is a Situation question. 'What does an "
        "unresolved break cost you when there is no overnight window to clear it?' is the weapon, "
        "and the buyer's own answer is the business case.",
        refs=(CURRICULUM,),
    ),
    _s(
        4,
        SlideKind.CONCEPT,
        "Discovery and diagnosis: Solution, Conceptual, Gap",
        "Three more. Mike Bosworth's Solution Selling: diagnose before you prescribe, and never "
        "pitch the same package twice. Conceptual or Consultative Selling: sell to the buyer's "
        "concept of their problem, not your product's feature set. Keenan's Gap Selling: quantify "
        "the distance between current and future state, because urgency is a function of the size "
        "of the gap made explicit.",
        refs=(CURRICULUM,),
    ),
    _s(
        5,
        SlideKind.CONCEPT,
        "Those three, in capital markets",
        "Solution Selling: configure to the firm's specific post-trade gap or data-lineage problem "
        "rather than running a standard product tour. Conceptual: map your proposal onto the CRO's "
        "mental model of capital efficiency, or the COO's model of operational leverage. Gap: size "
        "the operational gap the settlement squeeze opens — half the processing time, double the "
        "exception risk — and price the future state against it.",
        refs=(CURRICULUM,),
    ),
    _s(
        6,
        SlideKind.CONCEPT,
        "Insight and reframing: the Challenger Sale",
        "Dixon and Adamson: teach, tailor, take control. Lead with a commercial insight that "
        "reframes how the buyer sees their own world. The curriculum cites the research finding "
        "that roughly 40% of top performers in complex sales are Challengers — the largest share "
        "of "
        "any profile. That statistic is why this is the most-reached-for weapon in the armoury, "
        "and "
        "section 4 will warn you about exactly that.",
        refs=(CURRICULUM,),
    ),
    _s(
        7,
        SlideKind.CONCEPT,
        "Challenger, in capital markets",
        "Teach the Head of Trading a cost they have not measured. Reframe a 'UI modernisation' as "
        "a "
        "core-infrastructure problem. Note the shape of both examples: the Challenger move is not "
        "disagreeing with the buyer, it is showing them a different unit of account. The buyer who "
        "was budgeting for a front-end refresh is not wrong about their front end; they are "
        "measuring the wrong thing.",
        refs=(CURRICULUM,),
    ),
    _s(
        8,
        SlideKind.CONCEPT,
        "Insight and reframing: Provocation, and Command of the Message",
        "Provocation-Based Selling is the sharper cousin of Challenger: arrive with a contrarian "
        "thesis that disrupts the buyer's current plan, backed by evidence. Force Management's "
        "Command of the Message is the discipline of situational fluency, a differentiated value "
        "narrative and genuine urgency — sell the value, never the feature list. One is a strike; "
        "the other is a standard of preparation.",
        refs=(CURRICULUM,),
    ),
    _s(
        9,
        SlideKind.EXAMPLE,
        "A provocation, written out",
        "The curriculum's own example, worth reading as a sentence you could actually say: 'Your "
        "modernisation roadmap is backwards — you are refreshing the front-end on a core that "
        "cannot meet the 2027 deadline.' Notice it names their plan, states the flaw, and anchors "
        "to a date they cannot argue with. Without that last element it is an opinion, and a "
        "provocation that is only an opinion is bravado.",
        refs=(CURRICULUM,),
    ),
    _s(
        10,
        SlideKind.CONCEPT,
        "Value and economics: ROI Selling",
        "Build the quantified business case in the buyer's own units and let the economics carry "
        "the decision. 'Their own units' is the operative phrase and it is where most attempts "
        "fail: a percentage improvement is your unit, and basis points of slippage are theirs. If "
        "the buyer has to translate your number before they can use it internally, you have handed "
        "them work rather than a case.",
        refs=(CURRICULUM,),
    ),
    _s(
        11,
        SlideKind.CONCEPT,
        "The units, named",
        "The curriculum lists them: basis points of slippage, dollars-per-day of funding drag, "
        "CSDR penalty exposure, and FTEs consumed by exception management — which ran to "
        "two-thirds "
        "of some firms' transition costs. Learn these four. They are the vocabulary in which a "
        "capital-markets business case is written, and a seller who cannot use them is asking the "
        "buyer to do the translation.",
        refs=(CURRICULUM,),
    ),
    _s(
        12,
        SlideKind.CONCEPT,
        "Value and economics: the Mutual Action Plan",
        "A jointly owned, reverse-engineered close plan with dates, owners and dependencies. It "
        "converts a vague pipeline into a shared commitment. The capital-markets cut is the part "
        "that makes it work: reverse-engineer the plan from the buyer's own hard deadline — the "
        "December 2026 T+0 confirmation milestone — so the timeline is theirs rather than yours. A "
        "plan built from your quarter-end is a plan they will not defend.",
        refs=(CURRICULUM,),
    ),
    _s(
        13,
        SlideKind.CONCEPT,
        "Qualification and deal control: MEDDIC and MEDDPICC",
        "The enterprise inspection discipline: Metrics, Economic buyer, Decision criteria, "
        "Decision "
        "process, (Paper process), Identify pain, Champion, (Competition). Built for complex, "
        "multi-stakeholder deals. The curriculum cites Korn Ferry's finding that organisations "
        "with "
        "a consistent formal methodology see materially higher win rates — the consistency being "
        "the active ingredient, more than the particular letters.",
        refs=(CURRICULUM,),
    ),
    _s(
        14,
        SlideKind.CONCEPT,
        "Qualification and deal control: Sandler, NEAT, SNAP",
        "Sandler: mutual qualification through up-front contracts, a willingness to disqualify, "
        "and "
        "the buyer doing most of the talking. NEAT — Need, Economic impact, Access to authority, "
        "Timeline — for fast qualification. SNAP — keep it Simple, be iNvaluable, Align, raise "
        "Priorities — for overloaded buyers. The cuts: SNAP for a Head of Operations drowning in a "
        "T+1 programme; NEAT to triage the scramble of 23/5-readiness inbound.",
        refs=(CURRICULUM,),
    ),
    _s(
        15,
        SlideKind.CONCEPT,
        "Committee and account: the Blue Sheet",
        "Miller Heiman Strategic Selling maps every buying influence — economic, user, technical, "
        "coach — with their win-results and your standing with each. The curriculum calls it the "
        "canonical tool for orchestrating a large committee, and the default operating system for "
        "an eight-figure platform deal across PM, quant, architecture, risk and procurement. "
        "Section 6 is built on it, so this is the entry you will use most.",
        refs=(CURRICULUM,),
    ),
    _s(
        16,
        SlideKind.CONCEPT,
        "Committee and account: Target Account Selling",
        "Treat a named account as the unit of work, not a lead. Orchestrate a coordinated, "
        "multi-threaded campaign across the whole buying group. The capital-markets cut is a "
        "sentence worth arguing with your manager about: a Tier-1 bank is an account to be "
        "campaigned over quarters, not a lead to be worked in a week. Your CRM probably disagrees, "
        "and the curriculum's position is that the CRM is wrong.",
        refs=(CURRICULUM,),
    ),
    _s(
        17,
        SlideKind.CONCEPT,
        "Timing and presence: Social and Digital Selling",
        "Build presence and credibility in the places buyers research, long before a deal exists, "
        "so you are already known and trusted when one appears. In capital markets: be a "
        "recognised "
        "voice on T+1 readiness and post-trade automation, on the platforms and at the conferences "
        "where operations and risk leaders actually gather. This is unglamorous, slow, and the "
        "direct input to section 7's engineered luck.",
        refs=(CURRICULUM,),
    ),
    _s(
        18,
        SlideKind.CONCEPT,
        "Timing and presence: the Timing Layer, and why it is different",
        "Read this one twice. Every methodology above improves what happens *inside* a "
        "conversation. None tells you which conversation to be in, or when. The curriculum's "
        "judgement is that the discipline of watching trigger events decides where most revenue is "
        "actually won. That makes the Timing Layer not one of sixteen options but the layer the "
        "other fifteen sit on, which is why section 2 came before this one.",
        refs=(CURRICULUM,),
    ),
    _s(
        19,
        SlideKind.EXAMPLE,
        "Choosing badly: the same account, three wrong weapons",
        "A quant asks how the data is normalised, and receives a Challenger insight about "
        "unmeasured cost — irrelevant to them, and slightly insulting. A CRO is shown a working "
        "prototype — impressive, and unusable without an auditable control story. Procurement is "
        "given a provocation about their roadmap — they do not own the roadmap. Three good "
        "weapons, "
        "three disqualifications, one seller who will report that the deal 'went quiet'.",
        refs=(CURRICULUM,),
    ),
    _s(
        20,
        SlideKind.CHECKPOINT,
        "Audit your own armoury",
        "Go through all sixteen and mark each: *use regularly*, *know but never use*, *do not "
        "know*. "
        "Be strict — 'know' means you could explain its capital-markets cut to a colleague without "
        "notes. Most experienced sellers find they regularly use two or three and have never "
        "deliberately chosen any of them. That result is the point of the exercise, not a failure "
        "of it.",
        checkpoint="Mark all sixteen methodologies as use / know / do not know.",
        refs=(CURRICULUM,),
    ),
    _s(
        21,
        SlideKind.CHECKPOINT,
        "Find your missing group",
        "Look at your audit by group rather than by name. Which of the six purposes — diagnose, "
        "reframe, prove value, control the deal, navigate the committee, create timing — has no "
        "entry you use regularly? That gap is a prediction about how your deals fail, and it is "
        "usually accurate. Write down the group, and the last deal you lost in a way that matches "
        "it.",
        checkpoint="Name your weakest of the six groups, and a loss that fits it.",
        refs=(CURRICULUM,),
    ),
    _s(
        22,
        SlideKind.CHECKPOINT,
        "Write one capital-markets cut in your own words",
        "Pick any methodology you marked 'know but never use' and write its capital-markets cut in "
        "one sentence, in your own words, for an account on your watchlist from section 2. Not the "
        "curriculum's example — yours, with a real firm and a real constraint. This is the "
        "smallest "
        "possible rehearsal of the selection you make in the next section.",
        checkpoint="Write one methodology's capital-markets cut for a named account of your own.",
        refs=(CURRICULUM,),
    ),
    _s(
        23,
        SlideKind.CONCEPT,
        "What happens next",
        "You now have the field. Section 4 takes the first two convictions — that revenue is "
        "zero-sum, and that a generalist is forgettable — and asks you to convert this survey into "
        "a single choice. The curriculum is blunt about what that costs: choosing forecloses "
        "options, and that foreclosure is the whole point. Come to the next section having done "
        "the "
        "audit, or the choice will be made from habit.",
        refs=(CURRICULUM,),
    ),
)

SECTION_3_TEST = SectionTest(
    questions=(
        TestQuestion(
            prompt="Within SPIN, which question type does the curriculum identify as the weapon?",
            options=(
                "Implication — it makes the cost of the problem felt",
                "Situation — it establishes the facts the rest depends on",
                "Problem — it surfaces the dissatisfaction",
                "Need-payoff — it lets the buyer state the value themselves",
            ),
            answer_index=0,
            explanation=(
                "All four are part of the sequence, but Implication is the one that converts a "
                "known problem into a felt cost. 'How often does that happen' gathers; 'what does "
                "an unresolved break cost you with no overnight window' is the weapon."
            ),
        ),
        TestQuestion(
            prompt="What makes the Timing Layer different from the other fifteen entries?",
            options=(
                "The others improve what happens inside a conversation; it decides which "
                "conversation you are in",
                "It is the only one with published research behind it",
                "It applies to exchanges but not to brokers or wealth managers",
                "It replaces qualification once a trigger has been identified",
            ),
            answer_index=0,
            explanation=(
                "That is why it is a layer the other fifteen sit on rather than a sixteenth "
                "option, "
                "and why section 2's battlefield came before this section's armoury."
            ),
        ),
        TestQuestion(
            prompt="Which four units does the curriculum name for a capital-markets business case?",
            options=(
                "Basis points of slippage, dollars-per-day funding drag, CSDR penalty exposure, "
                "FTEs on exceptions",
                "Total cost of ownership, payback period, net present value, internal rate of "
                "return",
                "Licence cost, implementation cost, training cost, support cost",
                "Latency, throughput, uptime, mean time to recovery",
            ),
            answer_index=0,
            explanation=(
                "The second set is generic finance and the fourth is engineering. The point of ROI "
                "Selling is the buyer's own units — FTEs consumed by exception management ran to "
                "two-thirds of some firms' T+1 transition costs, which is a number they already "
                "track."
            ),
        ),
        TestQuestion(
            prompt="What does the capital-markets cut of the Mutual Action Plan insist on?",
            options=(
                "Reverse-engineering the plan from the buyer's own hard deadline, so the timeline "
                "is theirs",
                "Securing a signed commitment before technical validation begins",
                "Assigning every action to a named owner on the vendor side",
                "Aligning the close date with the vendor's quarter end",
            ),
            answer_index=0,
            explanation=(
                "The December 2026 T+0 confirmation milestone is the buyer's deadline, not yours. "
                "A "
                "plan built from your quarter end is one they will not defend internally when it "
                "comes under pressure."
            ),
        ),
        TestQuestion(
            prompt="Why is the armoury deliberately wide?",
            options=(
                "So you choose with knowledge, not so you use everything",
                "So a seller can match a different methodology to each quarter",
                "Because no single methodology has been shown to outperform",
                "So the course covers what any previous employer might have trained",
            ),
            answer_index=0,
            explanation=(
                "The curriculum says so directly. Section 4 then asks for a single selection — and "
                "a choice made without surveying the field is habit, which is exactly what the "
                "doctrine is trying to interrupt."
            ),
        ),
        TestQuestion(
            prompt=(
                "A quant asks how your data is normalised and you respond with a Challenger "
                "insight "
                "about an unmeasured cost. What has happened?"
            ),
            options=(
                "A disqualification: the right weapon aimed at the wrong stakeholder",
                "A reframe: the quant has been shown a better unit of account",
                "A qualification step: the quant's reaction reveals the decision criteria",
                "Nothing yet, provided the economic buyer hears the insight later",
            ),
            answer_index=0,
            explanation=(
                "Challenger is a strong weapon and irrelevant here — a quant responds to a "
                "working, "
                "tailored prototype. The seller will usually record this as the deal going quiet."
            ),
        ),
    ),
    pass_mark=0.8,
)


def section_3() -> CourseModule:
    """Section 3: the armoury, grouped by purpose."""
    return CourseModule(
        id=_id("module", "the-armoury"),
        title="The armoury: sixteen methodologies, grouped by what they do",
        order=2,
        lessons=(
            Lesson(
                id=_id("lesson", "the-armoury"),
                title="Survey the field before you choose your one weapon",
                body=_S3_BODY,
                order=0,
                author=LessonAuthor.HUMAN,
                slides=_SECTION_3_SLIDES,
                references=(CURRICULUM,),
                drill_topics=("doctrine:armoury",),
                measurement=(
                    "You have audited all sixteen methodologies as use / know / do not know, named "
                    "the group you have no regular entry in, and written one capital-markets cut "
                    "in "
                    "your own words for a named account."
                ),
            ),
        ),
        section_test=SECTION_3_TEST,
    )


# ==========================================================================================
# Section 4 — Convictions I and II: the zero-sum pipeline, and your one weapon
# ==========================================================================================

_S4_BODY = (
    "By the end of this lesson you can argue the zero-sum claim on its evidence rather than its "
    "tone, name your own signature weapon, and write the formula under which it wins. These are "
    "the "
    "first two of the eight convictions and they are the two the curriculum treats as hardest — "
    "the "
    "first because it asks you to admit comfort made you passive, the second because choosing one "
    "weapon forecloses the others, and the foreclosure is the point."
)

_SECTION_4_SLIDES: tuple[Slide, ...] = (
    _s(
        0,
        SlideKind.CONCEPT,
        "Conviction I: 'We do not wait for budget. We take it.'",
        "The first conviction, in the curriculum's words. Enterprise revenue is zero-sum and there "
        "is no neutral outcome. Every budget is finite, every mandate contested, and a contract "
        "you "
        "do not win is not one that stays open — it is one a competitor closes, often for three to "
        "five years, financing their roadmap with money that should have been yours. Read it as an "
        "accounting statement, not a rallying cry.",
        refs=(CURRICULUM, DECK_01),
    ),
    _s(
        1,
        SlideKind.CONCEPT,
        "The fact, and the consequence",
        "The deck separates the two, and the separation is worth keeping. The fact: every budget "
        "is "
        "finite and contested, and a multi-year contract won by a rival removes that spend for "
        "years. The consequence: there is no neutral outcome, so the deal you decline to pursue "
        "quietly funds someone else's roadmap. The first is verifiable. The second follows from it "
        "whether or not you find it comfortable.",
        refs=(DECK_01,),
    ),
    _s(
        2,
        SlideKind.CONCEPT,
        "Three to five years",
        "The number the deck puts on the board: three to five years is how long a competitor's win "
        "locks you out of an account. That is the whole argument for urgency compressed into a "
        "figure. A deal lost in 2026 is an account you cannot meaningfully sell into until 2030, "
        "which means the cost of a loss is never the deal — it is the deal plus every cycle inside "
        "the contract term.",
        refs=(DECK_01,),
    ),
    _s(
        3,
        SlideKind.CONCEPT,
        "Why capital markets is the purest case",
        "Core systems — order and execution management, market-data feeds, real-time risk and "
        "collateral engines, settlement and surveillance platforms — carry switching costs in the "
        "millions and contracts measured in years. When a Tier-1 bank signs multi-year with a "
        "competitor, that budget is gone and your access to the account is frozen for the life of "
        "the contract. Few markets make the zero-sum claim as literally true.",
        refs=(CURRICULUM,),
    ),
    _s(
        4,
        SlideKind.CONCEPT,
        "The passivity trap, precisely stated",
        "'The placeholder calls this the market. The principal calls it a position.' The trap is "
        "not laziness — activity stays high. It is the substitution of administering a territory "
        "for choosing targets, and its tell is linguistic: a seller in the trap describes outcomes "
        "in the passive voice. The deal slipped. The budget moved. The relationship cooled. Nobody "
        "did any of those things.",
        refs=(CURRICULUM, DECK_01),
    ),
    _s(
        5,
        SlideKind.CONCEPT,
        "The discipline: own the number, move first, decide",
        "Three moves from the deck. Own the number: measure yourself by outcomes held, not "
        "activity "
        "logged, and author it before anyone assigns it. Move first: create the reason to engage "
        "before the RFP exists, on your timeline. Decide: hesitation dressed up as politeness is "
        "how capable sellers quietly disappear. The third is the one experienced sellers resist, "
        "because it looks like recklessness from the inside.",
        refs=(DECK_01,),
    ),
    _s(
        6,
        SlideKind.CONCEPT,
        "What to measure instead",
        "The deck replaces activity metrics with four: accounts pursued versus merely covered; "
        "conversations you initiated rather than received; budget displaced from a competitor onto "
        "your roadmap; and decision-makers reached directly rather than through a gatekeeper. "
        "Every "
        "one of them is harder to report and impossible to inflate, which is the point. Motion is "
        "easy to log; territory is not.",
        refs=(DECK_01,),
    ),
    _s(
        7,
        SlideKind.EXAMPLE,
        "The drill from the deck, worked",
        "Reclaim one account, this week. Choose one you have been passively covering — served by a "
        "competitor or simply stagnating. Find the friction: one specific, costly problem the "
        "incumbent is not solving, such as latency, settlement risk or manual reconciliation. "
        "Build "
        "the reason: one tailored insight that makes engagement worth their time. Then reach the "
        "economic buyer ahead of any process.",
        refs=(DECK_01, CURRICULUM),
    ),
    _s(
        8,
        SlideKind.CONCEPT,
        "The three field notes for conviction I",
        "Worth memorising. The renewal date is public information; work backwards from it by nine "
        "to twelve months. 'Why now' beats 'why us' — lead with the catalyst, not the capability. "
        "And the test of whether you have a thesis at all: if you cannot name the incumbent and "
        "their weakness, you do not yet have one. That third note disqualifies most of what "
        "sellers "
        "call pipeline.",
        refs=(CURRICULUM,),
    ),
    _s(
        9,
        SlideKind.CONCEPT,
        "Conviction II: 'A generalist is forgettable. Choose one weapon.'",
        "The second conviction has two halves. First, a method is only a tool; it becomes a weapon "
        "at the moment you define the formula for how it wins — the buyer it is built for, the "
        "opening it exploits, the proof it carries, the close it forces. Until then it is "
        "potential, not power. Second, the generalist — fluent in everything, decisive about "
        "nothing — has no real value to a deal.",
        refs=(CURRICULUM, DECK_02),
    ),
    _s(
        10,
        SlideKind.CONCEPT,
        "Tool, weapon, formula",
        "The distinction collapses the moment you write it as a sentence, which is why the deck "
        "draws it. A tool is a methodology you happen to know. A weapon is that tool chosen "
        "deliberately as your one edge. A formula is the repeatable equation for when and how it "
        "wins. Most sellers have tools and believe they have weapons; the test is whether they can "
        "state the formula.",
        asset=_diagram(
            "tool_to_weapon",
            "The three stages, from Lesson 02 of the authored deck.",
            "Three panels connected by arrows. First, in a plain panel numbered 01: TOOL, a "
            "methodology you happen to know. Second, numbered 02 in a pale green panel: WEAPON, "
            "that tool chosen deliberately as your one edge. Third, numbered 03 in a dark green "
            "panel: FORMULA, the repeatable equation for when and how it wins. Beneath all three, "
            "the formula's shape stated as a sentence: when I do X to buyer Y, I produce outcome "
            "Z, "
            "labelled a formula, not a feature list.",
        ),
        refs=(DECK_02,),
    ),
    _s(
        11,
        SlideKind.CONCEPT,
        "Why range is not an edge",
        "The passive seller has become a generalist by default: available, likeable, easy to deal "
        "with, and quietly mistaking those for an edge. The curriculum's verdict is flat — they "
        "are "
        "not an edge, they are the price of entry. The market does not reward range; it rewards "
        "the "
        "seller who is undeniable at one thing. Range is comforting and invisible; an edge is "
        "uncomfortable and memorable.",
        refs=(CURRICULUM, DECK_02),
    ),
    _s(
        12,
        SlideKind.CONCEPT,
        "The three archetypal weapons",
        "The Relationship weapon converts trust into the internal political leverage needed to "
        "unseat a multi-year incumbent — in institutional finance, trust is capital, and you win "
        "not because they like you but because your standing earns you leverage. The Challenger "
        "weapon confronts the buyer with a cost they had not measured. The Demo weapon drops a "
        "sanitised snapshot of the buyer's own messy workflow into a working prototype.",
        refs=(DECK_02, CURRICULUM),
    ),
    _s(
        13,
        SlideKind.CONCEPT,
        "Match the weapon to the buyer",
        "The curriculum is specific about who each lands on. A Head of Trading responds to a "
        "quantified Challenger insight. A quant responds to a working, tailored prototype. A CRO "
        "responds to trust earned over time and a hard regulatory justification. The egoist is not "
        "equally good at all three — the egoist is famous for one, and knows which rooms to bring "
        "a "
        "colleague into.",
        refs=(CURRICULUM,),
    ),
    _s(
        14,
        SlideKind.CONCEPT,
        "The fidelity gap",
        "Every weapon has a way it fails, and the deck names the failure mode: the distance "
        "between "
        "what your weapon promises and what survives scrutiny. A demo that dazzles the front end "
        "and collapses under the CTO's questions on data lineage, SOC 2 and security kills the "
        "deal. Relationship without a formula is a fluke. A Challenger claim you cannot "
        "substantiate "
        "is bravado. Close the gap before you strike.",
        refs=(DECK_02,),
    ),
    _s(
        15,
        SlideKind.EXAMPLE,
        "A formula, written properly",
        "From the deck: 'When I reach a Head of Trading, I open with a quantified cost of their "
        "status quo — not a feature list.' Expand it to all four parts for your own use: the buyer "
        "(Head of Trading at a mid-tier broker), the opening (a cost they do not currently "
        "measure), the proof (their own volumes in a shadow-mode comparison), and the close (a "
        "mutual action plan reverse-engineered from their confirmation deadline).",
        refs=(DECK_02,),
    ),
    _s(
        16,
        SlideKind.EXAMPLE,
        "The same weapon, two fidelity outcomes",
        "Two sellers run the Demo weapon into the same asset manager. The first shows a polished "
        "dashboard on synthetic data and is asked, in week three, for lineage evidence they do not "
        "have; the deal dies in evaluation. The second shows a rougher prototype on a sanitised "
        "extract of the client's own reconciliation file, and answers the lineage question in the "
        "same breath. Same weapon, opposite fidelity.",
        refs=(DECK_02,),
    ),
    _s(
        17,
        SlideKind.CHECKPOINT,
        "Reclaim one account",
        "Run conviction I's drill for real. Name the account, the incumbent, the specific friction "
        "the incumbent is not solving, and the one tailored insight that earns you the meeting. "
        "Then name the economic buyer and the date you will reach them. If you cannot name the "
        "incumbent and their weakness, the field note applies: you do not have a thesis yet, and "
        "the first task is research rather than outreach.",
        checkpoint=(
            "Name the account, incumbent, friction, insight, economic buyer and contact date."
        ),
        refs=(DECK_01, CURRICULUM),
    ),
    _s(
        18,
        SlideKind.CHECKPOINT,
        "Name your weapon",
        "From the section 3 audit, commit to one. Relationship, Challenger, Demo, or a sharpened "
        "named methodology. The curriculum asks you to be honest about where you are already "
        "dangerous rather than aspirational about where you would like to be, and to commit "
        "publicly — to your manager — because a private commitment to a single weapon is one you "
        "will quietly abandon at the first unsuitable deal.",
        checkpoint="Commit to one signature weapon, and tell your manager.",
        refs=(DECK_02, CURRICULUM),
    ),
    _s(
        19,
        SlideKind.CHECKPOINT,
        "Write the formula",
        "One sentence: when I do X to buyer Y, I produce outcome Z. Then the three supporting "
        "answers — who it is lethal against (the exact buyer and the exact moment it lands "
        "hardest), what proof it requires, and what close it forces. Specific enough to repeat is "
        "the standard; if a colleague could not run it from your sentence, it is a description "
        "rather than a formula.",
        checkpoint="Write your weapon's formula in one sentence, plus buyer, proof and close.",
        refs=(DECK_02,),
    ),
    _s(
        20,
        SlideKind.CHECKPOINT,
        "Decline one deal on purpose",
        "The curriculum's sharpest drill, and the one most sellers skip. Decline, deliberately, "
        "one "
        "deal that does not suit your weapon — and notice how it sharpens your focus. Mastery, in "
        "the curriculum's terms, is the willingness to disqualify deals your weapon does not fit. "
        "Record which deal, and what you did with the time instead.",
        checkpoint="Name the deal you declined and what the freed time went to.",
        refs=(CURRICULUM,),
    ),
    _s(
        21,
        SlideKind.CONCEPT,
        "The test of whether it worked",
        "The field note is a good one: your weapon should be nameable by your clients, not just by "
        "you. If a client could not tell a colleague what you are unusually good at, you have "
        "chosen a weapon in a document rather than in the market. That takes a quarter or two to "
        "become true, which is why the commitment is quarterly rather than per-deal.",
        refs=(CURRICULUM,),
    ),
    _s(
        22,
        SlideKind.CONCEPT,
        "Where this goes next",
        "Conviction III turns a single win into a machine, and conviction IV sends you at the "
        "prospect you have been avoiding. Both assume you have done the work here: reproducibility "
        "has nothing to reproduce until you have a formula, and the hardest prospect is where a "
        "formula gets stress-tested. Do not read on with the weapon unchosen.",
        refs=(CURRICULUM,),
    ),
)

SECTION_4_TEST = SectionTest(
    questions=(
        TestQuestion(
            prompt="What does the deck give as the cost of a competitor's win?",
            options=(
                "Three to five years of lock-out from the account",
                "One budget cycle, after which the account reopens",
                "The deal value plus the cost of re-engaging later",
                "Nothing durable, if the relationship is maintained",
            ),
            answer_index=0,
            explanation=(
                "That figure is the whole argument for urgency in one number: a deal lost in 2026 "
                "is an account you cannot meaningfully sell into until 2030, so the cost of a loss "
                "is the deal plus every cycle inside the contract term."
            ),
        ),
        TestQuestion(
            prompt="What is the tell of a seller in the passivity trap?",
            options=(
                "They describe outcomes in the passive voice: the deal slipped, the budget moved",
                "Their activity levels fall away over successive quarters",
                "They resist adopting any formal sales methodology",
                "They over-forecast consistently at quarter end",
            ),
            answer_index=0,
            explanation=(
                "Activity stays high in the trap, which is what makes it hard to see from the "
                "inside. The language is the giveaway: nobody did any of those things."
            ),
        ),
        TestQuestion(
            prompt="What turns a tool into a weapon?",
            options=(
                "Defining the formula for how it wins: the buyer, opening, proof and close",
                "Using it consistently across a full quarter",
                "Being trained and certified in it",
                "Choosing the one with the strongest published win-rate evidence",
            ),
            answer_index=0,
            explanation=(
                "Until the formula is written the method is potential, not power. The test is "
                "whether a colleague could run your play from your sentence."
            ),
        ),
        TestQuestion(
            prompt="What is the fidelity gap?",
            options=(
                "The distance between what your weapon promises and what survives scrutiny",
                "The gap between the client's current state and their target state",
                "The difference between your demo environment and their production data",
                "The delay between a trigger firing and your first contact",
            ),
            answer_index=0,
            explanation=(
                "The second is Gap Selling and the fourth is section 7's time-to-first-contact. "
                "The "
                "fidelity gap is why a dazzling front-end demo dies under the CTO's questions on "
                "lineage, SOC 2 and security."
            ),
        ),
        TestQuestion(
            prompt="Which buyer does the curriculum match to a working, tailored prototype?",
            options=(
                "The quant",
                "The Head of Trading",
                "The CRO",
                "Procurement",
            ),
            answer_index=0,
            explanation=(
                "The Head of Trading responds to a quantified Challenger insight, and the CRO to "
                "trust earned over time plus a hard regulatory justification. Bringing the wrong "
                "one is the disqualification from section 1."
            ),
        ),
        TestQuestion(
            prompt="In the curriculum's terms, what is mastery of a weapon?",
            options=(
                "The willingness to disqualify deals your weapon does not fit",
                "The ability to run all three archetypal weapons equally well",
                "Winning a majority of the deals in which you deploy it",
                "Being able to train a colleague to use it",
            ),
            answer_index=0,
            explanation=(
                "Hence the drill of deliberately declining one unsuitable deal. The egoist is not "
                "equally good at all three weapons — the egoist is famous for one."
            ),
        ),
    ),
    pass_mark=0.8,
)


def section_4() -> CourseModule:
    """Section 4: convictions I and II."""
    return CourseModule(
        id=_id("module", "convictions-1-2"),
        title="Convictions I and II: the zero-sum pipeline, and your one weapon",
        order=3,
        lessons=(
            Lesson(
                id=_id("lesson", "convictions-1-2"),
                title="Take the budget, and be undeniable at one thing",
                body=_S4_BODY,
                order=0,
                author=LessonAuthor.HUMAN,
                slides=_SECTION_4_SLIDES,
                references=(CURRICULUM, DECK_01, DECK_02),
                drill_topics=("doctrine:zero-sum", "doctrine:signature-weapon"),
                measurement=(
                    "You have reclaimed one account with a named incumbent, friction and economic "
                    "buyer; committed publicly to one signature weapon; written its formula; and "
                    "declined one deal that does not fit it."
                ),
            ),
        ),
        section_test=SECTION_4_TEST,
    )


# ==========================================================================================
# Section 5 — Convictions III and IV: reproducibility, and the hardest prospect
# ==========================================================================================

_S5_BODY = (
    "By the end of this lesson you can decompose one of your own wins into a signature play, "
    "diagnose which term of the deal equation is dragging a live opportunity, and name the "
    "stakeholder you have been avoiding. Conviction III turns a win into a machine; conviction IV "
    "sends you at the deal that will build the capability you lack. Together they are the "
    "curriculum's answer to a seller who is good but inconsistent."
)

_SECTION_5_SLIDES: tuple[Slide, ...] = (
    _s(
        0,
        SlideKind.CONCEPT,
        "Conviction III: 'A win you cannot repeat is an accident.'",
        "The claim: a win you cannot explain is a win you cannot repeat, and a result you cannot "
        "repeat is not a skill, it is luck wearing a suit. Elite selling is an equation, not a "
        "performance. The curriculum ties this to how the firm treats technology — a one-off fix "
        "is "
        "worth little; a repeatable, compounding system is worth everything. The same standard is "
        "being applied to you.",
        refs=(CURRICULUM,),
    ),
    _s(
        1,
        SlideKind.CONCEPT,
        "The passivity trap here is a forecasting problem",
        "The passive seller coasts on the occasional hero deal — the quarter saved by a prospect "
        "who happened to love the product. They cannot explain why they won, so they cannot win "
        "that way again on purpose, and their forecast is a hope rather than a model. Awakening "
        "here is intellectual honesty: refusing to be carried by flukes, and insisting on "
        "understanding the mechanism well enough to reproduce it on command.",
        refs=(CURRICULUM,),
    ),
    _s(
        2,
        SlideKind.CONCEPT,
        "Why capital markets rewards reproducibility specifically",
        "Because the catalysts are shared. Dozens of regional brokers sit on the same legacy "
        "order-routing tool; scores of asset managers face the identical T+1 confirmation "
        "deadline; "
        "whole tiers of firms carry the same data-lineage debt now throttling their AI ambitions. "
        "A "
        "formula that wins once against a shared constraint can be run against every firm that "
        "shares it. This is where selling stops being art and becomes engineering.",
        refs=(CURRICULUM,),
    ),
    _s(
        3,
        SlideKind.CONCEPT,
        "The probability model",
        "Win probability rises with five things: the strength of the dated trigger you are riding, "
        "your access to the economic buyer, the differentiation of your insight, the fidelity of "
        "your proof, and the consensus you have built across the committee. It falls with the "
        "incumbent's switching cost. Six terms, and the curriculum's instruction is that every one "
        "is a lever rather than a given.",
        asset=_diagram(
            "the_deal_equation",
            "Five levers and one drag: diagnose the term that is binding.",
            "A row of five panels under a green heading reading RAISES WIN PROBABILITY: Trigger, "
            "the dated catalyst you are riding; Reach, access to the economic buyer; Insight, "
            "differentiation of your thesis; Proof, fidelity of what you can show; and Consensus, "
            "agreement across the committee. Below them, under a warm caution heading reading "
            "LOWERS IT, a single outlined panel: the incumbent's switching cost, millions in cost "
            "and contracts in years, with the note that absorbing it raises the odds. At the foot, "
            "in green: doubling your reach rate does as much as doubling your win rate.",
        ),
        refs=(CURRICULUM,),
    ),
    _s(
        4,
        SlideKind.CONCEPT,
        "Diagnose the binding term",
        "The practical instruction: a weak deal is rarely weak on all five. Diagnose which term is "
        "dragging and raise that one. This is the difference between working harder and working "
        "correctly — a deal short on consensus does not improve because you sharpen the insight, "
        "and a deal short on reach does not improve because you build better proof. Most sellers "
        "raise the term they are best at rather than the one that is binding.",
        refs=(CURRICULUM,),
    ),
    _s(
        5,
        SlideKind.CONCEPT,
        "The throughput model",
        "The scoring equation, and it contains the course's most counter-intuitive line: doubling "
        "your reach rate to the economic buyer does as much as doubling your win rate. And chasing "
        "more targets is the weakest lever if your reach and trigger-hit rates are low. The egoist "
        "tunes the coefficient that is actually binding rather than simply working harder across "
        "the board — which usually means fewer accounts, reached better.",
        refs=(CURRICULUM,),
    ),
    _s(
        6,
        SlideKind.CONCEPT,
        "The signature play: five fields",
        "Every documented win collapses into five fields: persona, trigger, insight, proof, close. "
        "Filled in, they become a play you can hand to your future self or a colleague and run "
        "again. The discipline is to fill them in from a real closed deal rather than from an "
        "ideal "
        "one, because the value is in what actually happened, including the parts that were "
        "accidental.",
        refs=(CURRICULUM,),
    ),
    _s(
        7,
        SlideKind.EXAMPLE,
        "The curriculum's worked play",
        "Head of Operations (persona) plus the December 2026 T+0 confirmation deadline (trigger) "
        "plus a quantified exception-rate and penalty model (insight) plus a shadow-mode "
        "reconciliation demo (proof) plus a mutual action plan reverse-engineered from the "
        "deadline "
        "(close). The curriculum adds the multiplier: attach the offering to a public, dated "
        "financial or regulatory goal and multi-thread to three executives, and the cycle "
        "compresses by roughly forty percent.",
        refs=(CURRICULUM,),
    ),
    _s(
        8,
        SlideKind.CONCEPT,
        "The weapons that make III work",
        "Three from the armoury. Win/loss reverse-engineering, to dissect closed deals into the "
        "five fields. Gap Selling and SPIN, to make the 'insight' variable repeatable and "
        "quantified rather than improvised. Value Selling and the Mutual Action Plan, to "
        "standardise 'proof' and 'close' across a segment. Note that the play is assembled from "
        "the "
        "armoury rather than replacing it.",
        refs=(CURRICULUM,),
    ),
    _s(
        9,
        SlideKind.CONCEPT,
        "The three field notes for conviction III",
        "If you cannot write the play down, you do not understand why you won. More targets is the "
        "weakest lever; reach and trigger-hit rates usually bind first. And a reusable proof asset "
        "— a shadow-mode demo — is worth more than a hundred slides. That last one is a budgeting "
        "instruction: build the asset once, properly, and run it across the tier that shares the "
        "constraint.",
        refs=(CURRICULUM,),
    ),
    _s(
        10,
        SlideKind.CONCEPT,
        "Conviction IV: 'Capability is forged under friction, never in comfort.'",
        "The seller who lives on easy, winnable deals does not stay sharp — they calcify at the "
        "level those deals demand and call it experience. Growth happens when your existing "
        "formula "
        "collides with real resistance and you are forced to build a new layer of skill simply to "
        "survive the deal. The conviction is to move toward the hardest prospect on purpose.",
        refs=(CURRICULUM,),
    ),
    _s(
        11,
        SlideKind.CONCEPT,
        "The trap: comfortable renewals",
        "The passive seller avoids hard deals, living in comfortable renewals and winnable "
        "mid-market opportunities. Because they are never stretched, they never grow; their skill "
        "set quietly ossifies at exactly the level the easy deals require. The awakening is to "
        "treat fear as a signal pointing toward growth rather than away from it — a compass rather "
        "than a warning.",
        refs=(CURRICULUM,),
    ),
    _s(
        12,
        SlideKind.CONCEPT,
        "The hardest rooms, named",
        "A CISO demanding evidence of data lineage. A CRO who will not move capital onto a system "
        "they cannot audit in real time. A compliance officer who needs every model explainable "
        "under the EU AI Act obligations arriving in August 2026. A procurement function built to "
        "extract concessions. The curriculum's reframe: these are not obstacles to route around, "
        "they are the training ground.",
        refs=(CURRICULUM,),
    ),
    _s(
        13,
        SlideKind.CONCEPT,
        "Governance is not the obstacle to the sale — it is the sale",
        "The market now insists governance ships with the use case: role-based permissions, "
        "segregation of duties, audit trails, deterministic fallbacks, continuous monitoring. The "
        "commercial consequence is the reason this conviction pays. A seller forced by one brutal "
        "deal to become fluent in that language emerges with a weapon that wins the next three, "
        "because most competitors still treat security and compliance as paperwork.",
        refs=(CURRICULUM,),
    ),
    _s(
        14,
        SlideKind.CONCEPT,
        "The weapons that survive a hard room",
        "MEDDPICC, for the inspection rigour to survive and steer a sophisticated, multi-gate "
        "buying process. Sandler up-front contracts, to avoid the nine-month proof-of-concept that "
        "dies in 'evaluation'. And security, lineage and regulatory fluency treated as a "
        "first-class part of the pitch rather than an appendix handled by someone else.",
        refs=(CURRICULUM,),
    ),
    _s(
        15,
        SlideKind.EXAMPLE,
        "The objection you cannot answer",
        "A CISO asks how you evidence lineage from source system to the figure on the report. You "
        "cannot answer. Two responses: route around them to the sponsor, which works until the "
        "security review, or treat the question as the syllabus, learn it, and return with the "
        "answer. The curriculum's field note is unambiguous — the objection you cannot yet answer "
        "is the weapon you do not yet have.",
        refs=(CURRICULUM,),
    ),
    _s(
        16,
        SlideKind.EXAMPLE,
        "Two sellers, one brutal deal",
        "Both lose a Tier-1 opportunity in the security review. The first records it as a "
        "product gap and moves on. The second writes down every question they could not answer, "
        "spends a month with their own engineers, and wins the next two deals in the same tier "
        "because they now open with the control story rather than being ambushed by it. Same loss, "
        "and only one of them was training.",
        refs=(CURRICULUM,),
    ),
    _s(
        17,
        SlideKind.CHECKPOINT,
        "Decompose a real win",
        "Take your last clear win and fill in the five fields: persona, trigger, insight, proof, "
        "close. Write what actually happened rather than what you would have liked to happen — "
        "including anything that was luck. If a field is blank, that is the most interesting part "
        "of the exercise, because it tells you which part of the win you do not control.",
        checkpoint="Fill the five fields of a signature play from a real closed deal.",
        refs=(CURRICULUM,),
    ),
    _s(
        18,
        SlideKind.CHECKPOINT,
        "Diagnose the binding term",
        "Take a live deal that is not moving. Score each of the five raising terms out of five — "
        "trigger, reach, insight, proof, consensus — and name the lowest. Then write the single "
        "action that raises that one term. Not three actions across three terms: one action on the "
        "binding term. This is the whole discipline of the equation in one exercise.",
        checkpoint="Name the binding term on a live deal and the one action that raises it.",
        refs=(CURRICULUM,),
    ),
    _s(
        19,
        SlideKind.CHECKPOINT,
        "Find three accounts that share the trigger",
        "The reproducibility test. Take the play you wrote in slide 17 and find three other "
        "accounts sharing the same trigger and persona. If you cannot find three, either the play "
        "is over-fitted to one firm or you do not know your segment well enough — both are useful "
        "findings. Run the identical play against one of them this month and record the cycle "
        "time.",
        checkpoint="Name three accounts sharing the trigger and persona, and the one you will run.",
        refs=(CURRICULUM,),
    ),
    _s(
        20,
        SlideKind.CHECKPOINT,
        "Name the stakeholder who frightens you",
        "Conviction IV's drill. Identify the deal in your pipeline you have been quietly avoiding "
        "because it is hard, and the specific stakeholder who frightens you — the CISO, the CRO, "
        "procurement. Engage them directly this week, treating their hardest objection as your "
        "syllabus. Then document the new capability the friction forced you to build.",
        checkpoint="Name the avoided deal, the stakeholder, and the date you will engage them.",
        refs=(CURRICULUM,),
    ),
    _s(
        21,
        SlideKind.CONCEPT,
        "Why these two convictions belong together",
        "III makes you consistent and IV makes you better, and each without the other fails in a "
        "recognisable way. Reproducibility alone produces a seller who runs one play efficiently "
        "into a shrinking set of accounts. Friction alone produces a seller who is always learning "
        "and never compounding. The pairing is the point: industrialise what works, and spend the "
        "capacity that frees on the rooms that will teach you something.",
        refs=(CURRICULUM,),
    ),
)

SECTION_5_TEST = SectionTest(
    questions=(
        TestQuestion(
            prompt="What does the throughput model say about chasing more targets?",
            options=(
                "It is the weakest lever if your reach and trigger-hit rates are low",
                "It is the most reliable lever, because pipeline coverage drives outcomes",
                "It is neutral: more targets raise volume without changing win rate",
                "It is the strongest lever early in a territory, and the weakest later",
            ),
            answer_index=0,
            explanation=(
                "The counter-intuitive companion line is that doubling your reach rate to the "
                "economic buyer does as much as doubling your win rate. In practice that usually "
                "means fewer accounts, reached better."
            ),
        ),
        TestQuestion(
            prompt="Which term LOWERS win probability in the deal equation?",
            options=(
                "The incumbent's switching cost",
                "The number of stakeholders on the committee",
                "The length of the buyer's budget cycle",
                "The strength of the dated trigger",
            ),
            answer_index=0,
            explanation=(
                "And it is still a lever rather than a given: absorbing the migration risk lowers "
                "the buyer's switching cost, which raises your odds without touching the other "
                "five."
            ),
        ),
        TestQuestion(
            prompt="What are the five fields of a signature play?",
            options=(
                "Persona, trigger, insight, proof, close",
                "Metrics, economic buyer, decision criteria, champion, competition",
                "Situation, problem, implication, need-payoff, close",
                "Account, incumbent, renewal, catalyst, thesis",
            ),
            answer_index=0,
            explanation=(
                "The second is MEDDIC and the third is SPIN. The five fields are what every "
                "documented win collapses into, which is what makes it handable to a colleague."
            ),
        ),
        TestQuestion(
            prompt=(
                "Why does the curriculum treat a hard security review as training rather than an "
                "obstacle?"
            ),
            options=(
                "Fluency won in one brutal deal wins the next three, because competitors treat it "
                "as paperwork",
                "Because security reviews are unavoidable in regulated markets",
                "Because the CISO is usually the economic buyer in infrastructure deals",
                "Because losing on security is a cheaper loss than losing on price",
            ),
            answer_index=0,
            explanation=(
                "The market now insists governance ships with the use case, so defensibility is a "
                "feature. The objection you cannot yet answer is the weapon you do not yet have."
            ),
        ),
        TestQuestion(
            prompt="A live deal is stalled. What does conviction III instruct you to do first?",
            options=(
                "Diagnose which of the five terms is binding, and raise that one",
                "Increase activity across every term until something moves",
                "Re-qualify the opportunity and consider disqualifying it",
                "Escalate to the economic buyer regardless of the current thread",
            ),
            answer_index=0,
            explanation=(
                "A weak deal is rarely weak on all five. Most sellers raise the term they are best "
                "at rather than the one that is binding — sharpening the insight on a deal that is "
                "short of consensus changes nothing."
            ),
        ),
        TestQuestion(
            prompt="What compresses the cycle by roughly forty percent in the worked play?",
            options=(
                "Attaching to a public dated goal and multi-threading to three executives",
                "Offering a proof of concept at no cost",
                "Bringing a sales engineer to every meeting from first contact",
                "Reducing the number of stakeholders involved in the decision",
            ),
            answer_index=0,
            explanation=(
                "Both halves matter: the public dated goal makes the timeline theirs, and the "
                "three "
                "threads mean no single stakeholder's silence can stall it — which is conviction V."
            ),
        ),
    ),
    pass_mark=0.8,
)


def section_5() -> CourseModule:
    """Section 5: convictions III and IV."""
    return CourseModule(
        id=_id("module", "convictions-3-4"),
        title="Convictions III and IV: reproducibility, and the hardest prospect",
        order=4,
        lessons=(
            Lesson(
                id=_id("lesson", "convictions-3-4"),
                title="Turn a win into a machine, then go where it breaks",
                body=_S5_BODY,
                order=0,
                author=LessonAuthor.HUMAN,
                slides=_SECTION_5_SLIDES,
                references=(CURRICULUM,),
                drill_topics=("doctrine:signature-play", "doctrine:hardest-prospect"),
                measurement=(
                    "You have a signature play filled in from a real win, a named binding term on "
                    "a "
                    "live deal with the one action that raises it, three accounts sharing the "
                    "trigger, and a date booked with the stakeholder you were avoiding."
                ),
            ),
        ),
        section_test=SECTION_5_TEST,
    )


# ==========================================================================================
# Section 6 — Convictions V and VI: the committee, and engineered luck
# ==========================================================================================

_S6_BODY = (
    "By the end of this lesson you can build a Blue Sheet for a live enterprise deal, assign a "
    "specific weapon to each seat on the committee, and operate a trigger watchlist as a standing "
    "discipline rather than a one-off exercise. Conviction V is about refusing to let one blocker "
    "decide an outcome; conviction VI is about being present in the account before the outcome is "
    "in play at all."
)

_SECTION_6_SLIDES: tuple[Slide, ...] = (
    _s(
        0,
        SlideKind.CONCEPT,
        "Conviction V: 'No one wins an enterprise deal alone.'",
        "Two claims. No individual and no single method wins an eight-figure deal — value "
        "compounds "
        "when distinct capabilities combine, and a commercial insight fused with deep technical "
        "proof produces a case neither could make alone. And a single internal blocker should "
        "never "
        "be allowed to decide an outcome. The seller's job is orchestration, not solo performance.",
        refs=(CURRICULUM,),
    ),
    _s(
        1,
        SlideKind.CONCEPT,
        "The trap: single-threading",
        "The passive seller finds one friendly contact, relies on them entirely, and when an "
        "internal stakeholder blocks the deal they accept the block and let the opportunity stall. "
        "They are managing one relationship rather than steering an outcome. The awakening is to "
        "take responsibility for the entire decision unit — and to refuse to let any single "
        "detractor, or any single champion's limits, determine the result.",
        refs=(CURRICULUM,),
    ),
    _s(
        2,
        SlideKind.CONCEPT,
        "Six seats, six appetites",
        "The Head of Trading wants speed. The quant wants elegant data access. The Head of "
        "Architecture wants resilience without lock-in. The CRO wants real-time risk and capital "
        "efficiency. Compliance wants explainability. Procurement wants price and terms. The "
        "curriculum's conclusion follows directly: no single message satisfies all of them, and a "
        "pitch tuned to the desk will alienate risk.",
        asset=_diagram(
            "the_committee",
            "The committee, and the weapon each seat answers to.",
            "A three-column table. The first column, headed THE SEAT, lists Head of Trading, the "
            "quant, Head of Architecture, the CRO, Compliance and Procurement. The second, headed "
            "WHAT THEY WANT, gives in order: speed; elegant data access; resilience without "
            "lock-in; real-time risk; explainability; price and terms. The third column, "
            "highlighted in pale green and headed WHAT MOVES THEM, gives: Challenger insight; a "
            "working demo; a strangler-gateway story; trust plus a regulatory case; a governance "
            "narrative; a mutual action plan.",
        ),
        refs=(CURRICULUM,),
    ),
    _s(
        3,
        SlideKind.CONCEPT,
        "Combining weapons across the room",
        "The egoist combines weapons across the committee: a Challenger insight to hook the desk, "
        "a "
        "working demo to win the quants, a trust-led economic and regulatory case to move the CRO, "
        "and a mutual action plan to satisfy procurement. This is the practical reason conviction "
        "II asks you to be famous for one weapon rather than adequate at three — you bring "
        "colleagues for the others.",
        refs=(CURRICULUM,),
    ),
    _s(
        4,
        SlideKind.CONCEPT,
        "Co-selling as the clearest case of compounding",
        "Commercial skill fused with a sales engineer's credibility produces a case neither could "
        "deliver alone. The curriculum treats this as the clearest example of the conviction "
        "rather "
        "than as a resourcing convenience. Read it as an instruction about who you bring into "
        "which "
        "room, and when — not as permission to hand the technical half of your deal to somebody "
        "else.",
        refs=(CURRICULUM,),
    ),
    _s(
        5,
        SlideKind.CONCEPT,
        "Absorb the blocker's constraint",
        "The move that separates conviction V from ordinary stakeholder management. When a "
        "stakeholder blocks — a rigid product manager, say — the constraint is absorbed and "
        "repurposed: their strict roadmap becomes a selling point for governance and transparency. "
        "The field note is the compressed version, and it is worth memorising: absorb the "
        "blocker's "
        "constraint and hand it back as your design principle.",
        refs=(CURRICULUM,),
    ),
    _s(
        6,
        SlideKind.CONCEPT,
        "The Blue Sheet",
        "Miller Heiman Strategic Selling is the operating system here: map every buying influence "
        "— "
        "economic, user, technical, coach — with their win-results and your standing with each. "
        "MEDDIC locks down the economic buyer, the decision process and a genuine champion. The "
        "two "
        "are complementary rather than alternatives: one maps the room, the other inspects the "
        "deal.",
        refs=(CURRICULUM,),
    ),
    _s(
        7,
        SlideKind.CONCEPT,
        "Win-results: the business result and the personal win",
        "The field note that most sellers skip. Map win-results for each stakeholder as two "
        "things: "
        "the business result and the personal win. The Head of Architecture's business result is "
        "resilience without lock-in; their personal win might be not being the person who signed "
        "off the last migration that failed. You will rarely be told the second one, and it "
        "frequently decides the vote.",
        refs=(CURRICULUM,),
    ),
    _s(
        8,
        SlideKind.CONCEPT,
        "A champion without power is a friend",
        "The second field note, and the most common expensive error in enterprise selling. A "
        "friendly contact who cannot convene the committee, cannot spend, and cannot survive "
        "internal opposition is a source of information and comfort, not a champion. The test is "
        "not whether they like you or your product; it is whether they have ever successfully "
        "pushed something through this organisation.",
        refs=(CURRICULUM,),
    ),
    _s(
        9,
        SlideKind.CONCEPT,
        "Conviction VI: 'Luck is the dividend of readiness and positioning.'",
        "Luck is not random. It is a dividend, and it pays out only to the seller already "
        "positioned "
        "to collect it. When a competitor stumbles and the client calls you first, that is not "
        "fortune — it is the return on relationships and presence you built before there was ever "
        "a "
        "deal. Opportunity, in large part, is manufactured.",
        refs=(CURRICULUM,),
    ),
    _s(
        10,
        SlideKind.CONCEPT,
        "The trap: going dark between deals",
        "The passive seller waits for the right moment and blames the market when it does not "
        "arrive. Between active deals they go dark; they do not nurture cold accounts, so they are "
        "nowhere when an opportunity finally breaks open. The curriculum's diagnosis is sharp: "
        "every methodology they know improves what happens inside a conversation, and none tells "
        "them which conversation to be in, or when.",
        refs=(CURRICULUM,),
    ),
    _s(
        11,
        SlideKind.CONCEPT,
        "The calendar is unusually predictable",
        "The October 2027 settlement deadline and its December 2026 confirmation milestone. The "
        "roll-out of 23/5 trading. Vendor-consolidation decisions, leadership changes, M&A. And "
        "the "
        "entirely unscheduled but inevitable incumbent outage during a volatile, bursty session. "
        "Each is a moment when a frozen budget thaws — and all but the last can be diarised months "
        "ahead.",
        refs=(CURRICULUM,),
    ),
    _s(
        12,
        SlideKind.EXAMPLE,
        "The dividend, worked",
        "An incumbent's settlement automation buckles during T+0 confirmation testing in 2026 and "
        "the client calls you first. The curriculum insists that is not luck: it is the dividend "
        "of "
        "having been a credible, present voice in that account for a year. The seller who receives "
        "that call did the unglamorous work twelve months earlier, and the seller who did not will "
        "describe the same event as someone else's good fortune.",
        refs=(CURRICULUM,),
    ),
    _s(
        13,
        SlideKind.CONCEPT,
        "Two disciplines, and the division of labour between them",
        "Social and digital presence does the quiet work of being known; trigger monitoring "
        "decides "
        "where you point it. Neither substitutes for the other — presence without monitoring is "
        "being well-regarded in the wrong accounts, and monitoring without presence is arriving as "
        "a stranger at exactly the right moment. The egoist is positioned at the spot where the "
        "mistake is most likely to happen, before it happens.",
        refs=(CURRICULUM,),
    ),
    _s(
        14,
        SlideKind.CONCEPT,
        "Nurture with insight, never with 'just checking in'",
        "The field note is a rule about content. A nurture cadence made of check-ins trains the "
        "account to ignore you, and does it faster than silence would. A cadence made of insight — "
        "what the December milestone means for their exception volumes, what a peer firm found in "
        "testing — builds the standing that the dividend pays out on. The cadence is the easy "
        "part; "
        "having something to say is the work.",
        refs=(CURRICULUM,),
    ),
    _s(
        15,
        SlideKind.CHECKPOINT,
        "Build a Blue Sheet for a live deal",
        "Take one live enterprise deal and map every buying influence. For each, record what they "
        "want, what they fear, and your current standing. Then assign the specific weapon you will "
        "bring to each. Blank cells are the deliverable here: an influence whose fears you cannot "
        "state is one you have not really met, whatever the CRM says about contact history.",
        checkpoint=(
            "Produce a Blue Sheet with want, fear, standing and assigned weapon per influence."
        ),
        refs=(CURRICULUM,),
    ),
    _s(
        16,
        SlideKind.CHECKPOINT,
        "Name your weakest thread and your most dangerous detractor",
        "From that Blue Sheet, identify two people: the influence where your standing is weakest, "
        "and the detractor most capable of stopping the deal. They are often not the same person, "
        "and the second is frequently someone you have never spoken to. Engage both this week. "
        "This "
        "is the drill the curriculum sets, and the reason single-threading survives is that this "
        "step is uncomfortable.",
        checkpoint="Name both people and the date you will engage each.",
        refs=(CURRICULUM,),
    ),
    _s(
        17,
        SlideKind.CHECKPOINT,
        "Test your champion",
        "Apply the field note to whoever you currently call your champion: have they ever "
        "successfully pushed something through this organisation? If you do not know, you have a "
        "friend rather than a champion, and finding out is this week's work. Write the evidence — "
        "a "
        "named initiative they carried, and what it cost them — or write that you could not find "
        "any.",
        checkpoint=(
            "Record the evidence that your champion has real internal power, or that they do not."
        ),
        refs=(CURRICULUM,),
    ),
    _s(
        18,
        SlideKind.CHECKPOINT,
        "Operate the watchlist",
        "Return to the ten-account trigger watchlist from section 2 and make it a standing "
        "discipline: renewal dates, deadlines, leadership changes, known fragilities. Define a "
        "nurture cadence for the cold accounts — insight, not pitches — and establish one credible "
        "public presence where your buyers actually gather. Then measure the thing that matters: "
        "your time-to-first-contact when a trigger fires.",
        checkpoint=(
            "Record your nurture cadence, your chosen public presence, and your "
            "time-to-first-contact."
        ),
        refs=(CURRICULUM,),
    ),
    _s(
        19,
        SlideKind.EXAMPLE,
        "The committee applied to an ATLAS engagement",
        "The Platform Power assessment gives you a legitimate reason to meet every seat on the "
        "committee, which is unusual and worth exploiting. Infrastructure modules need "
        "architecture. The metrics need operations and finance. The Powers ratings need the desk "
        "and the strategy owner. An assessment is multi-threading with a stated purpose — you are "
        "not asking for access, you are collecting inputs.",
        refs=(CURRICULUM,),
    ),
    _s(
        20,
        SlideKind.CONCEPT,
        "The two convictions together",
        "V is about the room and VI is about the calendar, and the pairing produces the seller who "
        "is neither surprised nor alone. The curriculum's ordering puts them in Phase II — the "
        "logic of joint execution — because both are about refusing to treat a deal as a private "
        "transaction between you and one contact. Section 7 takes what remains: the state you are "
        "in when you walk into the room.",
        refs=(CURRICULUM,),
    ),
)

SECTION_6_TEST = SectionTest(
    questions=(
        TestQuestion(
            prompt="What does the curriculum say to do with a stakeholder who blocks the deal?",
            options=(
                "Absorb their constraint and hand it back as your design principle",
                "Route around them to the economic buyer",
                "Disqualify the opportunity until they leave the role",
                "Escalate through your champion to have them overruled",
            ),
            answer_index=0,
            explanation=(
                "The worked example is a rigid product manager whose strict roadmap becomes your "
                "selling point for governance and transparency. Routing around a detractor works "
                "until the review at which they are asked for an opinion."
            ),
        ),
        TestQuestion(
            prompt="What distinguishes a champion from a friend?",
            options=(
                "A champion has successfully pushed something through the organisation before",
                "A champion prefers your product to the incumbent's",
                "A champion is senior enough to attend the final decision meeting",
                "A champion introduces you to other stakeholders",
            ),
            answer_index=0,
            explanation=(
                "A champion without power is a friend — a source of information and comfort. The "
                "test is internal track record, not warmth toward you or your product."
            ),
        ),
        TestQuestion(
            prompt="What moves the Head of Architecture, per the committee map?",
            options=(
                "A strangler-gateway story: resilience without lock-in",
                "A Challenger insight about an unmeasured cost",
                "A working prototype on their own data",
                "A mutual action plan with dates and owners",
            ),
            answer_index=0,
            explanation=(
                "The other three belong to the Head of Trading, the quant and procurement "
                "respectively. Incremental modernisation behind a clean interface is the answer to "
                "wanting resilience without a risky big-bang replacement."
            ),
        ),
        TestQuestion(
            prompt="In conviction VI, what is luck?",
            options=(
                "A dividend that pays out only to the seller already positioned to collect it",
                "Random variance that a large enough pipeline averages out",
                "The result of a competitor's error, which cannot be anticipated",
                "A euphemism for timing that experienced sellers develop by instinct",
            ),
            answer_index=0,
            explanation=(
                "When a competitor stumbles and the client calls you first, that is the return on "
                "presence built before there was a deal. The incumbent's outage is not an if — "
                "position as though it is a when."
            ),
        ),
        TestQuestion(
            prompt="What does the curriculum say to nurture cold accounts with?",
            options=(
                "Insight, never 'just checking in'",
                "A regular cadence of product updates and release notes",
                "Referrals and introductions to peer firms",
                "Invitations to events and briefings",
            ),
            answer_index=0,
            explanation=(
                "A cadence of check-ins trains the account to ignore you faster than silence "
                "would. "
                "The cadence is the easy part; having something worth saying is the work."
            ),
        ),
        TestQuestion(
            prompt="Why does an ATLAS assessment help with conviction V specifically?",
            options=(
                "It gives a stated reason to meet every seat on the committee",
                "It shortens the procurement cycle by pre-qualifying the buyer",
                "It replaces the need for a champion inside the account",
                "It produces a business case procurement will accept without challenge",
            ),
            answer_index=0,
            explanation=(
                "Infrastructure modules need architecture, metrics need operations and finance, "
                "Powers ratings need the desk. You are not asking for access, you are collecting "
                "inputs — which is multi-threading with a purpose."
            ),
        ),
    ),
    pass_mark=0.8,
)


def section_6() -> CourseModule:
    """Section 6: convictions V and VI."""
    return CourseModule(
        id=_id("module", "convictions-5-6"),
        title="Convictions V and VI: the committee, and engineered luck",
        order=5,
        lessons=(
            Lesson(
                id=_id("lesson", "convictions-5-6"),
                title="Orchestrate the room, and be there before the trigger fires",
                body=_S6_BODY,
                order=0,
                author=LessonAuthor.HUMAN,
                slides=_SECTION_6_SLIDES,
                references=(CURRICULUM,),
                drill_topics=("doctrine:multi-thread", "doctrine:engineered-luck"),
                measurement=(
                    "You hold a Blue Sheet for a live deal with want, fear, standing and weapon "
                    "per "
                    "influence; you have engaged your weakest thread and your most dangerous "
                    "detractor; and your watchlist has a nurture cadence and a measured "
                    "time-to-first-contact."
                ),
            ),
        ),
        section_test=SECTION_6_TEST,
    )


# ==========================================================================================
# Section 7 — Convictions VII and VIII: flow, and total account awareness
# ==========================================================================================

_S7_BODY = (
    "By the end of this lesson you can calibrate a deal to a seller deliberately, set a stretch "
    "goal that forces presence in a high-stakes room, and hold a living map of an account rather "
    "than a relationship with one person in it. These are Phase III, the peak of the doctrine, and "
    "they are the two convictions that cannot be faked: both are states you are in rather than "
    "moves you make."
)

_SECTION_7_SLIDES: tuple[Slide, ...] = (
    _s(
        0,
        SlideKind.CONCEPT,
        "Conviction VII: 'Peak performance is engineered, not awaited.'",
        "Peak performance lives at the precise meeting point of challenge and skill. Too little "
        "challenge breeds complacency; too much breeds fear; the right calibration produces total "
        "immersion and effortless command of the room. The conviction is to match the difficulty "
        "of "
        "the deal to the level of the seller deliberately, and to enter every high-stakes "
        "conversation with a specific, demanding goal.",
        refs=(CURRICULUM,),
    ),
    _s(
        1,
        SlideKind.CONCEPT,
        "The two failure modes",
        "The passive seller reads from a script and goes through the motions. In a deal far below "
        "their level they coast, skipping discovery and dropping balls. Thrown into one far above "
        "it, they freeze — hesitating, over-discounting out of fear, and losing the room. Both are "
        "calibration failures rather than effort failures, which is why working harder fixes "
        "neither.",
        refs=(CURRICULUM,),
    ),
    _s(
        2,
        SlideKind.CONCEPT,
        "Boredom, flow, anxiety",
        "The band is narrow and both edges are expensive. Study the diagram as a management tool "
        "as "
        "much as a personal one: the curriculum's two instructions are that you do not send a "
        "junior into a Tier-1 procurement battle where fear will drive over-discounting, and you "
        "do "
        "not waste an elite seller on a trivial renewal where boredom will make them sloppy.",
        asset=_diagram(
            "the_flow_channel",
            "Challenge against skill, and the band where command of the room lives.",
            "A plot with challenge on the vertical axis and skill on the horizontal. In the upper "
            "left, marked in a warm caution colour, ANXIETY: the Tier-1 procurement battle you "
            "sent "
            "a junior into, where fear drives over-discounting. In the lower right, in muted grey, "
            "BOREDOM: the trivial renewal given to your best seller. Running diagonally between "
            "them, highlighted in pale green, FLOW: difficulty matched to the seller, with one "
            "demanding goal for the room.",
        ),
        refs=(CURRICULUM,),
    ),
    _s(
        3,
        SlideKind.CONCEPT,
        "Why capital-markets rooms punish the scripted",
        "The rooms are volatile and adversarial: a boardroom mid-incident, a desk during a bursty, "
        "capacity-straining session, a procurement negotiation with a professional adversary. "
        "These "
        "rooms punish the scripted and reward the present. Deep, real-time discovery — SPIN's "
        "Implication questions, Sandler's call control — only works when the seller has dropped "
        "the "
        "deck and is genuinely listening.",
        refs=(CURRICULUM,),
    ),
    _s(
        4,
        SlideKind.CONCEPT,
        "The stretch goal",
        "Before every high-stakes conversation, set one specific, demanding goal that forces "
        "immersion instead of performance. The curriculum's example is precise enough to copy: to "
        "surface and resolve the CRO's unspoken objection live. Note what it is not — it is not "
        "'build rapport' or 'move the deal forward', neither of which can be failed and therefore "
        "neither of which demands anything.",
        refs=(CURRICULUM,),
    ),
    _s(
        5,
        SlideKind.CONCEPT,
        "The script is a comfort blanket",
        "The field note, and it is worth taking literally. In a volatile room, drop it. The deck "
        "you prepared is insurance against a conversation you are afraid of, and the cost of "
        "carrying it is that you cannot hear the thing that would have won the deal. Prepare "
        "thoroughly, then be willing to abandon the preparation — those are not contradictory "
        "instructions.",
        refs=(CURRICULUM,),
    ),
    _s(
        6,
        SlideKind.CONCEPT,
        "A stretch goal converts anxiety into focus",
        "The second field note explains the mechanism. Anxiety in a hard room comes from an "
        "unbounded threat — anything could go wrong. A specific demanding goal bounds it: there is "
        "now one thing to achieve, and attention has somewhere to go. This is why the goal has to "
        "be failable. A goal you cannot fail provides no boundary and therefore no relief.",
        refs=(CURRICULUM,),
    ),
    _s(
        7,
        SlideKind.CONCEPT,
        "The third field note, and what it costs",
        "'If a deal bores you, it is training someone else's bad habits into you.' Read that as an "
        "argument about compounding rather than about enjoyment. Skills degrade toward the level "
        "the work demands, so a book of comfortable renewals is not neutral — it is actively "
        "de-skilling, slowly, while producing perfectly acceptable quarterly numbers.",
        refs=(CURRICULUM,),
    ),
    _s(
        8,
        SlideKind.CONCEPT,
        "Conviction VIII: 'Read the whole field. Act before it is obvious.'",
        "At the highest level, deliberation is too slow. The elite seller does not study one "
        "champion and react to events; they read the entire account — its politics, its budget, "
        "its "
        "pressures, its hidden detractors — continuously, until the next move is obvious to them "
        "before it is visible to anyone else. The curriculum calls this total account awareness "
        "and "
        "treats it as the peak of the doctrine.",
        refs=(CURRICULUM,),
    ),
    _s(
        9,
        SlideKind.CONCEPT,
        "The trap: tunnel vision",
        "The passive seller sees only their one champion and the deal directly in front of them. "
        "They react to events after they happen and are repeatedly surprised by changes they could "
        "have anticipated. The awakening is the final shift: from reacting to anticipating, from "
        "watching one person to reading the entire system, and from responding to an RFP to "
        "closing "
        "before one is ever written.",
        refs=(CURRICULUM,),
    ),
    _s(
        10,
        SlideKind.CONCEPT,
        "The ecosystem is readable if you watch all of it",
        "Operational friction generates pressure on a schedule: T+1 today, T+0 tomorrow, overnight "
        "funding stress, liquidity fragmentation under 23/5. Regulatory deadlines surface "
        "detractors "
        "and create urgency. And executive anxiety pivots deals — when an incumbent cannot deliver "
        "real-time collateral mobility, the CRO's concern over trapped capital becomes the opening "
        "that decides the account.",
        refs=(CURRICULUM,),
    ),
    _s(
        11,
        SlideKind.CONCEPT,
        "The living map",
        "Total account awareness means holding a map of the politics, the budget cycle, the "
        "catalysts and the hidden opponents — and processing it continuously. The operative word "
        "is "
        "living. The field note is blunt about the alternative: map the account weekly, because a "
        "stale map is a liability dressed as an asset. A map you trust and have not updated is "
        "worse than no map.",
        refs=(CURRICULUM,),
    ),
    _s(
        12,
        SlideKind.CONCEPT,
        "The pre-emptive close",
        "The reward, stated precisely: identify the exact moment the deciding executive's anxiety "
        "peaks, bypass the slow IT-procurement track, and present an industrial-grade solution "
        "directly to the C-suite — closing before a competitor has even seen an RFP, because no "
        "RFP "
        "was ever written. This is conviction I's 'we do not wait for budget, we take it' executed "
        "with seven sections of apparatus behind it.",
        refs=(CURRICULUM,),
    ),
    _s(
        13,
        SlideKind.CONCEPT,
        "Whose anxiety decides the account",
        "The field note corrects the most common misidentification: the deciding anxiety usually "
        "sits with the CRO or COO, not your champion. Your champion's anxiety is about the "
        "project. "
        "The deciding anxiety is about the institution — trapped capital, an unauditable position, "
        "a deadline that will be missed publicly. Those are the fears that release budget outside "
        "a "
        "normal cycle.",
        refs=(CURRICULUM,),
    ),
    _s(
        14,
        SlideKind.EXAMPLE,
        "The pre-emptive close, worked",
        "An incumbent cannot deliver real-time collateral mobility. You have watched the account "
        "for "
        "a year and know the CRO's concern over trapped capital is rising with funding costs. When "
        "the quarterly capital review lands, you go directly to the C-suite with a costed, "
        "auditable answer — not a proposal, an answer. Procurement is later asked to paper a "
        "decision that has effectively been made.",
        refs=(CURRICULUM,),
    ),
    _s(
        15,
        SlideKind.EXAMPLE,
        "The same account, played reactively",
        "A second seller has the same product and a friendly champion in operations. They learn of "
        "the collateral problem when the RFP is published, respond thoroughly, and lose to a "
        "requirement list they now recognise was written around someone else's solution. Nothing "
        "they did was wrong. Everything they did was late, and the lateness was decided a year "
        "earlier.",
        refs=(CURRICULUM,),
    ),
    _s(
        16,
        SlideKind.CHECKPOINT,
        "Rate the challenge-skill match of your book",
        "Go through your live deals and mark each: boring, matched, or frightening. Be honest — "
        "'matched' is the answer people give when they have not thought about it. Then act on the "
        "two extremes: what would make a boring deal demanding, and who would you bring into a "
        "frightening one? A book with no frightening deals is a book that is de-skilling you.",
        checkpoint="Mark every live deal boring / matched / frightening, and act on both extremes.",
        refs=(CURRICULUM,),
    ),
    _s(
        17,
        SlideKind.CHECKPOINT,
        "Write one stretch goal, and debrief against it",
        "Before your next high-stakes meeting write one specific, demanding, failable goal for the "
        "room. Prepare your discovery questions and commit to abandoning the deck if the room "
        "demands it. Afterwards, debrief honestly: were you in boredom, anxiety, or flow — and "
        "why? "
        "The debrief is not optional; without it this is a mood rather than a discipline.",
        checkpoint="Record the stretch goal, whether you met it, and which state you were in.",
        refs=(CURRICULUM,),
    ),
    _s(
        18,
        SlideKind.CHECKPOINT,
        "Build the living map",
        "Choose your most important account and map it: politics, budget cycle, catalysts, "
        "detractors. Then identify the executive whose anxiety, when it peaks, will decide the "
        "account — and check yourself against the field note, because if you have named your "
        "champion you have probably named the wrong person. Track the ecosystem signals that tell "
        "you that moment is approaching.",
        checkpoint=(
            "Produce the map, name the deciding executive, and list the signals you will watch."
        ),
        refs=(CURRICULUM,),
    ),
    _s(
        19,
        SlideKind.CHECKPOINT,
        "Plan the pre-emptive move",
        "For that account, write the move you will make before any process begins: who you go to, "
        "what you bring, and what has to be true first. Then set the weekly review that keeps the "
        "map alive. The best RFP, per the field note, is the one your competitor never knew to "
        "respond to — and that outcome is planned months out or not at all.",
        checkpoint="Write the pre-emptive move and diarise the weekly map review.",
        refs=(CURRICULUM,),
    ),
    _s(
        20,
        SlideKind.CONCEPT,
        "Why these are the peak, and what remains",
        "Everything before this is apparatus: targets, weapons, plays, rooms, timing. VII and VIII "
        "are what the apparatus is for — a seller so completely oriented that execution becomes "
        "reflexive, acting a clear step ahead of the competition's comprehension. Section 8 runs "
        "all "
        "eight as a single campaign, against the engagement you actually sell.",
        refs=(CURRICULUM,),
    ),
)

SECTION_7_TEST = SectionTest(
    questions=(
        TestQuestion(
            prompt="What are the two failure modes conviction VII identifies?",
            options=(
                "Coasting in a deal below your level, and freezing in one above it",
                "Over-preparing, and under-preparing",
                "Talking too much, and listening passively",
                "Discounting too early, and holding price too long",
            ),
            answer_index=0,
            explanation=(
                "Both are calibration failures rather than effort failures, which is why working "
                "harder fixes neither. Hence the two management instructions about who you send "
                "into which room."
            ),
        ),
        TestQuestion(
            prompt="What makes a stretch goal work?",
            options=(
                "It is specific and failable, which bounds an otherwise unbounded threat",
                "It is ambitious enough to exceed the deal's realistic outcome",
                "It is agreed with the buyer at the start of the meeting",
                "It is measurable in revenue rather than in behaviour",
            ),
            answer_index=0,
            explanation=(
                "'Build rapport' cannot be failed and therefore demands nothing. 'Surface and "
                "resolve the CRO's unspoken objection live' can be failed, so attention has "
                "somewhere to go."
            ),
        ),
        TestQuestion(
            prompt="Whose anxiety usually decides the account?",
            options=(
                "The CRO or COO, not your champion",
                "Your champion, who carries the internal argument",
                "The economic buyer, who holds the budget",
                "The Head of Architecture, who owns the risk of migration",
            ),
            answer_index=0,
            explanation=(
                "Your champion's anxiety is about the project; the deciding anxiety is about the "
                "institution — trapped capital, an unauditable position, a deadline that will be "
                "missed publicly. Those release budget outside a normal cycle."
            ),
        ),
        TestQuestion(
            prompt="What does the field note say about a stale account map?",
            options=(
                "It is a liability dressed as an asset; map weekly",
                "It is still better than no map, provided you know its age",
                "It should be rebuilt at each stage gate rather than weekly",
                "It matters less once you have a champion with real power",
            ),
            answer_index=0,
            explanation=(
                "A map you trust and have not updated is worse than no map, because it produces "
                "confident decisions on stale politics. The operative word in 'living map' is "
                "living."
            ),
        ),
        TestQuestion(
            prompt="What is the pre-emptive close?",
            options=(
                "Going C-suite-direct at the moment the deciding anxiety peaks, before any "
                "process begins",
                "Presenting a final proposal before the competitor has presented theirs",
                "Asking for the business at the first meeting to test qualification",
                "Closing at the end of the buyer's budget cycle to use expiring funds",
            ),
            answer_index=0,
            explanation=(
                "The point is that no RFP is ever written. It is conviction I's 'we do not wait "
                "for "
                "budget, we take it' executed with seven sections of apparatus behind it."
            ),
        ),
        TestQuestion(
            prompt="Why does the curriculum warn against a book of boring deals?",
            options=(
                "Skills degrade toward the level the work demands, so it de-skills you while the "
                "numbers look fine",
                "Boring deals have lower average contract values",
                "Boring deals are the ones most likely to be lost to a competitor",
                "Boring deals consume the same time as demanding ones",
            ),
            answer_index=0,
            explanation=(
                "'If a deal bores you, it is training someone else's bad habits into you.' That is "
                "an argument about compounding, not about enjoyment — and it is why a book with no "
                "frightening deals is a problem."
            ),
        ),
    ),
    pass_mark=0.8,
)


def section_7() -> CourseModule:
    """Section 7: convictions VII and VIII."""
    return CourseModule(
        id=_id("module", "convictions-7-8"),
        title="Convictions VII and VIII: flow, and total account awareness",
        order=6,
        lessons=(
            Lesson(
                id=_id("lesson", "convictions-7-8"),
                title="Calibrate the room, then read the whole field",
                body=_S7_BODY,
                order=0,
                author=LessonAuthor.HUMAN,
                slides=_SECTION_7_SLIDES,
                references=(CURRICULUM,),
                drill_topics=("doctrine:flow", "doctrine:total-account-awareness"),
                measurement=(
                    "Your live deals are rated boring / matched / frightening with action on both "
                    "extremes, you have run and debriefed one stretch goal, and your most "
                    "important "
                    "account has a living map, a named deciding executive and a planned "
                    "pre-emptive "
                    "move."
                ),
            ),
        ),
        section_test=SECTION_7_TEST,
    )


# ==========================================================================================
# Section 8 — The campaign: the doctrine on one account, through an ATLAS engagement
# ==========================================================================================

_S8_BODY = (
    "By the end of this lesson you can run all eight convictions as a single campaign against one "
    "named account, and you can say exactly where the Platform Power assessment sits in that "
    "campaign — as the instrument that opens the committee, the evidence that carries the insight, "
    "and the deliverable that closes. This is where the doctrine stops being a reading exercise "
    "and "
    "becomes the way you work an account."
)

_SECTION_8_SLIDES: tuple[Slide, ...] = (
    _s(
        0,
        SlideKind.CONCEPT,
        "Eight convictions, one campaign",
        "The curriculum's integration is explicit: the eight convictions are not separate skills "
        "to "
        "be practised in isolation, they are one continuous campaign. Run end to end against a "
        "single Tier-1 account they have a shape, and the shape is not their numbered order. "
        "II and VI happen before anything else is in play, and VIII runs the whole way through.",
        asset=_diagram(
            "the_campaign",
            "The eight convictions in the order they actually run.",
            "Four panels connected left to right. BEFORE: choose the hard account (I), enter with "
            "one weapon (II), be present early (VI). THE TRIGGER: run the documented play (III), "
            "seek the hardest room (IV). THE ENGAGEMENT: orchestrate the committee (V), drop the "
            "script (VII). THE CLOSE: the pre-emptive strike (VIII) before an RFP exists. Beneath "
            "all four, a full-width dark green bar reading that conviction VIII, total account "
            "awareness, runs the whole way through.",
        ),
        refs=(CURRICULUM,),
    ),
    _s(
        1,
        SlideKind.CONCEPT,
        "Before: the account is chosen, not inherited",
        "You begin by choosing the account because it is hard and valuable, not because it is easy "
        "(I). You enter with your signature weapon rather than as a generalist (II). You arrive "
        "having watched the ecosystem for months, present and credible before any process begins "
        "(VI), reading the whole field rather than a single champion (VIII). Three of the four "
        "happen before you have a deal at all.",
        refs=(CURRICULUM,),
    ),
    _s(
        2,
        SlideKind.CONCEPT,
        "The trigger: the play, and the hard room",
        "As the dated catalyst approaches — the 2027 deadline, a consolidation, an incumbent's "
        "strain — you run the documented play that has worked against firms sharing the same "
        "constraint (III), and you deliberately seek the hardest stakeholders, turning the CISO "
        "and "
        "CRO from blockers into advocates (IV). The catalyst sets the clock; the play is what you "
        "do with the time.",
        refs=(CURRICULUM,),
    ),
    _s(
        3,
        SlideKind.CONCEPT,
        "The engagement, and the close",
        "You orchestrate the whole committee, combining weapons across trading, quant, "
        "architecture, risk and procurement, and absorbing the inevitable blocker (V). In the "
        "decisive rooms you drop the script and operate in flow (VII). And at the precise moment "
        "the deciding executive's anxiety peaks, you make the pre-emptive, C-suite-direct move and "
        "close before a competitor has seen an RFP (VIII).",
        refs=(CURRICULUM,),
    ),
    _s(
        4,
        SlideKind.CONCEPT,
        "Where our own product sits in that campaign",
        "The Platform Power assessment is not a deliverable you sell at the end. It is an "
        "instrument you use during the campaign, and it does three jobs the doctrine otherwise "
        "asks "
        "you to do by force of personality: it opens the committee, it manufactures the insight, "
        "and it converts a diagnosis into a priced decision. The next slides take each in turn.",
        refs=(CURRICULUM,),
    ),
    _s(
        5,
        SlideKind.CONCEPT,
        "The assessment as the committee-opener (conviction V)",
        "An assessment needs inputs from architecture, operations, finance, the desk and the "
        "strategy owner. That is a stated, legitimate reason to meet every seat — you are not "
        "requesting access, you are collecting data. Multi-threading is the hardest instruction in "
        "the doctrine to execute cold, and the assessment turns it into a process the client "
        "themselves helps you run.",
        refs=(CURRICULUM,),
    ),
    _s(
        6,
        SlideKind.CONCEPT,
        "The assessment as the insight (convictions II and III)",
        "The Challenger weapon requires a cost the buyer has not measured. The scored assessment "
        "produces exactly that, and it produces it from the client's own inputs rather than from "
        "your assertion — which closes the fidelity gap from section 4 before anyone tests it. In "
        "the deal equation's terms, the assessment raises the insight term and the proof term with "
        "one artefact.",
        refs=(CURRICULUM,),
    ),
    _s(
        7,
        SlideKind.CONCEPT,
        "The assessment as the close (conviction III)",
        "The report gives you the mutual action plan's spine: a ranked set of constraints with the "
        "value of fixing each. Reverse-engineer the plan from the client's own dated milestone and "
        "the close writes itself — the sequence is theirs, the priorities are their platform's, "
        "and "
        "the deadline is one they already have to meet. That is the 'close' field of your "
        "signature "
        "play, standardised across a segment.",
        refs=(CURRICULUM,),
    ),
    _s(
        8,
        SlideKind.CONCEPT,
        "What the assessment does not do",
        "It does not replace conviction I. The assessment is an instrument for a campaign you have "
        "already chosen to run; it cannot choose the account, and it will not create urgency where "
        "no catalyst exists. A seller who waits for an assessment request has simply moved the "
        "waiting one step earlier. The instrument is powerful in a campaign and inert without one.",
        refs=(CURRICULUM,),
    ),
    _s(
        9,
        SlideKind.CONCEPT,
        "The honesty constraint, and why it helps you",
        "The scoring engine refuses to produce a client-facing pack on draft coefficients, marks "
        "everything sandbox as non-production, and states what it has not assessed. That is a "
        "commercial asset in a hard room: conviction IV says the CISO and CRO are where deals are "
        "won, and a tool that will not overstate itself is the easiest thing you will ever take "
        "into that room.",
        refs=(CURRICULUM,),
    ),
    _s(
        10,
        SlideKind.EXAMPLE,
        "The campaign, run: months minus twelve to minus nine",
        "A mid-tier UK asset manager, incumbent post-trade vendor, renewal in eighteen months. You "
        "choose it because it is hard (I). Your weapon is Challenger (II). You spend the quarter "
        "building presence: two pieces of public work on T+0 confirmation readiness, one "
        "conversation a month with operations, no pitch (VI). You start the account map (VIII).",
        refs=(CURRICULUM,),
    ),
    _s(
        11,
        SlideKind.EXAMPLE,
        "Months minus nine to minus six",
        "The December 2026 milestone is now inside their planning horizon. You run the documented "
        "play (III): the Head of Operations persona, the confirmation deadline as trigger, a "
        "quantified exception-rate model as insight. You propose the Platform Power assessment as "
        "the way to size it — which gets you architecture, finance and the desk in the same "
        "fortnight (V).",
        refs=(CURRICULUM,),
    ),
    _s(
        12,
        SlideKind.EXAMPLE,
        "Months minus six to minus three",
        "The assessment scores. Their bottleneck is not where operations assumed. You take the "
        "finding to the CISO and the CRO first, not last, and spend two hard sessions on lineage "
        "and auditability (IV). Those sessions produce the governance narrative that later moves "
        "compliance (V). Your account map now has the CRO's trapped-capital concern rising on it "
        "(VIII).",
        refs=(CURRICULUM,),
    ),
    _s(
        13,
        SlideKind.EXAMPLE,
        "The close",
        "The quarterly capital review approaches and the CRO's concern peaks. You go directly with "
        "a costed, auditable answer built from their own scored assessment, reverse-engineered "
        "against the December milestone (VIII, III). In the room you abandon the prepared sequence "
        "when the CFO asks about phasing, and answer that instead (VII). Procurement papers a "
        "decision that has already been made.",
        refs=(CURRICULUM,),
    ),
    _s(
        14,
        SlideKind.CONCEPT,
        "The maturity model, revisited",
        "Return to where section 1 asked you to locate yourself: placeholder, operator, principal, "
        "egoist. The campaign above is a principal's work. What makes it an egoist's is doing it "
        "without being asked, on an account nobody assigned you, with a weapon you chose — and "
        "then "
        "running the same play against the next three firms that share the constraint.",
        refs=(CURRICULUM,),
    ),
    _s(
        15,
        SlideKind.CONCEPT,
        "The Bruntsfield Maxim",
        "The curriculum's closing: the elite seller does not wait for the market to choose them. "
        "They engineer its friction, sharpen a single weapon, and make the largest financial "
        "institutions in the world adapt to their formula. Across all eight convictions the same "
        "instruction recurs in different forms — stop waiting. For the RFP, for the relationship, "
        "for the right moment, for permission to act.",
        refs=(CURRICULUM,),
    ),
    _s(
        16,
        SlideKind.CONCEPT,
        "What the doctrine actually asked of you",
        "To take full personal ownership of the number, and to refuse, permanently, the "
        "comfortable "
        "disappearance of the placeholder. The curriculum's last line is the one to leave with: "
        "the "
        "ability is already in you, and this doctrine exists to wake it. That is a claim about "
        "dormancy rather than deficiency, and it is the same claim section 1 opened with.",
        refs=(CURRICULUM,),
    ),
    _s(
        17,
        SlideKind.CHECKPOINT,
        "Read your objection again",
        "Section 1 asked you to write down your strongest objection to this doctrine before "
        "reading "
        "it. Find it and read it now. Decide, in writing, whether it survived — and if it did, "
        "what "
        "specifically it survives against. An objection that held up through eight sections is "
        "worth raising properly rather than suppressing; take it to your manager.",
        checkpoint="Record whether your original objection survived, and why.",
        refs=(CURRICULUM,),
    ),
    _s(
        18,
        SlideKind.CHECKPOINT,
        "Choose the account you will campaign",
        "One account. Hard and valuable, not easy. Write the four phases against it: what you do "
        "before (I, II, VI), at the trigger (III, IV), during the engagement (V, VII), and at the "
        "close (VIII). Include dates. This is the artefact this whole course exists to produce, "
        "and "
        "it should fit on one page.",
        checkpoint="Produce a one-page campaign plan for one named account, with dates.",
        refs=(CURRICULUM,),
    ),
    _s(
        19,
        SlideKind.CHECKPOINT,
        "Place the assessment in your campaign",
        "On that same page, mark where the Platform Power assessment does its three jobs: which "
        "meeting it opens the committee with, which finding carries your insight, and which "
        "milestone the resulting plan is reverse-engineered from. If you cannot place all three, "
        "the campaign is a sequence of meetings rather than a play.",
        checkpoint="Mark the three points where the assessment does work in your campaign.",
        refs=(CURRICULUM,),
    ),
    _s(
        20,
        SlideKind.CHECKPOINT,
        "Book the first move",
        "The doctrine reduces to two words and this is where they apply. Take the first action on "
        "your campaign plan — the outreach, the public piece, the conversation with the CISO — and "
        "put it in the calendar before you close this course. Not a reminder to plan it. The "
        "action "
        "itself, with a date. Everything above is apparatus for this.",
        checkpoint="Diarise the first concrete action of your campaign, with a date.",
        refs=(CURRICULUM,),
    ),
)

SECTION_8_TEST = SectionTest(
    questions=(
        TestQuestion(
            prompt="In the campaign, which convictions run BEFORE there is a deal?",
            options=(
                "I, II and VI — choose the hard account, enter with one weapon, be present early",
                "I and III — choose the account, then run the documented play",
                "V and VII — orchestrate the committee and operate in flow",
                "Only VIII, since total account awareness is continuous",
            ),
            answer_index=0,
            explanation=(
                "Three of the four opening moves happen with no opportunity in play, which is the "
                "structural reason a reactive seller cannot catch up later. VIII does run "
                "throughout, but it is not the only one operating early."
            ),
        ),
        TestQuestion(
            prompt="What are the three jobs the Platform Power assessment does in a campaign?",
            options=(
                "Opens the committee, manufactures the insight, converts diagnosis into a priced "
                "decision",
                "Qualifies the buyer, sizes the deal, sets the price",
                "Replaces discovery, replaces the demo, replaces the business case",
                "Generates the lead, books the meeting, closes the deal",
            ),
            answer_index=0,
            explanation=(
                "It raises the insight and proof terms of the deal equation with one artefact, and "
                "gives a legitimate reason to meet every seat. What it cannot do is choose the "
                "account or create a catalyst."
            ),
        ),
        TestQuestion(
            prompt="Why is the engine's refusal to overstate itself a commercial asset?",
            options=(
                "Conviction IV puts the CISO and CRO at the centre, and a tool that will not "
                "overstate survives them",
                "It reduces the firm's liability if a client disputes a finding",
                "It shortens the security review by removing contested claims",
                "It allows the assessment to be sold without a client-facing gate",
            ),
            answer_index=0,
            explanation=(
                "The hardest rooms are where the durable weapons are forged, and a diagnostic that "
                "states what it has not assessed is the easiest thing you will ever take into one."
            ),
        ),
        TestQuestion(
            prompt="What does the curriculum say the assessment CANNOT do?",
            options=(
                "Choose the account, or create urgency where no catalyst exists",
                "Produce a quantified insight from the client's own inputs",
                "Give a legitimate reason to meet multiple stakeholders",
                "Provide the spine of a mutual action plan",
            ),
            answer_index=0,
            explanation=(
                "It is an instrument for a campaign already chosen. A seller who waits for an "
                "assessment request has moved the waiting one step earlier, not eliminated it."
            ),
        ),
        TestQuestion(
            prompt="What is the Bruntsfield Maxim's recurring instruction?",
            options=(
                "Stop waiting — for the RFP, the relationship, the right moment, permission",
                "Always be closing, in every conversation",
                "Qualify hard and disqualify early",
                "Lead with insight, never with capability",
            ),
            answer_index=0,
            explanation=(
                "Every conviction is a way of converting a passive habit into a deliberate, "
                "repeatable, self-authored move. The fourth option is true but is one conviction's "
                "field note, not the maxim."
            ),
        ),
        TestQuestion(
            prompt="What distinguishes an egoist from a principal in the maturity model?",
            options=(
                "Doing the campaign unasked, on an unassigned account, then repeating it across "
                "the segment",
                "Closing larger deals than a principal does",
                "Holding a formal certification in the doctrine",
                "Leading a team rather than carrying an individual number",
            ),
            answer_index=0,
            explanation=(
                "The campaign itself is a principal's work. What makes it an egoist's is "
                "self-authorship plus reproducibility — conviction III applied to conviction I."
            ),
        ),
    ),
    pass_mark=0.8,
)


def section_8() -> CourseModule:
    """Section 8: the campaign, and the assessment's place in it."""
    return CourseModule(
        id=_id("module", "the-campaign"),
        title="The campaign: the doctrine on one account, through an ATLAS engagement",
        order=7,
        lessons=(
            Lesson(
                id=_id("lesson", "the-campaign"),
                title="Run all eight against one account, and place the assessment in it",
                body=_S8_BODY,
                order=0,
                author=LessonAuthor.HUMAN,
                slides=_SECTION_8_SLIDES,
                references=(CURRICULUM,),
                drill_topics=("doctrine:the-campaign",),
                measurement=(
                    "You hold a one-page campaign plan for a named account with dates against all "
                    "four phases, the three points where the assessment does work are marked on "
                    "it, "
                    "and the first concrete action is in your calendar."
                ),
            ),
        ),
        section_test=SECTION_8_TEST,
    )


def rebuilt_sections() -> tuple[CourseModule, ...]:
    """The eight sections, in order (GRS-0218)."""
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


# All eight are written. The tuples stay, as they do in the other rebuilt courses, because the
# test that guards them reads them and because the next course rebuilt starts from this pattern.
SECTIONS_AUTHORED: tuple[str, ...] = (
    "the-doctrine",
    "the-battlefield",
    "the-armoury",
    "convictions-1-2",
    "convictions-3-4",
    "convictions-5-6",
    "convictions-7-8",
    "the-campaign",
)
SECTIONS_PLANNED: tuple[str, ...] = ()
