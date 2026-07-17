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
        "it is a network-economies read. The assessment IS the advancing move.",
        "sales:zero-sum-pipeline",
        "Every live account has a dated, owned next step in the pipeline board.",
    ),
    (
        "Total Account Awareness",
        "Sell to the account, not the contact. Total Account Awareness means knowing the whole "
        "buying unit, the incumbent, and the P&L line your solution moves — the discipline the "
        "Platform Power assessment enforces when it scores every module, not just the loudest one. "
        "In **retail brokerage** that is the whole 7-Powers surface; in **wealth** it is switching "
        "costs and brand together; on an **exchange** it is network and scale read as one system.",
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
        "earns the right to challenge.",
        "sales:relationship-weapon",
        "Each first meeting opens with account-specific evidence, not a generic pitch.",
    ),
    (
        "The Challenger Weapon — Teach",
        "The Challenger teaches the client something they did not know about their business. The "
        "Platform Power assessment is the teaching engine: it surfaces a bottleneck the client has "
        "under-priced — a thin moat in **retail brokerage**, an over-rated brand in **wealth**, a "
        "sub-scale **exchange** network. Lead with the insight that reframes their situation, then "
        "let the score carry the argument.",
        "sales:challenger-teach",
        "You can state one non-obvious, evidence-backed insight per target account.",
    ),
    (
        "The Challenger Weapon — Tailor & Take Control",
        "Teaching lands only when tailored to the buyer and only when you take control of the "
        "process — naming the next step and holding the timeline. Tailor the assessment read to "
        "operating model (**retail brokerage** vs **wealth** vs **exchange**) and to the "
        "incentives, then take control by scheduling the workshop, not asking for one. "
        "Comfort with tension is the Challenger's edge.",
        "sales:challenger-control",
        "You set the next date at the end of every advancing conversation.",
    ),
    (
        "The Demo Weapon — Show, Don't Tell",
        "The assessment IS the demo. Rather than describe value, run a scoped Platform Power read "
        "and let the client watch their own moat get measured. A live **retail brokerage** scale "
        "read, a **wealth** switching-cost score, or an **exchange** network-economies comparison "
        "demonstrates rigour no slide can. Show the method; the method sells.",
        "sales:demo-weapon",
        "At least one live/worked assessment artefact is shown in the demo, not just described.",
    ),
    (
        "Qualifying with the Assessment",
        "Qualify hard, early, with evidence. The Platform Power findings are your qualification "
        "lens: a genuine, addressable bottleneck means a deal; an already-strong surface means "
        "nurture, not push. Qualify a **retail brokerage** on a scale/counter-positioning gap, a "
        "**wealth** firm on brand/switching durability, an **exchange** on network density — and "
        "disqualify honestly when the assessment says the moat is already sound.",
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
        "deliverable.",
        "sales:awareness-to-close",
        "Each close ties a named assessment finding to a scoped, dated first deliverable.",
    ),
)


def sales_egoist_course() -> CourseTree:
    """Build the Sales Egoist course tree — 8 human-authored lessons, mandatory-first, no cert
    credit by itself (the certification sits on top in GRS-0127)."""
    lessons = tuple(
        Lesson(
            id=_id("lesson", str(order)),
            title=title,
            body=body,
            order=order,
            author=LessonAuthor.HUMAN,
            drill_topics=(drill,),
            measurement=measurement,
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
