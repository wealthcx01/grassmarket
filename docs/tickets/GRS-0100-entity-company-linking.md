# GRS-0100 — Tie the subject to a real company (entity resolution)

**Status:** Planned
**Loop:** Part 2 — Advisor Studio UI/UX review
**Phase:** B (flagged follow-up — its own ADR/ticket set later)
**Depends on:** —

## Why

Today the assessment subject is a free-text "subject business name" with no authentication or link to a
real entity — two advisors can assess "Revolut" and "Revolut Ltd" as unrelated records, and nothing
ties an assessment to an actual company. This ticket adds company lookup / autocomplete against a real
registry so a subject resolves to a canonical entity. It is a **genuinely new capability**, not a
surfacing of existing work, so it is **deferred behind Phase A**: the rigor/depth wizard tickets ship
first, and entity resolution is scoped later as part of its own ADR / ticket set (alongside GRS-0101
and GRS-0109).

## What to build

**Subject entry (`app/assessments/page.tsx`, `components/steps.tsx`)**
- Replace the free-text subject-name field with a company lookup / autocomplete that resolves to a real
  registry entity, storing the canonical identifier alongside the display name so assessments tie to
  actual companies.
- Keep a manual-entry fallback for subjects the registry doesn't cover (fail loud on ambiguous matches
  rather than silently picking one).

## Acceptance / verification

- Selecting a subject resolves to and stores a canonical company identity, not just a string.
- Two assessments of the same company link to the same entity.

## Not in scope

- Choice of registry / data source and the entity-store contract — the deferred ADR decides these.
- Broad AI-assisted input — GRS-0101.
- Portfolio broadening/naming — GRS-0098.
