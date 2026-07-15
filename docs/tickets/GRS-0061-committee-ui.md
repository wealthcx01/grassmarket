# GRS-0061 — Rating Committee sign-off UI (§8) — resolves the committee finalise blocker in-product

- **Loop:** 5 (governance)
- **Status:** Done — from GRS-0060 (governance-UI gap). Half 1 of 2 (committee; dual-rating is GRS-0062).

## What

The committee sign-off workflow was API-only. Now it is fully in-product:

- **Owner:** the assessment's Summary step shows a **Rating Committee sign-off** panel — each
  high-stakes item (power Established+, triad above None, module Frontier), its rating, reason, and
  status (awaiting / approved / rejected / stale). Read-only for the owner (peer challenge: you can
  never sign off your own ratings).
- **Committee member / admin — discovery:** a new org-wide work-queue, `GET /committee/queue`
  (committee/admin only; 403 otherwise), lists every in-progress assessment with pending high-stakes
  items. The Workbench **Committee** tab renders it.
- **Committee member — review:** a committee-accessible route `/committee/[id]` (loads via
  `get_assessment_for_committee`, not the owner-only wizard) renders the same panel with an
  **Approve / Reject** control per item, requiring a rationale and allowing a dissent note. The
  server enforces the role + peer-challenge + speculative-approval (GRS-0051) rules.

## Backend

- `Repository.list_assessments_for_committee` — in-progress assessments across owners, committee/
  admin only.
- `GET /committee/queue` → `CommitteeReviewSummary[]` (assessment_id, subject, pending_count).

## Verified

- Backend: `test_committee.py` (24) incl. the new queue test (members-only, lists pending).
- Frontend: `CommitteeReviewPanel.test.tsx` (owner read-only vs committee controls vs empty).
- Live end-to-end: committee member discovers → reviews → approves with rationale; the owner sees
  the approval on their Summary. Zero console/JS errors.

## Exit criteria

- A committee member can find and sign off high-stakes ratings entirely in the UI; the owner sees
  the status. (Dual-rating §9 — the other finalise precondition — is GRS-0062.)
