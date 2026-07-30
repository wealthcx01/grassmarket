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

from bcap_contracts.learning import (
    CertificationCredit,
    CourseTree,
)

from grassmarket.workbench.content.sales_ops_slides import rebuilt_sections

SALES_OPS_SLUG = "sales-ops-playbook"
_NS = "grassmarket:academy:sales-ops-playbook"


def _id(kind: str, key: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"{_NS}:{kind}:{key}")


def sales_ops_playbook_course() -> CourseTree:
    """The sales-ops process course: eight sections keyed to the CRM pipeline stages and grounded
    in the v7 two-stream schedule. Not a cert credit by itself (that sits on the doctrine)."""
    # The GRS-0217 rebuild: eight sections to the GRS-0215 depth standard, 192 slides, one
    # section test each, every stage name taken from the `PipelineStage` enum rather than
    # paraphrased. The four superseded paragraph-lessons that used to live in this file were
    # deleted on 2026-07-30, on the same standing decision as the three product courses.
    modules = rebuilt_sections()
    return CourseTree(
        title="Sales Operations Playbook",
        summary=(
            "The standing operational motion on meeting a prospect, keyed to the CRM pipeline "
            "stages (prospect → workshop → qualify → scope → contract → deliver) and grounded in "
            "the v7 two-stream commission schedule + workshop recovery fees."
        ),
        certification_credit=CertificationCredit.NONE,
        mandatory_first=False,
        modules=modules,
    )
