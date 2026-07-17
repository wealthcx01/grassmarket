"""Sales-ops playbook tests (GRS-0129).

The acceptance: a sales-ops process module exists in the CMS, grounded in the v7 agreement +
commission schedule; it cross-references the Pipeline/GTM stages so process and tooling line up; and
it is CMS-authored (published through GRS-0121), not hardcoded copy.
"""

from __future__ import annotations

from datetime import UTC, datetime

from bcap_contracts.entities import PipelineStage

from grassmarket.data.repository import Repository
from grassmarket.workbench.content.sales_ops_playbook import (
    SALES_OPS_SLUG,
    sales_ops_playbook_course,
)
from grassmarket.workbench.content.seed import seed_academy_content
from tests.conftest import SeededConsultant

_NOW = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)

# The forward operational path the playbook must walk (off-ramps Closed/Nurture are prose).
_FORWARD_STAGES = (
    PipelineStage.PROSPECT,
    PipelineStage.WORKSHOP_SCHEDULED,
    PipelineStage.WORKSHOP_DELIVERED,
    PipelineStage.QUALIFIED,
    PipelineStage.SCOPED,
    PipelineStage.CONTRACTED,
    PipelineStage.ACTIVE,
    PipelineStage.DELIVERED,
)


def test_module_exists_as_structured_content() -> None:
    tree = sales_ops_playbook_course()
    lessons = [lesson for module in tree.modules for lesson in module.lessons]
    assert len(lessons) == 4
    for lesson in lessons:
        assert lesson.body.strip() and lesson.drill_topics and lesson.measurement


def test_cross_references_every_forward_pipeline_stage() -> None:
    body = " ".join(
        lesson.body for module in sales_ops_playbook_course().modules for lesson in module.lessons
    )
    for stage in _FORWARD_STAGES:
        assert stage.value in body, f"the playbook does not reference the '{stage.value}' stage"


def test_grounded_in_the_v7_commission_schedule() -> None:
    text = " ".join(
        lesson.body for module in sales_ops_playbook_course().modules for lesson in module.lessons
    ).lower()
    # The two commission streams + the recovery-fee mechanism (v7 schedule).
    assert "stream a" in text and "stream b" in text
    assert "recovery fee" in text
    assert "self-sourced" in text  # the v7 sourcing distinction that changes the rate


def test_seed_publishes_the_playbook_through_the_cms(
    repo: Repository, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    seed_academy_content(repo, admin.principal, now=_NOW)
    published = repo.get_published_course(alice.principal, SALES_OPS_SLUG)
    assert published.tree.title == "Sales Operations Playbook"
    assert (
        published.tree.mandatory_first is False
    )  # the doctrine (Sales Egoist) is the mandatory one
    assert len(published.tree.modules[0].lessons) == 4
