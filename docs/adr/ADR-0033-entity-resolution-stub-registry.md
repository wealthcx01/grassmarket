# ADR-0033 — Entity resolution: a canonical `entity_id` over an injectable registry port (stub now)

- **Status:** Accepted (2026-07-18). Founder theme in the Part-2 review: an assessment subject is
  free text with no tie to a real company — two advisors assess "Revolut" and "Revolut Ltd" as
  unrelated records. GRS-0100 asks for lookup/autocomplete that resolves a subject to a canonical
  entity.
- **Date:** 2026-07-18
- **Deciders:** Founder theme + engineering (autonomous Part-2 build).
- **Normative source:** `docs/tickets/GRS-0100-entity-resolution.md`.
- **Implements:** GRS-0100 v1 (the stub-backed core). The **choice of the authoritative external
  registry** (Companies House / LSEG / a data vendor) is explicitly deferred — this ADR fixes the
  *port + storage* so that swap is a one-file change, not a rewrite.
- **Couples with:** ADR-0009 / ADR-0032 (the injectable-port pattern this reuses); CLAUDE.md #3
  (fail loud, never fabricate), #5 (all persistence through the repository), #9 (data scoping).

## Context

The subject is a free-text string on the assessment. Two open questions the ticket names:

1. **What is the entity-store contract, and where does the canonical id live?**
2. **Which registry is authoritative?** The ticket defers this to "the deferred ADR" — a live
   registry likely needs an external API + credentials the operator must provision.

We want the *user-visible capability* now (autocomplete → a canonical identity; two assessments of one
company share it) without blocking on the external-source decision.

## Decision

**A canonical `entity_id` stored on the assessment, resolved through an injectable `EntityRegistry`
port whose shipped implementation is a seeded in-repo stub.** Reuses the ADR-0009/0032 port pattern.

1. **`CompanyEntity` contract.** `{ entity_id (stable canonical id), name (canonical display),
   aliases, domain? }`. `entity_id` is the durable key an assessment points at; `name` is what the UI
   shows. Aliases carry the variants that should collapse to one entity ("Revolut", "Revolut Ltd").

2. **An injectable `EntityRegistry` port.** `search(query, limit) -> list[CompanyEntity]` and
   `get(entity_id) -> CompanyEntity | None`. The shipped `StubEntityRegistry` is a small, seeded,
   in-repo list of well-known finance/fintech firms with case-insensitive ranked matching
   (exact > prefix > alias/substring). A real registry adapter (Companies House, LSEG, a vendor) drops
   in behind the same port later — the endpoint, the storage, and the UI do not change.

3. **The canonical id lives on the assessment.** `AssessmentORM.entity_id` (nullable) + `entity_id` on
   the `Assessment` contract, set at create time and immutable-by-convention thereafter (a re-link is a
   deliberate future action, not this ticket). Storing it on the record — not only in the document —
   makes dedup a cheap owner-scoped query (`list_assessments_for_entity`).

4. **Resolution is human, never silent (fail loud, #3).** The registry only ever *proposes* candidates;
   it never auto-resolves a typed string to one entity. The UI shows matches and the advisor picks; on
   an ambiguous query nothing is chosen for them. The create endpoint accepts an explicit `entity_id`
   and **validates it against the registry** — an unknown id is a 400, never a fabricated link. Typing a
   subject the registry doesn't cover is the explicit **manual fallback**: `entity_id` stays null and the
   record is clearly "unlinked".

5. **Reference lookup is org-wide, not owner-scoped.** `GET /entities/search` is public reference data
   (like the registry of powers/modules) — every consultant queries the same company list. The
   *assessments* that carry an `entity_id` remain owner-scoped as always (#9); dedup counts a
   consultant's **own** book only.

## Consequences

- The capability ships now: autocomplete → a canonical identity, and two assessments of the same
  company share `entity_id` (queryable). The external-source decision is isolated behind the port.
- One nullable column (`entity_id`), no scoring-path change → golden master untouched.
- The stub's coverage is deliberately small; an uncovered subject is a first-class manual record, not
  an error. Breadth arrives with the real registry adapter.

## Alternatives considered

- **Store `entity_id` only in the document profile.** Rejected: dedup would need to parse every
  document; a column is the queryable home and matches how `provenance`/`state` already live on the row.
- **Resolve free text to an entity server-side (best-match auto-pick).** Rejected outright by #3 — a
  silent pick is exactly the "Revolut vs Revolut Ltd" collision inverted; the human must choose.
- **Block on the real registry.** Rejected: the port lets the capability and its UI ship now and the
  authoritative source land later without touching feature code.
