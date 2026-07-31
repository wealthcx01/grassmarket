# GRS-0184 — Scenario workspace v2

**Status:** OPEN (reconciled 2026-08-01). _Previously recorded as: Planned (2026-07-23, founder feedback item 12). **Priority:** MED-HIGH._
**Loop:** founder-feedback remediation, Wave 1.

## Why

The founder understands what scenarios are for but not what to do with the screen. Today the
step is ephemeral local state: unlabelled rows, one subcomponent change per scenario, results
lost on navigation, no saved scenarios and no comparison over time. Scenarios are the product's
"what should they fix first" engine and deserve a real workspace. (Non-negotiable #6: scenarios
stay editable; only finalised runs are immutable.)

## Scope

The scoring stays exactly where it is: named, saved scenarios are INPUTS that, when evaluated, go
through the existing deterministic `evaluateScenarios` path
(`POST /assessments/{id}/scenarios` → `evaluate_assessment_scenarios`,
`src/grassmarket/web/routers/assessments.py` line 304; `api.evaluateScenarios`,
`frontend/lib/api.ts` line 407) unchanged. This ticket adds persistence and a workspace UI around
that path. Scenarios are editable saved records, never immutable runs — so they are a normal
owner-scoped child of an assessment, not a scoring run.

1. **Contract — a saved-scenario resource.** New model in
   `packages/bcap_contracts/src/bcap_contracts/` (add to the existing scenarios/assessment contract
   module, or a new `scenarios.py`; wire into `schemas.py`):
   - `SavedScenario(OwnedResource)` (subclassing `OwnedResource` from `base.py`, which supplies
     `id`, `owner_consultant_id`, `created_at`, `updated_at`), `model_config =
     ConfigDict(extra="forbid")`, fields:
     - `assessment_id: UUID`
     - `name: str = Field(min_length=1, max_length=120)`
     - `changes: tuple[ScenarioChange, ...] = Field(min_length=1)` — the multi-change payload.
   - `ScenarioChange(BaseModel, extra="forbid", frozen=True)`:
     `subcomponent_key: str`, `module_key: str`, `target_level: MaturityLevel`. Decision: store the
     KEY + target level, not a whole `AssessmentDocument`, because a scenario is "raise these
     subcomponents to these levels against the current baseline" — persisting a full document snapshot
     would silently freeze a baseline that non-negotiable #6 says must stay live. The document is
     reconstructed at evaluate time from the current assessment doc plus the changes (exactly as the
     current `ScenariosStep` builds it via `doc.setSub`/`doc.subAssessed`).
   - Register `SavedScenario` (and `ScenarioChange` if it needs its own schema) in
     `EXPORTED_MODELS` in `schemas.py`, run `uv run python scripts/generate_schemas.py`, and add the
     hand-written TS mirror `SavedScenario` / `ScenarioChange` to `frontend/lib/types.ts` (schema-
     parity CI is the gate). The existing ephemeral `ScenarioComparison`/`NamedScenario` types are
     untouched — evaluation still returns `ScenarioComparison`.

2. **ORM + migration.** New `SavedScenarioORM` in `src/grassmarket/data/models.py`
   (`__tablename__ = "saved_scenarios"`), columns: `id` (`sa.Uuid`, PK), `owner_consultant_id`
   (`sa.Uuid`, FK `consultants.id`, not null), `assessment_id` (`sa.Uuid`, FK `assessments.id`, not
   null), `name` (`sa.String`, not null), `changes` (`sa.JSON`, not null — the list of
   `{subcomponent_key, module_key, target_level}`), `created_at`/`updated_at`
   (`sa.DateTime(timezone=True)`). New migration
   `migrations/versions/0032_saved_scenarios.py` (down_revision `0031_drill_card_prompt_answer`):
   `op.create_table("saved_scenarios", ...)` with an index on `owner_consultant_id` and one on
   `assessment_id`; `downgrade()` drops the table. Decision: `changes` as a JSON column, not a child
   table, because a scenario's changes are a small, always-loaded-together list with no independent
   identity or query need — a child table adds joins for no benefit.

3. **Repository methods** (`src/grassmarket/data/repository.py`, new section, all fail-loud, all
   through `_require_assessment` / `_assert_can_access`, mirroring the `create_contact` /
   `list_contacts` / `delete_contact` group at lines 717-812):
   - `create_saved_scenario(principal, assessment_id, *, name, changes) -> SavedScenario`:
     `_require_assessment` (owner/admin gate + `NotFoundError`); validates each change's keys against
     the assessment's registry VIEW (unknown key → `ConflictError`, never a silent skip — fail loud
     per house rules and defect D-class); writes `SavedScenarioORM(owner_consultant_id=
     assessment.owner_consultant_id, assessment_id=..., name=..., changes=[...])`; `add`+`flush`;
     returns `_to_saved_scenario(row)`. Does NOT refuse on a finalised assessment — scenarios stay
     editable against a finalised baseline (non-negotiable #6; a finalised RUN is immutable, a
     scenario over it is exploratory).
   - `list_saved_scenarios(principal, assessment_id) -> list[SavedScenario]`: `_require_assessment`
     gate, `select(SavedScenarioORM).where(assessment_id == ...).order_by(created_at)`.
   - `delete_saved_scenario(principal, scenario_id) -> None`: load row → `NotFoundError` if absent →
     `_assert_can_access(principal, row.owner_consultant_id)` → `session.delete` + `flush`.
   - (No update method: editing a saved scenario is delete-and-recreate from the UI, which keeps the
     repository surface minimal; a rename/edit is a fresh save. Decision recorded so a reviewer does
     not expect a PATCH.)

4. **Endpoints** (`src/grassmarket/web/routers/assessments.py`). The evaluate endpoint keeps its
   path; the CRUD endpoints use a distinct sub-path so there is no collision with
   `POST /assessments/{id}/scenarios` (evaluate):
   - `POST /assessments/{id}/saved-scenarios` → 201 `SavedScenario`; body `{name, changes}`; 404
     unowned/unknown assessment; 409 on an unknown subcomponent/module key (fail loud); 422 on an
     empty `changes` or blank `name` (contract validation).
   - `GET /assessments/{id}/saved-scenarios` → 200 `list[SavedScenario]` (owner-scoped; a second
     consultant gets 404 on the assessment, never another advisor's scenarios).
   - `DELETE /assessments/{id}/saved-scenarios/{scenario_id}` → 204; 404 if the scenario is unknown
     or not the caller's. Decision: `DELETE` returns 204 (no body) per REST norm; the UI drops the
     row on success.
   The existing `POST /assessments/{id}/scenarios` evaluate endpoint is unchanged; the workspace
   calls it with the reconstructed documents exactly as today.

5. **`api.ts` additions** (`frontend/lib/api.ts`): `saveScenario(id, {name, changes})`,
   `listSavedScenarios(id)`, `deleteSavedScenario(id, scenarioId)`, all with `authHeaders()` and an
   optional `AbortSignal`, mirroring the existing method shapes. `evaluateScenarios` is untouched.

6. **Workspace UI — rebuild `ScenariosStep`** (`frontend/components/steps.tsx`, currently lines
   1393-1508, ephemeral local state). New structure, presentation over the repository-backed data:
   - **On mount:** `listSavedScenarios(assessmentId)` populates the saved list. Each saved scenario
     is a named card showing its changes ("Order & Execution Management → Advanced; Risk Controls →
     Frontier") with Evaluate and Delete actions.
   - **Multi-change editor:** a scenario under construction holds an array of `{subcomponent_key,
     target_level}` rows (the current single-row control generalised to N rows with add/remove),
     plus a required Name field, and a Save button that calls `saveScenario`. The current one-change
     limit is removed — a scenario is several subcomponent upgrades evaluated together.
   - **Guided "start from the bottleneck" seed:** a one-click action that pre-fills the editor with
     the current weakest module's critical subcomponent(s) raised one level, read from the live
     score the step already has access to (`live.module_qm` weakest, matching the bottleneck logic in
     `LiveScorePanel`/`Interpretation`). Decision: seed the weakest module's critical subcomponent at
     one level above its current rating (the smallest meaningful, defensible upgrade), so the first
     scenario an advisor sees is the highest-leverage realistic fix, not a blank form.
   - **Plain-language result framing:** after Evaluate, show "If Revolut fixed Order & Execution
     Management to Advanced, V moves 60.5 → 63.1" alongside the existing ΔV priority bars, computed
     from the returned `ScenarioComparison` (`baseline_v`, `priority_index[*].delta_v`) — no new
     maths, just prose over the existing numbers.
   - **Comparison table:** a side-by-side table of the saved scenarios against the baseline: columns
     Scenario name · modules touched · baseline V · scenario V · ΔV, sorted by ΔV descending. Built by
     evaluating the saved scenarios through the unchanged `evaluateScenarios` path (one call carrying
     all saved scenarios as `NamedScenario`s, reconstructing each document from the current baseline +
     its `changes`) and joining the returned `priority_index`/comparison to the saved names.
   - **Empty state that teaches** (STYLE-VOICE register): when no scenarios are saved, explain what
     the step is for ("model what to fix first, and rank the fixes by how much they move Platform
     Value") with the guided-seed button as the first action. Replaces today's bare "Build candidate
     upgrades" paragraph on an empty screen.
   - Navigation no longer loses work: saved scenarios persist server-side; the in-progress editor may
     stay local (a half-built, unsaved scenario is transient by design), but everything Saved
     survives leaving and returning to the step.

## Test plan

Backend pytest (offline); frontend vitest per file; `pyright`, `ruff`, `tsc`, `ESLint`, and
schema-parity CI (`scripts/validate_contracts.py`) the standing gate.

1. New `tests/test_saved_scenarios.py`:
   - **Round-trip:** create a scenario with two changes → list returns it with both changes and the
     name; delete → list is empty.
   - **Multi-change persisted:** `changes` with three entries survives save/list byte-equal.
   - **Owner scoping (negative):** consultant B `GET /assessments/{A's id}/saved-scenarios` → 404;
     B cannot `DELETE` A's scenario (404); create under A's assessment as B → 404. Prove no
     cross-consultant leakage at the repository AND router level.
   - **Fail loud on unknown key:** create with a `subcomponent_key` not in the assessment's registry
     view → 409 (never a silent drop); empty `changes` → 422; blank `name` → 422.
   - **Editable against finalised baseline:** creating/listing scenarios on a FINALISED assessment
     succeeds (non-negotiable #6) — a scenario is not a mutation of the locked run.
   - **Evaluate path unchanged:** a saved scenario reconstructed to a document and sent through
     `evaluate_scenarios` yields the same `ScenarioComparison` as the equivalent ad-hoc scenario did
     before this ticket (fixture comparison — proves the engine path is byte-identical).
2. `tests/test_atlas_engine_golden_master.py` — unchanged and green (no scoring edit anywhere).
3. Schema parity: `uv run python scripts/validate_contracts.py` passes with `SavedScenario` /
   `ScenarioChange` exported and mirrored.
4. Frontend `bunx vitest run frontend/components/steps.test.tsx` (extend) — `ScenariosStep`:
   - Empty state renders the teaching copy and the guided-seed button; no saved list.
   - Saving a two-change scenario calls `api.saveScenario` with `{name, changes:[...]}` and, on
     success, the scenario appears in the saved list.
   - The guided "start from the bottleneck" seed pre-fills the editor with the weakest module's
     critical subcomponent raised one level (assert against a mocked `live.module_qm`).
   - Evaluate renders the plain-language "V moves X → Y" line and the ΔV bars from a mocked
     `ScenarioComparison`.
   - The comparison table lists saved scenarios sorted by ΔV descending.
   - Delete calls `api.deleteSavedScenario` and removes the row.

## Out of scope

- Any change to the scoring engine, `evaluate_scenarios`, the Monte Carlo, or the value bridge —
  evaluation uses the existing deterministic path unchanged (one-ticket-one-PR).
- Cross-assessment or portfolio-level scenario comparison; scenarios are scoped to one assessment.
- A PATCH/rename endpoint (edit = delete + recreate, by decision §3).
- Persisting the in-progress (unsaved) editor state across navigation — only Saved scenarios persist.
- Currency/value-bridge output in the workspace; the step stays score-domain only (ΔV), as today.

## Acceptance

An advisor can build a multi-change scenario, name it, save it, evaluate it, and see a plain-language
"V moves X → Y" plus a ΔV ranking; saved scenarios survive leaving and returning to the step; a
one-click "start from the bottleneck" seeds the highest-leverage fix; a comparison table ranks saved
scenarios by ΔV against the baseline. Scenarios are owner-scoped (a second consultant sees none,
proven by test) and remain editable even on a finalised assessment. The engine path and the golden
master are untouched.

---

## Status reconciliation — 2026-08-01

**OPEN.** No implementing commit on main; genuinely unbuilt.
