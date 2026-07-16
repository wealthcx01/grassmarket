# GRS-0081 — C rubric anchors

**Status:** Planned
**Loop:** Loop 7 — C-index (Customer Proposition)
**Depends on:** ADR-0023 (Accepted), ATLAS-Methodology-v1.3

## Why

A registry key with no rubric anchor cannot be scored consistently across raters. The existing
engine ships 204 anchors in `rubric_anchors.yaml` (Methodology §4 template) and the loader is
fail-loud: a subcomponent with no anchor set refuses to load. The C modules added in GRS-0080 need
the same anchor coverage before the wizard (GRS-0083) can present anything to a consultant. This
ticket authors the C anchors, seeded from the seven completed reviews so the anchor language is
grounded in real observed brokerage behaviour rather than invented from scratch.

## What to build

Files:
- `src/grassmarket/atlas/data/rubric_anchors_c.yaml` (new) — §4-template anchors for every C
  subcomponent across the 10 Phase-E modules (`CUST_ONBOARDING` … `CUST_INNOVATION_DIFFERENTIATORS`).
- `src/grassmarket/atlas/registry.py` / anchor loader — register the C anchor file alongside the
  existing anchor source; the fail-loud "every assessed subcomponent has a full anchor set" check
  extends to C keys.

Refs:
- `src/grassmarket/atlas/data/rubric_anchors.yaml` — the 204 existing anchors are the format and
  tone template (Basic → Emerging → Advanced → Leading maturity language, per §4).
- Seed evidence — the 7 completed `_Claude` checklists (read-only, authoring input only):
  Saxo, IBKR, Lightyear, Revolut, Trading212, WeBull, Hargreaves Lansdown, under
  `…/Business/Briefing/Content-Bank/Projects/Brokerage-App-Reviews/*/`.

Reuse:
- The §4 anchor template, the maturity-level vocabulary, and the fail-loud anchor loader — no new
  anchor format is introduced.

New:
- The C anchor content itself, one full anchor set per C subcomponent.

## Acceptance / verification

- Every C subcomponent in the registry has a complete anchor set at every maturity level; a missing
  anchor is a load-time error (loader stays green only when coverage is total).
- Anchor language is traceable to the seven seed reviews (spot-checked in review, not asserted
  in code).
- No B/P/L anchor is modified; existing anchor tests stay green.
- Golden master untouched (no engine or coefficient change here).

## Not in scope

- Registry/widget definitions — GRS-0080 (prerequisite).
- Engine `_score_c` and coefficients — GRS-0082.
- Wizard capture — GRS-0083.
- Benchmark ingestion of the scored reviews — GRS-0084.
