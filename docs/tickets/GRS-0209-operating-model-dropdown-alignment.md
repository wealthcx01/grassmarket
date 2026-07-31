# GRS-0209 — The Operating Model dropdown still does not line up

**Status:** DONE (reconciled 2026-08-01). _Previously recorded as: Planned (2026-07-26, staging review item 7). **Priority:** MED. **Type:** Bug._
**Loop:** founder-feedback remediation, Wave 1. **Follows GRS-0178.**

## Why

GRS-0178 was meant to fix this. The founder looked again on 2026-07-26 and it is still wrong:
"The drop down for 'Operating Model' still doesn't align properly."

GRS-0178 aligned the new-assessment form by restructuring it, and the fix was verified in a unit
test rather than against a rendered page. Whatever is still off is therefore something the test
cannot see: a control height, a label baseline, a native select that does not match the height of
the input beside it, or a grid column that collapses at the founder's viewport width.

## Scope

1. **Reproduce it first.** Screenshot the new-assessment form on staging at 1280, 1440 and 1920
   wide and put the screenshots in the PR. Name the discrepancy in pixels before changing
   anything. If it reproduces only at one width, say which.
2. **Fix the cause, not the symptom.** Likely candidates, to be confirmed rather than assumed: the
   native `<select>` inheriting a different line-height and border-box from the text input beside
   it, the label row using a different bottom margin, or the two controls sitting in grid cells
   with different alignment.
3. **Make it hold.** The control pair becomes a shared form-field component with one set of height
   and baseline tokens, so the next field added cannot drift.
4. **After-screenshots at the same three widths**, in the PR beside the before ones.

## Test plan

1. Vitest on the form component asserting both controls resolve to the same computed height class
   and share the field wrapper.
2. Manual screenshots at three widths, before and after, in the PR. This is the part that actually
   proves the ticket, because the unit test is what missed it last time.
3. Standing gate: tsc, ESLint, per-file vitest.

## Out of scope

- Any change to the form's fields, order or behaviour. GRS-0178 settled the structure; this is
  alignment only.
- The smart-search control itself (GRS-0210).

## Acceptance

The founder opens the new-assessment form and the two controls line up. The PR shows before and
after screenshots at three widths.

## What shipped

Measured first, on the rendered page, at 1280/1440/1920 — all three identical, so it was never
width-dependent. **The Operating Model select sat 23.4px below the subject input; it is now 0px.**
Screenshots, the raw geometry and the re-runnable measuring script are in
`docs/reviews/GRS-0209-form-alignment/`.

The cause was a single one, and not the one this ticket guessed at. The grid aligned cells on their
**end**, and `EntitySubjectField` always renders a caption under its input, so the caption's height
pushed that input up out of line. `align-items: start` fixes it: the label rows share a baseline, so
the controls beneath them do too, and a field that grows a caption can no longer move its own
control.

Two of the ticket's assumptions were wrong, and measuring is what caught them:

- **The controls' heights never differed.** Both measured 40.9px, so the suspected "native select
  computes taller" was not the defect here. Only the submit button was short (35.9px), because
  `.btn` carries its own padding. `--field-control-height` is therefore a `min-height` matching what
  the inputs already reach — it resizes neither of them, and brings the button up to the row.
- **A `<label>` wrapper renames a `<button>`.** Routing the button through the shared field
  component made its accessible name the empty spacer label instead of "Create and open". Its cell
  is a `<div>`, and a test locks that.

Scope item 3 is met by `frontend/components/FormField.tsx`: every cell is label-above-control with
captions rendered *below*, so the next field added cannot reintroduce this. The unit tests lock that
structure only — jsdom has no layout engine, which is exactly why GRS-0178's test passed on a broken
page. The pixels are proved by the measurements, not the tests.

---

## Status reconciliation — 2026-08-01

**DONE.** Landed on main in `83ce92c` (GRS-0209: measure the misalignment, then fix its one cause).
