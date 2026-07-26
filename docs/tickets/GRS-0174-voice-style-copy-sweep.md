# GRS-0174 — Voice & style guide + application copy sweep

**Status:** In review (2026-07-24) — STYLE-VOICE.md founder-approved; sweep of core surfaces done, PR open. **Priority:** HIGH — lands first;
every later frontend ticket writes in the new register.
**Loop:** founder-feedback remediation, Wave 1.

## Why

Founder verdict: the copy reads "AI heavy" — an overused em dash, and a concise, aphoristic
cadence that feels like a tweet rather than material that helps an advisor understand. The tone
is not confined to the Guide: the em-dash-as-default-connective and repeated mono mantras
("Words rate; numbers rank", "honest by design") run through component microcopy on at least four
surfaces. The writing style is to change completely.

## Scope

1. **Author `docs/STYLE-VOICE.md`** and get founder sign-off on it before any sweep commit. The
   guide is one page and normative for all user-facing copy. It contains, in this order:
   - The register in one paragraph: professional advisory writing that informs someone new to the
     product, in full sentences, with plain connectives (and, so, because, which means).
   - Named rules, each with one before/after example drawn from the current codebase:
     (a) the em dash is rare and never the default joiner; commas, colons, and full stops carry
     the load; (b) no aphorism in place of an explanation; a maxim may summarise a point that has
     already been explained, never substitute for it; (c) define a term before trading on it
     (V, C, q_m, P10/P50/P90, coverage, provenance); (d) size explanations to inform a newcomer,
     not to impress a colleague; (e) sentence-case headings and buttons; (f) numbers and units
     written out where a screen reader or a cold reader could misread them.
   - A short banned-pattern list: em-dash chains, "X; Y" tweet couplets, unexplained notation,
     mantra repetition across surfaces.
   - A note that each recurring mantra survives at most once, in the Guide, expanded into a real
     explanation (the expansion itself lands with GRS-0175).
2. **Sweep the component microcopy** against the signed-off guide. Verified surfaces that carry
   the register today (re-verify with `rg "—" frontend/` and `rg -l "Words rate|honest"` during
   implementation):
   - `frontend/components/steps.tsx` (53 em dashes; the `Interpretation` card at lines 1136-1176
     carries "Words rate; numbers rank" and "Read the range, not the point"; step intro copy,
     finalise-confirm copy at 1312-1329, solo-path callout at 1369-1374).
   - `frontend/components/LiveScorePanel.tsx`, `frontend/components/BandDisplay.tsx` (mantra
     copy asserted in their tests).
   - `frontend/app/assessments/page.tsx` (creation-form labels, sandbox tooltip at lines
     207-213, table header tooltips at 239-249, empty state).
   - `frontend/app/assessments/[id]/WizardClient.tsx` (`LiveSummary` rail copy, save badge,
     blocking-list copy).
   - `frontend/app/pipeline/page.tsx`, `frontend/components/KanbanBoard.tsx` (tooltips, stale
     badge, empty columns), `frontend/app/earnings/page.tsx` (carrot copy at lines 217-220,
     empty state), `frontend/components/EarningsProgress.tsx`, panel components
     (`WizardSuggestionsPanel`, `SellOpportunitiesPanel`, `CommitteeReviewPanel`,
     `DualRatingPanel`, `DeliverablesPanel`, `FirstRunWalkthrough`, `WelcomeBanner`,
     `AccountMenu`), and error/confirmation strings in `frontend/lib/api.ts` callers.
   Rewrite only prose; no logic, layout, markup-structure, or styling changes in this ticket.
   Decision: `frontend/app/guide/page.tsx` and `frontend/app/help/page.tsx` are excluded here
   because GRS-0175 rewrites them wholesale; sweeping them twice would produce merge churn.
3. **Update the copy assertions** in every affected test file so tests assert the new copy, not
   the mantras: `frontend/app/assessments/[id]/LiveSummary.test.tsx`,
   `frontend/components/BandDisplay.test.tsx`, and any other test that greps for swept strings
   (find them with `rg -l "Words rate|honest|—" frontend --glob "*.test.tsx"`).

## Test plan

1. Per-file vitest re-runs for every component whose copy is asserted:
   `bunx vitest run frontend/app/assessments/[id]/LiveSummary.test.tsx`,
   `bunx vitest run frontend/components/BandDisplay.test.tsx`, plus each additional test file
   the sweep touches. Then one full `bunx vitest run` to catch missed assertions.
2. Mechanical checks recorded in the PR description (not CI-enforced, since em dashes remain
   legal in rare, deliberate use): `rg -c "—" frontend/components frontend/app` before/after
   counts, and `rg "Words rate|honest by design" frontend` returning no hits outside the Guide
   files (which GRS-0175 owns).
3. Standing gate: tsc, ESLint. No backend tests are affected (no Python copy is user-facing on
   these surfaces).

## Out of scope

- The Guide and Primer pages (GRS-0175 rewrites them in this register).
- The Summary step's structural repair (GRS-0182) and any layout, component, or logic change.
- Backend strings, deliverable (.docx) narrative text, and Academy course content.
- docs/ prose other than the new STYLE-VOICE.md.

## Acceptance

STYLE-VOICE.md approved by the founder before the sweep merges. A cold read of the wizard,
portfolio, pipeline, and earnings screens finds no em-dash chains, no tweet-cadence lines, and no
unexplained jargon. `rg "Words rate|honest by design" frontend` matches nothing outside the two
guide pages. All existing tests pass with updated copy assertions.
