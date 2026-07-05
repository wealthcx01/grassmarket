# Architecture Decision Records

Cross-cutting decisions for Grassmarket. One ADR per decision; ADRs are immutable once
Accepted — a change is a new ADR that supersedes the old one (never a silent edit).

| ADR | Title | Status |
|---|---|---|
| [ADR-0001](ADR-0001-scale-system-and-key-registry.md) | Scale system and the single key registry | Accepted |
| [ADR-0002](ADR-0002-value-layer-two-track-scoring-and-value-bridge.md) | The value layer: two-track scoring and the three-layer value bridge | Accepted |
| [ADR-0003](ADR-0003-module-rating-gate.md) | The module rating gate (operationalising §5.2) | Accepted |
| [ADR-0004](ADR-0004-power-strength-encoding.md) | Numeric encoding of ordinal power strength for the P index | Accepted |
| [ADR-0005](ADR-0005-index-range-comparability.md) | Comparability of the B / P / L index ranges at composition | Accepted |
| [ADR-0006](ADR-0006-business-metric-grouping.md) | Group-weighted Business index (B) | Accepted |
| [ADR-0007](ADR-0007-powers-benefit-barrier-triad.md) | Powers carry Benefit + Barrier; the triad is derived; powers never N/A | Accepted |
| [ADR-0008](ADR-0008-metric-power-input-uncertainty.md) | Metric & power input uncertainty; honest labelling of unmodelled uncertainty | Accepted |

ADR-0003 through ADR-0007 are folded into `docs/ATLAS-Methodology-v1.1.md`; ADR-0008 into
`docs/ATLAS-Methodology-v1.2.md`, which supersedes v1.1 (amending §3.3/§7 only) and is normative for
the scoring engine. Where an ADR and the Methodology disagree, the Methodology wins and the ADR is a
defect.
