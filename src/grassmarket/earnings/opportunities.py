"""Sell-from-report opportunities (GRS-0162, ADR-0039) — "what do I sell against this report?"

A deterministic join, no AI: re-score the finalised document with the active coefficient seams
(the same paths the portfolio's V and C columns use), then match each product's authored fit
(`product_fit.yaml`) against the targets that are **assessed and weak**:

- a V/C module is a gap iff assessed and its gate band is Basic/Developing (or gate-blocked);
- a power is a gap iff assessed and its benefit or barrier is None/Emerging;
- **Not Assessed is never a gap** (D9) — it is reported separately, never a reason to sell.

Ranking is score-track only (ADR-0002): products with module gaps first, deepest addressed gap
(min q_m) first; power-only products after, weakest strength first. The live commission carrot
(GRS-0123) is displayed alongside and never enters the ordering. Advisor-facing only — this
output never reaches a client deliverable.
"""

from __future__ import annotations

from bcap_contracts.assessments import Assessment
from bcap_contracts.commissions import load_commission_config
from bcap_contracts.common import MaturityLevel, StrengthRating
from bcap_contracts.product_fit import (
    GapKind,
    OpportunityGap,
    SellOpportunities,
    SellOpportunity,
    load_product_fit,
)
from bcap_contracts.registry import load_registry

from grassmarket.assessments.service import c_result_of, deterministic_result
from grassmarket.atlas.active import profile_key_of, profile_scoring_context
from grassmarket.earnings.product_carrot import product_commission_carrot

# The maturity bands that read as a sellable gap (ADR-0039): Basic/Developing, or a blocked gate.
_WEAK_BANDS = frozenset({MaturityLevel.BASIC, MaturityLevel.DEVELOPING})
# The power strengths that read as a gap: no power, or one still emerging.
_WEAK_STRENGTHS = frozenset({StrengthRating.NONE, StrengthRating.EMERGING})
# Ordinal position for power-gap severity ordering (weakest first). Never arithmetic on ratings —
# a sort position only (ADR-0002 keeps ordinals out of equations, not out of ordering).
_STRENGTH_ORDER = {
    StrengthRating.NONE: 0,
    StrengthRating.EMERGING: 1,
    StrengthRating.ESTABLISHED: 2,
    StrengthRating.WIDE: 3,
}


def _module_gap(kind: GapKind, key: str, name: str, module) -> OpportunityGap | None:
    """An assessed module's gap, or None when it is strong. Caller has excluded unassessed."""
    if module.gate_blocked or MaturityLevel(module.gate_band) in _WEAK_BANDS:
        return OpportunityGap(
            kind=kind,
            key=key,
            name=name,
            q_m=module.q_m,
            gate_band=MaturityLevel(module.gate_band),
        )
    return None


def _gap_sort_key(gap: OpportunityGap) -> tuple:
    """Within one product: module gaps (deepest q_m first) before power gaps (weakest first)."""
    if gap.kind is GapKind.POWER:
        weakest = min(
            _STRENGTH_ORDER[gap.benefit] if gap.benefit is not None else len(_STRENGTH_ORDER),
            _STRENGTH_ORDER[gap.barrier] if gap.barrier is not None else len(_STRENGTH_ORDER),
        )
        return (1, weakest, gap.key)
    # A gate-blocked module can carry q_m None — deepest-unknown sorts after known-deep gaps.
    return (0, gap.q_m if gap.q_m is not None else 1.0, gap.key)


def _product_sort_key(opportunity: SellOpportunity) -> tuple:
    """Across products (ADR-0039): module-gap products by min addressed q_m ascending, then
    power-only products by weakest addressed strength. Commission NEVER enters (ADR-0002)."""
    module_qms = [g.q_m for g in opportunity.gaps if g.kind is not GapKind.POWER]
    if module_qms:
        known = [q for q in module_qms if q is not None]
        return (0, min(known) if known else 1.0, opportunity.product_id)
    weakest = min(
        _STRENGTH_ORDER[s]
        for g in opportunity.gaps
        for s in (g.benefit, g.barrier)
        if s is not None
    )
    return (1, weakest, opportunity.product_id)


def sell_opportunities(assessment: Assessment) -> SellOpportunities:
    """The ranked "recommended to sell" list for a FINALISED assessment (caller enforces the
    state). Deterministic and reproducible: the stored document + the active profile coefficient
    seam + the versioned fit map fully determine the output."""
    document = assessment.document
    profile_key = profile_key_of(document)
    view, coefficients = profile_scoring_context(profile_key)
    result = deterministic_result(document, coefficients, view)
    modules_by_key = {m.key: m for m in result.modules}

    # C scores off the assessment's PROFILE VIEW — the same seam the portfolio's C column uses
    # (GRS-0169; the full-registry shortcut listed retail C modules as "not yet assessed" on
    # wealth/exchange reports, whose taxonomy doesn't contain them at all).
    c_result = c_result_of(document, view)
    c_by_key = {m.key: m for m in c_result.modules} if c_result is not None else {}
    view_c_keys = view.c_module_keys()

    registry = load_registry()  # powers are shared across profiles; names come from here
    powers_by_key = {p.power_key: p for p in document.powers}
    config = load_commission_config()
    fit_map = load_product_fit()

    opportunities: list[SellOpportunity] = []
    for product_id in sorted(fit_map.products):
        fit = fit_map.products[product_id]
        if profile_key not in fit.profiles:
            continue  # not sellable into this operating model (GRS-0169) — never recommended
        gaps: list[OpportunityGap] = []
        unassessed: list[str] = []

        for key in fit.modules:
            module = modules_by_key.get(key)
            if module is None:
                continue  # not in this operating model's view — not applicable, not "unassessed"
            if module.q_m is None:
                # q_m is None ⟺ ZERO assessed subcomponents (D9) — no data is never a gap, even
                # though a fully-unassessed module also gate-blocks. (A partially-assessed module
                # with a blocked gate has a q_m and is caught by the band/blocked rule below.)
                unassessed.append(module.name)
                continue
            gap = _module_gap(GapKind.MODULE, key, module.name, module)
            if gap is not None:
                gaps.append(gap)

        for key in fit.c_modules:
            if key not in view_c_keys:
                continue  # not in this operating model's C taxonomy — not applicable (GRS-0169)
            c_module = c_by_key.get(key)
            if c_module is None or c_module.q_m is None:  # same D9 rule as the V modules
                unassessed.append(view.require_c_module(key).name)
                continue
            gap = _module_gap(GapKind.C_MODULE, key, c_module.name, c_module)
            if gap is not None:
                gaps.append(gap)

        for key in fit.powers:
            power_name = registry.require_power(key).name
            entry = powers_by_key.get(key)
            if entry is None:
                unassessed.append(power_name)
                continue
            if entry.benefit in _WEAK_STRENGTHS or entry.barrier in _WEAK_STRENGTHS:
                gaps.append(
                    OpportunityGap(
                        kind=GapKind.POWER,
                        key=key,
                        name=power_name,
                        benefit=entry.benefit,
                        barrier=entry.barrier,
                    )
                )

        if not gaps:
            continue  # every addressed target is strong or unknown — nothing honest to sell

        opportunities.append(
            SellOpportunity(
                product_id=product_id,
                name=config.require_product(product_id).name,
                pitch=fit.pitch,
                gaps=tuple(sorted(gaps, key=_gap_sort_key)),
                not_yet_assessed=tuple(unassessed),
                carrot=product_commission_carrot(product_id, config),
            )
        )

    # Honest empty-state (GRS-0169): when NO catalogue product lists this profile, say so — the
    # advisor must never read "no recommendations" as "no weak areas".
    any_applicable = any(profile_key in f.profiles for f in fit_map.products.values())
    note = (
        None
        if any_applicable
        else (
            f"The represented-product catalogue doesn't cover the {profile_key} operating model "
            "yet, so no product is recommended for this report — this says nothing about the "
            "report's gaps."
        )
    )
    return SellOpportunities(
        assessment_id=assessment.id,
        subject=assessment.subject,
        opportunities=tuple(sorted(opportunities, key=_product_sort_key)),
        note=note,
        fit_version=fit_map.version,
        coefficient_version=coefficients.version,
        schedule_version=config.version,
    )
