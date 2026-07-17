
## What shipped (Status: Shipped — branch grs-0104-live-score-message)

Replaced the opaque "Live V appears once the assessment is scoreable…" placeholder in the wizard side
rail (`LiveSummary` in `app/assessments/[id]/WizardClient.tsx`) with a genuinely useful preview:

- **Not scoreable** → a "Live score" card that lists, in plain English, exactly what remains — reusing
  the live-score service's `blocking` reasons (e.g. "Enter at least one business metric.", "Rate all 7
  Strategic Powers.", "Rate at least one subcomponent in a core module.") — plus how many subcomponents
  are rated so far. No bare "V" jargon.
- **Before any blockers are known** (initial load) → a gentle "Start rating the steps — the live score
  updates as you go."
- **Scoreable** → the live V band, unchanged (still via `BandDisplay`, honest about uncertainty).

Copy/state-presentation only — reuses the existing live-score service (no new scoring).

## Acceptance / verification

`LiveSummary.test.tsx` — the opaque string is gone; when not scoreable the concrete blockers render;
when scoreable the honest band renders. Frontend type-check · lint · vitest green.
