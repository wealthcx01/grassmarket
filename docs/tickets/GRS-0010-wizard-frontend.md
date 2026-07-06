# GRS-0010 — Wizard Path A frontend

- **Loop:** 2 (see PRD §9) — **the last Loop 2 ticket; this closes Loop 2.**
- **Branch:** `grs-0010-wizard-frontend`
- **Status:** In review
- **Normative source:** PRD §3 (the seven wizard steps); `docs/ATLAS-Methodology-v1.2.md` §7;
  ADR-0002 (score/currency separation), ADR-0008 (honest uncertainty labelling).
- **Depends on:** GRS-0009 (assessment lifecycle + API), GRS-0006 (value layer), GRS-0008 (rubric).

## Goal

The consultant-facing Wizard for Path A (manual entry): a seven-step assessment that autosaves,
scores live with honest uncertainty bands, ranks upgrade scenarios by ΔV, and finalises to a locked
immutable result. Plus the one thin backend addition Path A needs — scenario evaluation.

## What shipped

### Backend (thin addition)

1. **Scenario-evaluation endpoint** `POST /assessments/{id}/scenarios` — given a scoreable baseline
   and a list of named scenario documents, returns each scenario's ΔV/ΔL/ΔB/ΔP and the **Upgrade
   Priority Index** (ranked by ΔV). Score domain only — no currency; the ADR-0002 AST guard stays
   green (`grassmarket/assessments` is in the scan set). Scoped through the repository (cross-owner →
   404) and evaluated by the same document→inputs completion as live-score (unrated → Not Assessed).
   Contract: `ScenarioComparison` (`bcap_contracts.value`, schema-parity mirrored).
2. **Registry endpoint** `GET /registry` — the module/subcomponent/metric/power structure the wizard
   renders its forms from (one source of truth, the ADR-0001 registry). Authenticated, not
   owner-scoped (shared content).
3. `LiveScore` gained the **triad ordinals** (`triad_economic/perceived/defence`) so the Summary step
   can show Platform Power without a second round-trip.

### Frontend (Next.js App Router + TypeScript)

4. **Contract-typed TS mirrors** (`frontend/lib/types.ts`) — hand-written, field-for-field with the
   Pydantic contracts (the backend JSON Schemas remain the source of truth). Typed `api` client
   (`frontend/lib/api.ts`) carrying the JWT on every call; immutable `AssessmentDocument` helpers
   (`frontend/lib/doc.ts`).
5. **The seven steps** (`frontend/components/steps.tsx`, PRD §3): Overview; Business Metrics;
   Strategic Powers; Module Overview (quick pass); Infrastructure Deep Dive; Summary &
   Interpretation; Scenarios. **Not Assessed / Not Applicable are first-class choices** — a
   subcomponent can be left unrated, and unrated ≠ zero.
6. **Autosave + resume** (`WizardClient.tsx`): every edit debounce-autosaves (800 ms) against
   `PUT /assessments/{id}`; a partial document is always valid and never blocks. Resume loads the
   saved document via `GET /assessments/{id}`. A finalised assessment renders read-only.
7. **Live-score panel** (`LiveScorePanel` + `BandDisplay`): renders V/L/B/P and per-module q_m.
   **The §7/ADR-0008 honesty guarantee is enforced in the UI** — `BandDisplay` delegates to
   `describeBand`, and a band with `modelled=false` renders as a **labelled POINT**
   ("uncertainty not modelled"), never a tight range. Covered by a component unit test.
8. **Rubric guidance** (`GuidancePanel`): fetches the guidance endpoint per subcomponent and shows
   all four anchors including `todo` ones as "Guidance not yet authored" — never a blank.
9. **Scenarios step**: build candidate upgrades, call `POST /{id}/scenarios`, show the ΔV ranking
   (Upgrade Priority Index). **Finalisation**: finalise → lock → show the immutable result (V with
   band, triad ordinals), inputs read-only thereafter.
10. **Design tokens**: paper/ink palette, Bottle Green `#1A3B26`, Source Serif 4 / Inter / IBM Plex
    Mono — all via the existing CSS variables in `app/globals.css`.

## Tests

- **Backend:** scenarios rank by ΔV; an unscoreable baseline reports `scoreable:false` with blockers
  (not a 500); scenarios are scoped (cross-owner → 404); the registry endpoint returns the expected
  structure (9 modules / 51 subcomponents / 10 metrics / 7 powers) and requires authentication. The
  ADR-0002 AST scan now covers `grassmarket/assessments`. (171 backend tests pass.)
- **Frontend:** `BandDisplay.test.tsx` proves `modelled=false` renders a labelled point (not a band),
  `modelled=true` renders a range, and `null` renders neither — the honesty guarantee as an assertion.
  `npm test` (vitest) is now a CI step alongside type-check + lint.

## Exit criteria (closes Loop 2)

A consultant completes a full manual assessment through the wizard; autosave/resume works; live
scores show ranges with honest B/P labelling; the Scenarios step ranks by ΔV; finalisation locks.
Frontend `type-check` + `lint` + `test` and the full backend gate are green.

## Non-negotiables honoured

Data scoping stays server-enforced (the client only carries the JWT and shows the user's own work);
contract types drive the TS types; Path A is manual entry (no AI in this path); one ticket = one
branch = one PR.
