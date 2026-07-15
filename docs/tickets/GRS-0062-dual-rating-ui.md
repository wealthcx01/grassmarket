# GRS-0062 — Dual-rating UI (§9) — completes the finalise workflow in-product

- **Loop:** 5 (governance)
- **Status:** Done — half 2 of 2 of the GRS-0060 governance-UI gap (committee was GRS-0061).

## What

Dual rating (§9 — every assessed subcomponent needs two independent raters + resolved consensus)
was API-only. Now it is fully in-product, closing the last thing that stopped a lead finalising an
assessment through the UI.

- **Lead (assessment Summary step):** a *Dual rating & consensus* panel, per module that still needs
  it — assign a co-rater by email, submit your own rating, then resolve consensus once both are in.
- **Co-rater discovery:** a Workbench **Rating requests** tab lists every module a colleague asked
  them to rate (`GET /assessments/rating-requests`).
- **Co-rater rating:** `/rate/[assessmentId]/[moduleKey]` — a blind rating form (they never see the
  lead's ratings; server-enforced). Submitting locks their draft.

## Backend

- `GET /consultants/by-email` — resolve a colleague by EXACT email to the minimum needed to assign
  them (id, name; never a password hash). Exact-match, so no directory enumeration.
- `Repository.list_my_rating_assignments` + `GET /assessments/rating-requests` — the co-rater's
  work-queue (declared before `/{assessment_id}` so the static path resolves).

## Verified end-to-end

A live browser run took an assessment fully through: lead assigns a co-rater by email → submits →
**co-rater discovers the request in the Workbench, rates blind, submits** → lead resolves consensus →
the §9 finalise blocker clears. Then committee sign-off (§8, GRS-0061) → **the assessment finalises
and a scoring run is created — entirely in-product.** Zero console/JS errors.

- Backend: `test_dual_rating.py` (20, incl. lookup + rating-requests). Frontend:
  `RatingRequestsPanel.test.tsx`. type-check / lint / build green; 68-test regression sample green.

## Exit criteria (met)

- A lead + a co-rater + a committee member can take an assessment from scored → consensus →
  sign-off → **finalised** without leaving the UI. GRS-0060 is fully closed.
