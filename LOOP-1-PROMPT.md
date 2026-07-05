# Claude Code Loop 1 Prompt — paste the block below

Prerequisite: PR #1 (GRS-0001 scaffold) is merged to `main`.

```
Continue the Grassmarket project at C:\dev\Grassmarket. This session is Loop 1: the
ATLAS scoring engine, to ATLAS Methodology v1.1 exactly. No wizard UI (that's Loop 2).

CONTEXT: Loop 0 shipped the contracts package (registry, CoefficientSet invariants,
Money/Score ADR-0002 boundary), repository layer with scoping, auth, CI. Read your
project memories, CLAUDE.md, docs/ATLAS-Methodology-v1.1.md (normative), and
docs/Grassmarket-PRD-v2.md §3 before writing code. Pull latest main first.

WORK AS TICKETS, in this order (one ticket = one branch = one PR):

GRS-0002 — Registry content.
- Populate the 9 modules' subcomponents from the prototype's authoritative draft:
  C:\Users\John\OneDrive\BruntsfieldCapital\Business\Advisory\Technology\Assessment Wizard\
  bruntsfield_advisory_assessment_wizard_v2\config\modules_subcomponents.yaml
  (51 subcomponents with labels/descriptions). Mark the set status "draft-pending-
  ratification" in the registry metadata.
- Add a draft business-metric register: metric key, label, declared unit, direction,
  normalisation anchor points (documented placeholders where judgment is pending).
- Propose critical-subcomponent flags per module (needed by the rating gates) as
  draft; list them in the ticket for John's review.

GRS-0003 — Golden-master fixture.
- Build an Excel workbook (fixtures/golden-master.xlsx) that computes one complete
  assessment END-TO-END with visible spreadsheet formulas: all subcomponent ratings
  (levels + E-grades + some N/A and Not Assessed cases), q_m per module (blend +
  min), rating gates, L, B (with explicit normalisation), P, V, and the two-track
  outputs. Use a realistic composite mid-tier retail brokerage as the subject.
- Export the same case as tests/fixtures/golden_master.json (inputs + every
  intermediate + final value).
- STOP after this ticket and present the workbook for John's review — the scores
  and judgment calls are his to ratify. Do not start GRS-0004 until he approves
  the fixture (he may adjust scores; regenerate the JSON from the workbook).

GRS-0004 — Deterministic engine (after fixture approval).
- src/grassmarket/atlas/: pure functions, contracts-typed, fail-loud. Two-track
  aggregation per Methodology §5: continuous q_m/L/B/P/V AND rule-based rating
  gates. N/A renormalises weights; Not Assessed never contributes and taints the
  gate; denominators only over applicable+assessed.
- The golden-master test: engine reproduces every value in the fixture exactly.
- Property tests: monotonicity (raising any subcomponent never lowers V);
  bottleneck (raising the min subcomponent raises q_m at least as much as raising
  the max by the same step); N/A renormalisation; Not-Assessed exclusion; gate
  consistency (gate never contradicts §5.2 rules).
- A draft v1 CoefficientSet fixture with provenance record marked
  "draft-pending-elicitation" — loadable for tests, flagged not-client-usable.

GRS-0005 — Uncertainty engine.
- Monte Carlo per Methodology §7: evidence grades E1–E4 set input distribution
  widths; outputs P10/P50/P90 for V/L/B/P; per-module and overall Assessment
  Uncertainty Rating (Low/Medium/High/Very High) from evidence mix + coverage;
  tornado data (input sensitivity ranking) and weight stability intervals.
- Seeded RNG for deterministic tests; document distribution choices in the ticket.

GRS-0006 — Value layer + scoring runs.
- Scenario evaluation by FULL RE-SCORING (ΔV) → Upgrade Priority Index. No LV
  formula, no score×currency arithmetic (the AST test must stay green).
- Value bridge per Methodology §10 as three separated computations: cost model
  (Money), lever NPV model (Money, with a typed assumption register), strategic
  ordinal ratings. Levers: cost-to-serve, project drag, incident expected loss,
  revenue enablement — each with client-supplied baselines as inputs.
- Scoring-run persistence: append-only, content-hashed, storing inputs + all
  intermediates + engine/methodology/coefficient versions. Finalisation locks
  inputs; scenarios remain editable. First Alembic migration lands here.

EXIT CRITERIA: golden master reproduced exactly; all property tests green; ruff/
pyright/pytest/pre-commit green; CI green on every PR; registry populated (draft-
flagged); Monte Carlo produces ranges on the golden-master case; value bridge runs
on a worked example with its assumption register rendered.

Non-negotiables: Methodology v1.1 is normative — deviations require an ADR; fail loud;
no .get(key, default) in scoring paths; pure functions in the engine (DB access only
at the persistence boundary); propose-not-execute for anything AI-generated.
```

## Founder tasks alongside Loop 1 (not Claude Code's)

1. Review and ratify the golden-master workbook at the GRS-0003 pause — the scores
   are your judgment calls.
2. Review the draft subcomponent set + critical flags from GRS-0002.
3. Schedule the weight-elicitation panel (4–8 experts, swing-weighting + Delphi per
   Methodology §6) — its output replaces the draft CoefficientSet.
4. Start rubric anchor writing (204 anchors); the prototype descriptions are the
   seed material. Anchors are Loop 2's wizard guidance content.
