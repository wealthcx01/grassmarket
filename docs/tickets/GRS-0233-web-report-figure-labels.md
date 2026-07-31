# GRS-0233 — Web report figures: label the bars, keep the story's order

**Status:** Planned (2026-07-31, first-time-user review G5). **Priority:** MED-HIGH. **Type:** Bug.
**Loop:** client-report hardening. **Extends GRS-0220.** **Relates to:** GRS-0206, GRS-0219.

## Why

On the shared web page (`/r/<token>`, WeBull, 31/07/2026):

- The module-maturity figure is **nine solid bars with no labels**, followed by a separate
  name/value grid *in a different order* (bars sorted ascending by value; the grid reads
  column-major). A client cannot map bar to module without counting rows against a differently
  sorted table. The PDF's radar labels every spoke; the web rendition — the one the client actually
  interacts with — is the weaker of the two.
- The value build-up figure sorts its four bars by value (Powers 29, Platform Value 55,
  Infrastructure 58, Business 77) under the caption "How Platform Value builds up from the
  underlying indices" — the sort destroys the composition the caption promises. The PDF keeps
  Business → Powers → Infrastructure → Platform Value; the two renditions of the same figure
  disagree, which is the drift GRS-0211 exists to prevent.

GRS-0220 disclosed "bars, not the radar" as an accepted answer; it did not disclose bars without
labels. Aria-labels carrying every number exist and are good; sighted clients deserve the same.

## Scope

1. **Every bar is labelled** — module name and value on or beside the bar, at phone widths too
   (wrap or abbreviate by measurement, not truncation). The separate grid either goes or becomes a
   true table that matches the figure's order.
2. **Composition figures keep composition order.** The build-up chart renders Business → Powers →
   Infrastructure → Platform Value with the composite visually distinguished, matching the PDF.
   Weakest-first ordering stays where weakest-first means something (the module figure, both
   renditions, as the appendix caption already states).
3. **Parity is asserted, not hoped.** The content-parity test (GRS-0220 test 2) extends to figure
   ordering and label sets: same figures, same order, same labels across PDF and web.
4. **Hover explains, where it can.** On pointer devices a bar's title attribute (or equivalent)
   carries the module's one-line meaning — the cheap version of GRS-0220 scope 3's
   hover-to-explain, without waiting on GRS-0206.

## Test plan

1. Vitest: each rendered bar exposes its module name and value as visible text; build-up order is
   the composition order.
2. Parity test: figure order and label sets identical across renditions for the golden-master run.
3. Manual: WeBull share page re-issued, screenshots desktop + phone width, in the PR.
4. Standing gate: pytest, pyright, tsc, ESLint, per-file vitest.

## Out of scope

- Rive/interactive radar (GRS-0206).
- The watermark (GRS-0229).

## Acceptance

The founder reads the web report's figures without the grid, and the build-up chart tells the same
story in the same order as the PDF.
