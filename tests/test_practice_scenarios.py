"""Academy practice-scenario tests (GRS-0130).

The acceptance: practice-arena scenarios reference the Sales Egoist / product course content (not
generic filler); the seed is idempotent; and practice-arena feedback stays self-scoped and
AI-labelled with no approval record (non-negotiable #8 preserved).
"""

from __future__ import annotations

from datetime import UTC, datetime

from bcap_contracts.arena import ArenaSession

from grassmarket.data.repository import Repository
from grassmarket.workbench.content.practice_scenarios import academy_practice_scenarios
from grassmarket.workbench.content.seed import seed_academy_content
from tests.conftest import SeededConsultant

_NOW = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)


def test_scenarios_are_grounded_in_the_academy_doctrine() -> None:
    specs = academy_practice_scenarios()
    assert specs  # not empty
    for spec in specs:
        # Each names the doctrine it rehearses and probes a real power (benefit + barrier cues).
        assert "Sales Egoist" in spec.title
        assert spec.target_powers
        for power in spec.target_powers:
            assert power.power_key and power.benefit_cues and power.barrier_cues


def test_seed_publishes_scenarios_and_is_idempotent(
    repo: Repository, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    seed_academy_content(repo, admin.principal, now=_NOW)
    seed_academy_content(repo, admin.principal, now=_NOW)  # re-apply

    titles = [s.title for s in repo.list_arena_scenarios(alice.principal)]
    seeded = [s.title for s in academy_practice_scenarios()]
    # Every seeded scenario is present exactly once (idempotent by title).
    for title in seeded:
        assert titles.count(title) == 1


def test_practice_feedback_stays_self_scoped_and_ai_labelled() -> None:
    # #8: arena feedback is a labelled AI proposal on a self-owned session — never an approval
    # record. The contract has the label but no approver fields (deliberate exception).
    fields = ArenaSession.model_fields
    assert "feedback_is_ai_drafted" in fields  # the AI label
    assert "owner_consultant_id" in fields  # self-scoped
    assert not any("approv" in name for name in fields)  # no approval record
