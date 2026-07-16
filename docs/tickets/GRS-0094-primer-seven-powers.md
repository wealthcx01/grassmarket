# GRS-0094 — Primer: the 7 Powers (Helmer)

**Status:** Shipped
**Loop:** Part 2 — Advisor Studio UI/UX review
**Depends on:** GRS-0069 (`lib/powerGuidance.ts` per-power content)
**Branch:** `grs-0094-primer-seven-powers`

## What shipped

A new **"The seven Powers, one by one"** section in the primer (`app/guide/page.tsx`) that names and
explains each of Helmer's seven Powers:

- A card per power — Scale Economies, Network Economies, Counter-Positioning, Switching Costs, Branding,
  Cornered Resource, Process Power — each showing its **Benefit**, **Barrier**, and an illustrative
  brokerage **Example**, plus a **lifecycle-stage** badge (Origination / Take-off / Stability).
- The **benefit/barrier/example text is reused from `lib/powerGuidance.ts`** (GRS-0069) — imported, not
  re-authored — so the primer and the wizard's 7-Powers step stay consistent. Names + lifecycle stages
  match the registry (`powers.yaml`).
- A lead paragraph explains **lifecycle-stage fit** (which powers are even *available* at a platform's
  age) and a closing note reinforces the **weaker-side rule** (the score is the weaker of benefit and
  barrier — a benefit with a crossable barrier is a head start, not a power).

## Acceptance / verification

All seven powers are named and explained with benefit vs. barrier, the weaker-side rule, and
lifecycle-stage fit, reusing `powerGuidance.ts`. Frontend type-check · lint · vitest green.

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
