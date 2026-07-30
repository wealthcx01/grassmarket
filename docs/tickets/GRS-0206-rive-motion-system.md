# GRS-0206 — Evaluate and integrate Rive for the wizard and pipeline

**Status:** Planned (2026-07-26, staging review item 4). **Priority:** MED.
**Loop:** founder-feedback remediation, Wave 1.

## Why

The founder asked us to use the Rive CLI (https://github.com/George-RD/rive-rs-cli) to lift the
overall UI, naming the assessment wizard and the pipeline. Both screens are currently static: the
wizard advances between modules with no sense of progress or place, and the pipeline moves cards
between columns with no motion at all. Rive gives us authored, state-machine-driven animation that
a designer controls rather than something hand-rolled in CSS per component.

This ticket is deliberately a spike plus a first integration, not a rewrite. Rive is a runtime
dependency with a WASM payload, and the honest sequence is to prove it earns its weight on two
screens before it goes everywhere.

## Scope

1. **Spike (half of the ticket, written up before any component changes).**
   - Clone and build `George-RD/rive-rs-cli`. Record the version and the build steps in
     `docs/adr/ADR-0049-motion-system.md`.
   - Measure the runtime cost: bundle size added to the Next.js client, first-paint impact on the
     wizard, and behaviour with `prefers-reduced-motion`.
   - Confirm the licence terms for the runtime and for authored `.riv` files.
   - State plainly whether Rive is the right tool here or whether authored CSS/Framer transitions
     do the same job for less. A negative recommendation is an acceptable outcome and must be
     written up with the evidence, not quietly dropped.
2. **If the spike says yes**, integrate on exactly two surfaces:
   - **Wizard**: a progress state machine that shows which module you are in, how many remain,
     and which are complete, driven by the same coverage data the header already has.
   - **Pipeline**: card transitions between stages, and a stage-count state that reacts to the
     forecast numbers already on screen.
   - Assets committed under `frontend/public/motion/` with their `.riv` sources under
     `design/motion/` so they can be re-authored.
3. **Accessibility is not optional.** Every animation respects `prefers-reduced-motion` and has a
   static fallback that carries the same information. Motion never becomes the only way to know
   something.
4. **Design tokens.** Colours and timings come from the Bruntsfield design system, not from
   whatever the Rive editor defaulted to.

## Test plan

1. Vitest per file for the wizard progress and pipeline card components, asserting the static
   fallback renders and carries the same text content when motion is disabled.
2. A bundle-size assertion in CI: the client bundle grows by no more than the figure recorded in
   the ADR.
3. Manual: record the wizard and pipeline before and after, attach both to the PR.
4. Standing gate: pytest, pyright, tsc, ESLint.

## Out of scope

- Deliverable and report animation (GRS-0211 covers the interactive client page, which may reuse
  the runtime this ticket introduces).
- Course animation assets (GRS-0215).
- Any change to what the wizard or pipeline actually do.

## Acceptance

The founder opens the wizard and the pipeline on staging and the motion reads as deliberate. The
ADR records the measured cost and the decision, including a no if that is what the spike found.
