# GRS-0170 — Powers step: unrated ≠ "None", un-rate affordance, one-click chips

**Status:** Done (2026-07-23). Staging-rerun finding (3/5). **Loop:** rerun remediation.

## Why

The Powers step's native `<select>` displayed "None" — a REAL rating (zero power) — as the face of
an untouched control: the exact rated/unrated conflation D9 forbids, at the input layer. Worse,
rating one side silently wrote "None" on the other (a real zero-moat rating the advisor never
made). No un-rate existed, and 4–6 dropdowns per power made it the slowest screen in the core loop
(the infra chips made the contrast obvious).

## Fix (frontend only — the contract's both-sides-required rule is unchanged)

- `StrengthControl`: one-click segmented strengths (None/Emerging/Established/Wide); UNRATED shows
  no active segment; "None" is an explicit choice; clicking the active segment clears.
- `PowerStrengthGrid`: a power persists only when BOTH sides are rated; a half-rating lives in
  local pending state with a visible "rate the other side too" hint — never a silent "None".
  Clearing a side un-rates the power (`doc.removePower`), honestly. Grades/evidence attach once
  the rating is recorded.

## Acceptance

An untouched power shows no rating; rating is one click per side; a power can be returned to
unrated; nothing is ever recorded that the advisor didn't click.
