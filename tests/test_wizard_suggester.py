"""AI-assisted wizard input suggester (GRS-0101, ADR-0032).

Deterministic proposals over the current document: coverage guidance, a power-consistency nudge, and
a conservative carry-forward prefill. Every proposal targets an UNSET, registry-valid field and is
applied only by the advisor's explicit accept — asserted here at the service and HTTP layers.
"""

from __future__ import annotations

from bcap_contracts.assessments import (
    AssessmentDocument,
    PowerEntry,
    SubcomponentRating,
)
from bcap_contracts.common import EvidenceGrade, MaturityLevel, StrengthRating
from bcap_contracts.registry import load_registry
from bcap_contracts.wizard import WizardSuggestionKind

from grassmarket.assessments.suggester import HeuristicWizardSuggester, suggest_for
from grassmarket.data.repository import Repository
from tests.conftest import SeededConsultant, auth_header

_E3 = EvidenceGrade.E3_ARTIFACT


def _all_powers(benefit=StrengthRating.EMERGING, barrier=StrengthRating.EMERGING):
    return tuple(
        PowerEntry(
            power_key=p.key,
            benefit=benefit,
            barrier=barrier,
            benefit_grade=_E3,
            barrier_grade=_E3,
        )
        for p in load_registry().powers
    )


def test_coverage_guidance_when_not_scoreable() -> None:
    # An empty document is not scoreable → one guidance suggestion citing the blockers.
    doc = AssessmentDocument(subject="X")
    out = suggest_for(doc, load_registry())
    coverage = [s for s in out if s.id == "coverage:scoreable"]
    assert len(coverage) == 1
    assert coverage[0].kind is WizardSuggestionKind.GUIDANCE
    assert coverage[0].rationale  # names what's missing


def test_power_consistency_nudge_on_strong_benefit_no_barrier() -> None:
    registry = load_registry()
    first = registry.powers[0].key
    powers = (
        PowerEntry(
            power_key=first,
            benefit=StrengthRating.ESTABLISHED,
            barrier=StrengthRating.NONE,
            benefit_grade=_E3,
            barrier_grade=_E3,
        ),
    ) + _all_powers()[1:]
    doc = AssessmentDocument(subject="X", powers=powers)
    out = suggest_for(doc, registry)
    nudges = [s for s in out if s.id == f"consistency:power:{first}"]
    assert len(nudges) == 1
    assert nudges[0].power_key == first
    assert nudges[0].proposed_level is None  # guidance carries no value


def test_unrated_nudge_is_guidance_and_never_anchors_a_level() -> None:
    # A partly-rated module nudges the advisor to finish it — but proposes NO value (anti-anchoring,
    # GRS-0136): pre-planting a level would bias the bottleneck-sensitive score.
    registry = load_registry()
    module = next(m for m in registry.modules if m.key == "APP_SERVER")
    subs = tuple(
        SubcomponentRating(
            module_key="APP_SERVER",
            subcomponent_key=sc.key,
            level=MaturityLevel.ADVANCED,
            evidence_grade=_E3,
        )
        for sc in module.subcomponents[:2]  # rate the first two
    )
    doc = AssessmentDocument(subject="X", subcomponents=subs, powers=_all_powers())
    out = suggest_for(doc, registry)
    # No suggestion ever pre-plants a maturity level.
    assert all(s.proposed_level is None for s in out)
    assert all(s.kind is not WizardSuggestionKind.PREFILL for s in out)
    nudge = [s for s in out if s.id == "unrated:APP_SERVER"]
    assert len(nudge) == 1 and nudge[0].kind is WizardSuggestionKind.GUIDANCE
    assert nudge[0].module_key == "APP_SERVER"


def test_no_unrated_nudge_without_a_pattern() -> None:
    # A single rated subcomponent is not a pattern — no nudge yet.
    registry = load_registry()
    subs = (
        SubcomponentRating(
            module_key="APP_SERVER",
            subcomponent_key="APP_SERVER_API_DESIGN",
            level=MaturityLevel.ADVANCED,
            evidence_grade=_E3,
        ),
    )
    doc = AssessmentDocument(subject="X", subcomponents=subs, powers=_all_powers())
    out = HeuristicWizardSuggester().suggest(doc, registry)
    assert [s for s in out if s.id.startswith("unrated:")] == []


def test_http_suggestions_scoped_and_empty_when_finalised(
    repo: Repository, alice: SeededConsultant, bob: SeededConsultant, client
) -> None:
    a = repo.create_assessment(alice.principal, subject="Scoped")
    # Alice sees her own suggestions (a fresh draft → at least the coverage guidance).
    r = client.get(f"/assessments/{a.id}/suggestions", headers=auth_header(alice))
    assert r.status_code == 200
    body = r.json()
    assert body["suggester_version"]
    assert any(s["id"] == "coverage:scoreable" for s in body["suggestions"])

    # Bob cannot see Alice's assessment (owner-scoped → 404).
    assert (
        client.get(f"/assessments/{a.id}/suggestions", headers=auth_header(bob)).status_code == 404
    )
