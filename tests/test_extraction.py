"""Path B extraction → review (GRS-0030).

THE test (the PRD §3.3 acceptance criterion, executable): a confirmed extraction produces a
byte-identical scoring run to the same data entered manually through Path A — because both flow
through the identical document → inputs → content-hash path. Plus: unconfirmed extractions never
reach the engine, per-field provenance persists, and extracted evidence grades are capped.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from bcap_contracts.assessments import AssessmentDocument, SubcomponentRating
from bcap_contracts.common import EvidenceGrade, MaturityLevel
from bcap_contracts.extraction import ExtractionStatus
from bcap_contracts.registry import load_registry
from cryptography.fernet import Fernet

from grassmarket.assessments.service import _complete_inputs
from grassmarket.data.repository import (
    ConflictError,
    NotFoundError,
    Repository,
    ScopeViolationError,
    content_hash_for,
)
from grassmarket.pathb.cipher import FernetTranscriptCipher
from grassmarket.pathb.extraction import (
    ExtractedFieldSpec,
    FixtureExtractor,
)
from tests.conftest import SeededConsultant
from tests.test_assessment_lifecycle import _scoreable_partial_doc

_NOW = datetime(2026, 7, 14, 12, 0, tzinfo=UTC)


def _cipher() -> FernetTranscriptCipher:
    return FernetTranscriptCipher(Fernet.generate_key().decode())


def _doc() -> AssessmentDocument:
    """A scoreable partial document with every evidence grade at E2 — the extraction evidence-cap
    (E3/E4 → E1 on unsupported subcomponents and unconditionally on powers) is a no-op here, so Path
    A and Path B documents are exactly equal."""
    base = _scoreable_partial_doc()
    sub = base.subcomponents[0].model_copy(update={"evidence_grade": EvidenceGrade.E2_INTERVIEW})
    powers = tuple(
        p.model_copy(
            update={
                "benefit_grade": EvidenceGrade.E2_INTERVIEW,
                "barrier_grade": EvidenceGrade.E2_INTERVIEW,
            }
        )
        for p in base.powers
    )
    return base.model_copy(update={"subcomponents": (sub,), "powers": powers})


def _transcript_id(repo: Repository, owner: SeededConsultant, cipher: FernetTranscriptCipher):
    return repo.ingest_pasted_transcript(
        owner.principal, text="the discovery call", source_filename="call.txt", cipher=cipher
    ).id


# --- THE test: identical scoring run --------------------------------------------------------


def test_confirmed_extraction_scores_identically_to_manual_entry(
    repo: Repository, alice: SeededConsultant
) -> None:
    registry = load_registry()
    cipher = _cipher()
    document = _doc()

    # Path A — the wizard: the document is entered manually.
    a = repo.create_assessment(alice.principal, subject="Meridian")
    repo.update_assessment(alice.principal, a.id, document=document)
    doc_a = repo.get_assessment(alice.principal, a.id).document

    # Path B — extraction: the SAME data arrives via a confirmed extraction from a transcript.
    b = repo.create_assessment(alice.principal, subject="Meridian")
    tid = _transcript_id(repo, alice, cipher)
    extraction = repo.propose_extraction(
        alice.principal,
        assessment_id=b.id,
        transcript_id=tid,
        extractor=FixtureExtractor(document=document),
        cipher=cipher,
    )
    # GATED: nothing has reached assessment B yet — its document is still the empty default.
    assert repo.get_assessment(alice.principal, b.id).document != doc_a
    repo.confirm_extraction(alice.principal, extraction.id, now=_NOW)
    doc_b = repo.get_assessment(alice.principal, b.id).document

    # The confirmed Path B document is exactly the manual Path A document…
    assert doc_b == doc_a
    # …so the scoring runs are byte-identical: same inputs → same content hash (the run's identity).
    hash_a = content_hash_for(_complete_inputs(doc_a, registry), "engine-1", "method-1", "coef-1")
    hash_b = content_hash_for(_complete_inputs(doc_b, registry), "engine-1", "method-1", "coef-1")
    assert hash_a == hash_b


# --- Unconfirmed extractions never reach the engine ----------------------------------------


def test_a_proposed_extraction_does_not_touch_the_assessment(
    repo: Repository, alice: SeededConsultant
) -> None:
    cipher = _cipher()
    a = repo.create_assessment(alice.principal, subject="X")
    empty = repo.get_assessment(alice.principal, a.id).document
    tid = _transcript_id(repo, alice, cipher)
    repo.propose_extraction(
        alice.principal,
        assessment_id=a.id,
        transcript_id=tid,
        extractor=FixtureExtractor(document=_doc()),
        cipher=cipher,
    )
    # The proposal exists, but the assessment's document is unchanged — nothing scoreable leaked.
    assert repo.get_assessment(alice.principal, a.id).document == empty


# --- Per-field provenance persisted --------------------------------------------------------


def test_field_provenance_is_persisted_and_accepted_on_confirm(
    repo: Repository, alice: SeededConsultant
) -> None:
    from bcap_contracts.extraction import ExtractionConfidence

    cipher = _cipher()
    a = repo.create_assessment(alice.principal, subject="X")
    tid = _transcript_id(repo, alice, cipher)
    provenance = (
        ExtractedFieldSpec(
            "subcomponent:APP_SERVER_SECURITY_COMPLIANCE", ExtractionConfidence.HIGH, 0, 40
        ),
        ExtractedFieldSpec("power:SCALE_ECONOMIES", ExtractionConfidence.MEDIUM, 41, 80),
    )
    ext = repo.propose_extraction(
        alice.principal,
        assessment_id=a.id,
        transcript_id=tid,
        extractor=FixtureExtractor(document=_doc(), provenance=provenance),
        cipher=cipher,
    )
    prov = repo.list_field_provenance(alice.principal, ext.id)
    assert {p.field_ref for p in prov} == {
        "subcomponent:APP_SERVER_SECURITY_COMPLIANCE",
        "power:SCALE_ECONOMIES",
    }
    assert all(p.transcript_id == tid for p in prov)
    assert all(not p.accepted for p in prov)  # not accepted until confirmed

    repo.confirm_extraction(alice.principal, ext.id, now=_NOW)
    assert all(p.accepted for p in repo.list_field_provenance(alice.principal, ext.id))


# --- Evidence-grade discipline -------------------------------------------------------------


def test_extraction_caps_high_evidence_grades_without_an_artifact(
    repo: Repository, alice: SeededConsultant
) -> None:
    cipher = _cipher()
    a = repo.create_assessment(alice.principal, subject="X")
    tid = _transcript_id(repo, alice, cipher)
    # An extractor claims E4 (observed) with no evidence link — it must be knocked down to E1.
    doc = AssessmentDocument(
        subject="X",
        subcomponents=(
            SubcomponentRating(
                module_key="APP_SERVER",
                subcomponent_key="APP_SERVER_SECURITY_COMPLIANCE",
                level=MaturityLevel.ADVANCED,
                evidence_grade=EvidenceGrade.E4_OBSERVED,
            ),
        ),
    )
    ext = repo.propose_extraction(
        alice.principal,
        assessment_id=a.id,
        transcript_id=tid,
        extractor=FixtureExtractor(document=doc),
        cipher=cipher,
    )
    assert ext.proposed_document.subcomponents[0].evidence_grade is EvidenceGrade.E1_SELF_REPORTED


def test_extraction_caps_power_grades_which_can_never_carry_an_artifact(
    repo: Repository, alice: SeededConsultant
) -> None:
    from bcap_contracts.assessments import PowerEntry
    from bcap_contracts.common import StrengthRating

    cipher = _cipher()
    a = repo.create_assessment(alice.principal, subject="X")
    tid = _transcript_id(repo, alice, cipher)
    # A power carries no evidence-ref field, so an extracted E4 grade is unsupportable → capped.
    doc = AssessmentDocument(
        subject="X",
        powers=(
            PowerEntry(
                power_key="SCALE_ECONOMIES",
                benefit=StrengthRating.EMERGING,
                barrier=StrengthRating.EMERGING,
                benefit_grade=EvidenceGrade.E4_OBSERVED,
                barrier_grade=EvidenceGrade.E3_ARTIFACT,
            ),
        ),
    )
    ext = repo.propose_extraction(
        alice.principal,
        assessment_id=a.id,
        transcript_id=tid,
        extractor=FixtureExtractor(document=doc),
        cipher=cipher,
    )
    power = ext.proposed_document.powers[0]
    assert power.benefit_grade is EvidenceGrade.E1_SELF_REPORTED
    assert power.barrier_grade is EvidenceGrade.E1_SELF_REPORTED


# --- Lifecycle + scoping -------------------------------------------------------------------


def test_confirm_is_single_shot(repo: Repository, alice: SeededConsultant) -> None:
    cipher = _cipher()
    a = repo.create_assessment(alice.principal, subject="X")
    tid = _transcript_id(repo, alice, cipher)
    ext = repo.propose_extraction(
        alice.principal,
        assessment_id=a.id,
        transcript_id=tid,
        extractor=FixtureExtractor(document=_doc()),
        cipher=cipher,
    )
    repo.confirm_extraction(alice.principal, ext.id, now=_NOW)
    assert repo.get_extraction(alice.principal, ext.id).status is ExtractionStatus.CONFIRMED
    with pytest.raises(ConflictError, match="already confirmed"):
        repo.confirm_extraction(alice.principal, ext.id, now=_NOW)


def test_extraction_is_owner_scoped(
    repo: Repository, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    cipher = _cipher()
    a = repo.create_assessment(alice.principal, subject="X")
    tid = _transcript_id(repo, alice, cipher)
    ext = repo.propose_extraction(
        alice.principal,
        assessment_id=a.id,
        transcript_id=tid,
        extractor=FixtureExtractor(document=_doc()),
        cipher=cipher,
    )
    with pytest.raises(ScopeViolationError):
        repo.get_extraction(bob.principal, ext.id)
    with pytest.raises(ScopeViolationError):
        repo.confirm_extraction(bob.principal, ext.id, now=_NOW)


def test_proposing_against_a_foreign_transcript_is_refused(
    repo: Repository, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    cipher = _cipher()
    a = repo.create_assessment(alice.principal, subject="X")
    bob_tid = _transcript_id(repo, bob, cipher)  # bob's transcript
    with pytest.raises((ScopeViolationError, NotFoundError)):
        repo.propose_extraction(
            alice.principal,
            assessment_id=a.id,
            transcript_id=bob_tid,
            extractor=FixtureExtractor(document=_doc()),
            cipher=cipher,
        )
