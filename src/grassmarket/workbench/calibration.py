"""Inter-rater reliability statistics for calibration sessions (GRS-0022, Methodology §9).

Pure, deterministic functions — the golden-master discipline that governs the ATLAS engine applies
here too: κ_w and AC1 reproduce hand-computed fixtures exactly. Two chance-corrected agreement
coefficients, computed per anchor over the assessors who rated the shared vignettes:

- **Weighted Cohen's kappa** (quadratic ordinal weights) — the target metric (κ_w ≥ 0.75). For more
  than two raters it is the mean of the pairwise coefficients (Landis-Koch conventions).
- **Gwet's AC1** — reported alongside because it is robust to the prevalence/skew that inflates or
  deflates kappa when n is small (the calibration reality).

Fail-loud throughout (CLAUDE.md #3): fewer than two raters or fewer than one subject, ragged data
(raters who did not all rate every vignette), or an out-of-range category is a refusal — never a
silently-defaulted or fabricated coefficient.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from itertools import combinations

from bcap_contracts.calibration import (
    AnchorAgreement,
    CalibrationRating,
    CalibrationResult,
    CalibrationSession,
)
from bcap_contracts.common import MaturityLevel

_NUM_MATURITY_CATEGORIES = len(MaturityLevel)

# κ < 0.6 anchors are rewritten (Methodology §9). Kept here so the flag and the docs never drift.
KAPPA_REWRITE_THRESHOLD = 0.6
KAPPA_TARGET = 0.75


class CalibrationStatsError(ValueError):
    """Bad input to a calibration statistic — refused, never scored around."""


def _validate(by_subject: Sequence[Sequence[int]], num_categories: int) -> None:
    if num_categories < 2:
        raise CalibrationStatsError("At least two rating categories are required.")
    if not by_subject:
        raise CalibrationStatsError("At least one rated subject (vignette) is required.")
    rater_counts = {len(s) for s in by_subject}
    if rater_counts == {0} or 0 in rater_counts:
        raise CalibrationStatsError("Every subject must be rated by at least one rater.")
    if len(rater_counts) != 1:
        raise CalibrationStatsError(
            "Ragged calibration data: every rater must rate every vignette for an anchor "
            f"(subject rater-counts were {sorted(rater_counts)}). Balanced data is required."
        )
    n_raters = rater_counts.pop()
    if n_raters < 2:
        raise CalibrationStatsError("At least two raters are required to measure agreement.")
    for subject in by_subject:
        for category in subject:
            if not 0 <= category < num_categories:
                raise CalibrationStatsError(
                    f"Category {category} is outside the {num_categories}-category scale."
                )


def _quadratic_weight(i: int, j: int, num_categories: int) -> float:
    """Agreement weight (1 on the diagonal, decreasing with ordinal distance) — quadratic."""
    return 1.0 - ((i - j) / (num_categories - 1)) ** 2


def _clamp(coefficient: float) -> float:
    """A chance-corrected coefficient is mathematically in [-1, 1]; floating-point accumulation can
    land a hair outside (e.g. -1.0000000000000022). Clamp that noise so the value always satisfies
    its contract bound. A GROSS excursion is a logic error, not float noise — fail loud (#3), never
    silently map a bogus 5.0 to 1.0."""
    if not -1.0 - 1e-9 <= coefficient <= 1.0 + 1e-9:
        raise CalibrationStatsError(
            f"Coefficient {coefficient} is grossly outside [-1, 1] — a computation error, not "
            f"floating-point noise."
        )
    return max(-1.0, min(1.0, coefficient))


def cohen_weighted_kappa(
    rater_a: Sequence[int], rater_b: Sequence[int], num_categories: int
) -> float:
    """Cohen's weighted kappa (quadratic weights) between two raters over the shared subjects.

    Degenerate case: when expected agreement is already perfect (both raters always used the same
    single category), kappa is undefined (0/0); by convention it is 1.0 iff observed agreement is
    also perfect, else 0.0. Stated openly, never silently NaN."""
    if len(rater_a) != len(rater_b):
        raise CalibrationStatsError("Paired raters must rate the same number of subjects.")
    n = len(rater_a)
    if n == 0:
        raise CalibrationStatsError("At least one subject is required.")

    observed = [[0.0] * num_categories for _ in range(num_categories)]
    for a, b in zip(rater_a, rater_b, strict=True):
        observed[a][b] += 1.0 / n
    marg_a = [sum(observed[i][j] for j in range(num_categories)) for i in range(num_categories)]
    marg_b = [sum(observed[i][j] for i in range(num_categories)) for j in range(num_categories)]

    p_o = 0.0
    p_e = 0.0
    for i in range(num_categories):
        for j in range(num_categories):
            w = _quadratic_weight(i, j, num_categories)
            p_o += w * observed[i][j]
            p_e += w * marg_a[i] * marg_b[j]

    if abs(1.0 - p_e) < 1e-12:
        return 1.0 if abs(1.0 - p_o) < 1e-12 else 0.0
    return _clamp((p_o - p_e) / (1.0 - p_e))


def weighted_kappa(by_subject: Sequence[Sequence[int]], num_categories: int) -> float:
    """Multi-rater weighted kappa: the mean pairwise Cohen's weighted kappa across every rater pair.
    `by_subject[s]` is the list of category indices the raters gave subject s (consistent rater
    order across subjects)."""
    _validate(by_subject, num_categories)
    n_raters = len(by_subject[0])
    by_rater = [[subject[r] for subject in by_subject] for r in range(n_raters)]
    pair_kappas = [
        cohen_weighted_kappa(by_rater[a], by_rater[b], num_categories)
        for a, b in combinations(range(n_raters), 2)
    ]
    return _clamp(sum(pair_kappas) / len(pair_kappas))


def gwet_ac1(by_subject: Sequence[Sequence[int]], num_categories: int) -> float:
    """Gwet's AC1 over the subjects. Robust to skew: the chance term uses π_k(1−π_k) rather than
    kappa's product of marginals, so a lopsided category distribution does not deflate it."""
    _validate(by_subject, num_categories)
    n_subjects = len(by_subject)

    agreements: list[float] = []
    category_share = [0.0] * num_categories
    for subject in by_subject:
        n_i = len(subject)
        counts = [0] * num_categories
        for category in subject:
            counts[category] += 1
        agreements.append(sum(c * (c - 1) for c in counts) / (n_i * (n_i - 1)))
        for k in range(num_categories):
            category_share[k] += (counts[k] / n_i) / n_subjects

    p_a = sum(agreements) / n_subjects
    p_e = sum(pi * (1.0 - pi) for pi in category_share) / (num_categories - 1)
    # Defensive: AC1's p_e ≤ 1/q ≤ 0.5, so 1−p_e ≥ 0.5 and this guard cannot fire in practice —
    # kept only so the function is total for any input (a divide-by-zero never reaches a client).
    if abs(1.0 - p_e) < 1e-12:
        return 1.0 if abs(1.0 - p_a) < 1e-12 else 0.0
    return _clamp((p_a - p_e) / (1.0 - p_e))


def compute_calibration_result(
    session: CalibrationSession,
    ratings: Sequence[CalibrationRating],
    *,
    computed_at: datetime,
) -> CalibrationResult:
    """Compute the per-anchor inter-rater agreement for a closed session from its SUBMITTED ratings.

    Every submitted assessor must have rated every (vignette, anchor) the session declares — ragged
    data is refused (the coefficients need balanced, paired data). Fewer than two submitted raters
    cannot measure agreement. Levels map to the ordinal maturity scale (Basic=0 … Frontier=3)."""
    submitted = [r for r in ratings if r.submitted]
    if len(submitted) < 2:
        raise CalibrationStatsError(
            f"A calibration session needs ≥2 submitted raters to measure agreement; "
            f"{len(submitted)} submitted."
        )
    # Consistent rater order (by assessor id) so the pairwise kappa pairs align across subjects.
    submitted = sorted(submitted, key=lambda r: str(r.owner_consultant_id))

    # (vignette_index, subcomponent_key) → level, per rater.
    by_rater: list[dict[tuple[int, str], MaturityLevel]] = [
        {(e.vignette_index, e.subcomponent_key): e.level for e in r.entries} for r in submitted
    ]

    anchors: list[AnchorAgreement] = []
    # An anchor (subcomponent) may appear in several vignettes; those vignettes are its subjects.
    seen: set[str] = set()
    for vignette in session.vignettes:
        for anchor in vignette.anchors:
            key = anchor.subcomponent_key
            if key in seen:
                continue
            seen.add(key)
            subject_indices = [
                i
                for i, v in enumerate(session.vignettes)
                if any(a.subcomponent_key == key for a in v.anchors)
            ]
            if len(subject_indices) < 2:
                # Agreement over a single item is not a reliability measure — flagging an anchor for
                # rewrite on one data point would mislead. A measured anchor needs ≥2 vignettes.
                raise CalibrationStatsError(
                    f"Anchor {key!r} appears in {len(subject_indices)} vignette(s); a reliability "
                    f"coefficient needs at least two. Design the session so each anchor recurs."
                )
            by_subject: list[list[int]] = []
            for vidx in subject_indices:
                levels: list[int] = []
                for rater in by_rater:
                    level = rater.get((vidx, key))
                    if level is None:
                        raise CalibrationStatsError(
                            f"Anchor {key!r} in vignette {vidx} was not rated by every submitted "
                            f"assessor — calibration needs complete, balanced data."
                        )
                    levels.append(level.rank - 1)
                by_subject.append(levels)

            kappa = weighted_kappa(by_subject, _NUM_MATURITY_CATEGORIES)
            ac1 = gwet_ac1(by_subject, _NUM_MATURITY_CATEGORIES)
            anchors.append(
                AnchorAgreement(
                    subcomponent_key=key,
                    n_raters=len(submitted),
                    n_vignettes=len(subject_indices),
                    kappa_w=kappa,
                    ac1=ac1,
                    flagged=kappa < KAPPA_REWRITE_THRESHOLD,
                )
            )

    return CalibrationResult(
        session_id=session.id,
        computed_at=computed_at,
        n_raters=len(submitted),
        anchors=tuple(anchors),
    )
