# GRS-0188 — Implement the founder review gate

**Status:** Planned (2026-07-23, founder feedback items 23 and 24). **Priority:** HIGH.
**Loop:** founder-feedback remediation, Wave 2. Carries ADR-0041; Methodology v1.6 amends §8/§9.

## Why

Founder decision: peer rating requests, committee approvals, and calibration sessions go; every
client draft routes to john@bruntsfield.capital for review, and the founder signs everything
that leaves the building. Depth confirmed 23/07: **disable + founder gate** — governance code
and history tables stay dormant and reversible; the product flows change.

## Scope

1. **Founder identity (config, not code).** `Settings` in `src/grassmarket/config.py` gains
   `founder_reviewer_email: str` (env `GM_FOUNDER_REVIEWER_EMAIL`, default
   `john@bruntsfield.capital`). At login, `AuthService` mints an `is_founder` boolean claim into
   the Grassmarket JWT when the authenticated consultant's email equals the configured value
   (case-insensitive); `Principal` (in `src/grassmarket/data/repository.py`) gains
   `is_founder: bool = False`, threaded exactly as `is_admin`/`is_committee` are today. Decision:
   the founder role is a claim derived from config at token mint, not a DB column, so rotating
   the reviewer is an env change plus re-login, with no migration.

2. **Founder approval record (contract + migration).** New contract module
   `packages/bcap_contracts/src/bcap_contracts/founder_review.py` with:
   - `FounderApproval(OwnedResource)`: `assessment_id: UUID`, `document_hash: str`
     (`min_length=64, max_length=64`, lowercase sha256 hex), `approved_by_consultant_id: UUID`,
     `approved_at: datetime`.
   JSON schema regenerated into `packages/bcap_contracts/.../json_schema/`; TS mirror
   `FounderApproval` added to `frontend/lib/types.ts`. New migration
   `migrations/versions/0032_founder_review.py`: table `founder_approvals`
   (id, owner_consultant_id, assessment_id FK, document_hash, approved_by_consultant_id,
   approved_at, created_at, updated_at; index on assessment_id) plus a nullable
   `review_requested_at` timestamp column on `assessments`. Decision: approvals are append-only
   rows and the gate matches on the CURRENT document hash — a stale-hash approval simply never
   matches, which implements "re-edit re-opens review" with no state machine and no deletion.

3. **Repository methods** (new section in `src/grassmarket/data/repository.py`, all
   fail-loud, all through the repository layer):
   - `_document_hash(row) -> str`: sha256 hex of `row.document_json` (server-computed only,
     never caller-supplied).
   - `request_founder_review(principal, assessment_id) -> Assessment`: owner/admin only
     (existing `_require_assessment`), refuses a finalised assessment (`ConflictError`), sets
     `review_requested_at = now`. Idempotent re-request updates the timestamp.
   - `record_founder_approval(principal, assessment_id) -> FounderApproval`: refuses unless
     `principal.is_founder` (`ScopeViolationError`); refuses a finalised assessment
     (`ConflictError`); computes the hash from the stored document at call time; appends the
     row; writes an audit event (new `AuditEventType.FOUNDER_APPROVAL`).
   - `current_founder_approval(assessment_id) -> FounderApproval | None`: the newest approval
     whose `document_hash` equals the current document hash, else `None`.
   - `list_founder_review_queue(principal) -> list[tuple[Assessment, str]]`: founder/admin
     only; every PRODUCTION, non-finalised assessment with `review_requested_at` set and no
     current-hash approval, oldest request first, with the owning advisor's name.

4. **Endpoints** (`src/grassmarket/web/routers/assessments.py` + a new
   `src/grassmarket/web/routers/founder_review.py`, prefix `/founder-review`):
   - `POST /assessments/{id}/submit-for-review` → 200 `Assessment`; 404 unowned/unknown; 409
     finalised.
   - `POST /assessments/{id}/founder-approval` → 201 `FounderApproval`; 403 when the caller is
     not the founder (the resource is already visible to its owner, so a role refusal is honest
     and leaks nothing); 404 unknown; 409 finalised.
   - `GET /founder-review/queue` → 200 list (founder/admin); 403 otherwise.
   - `GET /assessments/{id}/founder-approval` → 200 `FounderApproval | null` (owner-scoped) so
     the wizard can show "Submitted for review → Approved by … on …".

5. **Finalise chain** (`finalise_assessment`, routers/assessments.py ~349–405): for
   `gated` (PRODUCTION) records, DELETE the `consensus_blockers` block and the
   `committee_blockers` block and ADD, in their place, one founder gate: if
   `repo.current_founder_approval(assessment_id)` is `None`, raise 409 with detail
   "Cannot finalise — awaiting founder approval (ADR-0041). Submit for review and have the
   founder approve the current document." Scoreability gate, certified-lead gate
   (`requires_certified_lead` + admin OVERRIDE), the ADR-0029 sandbox/demo self-approval
   branch, `compute_score`, and `create_scoring_run` are byte-for-byte unchanged — no stored
   score, run, or golden master changes.

6. **Deliverable release** (`src/grassmarket/deliverables/gate.py` + `service.py` +
   `routers/deliverables.py`): new `FounderApprovalPendingError` and
   `assert_founder_approved(approval: FounderApproval | None, *, client_facing: bool)` in
   gate.py (no-op for internal drafts; refuses a client pack without a current approval). The
   deliverables router fetches `current_founder_approval` for the linked assessment and passes
   it through `render_diagnostic_document`, which calls the new assert where it today calls
   `assert_committee_approved`; the committee assert and its call from
   `render_modernisation_roadmap` are removed from the live path but the functions and their
   unit tests remain in place, dormant. The AI-narrative gate (`assert_narratives_approved`,
   ADR-0009) is unchanged; for client packs the founder is in practice the approver, which
   needs no code change (approval is recorded by whoever holds the surface).

7. **Review surface (frontend).** New `frontend/components/workbench/FounderReviewPanel.tsx`
   in the CommitteePanel's slot: lists the queue from `GET /founder-review/queue`, links each
   row to the assessment, and offers "Approve current version" (POST founder-approval) with the
   hash short-form shown. `WorkbenchClient.tsx`: the tab is labelled "Founder review" and
   rendered only when the session carries `is_founder` (claim exposed through
   `frontend/lib/session.ts`). The wizard finalise rail (`frontend/app/assessments/[id]`)
   shows the review status chip: "Not submitted" / "Submitted for review" / "Approved by … on
   …" / "Re-edited since approval — re-submit".

8. **Retirements (disable, not delete).**
   - Frontend: remove the `calibration`, `requests`, and `committee` tabs from
     `WorkbenchClient.tsx`; delete `RatingRequestsPanel.tsx` (+ its test),
     `CalibrationPanel.tsx`, `CommitteePanel.tsx`, `frontend/components/CommitteeReviewPanel.tsx`
     (+ tests), and the dual-rating assignment/consensus UI from the assessment page; remove the
     related `frontend/lib/api.ts` calls.
   - Backend: the dual-rating routes in `routers/assessments.py` (`/raters`, own-draft,
     submit, consensus), all of `routers/committee.py`, and all of `routers/calibration.py`
     return 410 GONE with detail "Retired under ADR-0041 (founder review gate); the peer
     machinery is dormant, not deleted." Decision: 410 (not removal) so any stale client fails
     with an explanation, never a generic 404. Repository sections (dual rating ~2837–3130,
     committee ~3132–3259, calibration ~3273–3413), their tables, `grassmarket/atlas/committee.py`,
     `grassmarket/workbench/calibration.py`, and the kappa/AC1 stats engine stay in place with
     their unit tests (`test_dual_rating.py`, `test_committee.py`, `test_calibration.py`,
     `test_calibration_stats.py`) exercising the repository/pure layers directly; only their
     HTTP-level tests change to assert 410.

9. **Certification evidence.** Remove the `self._auto_credit_participation(row, finalised_at)`
   call from `finalise_assessment` in repository.py (~2743); the method body stays, dormant,
   with its unit tests. `log_shadow_assessment`, `log_observed_lead`, and OVERRIDE-with-reason
   remain the (founder/admin-recorded) evidence routes; ADR-0013's certified-lead enforcement
   in the finalise chain is untouched.

10. **Bench queue.** `assemble_queue` in `src/grassmarket/workbench/bench.py` drops the
    `pending_rating_*` and `committee_*` parameters and their two spec blocks; the workbench
    fetch in `routers/bench.py` stops computing those counts. `BenchItemKind.RATING_REQUEST`
    and `.COMMITTEE` stay in the contract (dormant). Full re-prioritisation is GRS-0199.

11. **Docs.** Flip ADR-0041 from Proposed to Accepted; add the Methodology v1.6 amendment
    document under `docs/` (same amendment pattern as v1.2: §8/§9 now describe the founder gate
    as the current governance mode and the peer machinery as the dormant scale-up mode; §5
    deterministic scoring unchanged).

## Test plan

Backend (pytest, offline):
- New `tests/test_founder_review.py`:
  - Production finalise without approval → 409 with "awaiting founder approval".
  - Submit-for-review → founder approves → finalise succeeds; the created run's result JSON is
    identical to the same document finalised on the pre-change code path (fixture comparison).
  - Re-edit after approval → `current_founder_approval` returns None → finalise 409 again;
    re-approval at the new hash unblocks.
  - Non-founder (owner, admin-without-founder-claim) POST founder-approval → 403; unknown
    assessment → 404; finalised assessment → 409.
  - Queue scoping: founder sees all pending production requests; a plain advisor GET queue →
    403; sandbox/demo records never appear in the queue.
  - Approval writes an audit event with the founder as actor.
- `tests/test_assessment_lifecycle.py`: sandbox/demo finalise path byte-identical (no approval
  required, watermark posture unchanged, ADR-0029).
- `tests/test_atlas_engine_golden_master.py` / `_v2.py`: unchanged and green (no scoring edit).
- `tests/test_deliverables.py` / `test_diagnostic_pack.py`: client-facing generation without a
  current founder approval → 409; with approval → 201; internal watermarked draft needs no
  approval; `assert_committee_approved` unit tests retained against the dormant function.
- HTTP retirement tests: every `/rate`-family, `/committee`, `/calibration` route → 410 with
  the ADR-0041 detail; repository-level dual-rating/committee/calibration tests unchanged.
- `tests/test_certification.py`: finalising a production assessment no longer creates
  SHADOW_LOGGED / OBSERVED_LEAD_LOGGED events; `log_shadow_assessment` and OVERRIDE paths still
  do; `_auto_credit_participation` unit test retained against the dormant method.
- `tests/test_bench_scoring.py`: queue never contains RATING_REQUEST or COMMITTEE items.

Frontend (vitest, per-file):
- `frontend/components/workbench/FounderReviewPanel.test.tsx`: queue renders, approve posts,
  empty state.
- `frontend/components/WorkbenchClient.test.tsx`: tab set is bench/certification/learning/arena
  plus Founder review only when `is_founder`.
- Assessment page test: review-status chip renders all four states.

## Out of scope

- Bench queue re-prioritisation beyond removing the two governance items (GRS-0199).
- Any change to scoring, uncertainty, coefficients, or the value bridge.
- Deleting governance tables, contracts, or the stats engine (dormant by decision).
- The report storytelling rebuild (GRS-0189) — this ticket only re-wires which gate the
  existing renderers sit behind.

## Acceptance

- A production assessment can finalise only after a founder approval recorded at the current
  document hash; re-editing invalidates the approval (verified by test).
- A client-facing deliverable cannot generate without a current founder approval (409).
- No peer-rating, committee, or calibration surface is reachable in the UI; their routes
  return 410 with the ADR-0041 reason.
- Certification progression works end-to-end via founder-recorded evidence; no auto-credit
  event is created by finalisation.
- ATLAS golden masters byte-identical; sandbox/demo flows unchanged.
- ADR-0041 Accepted and the Methodology v1.6 amendment merged in the same PR.
