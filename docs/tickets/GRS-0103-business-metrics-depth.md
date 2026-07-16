# GRS-0103 — Business Metrics: depth + per-metric context

**Status:** Planned
**Loop:** Part 2 — Advisor Studio UI/UX review
**Phase:** A (build now)
**Depends on:** —

## Why

The Business Metrics step reads "really high level — just inputting numbers": bare fields with no
explanation of what each metric means or why it matters. For a senior operator this is guesswork, and
worse, a metric means different things across operating models — a figure that's central for a retail
broker may be marginal for a wealth manager or an exchange. This ticket adds per-metric context that is
**operating-model aware**, so the advisor understands each number in the context of the profile being
assessed rather than filling a generic form.

## What to build

**Business Metrics step (`components/steps.tsx` — BusinessMetricsStep)**
- For each metric, show a plain-English explanation of what it is and why it matters, varied by the
  selected operating model (wealth manager vs retail broker vs exchange).
- Source the descriptions from the registry's metric definitions so the copy stays single-sourced and
  fails loud on an unknown metric rather than rendering an empty caption.

**Registry (metric descriptions)**
- Extend the registry metric definitions with the per-metric / per-profile descriptive context the step
  renders. REUSE the existing registry loading + fail-loud accessors; add description content, not a new
  mechanism.

## Acceptance / verification

- Every metric on the step renders a plain-English, operating-model-appropriate description.
- Descriptions come from the registry (single source); a metric missing its description fails loud.

## Not in scope

- Changing which metrics exist or how they score.
- Cross-cutting evidence capture on ratings — GRS-0107.
