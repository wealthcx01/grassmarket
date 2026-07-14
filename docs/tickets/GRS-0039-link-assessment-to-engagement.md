# GRS-0039 — Link a finalised assessment to an existing engagement

- **Loop:** 6 (workflow completion)
- **Branch:** `grs-0039-link-assessment`
- **Status:** In review
- **Normative source:** PRD §4 (engagements/deliverables). Surfaced by the 2026-07-14 UI/UX redesign
  (PR #45), which added the "Start an assessment →" CTA on the engagement page but left the loop open.
- **Depends on:** GRS-0013 (engagements), the assessment finalise flow.

## Problem

An engagement's `assessment_ids` were only settable **at engagement-open time**
(`repository.create_engagement`), before any assessment exists. But the real workflow is: contract a
prospect → open an engagement → *then* run and finalise an ATLAS assessment → generate deliverables.
With no way to link an assessment to an **existing** engagement, that chain **couldn't complete
through the UI** — deliverables (which require a finalised linked assessment) could never be
generated for an engagement opened the normal way.

## Change

- **Repository:** `link_assessment_to_engagement(principal, engagement_id, assessment_id)` — appends
  a finalised assessment to a scoped engagement. Same guards as engagement-open: cross-owner/missing
  engagement or assessment → not-found (no existence leak); unfinalised or already-linked →
  `EngagementLinkError`. Owner is the principal, never caller-supplied.
- **API:** `POST /engagements/{engagement_id}/assessments` `{assessment_id}` → the updated
  `Engagement`. 404 on cross-owner/missing; 409 on unfinalised or duplicate.
- **Frontend:** the engagement page gains a "Link a finalised assessment" control (a select of the
  advisor's own finalised assessments not yet linked here, + a Link button), next to the existing
  "Start an assessment →" CTA. On-design (shared `.btn`/form styling).

## Tests

- `tests/test_engagement_detail.py`: link a finalised assessment to an existing engagement (persists
  on detail); refuse an unfinalised assessment (409); refuse a duplicate link (409); refuse a
  cross-owner engagement (404). Verified live end-to-end (link → 200, dup → 409) and in the browser
  (the control renders and links).

## Exit criteria

- An engagement opened without an assessment can have a finalised assessment linked, after which
  deliverables generate.
- All the scoping/finalised/duplicate guards hold. Full gate green; CI green.
