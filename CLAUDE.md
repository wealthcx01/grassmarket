# CLAUDE.md — Grassmarket (Bruntsfield Advisor Studio)

Grassmarket is the advisor platform for the Bruntsfield Advisory Network: pipeline management, the ATLAS assessment engine (7 Powers + Platform Power + 9 infrastructure modules), deliverable generation, earnings, and the Workbench (certification, training, practice arena). Built standalone today; connects to Holy Corner (Bruntsfield OS) via the shared contracts package when it exists.

Normative documents (read before any engine work):
- `docs/Grassmarket-PRD-v2.md` — the product spec.
- `docs/ATLAS-Methodology-v1.md` — normative for the scoring engine. Where PRD and Methodology disagree, **Methodology wins**.
- `docs/ATLAS-Feasibility-Deep-Dive-v1.md` — the prototype audit and defect register D1–D9. The scaffold must make those defects structurally impossible.

## Non-negotiables

1. **This repo lives at `C:\dev\Grassmarket`, off OneDrive.** OneDrive corruption is the failure mode SD3 exists to escape. Same rule here. The OneDrive Technology folder is documents-only.
2. **The methodology is settled: implement it, don't re-invent.** ATLAS scoring implements `docs/ATLAS-Methodology-v1.md` exactly. Changes to scoring are ADRs + new methodology versions, never silent edits.
3. **Fail loud, never silently fall back.** A missing required input, unknown key, or unvalidated coefficient refuses to score. No `.get(key, default)` anywhere in the scoring path. Nothing is fabricated, null-filled, or defaulted around. (Defects D1–D7 in the prototype were all silent fallbacks.)
4. **Contract-typed everything.** Pydantic v2 models + JSON Schemas in `bcap-contracts` for every API resource and scoring output, mirrored to TypeScript. Schemas win on conflict. All module/subcomponent/power/metric keys validate against a single registry at load time (ADR-0001).
5. **All persistence through the repository layer** (`src/grassmarket/data/repository.py`). No scattered queries. The interface is shaped like Holy Corner's future API resources so the backing store can swap from local Postgres to the Holy Corner API without touching feature code.
6. **Scoring runs are immutable and versioned.** Append-only, stored with inputs, engine version, methodology version, coefficient version, and content hash. Finalisation locks inputs; scenarios stay editable.
7. **Two-track scoring, three-layer value bridge (ADR-0002).** Continuous scores prioritise; rule-based rating gates produce headline words; the value bridge prices (cost £ / lever NPV £ / strategic ordinal). Score-points and currency never mix in one equation.
8. **AI proposes, humans approve.** ActiveGraph approval policies gate every AI output: meeting-intelligence extraction, deliverable first drafts, practice-arena feedback. Nothing AI-generated reaches a client without consultant sign-off — a runtime guarantee, not a convention.
9. **Data scoping is absolute.** A consultant sees only their own pipeline, engagements, earnings, and assessments. Enforced in the repository layer, tested explicitly from day one.
10. **Built with gstack; no `--no-verify`; no scope creep.** One ticket = one branch = one PR. Tickets in `docs/tickets/GRS-nnnn-title.md`. ADRs in `docs/adr/` for cross-cutting decisions. Pre-commit hooks (ruff, format, schema-validate, secret-scan) never bypassed. (gbrain: pull from git if available; adopt where it extends this workflow.)

## Stack

- **Backend:** Python 3.12+, FastAPI, PostgreSQL (Railway managed), SQLAlchemy. Managed by `uv` (`uv sync`, `uv run ...`).
- **Frontend:** Next.js (App Router) + TypeScript. Design tokens from the Bruntsfield website design system (paper/ink palette, Bottle Green `#1A3B26` accent, Source Serif 4 / Inter / IBM Plex Mono).
- **Contracts:** `bcap-contracts` local package (Pydantic v2 + JSON Schema → generated TS types).
- **Agent layer:** ActiveGraph (event-sourced, approval policies) + Claude Agent SDK.
- **Computation:** deterministic scoring pipeline + Monte Carlo engine (uncertainty ranges P10/P50/P90) per Methodology §7.
- **Reports:** python-docx templates (SD3 report stack pattern).
- **Quality:** ruff (line-length 100), pytest (offline fixtures, no live calls in CI), pyright (standard). Tool config copied from `C:\dev\SD3\pyproject.toml`.
- **SCM/Deploy:** GitHub (wealthcx01, branch protection, Actions CI) + Railway.

## Layout

```
Grassmarket/
├── src/grassmarket/
│   ├── config.py            # one generation, no version suffixes
│   ├── contracts/           # re-exports from bcap-contracts + app-local models
│   ├── data/repository.py   # single data-access layer (fail-loud)
│   ├── atlas/               # scoring engine per Methodology v1: registry, engine, montecarlo, value_bridge
│   ├── pipeline/            # prospects, stages, workshops, recovery fees
│   ├── deliverables/        # templates, charts, AI drafts (gated), methods appendix
│   ├── workbench/           # certification, drills, practice arena, calibration, bench queue
│   ├── earnings/            # commission views (rates are config, not code)
│   ├── auth/                # invite flow, JWT (Holy Corner claim shape), scoping
│   └── web/                 # FastAPI app + routers
├── frontend/                # Next.js app
├── packages/bcap_contracts/ # shared contracts package
├── tests/                   # pytest; golden-master + property + scoping tests mandatory
├── docs/adr/                # architecture decision records
├── docs/tickets/            # GRS-nnnn-title.md
└── docs/                    # PRD, Methodology, feasibility report (markdown)
```

## Testing rules for the ATLAS engine (Loop 1)

- **Golden master before porting:** one full hand-computed assessment fixture (all modules); the engine must reproduce it exactly.
- **Property tests:** raising any subcomponent never lowers V (monotonicity); raising the min subcomponent raises q_m at least as much as raising the max (bottleneck behaviour); N/A removal renormalises weights; Not Assessed never contributes to any score.
- **Registry tests:** an unknown or missing key in any CoefficientSet is a load-time error.

## Build sequence (PIV loops — see PRD §9)

0. Scaffold, CI, auth + scoping, contracts, Railway skeleton, ADR-0001/0002 →
1. ATLAS engine to Methodology v1 + golden master (parallel: rubric authoring, weight elicitation) →
2. Wizard Path A →
3. Pipeline →
4. Deliverable builder →
5. Workbench + governance (calibration, committee, dual-rater) →
6. Earnings + Path B meeting intelligence + prediction register + hardening.

Prototype harvest sources (reference only, read-only):
`C:\Users\John\OneDrive\BruntsfieldCapital\Business\Advisory\Technology\Assessment Wizard\codespaces-blank` (most complete copy) and `...\bruntsfield_advisory_assessment_wizard_v2` (git repo, behind). The dpn/jcj/oqh/ryv variant folders are superseded — ignore.
