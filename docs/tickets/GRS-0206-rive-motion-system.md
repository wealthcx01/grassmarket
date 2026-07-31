# GRS-0206 — Rive as the diagram and motion system

**Status:** OPEN (reconciled 2026-08-01). _Previously recorded as: Planned (2026-07-26, staging review item 4; rewritten 2026-07-29 after actually reading._
the repository). **Priority:** HIGH. **Loop:** founder-feedback remediation, Wave 1.

## Why this ticket was rewritten

The first version of this ticket was a spike asking whether Rive earns its weight, written on the
assumption that Rive means an editor, a designer, and a WASM runtime we would be adopting on faith.
That assumption was wrong, and it was wrong because the ticket was written without reading the
repository the founder linked.

`George-RD/rive-rs-cli` is a tool built specifically so that **an AI agent can author animations
programmatically**. Its own README: "Write Rive animations as JSON. Compile them to real `.riv`
files. Prove they work before you ship." Six of its ten showcase examples were authored end to end
by fresh-context agents.

That changes the question from *should we adopt Rive* to *where do we use it*, and it removes the
blocker I had assumed existed. There is no editor in the loop and no designer dependency for the
kind of work this programme needs: explanatory diagrams and small interactive pieces.

## What the tool actually does

- `new` scaffolds a working scene; `generate` compiles a JSON SceneSpec to a real `.riv`; `validate`
  checks binary structure; `render` drives **headless Chromium with the real Rive runtime** and
  writes PNG frames; `compare` does pixel-difference testing against a reference.
- `schema`, `types` and `describe` are self-describing, so an author never guesses a field name.
  `describe <type>` is generated from the same code that compiles keyframes, so it cannot drift.
- `render --preview` prints an **ASCII coverage map**, dominant-colour percentage and content
  bounds, and writes `preview.txt` and `manifest.json`. This matters more than it sounds: it means
  a non-visual workflow can verify a render actually drew something, which is the difference
  between "the file compiled" and "the animation works".
- Text and images work, with **embedded asset bytes**. A licensed Inter subset ships in the repo.
- Licence: **MIT**.

Constraints found by reading, to be confirmed by building:

- **No published releases yet**, so installation is `cargo build --release` from source. That is a
  build-time dependency for us, not a runtime one, since the output is a `.riv` file.
- Rendering requires Chromium. We already have one for the browser harness.
- Rive draws the **first declared sibling on top**, the reverse of SVG and HTML. Noted here because
  it is the tool's own stated most-expensive mistake.

## Scope

1. **Get it building and prove the loop**, on this machine and in CI: scaffold, generate, validate,
   render, and inspect the preview output. Record the toolchain requirements and the build time in
   `docs/adr/ADR-0049-motion-system.md`. A `.riv` we generated and rendered is the evidence, not a
   claim that it worked.
2. **Decide how a `.riv` reaches a page.** The Rive web runtime is a WASM payload, so this is the
   one real cost and it needs measuring rather than assuming. Options to weigh with numbers:
   loading the runtime only on pages that carry a `.riv`; rendering to static frames at build time
   where the piece does not need to be interactive; or accepting it globally.
3. **Where it goes first**, in this order:
   - **Course diagrams** (GRS-0225). The most valuable and the least risky, because a diagram can
     fall back to a static frame.
   - **The assessment wizard**, which is the founder's named surface: progress through modules,
     and what a score is made of.
   - **The pipeline**, for stage transitions.
   - **The interactive client report** (GRS-0220), where an animated value build-up would carry
     more than a static chart.
4. **Assets and provenance.** `.riv` files and their JSON SceneSpecs both committed, the JSON being
   the source. A binary in the repository whose source is not next to it is not reviewable.
5. **Accessibility is not optional.** Every animation respects `prefers-reduced-motion` and has a
   static fallback carrying the same information. Motion is never the only way to know something.
6. **Design tokens.** Colours and timings come from the Bruntsfield system, not from whatever the
   scaffold template defaulted to.

## Test plan

1. A generate-validate-render check in CI over every committed SceneSpec: it compiles, the binary
   validates, and the render is **not blank**. The blank check is the one that catches real
   breakage, because a file can validate and still draw nothing.
2. `compare` against committed reference frames, so a change to a scene that alters its appearance
   is visible in review as a pixel delta rather than as a binary diff nobody can read.
3. Vitest per file: every component carrying a `.riv` renders its static fallback with the same
   text content when motion is disabled.
4. A bundle-size assertion against the figure recorded in the ADR.
5. Standing gate: pytest, pyright, tsc, ESLint.

## Out of scope

- Course content itself (GRS-0215 to GRS-0218). This ticket supplies the diagram capability; the
  courses decide what to draw.
- The report renditions (GRS-0219, GRS-0220), which consume this if the ADR says yes.

## Acceptance

A `.riv` file generated from JSON in this repository, rendered and verified by the tool, displayed
in the studio with a static fallback and reduced-motion respected, and ADR-0049 recording the
measured bundle cost rather than an estimate of it.

---

## Status reconciliation — 2026-08-01

**OPEN.** No implementing commit on main; genuinely unbuilt.
