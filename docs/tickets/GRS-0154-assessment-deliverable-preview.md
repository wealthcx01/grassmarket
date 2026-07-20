# GRS-0154 — Assessment-level deliverable preview (the solo/sandbox "see the real deliverable" path)

**Status:** Done (2026-07-20). From the mock-advisor re-measure — Priya/LSEG, Elena/Deutsche Börse, James/Brewin, all **HIGH**.
**Loop:** Part 2 — trust. **Related:** GRS-0148/0149 (solo/sandbox path), ADR-0023.

## Why

Three of five personas hit the same wall: after finalising a **sandbox** assessment (the solo path
that promises "see the real deliverable, watermarked"), there was **no route to a document**.
Deliverable generation was reachable *only* via a won deal's engagement (`POST
/engagements/{id}/deliverables`); a standalone finalised assessment wasn't linked to one, and
`/deliverables` redirected to an empty Engagements page. Priya: *"the whole point of the sandbox
didn't pay off — a cold user is left holding a finalised assessment with no output."* For a technical
buyer, **the artifact is the sale** — and it was unreachable.

## What shipped

- **`GET /assessments/{assessment_id}/deliverable-preview`** — renders the deliverable directly from a
  finalised assessment's own scoring run, **no engagement required**. It reuses the exact `_render`
  path (same profile view + coefficient set the run was scored under, GRS-0148e) and streams the
  `.docx`. It is **always internal + watermarked** (`client_facing=False`), so:
  - it renders even for a **draft wealth/exchange profile** (the client-pack gate is untouched — a
    client-facing pack still refuses on a non-client-usable set), and
  - nothing is persisted (a preview, not a stored deliverable).
  - Owner-scoped and fail-loud: unfinalised ⇒ 409; another consultant ⇒ 404; a committee gate ⇒ 409.
- **Frontend:** `api.previewAssessmentDeliverable`, and a **"Download preview (.docx)"** button on the
  Summary step of any **finalised** assessment — so the sandbox/solo promise actually pays off.

## Tests
`tests/test_deliverables.py`: finalised ⇒ 200 real `.docx` carrying the "DRAFT — not client-usable"
watermark; unfinalised ⇒ 409; owner-scoped (another consultant ⇒ 404). 18 deliverable tests green;
frontend type-check + lint green.
