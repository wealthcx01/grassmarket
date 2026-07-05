"""Shared assessment-input builders for the value-layer tests (underscore-prefixed so pytest does
not collect it as a test module)."""

from __future__ import annotations

import json
from pathlib import Path

from bcap_contracts.assessments import SubcomponentRating
from bcap_contracts.common import EvidenceGrade, MaturityLevel, NonScoreState, StrengthRating
from bcap_contracts.registry import Registry

from grassmarket.atlas import AssessmentInputs, MetricObservation, PowerObservation

_FIXTURE = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "golden_master.json"
_E3 = EvidenceGrade.E3_ARTIFACT


def uniform_inputs(
    registry: Registry,
    *,
    level: MaturityLevel = MaturityLevel.DEVELOPING,
    evidence: EvidenceGrade = _E3,
    overrides: dict[str, tuple[MaturityLevel, EvidenceGrade]] | None = None,
) -> AssessmentInputs:
    """Every subcomponent at ``level`` (E3), metrics at their mid anchor, powers (Emerging,
    Emerging), with per-subcomponent (level, evidence) overrides applied."""
    overrides = overrides or {}
    subs = []
    for module in registry.modules:
        for sub in module.subcomponents:
            lvl, ev = overrides.get(sub.key, (level, evidence))
            subs.append(
                SubcomponentRating(
                    module_key=module.key,
                    subcomponent_key=sub.key,
                    level=lvl,
                    evidence_grade=ev,
                )
            )
    metrics = [
        MetricObservation(metric_key=m.key, raw=float(m.normalisation.anchors[1].raw))
        for m in registry.metrics
    ]
    powers = [
        PowerObservation(
            power_key=p.key, benefit=StrengthRating.EMERGING, barrier=StrengthRating.EMERGING
        )
        for p in registry.powers
    ]
    return AssessmentInputs(subcomponents=tuple(subs), metrics=tuple(metrics), powers=tuple(powers))


def meridian_inputs() -> AssessmentInputs:
    """The ratified Meridian assessment, reconstructed from the golden-master fixture."""
    gm = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    subs = [
        SubcomponentRating(
            module_key=m["key"], subcomponent_key=s["key"], state=NonScoreState(s["state"])
        )
        if s["state"]
        else SubcomponentRating(
            module_key=m["key"],
            subcomponent_key=s["key"],
            level=MaturityLevel(s["level"]),
            evidence_grade=EvidenceGrade(s["evidence"]),
        )
        for m in gm["modules"]
        for s in m["subcomponents"]
    ]
    metrics = [
        MetricObservation(
            metric_key=r["key"],
            raw=None if r["state"] else r["raw"],
            state=NonScoreState(r["state"]) if r["state"] else None,
        )
        for r in gm["business"]["metrics"]
    ]
    powers = [
        PowerObservation(
            power_key=p["key"],
            benefit=StrengthRating(p["benefit"]),
            barrier=StrengthRating(p["barrier"]),
        )
        for p in gm["powers"]["powers"]
    ]
    return AssessmentInputs(subcomponents=tuple(subs), metrics=tuple(metrics), powers=tuple(powers))


def override(
    inputs: AssessmentInputs, key: str, level: MaturityLevel, evidence: EvidenceGrade = _E3
) -> AssessmentInputs:
    """A copy of ``inputs`` with a single subcomponent set to (level, evidence)."""
    new_subs = []
    for r in inputs.subcomponents:
        if r.subcomponent_key == key:
            new_subs.append(
                SubcomponentRating(
                    module_key=r.module_key,
                    subcomponent_key=key,
                    level=level,
                    evidence_grade=evidence,
                )
            )
        else:
            new_subs.append(r)
    return AssessmentInputs(
        subcomponents=tuple(new_subs), metrics=inputs.metrics, powers=inputs.powers
    )
