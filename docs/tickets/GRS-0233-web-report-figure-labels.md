# GRS-0233 — Web report figures: label the bars, keep the story's order

**Status:** DONE (reconciled 2026-08-01). _Previously recorded as: Planned (2026-07-31, first-time-user review G5). **Priority:** MED-HIGH. **Type:** Bug._
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

---

## Status reconciliation — 2026-08-01

**DONE.** All four scopes.

## What shipped

**1 — Every bar is labelled.** The figure was nine unlabelled `<rect>`s in a stretched SVG with the
names in a *separately sorted* grid underneath, so a client had to count rows against a mismatched
table. It is now rows of HTML: label, bar, value on one line. At phone widths the label takes its
own line and **wraps** rather than truncating — the ticket's "by measurement, not truncation". The
separate key grid is gone, and its now-dead CSS with it.

**2 — Composition figures keep composition order.** The renderer sorted *every* figure ascending, so
the value build-up rendered Powers → Platform Value → Infrastructure → Business under a caption
promising a build-up. `Series` now declares whether its order is binding; the build-up says yes, the
ranked figures say no and are still shown weakest-first, because weakest-first is what their caption
says they are.

**3 — Parity is asserted.** The payload carries the order *and* whether that order is significant,
so the web renderer has no reason to invent one. A backend test asserts the contract
(`value_buildup.ordered is True`, its four labels in build-up order, the ranked figures not
claiming a binding order) and a vitest asserts the renderer honours it both ways.

**4 — Hover explains.** Each bar carries its module's coverage: "Back Office: scored on 3 of 4
applicable subcomponents." Coverage rather than a registry description, deliberately — the score
alone does not tell a reader how much of the module was assessed, and a module scored on two
subcomponents of nine looks identical to one scored on all nine. That is the question a client asks
first when a number looks low.

## Compatibility

`notes` and `ordered` are optional on the wire. A link issued before this change carries neither and
still renders — tested — falling back to weakest-first, which is what those snapshots already showed.
