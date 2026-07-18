"""Sales Egoist — the Academy's mandatory "Sales 101" core module (GRS-0122, ADR-0028).

This is the *seed* of the doctrine, authored through the GRS-0121 CMS as structured content (not
decks). It is grounded in the publicly-documented Challenger Sales method (teach → tailor → take
control) and Bruntsfield's own Platform Power assessment work — NOT a copy of any proprietary deck.
The founder deepens it from the uploaded Sales Egoist decks over the top of this v1; because the
course is versioned, that deepening is a new published version, never a code change.

Every lesson carries the two things the ticket requires: a spaced-repetition **drill** topic and a
concrete **measurement**, and each ties the sales motion to the assessment across the three
operating models — **retail brokerage, wealth, and exchange**.

IDs are derived (uuid5) from a stable namespace so re-seeding is idempotent — the same lesson keeps
the same id across every publish.
"""

from __future__ import annotations

from uuid import NAMESPACE_URL, UUID, uuid5

from bcap_contracts.learning import (
    CertificationCredit,
    CourseModule,
    CourseTree,
    Lesson,
    LessonAuthor,
)

SALES_EGOIST_SLUG = "sales-egoist"
_NS = "grassmarket:academy:sales-egoist"


def _id(kind: str, key: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"{_NS}:{kind}:{key}")


# (title, body, drill_topic, measurement) — order is the tuple index.
_LESSONS: tuple[tuple[str, str, str, str], ...] = (
    (
        "The Zero-Sum Pipeline",
        "Every advisory conversation you do not advance, a competitor advances instead — the "
        "pipeline is zero-sum, so passivity is a loss, not a neutral. The Sales Egoist owns the "
        "next step of every live account. Across operating models the 'next step' differs: for a "
        "**retail brokerage** it is booking the Platform Power workshop off a growth pain; for a "
        "**wealth** firm it is scoping a switching-cost or brand assessment; for an **exchange** "
        "it is a network-economies read. The assessment IS the advancing move."
        "\n\n"
        "**In practice.** A warm wealth prospect said 'let me think about it' three weeks ago and "
        "went quiet. The passive advisor waits for a reply that never comes; a rival is already "
        "booking their next meeting. The Egoist treats the silence as a live position to advance: "
        "'I re-ran your public switching-cost signals and found something worth 20 minutes — I've "
        "held Thursday 3pm and Friday 11am, which suits?' Notice it offers a dated step off a "
        "specific hook, and never asks 'are you still interested?'."
        "\n\n"
        "**The move.** End every conversation by setting the next dated step yourself and logging "
        "it on the pipeline board. No account sits without an owned, dated next action — a blank "
        "next-step field is a deal you are quietly losing.",
        "sales:zero-sum-pipeline",
        "Every live account has a dated, owned next step in the pipeline board.",
    ),
    (
        "Total Account Awareness",
        "Sell to the account, not the contact. Total Account Awareness means knowing the whole "
        "buying unit, the incumbent, and the P&L line your solution moves — the discipline the "
        "Platform Power assessment enforces when it scores every module, not just the loudest one. "
        "In **retail brokerage** that is the whole 7-Powers surface; in **wealth** it is switching "
        "costs and brand together; on an **exchange** it is network and scale read as one system."
        "\n\n"
        "**In practice.** A retail-brokerage deal looks like one enthusiastic champion — the Head "
        "of Product who loves the demo. Total Account Awareness says: map the rest before you "
        "celebrate. The economic buyer is the COO, who owns the cost-to-serve line the deal "
        "actually moves; the silent blocker is a Head of Risk who has to sign off any new vendor; "
        "the incumbent is not a competitor at all but an in-house build the CTO is proud of. Four "
        "people, one deal — and your champion can't close any of them."
        "\n\n"
        "**The move.** Before the next call, write the account on one line: buying unit "
        "(champion + economic buyer + blocker), incumbent (who/what you're really displacing), the "
        "P&L line the assessment finding moves. If you can't fill all three, that's your next "
        "discovery question — not your next pitch.",
        "sales:total-account-awareness",
        "For each account you can name the buying unit, the incumbent, and the P&L line moved.",
    ),
    (
        "The Relationship Weapon",
        "Trust is the base layer — without it, nothing else fires. The Relationship Weapon is "
        "earned by doing unglamorous account work first and bringing evidence, not opinion. The "
        "assessment is your credibility instrument: a **wealth** client trusts a scored "
        "brand/switching-cost finding over a claim; a **retail brokerage** trusts a benchmarked "
        "scale-economies read; an **exchange** trusts a network-density comparison. Relationship "
        "earns the right to challenge."
        "\n\n"
        "**In practice.** Two advisors open the same wealth first meeting. The first: 'We help "
        "firms like yours strengthen client retention — let me walk you through our platform.' "
        "Generic; the prospect has heard it ten times. The second: 'Before this call I looked at "
        "your public transfer-out data — your average in-specie transfer runs about six weeks "
        "against a two-week market benchmark. That friction is a switching-cost moat you're "
        "under-pricing, and it's exactly what the assessment scores.' The second advisor did 20 "
        "minutes of unglamorous homework and earned the room in one sentence."
        "\n\n"
        "**The move.** Never open cold. Bring one account-specific data point — a public signal, a "
        "benchmark, a scored finding — to every first meeting, and lead with it. Opinion invites "
        "debate; evidence invites the next question.",
        "sales:relationship-weapon",
        "Each first meeting opens with account-specific evidence, not a generic pitch.",
    ),
    (
        "The Challenger Weapon — Teach",
        "The Challenger teaches the client something they did not know about their business. The "
        "Platform Power assessment is the teaching engine: it surfaces a bottleneck the client has "
        "under-priced — a thin moat in **retail brokerage**, an over-rated brand in **wealth**, a "
        "sub-scale **exchange** network. Lead with the insight that reframes their situation, then "
        "let the score carry the argument."
        "\n\n"
        "**In practice.** A retail brokerage is certain scale is its moat. The assessment scored "
        "SCALE_ECONOMIES benefit only *Emerging*, not *Wide* — because past a certain AUA their "
        "unit cost curve flattens, so new volume no longer buys durable advantage. The teach: "
        "'Your leadership treats scale as the moat. On the evidence it's closer to your exposure — "
        "the cost curve says a better-capitalised entrant can match your economics. The moat you "
        "actually have is switching costs, and you're under-investing in it.' That reframes their "
        "whole strategy conversation, and the score — not your opinion — is doing the arguing."
        "\n\n"
        "**The move.** For each target account, prepare ONE non-obvious, evidence-backed insight "
        "that contradicts a belief they hold about their own business, and open the meeting with "
        "it. A good teach makes the client slightly uncomfortable, then relieved you brought it.",
        "sales:challenger-teach",
        "You can state one non-obvious, evidence-backed insight per target account.",
    ),
    (
        "The Challenger Weapon — Tailor & Take Control",
        "Teaching lands only when tailored to the buyer and only when you take control of the "
        "process — naming the next step and holding the timeline. Tailor the assessment read to "
        "operating model (**retail brokerage** vs **wealth** vs **exchange**) and to the "
        "incentives, then take control by scheduling the workshop, not asking for one. "
        "Comfort with tension is the Challenger's edge."
        "\n\n"
        "**In practice.** Same 'scale is your exposure' insight, three buyers. To the **COO** it's "
        "a cost-to-serve risk: 'if a rival matches your economics, your margin is the first thing "
        "that moves.' To the **CEO** it's competitive exposure: 'the moat the board thinks you "
        "have isn't the one the data supports.' To the **Head of Risk** it's concentration: 'your "
        "defensibility rests on one power that's thinner than assumed.' One finding, three "
        "tailored framings. Then take control: 'The next step is a 90-minute Platform Power "
        "workshop with your product and risk leads. I've held Tuesday and Thursday — which works?' "
        "— an offer with a date, not a request for permission."
        "\n\n"
        "**The move.** Tailor the same finding to each buyer's incentive, then close the "
        "conversation by naming the next step and offering two concrete slots. If you leave it as "
        "'let me know when suits', you've handed control back.",
        "sales:challenger-control",
        "You set the next date at the end of every advancing conversation.",
    ),
    (
        "The Demo Weapon — Show, Don't Tell",
        "The assessment IS the demo. Rather than describe value, run a scoped Platform Power read "
        "and let the client watch their own moat get measured. A live **retail brokerage** scale "
        "read, a **wealth** switching-cost score, or an **exchange** network-economies comparison "
        "demonstrates rigour no slide can. Show the method; the method sells."
        "\n\n"
        "**In practice.** Don't present a case study about someone else. In the meeting, pull up "
        "the wizard and score ONE module on the client's own numbers, live. Rate two "
        "subcomponents, watch the Platform Value move with its uncertainty band, and say: 'This is "
        "your switching-cost read on your data — a 49 with a wide band, because we've only "
        "assessed two of eleven subcomponents. Finish the assessment and that band tightens into a "
        "number you can take to your board.' They're not watching a pitch; they're watching their "
        "own moat get measured, and the honesty of the uncertainty band is what makes it credible."
        "\n\n"
        "**The move.** Bring at least one live or worked assessment artefact to every demo — a "
        "scored module, a heat map, an uncertainty band on their own figures — and let it do the "
        "talking. Describing rigour is a claim; showing it is proof.",
        "sales:demo-weapon",
        "At least one live/worked assessment artefact is shown in the demo, not just described.",
    ),
    (
        "Qualifying with the Assessment",
        "Qualify hard, early, with evidence. The Platform Power findings are your qualification "
        "lens: a genuine, addressable bottleneck means a deal; an already-strong surface means "
        "nurture, not push. Qualify a **retail brokerage** on a scale/counter-positioning gap, a "
        "**wealth** firm on brand/switching durability, an **exchange** on network density — and "
        "disqualify honestly when the assessment says the moat is already sound."
        "\n\n"
        "**In practice.** Two wealth prospects, same enthusiasm. Prospect A scores a real "
        "switching-cost gap — slow transfers, shallow linked-account depth, a book that would "
        "leave if a rival made it easy. That's a deal: an addressable bottleneck with a lever you "
        "can move. Prospect B scores a strong brand and a genuinely sticky book already. Pushing B "
        "means fighting 'why would we change?' for months and losing — so you nurture, not push, "
        "and say so: 'Honestly, your moat here is already sound; I'd be selling you a fix you "
        "don't need. Let's revisit if your transfer times slip.' Disqualifying B *builds* the "
        "trust that wins their next, real project."
        "\n\n"
        "**The move.** For every deal you pursue, name the specific assessment finding that "
        "justifies it. If you can't, you're chasing enthusiasm, not a bottleneck — nurture it and "
        "spend the hour on a qualified deal instead.",
        "sales:qualify-with-assessment",
        "Every qualified deal cites the specific assessment finding that justifies pursuit.",
    ),
    (
        "From Awareness to Close",
        "Total Account Awareness closes by converting the assessment finding into a scoped "
        "engagement the client cannot un-see. Counter-position the status quo: the cost of leaving "
        "the bottleneck unaddressed, priced through the value bridge (cost £ / lever NPV £ / "
        "strategic ordinal — never mixed with score). Close a **retail brokerage**, **wealth**, "
        "or **exchange** account on the gap the assessment made undeniable, with a dated first "
        "deliverable."
        "\n\n"
        "**In practice.** The finding is a Client Management System bottleneck capping onboarding "
        "throughput. Don't close on the product; close on the cost of inaction: 'The assessment "
        "puts your onboarding ceiling here. Every quarter you leave it is roughly N accounts you "
        "can't take on — the value bridge prices that lost throughput as an NPV, separately from "
        "the score. The first deliverable is a modernisation roadmap by the 30th; we start there, "
        "and you decide the rest once you can see it.' The gap is now undeniable, the status quo "
        "has a price tag, and the ask is small and dated — not a leap of faith."
        "\n\n"
        "**The move.** Tie every close to a named assessment finding and a scoped, *dated* first "
        "deliverable — never an open-ended engagement. Counter-position on the cost of leaving the "
        "gap, priced through the value bridge, and keep score-points and pounds in separate "
        "sentences.",
        "sales:awareness-to-close",
        "Each close ties a named assessment finding to a scoped, dated first deliverable.",
    ),
)


# (check_question, check_answer) per lesson, in _LESSONS order — the retrieval-practice pair the
# advisor answers to complete the lesson, and which seeds its spaced-repetition drill (GRS-0139).
_CHECKS: tuple[tuple[str, str], ...] = (
    (
        "Why is a passive advisory conversation a loss rather than neutral — and what "
        "does the Sales Egoist own on every live account?",
        "The pipeline is zero-sum: any step you don't advance, a competitor advances "
        "instead. So the Sales Egoist owns the next step of every live account, and the "
        "Platform Power assessment is that advancing move.",
    ),
    (
        "What three things must you be able to name for each account, and why sell to "
        "the account rather than the contact?",
        "The whole buying unit, the incumbent, and the P&L line your solution moves. "
        "Selling to one contact misses the buying unit and the economics the assessment "
        "scores across every module.",
    ),
    (
        "How do you earn the right to challenge a client, and what makes the assessment "
        "your credibility instrument?",
        "By doing the unglamorous account work first and bringing evidence, not opinion — "
        "a scored finding a client trusts over a claim. Relationship earns the right to "
        "challenge.",
    ),
    (
        "What is the Challenger's 'teach', and how does the assessment power it?",
        "Teach the client a non-obvious insight about their own business — a bottleneck "
        "they've under-priced — that the Platform Power assessment surfaces. Lead with the "
        "insight; let the score carry the argument.",
    ),
    (
        "Teaching lands only under two conditions — what are they?",
        "It must be tailored to the buyer's operating model and incentives, and you must "
        "take control of the process by naming and scheduling the next step, not asking "
        "for one.",
    ),
    (
        "In the Sales Egoist method, what IS the demo — and why show rather than tell?",
        "The assessment is the demo: run a scoped Platform Power read and let the client "
        "watch their own moat get measured. A live artefact shows rigour no slide can — "
        "the method sells.",
    ),
    (
        "How do the assessment findings qualify — and disqualify — a deal?",
        "A genuine, addressable bottleneck means a deal; an already-strong surface means "
        "nurture, not push. Qualify on the specific gap, and disqualify honestly when the "
        "moat is already sound.",
    ),
    (
        "How does Total Account Awareness convert a finding into a close?",
        "Turn the finding into a scoped engagement, counter-positioning the cost of "
        "leaving the bottleneck unaddressed (priced via the value bridge, never mixed with "
        "the score), and close on the named finding with a dated first deliverable.",
    ),
)


def sales_egoist_course() -> CourseTree:
    """Build the Sales Egoist course tree — 8 human-authored lessons, mandatory-first, no cert
    credit by itself (the certification sits on top in GRS-0127). Each lesson carries a
    retrieval-practice check (GRS-0139) that gates completion and seeds its drill."""
    lessons = tuple(
        Lesson(
            id=_id("lesson", str(order)),
            title=title,
            body=body,
            order=order,
            author=LessonAuthor.HUMAN,
            drill_topics=(drill,),
            measurement=measurement,
            check_question=_CHECKS[order][0],
            check_answer=_CHECKS[order][1],
        )
        for order, (title, body, drill, measurement) in enumerate(_LESSONS)
    )
    module = CourseModule(
        id=_id("module", "core"),
        title="Sales Egoist — the core doctrine",
        order=0,
        lessons=lessons,
    )
    return CourseTree(
        title="Sales Egoist",
        summary=(
            "The mandatory Sales 101 doctrine: own the zero-sum pipeline, build Total Account "
            "Awareness, and wield the Relationship, Challenger, and Demo weapons — each tied "
            "to the Platform Power assessment across retail brokerage, wealth, and exchange."
        ),
        certification_credit=CertificationCredit.NONE,
        mandatory_first=True,
        modules=(module,),
    )
