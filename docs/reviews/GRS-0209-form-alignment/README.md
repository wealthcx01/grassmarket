# GRS-0209 — the Operating Model dropdown alignment, measured

The founder reported this twice. GRS-0178 was meant to fix it and its test passed, because that test
compared style **declarations** and the declarations were already identical. The defect was in the
rendered geometry, which no such test can see. So this time it was measured on the running page.

`measure-form.mjs` drives headless Chromium against a local dev stack, logs in, loads
`/assessments` at three viewport widths, and reads `getBoundingClientRect()` off the three controls.
Re-run it with `bun measure-form.mjs <label> <outdir>`.

## What was measured

Identical at 1280, 1440 and 1920 — the misalignment was not width-dependent.

| | subject input | Operating Model select | submit button | select top − input top |
|---|---|---|---|---|
| **Before** | top 299.7, height 40.9 | top **323.1**, height 40.9 | top 328.1, height 35.9 | **23.4px** |
| **After** | top 299.7, height 40.9 | top **299.7**, height 40.9 | top 299.7, height 40.8 | **0px** |

## The cause — one, not two

The form grid aligned its cells on their **end** (bottom). The subject cell is the taller of the two,
because `EntitySubjectField` always renders a caption under its input ("✓ Linked to…", or the
unlinked hint). Aligning on the bottom therefore pushed that input *up* by the height of its own
caption, and 23.4px is that caption plus its margin.

Two things worth recording, because both contradict what the fix was originally written against:

- **The controls were never mismatched in height.** Input and select both measured 40.9px. An earlier
  draft of this fix pinned a `--field-control-height: 2.35rem` (37.6px) token described as "the
  input's own natural height, so nothing resizes" — that would in fact have *shrunk* both controls by
  3.3px. The token now used is a `min-height` of 2.55rem, which matches what they already reach, so
  it resizes neither; it exists so the submit button (35.9px on its own) reaches the same row height.
- **A `<label>` around the submit button renames it.** A `<button>` is a labelable element, so
  wrapping it in the field wrapper made its accessible name the empty spacer label rather than
  "Create and open". The button's cell is a `<div>` for that reason, and a test locks it.

## What the unit tests can and cannot prove

`FormField.test.tsx` and the GRS-0209 block in `app/assessments/page.test.tsx` lock the *structure*
the fix depends on: one wrapper shape per cell, captions rendered after the control, the shared
control-height class on every control, and the button keeping its own accessible name. jsdom has no
layout engine, so the alignment itself is proved by the before/after measurements above — not by
those tests. That distinction is the whole point of this ticket.
