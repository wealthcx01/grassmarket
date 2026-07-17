# GRS-0107 — Evidence-based rating rigor across the wizard

**Status:** Shipped
**Loop:** Part 2 — Advisor Studio UI/UX review
**Phase:** A (build now)
**Depends on:** —

## Why

Across the wizard, ratings are bare `unrated / Basic / Developing / Not Applicable / Not Assessed`
dropdowns with "no rigor" — nothing captures *why* a rating was chosen or *what evidence* supports it,
so the flow feels like guesswork for juniors rather than objective homework for senior operators. This
cross-cutting ticket adds per-rating evidence/rationale capture so every rating is defensible and the
assessment reads as rigorous (the founder's expectation: ~1hr of grounded work per profile). It is the
shared mechanism that the metrics (GRS-0103) and powers (GRS-0105) steps consume.

## What to build

**Rating evidence capture (`components/steps.tsx` — metrics / powers / deep-dive)**
- Beside each rating, capture supporting evidence/rationale (and, where relevant, an evidence grade), so
  a rating carries its justification rather than standing alone.

**Contract (`AssessmentDocument`)**
- Add evidence/rationale fields on `AssessmentDocument` so captured evidence persists with the
  assessment. Keep it additive and fail-loud (no silent default when a required rating lacks its
  evidence at the point rigor is enforced).

## Acceptance / verification

- Ratings across metrics, powers, and the infrastructure deep dive can carry evidence/rationale.
- Evidence persists on `AssessmentDocument` and survives reload.
- The metrics and powers steps (GRS-0103 / GRS-0105) consume this shared field rather than each
  inventing their own.

## Not in scope

- Scoring weight of evidence (evidence is captured/displayed, not scored differently here).
- AI-assisted evidence suggestion — GRS-0101 (Phase B).

## What shipped (Status: Shipped — branch grs-0107-evidence-rigor)

Per-rating evidence/rationale capture across the wizard, so every rating carries its justification
rather than standing alone:

- **Infrastructure Deep Dive** (`InfrastructureDeepDiveStep`) — an evidence/rationale input under each
  assessed subcomponent ("What evidence supports this rating?") persisting to the existing
  `SubcomponentRating.notes`. The grade change now preserves the note.
- **Business Metrics** (`BusinessMetricsStep`) — an evidence/rationale input under each observed metric
  ("Source / as-of date"), persisting to a new **`MetricEntry.notes`** field (contract + TS + doc
  helper). Additive; not a scoring input (the engine ignores it).
- **Strategic Powers** already capture per-side rationale (`benefit_evidence` / `barrier_evidence`,
  GRS-0069/0105) — the same evidence discipline, now consistent across all three rating surfaces.

Kept additive and fail-loud: the fields are optional captures (a rating without evidence still saves,
per autosave); nothing is silently defaulted. Golden master untouched (`notes` is not scored).

## Acceptance / verification

Metrics, powers, and deep-dive ratings each capture supporting evidence/rationale that persists on the
document. Schema parity green; backend + frontend gates green; golden master unchanged.
