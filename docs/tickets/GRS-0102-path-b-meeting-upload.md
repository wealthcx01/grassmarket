# GRS-0102 — Meeting-recording upload → AI prepopulation (Path B)

**Status:** Planned
**Loop:** Part 2 — Advisor Studio UI/UX review
**Phase:** A (build now)
**Depends on:** Path B (GRS-0029/0030)

## Why

Advisors should be able to upload a recorded meeting and have AI prepopulate the assessment's inputs
and ratings — the founder's "AI-assisted, not raw data entry" theme made concrete. This is **Path B**,
which is likely already built on the backend (GRS-0029/0030); today only "Path A (manual)" is exposed in
the wizard, so the meeting-intelligence path is invisible to advisors. This ticket is therefore mostly a
**surfacing** job: expose the Path B upload → prepopulation flow in the wizard UI and wire it to the
existing backend, rather than building extraction from scratch. It sits in Phase A because it surfaces
capability that already exists.

## What to build

**Wizard path selection + upload (`app/assessments/[id]/WizardClient.tsx`, `components/steps.tsx`)**
- Expose a Path B entry point alongside Path A: upload a meeting recording, kick off the existing
  meeting-intelligence extraction (GRS-0029/0030), and land the extracted values into the wizard inputs
  as AI-proposed, human-approved prefill (per ADR-0009 — extraction carries a recorded approval before
  it reaches the assessment).
- REUSE the Path B backend from GRS-0029/0030 — do not re-implement extraction; wire the wizard to it.

## Acceptance / verification

- The wizard offers Path B (meeting upload) as well as Path A (manual).
- An uploaded recording drives the existing extraction pipeline and prepopulates wizard inputs as
  approved-before-committed AI proposals.

## Not in scope

- Building the meeting-intelligence extraction backend — GRS-0029/0030.
- Screen-recording → widget auto-population — GRS-0109.
