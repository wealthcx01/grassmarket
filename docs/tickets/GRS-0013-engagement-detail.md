# GRS-0013 — Engagement detail (backend)

- **Loop:** 3 (see PRD §9) — third Loop 3 ticket.
- **Branch:** `grs-0013-engagement-detail`
- **Status:** In review
- **Normative source:** PRD §4 (Pipeline Management); ADR-0001 (no silent defaults),
  ADR-0002 (score/currency separation — engagement detail stays free of both).
- **Depends on:** GRS-0009 (assessments/finalisation), GRS-0011 (pipeline lifecycle).

## Goal

The engagement record that ties a **contracted** prospect to the work: its finalised assessment(s),
a deliverables progress shell, and a communication log.

## What shipped

1. **Engagement** (`Engagement` contract extended): links a prospect, carries `assessment_ids`
   (finalised assessments it draws on), a `deliverables` progress shell, and a `comms_log`.
2. **Deliverables progress = a forward-compatible placeholder** (`DeliverableSlot` +
   `DeliverableStatus`, Loop 4 fills content): a slot is just a `key` + a status from a **closed**
   set (`not_started → in_progress → drafted → delivered`). No deliverable content is invented — the
   Loop 4 builder owns that; this is only the progress shell so an engagement can track state before
   the builder exists.
3. **Communication log** (`CommsLogEntry`, `CommsLogEntryORM`): timestamped, **append-only** entries
   (a separate table; rows are inserted, never updated) ordered by `at`. The append endpoint sets
   the author to the principal.
4. **Link rules, fail-loud**: an engagement may only link **the owner's own contracted** prospect —
   a cross-owner prospect/assessment is refused as not-found (404, no existence leak); an
   own-but-not-contracted prospect or an unfinalised assessment is an `EngagementLinkError` (409).
   No `.get(key, default)` anywhere.
5. **Score-and-money-free**: engagement detail carries no currency and no index, so the ADR-0002
   boundary is trivially held (the AST guard already scans the pipeline tree from GRS-0012, and no
   Money/Score appears here).
6. **API** (`engagements` router): `POST/GET /engagements`, `GET /engagements/{id}` (detail, comms
   log included, ordered), `POST /engagements/{id}/comms`. All scoped; cross-owner → 404 everywhere.
7. **Persistence**: `engagements` (assessment ids + deliverables shell as JSON) + `comms_log_entries`
   tables via **Alembic migration 0005**; migration↔models parity holds.

## Tests

The deliverable-slot placeholder validates and its status set is closed (unknown status refused,
empty key refused); an engagement links the owner's own contracted prospect but refuses a
not-contracted one, a cross-owner prospect (404), an unfinalised assessment (409), and links a
finalised assessment (HTTP); comms entries appended out of order round-trip **sorted by `at`**;
cross-owner engagement GET + comms-append are 404; the list is scoped; endpoints require auth.
**212 backend tests pass** (+11).

## Non-negotiables honoured

Repository-only persistence; data scoping absolute + tested (own engagements + comms only,
cross-owner → 404 everywhere); contract-typed with schema parity; fail-loud link rules (no silent
defaults); deliverables are a typed forward-compatible placeholder, not a fabricated builder;
score-and-money-free; one ticket = one branch = one PR.
