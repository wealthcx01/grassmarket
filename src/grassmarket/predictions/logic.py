"""Prediction extraction + scoring (GRS-0031). Pure, deterministic.

`predictions_from_levers` turns a value bridge's levers into prediction specs at finalisation;
`score_prediction` grades a realised outcome — a directional hit/miss and a Brier score for the
probabilistic claim. Money stays Money throughout (ADR-0002); no Score/currency mixing.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from bcap_contracts.money import Money
from bcap_contracts.predictions import PredictionOutcome
from bcap_contracts.value import LeverKind, LeverValuation


@dataclass(frozen=True)
class PredictionSpec:
    """One lever's prediction, before it is persisted against a scoring run."""

    lever: LeverKind
    predicted_delta: Money


def predictions_from_levers(levers: Sequence[LeverValuation]) -> tuple[PredictionSpec, ...]:
    """Extract one prediction per lever: the lever, and its NPV as the predicted value impact.
    Deterministic and order-preserving — a roadmap's levers become its predictions."""
    return tuple(PredictionSpec(lever=v.lever, predicted_delta=v.npv) for v in levers)


def _sign(minor: int) -> int:
    return (minor > 0) - (minor < 0)


def score_prediction(
    *, predicted_delta: Money, realised_delta: Money, probability: float
) -> tuple[PredictionOutcome, float]:
    """Grade a prediction against its realised value.

    Directional: a HIT iff the realised value moved in the SAME (non-zero) direction as predicted —
    a predicted gain realised as a gain, a predicted reduction realised as a reduction. Brier score:
    ``(probability − outcome)²`` where outcome is 1 for a hit, 0 for a miss — the model's confidence
    is rewarded when it was right and penalised when wrong. Cross-currency is refused (no FX)."""
    if realised_delta.currency is not predicted_delta.currency:
        raise ValueError(
            f"Refusing to score a {realised_delta.currency.value} realised value against a "
            f"{predicted_delta.currency.value} prediction: no silent FX."
        )
    predicted_sign = _sign(predicted_delta.amount_minor)
    hit = predicted_sign != 0 and _sign(realised_delta.amount_minor) == predicted_sign
    brier = (probability - (1.0 if hit else 0.0)) ** 2
    return (PredictionOutcome.HIT if hit else PredictionOutcome.MISS, brier)
