# GRS-0265 — a run report records which skills its worker used

**Status:** DONE (2026-10-01). **Priority:** MEDIUM. **Type:** Contract addition, additive.
**Source:** fountainbridge FB-231 / FB-239. **Consumer:** the Foundry Studio.

## Why

John, on the Foundry's office:

> *"should it not be one temp VM on railway per pixel agent, per ticket that is being worked, with
> the right skills files loaded to tackle the ticket? **and we should be able to see what skills each
> worker used**"*

Checked against the data models rather than guessed, and the answer was no — for a plain reason.
The Foundry's office record holds eight fields per character and its run report held nine. **Neither
had room for a skill.** The fact was not hidden behind a permission or a missing read; it was never
written down by anybody.

This package is where that fact has to live. fountainbridge's non-negotiable 7 is that every rendered
entity is a bcap-contracts type and schema changes happen here, consumed there as generated types.

## What changed

`RunReport.skills_used: list[str]`, defaulting to empty.

## Two decisions worth keeping

**Additive and optional**, because this package's own rule is that consumers never break on an
upgrade. Every run report already written to a venture's state ref omits this field — ARCA alone has
9,904 of them — and making it required would make the entire history of every venture unreadable the
moment the package upgraded.

**Empty is not a claim.** It means no skills were used *or* that the run predates the field, and the
two cannot be told apart. The field description says so out loud, because the reader lives in another
repository and will be tempted to render empty as a fact. A studio that printed "this worker used no
skills" over a report written in August would be asserting something about every run in history that
nobody ever measured — the silent-fallback failure non-negotiable 3 forbids.

## Checks

- `pytest tests/test_foundry_contracts.py` — 31 passed, including four new ones.
- Each new test checked by breaking it: making the field required fails collection outright (every
  existing report stops validating, which is the upgrade this design avoids); removing the field
  fails four tests.
- `scripts/generate_schemas.py` regenerated 132 schemas; the diff touches `RunReport.json` only.
- Version 0.3.0 → 0.4.0.

## What happens next, in the other repository

fountainbridge FB-231 consumes it: the lane writes the field from the session transcript it already
keeps, and the ticket's trail renders it in words a founder reads without knowing what a skill is.
That unblocks FB-239 — one machine per ticket, with the skills it used on the record.
