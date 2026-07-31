# GRS-0065 — First-run onboarding walkthrough

**Status:** DONE (reconciled 2026-08-01).

- **Loop:** — (UX)
- **Status:** Done — closes rubric #4 (guided first-run) from the 2026-07-15 UX audit.

## What

A short, skippable guided tour shown once on a new advisor's first signed-in visit to the
dashboard, then never again. Four steps: welcome → the four-move workflow (Pipeline → Assessments →
Deliverables → Earnings) → the honest-by-design principles (uncertainty shown loudly; peer review
before finalise; AI proposes, you approve) → a start action (Read the primer / Go to my pipeline).

- **Persisted** via a `bas.onboarding_seen` localStorage flag (a UI preference, not user data) — it
  shows once. **Replayable** from the guide via a "Replay the welcome tour" link (`/?tour=1`).
- **Accessible:** `role="dialog"` + `aria-modal`, labelled, focus moved to the primary action, ESC
  and backdrop-click skip, Tab wraps within the dialog. Styled through design tokens, so both light
  and dark themes work; kept deliberately brief and quiet (no gamification), matching the ethos.

## Exit criteria

- Shows on a signed-in advisor's first dashboard visit; never again once dismissed; not shown when
  signed out; the guide can replay it. Pinned by `FirstRunWalkthrough.test.tsx` (5) and verified
  live (renders, steps through, navigates, does not reappear, no errors). type-check/lint/build green.

---

## Status reconciliation — 2026-08-01

**DONE.** Landed on main in `5828efb` (GRS-0065: first-run onboarding walkthrough).

This ticket carried no *What shipped* record; the commits above are that record.
