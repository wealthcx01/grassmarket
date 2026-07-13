# GRS-0017 — AI first-draft narratives (gated)

- **Loop:** 4
- **Branch:** `grs-0017-ai-draft-narratives`
- **Status:** Planned
- **Normative source:** PRD §5; CLAUDE.md non-negotiable #8 (AI proposes, humans approve — runtime guarantee).
- **Depends on:** GRS-0015 (builder, approver fields). ActiveGraph if available; otherwise a minimal proposal/approval model now with an ActiveGraph adapter later (record the choice as an ADR).

## Goal

AI drafts the interpretation/commentary/recommendation sections of deliverables; a human approves every word before it can reach a client — enforced at runtime, not by convention.

## Scope

1. Narrative drafting service (Claude Agent SDK): produces *proposals* bound to a specific scoring run; prompt templates versioned in-repo.
2. Approval workflow: approver identity, timestamp, and a diff of consultant edits persisted with the deliverable.
3. Quality-review gate: deliverables authored by Venture Associates / early-tier Advisors require senior approval before finalisation (PRD §5).
4. Gate extension: a pack containing any unapproved AI section refuses client-facing generation (extends the GRS-0015 `ClientUsabilityError` pattern; 409 over HTTP).
5. Drafts clearly labelled as AI-drafted in any internal/watermarked rendering.

## Exit criteria

- Unapproved AI narrative → client generation refused (unit + service + HTTP tests).
- Approval trail (who, when, what changed) persists and renders in the methods appendix.
- Draft quality exercised against the golden-master run (snapshot review, not asserted in tests).
- Full gate green; CI green.
