# GRS-0193 — Import the GTM contact databases

**Status:** Planned (2026-07-23, founder feedback item 16a). **Priority:** HIGH within Wave 5 —
it unblocks GRS-0194 and the GRS-0199 radar wiring. **Loop:** founder-feedback remediation,
Wave 5. Carries ADR-0045 (target & contact registry; extends ADR-0027). Supersedes the scope of
the planned GRS-0115. Consumes GRS-0200 (the dataset already pulled).

## Why

The GTM data exists as operator files and needs to live in the product: the Exchange Supplier
List v2 (1,001 audited supplier-service rows with contacts, URLs, LinkedIn), the List of Banks
(150 institutions), the Barclays Live influencer map (the LSEG 3-tab shape), and — since
2026-07-23 — the network-wide **LSEG analyst roster dataset** pulled via bcap-lseg (GRS-0200:
1,754 rows / 53 RICs / 134 contributor banks, committed in-repo at `data/gtm/lseg/`).
Today prospects are typed by hand against a 15-row in-repo stub (`StubEntityRegistry`,
`src/grassmarket/entities/registry.py`) and the Bench radar has nothing external to draw on.

## Design decision (the seam)

Import **behind the existing `EntityRegistry` port** (ADR-0033), not as a parallel store. The
port already has one documented swap point — `active_entity_registry()` — used by the
`/entities` search endpoint and the wizard's `EntitySubjectField`. This ticket ships a
DB-backed adapter that implements the same `search()`/`get()` protocol, so Add-prospect
autocomplete, subject resolution, and the radar all read the imported universe through the
unchanged seam. The contacts side is a **new network-shared registry table**, kept distinct from
the existing per-prospect `contacts` table (`ContactORM`, advisor-owned pipeline data) because
the two have different scoping (shared read vs owner-private) and different lifecycles.

## Scope

1. **Contracts** (`packages/bcap_contracts/src/bcap_contracts/entities.py`, alongside
   `CompanyEntity`):
   - `RegistryTarget(BaseModel, extra="forbid")`: `target_id: str` (slug), `name: str`,
     `aliases: tuple[str, ...]`, `domain: str | None`, `segment: str | None`,
     `country: str | None`, `ric: str | None` (nullable — the LSEG grouping RIC where known),
     `ctb_id: int | None`, `source: str` (dataset provenance token), `imported_on: date`.
   - `RegistryContact(BaseModel, extra="forbid")`: `contact_id: str`, `target_id: str`,
     `full_name: str`, `email: str | None`, `phone: str | None`, `job_role: str | None`,
     `linkedin: str | None`, `verified: bool = False`, `source: str`, `imported_on: date`.
   `CompanyEntity` is produced from a `RegistryTarget` by a pure adapter (name/aliases/domain/
   segment carry over), so the search port contract is unchanged. Register both in `schemas.py`
   `EXPORTED_MODELS`, regenerate JSON schema, mirror TS interfaces into `frontend/lib/types.ts`.

2. **ORM + migration.** `RegistryTargetORM` (`registry_targets`) and `RegistryContactORM`
   (`registry_contacts`) in `src/grassmarket/data/models.py`. `registry_targets`: target_id
   (PK, str), name, aliases (JSON), domain, segment, country, ric, ctb_id, source, imported_on,
   created_at, updated_at; indexes on `name` and `ctb_id`. `registry_contacts`: contact_id (PK),
   target_id (FK `registry_targets.target_id`, indexed), full_name, email, phone, job_role,
   linkedin, verified (bool), source, imported_on, created_at; index on `target_id`. Migration
   `migrations/versions/00xx_gtm_registry.py` (next free number after rebasing onto the merged
   head — GRS-0184/0188/0197/0198 also add migrations; do not pin `0032`). Decision: `aliases`
   as a JSON column, not a child table, matching the stub's shape and query pattern.

3. **Repository methods** (`src/grassmarket/data/repository.py`), all fail-loud:
   - `upsert_registry_target(target)` / `upsert_registry_contact(contact)` — idempotent by PK
     (import re-run overwrites the same row, never duplicates); used only by the ingest layer
     (admin/operator context), not by advisor-facing routes.
   - `search_registry_targets(query, *, limit)` and `get_registry_target(target_id)` — the
     data behind the DB `EntityRegistry` adapter; ranking reuses the stub's exact>prefix>alias
     logic (`_rank`), so behaviour is identical to today, only the corpus is larger.
   - `list_registry_contacts(target_id)` — the contacts for an institution (network-shared
     read; any authenticated consultant may read the shared universe, per ADR-0045 scoping).
   Registry reads are **network-shared** and take no owner filter; this is the one deliberate
   exception to owner-scoping (ADR-0045 §2), tested explicitly so it cannot leak into
   owner-scoped resources.

4. **DB entity-registry adapter.** New `DbEntityRegistry` in `src/grassmarket/entities/registry.py`
   implementing the `EntityRegistry` Protocol over the repository. `active_entity_registry()`
   returns it when the `registry_targets` table is populated, else the stub (so a fresh dev DB
   still works). Decision: merge — the adapter unions the imported targets with the stub seed on
   an empty overlap, so the demo subjects (Revolut/HL/WeBull) never disappear.

5. **Ingest scripts** (operator/admin-run, reading the committed files under `data/gtm/`), one
   per source shape, each fail-loud on malformed rows with a per-import summary
   (`{rows_read, targets_upserted, contacts_upserted, skipped: [...reasons]}`):
   - `scripts/import_exchange_suppliers.py` — `data/gtm/sources/exchange-supplier-list.xlsx`
     (`Supplier`, `Supplier Service`, `Content Type`, audited contact/URL/LinkedIn columns) → one
     target per supplier, contacts from the audited `Contact Name`/`Email`/`LinkedIn` columns.
   - `scripts/import_bank_list.py` — `data/gtm/sources/list-of-banks.xlsx` (150-row
     `Country, Company`) → targets only (no contacts), `segment="Bank"`.
   - `scripts/import_lseg_rosters.py` — `data/gtm/lseg/analysts_unified.csv` +
     `data/gtm/lseg/contributor_institution_map.csv`: one target per `ctb_id` (name from the
     curated institution map, `ric` and `ctb_id` set), one contact per named analyst row.
     **Applies the GRS-0200 caveats:** decode the epoch-nanosecond `rec_rating_24m`, drop the 311
     anonymous slots (blank `analyst_name`), and treat `<NA>`/`NaT` as null.
   - `scripts/import_barclays_influencer.py` — the 3-tab workbook → the Barclays target + its
     analyst and owner contacts, owner rows carrying `verified` from the workbook's verification
     column.
   Each script is idempotent (re-run overwrites by PK), reads its path from an argument or env
   var (never a committed path), and prints its summary. Column-mapping constants live in the
   script, reviewable.

6. **Surfaces.**
   - Add-prospect autocomplete and subject resolution: unchanged code, now backed by the larger
     corpus through `active_entity_registry()`.
   - Prospect detail (`frontend/app/prospects/[id]/page.tsx`): a "Registry contacts" panel
     listing `list_registry_contacts(target_id)` for the prospect's resolved institution, each
     with role, verification flag, and source provenance. New endpoint
     `GET /entities/{target_id}/contacts` → 200 `list[RegistryContact]` (any authenticated
     consultant; network-shared).
   - The Bench radar draws unclaimed targets (GRS-0199 §5 consumes `search_registry_targets`).

7. **PII handling.** Registry contacts are personal data. They live in the DB only, never in a
   committed fixture (tests build rows in-code), and they are added to the SAR export and scrub
   paths (`repository.py` ~2034): a subject's `registry_contacts` rows are included in their SAR
   and removed/anonymised on scrub, exactly as `contacts` and `invitations` already are.

## Test plan

Backend (pytest, offline; rows built in-code, never a committed data file):
- `tests/test_gtm_registry.py`:
  - `upsert_registry_target`/`upsert_registry_contact` are idempotent (two upserts of the same
    PK yield one row, second overwrites fields).
  - `search_registry_targets` reproduces the stub ranking (exact>prefix>alias) over DB rows; a
    known target autocompletes.
  - `DbEntityRegistry.search`/`get` return the imported corpus when populated and fall back to
    the stub on an empty table; the demo subjects remain resolvable in the merged mode.
  - **Scoping:** `list_registry_contacts` is network-shared (advisor B reads the same shared
    contacts as advisor A) — asserted as the intended exception — while a prospect's own
    `contacts` remain owner-private (the existing owner-scope test still passes, proving the two
    stores did not merge).
  - Malformed-row fail-loud: an ingest helper given a row missing a required column raises rather
    than skipping silently (a summary `skipped` reason is recorded for genuinely optional gaps).
  - LSEG caveat handling: anonymous rows are dropped, `rec_rating_24m` decoded, `<NA>` nulled.
- `tests/test_data_subject_rights.py` (extend): a SAR includes the subject's `registry_contacts`;
  scrub removes them.

Frontend (vitest, per file):
- `bunx vitest run frontend/components/EntitySubjectField.test.tsx`: unchanged behaviour against
  a mocked larger corpus (the component does not special-case the source).
- `bunx vitest run frontend/app/prospects/[id]/page.test.tsx` (extend/create): the registry
  contacts panel renders contacts with role, verification flag, and provenance; empty state when
  the institution has none.

`pyright`, `ruff`, `tsc`, `ESLint`, and schema-parity are the standing gate. Golden master is
untouched (this ticket adds no scoring input).

## Out of scope

- The per-target influencer-map generator (GRS-0194) and the radar wiring (GRS-0199 §5) —
  both consume this registry.
- Curating the contributor→institution map beyond the first-pass inference (a data task; the
  ingest uses the map as delivered and records `verified=false` where inference is uncertain).
- Adding an information-vendor operating-model profile (GRS-0185 territory).
- Any outbound/outreach capability (GRS-0195).
- One ticket = one branch = one PR (contract regen + migration + scripts + surfaces ship
  together; the four ingest scripts are one PR since they share the registry model).

## Acceptance

All four sources import idempotently with per-import row-count summaries; a seeded target
autocompletes in Add-prospect through the unchanged `EntityRegistry` seam; registry contacts
render on the prospect record with role, verification, and source provenance; the shared-read vs
owner-private scoping split is test-enforced; SAR export includes registry contacts and scrub
removes them; no operator file or PII is committed; golden master byte-identical.
