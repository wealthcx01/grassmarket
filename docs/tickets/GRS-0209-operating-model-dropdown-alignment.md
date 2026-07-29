# GRS-0209 — The Operating Model dropdown still does not line up

**Status:** Planned (2026-07-26, staging review item 7). **Priority:** MED. **Type:** Bug.
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
