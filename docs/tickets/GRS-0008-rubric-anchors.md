# GRS-0008 — Rubric anchor library

- **Loop:** 2 (see PRD §9)
- **Branch:** `grs-0008-rubric-anchors`
- **Status:** In review
- **Normative source:** `docs/ATLAS-Methodology-v1.2.md` §4; ADR-0001.
- **Depends on:** GRS-0002/0002a (registry).

## Goal

Contract-typed storage + loader for the **204 rubric anchors** (51 subcomponents × 4 maturity
levels, Methodology §4) — the guidance content the wizard (GRS-0010) renders. This ticket is the
**structure**; the content is John's to author and ratify.

## What shipped

- **Contracts (`bcap_contracts.rubric`):** `RubricAnchor` (§4 template — behavioural statement,
  required evidence, differentiator questions, misgrading notes) with an `AnchorStatus`
  (`authored` / `draft` / `todo`); `RubricLibrary` with `get` / `for_subcomponent` /
  `validate_against`; `load_rubric_library()`.
- **Fail-loud (ADR-0001):** the loader validates every (subcomponent, level) pair is **present or
  explicitly TODO**. A silently missing pair → `MissingAnchorError`; an unknown subcomponent key →
  `UnknownKeyError`; a duplicate → `DuplicateAnchorError`. An `authored` anchor with an empty
  statement (or without the full §4 template) is refused; a `todo` anchor must carry no content, so
  draft/authored content can never hide behind a TODO. `status` is required (no default).
- **Registry-linked, fully-qualified keys:** anchors key off the GRS-0002a `<MODULE_KEY>_<LEAF>`
  keys (e.g. `OEMS_EXEC_ALGOS`) — the old short keys are never reintroduced.
- **Seed (`registry_data/rubric_anchors.yaml`, draft-pending-ratification):** the prototype provided
  **no** anchor content (only subcomponent labels, already in the registry), so the only
  authoritative seed is the Methodology **§4 worked example** — Smart Order Routing — authored across
  all four levels for `OEMS_EXEC_ALGOS`. Every other subcomponent is listed under `todo_all_levels`:
  all four levels **explicitly** not-yet-authored. **Nothing is fabricated.** Result: 4 authored, 200
  explicit TODO, 204 total.

## Tests

Seeded library loads all 204 (4 authored OEMS anchors round-trip with the full template; an
unauthored anchor is an explicit empty TODO point); a missing level, an unknown key, and a duplicate
each refuse at load time; every anchor's level is a valid `MaturityLevel`; an authored anchor
requires a statement + the full template; a todo anchor must carry no content.

## Content note (founder task, NOT this ticket)

Author and ratify the 204 anchors — full BARS statements, 2–4 required-evidence artifacts, 1–2
differentiator questions, and misgrading notes per §4. The prototype descriptions (now the
subcomponent labels in the registry) are the seed; the `OEMS_EXEC_ALGOS` anchors are a worked
example of the target quality. Authoring a subcomponent moves it out of `todo_all_levels` into
`anchors:`; κ data from calibration sessions (§9) tells us which anchors actually need work.

## Out of scope

Exposing anchors through the assessment API (GRS-0009) and rendering guidance in the wizard
(GRS-0010). The anchor contracts are not yet in the JSON-Schema mirror — they join it when the API
surfaces them to the frontend.
