# GRS-0104 — Fix the confusing "Live V appears once scoreable…" message

**Status:** Planned
**Loop:** Part 2 — Advisor Studio UI/UX review
**Phase:** A (build now)
**Depends on:** —

## Why

Every wizard step's side rail shows "Live V appears once the assessment is scoreable…" — a message the
founder reacted to with "I don't even know what that means." It's opaque jargon that occupies prime
real estate on the panel meant to give live feedback, and it tells the advisor nothing about what to do
to make a score appear. Replace it with a genuinely helpful live-score preview that either shows the
current live score or clearly states what's still needed to reach a scoreable state.

## What to build

**Live summary side rail (`app/assessments/[id]/WizardClient.tsx` — LiveSummary, `components/LiveScorePanel.tsx`)**
- Replace the "Live V appears once the assessment is scoreable…" placeholder with a preview that: when
  scoreable, shows the live score/ranges; when not yet scoreable, names concretely what remains (which
  inputs/coverage) to become scoreable — plain English, no bare "V" jargon.
- REUSE the existing live-score service the panel already calls — this is a copy/state-presentation
  change, not new scoring.

## Acceptance / verification

- The opaque "Live V appears once the assessment is scoreable…" string is gone from every step's rail.
- When not scoreable, the panel states what's missing; when scoreable, it shows the live score/ranges.

## Not in scope

- Changing live-score computation or the scoreable threshold.
- Summary/Scenarios depth — GRS-0110.
