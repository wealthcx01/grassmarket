# GRS-0258 — Founder review: return with a note

**Status:** OPEN (2026-09-03). **Priority:** MED-HIGH. **Type:** Feature. **Source:** R6. Replaces **G6**.

## Why

A review can be approved and nothing else. `POST /assessments/{id}/founder-approval` is
approve-only: no note, no returned state, no resubmission. The design's whole review loop —
"Henderson resolved your switching-costs note, the powers are back for re-review" — has no backing.

So today a founder who disagrees has to either approve something they do not believe or say nothing
and leave the advisor guessing.

## Build

- A **return** action carrying a **required** note. Returning without saying why is the failure
  mode this exists to fix.
- Note threading on the assessment.
- `returned` and `resubmitted` states surfaced in `/founder-review/queue`.
- Approval signs **the exact version**; a later edit voids it (matches GRS-0256).

## Done when

A founder returns an assessment with a note, the advisor sees it against the section it concerns,
resubmits, and the queue shows it as resubmitted rather than new.
