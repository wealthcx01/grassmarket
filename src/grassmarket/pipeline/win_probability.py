"""Win-probability scorer (GRS-0111, PRD §4) — a deterministic, explainable estimate of how likely
a single prospect is to become a won deal.

It is *not* a black box: it starts from the prospect's stage close-probability (the strongest
signal — a Contracted deal is inherently likelier than a cold Prospect), nudges it by whether the
record carries the qualifying information a consultant would look for, and dampens it when the
prospect has gone stale. Every weight is configuration (``pipeline_config.yaml``), so calibration is
an edit, not a code change. The result is a *probability* percentage — never currency (ADR-0002).

Determinism: given the same prospect fields, staleness flag and config, the output is byte-stable —
no wall-clock read, no randomness. Staleness is passed in (computed once by the board), so this
module never touches ``datetime.now``.
"""

from __future__ import annotations

from bcap_contracts.entities import Prospect
from bcap_contracts.pipeline import PipelineConfig, WinProbability


def score_win_probability(
    prospect: Prospect, *, stale: bool, config: PipelineConfig
) -> WinProbability:
    """Score one prospect. ``stale`` is the board's time-in-stage staleness flag for this prospect.

    A *settled* stage (close-probability exactly 0.0 or 1.0 — a lost/closed deal, or a won one that
    is Active/Delivered) has a determined outcome: the base is returned verbatim with no signal
    adjustment, because completeness can't change a settled result. Every other stage is the base
    plus the completeness signals, clamped to [0, 1]."""
    base = config.params(prospect.stage).close_probability
    signals = config.win_probability.signals

    stage_name = prospect.stage.value.replace("_", " ").title()
    reasons: list[str] = [f"{stage_name} stage — {_pct(base)}% base"]
    missing: list[str] = []

    if base in (0.0, 1.0):
        # Settled outcome — a closed/lost deal (0.0) or a won, in-delivery one (1.0). Completeness
        # is irrelevant to an already-determined result, so no signals apply.
        note = "closed — no longer in pursuit" if base == 0.0 else "won — in delivery"
        reasons.append(f"Outcome settled ({note}).")
        return WinProbability(
            score=_pct(base),
            label=config.win_probability.band_for(base),
            reasons=tuple(reasons),
            missing_info=(),
        )

    adjusted = base
    # Each completeness signal: present → apply its weight and record why; absent → flag the gap so
    # the consultant knows exactly what would sharpen the estimate.
    for present, weight, present_reason, gap in (
        (
            bool(prospect.primary_contact_name),
            signals.has_primary_contact,
            "Primary contact on file",
            "No primary contact named",
        ),
        (
            bool(prospect.primary_contact_email),
            signals.has_contact_email,
            "Reachable contact email",
            "No contact email",
        ),
        (bool(prospect.sector), signals.has_sector, "Sector recorded", "No sector recorded"),
        (
            bool(prospect.notes),
            signals.has_notes,
            "Qualifying notes captured",
            "No qualifying notes",
        ),
    ):
        if present:
            adjusted += weight
            reasons.append(f"{present_reason} (+{_pct(weight)}pp)")
        else:
            missing.append(gap)

    if stale:
        adjusted += signals.stale_penalty
        reasons.append(f"Stale in stage ({_pct(signals.stale_penalty)}pp)")

    adjusted = max(0.0, min(1.0, adjusted))
    return WinProbability(
        score=_pct(adjusted),
        label=config.win_probability.band_for(adjusted),
        reasons=tuple(reasons),
        missing_info=tuple(missing),
    )


def _pct(probability: float) -> int:
    """Probability (0–1, may be negative for a penalty) → signed whole-number percentage points."""
    return round(probability * 100)
