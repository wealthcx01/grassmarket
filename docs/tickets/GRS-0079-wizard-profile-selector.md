# GRS-0079 — Wizard operating-model profile selector

**Status:** Planned
**Loop:** Loop 7 — Operating-model profiles
**Depends on:** ADR-0025 (operating-model profiles), GRS-0077 (profiles mechanism), GRS-0078 (exchange profile)

## Why

Profiles are elevated to a program (D-5), but a consultant can't reach them: the wizard's operating
model is still a free-text hint. `BusinessProfile.segment` is a datalist of suggestions
(`frontend/components/steps.tsx:77`) explicitly carrying the comment "the operating-model profile
selector is deferred" (`:76`). This ticket promotes that field into a real profile selector that
drives module/weight selection, so choosing "Exchange" actually reshapes the assessment instead of
just labelling it. Retail stays the default and its scoring is unchanged (ADDITIVE).

## What to build

**Frontend (`frontend/components/steps.tsx`)**
- Replace the `SEGMENT_SUGGESTIONS` datalist (`steps.tsx:77`, anchored by the deferral comment `:76`)
  with a **profile selector** bound to the profile keys shipped by GRS-0077/0078 (retail default;
  exchange). Selecting a profile sets the document's profile, which reshapes the module/subcomponent
  set the wizard renders and the weight/critical set it scores against.
- REUSE the existing overview field wiring (`OverviewStep`, `steps.tsx:86`) and document update path;
  do not invent a parallel state channel.

**Wire-through (contracts + service)**
- The selected profile flows onto the assessment document and into `live_score`
  (`src/grassmarket/assessments/service.py:220`), which already takes `coefficients` + `registry` —
  it picks the profile's CoefficientSet + registry view (mechanism from GRS-0077). No new engine
  logic here; this ticket only routes the selection.
- Persist the profile on the assessment so a finalised run records which profile scored it (immutable
  provenance — CLAUDE.md #6).

## Acceptance / verification

- Choosing "Exchange" reshapes the wizard's rendered module set AND the scoring (exchange
  CoefficientSet + registry view), with no retail-only subcomponents shown.
- Retail is the default and is **unchanged** — an existing retail assessment renders and scores
  identically (golden master `V = 0.478565` still reproduced end-to-end).
- The selected profile round-trips: set in the wizard → carried on the document → used by
  `live_score` → recorded on the finalised run.
- Frontend suite (type-check · lint · vitest) green; a profile with no shipped content cannot be
  selected (fail-loud, not a blank scoring run).

## Not in scope

- The profile mechanism and registry view — GRS-0077.
- Exchange (or any non-retail) profile CONTENT — GRS-0078 and later tickets.
- Diagnostic visuals / deliverable sections reacting to profile — later Loop 7 tickets.

> Note: profile criticals interact with a base set still `draft-pending-ratification`
> (`modules.yaml:10-15`); the selector must not imply the exchange criticals are ratified — surface
> the draft status in the UI where a critical-driven rating word is shown.
