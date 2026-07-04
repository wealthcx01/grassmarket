# Grassmarket — Bruntsfield Advisor Studio: PRD v2

**Bruntsfield Capital — CONFIDENTIAL — July 2026**

Consolidated Product Requirements Document: product scope, ATLAS engine to Methodology v1, governance workflows, training, engineering standards, build plan. Supersedes Grassmarket PRD v1 and Build Plan v1.

---

## 1. Overview

Grassmarket (product name: **Bruntsfield Advisor Studio**) is the advisor platform of the Bruntsfield Advisory Network: pipeline management, the ATLAS assessment engine, deliverable generation, earnings transparency, and the Workbench (certification, training, practice). This v2 incorporates (a) the ATLAS deep-dive findings (defect register D1–D9, see `ATLAS-Feasibility-Deep-Dive-v1.md`), and (b) **ATLAS Methodology v1, which is normative for the scoring engine: where this PRD and the Methodology disagree, the Methodology wins.**

Decisions in force:

- Standalone app now; connected to Holy Corner (Bruntsfield OS, adapted from Elite Vault System) later via the shared `bcap-contracts` package.
- Edinburgh codenames with plain product names; advisor-first build.
- Repo at `C:\dev\Grassmarket`, off OneDrive; GitHub (wealthcx01) + Railway.
- SD3 engineering standards throughout (gstack workflow, fail-loud, contract-typed, ActiveGraph approval gating on all AI output).

Portals: `advisors.bruntsfieldcapital.com` (this product), `os.bruntsfieldcapital.com` (Holy Corner, phase 2), `clients.bruntsfieldcapital.com` (Viewforth, phase 3). Main site (design tokens: paper/ink palette, Bottle Green `#1A3B26` accent, Source Serif 4 / Inter / IBM Plex Mono) routes login by role.

## 2. Users & Access

Advisory Network consultants in three tiers (Venture Associate, Advisor, Consultant) plus assessor certification levels from the Methodology (Trained / Shadow / Observed Lead / Certified Lead) and committee membership. **Data scoping is absolute:** a consultant sees only their own pipeline, engagements, earnings and assessments; enforced in the repository layer and tested explicitly. JWT auth, invitation-based signup, MFA available; claim shape matches the future Holy Corner SSO.

## 3. ATLAS Assessment Engine

Implements Methodology v1 exactly. Key requirements beyond the prototype:

### 3.1 Data model (per assessment)

- **Subcomponent rating:** level (Basic/Developing/Advanced/Frontier), evidence-strength grade E1–E4, typed evidence artifact links, notes, rater IDs (≥2), consensus flag + dissent note, and first-class Not Applicable (with rationale) / Not Assessed states.
- **Module:** continuous q_m, rule-based rating-gate result, uncertainty band, bottleneck flags (only over assessed items).
- **Powers:** per power — Benefit evidence, Barrier evidence, strength (None/Emerging/Established/Wide), trend, lifecycle plausibility flag, committee approval record. Derived triad ratings (Economic/Perceived/Defence Value) with rationale text.
- **Business metrics:** value + declared unit (never inferred), per-metric normalisation spec reference, confidence.
- **Coefficients:** versioned CoefficientSet validated at load against the single key registry — unknown/missing keys refuse to score (kills defects D1–D7). Σθ=1 and α∈[0,1] enforced. Every coefficient carries its Weight Provenance Record.
- **Scoring runs:** append-only, hashed, storing inputs, engine version, methodology version, coefficient version. Finalisation locks inputs; scenarios stay editable.

### 3.2 Computation

- Deterministic pipeline per Methodology §5 (two-track: continuous scores + rating gates).
- Monte Carlo engine: input distributions from evidence grades → V/L/B/P as P10/P50/P90; tornado and weight-stability outputs rendered into reports.
- Scenario evaluation by full re-scoring (ΔV → Upgrade Priority Index). Value bridge computed as three separated layers (cost £ / lever NPV £ with assumption register / strategic ordinal) — **no cross-domain arithmetic anywhere in the codebase.**

### 3.3 Input paths

- **Path A — wizard:** seven steps (Overview; Business Metrics; Strategic Powers; Module Overview quick pass; Infrastructure Deep Dive; Summary & Interpretation; Scenarios), autosave, save/resume, guidance text from the rubric library, validation, live score panel with uncertainty band.
- **Path B — meeting intelligence:** upload/transcript → transcription → AI extraction to the same intermediate schema with per-field confidence → consultant review/correction → confirm. Identical downstream. All AI extractions are ActiveGraph-gated proposals; acceptance is logged. **Acceptance criterion:** confirmed Path B data scores identically to the same data entered manually.

### 3.4 Governance workflows

- Dual-rater assignment and consensus screen per module.
- Rating Committee queue: approvals for Established/Wide powers, triad ratings, Frontier modules — with rationale and dissent capture.
- Calibration module: quarterly shared-vignette sessions, automatic weighted-kappa (and AC1) computation per anchor, flags anchors below κ 0.6 for rewrite.
- Prediction register + follow-up scheduler (12/24-month re-contact) feeding the validation loop; anonymised benchmark-population ingestion.

## 4. Pipeline Management

Prospect creation (entity-shaped for later Holy Corner sync), kanban stages (Prospect → Workshop Scheduled → Workshop Delivered → Qualified → Scoped → Contracted → Active → Delivered → Closed → Nurture), time-in-stage flags, revenue forecast, workshop management with Pre-Workshop Brief and Workshop Output tracking, Workshop Recovery Fee eligibility (12-month attribution window), engagement detail with deliverables progress and communication log.

## 5. Deliverable Builder

- Template-driven generation (python-docx, SD3 report stack): Executive Summary, Platform Power Report (B/P/L/V + triad ratings with rationale), Infrastructure Heatmap, Modernisation Roadmap (Upgrade Priority Index ranking + value bridge), Technical Appendix, Workshop Output, Score Evolution Report.
- Every deliverable auto-includes: uncertainty statement (ranges + Assessment Uncertainty Rating), tornado/stability summary, assumption register for all currency claims, and the auto-generated methods appendix from provenance records.
- AI first-draft narratives behind ActiveGraph approval policies; quality-review gate for VAs and early Advisors before anything reaches a client.
- Visualisations: radar (modules), heatmap (subcomponents), score evolution, priority-vs-cost scatter.

## 6. The Workbench (training as a first-class product)

- **Certification ladder** mirrors the Methodology's assessor model: Bruntsfield Playbook, ATLAS Methodology (as textbook, with exam), Workshop Delivery, then Shadow → Observed Lead → Certified Lead progression tracked in-product.
- **Practice Arena:** AI-simulated client sessions (Claude role-plays client executives from anonymised profiles); sessions scored against ATLAS extraction completeness with model answers. Calibration vignettes double as arena content — training and inter-rater measurement are the same activity.
- **Power Drills:** spaced-repetition micro-quizzes on the 7 Powers, the triad, the 9 modules and rubric anchors; weekly quiz auto-generated from Briefing publications.
- **Bench-Time Queue:** idle advisors get a prioritised queue — next certification module, an arena scenario, this week's drill, an Opportunity Radar research task (earns sourcing credit). Progress feeds tier progression and quality score.
- **Knowledge Base & Performance:** Briefing archive, case studies, primers, sales journeys (old school / new school); own metrics and trends; opportunity radar.

## 7. My Earnings

Engagement-by-engagement commission breakdown, Workshop Recovery Fees, retainer income, payment status, YTD and projection. **Rates are configuration (per tier and attribution), never code** — exact percentages remain an open commercial item.

## 8. Technical Architecture & Engineering Standards

- **Backend:** Python 3.12 + FastAPI + PostgreSQL (Railway managed) + SQLAlchemy, uv-managed; ruff / pytest / pyright configs copied from SD3. **Frontend:** Next.js App Router + TypeScript with the BC design tokens. **Contracts:** `bcap-contracts` (Pydantic v2 + JSON Schema → generated TS types), shared with future Holy Corner and Viewforth.
- **Fail loud, never fall back:** registry-validated keys, refused scoring on missing data, no `.get(key, default)` in the scoring path. Golden-master test: one full hand-computed assessment fixture the engine must reproduce exactly; property tests (monotonicity, bottleneck behaviour); scoping tests mandatory.
- **ActiveGraph agent layer:** meeting-intelligence extraction, deliverable drafting, practice-arena simulation — all event-sourced with approval policies (AI proposes, consultant approves; a runtime guarantee).
- **gstack workflow:** one ticket = one branch = one PR (GRS-nnnn), ADRs in `docs/adr` (ADR-0001 scale/registry conventions; ADR-0002 value-layer redefinition), pre-commit hooks never bypassed; gbrain pulled from git alongside gstack at scaffold time.
- **Source consolidation precondition:** harvest `codespaces-blank` + `bruntsfield_advisory_assessment_wizard_v2` (OneDrive prototypes) for reference; archive dpn/jcj/oqh/ryv variants; OneDrive is documents-only from then on.

## 9. Build Sequence (PIV Loops)

| Loop | Scope | Exit criterion | Est. |
|---|---|---|---|
| 0 | Scaffold: repo, CI, auth + scoping, bcap-contracts, Railway skeleton; consolidate prototype sources; ADR-0001/0002 ratified | Logged-in shell deployed; CI green | 1 wk |
| 1 | ATLAS engine to Methodology v1: registry, contract-typed CoefficientSet, two-track aggregation, Monte Carlo, value-bridge computation; golden-master + property tests. **Parallel content track:** rubric anchor authoring (204 anchors) and v1 weight elicitation workshops | Engine reproduces hand-computed fixture; elicited v1 CoefficientSet loaded with provenance | 3–4 wks |
| 2 | Wizard Path A (7 steps, autosave, rubric guidance, live scores with ranges) + assessment lifecycle + finalisation locking | Full manual assessment end-to-end with uncertainty outputs | 2–3 wks |
| 3 | Pipeline management + workshop tracking + recovery-fee attribution | Working advisor CRM | 2 wks |
| 4 | Deliverable builder with methods appendix, uncertainty statements, AI drafts behind approval gates | Client-ready Diagnostic pack generated from a real assessment | 2 wks |
| 5 | Workbench: certification ladder, Practice Arena v1, Power Drills, bench queue; calibration module + committee queue + dual-rater consensus | Training live; first calibration session run in-product | 2–3 wks |
| 6 | My Earnings; Path B meeting intelligence; prediction register + follow-up scheduler; hardening, MFA, audit logging | PRD v2 feature-complete | 2–3 wks |

Content work (rubric anchors, elicitation, playbook modules) runs alongside code from Loop 1 — it is the critical path for credibility, not the software.

## 10. Dependencies, Open Items & Risks

| Item | Status / mitigation |
|---|---|
| ATLAS Methodology v1 | Companion document, normative. Rubric library (204 anchors) is the largest content task — begin immediately, founder + early advisors. |
| Weight elicitation panel | Needs 4–8 experts; Delphi + swing-weighting workshops scheduled during Loop 1. |
| gbrain location | Pull from git at Loop 0; adopt where it extends gstack. |
| Commission rates | Config, not code; commercial decision outstanding. |
| Transcription provider (Path B) | Swappable adapter; decide in Loop 6. |
| Holy Corner integration | Deferred by design; contracts package keeps the seam clean. Elite Vault System adaptation is the phase-2 project. |
| Risk: methodology overhead slows early deals | Dual-rating and committees apply to deliverable-bearing engagements; workshops and drafts run lighter. Calibrate process weight to engagement value. |
| Risk: rubric authoring stalls | Anchor-writing sprints with AI-drafted first passes (approval-gated), founder review; κ data from calibration sessions tells us which anchors actually need work. |
