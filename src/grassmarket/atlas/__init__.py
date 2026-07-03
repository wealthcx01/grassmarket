"""ATLAS scoring engine — Loop 1 (NOT this loop).

Deliberately empty of computation. The engine implements `docs/ATLAS-Methodology-v1.md` exactly:
the registry-validated `CoefficientSet` (see `bcap_contracts.assessments`), two-track aggregation
(§5), Monte Carlo ranges (§7), and the three-layer value bridge (§10, ADR-0002). Loop 0 ships
only the contracts and invariants that make the prototype's defects (D1–D9) structurally
impossible; no scoring code exists here yet, and the golden-master fixture (CLAUDE.md testing
rules) gates the first line of it.

Do not add scoring here without: (1) the hand-computed golden-master fixture, and (2) the
property tests (monotonicity, bottleneck, N/A renormalisation, Not-Assessed exclusion).
"""
