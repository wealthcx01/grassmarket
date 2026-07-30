"""The Sales Operations Playbook, rebuilt to the GRS-0215 depth standard (GRS-0217).

The last course on the ticket, and the only one that is not about a product. Where Sales Egoist is
the *doctrine* (GRS-0218, still blocked on source material), this is the *operational process*: what
an advisor actually does at each pipeline stage.

**Its source of truth is the codebase**, which makes it the most checkable course in the Academy.
Every stage name is a real `PipelineStage` value, the two commission streams are the real
`CommissionStream` members, the recovery fee is the real `CommissionKind.WORKSHOP_RECOVERY_FEE`, and
the Stream B rate axes are the real `DeliveryType` and `SourcingAttribution` values. That is
deliberate: the process the CRM enables and the process the Academy teaches have to be the same
thing, and using the enum's own words is what stops them drifting apart. `test_sales_ops_course.py`
asserts the course quotes the enums rather than a paraphrase of them.

## What this course deliberately does not do

- **No commission figures.** Both streams and the recovery fee resolve live from the v7 schedule.
  A rate typed into content is a rate that goes stale silently and gets quoted anyway.
- **No mixing of score and currency.** Section 5 is built on non-negotiable #7 and ADR-0002: the
  score rates the moat in points, the value bridge prices the lever in pounds, and the two never
  appear in one equation. The contracts enforce it — `ValueBridge.total_lever_npv` sums Money and
  Money only, and a bridge citing an assumption outside its register refuses to construct.
- **No promise that Nurture is failure.** Closed and Nurture are recorded outcomes, and the course
  treats an honest Nurture as a correct answer rather than a lost deal.
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

from grassmarket.workbench.content.sales_ops_diagrams import SVG

_NS = "grassmarket:academy:sales-ops-playbook"


def _id(kind: str, key: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"{_NS}:{kind}:{key}")


# --- Sources. Internal normative documents, because that is what this course is grounded in ----

METHODOLOGY = SourceRef(
    title="ATLAS Methodology v1.2 (normative for scoring)",
    url="https://docs.bruntsfield.capital/atlas/methodology",
    kind=SourceRefKind.DOCS,
)
ADR_VALUE_BRIDGE = SourceRef(
    title="ADR-0002 — two-track scoring, three-layer value bridge",
    url="https://docs.bruntsfield.capital/adr/0002",
    kind=SourceRefKind.DOCS,
)
ADR_STREAMS = SourceRef(
    title="ADR-0026 — Commission Schedule v7, two streams",
    url="https://docs.bruntsfield.capital/adr/0026",
    kind=SourceRefKind.DOCS,
)
SCORING_EXPLAINED = SourceRef(
    title="ATLAS Scoring Explained — the maths, in English",
    url="https://docs.bruntsfield.capital/atlas/scoring-explained",
    kind=SourceRefKind.DOCS,
)
ADR_APPROVAL = SourceRef(
    title="ADR-0009 — AI proposes, humans approve (deliverable approval gate)",
    url="https://docs.bruntsfield.capital/adr/0009",
    kind=SourceRefKind.DOCS,
)
EGOIST = SourceRef(
    title="The Sales Egoist course (the doctrine this process serves)",
    url="https://docs.bruntsfield.capital/academy/sales-egoist",
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
    """A course diagram (GRS-0225 toolchain), generated from the SceneSpec under
    `design/motion/courses/sales_ops/`. Caption and alt text are authored prose and live here,
    beside the slide. `SVG[key]` raises on an unknown key rather than returning a placeholder."""
    return LessonAsset(caption=caption, alt=alt, svg=SVG[key])


# --- Section 1 — The motion, stage by stage -------------------------------------------------

_S1_BODY = (
    "By the end of this lesson you can draw the pipeline from memory, name every stage in the "
    "CRM's own words, and say what has to be true before a deal may move from one to the next. "
    "That last part is the whole point: a stage is not a label somebody applies when it feels "
    "right, it is a claim about what has happened, and a pipeline where the stages are opinions "
    "cannot be forecast from."
)

_SECTION_1_SLIDES: tuple[Slide, ...] = (
    _s(
        0,
        SlideKind.CONCEPT,
        "Why a process at all",
        "Because the alternative is a set of habits that differ per advisor, and a pipeline nobody "
        "can read. The process the CRM enables and the process the Academy teaches have to be one "
        "thing. That is why every stage name in this course is the system's own word rather than a "
        "paraphrase of it: the two drift apart the moment we start describing rather than quoting.",
    ),
    _s(
        1,
        SlideKind.CONCEPT,
        "The motion, stage by stage",
        "Eight stages on the main path — **prospect, workshop scheduled, workshop delivered, "
        "qualified, scoped, contracted, active, delivered** — and two exits available from almost "
        "anywhere: **closed** and **nurture**. Ten in total. Learn them in the system's words, "
        "because those are the words on the board you will actually be looking at.",
        asset=_diagram(
            "the_ten_stages",
            "The whole motion: eight stages, two exits, and where money enters.",
            "A left-to-right path of eight boxes: prospect, workshop scheduled, workshop "
            "delivered, qualified, scoped, contracted, active, delivered. Qualified and contracted "
            "are filled dark green and labelled above as where Stream A and Stream B open. Below "
            "the path sit two more boxes, closed and nurture, described as two exits available "
            "from almost anywhere. A line beneath reads: neither exit is a failure, both are "
            "recorded outcomes you re-open later.",
        ),
    ),
    _s(
        2,
        SlideKind.CONCEPT,
        "A stage is a claim, not a mood",
        "Moving a deal to Qualified asserts that a named, addressable bottleneck exists. Moving it "
        "to Contracted asserts that a scoped engagement with a dated first deliverable is signed. "
        "If the assertion is not true, the move is not available. This is the difference between a "
        "pipeline you can forecast from and a list of things you feel hopeful about.",
    ),
    _s(
        3,
        SlideKind.CONCEPT,
        "The two exits are outcomes, not failures",
        "**Closed** records that this is not happening. **Nurture** records that it is not "
        "happening *yet*, with a dated reason to come back. Neither is a loss of process. What is "
        "a loss of process is a deal left sitting in a middle stage with no date on it, because "
        "that is not an outcome at all — it is nobody having decided.",
    ),
    _s(
        4,
        SlideKind.CONCEPT,
        "Where money enters, and it is two places",
        "Product commission (Stream A) becomes possible at **qualified**, when a represented "
        "product turns out to answer the finding. Consultancy commission (Stream B) opens at "
        "**contracted**, when the work is signed. Those are different moments and different "
        "streams, and section 6 is about not confusing them.",
        refs=(ADR_STREAMS,),
    ),
    _s(
        5,
        SlideKind.CONCEPT,
        "The one decision made before any of it",
        "Who sourced the prospect. Self-sourced pays more than firm-sourced on the consultancy "
        "stream, and that attribution is set at the moment the account is opened. It cannot be "
        "reconstructed nine months later from memory, and the person it costs is you.",
        refs=(ADR_STREAMS,),
    ),
    _s(
        6,
        SlideKind.CONCEPT,
        "How this course maps onto the motion",
        "One section per meaningful move. Section 2 is opening the account. Section 3 is the "
        "workshop. Section 4 is the fork it ends in. Section 5 is scoping and pricing. Section 6 "
        "is contracting and the two streams. Section 7 is delivery. Section 8 is the exits, "
        "including the money most advisors leave behind.",
    ),
    _s(
        7,
        SlideKind.CONCEPT,
        "What this course is not",
        "It is not the doctrine. Why the pipeline is zero-sum, why the workshop is the demo, why "
        "you never leave without an advancing action — that is the Sales Egoist course. This one "
        "assumes you have taken it and answers a narrower question: what do you actually do, at "
        "each stage, and what has to be recorded before you move on.",
        refs=(EGOIST,),
    ),
    _s(
        8,
        SlideKind.CONCEPT,
        "Why the recording matters as much as the doing",
        "An unrecorded qualification is not a qualification. An unrecorded source attribution "
        "costs you money. An unrecorded next step is a deal that will quietly stall. The CRM is "
        "not admin sitting alongside the work — for most of this process it *is* the work, because "
        "it is the only durable evidence that any of it happened.",
    ),
    _s(
        9,
        SlideKind.WALKTHROUGH,
        "Draw the pipeline from memory",
        "On paper, right now: the eight stages in order, then the two exits. Do not look. Then "
        "check. Whatever you missed is the part of the motion you will skip under pressure, which "
        "makes this two minutes the most useful two minutes in the section.",
    ),
    _s(
        10,
        SlideKind.WALKTHROUGH,
        "Open the real board and read the stage names",
        "Go to the Pipeline in the studio and read the stage labels. They are the same words this "
        "course uses, because both come from the same enum. If you ever find a course that "
        "describes a stage the board does not have, the course is wrong — report it rather than "
        "reconciling it in your head.",
    ),
    _s(
        11,
        SlideKind.WALKTHROUGH,
        "Audit your own pipeline against the claims",
        "For every live deal, ask whether the claim its stage makes is actually true. A deal at "
        "Qualified with no recorded finding is mis-staged. So is one at Contracted with no dated "
        "deliverable. Fix the stages before you fix anything else — you cannot manage a board that "
        "is lying to you.",
    ),
    _s(
        12,
        SlideKind.WALKTHROUGH,
        "Find every deal with no date on it",
        "Filter your pipeline for deals with no dated next step. Those are the ones that will "
        "still be there next quarter in the same state. Each one needs either a date or an exit, "
        "and deciding which is the single highest-value hour in your week.",
    ),
    _s(
        13,
        SlideKind.EXAMPLE,
        "A board that cannot be forecast from",
        "Six deals at Qualified, none with a recorded finding. Four at Workshop Delivered from "
        "three months ago. Two at Contracted with no deliverable date. Nothing here is a lie "
        "exactly, and none of it can be forecast from, because every stage means whatever the "
        "advisor felt when they dragged the card.",
    ),
    _s(
        14,
        SlideKind.EXAMPLE,
        "The same board, staged honestly",
        "Two at Qualified with named bottlenecks. Four moved to Nurture with dated return reasons. "
        "Two at Contracted with deliverables dated. It is a smaller pipeline and a real one, and "
        "the forecast that comes off it is worth something. Honest staging usually shrinks a "
        "pipeline before it grows it.",
    ),
    _s(
        15,
        SlideKind.EXAMPLE,
        "What a stale deal actually costs",
        "It is not the deal — that was probably never real. It is your attention: a board with "
        "twenty deals on it, six of which are alive, means every review starts by working out "
        "which six. Do that once, properly, and the review takes ten minutes instead of an hour.",
    ),
    _s(
        16,
        SlideKind.CONCEPT,
        "The rule that covers most of this",
        "Every deal has either a dated next step or an exit. There is no third state. A deal with "
        "neither is not being worked, whatever the board says, and the honest move is to give it "
        "one or the other rather than let it sit.",
    ),
    _s(
        17,
        SlideKind.CONCEPT,
        "Why Nurture is a professional answer",
        "Because pushing a client who does not have the problem is how you lose the account you "
        "would have had in two years. A scored moat that came out strong is a genuine finding, and "
        "saying so is what makes your next assessment credible with them. Nurture with a date is a "
        "result.",
    ),
    _s(
        18,
        SlideKind.CONCEPT,
        "Where the assessment sits in all this",
        "The workshop produces a scored assessment, and that assessment is what makes the "
        'qualification objective. "There is a real bottleneck" stops being your opinion and '
        "becomes a module score with a named subcomponent. That is the difference between this "
        "motion and ordinary consultative selling.",
        refs=(METHODOLOGY,),
    ),
    _s(
        19,
        SlideKind.CONCEPT,
        "One thing to carry into section 2",
        "The attribution. Whatever else you take from this section, take the habit of logging who "
        "sourced a prospect the day the prospect exists. It is thirty seconds, it is invisible for "
        "months, and it is the difference between two rates on the same deal.",
        refs=(ADR_STREAMS,),
    ),
    _s(
        20,
        SlideKind.CHECKPOINT,
        "Recite the ten, in order",
        "Eight on the path and two exits, in the system's own words. Then say what claim each of "
        "Qualified and Contracted makes. If you can only manage the eight, you have most of it — "
        "but the two exits are where the discipline actually lives.",
        checkpoint=(
            "Name all eight path stages and both exits from memory, then the claim Qualified and "
            "Contracted each make."
        ),
    ),
    _s(
        21,
        SlideKind.CHECKPOINT,
        "Re-stage your own board honestly",
        "Go through every live deal and move it to the stage its evidence supports. Expect the "
        "board to shrink. Write down how many deals moved backwards, because that number is the "
        "size of the gap between what you thought you had and what you have.",
        checkpoint=(
            "Re-stage every live deal to what its evidence supports, and count the ones that moved "
            "back."
        ),
    ),
    _s(
        22,
        SlideKind.CONCEPT,
        "The measure for this whole course",
        "Not deals closed. Whether an outside reader could open your pipeline and know, without "
        "asking you, what state every deal is in and what happens next. If they can, the process "
        "is working. If they cannot, the process is in your head, which means it does not survive "
        "your holiday.",
    ),
    _s(
        23,
        SlideKind.CONCEPT,
        "Where this goes next",
        "Section 2 is the first move: opening the account so that it is a deal rather than a "
        "business card — which comes down to three fields, one of which decides money nine months "
        "later.",
    ),
)

SECTION_1_TEST = SectionTest(
    pass_mark=0.8,
    questions=(
        TestQuestion(
            prompt="Why does this course use the CRM's exact stage names rather than paraphrasing?",
            options=(
                "Because the names are trademarked",
                "Because the process the CRM enables and the process the Academy teaches must be\n"
                " one thing, and they drift apart the moment we describe rather than quote",
                "Because the enum values are shorter",
                "Because the board cannot be relabelled",
            ),
            answer_index=1,
            explanation=(
                "If you find a course describing a stage the board does not have, the course is "
                "wrong — report it rather than reconciling it in your head."
            ),
        ),
        TestQuestion(
            prompt="What does moving a deal to Qualified assert?",
            options=(
                "That the client was enthusiastic",
                "That a named, addressable bottleneck exists — and if that is not true, the move\n"
                " is not available",
                "That a workshop has been delivered",
                "That a price has been discussed",
            ),
            answer_index=1,
            explanation=(
                "A stage is a claim, not a mood. That is the difference between a pipeline you can "
                "forecast from and a list of things you feel hopeful about."
            ),
        ),
        TestQuestion(
            prompt="Where do the two commission streams enter the motion?",
            options=(
                "Both at Contracted",
                "Stream A becomes possible at Qualified when a product answers the finding;\n"
                " Stream B opens at Contracted when the work is signed",
                "Both at Qualified",
                "Stream A at Prospect, Stream B at Delivered",
            ),
            answer_index=1,
            explanation=(
                "Different moments and different streams. Confusing them is how a forecast ends up "
                "counting money that has not become possible yet."
            ),
        ),
        TestQuestion(
            prompt="What is the rule that covers most stale-pipeline problems?",
            options=(
                "Review the board weekly",
                "Every deal has either a dated next step or an exit. There is no third state",
                "Close anything older than a quarter",
                "Never exceed twenty live deals",
            ),
            answer_index=1,
            explanation=(
                "A deal with neither is not being worked, whatever the board says. Giving it one "
                "or the other is the honest move."
            ),
        ),
        TestQuestion(
            prompt="Why is moving a deal to Nurture a professional answer rather than a loss?",
            options=(
                "Because it keeps the pipeline number up",
                "Because pushing a client who does not have the problem loses the account you\n"
                " would have had in two years; a strong scored moat is a genuine finding",
                "Because Nurture deals still pay a recovery fee automatically",
                "Because it defers the decision",
            ),
            answer_index=1,
            explanation=(
                "Saying so honestly is what makes your next assessment credible with them. Nurture "
                "with a date is a result."
            ),
        ),
        TestQuestion(
            prompt="What is the measure of success for this whole course?",
            options=(
                "Deals closed per quarter",
                "Whether an outside reader could open your pipeline and know, without asking you,\n"
                " what state every deal is in and what happens next",
                "Number of workshops delivered",
                "Average time in each stage",
            ),
            answer_index=1,
            explanation=(
                "If they cannot, the process is in your head — which means it does not survive "
                "your holiday."
            ),
        ),
    ),
)


def section_1() -> CourseModule:
    """Section 1: the motion, and why a stage is a claim."""
    return CourseModule(
        id=_id("module", "the-motion"),
        title="The motion, stage by stage",
        order=0,
        lessons=(
            Lesson(
                id=_id("lesson", "the-motion"),
                title="Ten stages, and what each one claims",
                body=_S1_BODY,
                order=0,
                slides=_SECTION_1_SLIDES,
                drill_topics=("ops:the-motion",),
                measurement=(
                    "You can draw the pipeline from memory and every live deal on your board is at "
                    "the stage its evidence supports."
                ),
            ),
        ),
        section_test=SECTION_1_TEST,
    )


# --- Section 2 — Prospect: open the account properly ----------------------------------------

_S2_BODY = (
    "The first move, and the one that quietly decides what you earn. By the end of this lesson you "
    "know the three fields that turn a name into a deal, why one of them cannot be added later, "
    "and what a prospect record has to contain before you are allowed to say the account is open."
)

_SECTION_2_SLIDES: tuple[Slide, ...] = (
    _s(
        0,
        SlideKind.CONCEPT,
        "A prospect record, or a business card",
        "Anyone can type a company and a contact. Three more fields are what make it a deal: the "
        "**growth pain in their words**, **who sourced it**, and **a dated next step**. A record "
        "with the first two fields and none of the last three is a business card in a database.",
        asset=_diagram(
            "what_a_prospect_needs",
            "Five fields. The bottom three are the ones that make it a deal.",
            "A record card listing five fields. The top two, company and contact, and sector, are "
            "plain. The bottom three are filled dark green: the growth pain verbatim, who sourced "
            "it, and a dated next step. Notes to the right explain that no pain means no reason to "
            "meet, and that sourcing decides your rate later. A warning beneath reads: log who "
            "sourced it on day one, nobody can reconstruct it in month nine.",
        ),
    ),
    _s(
        1,
        SlideKind.CONCEPT,
        "The growth pain, in their words",
        "Not your summary of it. The sentence they actually said, captured close enough to quote "
        'back. "Onboarding takes too long" is worth more in the notes than "operational '
        'inefficiency in client onboarding", because the first is something you can open a '
        "conversation with three weeks later and the second is something you wrote.",
    ),
    _s(
        2,
        SlideKind.CONCEPT,
        "Why verbatim matters commercially",
        'Because the workshop gets booked off it. "You mentioned onboarding takes too long — that '
        'is exactly what a Platform Power workshop scores" only works if you have the phrase. '
        "Paraphrased, it becomes a generic pitch, and a generic pitch does not earn ninety minutes "
        "of a COO's time.",
    ),
    _s(
        3,
        SlideKind.CONCEPT,
        "Sourcing attribution, and why it is now or never",
        "Self-sourced pays more than firm-sourced on the consultancy stream. That attribution is a "
        "fact about how the prospect came to exist, and it is knowable on day one and "
        "unreconstructable by month nine. Nobody will fight you for it — they will simply not be "
        "able to establish it, and the default will not be the one that pays you more.",
        refs=(ADR_STREAMS,),
    ),
    _s(
        4,
        SlideKind.CONCEPT,
        "The four attributions, and the two that carry a rate",
        "The system records self-sourced, firm-sourced, Bruntsfield-sourced and co-sourced. The v7 "
        "schedule prices **self-sourced and firm-sourced**. That is worth knowing: the other two "
        "are real states that describe how a deal arrived, and they are not v7 rate cells. If a "
        "deal is genuinely co-sourced, say so and let the schedule be applied rather than "
        "guessing.",
        refs=(ADR_STREAMS,),
    ),
    _s(
        5,
        SlideKind.CONCEPT,
        "The dated next step",
        "A date, on the record, for the next thing that happens. Ideally a booked workshop. "
        'Acceptably a call with a date. Never "follow up in a few weeks", because a few weeks '
        "has no end and the deal will still be there next quarter in exactly this state.",
    ),
    _s(
        6,
        SlideKind.CONCEPT,
        "What a good first move actually looks like",
        'You hear the pain, and you book off it there and then. Not "I\'ll add you to our list" — '
        "that is the passive version and it converts at roughly nothing. The move is to name the "
        "workshop, say what it does, offer a specific date, and leave with it held.",
        refs=(EGOIST,),
    ),
    _s(
        7,
        SlideKind.CONCEPT,
        "Why the workshop is the ask, not a meeting",
        "Because a meeting is a favour and a workshop is a product with a deliverable. Ninety "
        "minutes, on their own numbers, producing a scored assessment. That is a thing a busy "
        "person can say yes to, and it advances the deal by itself rather than creating another "
        "conversation about having a conversation.",
        refs=(EGOIST,),
    ),
    _s(
        8,
        SlideKind.CONCEPT,
        "The sector field, which is not decoration",
        "Sector drives the operating-model profile, which drives which modules the assessment "
        "scores and which products the sell panel will offer against the findings. Get it wrong "
        "and the whole downstream chain is subtly wrong — a retail brokerage assessed on an "
        "exchange profile produces recommendations for the wrong business.",
    ),
    _s(
        9,
        SlideKind.WALKTHROUGH,
        "Open a real prospect end to end",
        "In the studio, create a prospect with all five fields filled properly — including a pain "
        "you have actually heard and a real date. Time it. It takes under two minutes, which is "
        "the point: the reason records are thin is never that it is slow.",
    ),
    _s(
        10,
        SlideKind.WALKTHROUGH,
        "Audit your existing prospects for the three fields",
        "Go through every prospect you already have and check for the pain, the source and the "
        "date. Count how many have all three. That number, divided by your total, is the honest "
        "state of your top of funnel, and it is usually lower than people expect.",
    ),
    _s(
        11,
        SlideKind.WALKTHROUGH,
        "Fix the sourcing on everything you can still remember",
        "For the ones missing attribution, set it now while you still know. This is a one-off "
        "piece of work with a direct financial consequence, and every week you leave it the number "
        "of records you can honestly reconstruct goes down.",
        refs=(ADR_STREAMS,),
    ),
    _s(
        12,
        SlideKind.WALKTHROUGH,
        "Write your booking sentence",
        "Write the exact words you use to turn a mentioned pain into a held date. Yours, not mine. "
        "It has to name the pain, name the workshop, say how long it takes, and offer a specific "
        "day. Four elements, one sentence, and you will use it more than anything else in this "
        "course.",
    ),
    _s(
        13,
        SlideKind.EXAMPLE,
        "The passive version",
        '"That\'s really interesting — let me send you some information and we can find a time." '
        "Nothing was decided, nothing was dated, and the pain was not captured. Three weeks later "
        'you are opening with "just following up", which is the weakest sentence in sales.',
    ),
    _s(
        14,
        SlideKind.EXAMPLE,
        "The ops version",
        '"Onboarding taking too long is exactly what the Platform Power workshop scores — ninety '
        "minutes, on your own numbers, and you get the assessment out of it. I've got Thursday the "
        '12th; shall I hold it?" A dated workshop, and the pain goes in the notes in their words.',
    ),
    _s(
        15,
        SlideKind.EXAMPLE,
        "The record that costs you money nine months later",
        "Everything filled except sourcing. The deal converts, the engagement is large, and the "
        "attribution defaults to the one that pays less because nobody can now establish "
        "otherwise. The work was identical; the record was not. This is the most avoidable loss in "
        "the whole motion.",
        refs=(ADR_STREAMS,),
    ),
    _s(
        16,
        SlideKind.CONCEPT,
        "What not to put in a prospect record",
        "Speculation about budget. Your opinion of the person. Anything you would not want the "
        "client to read. The record is organisational memory, not a diary, and it will outlive "
        "your involvement in the account.",
    ),
    _s(
        17,
        SlideKind.CONCEPT,
        "The contact matters more than the company",
        "A company does not have a pain; a person does. Record who said it and what their role is, "
        "because when they move — and they do — you need to know whether the pain moved with them "
        "or stayed with the seat.",
    ),
    _s(
        18,
        SlideKind.CONCEPT,
        "One prospect, one record",
        "Two advisors opening the same company separately produces two records, two histories and "
        "an attribution argument. Search before you create. It takes five seconds and it prevents "
        "the one conversation nobody in a small firm wants to have.",
    ),
    _s(
        19,
        SlideKind.CONCEPT,
        "The standard for this stage, stated plainly",
        "Within a week of a prospect existing, it has a captured pain, a recorded source and "
        "either a booked workshop or a dated next step. If it does not, it is not a prospect you "
        "are working — and the honest move is to either work it or let it go.",
    ),
    _s(
        20,
        SlideKind.CHECKPOINT,
        "Say the five fields, then the three that matter",
        "From memory: all five, then which three make it a deal, then which single one cannot be "
        "reconstructed later. If you only remember one thing from this section, it should be the "
        "last of those.",
        checkpoint=(
            "Name all five prospect fields, the three that make it a deal, and the one that cannot "
            "be added later."
        ),
    ),
    _s(
        21,
        SlideKind.CHECKPOINT,
        "Use your booking sentence for real",
        "Say it out loud, then use it on the next prospect conversation you have. Come back and "
        "note whether you left with a date. That is the only measure of this section that means "
        "anything.",
        checkpoint="Say your booking sentence aloud, then use it on a real conversation.",
    ),
    _s(
        22,
        SlideKind.CONCEPT,
        "Why this section is short on theory",
        "Because there is not much. Capture the pain, record the source, book the date. The reason "
        "it gets a section is not that it is complicated, it is that it is skipped — and the cost "
        "of skipping it does not show up for months.",
    ),
    _s(
        23,
        SlideKind.CONCEPT,
        "Where this goes next",
        "Section 3 is the workshop itself: what makes it an advancing action rather than a "
        "courtesy call, and why it is the demo rather than a step towards one.",
    ),
)

SECTION_2_TEST = SectionTest(
    pass_mark=0.8,
    questions=(
        TestQuestion(
            prompt="Which three fields turn a name into a deal?",
            options=(
                "Company, contact and sector",
                "The growth pain in their words, who sourced it, and a dated next step",
                "Sector, budget and decision-maker",
                "Contact, phone number and a follow-up reminder",
            ),
            answer_index=1,
            explanation=(
                "Anyone can type a company and a contact. A record with only those is a business "
                "card in a database."
            ),
        ),
        TestQuestion(
            prompt="Why must the sourcing attribution be recorded on day one?",
            options=(
                "Because the CRM requires it",
                "Because it is knowable on day one and unreconstructable by month nine, and the\n"
                " default will not be the attribution that pays you more",
                "Because it affects which profile is used",
                "Because it determines the workshop date",
            ),
            answer_index=1,
            explanation=(
                "Nobody will fight you for it — they simply will not be able to establish it. The "
                "work is identical; the record is not."
            ),
        ),
        TestQuestion(
            prompt="Why capture the growth pain verbatim rather than paraphrased?",
            options=(
                "For compliance reasons",
                "Because the workshop gets booked off it, and quoting their phrase back works\n"
                " where a paraphrase becomes a generic pitch",
                "Because paraphrases are often inaccurate",
                "Because the assessment engine parses it",
            ),
            answer_index=1,
            explanation=(
                "A generic pitch does not earn ninety minutes of a COO's time. Their sentence does."
            ),
        ),
        TestQuestion(
            prompt="How many sourcing attributions exist, and how many carry a v7 rate?",
            options=(
                "Two exist and both carry a rate",
                "Four exist — self, firm, Bruntsfield and co-sourced — and the schedule prices\n"
                " self-sourced and firm-sourced",
                "Three exist and one carries a rate",
                "Four exist and all four carry a rate",
            ),
            answer_index=1,
            explanation=(
                "The other two are real states describing how a deal arrived. If a deal is "
                "genuinely co-sourced, say so and let the schedule be applied rather than guessing."
            ),
        ),
        TestQuestion(
            prompt="Why is the sector field not decoration?",
            options=(
                "It is used for reporting only",
                "It drives the operating-model profile, which drives which modules are scored and\n"
                " which products the sell panel offers",
                "It sets the commission stream",
                "It determines the workshop length",
            ),
            answer_index=1,
            explanation=(
                "Get it wrong and the whole downstream chain is subtly wrong — a retail brokerage "
                "assessed on an exchange profile produces recommendations for the wrong business."
            ),
        ),
        TestQuestion(
            prompt="What is the standard for this stage?",
            options=(
                "A prospect record created within 24 hours",
                "Within a week: a captured pain, a recorded source, and either a booked workshop\n"
                " or a dated next step",
                "A qualified budget and an identified decision-maker",
                "A first meeting held within a month",
            ),
            answer_index=1,
            explanation=(
                "If it does not have those, it is not a prospect you are working — and the honest "
                "move is to either work it or let it go."
            ),
        ),
    ),
)


def section_2() -> CourseModule:
    """Section 2: opening the account, and the field that decides your rate."""
    return CourseModule(
        id=_id("module", "open-the-account"),
        title="Prospect: open the account properly",
        order=1,
        lessons=(
            Lesson(
                id=_id("lesson", "open-the-account"),
                title="Three fields, and one that cannot wait",
                body=_S2_BODY,
                order=0,
                slides=_SECTION_2_SLIDES,
                drill_topics=("ops:open-and-book",),
                measurement=(
                    "Every prospect you open has a verbatim pain, a recorded source and a dated "
                    "next step within a week."
                ),
            ),
        ),
        section_test=SECTION_2_TEST,
    )


# --- Section 3 — The workshop: the advancing action -----------------------------------------

_S3_BODY = (
    "Two meetings can look identical in a calendar and be completely different events. By the end "
    "of this lesson you know what makes the Platform Power workshop an advancing action rather "
    "than a courtesy call, how to run it so the client does the discovering, and what has to leave "
    "the room with you before you are allowed to call it delivered."
)

_SECTION_3_SLIDES: tuple[Slide, ...] = (
    _s(
        0,
        SlideKind.CONCEPT,
        "Two meetings, one calendar entry",
        "In one you describe a methodology and they say it sounds interesting. In the other they "
        "watch their own moat get scored on their own numbers. The calendar cannot tell them apart "
        "and the pipeline can: only one of them ends with a finding and a date.",
        asset=_diagram(
            "the_workshop_is_the_demo",
            "The same ninety minutes, run two ways. Only one of them advances anything.",
            "Two panels. On the left, a courtesy call: you describe the methodology, they say it "
            "sounds interesting, and there is no dated next step. On the right, outlined in green, "
            "an advancing action: they watch their own moat get scored, on their own numbers, in "
            "ninety minutes, producing a finding and a date. A line beneath reads: the workshop IS "
            "the demo, book it off a pain you actually heard.",
        ),
    ),
    _s(
        1,
        SlideKind.CONCEPT,
        "The workshop is the demo",
        "This is the doctrine's line and it is worth restating operationally: there is no separate "
        "demo to work towards. The scoring session *is* the product experience. A client who has "
        "sat through one has used the thing, which is why the motion has no stage between workshop "
        "and qualification.",
        refs=(EGOIST,),
    ),
    _s(
        2,
        SlideKind.CONCEPT,
        "Why that changes how you run it",
        "If it is the demo, you are not presenting — you are operating the tool in front of them "
        "with their inputs. The measure of a good workshop is how much of the talking they did. A "
        "session where you explained the methodology beautifully for ninety minutes is a session "
        "where nothing got scored.",
    ),
    _s(
        3,
        SlideKind.CONCEPT,
        "Score live, not afterwards",
        "Take the ratings in the room, with them watching. It is slower, it produces arguments, "
        "and the arguments are the value: a client who has disagreed with a rating and been talked "
        "through the rubric now believes the number. One produced afterwards is your opinion "
        "delivered by email.",
        refs=(METHODOLOGY,),
    ),
    _s(
        4,
        SlideKind.CONCEPT,
        "Use the evidence grades honestly in the room",
        "When they assert something you cannot evidence, grade it as what it is rather than taking "
        "it at face value. Doing that visibly is one of the strongest credibility moves available: "
        "it shows the score is a measurement rather than a flattery exercise, and it makes the "
        "findings they *do* get harder to dismiss.",
        refs=(METHODOLOGY,),
    ),
    _s(
        5,
        SlideKind.CONCEPT,
        "Not Assessed is a legitimate answer",
        "If a module genuinely cannot be judged in the room, mark it Not Assessed rather than "
        "guessing. It never contributes to any score, which is the point — a guess would. Saying "
        '"we do not have enough to judge that today" is more professional than a number nobody '
        "can defend.",
        refs=(METHODOLOGY,),
    ),
    _s(
        6,
        SlideKind.CONCEPT,
        "What has to leave the room with you",
        "A scored assessment, a named bottleneck or an honest absence of one, and a dated next "
        "step. Three things. If you have the first two and not the third, you have done good work "
        "and left it to decay.",
    ),
    _s(
        7,
        SlideKind.CONCEPT,
        "Move the stage the same day",
        "Workshop delivered is a transient state, not a resting place. The board should show the "
        "outcome — Qualified or Nurture — within a day, because a deal that sits at Delivered is "
        "one nobody has decided about and the deciding gets harder every week.",
    ),
    _s(
        8,
        SlideKind.CONCEPT,
        "Who should be in the room",
        "Somebody who owns a number. A COO, a head of product, a head of operations. Not "
        "exclusively a technologist: the findings are about the business model and its "
        "bottlenecks, and a room with only engineers in it produces a technically interesting "
        "session with nobody to act on it.",
    ),
    _s(
        9,
        SlideKind.CONCEPT,
        "Ninety minutes is the promise, so keep it",
        "You sold ninety minutes. Running to two hours costs you the next one, however good it "
        "was. Cover fewer modules properly rather than all of them badly — an assessment with "
        "three modules genuinely scored and the rest Not Assessed is more useful than one where "
        "everything got a hurried guess.",
        refs=(METHODOLOGY,),
    ),
    _s(
        10,
        SlideKind.WALKTHROUGH,
        "Run one against the seeded demo data",
        "Open the studio's demo assessment and work through a module as though the client were "
        "watching: read the anchor, take the rating, set the evidence grade. Do it out loud. The "
        "point is to find where you stumble over the rubric wording before a client hears you do "
        "it.",
        refs=(SCORING_EXPLAINED,),
    ),
    _s(
        11,
        SlideKind.WALKTHROUGH,
        "Practise the disagreement",
        "Have someone push back on a rating you have just given and talk them through the anchor "
        "until you both land somewhere. This is the single most valuable ninety seconds of a real "
        "workshop and the one advisors handle worst, because the instinct is to concede rather "
        "than to explain.",
        refs=(METHODOLOGY,),
    ),
    _s(
        12,
        SlideKind.WALKTHROUGH,
        "Write your ninety-second opening",
        "What you say in the first ninety seconds of the workshop: what is about to happen, how "
        "long it takes, what they get, and what you need from them. Four things. Get this right "
        "and the rest of the session runs itself; get it wrong and you spend twenty minutes "
        "re-explaining.",
    ),
    _s(
        13,
        SlideKind.WALKTHROUGH,
        "Time yourself on one module",
        "Score a single module end to end and time it. Multiply by the number you intend to cover. "
        "If the answer is more than ninety minutes, you now know before the meeting rather than "
        "during it, and you can choose what to drop deliberately.",
    ),
    _s(
        14,
        SlideKind.EXAMPLE,
        "A workshop that was really a presentation",
        "You talked for eighty minutes about the seven powers, they nodded, and you promised to "
        "send the assessment over. Nothing was scored in the room, nothing was disagreed with, and "
        "the email you send lands as a document rather than as a conclusion they helped reach.",
    ),
    _s(
        15,
        SlideKind.EXAMPLE,
        "A workshop that advanced",
        "You scored switching costs live. They pushed back on the rating. You read the anchor, "
        "they conceded the linked-account depth was thin, and the finding is now theirs rather "
        "than yours. You leave at Qualified with the finding recorded verbatim and a scoping call "
        "dated.",
    ),
    _s(
        16,
        SlideKind.EXAMPLE,
        "The workshop that found nothing, done well",
        'Everything scored strong. There is no addressable bottleneck, and you say so: "Honestly, '
        'your moat is in better shape than most — I do not think you need us this year." Nurture, '
        "dated, and the most credible thing you will ever say to that client. They will remember "
        "it when something does break.",
    ),
    _s(
        17,
        SlideKind.CONCEPT,
        "The comparison an advisor should not make",
        "Do not tell a client how they score against other firms you have assessed. Those "
        "assessments belong to those clients, the scoping is absolute, and a comparison is worth "
        "far less than the finding in front of them anyway.",
    ),
    _s(
        18,
        SlideKind.CONCEPT,
        "What to do with the assessment afterwards",
        "Finalise it. An unfinalised assessment is a working document and a finalised one is a "
        "record with locked inputs. The scoping conversation in section 5 refers back to it, and "
        "referring back to something still editable undermines the whole point of the method.",
        refs=(METHODOLOGY,),
    ),
    _s(
        19,
        SlideKind.CONCEPT,
        "The standard for this stage",
        "Every delivered workshop leaves the room with a scored assessment, an outcome decided "
        'within a day, and the specific finding recorded in the client\'s words. "It went well" '
        "is not a record of anything.",
    ),
    _s(
        20,
        SlideKind.CHECKPOINT,
        "Say the three things that must leave the room",
        "From memory, and then say what you do if you only have two of them. The answer to the "
        "second half is what separates advisors whose pipelines can be forecast from those whose "
        "cannot.",
        checkpoint=(
            "Name the three things that must leave the workshop, and what you do if the third is "
            "missing."
        ),
    ),
    _s(
        21,
        SlideKind.CHECKPOINT,
        "Deliver your ninety-second opening out loud",
        "All four elements, timed. If it runs over two minutes it is too long — this is the part "
        "of the session where you are asking for their attention rather than earning it, so it "
        "should be the shortest thing you say all meeting.",
        checkpoint="Deliver your ninety-second workshop opening aloud, timed, all four elements.",
    ),
    _s(
        22,
        SlideKind.CONCEPT,
        "Why this stage is where most value is created",
        "Because it is the only point in the motion where the client experiences the method rather "
        "than hearing about it. Everything after this is administration of a conclusion they "
        "reached in the room. Everything before it is trying to get them into the room.",
    ),
    _s(
        23,
        SlideKind.CONCEPT,
        "Where this goes next",
        "Section 4 is the fork the workshop ends in: qualified against a named bottleneck, or "
        "nurtured with a date. It also covers the third outcome that is not an outcome at all, and "
        "which is where more pipeline value is lost than anywhere else in the motion.",
    ),
)

SECTION_3_TEST = SectionTest(
    pass_mark=0.8,
    questions=(
        TestQuestion(
            prompt="What does 'the workshop is the demo' mean operationally?",
            options=(
                "That you should demo the software during the workshop",
                "That there is no separate demo to work towards — the scoring session IS the\n"
                " product experience, which is why no stage sits between workshop and "
                "qualification",
                "That the workshop replaces the proposal",
                "That the assessment should be sent afterwards",
            ),
            answer_index=1,
            explanation=(
                "A client who has sat through one has used the thing. That is what makes it an "
                "advancing action rather than a step towards one."
            ),
        ),
        TestQuestion(
            prompt="Why score live in the room rather than afterwards?",
            options=(
                "It saves time",
                "Because disagreement is the value: a client talked through the rubric believes\n"
                " the number, where one produced afterwards is your opinion delivered by email",
                "Because the engine requires it",
                "Because it avoids a second meeting",
            ),
            answer_index=1,
            explanation=(
                "It is slower and it produces arguments, and the arguments are the point. The "
                "finding becomes theirs rather than yours."
            ),
        ),
        TestQuestion(
            prompt="A module genuinely cannot be judged in the room. What do you do?",
            options=(
                "Give it a middle rating",
                "Mark it Not Assessed, which never contributes to any score — a guess would",
                "Score it from public information afterwards",
                "Ask the client to self-rate it",
            ),
            answer_index=1,
            explanation=(
                '"We do not have enough to judge that today" is more professional than a number '
                "nobody can defend."
            ),
        ),
        TestQuestion(
            prompt="What are the three things that must leave the room with you?",
            options=(
                "A proposal, a price and a decision-maker",
                "A scored assessment, a named bottleneck or an honest absence of one, and a dated\n"
                " next step",
                "A signed engagement letter and two references",
                "Notes, a follow-up email and a calendar invite",
            ),
            answer_index=1,
            explanation=(
                "With the first two and not the third, you have done good work and left it to "
                "decay."
            ),
        ),
        TestQuestion(
            prompt="Everything scores strong and there is no addressable bottleneck. What now?",
            options=(
                "Look harder for a weakness to sell against",
                "Say so plainly and move to Nurture with a date — it is the most credible thing\n"
                " you will say to that client",
                "Score a borderline module lower to create an opening",
                "Leave the deal at Workshop Delivered",
            ),
            answer_index=1,
            explanation=(
                "They will remember it when something does break. Pushing a fix they do not need "
                "loses the account you would have had later."
            ),
        ),
        TestQuestion(
            prompt="Why should you never tell a client how they score against other firms?",
            options=(
                "Because the comparison is usually unflattering",
                "Because those assessments belong to those clients, scoping is absolute, and the\n"
                " comparison is worth less than the finding in front of them anyway",
                "Because the scores are not comparable across profiles",
                "Because it requires committee approval",
            ),
            answer_index=1,
            explanation=(
                "Both a scoping rule and a sales point: the finding in front of them is the thing "
                "that moves the deal."
            ),
        ),
    ),
)


def section_3() -> CourseModule:
    """Section 3: the workshop as the advancing action."""
    return CourseModule(
        id=_id("module", "the-workshop"),
        title="The workshop: the advancing action",
        order=2,
        lessons=(
            Lesson(
                id=_id("lesson", "the-workshop"),
                title="Ninety minutes, scored live",
                body=_S3_BODY,
                order=0,
                slides=_SECTION_3_SLIDES,
                drill_topics=("ops:deliver-and-qualify",),
                measurement=(
                    "Every workshop you run is scored live in the room and leaves with a finding "
                    "and a dated next step."
                ),
            ),
        ),
        section_test=SECTION_3_TEST,
    )


# --- Section 4 — Qualified or Nurture: the honest fork --------------------------------------

_S4_BODY = (
    "Every workshop ends in one of two states, and the most common failure is ending in neither. "
    "By the end of this lesson you can qualify against a named bottleneck rather than a feeling, "
    "recognise when Nurture is the correct professional answer, and explain why a deal left at "
    "Workshop Delivered is not a third option."
)

_SECTION_4_SLIDES: tuple[Slide, ...] = (
    _s(
        0,
        SlideKind.CONCEPT,
        "Two states, and one non-answer",
        "**Qualified** if there is a real, addressable bottleneck. **Nurture** if there is not, "
        "with a dated reason to return. Left at Workshop Delivered is not a third answer — it is "
        "nobody having decided, and it is where most pipelines quietly rot.",
        asset=_diagram(
            "qualify_or_nurture",
            "One question, two honest answers, and the non-answer that is where pipelines rot.",
            "A decision box asking whether there is a real, addressable bottleneck. A Yes branch "
            "leads to Qualified, filled dark green, meaning advance with the finding recorded. A "
            "No branch leads to Nurture, meaning say so honestly with a dated reason to return. A "
            "warning beneath reads: left at Delivered is not a third answer, it is nobody having "
            'decided. A final line adds: "it went well" is not a qualification, a named '
            "bottleneck is.",
        ),
    ),
    _s(
        1,
        SlideKind.CONCEPT,
        "What makes a bottleneck real",
        "It came out of the scoring rather than the conversation. A module or subcomponent rated "
        "low, with an evidence grade you would defend, on something that actually constrains the "
        'business. "They mentioned they\'d like better reporting" is a wish. A weak '
        "switching-cost module with thin linked-account depth is a finding.",
        refs=(METHODOLOGY,),
    ),
    _s(
        2,
        SlideKind.CONCEPT,
        "What makes it addressable",
        "That something can be done about it inside a scope somebody would buy. A structural "
        "constraint you cannot move — their licence, their ownership, their market — is a real "
        "weakness and not an engagement. Qualifying on an unaddressable finding produces a "
        "proposal nobody can act on.",
    ),
    _s(
        3,
        SlideKind.CONCEPT,
        "Record the finding verbatim",
        "The specific module, the specific subcomponent, and the sentence you would use to "
        'describe it back to them. Not "weak moat". The scoping conversation happens weeks later '
        "and it opens by referring to this, so it needs to be something you can read aloud rather "
        "than something you have to reconstruct.",
    ),
    _s(
        4,
        SlideKind.CONCEPT,
        "Where the second door opens",
        "If a product you represent is what closes that specific gap, this is the moment Stream A "
        "enters — alongside the consultancy work rather than instead of it. Notice it here rather "
        "than later: the sell panel surfaces the products that fit the findings and the profile, "
        "and it is at its most useful the day the assessment is finalised.",
        refs=(ADR_STREAMS,),
    ),
    _s(
        5,
        SlideKind.CONCEPT,
        "Both doors, or either, or neither",
        "A deal can be consultancy only, product only, both, or nothing. All four are legitimate "
        "outcomes of a qualification. What is not legitimate is deciding which one it is before "
        "the assessment has told you, which is what happens when an advisor arrives having already "
        "decided what they are selling.",
    ),
    _s(
        6,
        SlideKind.CONCEPT,
        "Nurture is a decision, not a shelf",
        'It means: no engagement now, and here is the dated reason we come back. "Their new COO '
        'starts in April" or "they re-platform next year" or simply "six months". A Nurture '
        "with no date is a Closed nobody was willing to write down.",
    ),
    _s(
        7,
        SlideKind.CONCEPT,
        "Why an honest Nurture is commercially valuable",
        "Because it is the thing that makes your next assessment credible with them. An advisor "
        'who has once said "you do not need us" is an advisor whose findings are worth listening '
        "to. An advisor who has never said it is a salesperson with a methodology attached.",
    ),
    _s(
        8,
        SlideKind.CONCEPT,
        "The tell that you are forcing it",
        "You find yourself arguing the client into a weakness they do not recognise. If the "
        "finding were real and addressable they would recognise it — they run the business. "
        "Persistent disagreement after you have read them the anchor is usually information, not "
        "resistance.",
        refs=(METHODOLOGY,),
    ),
    _s(
        9,
        SlideKind.CONCEPT,
        "Why Delivered rots specifically",
        "Because it is the only stage where the work is done and the decision is not. Every other "
        "stalled stage has an obvious owner and an obvious next action. This one feels finished, "
        "so it drops off the review, and three months later nobody remembers enough to qualify it "
        "either way.",
    ),
    _s(
        10,
        SlideKind.WALKTHROUGH,
        "Write two findings, one real and one not",
        "Take a real assessment and write the strongest genuine finding, then write the sort of "
        "vague one you would be tempted by on a slow month. Put them side by side. The difference "
        "is usually that one names a module and the other names a feeling.",
    ),
    _s(
        11,
        SlideKind.WALKTHROUGH,
        "Check your board for deals stuck at Delivered",
        "Filter for Workshop Delivered and look at the dates. Anything older than a week is a "
        "decision you have not made. Make them now — Qualified with a finding, or Nurture with a "
        "date. Both are fine. Leaving them is not.",
    ),
    _s(
        12,
        SlideKind.WALKTHROUGH,
        "Write your Nurture sentence",
        "The words you use to tell a client they do not need you this year, without it sounding "
        "like you failed to find something. It should be short, specific about what was strong, "
        "and carry the date. Practise it, because saying it well is harder than it looks.",
    ),
    _s(
        13,
        SlideKind.WALKTHROUGH,
        "Open the sell panel on a finalised assessment",
        "Look at what it offers against the findings for that profile. Note that it is scoped — it "
        "will not offer a variant that does not fit the segment. That is the Stream A door, and "
        "seeing it once means you will remember to look at it when it matters.",
    ),
    _s(
        14,
        SlideKind.EXAMPLE,
        "A qualification that holds",
        '"The switching-cost module came out weak, specifically linked-account depth — you have '
        "single-product relationships where competitors have three. That is addressable and it is "
        'what I would scope against." A named module, a named subcomponent, a business '
        "consequence.",
    ),
    _s(
        15,
        SlideKind.EXAMPLE,
        "A qualification that does not",
        '"There is definitely room to improve the client experience." No module, no '
        "subcomponent, no consequence, and nothing to scope. This will produce a proposal that "
        "reads as generic consulting, and it will lose to the incumbent who at least knows the "
        "business.",
    ),
    _s(
        16,
        SlideKind.EXAMPLE,
        "A Nurture that earns the next meeting",
        '"Your scale economies and switching costs both came out strong — genuinely, this is a '
        "better book than most I score. I do not think there is an engagement here this year. You "
        "mentioned re-platforming in eighteen months; that is when this conversation gets "
        'interesting, so I will come back then."',
    ),
    _s(
        17,
        SlideKind.CONCEPT,
        "The one-day rule",
        "The outcome is on the board within a day of the workshop. Not because a day is magic, but "
        "because the decision is easiest while the session is fresh and gets monotonically harder "
        "afterwards. Everything about this stage is a fight against deferral.",
    ),
    _s(
        18,
        SlideKind.CONCEPT,
        "What Closed is for, at this stage",
        "Rarely used here. Closed is for a deal that is genuinely not happening — they said no, "
        "they were acquired, they have no budget and no horizon. Most post-workshop outcomes are "
        "Nurture rather than Closed, because a scored assessment is a relationship you have "
        "already invested in.",
    ),
    _s(
        19,
        SlideKind.CONCEPT,
        "The standard for this stage",
        "Every delivered workshop is Qualified or Nurture within a day. Every Qualified cites a "
        "named module or subcomponent. Every Nurture carries a date. Three rules, no exceptions, "
        "and a board you can read at a glance.",
    ),
    _s(
        20,
        SlideKind.CHECKPOINT,
        "Say the two tests a finding must pass",
        "Real and addressable, and what each means. Then say what you do when a finding is real "
        "but not addressable — that case comes up more than people expect and handling it well is "
        "what stops you writing an unsellable proposal.",
        checkpoint=(
            "Say both tests a finding must pass and what you do when one is real but not "
            "addressable."
        ),
    ),
    _s(
        21,
        SlideKind.CHECKPOINT,
        "Say your Nurture sentence aloud",
        "Once, properly. Then decide whether you would actually say it to your largest current "
        "prospect if the assessment came out strong. If the answer is no, that is worth sitting "
        "with — it is the difference between running the method and using it as cover.",
        checkpoint=(
            "Say your Nurture sentence aloud and test it against your largest live prospect."
        ),
    ),
    _s(
        22,
        SlideKind.CONCEPT,
        "Why this is the section that changes forecasts",
        "Because it is where a pipeline stops containing hope. A board where every post-workshop "
        "deal is Qualified-with-a-finding or Nurtured-with-a-date is a board you can forecast "
        "from. Nothing else in this course changes the numbers as much.",
    ),
    _s(
        23,
        SlideKind.CONCEPT,
        "Where this goes next",
        "Section 5 turns a finding into a scope and a price — and covers the single rule that the "
        "methodology enforces in code, which is that the score and the price never appear in the "
        "same equation.",
        refs=(ADR_VALUE_BRIDGE,),
    ),
)

SECTION_4_TEST = SectionTest(
    pass_mark=0.8,
    questions=(
        TestQuestion(
            prompt="What two tests must a finding pass to justify Qualified?",
            options=(
                "It must be significant and urgent",
                "Real — it came out of the scoring with a defensible evidence grade — and\n"
                " addressable inside a scope somebody would buy",
                "It must be agreed by the client and budgeted",
                "It must appear in at least two modules",
            ),
            answer_index=1,
            explanation=(
                "A structural constraint you cannot move is a real weakness and not an engagement. "
                "Qualifying on one produces a proposal nobody can act on."
            ),
        ),
        TestQuestion(
            prompt="Why is a deal left at Workshop Delivered worse than one left elsewhere?",
            options=(
                "Because the recovery-fee window starts there",
                "Because it is the only stage where the work is done and the decision is not, so\n"
                " it feels finished, drops off the review, and becomes unqualifiable",
                "Because it blocks the assessment from finalising",
                "Because it distorts the forecast weighting",
            ),
            answer_index=1,
            explanation=(
                "Every other stalled stage has an obvious owner and next action. This one does "
                "not, which is why the one-day rule exists."
            ),
        ),
        TestQuestion(
            prompt="What makes an honest Nurture commercially valuable?",
            options=(
                "It keeps the pipeline count up",
                "It makes your next assessment credible with them — an advisor who has once said\n"
                " 'you do not need us' is one whose findings are worth listening to",
                "It preserves the recovery fee",
                "It defers the decision to a better quarter",
            ),
            answer_index=1,
            explanation=(
                "An advisor who has never said it is a salesperson with a methodology attached."
            ),
        ),
        TestQuestion(
            prompt=(
                "The client keeps disagreeing after you have read them the anchor. What is that?"
            ),
            options=(
                "Resistance to be worked through",
                "Usually information rather than resistance — if the finding were real and\n"
                " addressable they would recognise it, because they run the business",
                "A sign the rubric needs revising",
                "A reason to lower the evidence grade",
            ),
            answer_index=1,
            explanation=(
                "Arguing a client into a weakness they do not recognise is the tell that you are "
                "forcing the qualification."
            ),
        ),
        TestQuestion(
            prompt="When does Stream A enter, and what should you do about it?",
            options=(
                "At Contracted, alongside Stream B",
                "At Qualified, when a represented product answers the specific finding — check\n"
                " the sell panel the day the assessment is finalised",
                "At Prospect, when the sector is set",
                "It cannot coexist with a consultancy engagement",
            ),
            answer_index=1,
            explanation=(
                "A deal can be consultancy only, product only, both or neither. Deciding which "
                "before the assessment tells you is arriving having already chosen what to sell."
            ),
        ),
        TestQuestion(
            prompt="What is the standard for this stage?",
            options=(
                "A proposal within a week of every workshop",
                "Qualified or Nurture within a day; every Qualified cites a named module or\n"
                " subcomponent; every Nurture carries a date",
                "Every workshop produces a scoped engagement",
                "No deal stays in any stage longer than a month",
            ),
            answer_index=1,
            explanation=(
                "Three rules, no exceptions, and a board you can read at a glance — which is what "
                "makes it forecastable."
            ),
        ),
    ),
)


def section_4() -> CourseModule:
    """Section 4: the fork, and the non-answer that rots pipelines."""
    return CourseModule(
        id=_id("module", "qualify-or-nurture"),
        title="Qualified or Nurture: the honest fork",
        order=3,
        lessons=(
            Lesson(
                id=_id("lesson", "qualify-or-nurture"),
                title="Two states, and the one that is not a state",
                body=_S4_BODY,
                order=0,
                slides=_SECTION_4_SLIDES,
                drill_topics=("ops:qualify-or-nurture",),
                measurement=(
                    "No deal on your board sits at Workshop Delivered for more than a day, and "
                    "every Qualified cites a named module or subcomponent."
                ),
            ),
        ),
        section_test=SECTION_4_TEST,
    )


# --- Section 5 — Scoped: price the lever, never the score -----------------------------------

_S5_BODY = (
    "Turning a finding into a scoped engagement, and the one rule the methodology enforces in "
    "code. By the end of this lesson you can price an engagement against the value bridge, state "
    "what every currency figure traces back to, and explain why dividing a score into pounds "
    "produces a number the system will refuse to construct."
)

_SECTION_5_SLIDES: tuple[Slide, ...] = (
    _s(
        0,
        SlideKind.CONCEPT,
        "Two numbers, and a wall between them",
        'The **score** rates the moat, in score points, and answers "how bad is this?". The '
        "**value bridge** prices the lever, in pounds traceable to an assumption, and answers "
        '"what is it worth doing?". They are different questions with different units, and they '
        "never appear in one equation.",
        refs=(ADR_VALUE_BRIDGE, METHODOLOGY),
        asset=_diagram(
            "score_and_price_never_mix",
            "The score rates the moat; the value bridge prices the lever. Never one equation.",
            "Two panels with a solid vertical wall between them. On the left, THE SCORE: it "
            "measures how weak the moat is, its unit is score points, and it answers how bad is "
            "this. On the right, filled dark green, THE VALUE BRIDGE: it measures what fixing it "
            "is worth, its unit is pounds traceable to an assumption, and it answers what is it "
            "worth doing. The wall is labelled never one equation, and a warning beneath reads: "
            "dividing a score into pounds invents a number the methodology refuses to produce.",
        ),
    ),
    _s(
        1,
        SlideKind.CONCEPT,
        "Why this is a rule and not a preference",
        "Because it is enforced. The value bridge sums Money with Money and never touches a score. "
        "A bridge whose figures cite an assumption outside its register refuses to construct at "
        "all. You cannot produce the forbidden number through the system, which means if you have "
        "one, you made it up outside the system.",
        refs=(ADR_VALUE_BRIDGE,),
    ),
    _s(
        2,
        SlideKind.CONCEPT,
        "The specific temptation",
        "It is always the same shape: their moat scored 4.2 out of 10, the gap is 5.8, so if the "
        "business is worth X then closing the gap is worth 0.58X. It feels rigorous, it produces a "
        "confident-sounding price, and every step after the first is invented. Score points are "
        "ordinal ratings, not a fraction of enterprise value.",
        refs=(METHODOLOGY,),
    ),
    _s(
        3,
        SlideKind.CONCEPT,
        "What the value bridge actually is",
        "Three layers sharing one assumption register: the **cost** of doing the work, the **NPV "
        "of each lever** the work unlocks, and a **strategic** layer that is ordinal and never a "
        "decimal. Every currency figure traces to a client-supplied baseline in the register. If "
        "it does not trace, it does not go in.",
        refs=(ADR_VALUE_BRIDGE,),
    ),
    _s(
        4,
        SlideKind.CONCEPT,
        "The assumption register is the whole point",
        'It is what turns a price from an assertion into an argument. "Six weeks of work returns '
        '£340k of retained revenue" is a claim. "…based on your stated 11% attrition on '
        'single-product relationships, your own figure" is an argument they can check and '
        "disagree with in specifics.",
        refs=(ADR_VALUE_BRIDGE,),
    ),
    _s(
        5,
        SlideKind.CONCEPT,
        "Get the baselines from them, in the workshop",
        "Every number in the register should be theirs. Attrition rate, average revenue per "
        "relationship, cost of the operation you are proposing to change. Ask in the workshop "
        "while you have them — reconstructing it afterwards from public filings produces a bridge "
        "they can dismiss as guesswork.",
    ),
    _s(
        6,
        SlideKind.CONCEPT,
        "Say the two sentences separately",
        '"The assessment says your switching costs are weak, specifically linked-account depth." '
        'Full stop. "Separately: on your own attrition figure, moving single-product '
        'relationships to three products is worth this much over three years." Two sentences, '
        "deliberately not joined, because joining them is where the invented number appears.",
    ),
    _s(
        7,
        SlideKind.CONCEPT,
        "The strategic layer, and why it stays ordinal",
        "Some value is real and not quantifiable — optionality, defensibility, position. The "
        "bridge carries those as an ordinal rating rather than forcing a number onto them. Resist "
        "the urge to price them: a made-up figure in the strategic layer discredits the two layers "
        "that were honest.",
        refs=(ADR_VALUE_BRIDGE,),
    ),
    _s(
        8,
        SlideKind.CONCEPT,
        "Scope to the finding, not to the budget",
        "The scope is what closes the gap the assessment found. If that is six weeks, scope six "
        "weeks. Padding it to fit a number you think they will pay produces work nobody needs, and "
        "it is visible in the deliverable — which is the thing the next engagement gets sold off.",
    ),
    _s(
        9,
        SlideKind.CONCEPT,
        "The dated first deliverable",
        "Never contract without one on the record. A scope with no dated first deliverable is a "
        "retainer with ambitions, and it is the single most common cause of an engagement that "
        "drifts. The date is also what makes the Active-to-Delivered transition in section 7 mean "
        "anything.",
    ),
    _s(
        10,
        SlideKind.WALKTHROUGH,
        "Build one bridge on a real assessment",
        "Take a finalised assessment and build the value bridge: the cost, one lever with its NPV, "
        "and the strategic entries. Try to add a figure that does not trace to the register and "
        "watch it refuse. That refusal is the rule made concrete, and seeing it once is worth more "
        "than reading it three times.",
        refs=(ADR_VALUE_BRIDGE,),
    ),
    _s(
        11,
        SlideKind.WALKTHROUGH,
        "Write the two sentences for a live deal",
        "The finding sentence and the value sentence, separately, for a real prospect. Read them "
        "back and check that neither contains a number from the other. If the value sentence "
        "mentions the score, or the finding sentence mentions pounds, rewrite both.",
    ),
    _s(
        12,
        SlideKind.WALKTHROUGH,
        "List the baselines you would need",
        "For the same deal, write down every client number the bridge would need. Then check which "
        "of them you actually have. The gap is your agenda for the scoping call, and it is usually "
        "shorter than people fear — three or four figures.",
    ),
    _s(
        13,
        SlideKind.WALKTHROUGH,
        "Read the scoring explainer once",
        "Read `ATLAS Scoring Explained` end to end. You are not learning to compute anything — you "
        "are making sure that when a client asks what the number means, you answer from "
        "understanding rather than from a memorised phrase. They can tell the difference.",
        refs=(SCORING_EXPLAINED,),
    ),
    _s(
        14,
        SlideKind.EXAMPLE,
        "The pricing conversation done properly",
        '"Linked-account depth is the weak subcomponent. Separately, on your figures — 11% '
        "attrition on single-product relationships, average revenue you gave me — closing that is "
        "worth around £340k over three years. The work to do it is six weeks. Here is the first "
        'deliverable and it is dated the 30th."',
    ),
    _s(
        15,
        SlideKind.EXAMPLE,
        "The pricing conversation done badly",
        '"You scored 4.2, so there is 5.8 of upside, which on a business your size is about £2m '
        'of value — so our fee is a fraction of that." Every number after the first is invented, '
        "none of it traces to anything they said, and a CFO will take it apart in one question.",
    ),
    _s(
        16,
        SlideKind.EXAMPLE,
        "What the CFO asks",
        '"Where does that £2m come from?" There is no answer, because it came from multiplying a '
        "rating by a valuation. The credibility loss is not confined to the price — it lands on "
        "the assessment too, which was the honest part.",
    ),
    _s(
        17,
        SlideKind.CONCEPT,
        "Why the wall protects the score",
        "This is the part advisors miss. The rule is not there to make pricing harder; it is there "
        "so the assessment stays defensible. The moment a score is used as a multiplier, it stops "
        "being a measurement and becomes a sales instrument — and everyone in the room can feel "
        "it.",
        refs=(METHODOLOGY,),
    ),
    _s(
        18,
        SlideKind.CONCEPT,
        "What to do when they ask you to join them",
        'Clients sometimes ask directly: "so what is the score worth in pounds?" The answer is '
        "that it does not convert, and then you give them what does — the lever, on their numbers. "
        '"The score tells you where the weakness is; this tells you what fixing it returns" is a '
        "better answer than any number.",
    ),
    _s(
        19,
        SlideKind.CONCEPT,
        "The standard for this stage",
        "Every scoped engagement has a dated first deliverable, a value bridge whose every figure "
        "traces to a client-supplied baseline, and a price that was never derived from a score. "
        "Three rules, and the third is enforced by the system rather than by you remembering it.",
        refs=(ADR_VALUE_BRIDGE,),
    ),
    _s(
        20,
        SlideKind.CHECKPOINT,
        "State the wall from memory",
        "What each number measures, in what unit, answering what question. Six facts. Then say "
        "what happens if you try to put a figure in a bridge that does not trace to the register — "
        "the answer is a specific behaviour, not a warning.",
        checkpoint=(
            "State what each of the score and the value bridge measures, its unit and its "
            "question, then what an untraceable figure does."
        ),
    ),
    _s(
        21,
        SlideKind.CHECKPOINT,
        "Say the two sentences out loud",
        'The finding and the value, separately, for a live deal. Then have someone ask "what is '
        'the score worth in pounds?" and answer it without converting. That exchange is the '
        "section, and it is the one you will actually be tested on by a client.",
        checkpoint=(
            "Say both sentences aloud, then answer 'what is the score worth in pounds?' without "
            "converting."
        ),
    ),
    _s(
        22,
        SlideKind.CONCEPT,
        "Why this is the most important rule in the Academy",
        "Because it is the one where breaking it looks like doing a better job. Every other bad "
        "habit in this course is visibly lazy. This one produces a confident number and a "
        "persuasive slide, and it quietly destroys the credibility of the only genuinely rigorous "
        "thing we sell.",
    ),
    _s(
        23,
        SlideKind.CONCEPT,
        "Where this goes next",
        "Section 6 is contracting, and the two commission streams — including the two-by-two that "
        "sets the consultancy rate and the reason you should never quote it from memory.",
        refs=(ADR_STREAMS,),
    ),
)

SECTION_5_TEST = SectionTest(
    pass_mark=0.8,
    questions=(
        TestQuestion(
            prompt="What does each of the two numbers measure, and in what unit?",
            options=(
                "Both measure business value, one in points and one in pounds",
                "The score rates the moat in score points; the value bridge prices the lever in\n"
                " pounds traceable to an assumption",
                "The score measures risk; the value bridge measures return",
                "The score is an input to the value bridge",
            ),
            answer_index=1,
            explanation=(
                "Different questions, different units, and they never appear in one equation. The "
                "last option is exactly the mistake."
            ),
        ),
        TestQuestion(
            prompt="Why is this a rule rather than a preference?",
            options=(
                "Because the founder prefers it",
                "Because it is enforced: the bridge sums Money with Money only, and a bridge "
                "citing an assumption outside its register refuses to construct",
                "Because auditors require the separation",
                "Because score points are confidential",
            ),
            answer_index=1,
            explanation=(
                "You cannot produce the forbidden number through the system — so if you have one, "
                "you made it up outside the system."
            ),
        ),
        TestQuestion(
            prompt="What is the specific temptation this rule prevents?",
            options=(
                "Quoting a fee before scoping",
                "Treating the score gap as a fraction of enterprise value: scored 4.2, gap is "
                "5.8, so closing it is worth 0.58 of the business",
                "Using public filings for baselines",
                "Discounting the engagement fee",
            ),
            answer_index=1,
            explanation=(
                "It feels rigorous and produces a confident price, and every step after the first "
                "is invented. Score points are ordinal ratings, not a fraction of value."
            ),
        ),
        TestQuestion(
            prompt="Where should the numbers in the assumption register come from?",
            options=(
                "Industry benchmarks",
                "The client, gathered in the workshop — reconstructing them afterwards from "
                "public filings produces a bridge they can dismiss as guesswork",
                "Comparable engagements",
                "The scoring engine",
            ),
            answer_index=1,
            explanation=(
                "It is what turns a price from an assertion into an argument they can check and "
                "disagree with in specifics."
            ),
        ),
        TestQuestion(
            prompt="A client asks: 'so what is the score worth in pounds?' What do you say?",
            options=(
                "Give a range based on their revenue",
                "That it does not convert — then give them what does: the lever, on their own\n"
                " numbers",
                "Explain that pricing is confidential",
                "Multiply the gap by the engagement fee",
            ),
            answer_index=1,
            explanation=(
                '"The score tells you where the weakness is; this tells you what fixing it '
                'returns" is a better answer than any number.'
            ),
        ),
        TestQuestion(
            prompt="Why does the wall ultimately protect the SCORE rather than the price?",
            options=(
                "Because scores are proprietary",
                "Because the moment a score is used as a multiplier it stops being a measurement\n"
                " and becomes a sales instrument, and everyone in the room can feel it",
                "Because the score would otherwise be disclosed",
                "Because prices change more often than scores",
            ),
            answer_index=1,
            explanation=(
                "This is the part advisors miss. The rule exists so the assessment stays "
                "defensible, not to make pricing harder."
            ),
        ),
    ),
)


def section_5() -> CourseModule:
    """Section 5: scoping and pricing, and the wall the methodology enforces."""
    return CourseModule(
        id=_id("module", "scope-and-price"),
        title="Scoped: price the lever, never the score",
        order=4,
        lessons=(
            Lesson(
                id=_id("lesson", "scope-and-price"),
                title="The value bridge, and the wall",
                body=_S5_BODY,
                order=0,
                slides=_SECTION_5_SLIDES,
                drill_topics=("ops:scope-and-contract",),
                measurement=(
                    "Every price you quote traces to a client-supplied baseline, and you have "
                    "never derived a number in pounds from a score."
                ),
            ),
        ),
        section_test=SECTION_5_TEST,
    )


# --- Section 6 — Contracted: the two streams ------------------------------------------------

_S6_BODY = (
    "Contracting is the gate that opens consultancy commission, and the point at which two "
    "different streams can be running on the same account. By the end of this lesson you know "
    "which stream opens when, what the two axes are that set the consultancy rate, and why you "
    "read the cell rather than remember it."
)

_SECTION_6_SLIDES: tuple[Slide, ...] = (
    _s(
        0,
        SlideKind.CONCEPT,
        "Two streams, entering at different stages",
        "**Stream A is product** commission, and it becomes possible at Qualified, when a "
        "represented product answers the finding. **Stream B is consultancy** commission, and it "
        "opens at Contracted, when the work is signed. Same account, two streams, two different "
        "moments.",
        refs=(ADR_STREAMS,),
        asset=_diagram(
            "two_streams",
            "Two streams, two entry points, and a two-by-two that sets the consultancy rate.",
            "Two panels. Stream A, product, opens when a product answers the finding, at "
            "Qualified. Stream B, consultancy, filled dark green, opens when the work is "
            "contracted. Below them a two-by-two grid: rows bruntsfield-led and consultant-led, "
            "columns self-sourced and firm-sourced, with each of the four cells labelled rate. A "
            "line beneath reads: self-sourced always pays more, read the live cell off the "
            "Earnings page.",
        ),
    ),
    _s(
        1,
        SlideKind.CONCEPT,
        "Why they are separate rather than one number",
        "Because they are different businesses. A product commission is a share of somebody else's "
        "revenue that you influenced. A consultancy commission is a share of work Bruntsfield "
        "delivered. Different economics, different windows, different rates — and adding them "
        "together in a forecast without noticing which is which is how forecasts go wrong.",
        refs=(ADR_STREAMS,),
    ),
    _s(
        2,
        SlideKind.CONCEPT,
        "The two axes that set the consultancy rate",
        "**Delivery type** — Bruntsfield-led or consultant-led — and **sourcing** — self-sourced "
        "or firm-sourced. Two by two, four cells, four different rates. It is not one number with "
        "adjustments; it is a lookup, and the cell you are in was largely decided months ago.",
        refs=(ADR_STREAMS,),
    ),
    _s(
        3,
        SlideKind.CONCEPT,
        "What delivery type actually distinguishes",
        "Bruntsfield-led is the Power Platform assessment and methodology work — our product, our "
        "method. Consultant-led is bespoke work whose scope the client and the consultant "
        "determined. The distinction is about whose method is being delivered, not about who is in "
        "the room.",
        refs=(ADR_STREAMS,),
    ),
    _s(
        4,
        SlideKind.CONCEPT,
        "Self-sourced always pays more",
        "On both delivery types. That is the schedule's deliberate shape: originating the "
        "relationship is the scarce thing. It is also why section 2 spent so long on a single "
        "field — the difference between the two columns is not a rounding adjustment.",
        refs=(ADR_STREAMS,),
    ),
    _s(
        5,
        SlideKind.CONCEPT,
        "Read the cell, never remember it",
        "The rates live in the v7 schedule and they resolve live on the Earnings page. Do not "
        "memorise them, do not quote them from a course, and do not forecast from a number you are "
        "fairly confident about. A rate you remembered is a rate that was correct once.",
    ),
    _s(
        6,
        SlideKind.CONCEPT,
        "The first-year rate and what follows it",
        "Each cell has a first-twelve-months rate and a thereafter rate, and they differ. That "
        "matters for a long engagement: two deals of the same size can be worth different amounts "
        "to you depending on how long they run. Look at both numbers, not the headline one.",
        refs=(ADR_STREAMS,),
    ),
    _s(
        7,
        SlideKind.CONCEPT,
        "What has to be true to move to Contracted",
        "A signed engagement with a scoped deliverable and a date. Not a verbal yes, not a "
        "handshake at the end of a good meeting. Contracted is the stage that opens a commission "
        "stream, which makes it the stage where an optimistic move is most expensive — it puts "
        "money in a forecast that has not been agreed.",
    ),
    _s(
        8,
        SlideKind.CONCEPT,
        "Both streams on one account is normal",
        "A client who contracts a retention engagement *and* buys a product that closes part of "
        "the same gap generates both. That is the best outcome in this catalogue and it is not "
        "rare. It does require you to have noticed the product door at Qualified rather than after "
        "the engagement started.",
        refs=(ADR_STREAMS,),
    ),
    _s(
        9,
        SlideKind.CONCEPT,
        "What you do not control",
        "The rate cell, the schedule, and the contracting itself. What you do control is the "
        "sourcing attribution, the accuracy of the delivery-type classification, and whether the "
        "deal is staged honestly. Those three are yours, and they are what the cell is looked up "
        "from.",
    ),
    _s(
        10,
        SlideKind.WALKTHROUGH,
        "Open the Earnings page and find your cell",
        "For a live contracted deal, work out which of the four cells applies and read the two "
        "numbers. Do it now, with a real deal, rather than in the abstract — the abstract version "
        "is forgettable and the real one sticks.",
    ),
    _s(
        11,
        SlideKind.WALKTHROUGH,
        "Classify three engagements by delivery type",
        "Take three real or recent engagements and decide whether each is Bruntsfield-led or "
        "consultant-led, and say why in one sentence. If any of the three is genuinely ambiguous, "
        "that is worth raising rather than deciding quietly — the classification changes the rate.",
    ),
    _s(
        12,
        SlideKind.WALKTHROUGH,
        "Check every contracted deal has a dated deliverable",
        "Filter for Contracted and confirm each has a scoped, dated first deliverable recorded. "
        "Any that do not are mis-staged: they are Scoped at best. Fixing that is unglamorous and "
        "it is what makes the next section's delivery tracking possible at all.",
    ),
    _s(
        13,
        SlideKind.WALKTHROUGH,
        "Find the product door you missed",
        "Take two recently contracted engagements and check whether a represented product would "
        "have answered part of the finding. If one would have, that is a Stream A you did not "
        "open. Do this occasionally — it is the cheapest revenue in the motion and it is missed by "
        "forgetting to look.",
    ),
    _s(
        14,
        SlideKind.EXAMPLE,
        "A forecast that was wrong for a structural reason",
        "An advisor forecasts a large consultancy number on a firm-sourced, Bruntsfield-led "
        "engagement using the self-sourced rate they half-remembered. The deal lands, the number "
        "does not, and the gap is not small. Nothing went wrong with the deal — the forecast was "
        "built on a remembered rate.",
    ),
    _s(
        15,
        SlideKind.EXAMPLE,
        "Both streams, done deliberately",
        "The assessment finds thin linked-account depth. The engagement scopes the retention work "
        "(Stream B). A represented product closes the onboarding half of the same gap (Stream A). "
        "One finding, two streams, and the second one existed because somebody opened the sell "
        "panel at Qualified.",
        refs=(ADR_STREAMS,),
    ),
    _s(
        16,
        SlideKind.EXAMPLE,
        "The optimistic stage move",
        '"They said yes on the call, I\'ll move it to Contracted." Two weeks later procurement '
        "changes the scope and the start slips a quarter. The forecast carried a number that was "
        "never real, and the correction lands on the whole team's numbers rather than on the "
        "advisor's.",
    ),
    _s(
        17,
        SlideKind.CONCEPT,
        "The recovery fee exists in this family too",
        "Alongside engagement commission, the schedule carries a workshop recovery fee. It is not "
        "an engagement commission and it is not a retainer — it is its own kind of line, and "
        "section 8 is about the case where it applies. Knowing it exists now means you will not "
        "write off a lapsed workshop out of ignorance.",
        refs=(ADR_STREAMS,),
    ),
    _s(
        18,
        SlideKind.CONCEPT,
        "What to say to a client about your commission",
        'Nothing, unless asked, and then honestly and without a figure. "Bruntsfield is '
        "compensated on the engagement and, where a product is involved, on that too — the "
        'specific terms are with the firm." Transparency about the existence of the arrangement '
        "costs nothing; a number invites a negotiation you cannot conduct.",
    ),
    _s(
        19,
        SlideKind.CONCEPT,
        "The standard for this stage",
        "Nothing moves to Contracted without a signature, a scope and a date. Every contracted "
        "deal has its delivery type and sourcing recorded accurately. No forecast uses a rate that "
        "was not read off the Earnings page that week.",
    ),
    _s(
        20,
        SlideKind.CHECKPOINT,
        "Name the two streams and their entry points",
        "From memory, then the two axes that set the consultancy rate, then which column always "
        "pays more. Five facts. The one people get wrong is which stream opens where, so start "
        "there.",
        checkpoint=(
            "Name both streams and where each opens, the two rate axes, and which column pays more."
        ),
    ),
    _s(
        21,
        SlideKind.CHECKPOINT,
        "Look up a real cell, and say the two numbers",
        "Not from memory — from the Earnings page, for a real deal, out loud. Then say what would "
        "have to change about that deal for it to be in a different cell. That second part is what "
        "makes the grid something you use rather than something you have read.",
        checkpoint=(
            "Read a real rate cell off the Earnings page and say what would move the deal to a "
            "different cell."
        ),
    ),
    _s(
        22,
        SlideKind.CONCEPT,
        "Why this section is mostly about not guessing",
        "There is very little judgement in it. The rate is a lookup, the streams are defined, the "
        "stage has a hard entry condition. Almost every error here is somebody substituting memory "
        "for the schedule, and the fix is a habit rather than a skill.",
    ),
    _s(
        23,
        SlideKind.CONCEPT,
        "Where this goes next",
        "Section 7 is delivery: keeping one activity timeline per account so that anybody — "
        "including you in three months — can tell what state the engagement is actually in without "
        "asking a person.",
    ),
)

SECTION_6_TEST = SectionTest(
    pass_mark=0.8,
    questions=(
        TestQuestion(
            prompt="Where does each commission stream open?",
            options=(
                "Both at Contracted",
                "Stream A (product) becomes possible at Qualified; Stream B (consultancy) opens\n"
                " at Contracted",
                "Stream A at Contracted; Stream B at Qualified",
                "Both at Delivered",
            ),
            answer_index=1,
            explanation=(
                "This is the one most people get wrong. Same account, two streams, two different "
                "moments."
            ),
        ),
        TestQuestion(
            prompt="What two axes set the consultancy rate?",
            options=(
                "Engagement size and duration",
                "Delivery type (Bruntsfield-led or consultant-led) and sourcing (self- or\n"
                " firm-sourced) — four cells, four rates",
                "Sector and operating-model profile",
                "Consultant tier and client tier",
            ),
            answer_index=1,
            explanation=(
                "It is not one number with adjustments, it is a lookup — and the cell you are in "
                "was largely decided months ago."
            ),
        ),
        TestQuestion(
            prompt="What distinguishes Bruntsfield-led from consultant-led delivery?",
            options=(
                "Whether a Bruntsfield employee is in the room",
                "Whose method is being delivered: the Power Platform assessment and methodology\n"
                " work versus bespoke work the client and consultant scoped",
                "The size of the engagement",
                "Whether the client or Bruntsfield invoices",
            ),
            answer_index=1,
            explanation=("The distinction is about the method, not about who is present."),
        ),
        TestQuestion(
            prompt="Why should you never forecast from a remembered rate?",
            options=(
                "Because rates are confidential",
                "Because a rate you remembered is a rate that was correct once — the schedule\n"
                " resolves live on the Earnings page",
                "Because rates vary by client",
                "Because the forecast tool overrides it anyway",
            ),
            answer_index=1,
            explanation=(
                "The classic failure is forecasting a firm-sourced deal at a half-remembered "
                "self-sourced rate. Nothing goes wrong with the deal; the forecast was never real."
            ),
        ),
        TestQuestion(
            prompt="What has to be true before a deal moves to Contracted?",
            options=(
                "A verbal yes from the decision-maker",
                "A signed engagement with a scoped deliverable and a date",
                "A finalised assessment and a value bridge",
                "Procurement approval in principle",
            ),
            answer_index=1,
            explanation=(
                "It is the stage that opens a commission stream, which makes an optimistic move "
                "here the most expensive one on the board."
            ),
        ),
        TestQuestion(
            prompt="A client asks what Bruntsfield earns on the deal. What do you say?",
            options=(
                "Decline to discuss it",
                "Confirm honestly that Bruntsfield is compensated on the engagement and on any\n"
                " product involved, without a figure — the terms are with the firm",
                "Give the percentage from the schedule",
                "Say there is no commission on consultancy work",
            ),
            answer_index=1,
            explanation=(
                "Transparency about the arrangement costs nothing; a number invites a negotiation "
                "you cannot conduct."
            ),
        ),
    ),
)


def section_6() -> CourseModule:
    """Section 6: contracting, and the two commission streams."""
    return CourseModule(
        id=_id("module", "contract-and-streams"),
        title="Contracted: the two streams",
        order=5,
        lessons=(
            Lesson(
                id=_id("lesson", "contract-and-streams"),
                title="Two streams, four cells, one lookup",
                body=_S6_BODY,
                order=0,
                slides=_SECTION_6_SLIDES,
                drill_topics=("ops:contract-and-streams",),
                measurement=(
                    "Nothing on your board reaches Contracted without a signature, a scope and a "
                    "date, and you have never forecast from a remembered rate."
                ),
            ),
        ),
        section_test=SECTION_6_TEST,
    )


# --- Section 7 — Active to Delivered: one timeline -------------------------------------------

_S7_BODY = (
    "Running the engagement, and the discipline that makes it legible to anyone but you. By the "
    "end of this lesson you know what belongs on the account's activity timeline, why scattering "
    "it across an inbox and a chat costs more than it saves, and what has to be true before an "
    "engagement can be called delivered."
)

_SECTION_7_SLIDES: tuple[Slide, ...] = (
    _s(
        0,
        SlideKind.CONCEPT,
        "One account, one timeline",
        "Every touch on the engagement goes on the account's activity log: the kickoff, the "
        "deliverable review, the check-in that got moved, the sign-off. One place, in order. Not "
        "because tidiness is a virtue, but because it is the only way anybody — including you in "
        "three months — can see the deal's true state without asking a person.",
        asset=_diagram(
            "one_timeline",
            "Scattered touches versus one ordered log. The argument is legibility, not tidiness.",
            "Two panels. On the left, an inbox, a chat and a notebook: five grey blocks scattered "
            "at different positions, described as nobody can see the state. On the right, the "
            "account's activity log: five green blocks in one ordered column, described as anyone "
            "can, including you. A line beneath reads: you will not remember this deal in three "
            "months, the log will.",
        ),
    ),
    _s(
        1,
        SlideKind.CONCEPT,
        "What actually goes on it",
        "Anything that changes what somebody would do next. A meeting held, a deliverable sent, a "
        "decision taken, a date moved, a risk raised. Not every email — a log nobody reads is as "
        "useless as no log. The test is whether a colleague picking this up cold would need to "
        "know it.",
    ),
    _s(
        2,
        SlideKind.CONCEPT,
        "Why the inbox is not a system of record",
        "Because it is yours. It is not searchable by anyone else, it is not ordered by account, "
        "and it disappears when you do. The same is true of a chat thread and a notebook. Each is "
        "a fine place to do the work and a terrible place to record that the work happened.",
    ),
    _s(
        3,
        SlideKind.CONCEPT,
        "The three-month test",
        "Could you, in three months, reconstruct what state this engagement is in and what happens "
        "next, from the record alone? If the answer depends on remembering, the record is "
        "incomplete. This is not a hypothetical — three months is roughly when a client asks you "
        "something you have entirely forgotten.",
    ),
    _s(
        4,
        SlideKind.CONCEPT,
        "The colleague test, which is stricter",
        "Could somebody else pick this account up on Monday and know what to do? That is the "
        "standard a professional services firm is actually held to, and it is the difference "
        "between an account the firm owns and an account you own. Only one of those survives a "
        "holiday.",
    ),
    _s(
        5,
        SlideKind.CONCEPT,
        "Deliverables are the spine of the engagement",
        "The dated first deliverable from section 5 is the thing everything else hangs off. When "
        "it moves — and it sometimes should — move it on the record with the reason. An engagement "
        "where the deliverable date has quietly slipped twice with no note is one nobody can "
        "forecast the end of.",
    ),
    _s(
        6,
        SlideKind.CONCEPT,
        "AI-drafted work still needs a human on it",
        "Deliverable first drafts can be AI-assisted, and every one of them carries an approval "
        "gate before it reaches a client. That is a runtime guarantee rather than a convention, so "
        "you cannot accidentally send an unreviewed draft — but you can sit on one, which stalls "
        "the engagement just as effectively.",
        refs=(ADR_APPROVAL,),
    ),
    _s(
        7,
        SlideKind.CONCEPT,
        "What Delivered means",
        'The scoped work is done and the client has it. Not "the last meeting happened" and not '
        '"we are basically finished". Delivered is a claim like every other stage, and the '
        "evidence is the deliverable being with the client with a date on it.",
    ),
    _s(
        8,
        SlideKind.CONCEPT,
        "The moment to look for the next thing",
        "Delivery is when your credibility with the account is highest and your access is best. It "
        "is the natural moment for the next assessment, the adjacent bottleneck you noticed but "
        "did not scope, or the product that would close a gap the engagement exposed. Do not wait "
        "for a renewal cycle to have that conversation.",
    ),
    _s(
        9,
        SlideKind.CONCEPT,
        "And the moment people quietly disappear",
        "The commonest failure at Delivered is nothing: the work lands, the advisor moves on, the "
        "account cools, and six months later somebody else sells them the follow-on. A delivered "
        "engagement with no next dated step is the same problem as a workshop with no next dated "
        "step, later in the funnel.",
    ),
    _s(
        10,
        SlideKind.WALKTHROUGH,
        "Read one of your accounts as a stranger",
        "Open an active engagement and read only the record. Write down what state you would say "
        "it is in and what happens next. Then compare with what you actually know. The gap is what "
        "is missing from the log, and it is usually one or two specific things rather than "
        "everything.",
    ),
    _s(
        11,
        SlideKind.WALKTHROUGH,
        "Backfill the one thing that matters",
        "You will not reconstruct months of history and you should not try. Add the two or three "
        "entries that would let a colleague take over: where the deliverable stands, what was last "
        "decided, and what the next dated thing is. That is enough to pass the colleague test.",
    ),
    _s(
        12,
        SlideKind.WALKTHROUGH,
        "Check every Active deal for a next date",
        "Filter for Active and confirm each has a dated next action. Any without one is drifting, "
        "whatever its stage says. This is the same audit as section 1's, applied to the half of "
        "the pipeline that people assume is safe because it is already sold.",
    ),
    _s(
        13,
        SlideKind.WALKTHROUGH,
        "Write your delivery-moment question",
        "The one you will ask at sign-off to open the next conversation. It should refer to "
        'something specific the engagement exposed rather than being a generic "what else can we '
        'help with". Write it for a real account you are close to delivering.',
    ),
    _s(
        14,
        SlideKind.EXAMPLE,
        "An account only one person can read",
        "The history is in an advisor's inbox, two chat threads and a notebook. They are excellent "
        "at it and the client is happy. Then they take three weeks off, the client calls with a "
        "question, and nobody can answer it. The problem was never the advisor's competence — it "
        "was that the competence was not written down.",
    ),
    _s(
        15,
        SlideKind.EXAMPLE,
        "A handover that took four minutes",
        "Same engagement, one timeline. The colleague reads twelve entries, sees the deliverable "
        "went out on the 30th, the client raised a scope question on the 4th, and a call is dated "
        "for the 11th. They answer the client that afternoon. The advisor's holiday is not a "
        "business continuity event.",
    ),
    _s(
        16,
        SlideKind.EXAMPLE,
        "The delivery moment used well",
        '"While we were in the onboarding data we kept running into the reconciliation step — it '
        "was outside this scope, but it is the same shape of problem and it is costing you more "
        'than this was. Worth scoring it properly?" Specific, earned, and it comes from having '
        "done the work.",
    ),
    _s(
        17,
        SlideKind.CONCEPT,
        "What not to put on the timeline",
        "Opinions about people, speculation about internal politics, anything you would not want a "
        "client to read. The activity log is organisational memory and it may be read by people "
        "you did not anticipate. Record what happened, not what you thought of it.",
    ),
    _s(
        18,
        SlideKind.CONCEPT,
        "The scoping rule still applies",
        "You see your own accounts. That is enforced rather than conventional, which means the log "
        "is safe to be candid in about the *work* — but it also means a colleague can only pick up "
        "an account they have been given. Handover is an act, not an assumption.",
    ),
    _s(
        19,
        SlideKind.CONCEPT,
        "The standard for this stage",
        "One current timeline per account. Every Active deal has a dated next action. Nothing is "
        "marked Delivered until the client has the deliverable. And no engagement is closed out "
        "without a next dated step or a deliberate decision that there is not one.",
    ),
    _s(
        20,
        SlideKind.CHECKPOINT,
        "Apply the colleague test out loud",
        "Pick a live account and say, from the record only, what state it is in and what happens "
        "next. If you find yourself adding things you know but have not written, stop and write "
        "them. That is the exercise.",
        checkpoint=(
            "State a live account's status and next step from the record alone, and write down "
            "anything you had to supply from memory."
        ),
    ),
    _s(
        21,
        SlideKind.CHECKPOINT,
        "Say your delivery-moment question",
        "Out loud, for a real account, referring to something specific that engagement exposed. If "
        "it could be said to any client about any engagement, it is too generic to earn the next "
        "conversation — rewrite it until it could only be said to this one.",
        checkpoint=(
            "Say your delivery-moment question aloud, specific enough to fit only one account."
        ),
    ),
    _s(
        22,
        SlideKind.CONCEPT,
        "Why this section feels like admin and is not",
        "Because everything in it is about whether the work you did is visible. An engagement "
        "delivered brilliantly and recorded badly is, to the firm, indistinguishable from one "
        "delivered adequately. The record is not evidence of the work — for anyone who was not "
        "there, it is the work.",
    ),
    _s(
        23,
        SlideKind.CONCEPT,
        "Where this goes next",
        "Section 8 is the exits, and the money most advisors leave on the table: what happens to a "
        "delivered workshop that never contracted, and why the default outcome there is the wrong "
        "one.",
    ),
)

SECTION_7_TEST = SectionTest(
    pass_mark=0.8,
    questions=(
        TestQuestion(
            prompt="What is the argument for one activity timeline per account?",
            options=(
                "Tidiness and audit compliance",
                "Legibility: it is the only way anybody, including you in three months, can see "
                "the deal's true state without asking a person",
                "It reduces email volume",
                "It is required before an engagement can be contracted",
            ),
            answer_index=1,
            explanation=(
                "An inbox is a fine place to do the work and a terrible place to record that the "
                "work happened — it is yours, unsearchable by others, and it leaves when you do."
            ),
        ),
        TestQuestion(
            prompt="What belongs on the timeline?",
            options=(
                "Every email and message, for completeness",
                "Anything that changes what somebody would do next — the test is whether a\n"
                " colleague picking it up cold would need to know it",
                "Only client-facing communications",
                "Only items with a date attached",
            ),
            answer_index=1,
            explanation=(
                "A log nobody reads is as useless as no log. Completeness is not the goal; "
                "legibility is."
            ),
        ),
        TestQuestion(
            prompt="What does Delivered actually claim?",
            options=(
                "That the last scheduled meeting has happened",
                "That the scoped work is done and the client has the deliverable, with a date",
                "That the invoice has been issued",
                "That the engagement period has elapsed",
            ),
            answer_index=1,
            explanation=(
                "Delivered is a claim like every other stage. 'We are basically finished' is not "
                "evidence of anything."
            ),
        ),
        TestQuestion(
            prompt="Why is delivery the right moment to open the next conversation?",
            options=(
                "Because the client is contractually obliged to consider it",
                "Because your credibility and access are at their highest, and you can point at\n"
                " something specific the engagement exposed",
                "Because the renewal cycle begins then",
                "Because the commission window is about to close",
            ),
            answer_index=1,
            explanation=(
                "The commonest failure here is doing nothing: the work lands, the account cools, "
                "and six months later somebody else sells the follow-on."
            ),
        ),
        TestQuestion(
            prompt="What should NOT go on the activity timeline?",
            options=(
                "Dates that have moved",
                "Opinions about people, speculation about internal politics, anything you would\n"
                " not want a client to read",
                "Risks raised by the client",
                "Decisions taken in meetings",
            ),
            answer_index=1,
            explanation=(
                "It is organisational memory and may be read by people you did not anticipate. "
                "Record what happened, not what you thought of it."
            ),
        ),
        TestQuestion(
            prompt="Why does an engagement delivered brilliantly but recorded badly matter?",
            options=(
                "It does not, as long as the client is satisfied",
                "Because to anyone who was not there the record IS the work — badly recorded is\n"
                " indistinguishable from adequately delivered",
                "Because it affects the commission calculation",
                "Because compliance requires a full audit trail",
            ),
            answer_index=1,
            explanation=(
                "This is why the section feels like admin and is not: everything in it is about "
                "whether the work you did is visible."
            ),
        ),
    ),
)


def section_7() -> CourseModule:
    """Section 7: delivery, and the record that makes it legible."""
    return CourseModule(
        id=_id("module", "deliver-the-work"),
        title="Active to Delivered: one timeline",
        order=6,
        lessons=(
            Lesson(
                id=_id("lesson", "deliver-the-work"),
                title="The record is the work",
                body=_S7_BODY,
                order=0,
                slides=_SECTION_7_SLIDES,
                drill_topics=("ops:deliver-and-recover",),
                measurement=(
                    "A colleague could pick up any of your accounts on Monday and know its state "
                    "and next step from the record alone."
                ),
            ),
        ),
        section_test=SECTION_7_TEST,
    )


# --- Section 8 — Closed, Nurture, and the recovery fee ---------------------------------------

_S8_BODY = (
    "The exits, and the money most advisors leave on the table. By the end of this lesson you know "
    "what the workshop recovery fee is and when it applies, why the default outcome for a lapsed "
    "workshop is the wrong one, and how to park a deal so that it comes back rather than dies."
)

_SECTION_8_SLIDES: tuple[Slide, ...] = (
    _s(
        0,
        SlideKind.CONCEPT,
        "A workshop delivered, and no contract",
        "It happens, and it is not a failure. You delivered ninety minutes of real work, produced "
        "a scored assessment, and the client did not contract inside the attribution window. There "
        "are two things that can happen next, and only one of them is a decision.",
        asset=_diagram(
            "the_recovery_fee",
            "One situation, two endings — and the wrong one is what happens by default.",
            "A box stating that the attribution window closes, with two branches. Doing nothing "
            "leads to Written off: the effort is gone and the lead goes cold. Resolving it leads "
            "to Recovery fee, filled dark green: the workshop effort is recovered and the deal "
            "moves to Nurture. A warning beneath reads: written off is the default, it is what "
            "happens when nobody does anything. A final line adds: a scored moat that was not "
            "ready today is a warm lead in two quarters.",
        ),
    ),
    _s(
        1,
        SlideKind.CONCEPT,
        "What the recovery fee is",
        "A distinct kind of commission line, alongside engagement commission and retainers. It "
        "exists so that a delivered workshop that did not convert can be recovered rather than "
        "written off. It is not a consolation prize — it is the schedule recognising that the "
        "workshop was real work with a real cost.",
        refs=(ADR_STREAMS,),
    ),
    _s(
        2,
        SlideKind.CONCEPT,
        "Why the default is the wrong outcome",
        "Because doing nothing produces the write-off. Nobody decides to abandon the fee; the "
        "window simply closes while everyone is busy. That is the entire failure mode, and it is "
        "why this is a process point rather than a judgement call — the fix is a habit of "
        "resolving, not a skill.",
    ),
    _s(
        3,
        SlideKind.CONCEPT,
        "Resolve it explicitly, either way",
        "Every delivered workshop that did not contract needs its recovery position explicitly "
        "resolved: claimed, or deliberately not claimed with a reason. Both are fine. What is not "
        "fine is a lapsed workshop with nothing recorded, because that is indistinguishable from "
        "having forgotten.",
    ),
    _s(
        4,
        SlideKind.CONCEPT,
        "The attribution window",
        "The recovery position is tied to an attribution — which workshop, for which prospect, in "
        "which window. That is why section 2 mattered: a workshop delivered against a prospect "
        "with no recorded sourcing is harder to resolve, and the ambiguity is not resolved in your "
        "favour.",
        refs=(ADR_STREAMS,),
    ),
    _s(
        5,
        SlideKind.CONCEPT,
        "Nurture, properly",
        'A parked deal with a dated reason to return. Not "check back sometime". The date should '
        "come from something real: their re-platforming, a new hire starting, a fiscal year, a "
        "regulatory deadline. A date with a reason behind it survives; an arbitrary one gets "
        "snoozed forever.",
    ),
    _s(
        6,
        SlideKind.CONCEPT,
        "What makes a Nurture worth having",
        "The scored assessment. This is not a cold lead — it is a firm whose moat you have "
        "measured and whose bottlenecks you know. When you come back you are not re-qualifying "
        "from scratch, you are asking whether one specific thing has changed. That is a far "
        "stronger second conversation than a first one.",
    ),
    _s(
        7,
        SlideKind.CONCEPT,
        "Closed, and when to use it",
        "When it is genuinely not happening: they said no, they were acquired, the business "
        "changed. Closing a deal honestly is a service to the pipeline — it keeps the board "
        "readable. The failure is not closing too much, it is closing nothing and calling a "
        "graveyard a pipeline.",
    ),
    _s(
        8,
        SlideKind.CONCEPT,
        "Neither exit is a judgement on you",
        "Both are recorded outcomes. A pipeline with a healthy flow into Nurture and Closed is one "
        "being actively managed. A pipeline where nothing ever exits is one where nobody is "
        "deciding anything, and it is worth less than a smaller honest one.",
    ),
    _s(
        9,
        SlideKind.CONCEPT,
        "Re-engagement is a first-class move",
        "A dated Nurture arriving is a real task, not a reminder to feel guilty about. Open the "
        "old assessment, look at what you found, and ask whether the thing that stopped it has "
        "changed. That takes ten minutes and it is the highest-conversion outreach available to "
        "you.",
    ),
    _s(
        10,
        SlideKind.WALKTHROUGH,
        "Find every lapsed workshop on your board",
        "Filter for workshops delivered where nothing contracted. For each one, resolve the "
        "recovery position explicitly. If this is the first time you have done it, expect to find "
        "more than you thought — that is normal and it is exactly the point of the exercise.",
    ),
    _s(
        11,
        SlideKind.WALKTHROUGH,
        "Give every parked deal a real date",
        "Go through your Nurture deals and check each has a date with a reason behind it. Replace "
        "every arbitrary date with a real one, or Close the deal. A Nurture pile with no reasons "
        "in it is a Closed pile that nobody was willing to write down.",
    ),
    _s(
        12,
        SlideKind.WALKTHROUGH,
        "Re-open one old assessment",
        "Take a Nurture from six months ago, open the assessment, and read the finding. Decide "
        "whether it is worth a call this week. Do it now rather than when the reminder fires — the "
        "point is to experience how much context is sitting there waiting.",
    ),
    _s(
        13,
        SlideKind.WALKTHROUGH,
        "Write your re-engagement opening",
        "The sentence you use coming back to a Nurture. It should reference the specific finding "
        'from the assessment and the specific reason you parked it. "Last year the linked-account '
        'depth was the weak point and you were mid re-platform — has that landed?" Write yours.',
    ),
    _s(
        14,
        SlideKind.EXAMPLE,
        "The write-off nobody chose",
        "Four workshops delivered over a quarter, none contracted, all four windows quietly "
        "closed. Nobody decided to abandon any of them. The effort is unrecovered and four scored "
        "assessments are sitting in the system attached to deals nobody will re-open, because "
        "nothing has a date on it.",
    ),
    _s(
        15,
        SlideKind.EXAMPLE,
        "The same quarter, resolved",
        "Same four workshops. Each recovery position resolved explicitly — three claimed, one not, "
        "with a reason. All four moved to Nurture with dates drawn from real events. Two come back "
        "the following year, and the second conversation starts from a scored assessment rather "
        "than from nothing.",
    ),
    _s(
        16,
        SlideKind.EXAMPLE,
        "A re-engagement that works",
        '"When we scored you last March, linked-account depth was the weak point and you were '
        "about to re-platform. That has landed now — worth twenty minutes to see whether it moved "
        'the number?" Specific, warm, and it is a conversation about their business rather than '
        "about your quarter.",
    ),
    _s(
        17,
        SlideKind.CONCEPT,
        "Do not claim what is not there",
        "The recovery fee applies to a workshop that was actually delivered, against a real "
        "attribution, inside its window. Resolving a position honestly sometimes means resolving "
        "it as not claimable. That is a correct outcome, and recording it is what makes the claims "
        "you do make credible.",
        refs=(ADR_STREAMS,),
    ),
    _s(
        18,
        SlideKind.CONCEPT,
        "The standard for this stage",
        "Every delivered workshop that did not contract has its recovery position explicitly "
        "resolved. Every parked deal has a date with a reason behind it. Nothing sits in a middle "
        "stage indefinitely, and Closed is used when Closed is true.",
    ),
    _s(
        19,
        SlideKind.CONCEPT,
        "How this closes the loop",
        "Section 1 said every deal has a dated next step or an exit. This is the section that "
        "makes the second half of that real: exits are things you choose, record and come back "
        "from, rather than what happens to deals you stopped looking at.",
    ),
    _s(
        20,
        SlideKind.CHECKPOINT,
        "Say what the recovery fee is and when it applies",
        "From memory: what kind of thing it is, what situation it covers, and what the default "
        "outcome is if nobody acts. Three facts, and the third is the one that costs money.",
        checkpoint=(
            "State what the recovery fee is, when it applies, and what happens by default if "
            "nobody resolves it."
        ),
    ),
    _s(
        21,
        SlideKind.CHECKPOINT,
        "Resolve your own board, then say the re-engagement line",
        "Do the two audits — lapsed workshops resolved, parked deals dated — and then say your "
        "re-engagement opening out loud for one real Nurture. Finishing this course means your "
        "board has no unresolved positions and no undated parks on it.",
        checkpoint=(
            "Resolve every lapsed workshop and date every parked deal, then say your re-engagement "
            "opening aloud."
        ),
    ),
    _s(
        22,
        SlideKind.CONCEPT,
        "What you should be able to do now",
        "Draw the motion from memory. Open an account so it is a deal rather than a business card. "
        "Run a workshop that scores live and ends in a decision. Qualify against a named "
        "bottleneck or nurture honestly. Price the lever without touching the score. Contract, "
        "deliver legibly, and exit deliberately.",
    ),
    _s(
        23,
        SlideKind.CONCEPT,
        "And the one measure that covers all of it",
        "Whether somebody else could open your pipeline and know what state every deal is in and "
        "what happens next, without asking you. If they can, the process is real. If they cannot, "
        "it is in your head — and everything in this course was about getting it out of there.",
    ),
)

SECTION_8_TEST = SectionTest(
    pass_mark=0.8,
    questions=(
        TestQuestion(
            prompt="What is the workshop recovery fee?",
            options=(
                "A discount applied to a stalled engagement",
                "A distinct kind of commission line that lets a delivered workshop which did not\n"
                " convert be recovered rather than written off",
                "A retainer for nurtured accounts",
                "A refund to the client for an unconverted workshop",
            ),
            answer_index=1,
            explanation=(
                "It is not a consolation prize — it is the schedule recognising that the workshop "
                "was real work with a real cost."
            ),
        ),
        TestQuestion(
            prompt="Why is the write-off described as the default outcome?",
            options=(
                "Because most workshops do not convert",
                "Because doing nothing produces it: nobody decides to abandon the fee, the window\n"
                " simply closes while everyone is busy",
                "Because the schedule requires an explicit claim within 30 days",
                "Because unconverted workshops are automatically closed",
            ),
            answer_index=1,
            explanation=(
                "That is the entire failure mode, which is why the fix is a habit of resolving "
                "rather than a skill."
            ),
        ),
        TestQuestion(
            prompt="What makes a Nurture date worth having?",
            options=(
                "That it is at least six months out",
                "That it comes from something real — a re-platform, a new hire, a fiscal year — "
                "so it survives rather than being snoozed forever",
                "That it is reviewed monthly",
                "That the client agreed to it",
            ),
            answer_index=1,
            explanation=(
                "A Nurture pile with no reasons in it is a Closed pile that nobody was willing to "
                "write down."
            ),
        ),
        TestQuestion(
            prompt="Why is a nurtured deal a strong second conversation rather than a cold lead?",
            options=(
                "Because they have already met you",
                "Because you have a scored assessment: you are not re-qualifying from scratch, "
                "you are asking whether one specific thing has changed",
                "Because the recovery fee has already been claimed",
                "Because the pricing was already agreed",
            ),
            answer_index=1,
            explanation=(
                "It is the highest-conversion outreach available, and re-opening the old "
                "assessment takes about ten minutes."
            ),
        ),
        TestQuestion(
            prompt="Resolving a recovery position honestly sometimes means what?",
            options=(
                "Claiming the maximum available",
                "Resolving it as NOT claimable, with a reason — which is what makes the claims "
                "you do make credible",
                "Deferring it to the next window",
                "Escalating it to the firm",
            ),
            answer_index=1,
            explanation=(
                "The fee applies to a workshop actually delivered, against a real attribution, "
                "inside its window. A recorded non-claim is a correct outcome."
            ),
        ),
        TestQuestion(
            prompt="What is the single measure that covers this whole course?",
            options=(
                "Deals contracted per quarter",
                "Whether somebody else could open your pipeline and know what state every deal is\n"
                " in and what happens next, without asking you",
                "Recovery fees claimed",
                "Workshops delivered per month",
            ),
            answer_index=1,
            explanation=(
                "If they cannot, the process is in your head — and everything in this course was "
                "about getting it out of there."
            ),
        ),
    ),
)


def section_8() -> CourseModule:
    """Section 8: the exits, and the money left on the table."""
    return CourseModule(
        id=_id("module", "exits-and-recovery"),
        title="Closed, Nurture, and the recovery fee",
        order=7,
        lessons=(
            Lesson(
                id=_id("lesson", "exits-and-recovery"),
                title="Exits you choose, not exits that happen",
                body=_S8_BODY,
                order=0,
                slides=_SECTION_8_SLIDES,
                drill_topics=("ops:exits-and-recovery",),
                measurement=(
                    "Every lapsed workshop on your board has its recovery position explicitly "
                    "resolved, and every parked deal carries a date with a reason behind it."
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
    "the-motion",
    "open-the-account",
    "the-workshop",
    "qualify-or-nurture",
    "scope-and-price",
    "contract-and-streams",
    "deliver-the-work",
    "exits-and-recovery",
)
# All eight are written (2026-07-30), which completes GRS-0217. The tuple stays, empty, because the
# test that guards it reads it.
SECTIONS_PLANNED: tuple[str, ...] = ()
