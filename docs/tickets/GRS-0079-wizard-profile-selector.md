# GRS-0079 — Wizard operating-model profile selector

**Status:** Shipped
**Loop:** Loop 7 — Operating-model profiles
**Depends on:** ADR-0025, GRS-0077 (mechanism), GRS-0078 (exchange profile)
**Branch:** `grs-0079-wizard-profile-selector`

## Why

Profiles are a program (D-5) but a consultant couldn't reach them — the wizard's operating model was
a free-text `segment` datalist. This ticket makes choosing "Exchange" actually reshape the assessment
(module set + weights), not just label it. Retail stays the default and its scoring is unchanged.

## What shipped

**Contract:** `BusinessProfile.operating_model` (profile key; None → retail). Unlike the other
descriptive fields it IS scoring-relevant configuration — it selects WHICH keys/weights apply
(ADR-0025), validated at score time (fail loud). Schemas regenerated (parity green).

**Backend:**
- `GET /registry/profiles` → the selectable profiles (`{key, name}`, retail first).
- `GET /registry?profile=<key>` → the profile's registry VIEW (default retail = the full superset,
  byte-identical); an unknown profile is a 404.
- `atlas/active.profile_key_of(document)` + the router's `_profile_context(document)` route
  `live_score`, `evaluate_scenarios`, and `finalise` through `profile_scoring_context` — so the
  live panel, scenarios, and the finalised run all score against the document's profile. The run
  records WHICH profile scored it via the profile's distinct `coefficient_version` (immutable, #6).
  An unknown profile on the document is a 422 (never a silent retail fallback).

**Frontend:**
- Overview step: an **Operating model** selector bound to `/registry/profiles` (retail default);
  choosing a non-retail profile shows a "draft — not client-usable" caveat.
- `WizardClient`: fetches the profiles; a profile-keyed effect re-fetches `GET /registry?profile=` on
  profile change (a primitive dep, so only on the key changing — not every keystroke) → the wizard
  re-renders the profile's module/subcomponent set. Scenarios inherit the view for free.

## Guardrails

- **Retail default + unchanged:** an assessment with no `operating_model` scores identically — the
  golden master reproduces `V = 0.478565` end-to-end (proven in `test_profile_wizard_routing`).
- **Round-trip:** wizard selection → document → `live_score`/`finalise` → the profile's
  `coefficient_version` on the result. Non-retail is draft (`client_usable=False`) — surfaced in the
  UI where a critical-driven word would show.
- **Fail-loud:** only profiles with real content are offered; an unknown key 404s (registry) / 422s
  (scoring) — never a blank scoring run.

## Tests

`tests/test_profile_wizard_routing.py` — `profile_key_of` defaulting; `/registry/profiles`;
`/registry?profile=` reshaping + 404; live-score's `coefficient_version` reflects the profile
(retail/exchange). Frontend type-check · lint · vitest green; backend + golden master green.

## Not in scope / follow-ups

- Profile-aware **co-rater** dual-rating (the `/rate/…` page stays full-superset for now).
- Wealth/infra profiles, real weight elicitation, profile-filtered benchmark comparison (GRS-0084).
