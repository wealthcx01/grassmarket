# GRS-0019 — Deliverables frontend

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
