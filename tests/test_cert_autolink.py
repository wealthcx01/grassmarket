"""Certification-evidence auto-linking tests (GRS-0131).

The gap this closes: certification evidence used to be honour-system admin entry. Now real
participation in a *finalised* assessment auto-counts — a non-lead co-rater earns a shadow credit,
the lead earns an observed-lead credit — each once per assessment (idempotent), and only for
PRODUCTION assessments. The reconciliation of the two high-stakes thresholds lives in
tests/test_certification.py.
"""

from __future__ import annotations

from datetime import UTC, datetime

from bcap_contracts.assessments import RecordProvenance
from bcap_contracts.certification import CertificationEventKind

from grassmarket.data.models import AssessmentORM, ModuleRatingDraftORM
from grassmarket.data.repository import Repository
from tests.conftest import SeededConsultant

_NOW = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)


def _add_rater(repo: Repository, assessment_id, rater_id) -> None:
    repo._session.add(
        ModuleRatingDraftORM(
            owner_consultant_id=rater_id, assessment_id=assessment_id, module_key="APP_SERVER"
        )
    )
    repo._session.flush()


def _record(repo: Repository, principal, advisor_id):
    return repo.get_certification_record(principal, advisor_id)


def test_participation_auto_credits_shadow_and_observed_lead(
    repo: Repository, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    # Alice leads; Bob co-rates. A finalised production assessment credits both automatically.
    assessment = repo.create_assessment(alice.principal, subject="Meridian")
    _add_rater(repo, assessment.id, bob.principal.consultant_id)
    _add_rater(repo, assessment.id, alice.principal.consultant_id)  # the lead also rated
    row = repo._session.get(AssessmentORM, assessment.id)

    repo._auto_credit_participation(row, _NOW)

    # Bob (non-lead rater) earns a shadow; Alice (lead) earns observed-lead — not a shadow.
    assert _record(repo, bob.principal, bob.principal.consultant_id).shadow_count == 1
    alice_rec = _record(repo, alice.principal, alice.principal.consultant_id)
    assert alice_rec.observed_lead_logged is True
    assert alice_rec.shadow_count == 0  # leading is observed-lead, never a self-shadow

    # The audit events are tied to the real assessment (the founder's ask).
    bob_events = repo.list_certification_events(bob.principal, bob.principal.consultant_id)
    shadow = [e for e in bob_events if e.kind is CertificationEventKind.SHADOW_LOGGED]
    assert len(shadow) == 1 and shadow[0].assessment_id == assessment.id


def test_auto_credit_is_idempotent_per_assessment(
    repo: Repository, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    assessment = repo.create_assessment(alice.principal, subject="Once")
    _add_rater(repo, assessment.id, bob.principal.consultant_id)
    row = repo._session.get(AssessmentORM, assessment.id)

    repo._auto_credit_participation(row, _NOW)
    repo._auto_credit_participation(row, _NOW)  # re-run (e.g. a retry) must not double-count

    assert _record(repo, bob.principal, bob.principal.consultant_id).shadow_count == 1


def test_a_second_assessment_counts_a_second_shadow(
    repo: Repository, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    for subject in ("A", "B"):
        a = repo.create_assessment(alice.principal, subject=subject)
        _add_rater(repo, a.id, bob.principal.consultant_id)
        repo._auto_credit_participation(repo._session.get(AssessmentORM, a.id), _NOW)
    # Two distinct finalised assessments → two shadows (per-assessment, not per-finalise-blindly).
    assert _record(repo, bob.principal, bob.principal.consultant_id).shadow_count == 2


def test_sandbox_participation_does_not_count(
    repo: Repository, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    # A sandbox/demo run is training, never real certification evidence (ADR-0029).
    assessment = repo.create_assessment(
        alice.principal, subject="Sandbox", provenance=RecordProvenance.SANDBOX
    )
    _add_rater(repo, assessment.id, bob.principal.consultant_id)
    repo._auto_credit_participation(repo._session.get(AssessmentORM, assessment.id), _NOW)

    assert _record(repo, bob.principal, bob.principal.consultant_id).shadow_count == 0
    assert (
        _record(repo, alice.principal, alice.principal.consultant_id).observed_lead_logged is False
    )
