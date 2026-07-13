"""Golden-master + property tests for the calibration statistics (GRS-0022, Methodology §9).

The golden values are hand-computed (worked out in the comments) so the engine is pinned to an
independently-derived answer, not to itself — the same discipline as the ATLAS engine golden master.
"""

from __future__ import annotations

import math

import pytest

from grassmarket.workbench.calibration import (
    CalibrationStatsError,
    _clamp,
    cohen_weighted_kappa,
    gwet_ac1,
    weighted_kappa,
)


# --- Golden master: Cohen's weighted kappa (quadratic) ----------------------------------
#
# Two raters, k=3 categories (0,1,2), 4 subjects:
#   A = [0, 1, 2, 1], B = [0, 1, 1, 2]
# Observed proportions (÷4): (0,0)=.25 (1,1)=.25 (2,1)=.25 (1,2)=.25
# Marginals: A=[.25,.5,.25]  B=[.25,.5,.25]
# Quadratic weights w_ij = 1-((i-j)/2)^2 : diag=1, dist-1=.75, dist-2=0
#   p_o = 1(.25)+1(.25)+.75(.25)+.75(.25) = .875
#   p_e = Σ w_ij·A_i·B_j = .75
#   κ_w = (.875-.75)/(1-.75) = .125/.25 = 0.5
def test_cohen_weighted_kappa_golden() -> None:
    kappa = cohen_weighted_kappa([0, 1, 2, 1], [0, 1, 1, 2], num_categories=3)
    assert math.isclose(kappa, 0.5, abs_tol=1e-12)


# --- Golden master: Gwet's AC1 ----------------------------------------------------------
#
# Three raters, k=2 categories (0,1), 2 subjects:
#   subject 1 = [1,1,0]  (counts: cat0=1, cat1=2)
#   subject 2 = [0,0,1]  (counts: cat0=2, cat1=1)
# agree_i = Σ c(c-1) / (n(n-1)),  n=3 → denom 6
#   agree_1 = (0 + 2) / 6 = 1/3 ;  agree_2 = (2 + 0) / 6 = 1/3 ;  p_a = 1/3
# π_0 = mean(1/3, 2/3) = 1/2 ; π_1 = mean(2/3, 1/3) = 1/2
# p_e = 1/(2-1) · [ .5·.5 + .5·.5 ] = 0.5
#   AC1 = (1/3 - 1/2)/(1 - 1/2) = (-1/6)/(1/2) = -1/3
def test_gwet_ac1_golden() -> None:
    ac1 = gwet_ac1([[1, 1, 0], [0, 0, 1]], num_categories=2)
    assert math.isclose(ac1, -1.0 / 3.0, abs_tol=1e-12)


# --- Multi-rater weighted kappa is the mean of the pairwise coefficients -----------------
#
# Three raters over 3 subjects, k=4. Raters A and B are identical; C differs. The mean pairwise
# kappa must equal (κ_AB + κ_AC + κ_BC)/3, and κ_AB = 1 (identical), κ_AC = κ_BC (C vs a shared
# pattern) — so we assert the composition explicitly against the pairwise function.
def test_weighted_kappa_is_mean_of_pairwise() -> None:
    by_subject = [[3, 3, 2], [1, 1, 1], [2, 2, 3]]  # A,B identical; C = [2,1,3]
    a = [3, 1, 2]
    b = [3, 1, 2]
    c = [2, 1, 3]
    expected = (
        cohen_weighted_kappa(a, b, 4)
        + cohen_weighted_kappa(a, c, 4)
        + cohen_weighted_kappa(b, c, 4)
    ) / 3
    assert math.isclose(weighted_kappa(by_subject, num_categories=4), expected, abs_tol=1e-12)


# --- Properties -------------------------------------------------------------------------


def test_perfect_agreement_is_one() -> None:
    by_subject = [[2, 2, 2], [0, 0, 0], [3, 3, 3]]  # all raters identical every subject
    assert math.isclose(weighted_kappa(by_subject, 4), 1.0, abs_tol=1e-12)
    assert math.isclose(gwet_ac1(by_subject, 4), 1.0, abs_tol=1e-12)


def test_kappa_penalises_ordinal_distance() -> None:
    # Identical but for the last subject: a one-band error is penalised LESS than a three-band error
    # (the whole point of ordinal/quadratic weighting), so the near case scores a higher kappa.
    near = cohen_weighted_kappa([0, 1, 2, 3], [0, 1, 2, 2], 4)  # last off by one band
    far = cohen_weighted_kappa([0, 1, 2, 3], [0, 1, 2, 0], 4)  # last off by three bands
    assert near > far


def test_ragged_data_is_refused() -> None:
    with pytest.raises(CalibrationStatsError):
        weighted_kappa([[1, 2, 3], [1, 2]], num_categories=4)  # subject 2 missing a rater


def test_fewer_than_two_raters_is_refused() -> None:
    with pytest.raises(CalibrationStatsError):
        gwet_ac1([[1], [2]], num_categories=4)


def test_no_subjects_is_refused() -> None:
    with pytest.raises(CalibrationStatsError):
        weighted_kappa([], num_categories=4)


def test_out_of_range_category_is_refused() -> None:
    with pytest.raises(CalibrationStatsError):
        gwet_ac1([[0, 4]], num_categories=4)  # 4 is out of a 0..3 scale


def test_coefficients_never_escape_their_contract_bounds() -> None:
    # This exact perfect-disagreement distribution computes to -1.0000000000000022 before clamping,
    # which would fail AnchorAgreement's Field(ge=-1.0) and 500 the close. The value is clamped to
    # exactly the mathematical bound.
    kappa = weighted_kappa([[0, 2], [1, 1], [2, 0], [1, 1], [1, 1]], num_categories=3)
    assert kappa >= -1.0
    assert math.isclose(kappa, -1.0, abs_tol=1e-9)


def test_clamp_absorbs_float_noise_but_fails_loud_on_a_gross_excursion() -> None:
    assert _clamp(-1.0 - 1e-15) == -1.0  # float noise clamped to the bound
    assert _clamp(1.0 + 1e-15) == 1.0
    with pytest.raises(CalibrationStatsError):
        _clamp(5.0)  # a gross out-of-range is a logic error, refused (#3), not silenced to 1.0
