"""Academy-grounded Practice Arena scenarios (GRS-0130, ADR-0028).

The practice arena should rehearse the *real* motions the Academy teaches, not generic filler. These
scenarios are drawn from the Sales Egoist doctrine (GRS-0122) — each puts the advisor in a discovery
that exercises a specific weapon (Challenger teach, Demo, Total Account Awareness) against a real
7-Powers probe. They are seeded through the same admin path as any arena content.

Practice-arena feedback stays self-scoped and AI-labelled (`ArenaSession.feedback_is_ai_drafted`),
never an approval record — the deliberate #8 exception for self-only training content. Nothing here
changes that; these are just better-grounded scenarios.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from bcap_contracts.arena import ArenaPowerTarget


@dataclass(frozen=True)
class PracticeScenarioSpec:
    """The content of one Academy-grounded scenario (the owner/id are set at seed time)."""

    title: str
    brief: str
    client_persona: str
    target_powers: tuple[ArenaPowerTarget, ...]
    evidence_cues: tuple[str, ...] = field(default_factory=tuple)


def academy_practice_scenarios() -> list[PracticeScenarioSpec]:
    """The seeded Academy scenarios — each rehearses a Sales Egoist motion against a real power."""
    return [
        PracticeScenarioSpec(
            title="Sales Egoist: the Challenger teach (scale economies)",
            brief=(
                "Rehearse the Sales Egoist Challenger weapon: teach a mid-market broker something "
                "they under-price about their own moat. Use the Platform Power read to surface a "
                "thin scale-economies position, then take control and book the workshop — do not "
                "leave without the next step (the zero-sum pipeline)."
            ),
            client_persona=(
                "A confident retail-brokerage COO who believes their low prices are a durable "
                "advantage and has not considered whether the underlying cost base actually scales."
            ),
            target_powers=(
                ArenaPowerTarget(
                    power_key="SCALE_ECONOMIES",
                    benefit_cues=("unit cost falls with volume", "fixed cost spread over accounts"),
                    barrier_cues=("a sub-scale rival prices below cost", "buy share at a loss"),
                ),
            ),
            evidence_cues=("clearing and market-data cost base", "accounts and volume trend"),
        ),
        PracticeScenarioSpec(
            title="Sales Egoist: the Demo weapon (switching costs)",
            brief=(
                "Rehearse the Sales Egoist Demo weapon on a wealth manager: run a scoped "
                "switching-cost read live and let the client watch their own lock-in get measured. "
                "Build Total Account Awareness — the whole buying unit, not just the contact — and "
                "qualify honestly on whether the switching moat is real or assumed."
            ),
            client_persona=(
                "A wealth-management founder who assumes clients stay out of loyalty and has never "
                "quantified the friction of an in-specie transfer or an unrealised CGT position."
            ),
            target_powers=(
                ArenaPowerTarget(
                    power_key="SWITCHING_COSTS",
                    benefit_cues=(
                        "what a client forgoes by leaving",
                        "in-specie transfer friction",
                    ),
                    barrier_cues=(
                        "rivals must compensate for the pain of switching",
                        "CGT lock-in",
                    ),
                ),
            ),
            evidence_cues=("actual churn and transfer-out times", "linked-account depth"),
        ),
    ]
