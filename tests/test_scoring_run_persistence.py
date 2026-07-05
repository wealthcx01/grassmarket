"""Scoring-run persistence tests (GRS-0006) — immutable, content-hashed, version-stamped, scoped.

Runs go through the repository only (non-negotiable #5), are append-only and immutable (finalisation
is the one permitted state change), and a consultant can never read another's runs (non-negotiable
#9). The content hash is stable and recomputable from the stored inputs — the tamper-evidence seal.
"""

from __future__ import annotations

import uuid

import pytest
from bcap_contracts.registry import load_registry

from grassmarket.atlas import AssessmentInputs, score
from grassmarket.atlas.draft_coefficients import draft_v1_coefficient_set
from grassmarket.data.repository import (
    ConflictError,
    NotFoundError,
    Repository,
    ScopeViolationError,
    content_hash_for,
)
from tests._atlas_inputs import uniform_inputs
from tests.conftest import SeededConsultant

_REGISTRY = load_registry()
_COEFFS = draft_v1_coefficient_set(_REGISTRY)
_INPUTS = uniform_inputs(_REGISTRY)
_RESULT = score(_INPUTS, _COEFFS, _REGISTRY)
_ASSESSMENT = uuid.uuid4()


def _create(repo: Repository, owner: SeededConsultant, inputs: AssessmentInputs = _INPUTS):
    result = score(inputs, _COEFFS, _REGISTRY)
    return repo.create_scoring_run(
        owner.principal, assessment_id=_ASSESSMENT, inputs=inputs, result=result
    )


def test_run_is_version_stamped_and_hashed(repo: Repository, alice: SeededConsultant) -> None:
    run = _create(repo, alice)
    assert run.engine_version == _RESULT.engine_version
    assert run.methodology_version == "1.1"
    assert run.coefficient_version == _COEFFS.version
    assert run.v_index == _RESULT.composite.v_index
    assert run.owner_consultant_id == alice.principal.consultant_id
    # The stored hash equals a hash independently recomputed from the same inputs + versions.
    expected = content_hash_for(
        _INPUTS,
        _RESULT.engine_version,
        _RESULT.methodology_version,
        _COEFFS.version,
    )
    assert run.content_hash == expected


def test_content_hash_is_stable_run_to_run(repo: Repository, alice: SeededConsultant) -> None:
    a = _create(repo, alice)
    b = _create(repo, alice)  # identical inputs + versions → identical hash (append-only re-run)
    assert a.id != b.id
    assert a.content_hash == b.content_hash


def test_hash_recomputes_from_stored_inputs_tamper_evidence(
    repo: Repository, alice: SeededConsultant
) -> None:
    run = _create(repo, alice)
    record = repo.get_scoring_run_record(alice.principal, run.id)
    restored = AssessmentInputs.model_validate_json(record.inputs_json)
    recomputed = content_hash_for(
        restored,
        record.engine_version,
        record.methodology_version,
        record.coefficient_version,
    )
    assert recomputed == record.content_hash


def test_finalisation_locks_and_is_idempotent_refused(
    repo: Repository, alice: SeededConsultant
) -> None:
    run = _create(repo, alice)
    assert run.finalised is False
    finalised = repo.finalise_scoring_run(alice.principal, run.id)
    assert finalised.finalised is True
    # Runs are immutable — re-finalising (the only state change) is refused loudly.
    with pytest.raises(ConflictError):
        repo.finalise_scoring_run(alice.principal, run.id)
    # The content hash never changes across finalisation.
    assert repo.get_scoring_run(alice.principal, run.id).content_hash == run.content_hash


def test_consultant_sees_only_their_own_runs(
    repo: Repository, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    alice_run = _create(repo, alice)
    _create(repo, bob)
    assert [r.id for r in repo.list_scoring_runs(alice.principal)] == [alice_run.id]
    # Bob cannot read Alice's run — not by get, not by record fetch.
    with pytest.raises(ScopeViolationError):
        repo.get_scoring_run(bob.principal, alice_run.id)
    with pytest.raises(ScopeViolationError):
        repo.get_scoring_run_record(bob.principal, alice_run.id)


def test_missing_run_raises_not_found(repo: Repository, alice: SeededConsultant) -> None:
    with pytest.raises(NotFoundError):
        repo.get_scoring_run(alice.principal, uuid.uuid4())


def test_admin_can_read_any_run(
    repo: Repository, alice: SeededConsultant, admin: SeededConsultant
) -> None:
    run = _create(repo, alice)
    assert repo.get_scoring_run(admin.principal, run.id).id == run.id
