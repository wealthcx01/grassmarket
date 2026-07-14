"""Deliverable generation service (GRS-0015).

Ties a finalised scoring run to a rendered document. The point scores/triad come from the run's
**stored, immutable** AtlasResult; the uncertainty bands (with the ADR-0008 modelled flags) are
re-derived by re-running the Monte Carlo from the run's stored inputs with a fixed seed — so the
document is reproducible. The client-usable gate is enforced BEFORE anything is rendered.
"""

from __future__ import annotations

import random
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date

from bcap_contracts.assessments import CoefficientSet
from bcap_contracts.committee import CommitteeDecision
from bcap_contracts.deliverables import DeliverableMode, DeliverableType
from bcap_contracts.narratives import AINarrative
from bcap_contracts.registry import Registry
from bcap_contracts.uncertainty import UncertaintyModel
from bcap_contracts.value import ScenarioResult, ValueBridge

from grassmarket.atlas import AssessmentInputs, run_monte_carlo
from grassmarket.atlas.results import AtlasResult
from grassmarket.deliverables.builder import DeliverableContext, build_platform_power_report
from grassmarket.deliverables.gate import (
    assert_committee_approved,
    assert_uncertainty_client_usable,
    resolve_mode,
)
from grassmarket.deliverables.heatmap import build_infrastructure_heatmap
from grassmarket.deliverables.reports import (
    build_executive_summary,
    build_technical_appendix,
    build_workshop_output,
)
from grassmarket.deliverables.roadmap import (
    RoadmapContext,
    RoadmapEntry,
    build_modernisation_roadmap,
)


class UnsupportedDeliverableTypeError(ValueError):
    """The requested deliverable type is not a single-run document — it has its own render path
    (the roadmap needs the value bridge; score evolution needs multiple runs). A `ValueError`
    subclass so callers may catch it specifically without a broad `except ValueError`."""


@dataclass(frozen=True)
class _SingleRunSpec:
    # Every single-run builder takes the same shape; only the Platform Power Report renders the AI
    # narratives (GRS-0017) into its methods appendix — the others accept and ignore them, so the
    # dispatcher can pass narratives uniformly.
    build: Callable[[DeliverableContext, DeliverableMode, Sequence[AINarrative]], bytes]
    title: str


# THE single source of truth for the single-run Diagnostic-pack documents: builder AND display
# title in one place, so a new type can never render fine then 500 on a missing title lookup.
# MODERNISATION_ROADMAP (needs the value bridge) and SCORE_EVOLUTION (needs multiple runs) have
# their own render paths and are deliberately absent here.
_SINGLE_RUN_BUILDERS: dict[DeliverableType, _SingleRunSpec] = {
    DeliverableType.EXECUTIVE_SUMMARY: _SingleRunSpec(build_executive_summary, "Executive Summary"),
    DeliverableType.PLATFORM_POWER_REPORT: _SingleRunSpec(
        build_platform_power_report, "Platform Power Report"
    ),
    DeliverableType.INFRASTRUCTURE_HEATMAP: _SingleRunSpec(
        build_infrastructure_heatmap, "Infrastructure Heatmap"
    ),
    DeliverableType.TECHNICAL_APPENDIX: _SingleRunSpec(
        build_technical_appendix, "Technical Appendix"
    ),
    DeliverableType.WORKSHOP_OUTPUT: _SingleRunSpec(build_workshop_output, "Workshop Output"),
}

# The same fixed seed the finalise path uses, so re-derived bands reproduce the finalised run.
DELIVERABLE_SEED = 20260706


def title_for(deliverable_type: DeliverableType) -> str:
    """The display title for a single-run type. Refuses a non-single-run type loud (same registry
    the builder is looked up from — no drift, no request-time 500)."""
    if deliverable_type not in _SINGLE_RUN_BUILDERS:
        raise UnsupportedDeliverableTypeError(
            f"{deliverable_type.value} is not a single-run diagnostic document."
        )
    return _SINGLE_RUN_BUILDERS[deliverable_type].title


@dataclass(frozen=True)
class RenderedDeliverable:
    mode: DeliverableMode
    docx_bytes: bytes


def render_diagnostic_document(
    *,
    deliverable_type: DeliverableType,
    inputs: AssessmentInputs,
    stored_result: AtlasResult,
    coefficients: CoefficientSet,
    registry: Registry,
    model: UncertaintyModel,
    subject: str,
    generated_on: date,
    client_facing: bool,
    narratives: Sequence[AINarrative] = (),
    committee_decisions: Sequence[CommitteeDecision] = (),
) -> RenderedDeliverable:
    """Render one single-run Diagnostic-pack document. Enforces the client-usable AND committee
    gates first (may raise `ClientUsabilityError` / `CommitteePendingError`), then re-derives the
    uncertainty bands from the stored inputs (fixed seed → reproducible) and dispatches to the
    builder. Approved AI narratives and committee rationale/dissent render into the Platform Power
    Report's methods appendix (GRS-0017/0021); other types accept and ignore the narratives.

    A type that is not a single-run document (the roadmap, which needs the value bridge; score
    evolution, which needs multiple runs) is refused loud — those have their own render paths."""
    if deliverable_type not in _SINGLE_RUN_BUILDERS:
        raise UnsupportedDeliverableTypeError(
            f"{deliverable_type.value} is not a single-run diagnostic document; it has its own "
            f"render path (roadmap needs the value bridge; score evolution needs multiple runs)."
        )
    mode = resolve_mode(coefficients, client_facing=client_facing)  # the gate — refuses first
    # The §7 twin: a client pack's ranges must come from elicited widths, not draft placeholders.
    assert_uncertainty_client_usable(model, client_facing=client_facing)
    # High-stakes ratings need committee sign-off before a client pack (Methodology §8).
    assert_committee_approved(stored_result, committee_decisions, client_facing=client_facing)
    uncertainty = run_monte_carlo(
        inputs, coefficients, registry, model, random.Random(DELIVERABLE_SEED)
    )
    context = DeliverableContext(
        subject=subject,
        result=stored_result,
        uncertainty=uncertainty,
        coefficients=coefficients,
        uncertainty_version=model.version,
        generated_on=generated_on,
        committee_decisions=tuple(committee_decisions),
    )
    build = _SINGLE_RUN_BUILDERS[deliverable_type].build
    return RenderedDeliverable(mode=mode, docx_bytes=build(context, mode, narratives))


def render_platform_power_report(
    *,
    inputs: AssessmentInputs,
    stored_result: AtlasResult,
    coefficients: CoefficientSet,
    registry: Registry,
    model: UncertaintyModel,
    subject: str,
    generated_on: date,
    client_facing: bool,
    narratives: Sequence[AINarrative] = (),
    committee_decisions: Sequence[CommitteeDecision] = (),
) -> RenderedDeliverable:
    """Render the Platform Power Report (a thin wrapper over `render_diagnostic_document`). Approved
    AI narratives and the committee-approved triad rationale render into its methods appendix."""
    return render_diagnostic_document(
        deliverable_type=DeliverableType.PLATFORM_POWER_REPORT,
        inputs=inputs,
        stored_result=stored_result,
        coefficients=coefficients,
        registry=registry,
        model=model,
        subject=subject,
        generated_on=generated_on,
        client_facing=client_facing,
        narratives=narratives,
        committee_decisions=committee_decisions,
    )


def render_modernisation_roadmap(
    *,
    stored_result: AtlasResult,
    coefficients: CoefficientSet,
    bridge: ValueBridge,
    entries: tuple[RoadmapEntry, ...],
    scenarios: tuple[ScenarioResult, ...],
    uncertainty_version: str,
    subject: str,
    generated_on: date,
    client_facing: bool,
    committee_decisions: Sequence[CommitteeDecision] = (),
) -> RenderedDeliverable:
    """Render the Modernisation Roadmap. Enforces the client-usable AND committee gates first (may
    raise `ClientUsabilityError` / `CommitteePendingError`) — a draft coefficient set or an
    unsigned-off high-stakes rating yields only a watermarked internal document, never a client pack
    — then builds the .docx from the upstream value-bridge + priority objects. Versions come from
    run's immutable stored result, so the document is reproducible."""
    mode = resolve_mode(coefficients, client_facing=client_facing)  # the gate — refuses first
    assert_committee_approved(stored_result, committee_decisions, client_facing=client_facing)
    context = RoadmapContext(
        subject=subject,
        bridge=bridge,
        entries=entries,
        scenarios=scenarios,
        engine_version=stored_result.engine_version,
        methodology_version=stored_result.methodology_version,
        coefficient_version=stored_result.coefficient_version,
        uncertainty_version=uncertainty_version,
        generated_on=generated_on,
    )
    return RenderedDeliverable(mode=mode, docx_bytes=build_modernisation_roadmap(context, mode))
