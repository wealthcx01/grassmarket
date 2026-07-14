# ADR-0017 — Commission config, immutable lines, and earnings governance

- **Status:** Accepted
- **Loop:** 6 (GRS-0028)
- **Normative source:** PRD §7 (earnings; rates are configuration per tier and attribution, never
  code); CLAUDE.md #6 (immutable versioned runs), #9 (scoping), ADR-0002 (score ≠ currency),
  ADR-0014 (objective facts are not self-attested).
- **Builds on:** ADR-0002 (`Money`), GRS-0012 (recovery-fee attribution + window).

## Context

"My Earnings" turns pipeline outcomes into money the advisor can see. Three things needed pinning:
how rates live (so a commercial change is never a code change), how a recorded commission stays
trustworthy over time, and who may do what.

## Decision

### 1. Rates are configuration, applied as basis points, fail-loud complete

The commission schedule is `registry_data/commissions.yaml` — a **basis-point** rate per
(consultant tier × sourcing attribution), loaded through `CommissionConfig`, which **refuses to load
unless every tier × every attribution is present** (the RecoveryFeeConfig / ADR-0001 completeness
pattern — a missing combination is a load-time error, never a default). A commission is
`round(base_value × rate_bps / 10_000)` in integer minor units (round-half-to-even, fixed and
golden-mastered); the base value's currency must match the config currency (no silent FX). The
computed `Money` carries the config `rate_ref` as its assumption reference — the £ is never bare
(ADR-0002). The shipped values are DRAFT (`commissions-v1-draft`); the real rates are an open
commercial decision (PRD §7), but the machinery and completeness guarantee are in place.

### 2. A commission line is immutable and content-hash-sealed; the rate is never retroactive

A `CommissionLine` stamps its provenance at record time — tier, attribution, `rate_ref`, and the
`base_value` the rate was applied to — and seals the **financial figures** with a SHA-256
`content_hash` (the scoring-run immutability pattern). Because the rate reference is frozen onto the
line, a later edit to `commissions.yaml` **cannot** change an existing commission — it reproduces
from its own fields. `payment_status` is the single mutable field (its lifecycle) and is
**deliberately excluded** from the hash, so the seal protects the money figures while the status
advances. Payment advances **forward-only**: pending → invoiced → paid; a backward move or a skip is
refused.

### 3. Governance: advisors VIEW their own earnings; recording + payment are admin/finance

Earnings transparency is self-service — an advisor lists their own commission lines, sees their
roll-up summary, and downloads a statement, all **strictly self-scoped** (another advisor's lines
are never visible; the cross-advisor aggregate is Holy Corner scope, not this ticket). But
**recording** a commission (which fixes the objective contract value it derives from) and
**advancing payment status** ("invoiced", "paid") are **admin/finance actions** (403 for a
non-admin). This is the ADR-0014 principle applied to money: an advisor cannot set the base value of
their own commission or mark their own pay "paid" — objective money facts are never self-attested.
The recovery fee is claimed once per attribution (a unique constraint refuses a double-claim).

## Consequences

- A rate change is a config edit + a new config version, never a code change, and never rewrites
  history; every recorded line traces to the `rate_ref` that produced it.
- The earnings surface is safe to expose to advisors: they see only their own, and cannot fabricate
  a paid commission.
- **Accepted scope boundaries:** the exact commission rates are the open commercial item (draft
  config, flagged). Retainer income (`CommissionKind.RETAINER`) has a kind but no dedicated recording
  flow yet — it records through the generic engagement path when needed. Pipeline-value projection
  is the earned-but-unpaid figure (pending + invoiced); a forward projection from un-recorded
  active-pipeline value needs a per-engagement contract value, which is a later addition. The
  admin/cohort earnings aggregate is Holy Corner scope.
