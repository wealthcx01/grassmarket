# GRS-0090 — Rename "ATLAS" → "Platform Power" product-wide

**Status:** Planned
**Loop:** Part 2 — Advisor Studio UI/UX review
**Depends on:** ADR (ATLAS → Platform Power rename)

## Why

"ATLAS" is a placeholder name that carries no meaning for an advisor or client — the founder's decision
(2026-07-16) is to retire it everywhere user- and client-facing and adopt **"Platform Power."** The
framework already produces "the Platform Power Report" and a score called "Platform Value (V)", so the
name is coherent; only the ATLAS label is legacy. This is a broad find-and-replace across advisor UI
copy, methodology/docs, and a coordination note to the public BC Advisory page. The engine's internal
identifiers stay untouched to avoid churn and protect the golden master.

## What to build

**Naming nuance (apply exactly, everywhere copy is changed)**
- Use **"the Platform Power assessment/method"** for the *process*.
- Use **"the Platform Power Report"** for the *deliverable*.
- Avoid the awkward recursion — never write "the Platform Power methodology produces the Platform Power
  Report."
- Engine identifiers stay **internal and unchanged**: the `atlas/` package, the `b`/`p`/`l`/`v` keys,
  `atlas/`-engine references in code. Only user- and client-facing text changes.

**(a) UI copy** — replace ATLAS references across `frontend/app/page.tsx`, `frontend/app/guide/page.tsx`,
`frontend/components/steps.tsx`, and section blurbs. Grep `ATLAS`/`atlas` across the frontend and update
only the human-facing strings.

**(b) Docs / methodology** — update `docs/ATLAS-Methodology-*` and the "ATLAS Assessment — How It Works"
copy, plus any prose references to the engine. (Methodology-doc filenames may stay; the decision on
renaming files vs. only their prose is captured in the ADR.)

**(c) Engine internal rename decision** — flag whether to rename the `atlas/` package/identifiers. The
recommendation is to **leave internal code identifiers as `atlas`** to avoid churn and protect the
golden master; record the decision in the ADR.

**(d) Public-site coordination note** — the public BC Advisory page also says "ATLAS"; add a coordination
note so the public design is updated in step.

## Acceptance / verification

- No advisor- or client-facing surface displays "ATLAS"; all read "Platform Power" per the nuance above.
- The recursion antipattern ("Platform Power methodology produces the Platform Power Report") appears
  nowhere.
- Engine identifiers (`atlas/`, `b`/`p`/`l`/`v`) and the golden master are unchanged; tests stay green.
- The public-site coordination note is recorded.

## Not in scope

- Refining the P and L labels — that is GRS-0097.
- Any change to scoring math or engine identifiers.
