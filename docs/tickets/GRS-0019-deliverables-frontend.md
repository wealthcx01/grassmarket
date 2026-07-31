# GRS-0019 — Deliverables frontend

**Status:** DONE (reconciled 2026-08-01).

- **Loop:** 4 (closes Loop 4)
- **Branch:** `grs-0019-deliverables-frontend`
- **Status:** In review — PR #20
- **Normative source:** PRD §5; CLAUDE.md #8, #9.
- **Depends on:** GRS-0015–0018 APIs.

## Goal

The advisor-facing deliverable workflow in the Next.js app.

## Scope

1. Per-engagement deliverable library: type, mode (client/internal-draft), status, versions, generated-at.
2. Generate flow with explicit client-facing vs internal choice; gate refusals (draft coefficient set, unapproved AI narrative, committee-pending ratings once GRS-0021 lands) surfaced as clear, non-technical messages.
3. AI-narrative review screens: draft vs edited diff view, approve action, senior-review queue for gated tiers.
4. Watermarked-draft preview; download of generated .docx.
5. Scoping in UI: advisors see own engagements only (404 pattern respected; no existence leakage).

## Exit criteria

- End-to-end in browser against seeded data: generate → review AI sections → approve → download.
- Review gate blocks unapproved packs in UI and API.
- Type-check/lint green; frontend CI green.

---

## Status reconciliation — 2026-08-01

**DONE.** Landed on main in `ff5ef45` (GRS-0019 slice 3: review gate visible + approval queue + scoping), `40edb69` (GRS-0019 slice 2: AI-narrative review + approve UI), `c7894d0` (GRS-0019: Playwright E2E scaffold + slice-1 browser specs (for CI)), and 2 more.

This ticket carried no *What shipped* record; the commits above are that record.
