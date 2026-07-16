# GRS-0089 — Home welcome + context

**Status:** Shipped
**Loop:** Part 2 — Advisor Studio UI/UX review
**Depends on:** —
**Branch:** `grs-0089-home-welcome-context`

## What shipped

- **`components/WelcomeBanner.tsx`** (new) — a personalised welcome on the home page: a time-of-day
  greeting with the advisor's first name (best-effort from the session email local-part — reuses
  `lib/session`, no re-fetch), a one-line statement of what the platform does, and an **orientation**
  line: start a **first assessment** vs. resume your **portfolio** / **pipeline**. Mount-guarded so
  the first client paint matches the server (no personalised/anonymous flash).
- **`app/page.tsx`** — replaced the flat "Advisor dashboard" eyebrow + one-liner hero with
  `<WelcomeBanner />`. It **complements** the existing one-time first-run walkthrough (GRS-0065) and
  the primer strip below it (the welcome is a persistent greeting + orientation, not a second
  onboarding tour — no duplication).

## Acceptance / verification

`components/WelcomeBanner.test.tsx` — personalises the greeting from the session email; orients with
first-assessment / portfolio / pipeline links; still renders the studio title when signed out.
Frontend type-check · lint · vitest green.

## Why

The dashboard opens with a flat "Advisor dashboard" heading and a one-line overview — no welcome, no
introduction, no orientation. An advisor arriving for the first time is given no sense of who they are,
what the platform does, or what to do first versus what to resume. A top-consultancy product (the
McKinsey/Bain/Goldman bar) greets the operator and orients them to their next action. This ticket adds
a proper, ideally personalised, welcome and context block to the home page.

## What to build

**Dashboard (`frontend/app/page.tsx`)**
- Add a welcome/context block near the top of the home page: greet the signed-in advisor (personalised
  where identity is available), state briefly what the platform does, and orient them — what to do first
  versus what to resume. Lift the copy and layout to a considered, professional standard.

**First-run walkthrough (`frontend/components/FirstRunWalkthrough.tsx`)**
- Coordinate with the existing first-run walkthrough (GRS-0065) so the welcome and the walkthrough
  reinforce rather than duplicate each other. REUSE the walkthrough component; do not build a second
  onboarding path.

## Acceptance / verification

- The dashboard shows a welcome that orients the advisor (identity, what the platform does, what to do
  first vs. resume), not just a flat heading + one-liner.
- The welcome is personalised where the signed-in identity is available.
- The welcome and the existing first-run walkthrough coexist without duplicating each other.

## Not in scope

- The header account menu (GRS-0087) and the section-grid IA rework (GRS-0091).
- Deep per-section content — this is the home orientation layer only.
