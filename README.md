# Grassmarket — Bruntsfield Advisor Studio

The advisor platform for the Bruntsfield Advisory Network: pipeline management, the **ATLAS**
assessment engine (7 Powers + Platform Power + 9 infrastructure modules), deliverable
generation, earnings, and the Workbench. Built standalone today; connects to Holy Corner
(Bruntsfield OS) via the shared `bcap-contracts` package later.

> **Loop 0 (this scaffold):** repo, CI, auth + absolute data scoping, the `bcap-contracts`
> package with the single key registry and the score/currency type boundary, and the FastAPI
> shell. **No scoring engine yet** — that is Loop 1. See `docs/tickets/GRS-0001-scaffold.md`.

## Read order

1. [`CLAUDE.md`](CLAUDE.md) — the non-negotiables.
2. [`docs/Grassmarket-PRD-v2.md`](docs/Grassmarket-PRD-v2.md) — the product spec.
3. [`docs/ATLAS-Methodology-v1.md`](docs/ATLAS-Methodology-v1.md) — normative for scoring.
4. [`docs/ATLAS-Feasibility-Deep-Dive-v1.md`](docs/ATLAS-Feasibility-Deep-Dive-v1.md) — the
   prototype defect register D1–D9 the scaffold makes impossible.
5. [`docs/adr/`](docs/adr/) — ADR-0001 (scale + registry) and ADR-0002 (value layer).

## Stack

- **Backend:** Python 3.12+, FastAPI, SQLAlchemy, PostgreSQL (Railway) / SQLite (local, CI),
  managed by `uv`.
- **Contracts:** `bcap-contracts` (Pydantic v2 + JSON Schema), a local workspace package.
- **Frontend:** Next.js (App Router) + TypeScript — see [`frontend/`](frontend/).
- **Quality:** ruff (line-length 100), pytest, pyright (standard); pre-commit gate never
  bypassed.

## Two invariants the scaffold guarantees structurally

- **ADR-0001 — one scale, one registry.** An unknown module/subcomponent/power/metric key is a
  *refusal to score*, not a default. `CoefficientSet` validates against the registry at load
  (Σθ=1, α∈[0,1], completeness, mandatory provenance). Makes prototype defects D1–D7 impossible.
- **ADR-0002 — score and currency never mix.** Score-domain values are dimensionless `[0,1]`;
  money is the `Money` type with a currency and a mandatory assumption-register reference. No
  function takes a score and a `Money` and returns a number. The category error is
  unrepresentable.

## Develop

```bash
uv sync --all-extras                       # create the venv, install workspace + dev deps
cp .env.example .env                        # then set GM_JWT_SECRET (fail-loud if absent)
uv run python scripts/generate_schemas.py   # regenerate JSON Schemas from the models
uv run ruff check . && uv run pyright && uv run pytest -q   # the local gate
uv run uvicorn grassmarket.web.main:app --reload            # http://localhost:8000/health
pre-commit install                          # the hooks that CI also enforces
```

Frontend:

```bash
cd frontend && npm install && npm run dev    # http://localhost:3000
```

## Layout

```
src/grassmarket/       # config, contracts, data (repository), atlas (Loop 1), pipeline,
                       # deliverables, workbench, earnings, auth, web (FastAPI)
packages/bcap_contracts/  # shared Pydantic + JSON Schema contracts (the Holy Corner surface)
frontend/              # Next.js App Router shell
tests/                 # scoping, registry, coefficient-invariant, ADR-compliance, auth tests
docs/adr/              # architecture decision records (ADR-0001, ADR-0002)
docs/tickets/          # GRS-nnnn-title.md — one ticket = one branch = one PR
```

## Discipline

One ticket = one branch = one PR (`GRS-nnnn`). ADRs are immutable once Accepted — a change is a
new ADR. Pre-commit hooks (ruff, format, schema-validate, secret-scan) are **never** bypassed;
no `--no-verify`, ever.
