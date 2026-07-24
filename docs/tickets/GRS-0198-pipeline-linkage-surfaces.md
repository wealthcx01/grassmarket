# GRS-0198 — Pipeline linkage: assessment & deliverable milestones on the pipeline

**Status:** Planned (2026-07-23, founder feedback item 19). **Priority:** MED-HIGH.
**Loop:** founder-feedback remediation, Wave 5.

## Why

The founder asked whether Portfolio, Wizard and Deliverables updates are "linked and updated to
the Pipeline". Honest answer, verified in source: no — finalising an assessment or generating a
deliverable never touches pipeline state; stage moves happen only through the explicit stage
endpoint. The linkage exists in the data (prospect → engagement → assessment → deliverables) but
the pipeline surface shows none of it.

## Scope

1. **Linkage summary contract.** New Pydantic model `ProspectLinkageSummary` in
   `packages/bcap_contracts/src/bcap_contracts/pipeline.py`: `engagement_id: UUID | None`,
   `linked_assessment_count: int`, `finalised_assessment_count: int`,
   `latest_assessment_state: str | None` (`draft` | `finalised`),
   `latest_completeness: float | None` (draft % when the newest linked assessment is a draft),
   `latest_v: float | None` and `latest_c: str | None` (headline V and rating class when the newest
   is finalised), `deliverable_count: int`. `PipelineBoardEntry` gains
   `linkage: ProspectLinkageSummary` (default empty). Regenerate the JSON schema and mirror both
   interfaces into `frontend/lib/types.ts`. Decision: read-computed at board build time, **no new
   denormalised columns** — the linkage already lives in the data.
2. **Board builder threading (pure).** `src/grassmarket/pipeline/service.py` `_board_entry`/
   `build_board` (~41–59) accept an optional `linkage: Mapping[UUID, ProspectLinkageSummary]` and
   attach the matching summary to each entry (empty summary when absent). The module stays pure (no
   db/clock); the repository computes the map. Repository method `_linkage_for_prospects(principal,
   prospects) -> dict[UUID, ProspectLinkageSummary]` fetches the owner's engagements + their linked
   assessments + deliverable counts in bulk (no N+1), keyed by prospect_id, and the board endpoint
   passes it into `build_board`.
3. **Milestone chips (frontend).** `frontend/components/KanbanBoard.tsx` deal cards and
   `frontend/components/DealDetailPanel.tsx` render, from `entry.linkage`: an assessment chip —
   "Assessment: draft {n}%" or "Assessment: finalised V {v} · {C}" — and a "{k} deliverables" chip
   when `deliverable_count > 0`. No chip renders when nothing is linked (honest blank, never a
   fabricated zero-state that implies work exists). The chips in `DealDetailPanel` link to the
   engagement (`/engagements/{engagement_id}`).
4. **Stage-advance suggestions — never silent moves.** A finalised linked assessment (or the first
   client-facing deliverable) produces a *suggestion*, not a mutation. New pure helper
   `stage_suggestions(prospect, linkage) -> list[StageSuggestion]` in `service.py`, with the
   mapping: newest linked assessment finalised AND `prospect.stage` earlier than `SCOPED` → suggest
   `SCOPED`; first client-facing deliverable exists AND stage earlier than `CONTRACTED` → suggest
   `CONTRACTED`. New contract `StageSuggestion{ prospect_id: UUID, kind: StageSuggestionKind
   (assessment_finalised | client_deliverable_generated), suggested_stage: PipelineStage,
   message: str }`. The advisor confirms through the **existing** `PATCH /prospects/{id}/stage`
   choke-point (repository `update_prospect_stage`, ~614) — this ticket adds **no** auto-mutation,
   so stage history stays a true record of advisor decisions (fail-loud / honest-history).
5. **Where the prompt state lives (decided).** Dismissals persist **server-side**, not in client
   localStorage: migration `migrations/versions/00xx_stage_suggestion_dismissals.py` (next free
   number after rebasing) — table `stage_suggestion_dismissals` (id, owner_consultant_id,
   prospect_id, kind, dismissed_at, created_at; unique on (prospect_id, kind)). Reason: a dismissal
   is a per-advisor decision that must survive devices and reloads, and it belongs with the honest
   record, not in a browser. A suggestion is suppressed when a matching dismissal exists **or** when
   the stage has already advanced past the threshold (so acting on it clears it naturally — no stale
   prompt). Repository `list_stage_suggestions(principal)` (self-scoped; computes suggestions from
   linkage, filters dismissed/satisfied) and `dismiss_stage_suggestion(principal, prospect_id,
   kind)`.
6. **Endpoints** (`src/grassmarket/web/routers/pipeline.py`):
   - `GET /pipeline/stage-suggestions` → 200 `list[StageSuggestion]` (self-scoped).
   - `POST /pipeline/stage-suggestions/dismiss` body `{ prospect_id, kind }` → 200; 404 when the
     prospect is not the caller's; idempotent (re-dismiss is a no-op 200).
   The board endpoint returns `linkage` inline (no new endpoint for chips).
7. **Reverse links.** Engagement detail (`frontend/app/engagements/[id]/page.tsx`) and the
   assessment/wizard finalise rail show the prospect's current stage as a chip linking to
   `/prospects/{prospect_id}` (read from the engagement's `prospect_id` → `api.getProspect`).
8. **Frontend suggestion surface.** `frontend/app/pipeline/page.tsx` renders a non-blocking banner
   per outstanding suggestion — e.g. "Revolut's assessment is finalised. Move to Scoped?" — with
   "Move to {stage}" (calls `api.updateProspectStage`) and "Dismiss" (calls the dismiss endpoint);
   the banner does not reappear once dismissed or acted on.

## Test plan

Backend (pytest, offline):
- `tests/test_pipeline_lifecycle.py` additions:
  - `build_board` attaches the correct `ProspectLinkageSummary` (draft % vs finalised V·C, correct
    counts) and an empty summary for a prospect with no engagement.
  - `_linkage_for_prospects` is bulk (assert query behaviour / no per-prospect fan-out) and
    owner-scoped (advisor B's engagement never contributes to advisor A's board).
- New `tests/test_stage_suggestions.py`:
  - A finalised linked assessment on a `PROSPECT`-stage deal yields a `SCOPED` suggestion; the same
    on an already-`SCOPED`-or-later deal yields none.
  - **No auto-mutation:** after finalisation the prospect's stage is unchanged until an explicit
    `PATCH /stage`; stage history has no new row from finalisation.
  - A first client-facing deliverable yields a `CONTRACTED` suggestion (below threshold) and none
    above it.
  - Dismiss suppresses the suggestion; it does not reappear on the next `GET`; advancing the stage
    past the threshold also clears it.
  - Scoping: advisor B has no suggestions for advisor A's prospects; `POST /dismiss` on a foreign
    prospect → 404.

Frontend (vitest, per-file):
- `bunx vitest run frontend/components/DealDetailPanel.test.tsx`: renders the assessment chip
  (draft % and finalised V·C variants) and the deliverable-count chip; no chip when linkage is
  empty; the chip links to the engagement.
- `bunx vitest run frontend/app/pipeline/page.test.tsx`: the suggestion banner renders, "Move"
  calls `updateProspectStage`, "Dismiss" calls the dismiss endpoint, and the banner does not
  reappear after either action.

## Out of scope

- Any automatic stage mutation on finalisation or deliverable generation (explicitly forbidden).
- Bench-queue re-prioritisation (GRS-0199) and the founder review gate (GRS-0188).
- New denormalised linkage columns — linkage is computed at read.
- One ticket = one branch = one PR; contract regeneration + the migration ship in this PR.

## Acceptance

A finalised assessment and its deliverable count are visible on the deal card and detail panel
without opening the wizard; when an assessment finalises the pipeline shows a non-blocking
"move stage?" prompt that the advisor must confirm; stage changes appear in history only when an
advisor confirmed them; a dismissed or acted-on prompt does not repeat; all new reads are
owner-scoped with passing cross-advisor negatives.
