"""Sales operational-process playbook (GRS-0129, ADR-0028) — the standing motion an advisor runs on
meeting a prospect, authored through the GRS-0121 CMS.

Where Sales Egoist is the *doctrine*, this is the *operational process*: what the advisor actually
does at each pipeline stage, so the process the CRM (§4 Pipeline/GTM) enables and the process the
Academy teaches are the same. Each lesson is keyed to the real `PipelineStage` values, and the
commission mechanics are grounded in the v7 two-stream schedule (product Stream A / consultancy
Stream B + workshop recovery fees) — the schedule is the source of truth, referenced, never
re-typed here as figures (the live numbers live on the product courses, GRS-0123).

IDs are derived (uuid5) from a stable namespace so re-seeding is idempotent.
"""

from __future__ import annotations

from uuid import NAMESPACE_URL, UUID, uuid5

from bcap_contracts.entities import PipelineStage
from bcap_contracts.learning import (
    CertificationCredit,
    CourseModule,
    CourseTree,
    Lesson,
    LessonAuthor,
)

SALES_OPS_SLUG = "sales-ops-playbook"
_NS = "grassmarket:academy:sales-ops-playbook"


def _id(kind: str, key: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"{_NS}:{kind}:{key}")


def _stages(*stages: PipelineStage) -> str:
    return " → ".join(s.value for s in stages)


# (title, body, drill_topic, measurement) — order is the tuple index. Each body names the CRM
# PipelineStage(s) it corresponds to, so process and tooling line up (GRS-0129 acceptance).
_LESSONS: tuple[tuple[str, str, str, str], ...] = (
    (
        "Open the account and book the workshop",
        "The motion begins the moment a prospect exists. In the CRM this is the "
        f"'{_stages(PipelineStage.PROSPECT, PipelineStage.WORKSHOP_SCHEDULED)}' move: create the "
        "prospect, capture the contact and sector, and book the Platform Power workshop off a "
        "growth pain — the workshop is the advancing action, not a courtesy call. Sourcing the "
        "prospect yourself is what earns the self-sourced commission rate later, so log it now."
        "\n\n"
        "**In practice.** You meet a wealth-firm COO at a conference who mentions, in passing, "
        "that onboarding takes too long. The passive move is 'I'll add you to the CRM and send a "
        "follow-up.' The ops move is to open the account there and then and book off the pain you "
        "just heard: 'That onboarding friction is exactly what a Platform Power workshop scores — "
        "it's 90 minutes, on your own numbers. I've got Thursday the 12th; shall I hold it?' You "
        "leave with a dated workshop and the growth pain captured in the notes, and you log "
        "yourself as the source — that's what earns the self-sourced rate when the deal converts."
        "\n\n"
        "**The move.** Within the first week, every new prospect has a booked workshop (or a dated "
        "next step) AND a captured growth pain in the notes. A prospect with no pain and no date "
        "is a business card, not a deal.",
        "ops:open-and-book",
        "Every new prospect has a booked workshop or a dated next step within the first week.",
    ),
    (
        "Deliver the workshop and qualify",
        "Run the workshop, then move the CRM from "
        f"'{_stages(PipelineStage.WORKSHOP_DELIVERED, PipelineStage.QUALIFIED)}'. The workshop IS "
        "the demo (see Sales Egoist): the client watches their own moat get scored. Qualify hard "
        "on a genuine, addressable bottleneck — a real gap means advance; a strong surface "
        "means Nurture, not push. If a represented product fixes the gap, that is where product "
        "commission (Stream A) enters."
        "\n\n"
        "**In practice.** In the workshop you score the COO's switching-cost module live, and the "
        "assessment surfaces thin linked-account depth — a real, addressable gap. That is a "
        "qualify: move the CRM to Qualified and log the finding verbatim. Had it scored a strong, "
        "sticky book instead, you would move it to Nurture and say so honestly, rather than push a "
        "fix they don't need. And notice the second door: if a product you represent (say a "
        "brand-data or onboarding tool) is what closes that specific gap, this is the moment "
        "Stream A product commission enters the deal alongside the consultancy work."
        "\n\n"
        "**The move.** Leave every workshop with the CRM at Qualified or Nurture — never left at "
        "Delivered — and the specific assessment finding recorded against the account. 'It went "
        "well' is not a qualification; a named bottleneck is.",
        "ops:deliver-and-qualify",
        "Each qualified prospect cites the specific assessment finding that justifies pursuit.",
    ),
    (
        "Scope and contract",
        "Convert the finding into a scoped engagement, moving the CRM from "
        f"'{_stages(PipelineStage.SCOPED, PipelineStage.CONTRACTED)}'. Scope against the value "
        "bridge (cost / lever NPV / strategic ordinal — never mixed with the score), and set a "
        "dated first deliverable. Contracting is the gate that opens consultancy commission "
        "(Stream B): the delivery_type × sourcing cell of the v7 schedule sets your rate, and "
        "self-sourced always pays more than firm-sourced."
        "\n\n"
        "**In practice.** You turn 'thin linked-account depth' into a scoped six-week engagement "
        "whose first deliverable is a modernisation roadmap, dated to the 30th. You price it "
        "against the value bridge — the NPV of the retention lift the fix unlocks — and you keep "
        "that in a different sentence from the score: the assessment says *how weak* the moat is; "
        "the value bridge says *what fixing it is worth*, in pounds. When it moves to Contracted, "
        "Stream B opens, and the v7 schedule's delivery_type × sourcing cell sets your rate — the "
        "self-sourced prospect you opened in lesson one now pays more than a firm-sourced one."
        "\n\n"
        "**The move.** Never contract without a scoped, *dated* first deliverable on the CRM, and "
        "never quote a price by dividing a score into pounds — the value bridge prices the lever, "
        "the score rates the moat, and the two never share an equation.",
        "ops:scope-and-contract",
        "Each contracted engagement has a scoped, dated first deliverable on the CRM.",
    ),
    (
        "Deliver, and protect the recovery fee",
        "Execute the engagement: "
        f"'{_stages(PipelineStage.ACTIVE, PipelineStage.DELIVERED)}'. Keep the comms log current, "
        "the account has one activity timeline. If a workshop was delivered but the deal did not "
        "contract inside the attribution window, the **workshop recovery fee** applies — the v7 "
        "schedule lets you recover the workshop effort rather than write it off. A Closed or "
        "Nurtured deal is not a failure of process; it is a recorded outcome you re-engage later."
        "\n\n"
        "**In practice.** The retention engagement runs Active → Delivered, and every touch — the "
        "roadmap review, the check-in call, the sign-off — goes on the one account timeline, so "
        "anyone can see the deal's true state. Now the harder case: a different prospect took the "
        "workshop but never contracted, and the attribution window has closed. The amateur writes "
        "it off as a loss. The Sales Egoist resolves the **recovery fee** — the v7 schedule lets "
        "you recover the workshop effort — and moves the deal to Nurture with a dated re-engage "
        "reminder, because a scored moat that wasn't ready today is a warm lead in two quarters."
        "\n\n"
        "**The move.** Keep one current activity timeline per account, and never let a delivered "
        "workshop lapse silently: every delivered or lapsed engagement has its recovery-fee "
        "position explicitly resolved, and every parked deal carries a dated reason to come back.",
        "ops:deliver-and-recover",
        "Every delivered or lapsed engagement has its recovery-fee position resolved, not ignored.",
    ),
)


def sales_ops_playbook_course() -> CourseTree:
    """The sales-ops process module — four lessons keyed to the CRM pipeline stages, grounded in the
    v7 commission schedule. Not a cert credit by itself (that sits on the doctrine, GRS-0127)."""
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
        title="The operational motion, stage by stage",
        order=0,
        lessons=lessons,
    )
    return CourseTree(
        title="Sales Operations Playbook",
        summary=(
            "The standing operational motion on meeting a prospect, keyed to the CRM pipeline "
            "stages (prospect → workshop → qualify → scope → contract → deliver) and grounded in "
            "the v7 two-stream commission schedule + workshop recovery fees."
        ),
        certification_credit=CertificationCredit.NONE,
        mandatory_first=False,
        modules=(module,),
    )
