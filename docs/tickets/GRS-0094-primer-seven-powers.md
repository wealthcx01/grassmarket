# GRS-0094 — Primer: the 7 Powers (Helmer)

**Status:** Planned
**Loop:** Part 2 — Advisor Studio UI/UX review
**Depends on:** GRS-0069 (`lib/powerGuidance.ts` per-power content)

## Why

The founder asked directly: "There's a lot of Hamilton Helmer material on benefits & barriers — why
isn't it in the primer?" The primer should teach the seven powers properly for senior operators: each
power, its benefit versus its barrier, the principle that the **weaker side sets the strength**, and how
the powers fit the target's lifecycle stage. The per-power content already exists in code from GRS-0069,
so this is largely surfacing authored material into the primer rather than writing it from scratch.

## What to build

**Primer (`frontend/app/guide/page.tsx`)**
- Add a section on Helmer's **seven powers**: name and explain each one.
- For each power, cover **benefit vs. barrier**, and explain why the **weaker side sets the strength**.
- Explain **lifecycle-stage fit** — which powers are available/relevant at which stage.
- REUSE the per-power content authored in `frontend/lib/powerGuidance.ts` (GRS-0069) rather than
  re-authoring it; pull the benefit/barrier/guidance text from there so the primer and the wizard stay
  consistent.

## Acceptance / verification

- All seven powers appear in the primer with benefit vs. barrier and the weaker-side-sets-strength
  principle.
- Lifecycle-stage fit is explained.
- The per-power text is sourced from `lib/powerGuidance.ts`, not duplicated with divergent wording.

## Not in scope

- The lens overview and label refinement (GRS-0093/0097).
- Changes to `powerGuidance.ts` content itself (reuse as-is).
