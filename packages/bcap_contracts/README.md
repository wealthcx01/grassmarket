# bcap-contracts

Shared Bruntsfield Capital contracts: Pydantic v2 models + generated JSON Schemas.
This package is the **future Holy Corner API surface** — the resources here are shaped so
Grassmarket's repository layer can swap its backing store from local Postgres to the Holy
Corner API without touching feature code (CLAUDE.md non-negotiable #5).

Two invariants this package exists to guarantee:

- **ADR-0001 — one scale, one registry.** The maturity scale (0.2/0.5/0.8/1.0), the evidence
  grades (E1–E4), and the single key registry (modules / subcomponents / powers / metrics)
  live here and nowhere else. An unknown key is a refusal to score, not a default —
  `CoefficientSet` validates against the registry at load and raises `UnknownKeyError` /
  `MissingKeyError`. This makes prototype defects D1–D7 structurally impossible.
- **ADR-0002 — score and currency never mix.** Score-domain quantities are dimensionless
  `Score` values in `[0,1]`; money is the `Money` type carrying a currency and a mandatory
  assumption-register reference. There is **no** function that takes a `Score` and a `Money`
  and returns a number. The category error is unrepresentable.

## Layout

```
src/bcap_contracts/
├── common.py         # the scale vocabulary + shared enums (ADR-0001 single source)
├── money.py          # Money type + the score/currency boundary (ADR-0002)
├── provenance.py     # WeightProvenanceRecord (Methodology §6)
├── registry.py       # the single key registry loader + typed errors
├── registry_data/    # canonical registry content (YAML): powers (settled), modules (Loop 1)
├── auth.py           # JWTClaims — the Holy Corner SSO claim shape
├── entities.py       # Entity / Prospect (pipeline resource, Holy-Corner-shaped)
├── engagements.py    # Engagement + pipeline stages
├── assessments.py    # CoefficientSet, SubcomponentRating, ScoringRun, ... (the ATLAS surface)
├── deliverables.py   # Deliverable resource
├── commissions.py    # Commission / earnings line
├── learning.py       # Workbench: certification + drill progress
├── schemas.py        # export_all() + check_parity() (drives the pre-commit gate)
└── json_schema/      # committed JSON Schemas — a faithful mirror of the models
```

## Regenerating schemas

```bash
uv run python scripts/generate_schemas.py   # rewrites json_schema/*.json from the models
```

The `schema-validate` pre-commit hook fails if a model changed but the schema was not
regenerated — schemas are always a faithful mirror (non-negotiable #4). No silent drift.
