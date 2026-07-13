"""Deliverable generation service (GRS-0015).

Ties a finalised scoring run to a rendered document. The point scores/triad come from the run's
**stored, immutable** AtlasResult; the uncertainty bands (with the ADR-0008 modelled flags) are
re-derived by re-running the Monte Carlo from the run's stored inputs with a fixed seed — so the
document is reproducible. The client-usable gate is enforced BEFORE anything is rendered.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date

from bcap_contracts.assessments import CoefficientSet
from bcap_contracts.deliverables import DeliverableMode, DeliverableType
from bcap_contracts.registry import Registry
from bcap_contracts.uncertainty import UncertaintyModel
from bcap_contracts.value import ScenarioResult, ValueBridge

from grassmarket.atlas import AssessmentInputs, run_monte_carlo
from grassmarket.atlas.results import AtlasResult
from grassmarket.deliverables.builder import DeliverableContext, build_platform_power_report
from grassmarket.deliverables.gate import resolve_mode
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

# The single-run Diagnostic-pack documents — each builds from one finalised run's context.
# MODERNISATION_ROADMAP (needs the value bridge) and SCORE_EVOLUTION (needs multiple runs) have
# their own render paths and are deliberately absent here.
_SINGLE_RUN_BUILDERS = {
    DeliverableType.EXECUTIVE_SUMMARY: build_executive_summary,
    DeliverableType.PLATFORM_POWER_REPORT: build_platform_power_report,
    DeliverableType.INFRASTRUCTURE_HEATMAP: build_infrastructure_heatmap,
    DeliverableType.TECHNICAL_APPENDIX: build_technical_appendix,
    DeliverableType.WORKSHOP_OUTPUT: build_workshop_output,
}

# The same fixed seed the finalise path uses, so re-derived bands reproduce the finalised run.
DELIVERABLE_SEED = 20260706


class UnsupportedDeliverableTypeError(ValueError):
    """The requested deliverable type is not a single-run document — it has its own render path
    (the roadmap needs the value bridge; score evolution needs multiple runs). A `ValueError`
    subclass so callers may catch it specifically without a broad `except ValueError`."""


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
) -> RenderedDeliverable:
    """Render one single-run Diagnostic-pack document. Enforces the client-usable gate first (may
    raise `ClientUsabilityError`), then re-derives the uncertainty bands from the stored inputs
    (fixed seed → reproducible) and dispatches to the builder for the requested type.

    A type that is not a single-run document (the roadmap, which needs the value bridge; score
    evolution, which needs multiple runs) is refused loud — those have their own render paths."""
    if deliverable_type not in _SINGLE_RUN_BUILDERS:
        raise UnsupportedDeliverableTypeError(
            f"{deliverable_type.value} is not a single-run diagnostic document; it has its own "
            f"render path (roadmap needs the value bridge; score evolution needs multiple runs)."
        )
    mode = resolve_mode(coefficients, client_facing=client_facing)  # the gate — refuses first
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
    )
    builder = _SINGLE_RUN_BUILDERS[deliverable_type]
    return RenderedDeliverable(mode=mode, docx_bytes=builder(context, mode))


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
) -> RenderedDeliverable:
    """Render the Platform Power Report (a thin wrapper over `render_diagnostic_document`)."""
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
) -> RenderedDeliverable:
    """Render the Modernisation Roadmap. Enforces the client-usable gate first (may raise
    `ClientUsabilityError`) — a draft coefficient set yields only a watermarked internal document,
    never a client pack — then builds the .docx from the upstream value-bridge + priority objects.
    Versions come from the run's immutable stored result, so the document is reproducible."""
    mode = resolve_mode(coefficients, client_facing=client_facing)  # the gate — refuses first
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
