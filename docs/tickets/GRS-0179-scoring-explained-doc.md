# GRS-0179 — docs/ATLAS-Scoring-Explained.md: the maths, in English

**Status:** In review (2026-07-25) — docs/ATLAS-Scoring-Explained.md authored + linked from the Guide and the Summary step; PR open. **Priority:** HIGH.
**Loop:** founder-feedback remediation, Wave 1. Docs only; no engine change.

## Why

There is no full, reviewable explanation of the maths behind Platform (V) and Customer (C). The
Guide's "Reading the Outputs" section is the only account and it references P50/P10/P90 without
definition. The founder also asked directly: what is the balance between Business Metrics,
Powers, Infrastructure Deep Dive and Customer Proposition, how would Hamilton Helmer treat
these, and why do all the scores look surprisingly similar?

## Scope

One standalone `docs/ATLAS-Scoring-Explained.md`, authored in the STYLE-VOICE register (plain
sentences, no jargon without a definition, no em-dash pile-ups). It is the single reviewable
account of the maths and must never restate a number the engine does not actually use. Every
coefficient is transcribed from the live source, with the source path and symbol named inline so
a reviewer can check it. Structure, section by section:

1. **Front matter and cross-links.** A one-paragraph purpose statement ("read this instead of the
   Methodology to understand the scoring") and a "who should read the Methodology instead" pointer
   (anyone changing the scoring, since changes are ADRs plus a new Methodology version, never edits
   to this file). Link targets, added in this same PR:
   - `docs/Advisor-Guide-to-ATLAS.md` gains a link to this file from its outputs-interpretation
     section `## 7. What the outputs mean (and don't mean)` (the Guide has no literal "Reading the
     Outputs" heading; §7 is that content). A second link may sit in `## 6. Scoring the 7 Powers:
     benefit AND barrier` where the mechanics are introduced.
   - `frontend/components/steps.tsx` `SummaryStep` gains a single text link "How the maths works"
     pointing at the published docs path. Decision: link only, no inline duplication of the maths
     into the UI, because the doc is the one source of truth and duplicated prose drifts.
   This file is authoritative for the plain-English account; where it needs the Helmer framing it
   **cross-references `docs/ATLAS-7Powers-Adaptation.md`** (authored by GRS-0180) rather than
   paraphrasing it, so the two documents cannot diverge. If that file is not yet merged when this
   ticket lands, the link is added as a relative path and the PR notes the dependency; the section
   still stands on the ADR-0007 summary below.

2. **The composite V**, with the real coefficients. State V = θ_B·B + θ_P·P + θ_L·L and give the
   per-segment θ triples exactly as the live sources hold them, each with the source path, symbol,
   and the one-line reasoning already recorded in code:
   - Retail draft: θ_B 0.30 / θ_P 0.30 / θ_L 0.40
     (`src/grassmarket/atlas/draft_coefficients.py`, `draft_v1_coefficient_set` default `theta`
     around line 83; methodology v1.1, `client_usable` via the retail path).
   - Wealth elicited starter: θ_B 0.45 / θ_P 0.30 / θ_L 0.25
     (`src/grassmarket/atlas/elicited_coefficients.py`, `elicited_wealth_coefficient_set` around
     line 261) — reasoning as recorded: franchise economics lead, L trimmed because infrastructure
     is hygiene that is largely priced into B.
   - Exchange elicited starter: θ_B 0.30 / θ_P 0.37 / θ_L 0.33
     (`elicited_coefficients.py`, `elicited_exchange_coefficient_set` around line 279) — reasoning
     as recorded: the moat (P) is the top term; B rises because volume is roughly half of revenue.
   Note the drafted v1.4 four-index direction as DRAFT only: the placeholder re-split θ 0.25 / 0.25
   / 0.35 with θ_C 0.15 (`draft_coefficients.py` `_V1_4_THETA` / `_V1_4_THETA_C` around lines
   73-74), explicitly `client_usable=False` and pending the θ_C panel (ADR-0023 Stage 2). State
   plainly that C is today **reported alongside V, not folded into it** (ADR-0023 Stage 1), and
   that no four-index weight is live. Do not present v1.4 numbers as active.

3. **Module maturity q_m**, worked end to end. Define q_m as the module's maturity index, show one
   worked example over a small module including the bottleneck min-term (a module cannot outrun its
   weakest critical subcomponent — the ★ gate), and state the L blend exactly as the UI already
   discloses it: L = α·(Σ weight·q_m) + (1−α)·(min q_m over critical modules), naming that the
   min-term drags L below the plain weighted average by design (this is the same disclosure text in
   `frontend/components/LiveScorePanel.tsx` around lines 86-89, so the doc and the UI agree). Close
   with the words-vs-numbers rule: gate bands (Basic → Frontier) are what you defend out loud;
   the continuous scores decide what to fix first.

4. **Uncertainty from scratch.** Explain what the Monte Carlo does in plain words (it re-samples
   each input within its evidence-graded confidence and re-scores many times to produce a
   distribution, per Methodology §7), define P10 / P50 / P90 in words with one simple ASCII or
   described figure (P50 is the median outcome; P10–P90 is the honest range; a wider band means
   thinner or weaker-graded evidence), and give the one-number rule (ADR-0040) in plain language:
   the headline always quotes the deterministic point, and the prose quotes the range around it —
   the two never disagree. Note that an unmodelled band shows an honest labelled point, never a
   falsely tight range (ADR-0008).

5. **"Why do scores cluster?"** — the honest section the founder asked for. Cover, each as its own
   short paragraph: (a) maturity anchors quantise q_m onto a few plateaus (~37.5 / 50 / 80 on the
   display scale), so nearby inputs collapse to the same rung; (b) the draft retail weights are
   uniform — every module κ is 11.1% (1/9), so no module can pull the average far; (c) B saturates
   because it is built from few metrics, so it sits high and flat across subjects; (d) the demo
   subjects (Revolut, Hargreaves Lansdown, WeBull) were seeded deliberately similar. Then state
   what will spread scores in real use: elicited (non-uniform) segment weights, more metrics feeding
   B, and real input dispersion across genuinely different businesses. This section makes clear the
   clustering is an artefact of draft weights and demo data, not a defect in the maths.

6. **"How would Helmer treat these?"** — cross-referencing `docs/ATLAS-7Powers-Adaptation.md`
   (GRS-0180) for the full §5 treatment rather than restating it. Summarise only what this document
   needs: B and L are operational excellence in 7 Powers terms (necessary to run the business, but
   not by themselves a durable advantage); P is the Helmer-native lens, because a Power requires
   BOTH a Benefit and a Barrier, and our strength = min(Benefit, Barrier) is exactly that dual test
   (ADR-0007, the same min the wizard applies per power in `steps.tsx`). Explain why an advisory
   product still scores the whole platform, not only its moat: the client is buying an operating
   assessment, so B, L and C matter to the verdict even though only P is durable advantage in
   Helmer's strict sense. Point the reader at the adaptation doc for the per-power (Scale Economies,
   Network Economies, Counter-Positioning, Switching Costs, Branding, Cornered Resource, Process
   Power) treatment and the B/L/P/C mapping.

## Test plan

This is a documentation ticket; the "tests" are the review-gate checks that keep the prose honest
and the file wired in. No pytest/vitest suite changes.

1. **Number-fidelity check (manual, recorded in the PR).** Every θ triple, the v1.4 placeholder,
   and the κ figure quoted in the doc are diffed against the live sources named in Scope §2
   (`draft_coefficients.py`, `elicited_coefficients.py`). The PR description lists each quoted
   number with its source line, so a reviewer confirms zero drift. Decision: a manual cross-check,
   not an automated assert, because the doc is prose and the coefficients already have their own
   unit coverage; duplicating that in a doc test adds no safety.
2. **Link check.** The new link from `docs/Advisor-Guide-to-ATLAS.md`, the `SummaryStep` link in
   `frontend/components/steps.tsx`, and the internal cross-link to
   `docs/ATLAS-7Powers-Adaptation.md` all resolve (relative paths valid from their file locations).
   Run the repo's markdown link check if one exists; otherwise verify by hand and record in the PR.
3. **Standing gate.** `tsc` and ESLint pass for the single-line `steps.tsx` edit;
   `bunx vitest run frontend/components/steps.test.tsx` (if present) stays green — the edit is an
   inert anchor tag, no behaviour change. `uv run pytest tests/test_atlas_engine_golden_master.py`
   is the proof that nothing in the scoring path moved (this ticket touches no Python scoring code).

## Out of scope

- Any change to coefficients, the composite, uncertainty, the value bridge, or any scoring code.
  One-ticket-one-PR: this ships the document plus its two link edits only.
- Authoring `docs/ATLAS-7Powers-Adaptation.md` — that is GRS-0180; this ticket links to it.
- The four-index (θ_C) activation — that remains ADR-0023 Stage 2 / GRS work, described here only
  as a documented draft direction, never presented as live.
- Any UI beyond the single "How the maths works" link in `SummaryStep`; no new component, no inline
  maths panel.

## Acceptance

The founder can review the scoring maths end-to-end from `docs/ATLAS-Scoring-Explained.md` alone,
without opening the Methodology: the composite and its per-segment weights, module maturity and the
L bottleneck blend, uncertainty and P10/P50/P90, an honest account of why demo scores cluster, and
the Helmer treatment (cross-linked to the adaptation doc). Every coefficient quoted matches the
live sets named in Scope §2 (verified line-by-line in the PR). The Guide and the Summary step both
link to it. No scoring change anywhere; the golden master is byte-identical.
