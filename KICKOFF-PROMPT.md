# Claude Code Kickoff Prompt — paste the block below

```
Kick off the Grassmarket project (product name: Bruntsfield Advisor Studio) — the advisor
platform for Bruntsfield Capital Advisory. Working directory: C:\dev\Grassmarket.
This session is Loop 0: scaffold only.

READ FIRST (all local to this repo):
1. CLAUDE.md — the non-negotiables. Follow it exactly.
2. docs/Grassmarket-PRD-v2.md — the product spec.
3. docs/ATLAS-Methodology-v1.md — normative for the scoring engine. Where PRD and
   Methodology disagree, Methodology wins.
4. docs/ATLAS-Feasibility-Deep-Dive-v1.md — the prototype defect register D1–D9.
   The scaffold must make these defects structurally impossible.
5. C:\dev\SD3\CLAUDE.md and C:\dev\SD3\pyproject.toml — the engineering standards to
   inherit; copy the ruff/pytest/pyright tool config verbatim.

LOOP 0 SCOPE:
- git init in this folder, GitHub remote wealthcx01/grassmarket.
- Layout per CLAUDE.md: src/grassmarket/{config,contracts,data,atlas,pipeline,
  deliverables,workbench,earnings,auth,web}, frontend/ (Next.js App Router +
  TypeScript), packages/bcap_contracts/, tests/, docs/adr/, docs/tickets/.
- Python 3.12 + uv + FastAPI + SQLAlchemy + Pydantic v2; ruff/pytest/pyright wired
  into pre-commit. No --no-verify, ever.
- bcap-contracts as a local package holding Pydantic models + JSON Schemas for the
  core resources (entities, engagements, assessments, deliverables, commissions,
  learning) — shaped like the future Holy Corner API per PRD §1.
- Auth skeleton: invitation-based signup, email/password + JWT with role/tier claims,
  data-scoping enforced in a single repository layer (src/grassmarket/data/
  repository.py — no scattered queries). Scoping tests mandatory from day one.
- Write ADR-0001 (scale system 0.2/0.5/0.8/1.0 internal + 0–100 display; single
  module/subcomponent/power/metric key registry; Σθ=1 and α∈[0,1] enforced at load;
  unknown key = refusal to score) and ADR-0002 (value layer: two-track scoring +
  three-layer value bridge; no score-points × currency arithmetic) from the
  Methodology BEFORE writing any engine code.
- Railway deploy skeleton (FastAPI + managed Postgres) with GitHub Actions CI:
  ruff + pytest + pyright must pass.
- Prototype reference (read-only, do NOT copy code blindly — harvest per the
  feasibility report):
  C:\Users\John\OneDrive\BruntsfieldCapital\Business\Advisory\Technology\Assessment Wizard\codespaces-blank
  (most complete copy) and ...\bruntsfield_advisory_assessment_wizard_v2 (git repo,
  behind). Ignore the dpn/jcj/oqh/ryv variant folders.
- If gstack/gbrain tooling is available from wealthcx01 on GitHub, pull it in and
  adopt its workflow (/qa, /review, /ship); otherwise follow the ticket discipline
  manually: one ticket = one branch = one PR, tickets as docs/tickets/GRS-nnnn-title.md.

EXIT CRITERIA (do not exceed scope — Loop 1 is the ATLAS engine, a separate session):
- Repo builds, CI green, pre-commit active.
- A logged-in empty shell deploys to Railway (health endpoint + auth flow working).
- ADR-0001 and ADR-0002 committed.
- Scoping tests passing.

Non-negotiables throughout: fail loud (a missing key or input is an error, never a
default), contract-typed everything, all persistence through the repository layer,
propose-not-execute for anything AI-generated. Work ticket by ticket; start with
GRS-0001-scaffold.
```

## Loop 1 reminder (for the next session, not now)

Before porting any engine code: hand-compute one full assessment in a spreadsheet
(the golden-master fixture). The engine must reproduce it exactly. Then property
tests: monotonicity (raising any subcomponent never lowers V), bottleneck behaviour,
N/A renormalisation, Not-Assessed exclusion. That test suite is what would have
caught every defect in the prototype.
