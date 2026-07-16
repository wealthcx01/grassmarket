"""GRS-0084 — C benchmark ingestion + peer comparison (ADR-0023).

The C benchmark is a NAMED public-app peer set, approval-gated (ADR-0009): ingestion only PROPOSES a
row; a consultant records the sign-off that makes it live. These tests pin the fail-loud ingestion,
the approval gate, the repository read (shared org-wide reference), and the peer comparison. No real
review data is committed — synthetic ratings exercise the machinery."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from bcap_contracts.assessments import SubcomponentRating
from bcap_contracts.common import EvidenceGrade, MaturityLevel
from bcap_contracts.predictions import CBenchmarkRow
from bcap_contracts.registry import load_registry
from pydantic import ValidationError

from grassmarket.atlas.c_benchmark import (
    C_BENCHMARK_PEER_ROSTER,
    c_benchmark_proposal,
    c_peer_comparison,
)
from grassmarket.atlas.draft_coefficients import draft_v1_coefficient_set
from grassmarket.data.repository import NotFoundError

_NOW = datetime(2026, 7, 16, 12, 0, tzinfo=UTC)


def _all_c_ratings(registry, level=MaturityLevel.ADVANCED) -> tuple[SubcomponentRating, ...]:
    """Every C subcomponent rated `level` (E3) — full C coverage for a peer."""
    return tuple(
        SubcomponentRating(
            module_key=m.key,
            subcomponent_key=s.key,
            level=level,
            evidence_grade=EvidenceGrade.E3_ARTIFACT,
        )
        for m in registry.c_modules
        for s in m.subcomponents
    )


def _proposal(registry, peer_name="Saxo", level=MaturityLevel.ADVANCED):
    coeffs = draft_v1_coefficient_set(registry, score_c=True)
    return c_benchmark_proposal(
        peer_name,
        "retail",
        _all_c_ratings(registry, level),
        coeffs,
        registry,
        source_ref="review:saxo",
    )


# --- Ingestion (fail-loud) ---------------------------------------------------------------


def test_ingestion_scores_a_peer_into_a_proposal() -> None:
    registry = load_registry()
    proposal = _proposal(registry)
    assert proposal.peer_name == "Saxo"
    assert 0.0 <= proposal.c_index <= 1.0
    assert set(proposal.module_scores) == registry.c_module_keys()  # per-module q_m for all 10
    assert proposal.source_ref == "review:saxo"


def test_ingestion_of_incomplete_c_coverage_fails_loud() -> None:
    registry = load_registry()
    coeffs = draft_v1_coefficient_set(registry, score_c=True)
    partial = _all_c_ratings(registry)[:-1]  # drop one C subcomponent
    with pytest.raises(ValueError, match="c_subcomponent"):
        c_benchmark_proposal("Saxo", "retail", partial, coeffs, registry)


def test_roster_lists_the_seven_public_peers() -> None:
    assert len(C_BENCHMARK_PEER_ROSTER) == 7
    assert "Saxo" in C_BENCHMARK_PEER_ROSTER and "Revolut" in C_BENCHMARK_PEER_ROSTER


# --- Approval gate (ADR-0009) ------------------------------------------------------------


def test_proposed_row_is_not_live_until_approved(repo, alice) -> None:
    registry = load_registry()
    p = _proposal(registry)
    row = repo.propose_c_benchmark_row(
        alice.principal,
        peer_name=p.peer_name,
        profile_key=p.profile_key,
        c_index=p.c_index,
        module_scores=p.module_scores,
        methodology_version=p.methodology_version,
        coefficient_version=p.coefficient_version,
        source_ref=p.source_ref,
        now=_NOW,
    )
    assert row.approved is False
    # Not in the live (approved-only) set yet; visible only when pending proposals are included.
    assert repo.list_c_benchmark_rows(approved_only=True) == []
    assert [r.id for r in repo.list_c_benchmark_rows(approved_only=False)] == [row.id]

    approved = repo.approve_c_benchmark_row(alice.principal, row.id, now=_NOW)
    assert approved.approved is True
    assert approved.approved_by == alice.principal.consultant_id
    assert approved.approved_at == _NOW
    assert [r.id for r in repo.list_c_benchmark_rows(approved_only=True)] == [row.id]


def test_approving_a_missing_row_fails_loud(repo, alice) -> None:
    from uuid import uuid4

    with pytest.raises(NotFoundError):
        repo.approve_c_benchmark_row(alice.principal, uuid4(), now=_NOW)


def test_the_row_contract_requires_a_recorded_approval() -> None:
    # approved=True with no approver/timestamp is refused (ADR-0009 recorded-approval invariant).
    with pytest.raises(ValidationError, match="approved"):
        CBenchmarkRow(
            id=__import__("uuid").uuid4(),
            peer_name="Saxo",
            profile_key="retail",
            c_index=0.5,
            methodology_version="1.1",
            coefficient_version="v1",
            approved=True,
            ingested_at=_NOW,
        )


# --- Read scoping + peer comparison ------------------------------------------------------


def test_the_peer_set_is_a_shared_org_wide_reference(repo, alice, bob) -> None:
    registry = load_registry()
    p = _proposal(registry)
    row = repo.propose_c_benchmark_row(
        alice.principal,
        peer_name=p.peer_name,
        profile_key=p.profile_key,
        c_index=p.c_index,
        module_scores=p.module_scores,
        methodology_version=p.methodology_version,
        coefficient_version=p.coefficient_version,
        source_ref=p.source_ref,
        now=_NOW,
    )
    repo.approve_c_benchmark_row(alice.principal, row.id, now=_NOW)
    # Peers are public reference data — bob (a different consultant) sees the same approved set.
    assert [r.id for r in repo.list_c_benchmark_rows(approved_only=True)] == [row.id]
    retail_only = repo.list_c_benchmark_rows(approved_only=True, profile_key="retail")
    assert [r.id for r in retail_only] == [row.id]
    assert repo.list_c_benchmark_rows(approved_only=True, profile_key="exchange") == []


def test_peer_comparison_positions_the_subject() -> None:
    cmp = c_peer_comparison(0.62, [0.40, 0.55, 0.70, 0.80])
    assert cmp.peer_count == 4
    assert cmp.ahead_of == 2  # beats 0.40 and 0.55
    assert cmp.percentile == 0.5
    # No peers → percentile is a first-class None, never a fabricated 0.
    assert c_peer_comparison(0.5, []).percentile is None
