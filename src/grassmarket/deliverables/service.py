"""Deliverable generation service (GRS-0015).

Ties a finalised scoring run to a rendered document. The point scores/triad come from the run's
**stored, immutable** AtlasResult; the uncertainty bands (with the ADR-0008 modelled flags) are
re-derived by re-running the Monte Carlo from the run's stored inputs with a fixed seed — so the
document is reproducible. The client-usable gate is enforced BEFORE anything is rendered.
"""

from __future__ import annotations

import random
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from bcap_contracts.assessments import CoefficientSet
from bcap_contracts.deliverables import DeliverableMode
from bcap_contracts.narratives import AINarrative
from bcap_contracts.registry import Registry
from bcap_contracts.uncertainty import UncertaintyModel

from grassmarket.atlas import AssessmentInputs, run_monte_carlo
from grassmarket.atlas.results import AtlasResult
from grassmarket.deliverables.builder import DeliverableContext, build_platform_power_report
from grassmarket.deliverables.gate import resolve_mode

# The same fixed seed the finalise path uses, so re-derived bands reproduce the finalised run.
DELIVERABLE_SEED = 20260706


@dataclass(frozen=True)
class RenderedDeliverable:
    mode: DeliverableMode
    docx_bytes: bytes


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
) -> RenderedDeliverable:
    """Render the Platform Power Report. Enforces the client-usable gate first (may raise
    `ClientUsabilityError`), then re-derives bands and builds the .docx. Any AI narratives are
    rendered into the methods appendix with their approval trail (GRS-0017)."""
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
    return RenderedDeliverable(
        mode=mode, docx_bytes=build_platform_power_report(context, mode, narratives)
    )
