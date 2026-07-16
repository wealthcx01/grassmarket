# GRS-0068 — Structured create + Step-1 business profile

**Status:** Shipped
**Loop:** Track A (guided consulting UX — delivery review §4, NEXT-STEPS §3.6)
**Branch:** `grs-0068-business-profile`

## Why

The delivery review asked for a "structured Step-1 business profile (segment / regions / asset
classes / licensing)" so an assessment opens with the consulting context, not a bare subject line.
The wizard's Overview step collected only a subject and free-text notes.

## What shipped

**Contract (additive, descriptive — never scored):** new `BusinessProfile`
(`country`, `segment`, `asset_classes`, `regions`, `licensing` — all optional) on
`AssessmentDocument.profile`. It frames the assessment and feeds the portfolio view; it is **never a
scoring input** (the engine reads only subcomponents / metrics / powers) and **never enters the
scoring-run content hash** (verified: the hash is over `AssessmentInputs`, not the document).
Regenerated the committed schemas (`AssessmentDocument`, `Assessment`, `Extraction` — parity green).

**Wizard Overview step** (now the structured Step 1): a "Business profile · context only, not scored"
fieldset with Country, Segment (free-text with a suggestion datalist — **not** an enum; the
operating-model *profile selector* is the deferred Track-B concern), Asset classes and Regions
(comma-separated, parsed on blur so typing commas isn't fought), and Licensing. Autosaves through the
existing document PUT — no new endpoint. Read-only when finalised.

**On "structured create":** the create form stays a single field (name the business), and the
structured intake is the Step-1 profile — the business is named, then profiled. This delivers the
review's intent without plumbing profile fields through the create endpoint.

## Guardrails

- Purely descriptive: no scoring behaviour changes (CLAUDE.md #2, #6); the golden master and engine
  are untouched.
- `segment` is free text, deliberately **not** the operating-model profile selector (exchange vs
  broker module selection/weights) — that remains deferred to the profile ADR (Track B).

## Tests

`frontend/lib/doc.test.ts` — `setProfile` creates/merges the profile and never disturbs scoring
inputs; `parseList` trims and drops empties. Backend assessment/schema/finalise/repository subset
(42) + schema parity green; frontend type-check · lint · vitest green.

## Not in scope

- "Your Brokerages" portfolio home (which will surface `segment`) — GRS-0071.
- Operating-model profile selector + weights — Track B (profile ADR).
