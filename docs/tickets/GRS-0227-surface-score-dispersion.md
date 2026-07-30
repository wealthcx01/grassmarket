# GRS-0227 — Surface the dispersion beside the score

**Status:** Planned (2026-07-30, arising from GRS-0223). **Priority:** HIGH. **Loop:**
founder-feedback remediation, Wave 1. **Depends on:** GRS-0223 (the measurement that motivates it).

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
