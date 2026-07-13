# GRS-0027 — Workbench frontend

- **Loop:** 5 (closes Loop 5)
- **Branch:** `grs-0027-workbench-frontend`
- **Status:** Planned
- **Normative source:** PRD §6; design tokens per CLAUDE.md.
- **Depends on:** GRS-0020–0026 APIs.

## Goal

The Workbench as one coherent surface in the Next.js app.

## Scope

1. Certification progress view (ladder state, evidence, what's next).
2. Learning library + drills player (spaced-repetition session UI).
3. Practice Arena chat UI (session, scoring reveal, model answers).
4. Calibration session screens: blind rating entry; results visible only after session close.
5. Committee queue screen (members only); consensus/dissent screens for dual rating (if not surfaced in GRS-0020).
6. Bench-time dashboard as the advisor's landing state when no active engagement.
7. Role gating in UI mirrors API claims exactly (committee, certification levels).

## Exit criteria

- All Loop 5 features usable in-browser against seeded data.
- Blind-entry and role gating verified in UI tests.
- Type-check/lint green; frontend CI green.
