# GRS-0227 — Surface the dispersion beside the score

**Status:** DONE (reconciled 2026-08-01). _Previously recorded as: Built, in review (2026-07-30). **Priority:** HIGH. **Loop:** founder-feedback._
remediation, Wave 1. **Depends on:** GRS-0223 (the measurement that motivates it).

## Why

GRS-0223 answered the founder's "all the scores seem surprisingly similar" and found the engine is
not at fault: V averages nine modules, seven powers and four metrics, so a firm that is strong in
some places and weak in others is pulled to the middle by construction. Every real firm is a mixed
bag, so every real firm lands near the middle.

Two of the three recommendations from that analysis are founder-scoped methodology questions. This
is the third, and it is the only one buildable without a decision:

> A V of 0.57 built from modules spanning 0.20–0.80 is a **different firm** from a V of 0.57 built
> from modules all at 0.55, and today both display identically.

That is the actual problem behind the founder's observation. The scores are not wrong; the report
throws away the information that would make them read as different. The engine already computes
every `q_m` and already identifies each module's bottleneck subcomponent — none of this needs new
maths, only surfacing.

## Scope

1. **A dispersion figure on the assessment summary**, beside V. The spread of assessed `q_m` —
   range or interquartile, whichever reads better against real data — presented as what it is: how
   uneven this firm is, not a second quality score. It must be impossible to read as "another V".
2. **Say what the number means in one line.** "Your modules range from 0.20 to 0.80: this is an
   uneven business with a specific weak spot, not an average one." A tight spread gets the opposite
   sentence. The wording is the deliverable as much as the figure is.
3. **Lead the report with the bottleneck rather than the mean** where dispersion is high. The
   engine already records `bottleneck_subcomponent` per module; a high-dispersion firm should have
   its weakest module named on the summary, because that is the finding an advisor scopes against
   (GRS-0217 §4 of the Sales Ops Playbook teaches exactly this qualification).
4. **Do not invent a band or a label for it.** No "high/medium/low dispersion" rating gate. That
   would be a new scored dimension arriving without a methodology version, which is precisely what
   GRS-0223 declined to do.

## Explicitly not in scope

- Any change to V, to coefficients, or to the maturity scale. GRS-0223 measured and recommended
  **no engine change**; this ticket surfaces what the engine already produces.
- The rubric-usage and B-saturation findings, which are founder-scoped methodology questions.

## Test plan

1. Two synthetic assessments with the **same V** and very different `q_m` spreads must render
   visibly differently. That is the whole point of the ticket, so it is the headline test.
2. The dispersion figure is derived from assessed modules only — a Not Assessed module contributes
   nothing, per D9, exactly as it contributes nothing to V.
3. An assessment where every module is at the same level reports a spread of zero without dividing
   by anything or rendering an empty state.
4. Golden master byte-identical: this adds a view over existing outputs.
5. Standing gate: pytest, pyright, ruff, tsc, per-file vitest.

## Acceptance

Two firms with the same headline score no longer look like the same firm, and an advisor opening a
mid-range report can see immediately whether it is mid-range because everything is mediocre or
because one thing is broken.

## What was built

**The measurement that justified it, taken on the real demo data.** The three showcase firms span
0.058 of V and 0.448 / 0.600 / 0.542 of module `q_m`. Hargreaves reads mid-range at V 0.572 with a
module sitting exactly on the rubric floor (0.200); Revolut reads 0.605 and bottoms out at 0.375.
That gap between the two numbers is the whole argument, and it is pinned in
`tests/test_module_dispersion.py` so the feature cannot outlive its evidence.

1. **`module_qm_point` on the live payload** — the deterministic `q_m` per module (ADR-0040), keyed
   only by modules that actually scored. Not the Monte Carlo bands: an unassessed module carries a
   modelled band and no point, so a band-derived range would invent a weak spot nobody measured
   (D9). Worth recording that the obvious reason for this field is not the real one — at module
   level the MC median lands exactly on the deterministic point, because a fully rated module has
   no rating uncertainty to draw over. The drift is at the composite. The reason to read points is
   **coverage**, not drift.
2. **`frontend/lib/dispersion.ts`** — the range, the weakest module, and the sentence. No band, no
   label, no high/medium/low gate, per scope item 4.
3. **The summary card and the live panel** both state the range and what it means. Where the spread
   is wide the bottleneck **leads** the card (scope item 3) — but never below half coverage, where
   the weakest module may simply be the one nobody has assessed yet (the GRS-0145 caveat).

**The threshold is one full rubric step (0.3), not an invented percentile.** `MaturityLevel.
score_index` places the levels at 0.2 / 0.5 / 0.8 / 1.0, so the widest adjacent step is 0.3. Below
it every module sits within a single rubric level of every other and calling the firm uneven would
be reading noise; at or above it the modules are genuinely at different maturity levels. That is a
fact about the scale rather than a choice about the data.

### On scope item 4

A binary `uneven` flag does exist internally, because scope item 2 requires a tight spread to get
the *opposite* sentence and that needs a threshold. It is used only to choose wording and bullet
order and is never rendered as a label; both test files assert no rating word reaches the screen.

### Test plan, as delivered

Every item is covered. The headline test — same V, different spread, must render differently — is
asserted twice: on the helper (`lib/dispersion.test.ts`) and on rendered output
(`components/LiveScorePanel.dispersion.test.tsx`), because the ticket's acceptance is a claim about
what is on screen. Assessed-only (D9), zero-spread, and the single-module case (which renders
nothing rather than claiming a perfectly even firm) are each covered. No change to the scoring path.

---

## Status reconciliation — 2026-08-01

**DONE.** Landed on main in `86946df` (GRS-0227: report how uneven the firm is, beside the score).

This ticket carried no *What shipped* record; the commits above are that record.
