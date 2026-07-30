# ADR-0049 — Rive as the diagram and motion system

- **Status:** Accepted for diagrams. **Open** for in-page motion, pending a measured runtime cost.
- **Date:** 2026-07-29
- **Driver:** Founder review 2026-07-26, item 4 ("use the Rive CLI to generally improve the overall
  UI") and item 14 ("use the Rive CLI to totally reconstruct these"). Tickets GRS-0206, GRS-0225.

## Context

The first version of GRS-0206 asked whether Rive earns its weight, on the assumption that Rive
means a visual editor, a designer in the loop, and a WASM runtime adopted on faith. That ticket was
written without reading the repository the founder linked, and every part of the assumption was
wrong.

`George-RD/rive-rs-cli` (MIT) exists specifically so an agent can author animations
programmatically. Its README: "Write Rive animations as JSON. Compile them to real `.riv` files.
Prove they work before you ship." Six of its ten showcase examples were authored end to end by
fresh-context agents.

## Decision

**Adopt it for authoring diagrams now.** Course diagrams are written as JSON scene specs under
`design/motion/`, compiled to `.riv`, and rendered to stills. The still is committed alongside, and
is both the reduced-motion fallback and the deck asset.

**Do not yet adopt the web runtime.** Putting a `.riv` on a page means shipping the Rive WASM
runtime, and that cost has not been measured. Until it is, the committed stills are what the
product displays. This ADR will be amended with the number, not with an estimate of it.

The split matters: it lets the diagrams land in the courses immediately without a bundle decision
blocking them, and it means a negative runtime finding costs us nothing already built.

## What was verified on 2026-07-29, not assumed

Built from source, `rive-cli 0.1.0`, `cargo build --release`, 4m46s. There are **no published
releases**, so source is the only route and a Rust toolchain is a build-time dependency. It is not
a runtime dependency: the output is a file.

The loop, run against seven real scenes:

```
generate → validate → render
```

- `generate` produced 12–16KB `.riv` files. `validate` reported `RIVE v7.0 … valid`.
- `render` drove headless Chromium with the **real Rive runtime**. This is the gate that matters:
  the toolchain's own guidance is explicit that a file can validate and still be rejected by the
  runtime or draw nothing.
- `render --preview` prints an ASCII coverage map, dominant-colour percentage and content bounds.
  That is how a non-visual workflow verifies a render, and `design/motion/render.sh` fails the
  build on a blank frame or an implausibly low colour count.
- Motion is confirmed by **frame hashes**, not colour counts. Identical colour counts across frames
  is the documented false-negative for "nothing is animating".

### Chromium

rive-cli launches Chromium **without** `--no-sandbox`, which is the correct default. On a host with
unprivileged user namespaces restricted (Ubuntu 23.10+ AppArmor) Chromium aborts with
`No usable sandbox!` and the render times out waiting for DevTools. Point `RIVE_CHROME` at a shim
that adds the flag. Do not patch the tool, and do not add the flag anywhere it would apply to a
browser handling untrusted content.

## Two rules that cost real time to discover

1. **Rive paints the FIRST declared sibling on top.** The reverse of SVG, HTML and every design
   tool. It is silent: the scene compiles, validates, and renders as a flat block of whatever was
   declared last. `authoring.stack()` exists so authors write front-first explicitly. Two of the
   seven diagrams shipped their first render with arrowheads hidden behind the boxes they pointed
   at, for exactly this reason.
2. **A font asset's `source` must resolve inside the project owning the scene.** Hence the vendored
   Inter subset at `design/motion/assets/fonts/`, with its **SIL OFL 1.1** licence text beside it.

## A limit of the automated check

`render.sh` proves a diagram is not blank. It does not prove the diagram is *right*. The first AGPL
render ran its right-hand box off the artboard and into its neighbour, and passed every check.
Diagrams get looked at, and the committed still is what makes that review possible in a pull
request.

## Amendment, 2026-07-29: how a diagram reaches the page

The original decision said the committed stills are what the product displays. That turned out not
to be possible as written, and the fix is better than the plan.

**The stills are PNG, and `LessonAsset` refuses raster.** The contract requires an inline SVG string
and says so for a reason: a published `CourseVersion` is an immutable snapshot, and raster is out of
contract because a photograph belongs behind a `SourceRef`. So the choice was to amend the contract
to carry a raster data URI, or to produce vector.

**`rive-cli` cannot produce vector.** Its `render` drives headless Chromium and writes PNG; `SVGAsset`
exists in its object registry only as an input you embed. Checked against `--help`, `render --help`
and the crate source.

**So the SVG comes from the same source, by a second renderer.** `design/motion/svg_export.py` reads
the SceneSpec JSON — not the compiled `.riv` — and emits SVG. The scene stays the single source of
truth with three outputs: the `.riv` for motion, the PNG still for review and decks, and the SVG the
course actually serves. No contract amendment, no data URI, and no bundle decision.

Two things this costs, both accepted:

- **Two renderers of one source can disagree.** Verified by rendering the SVG in Chromium against
  the Rive still and comparing per-region ink coverage: mean absolute difference under 1.3/255 on
  all nine, worst single region 42. The differences are text metrics, which is expected — Rive lays
  out text itself and a browser lays out SVG text. The procedure is in `design/motion/README.md`;
  it needs the toolchain and so is a local gate, not a CI one.
- **The emitter must refuse what it cannot render.** An unknown node type, an unimplemented
  property, or an animated property it cannot resolve into a still all raise. A silently dropped
  property would produce a diagram that looks finished and is wrong — the same class of failure as
  the AGPL box that rendered off the artboard and passed every check.

The still is also the reduced-motion fallback, so the export resolves animated properties at frame
0 rather than using authored values. `linked_parameters` proves why: it cross-fades two text runs
stacked at one position, and ignoring opacity drew both on top of each other.

## Consequences

- Nine OpenBB diagrams exist as reviewable JSON with committed binaries, stills and SVG (GRS-0225),
  and each is on the slide whose idea it carries.
- CI needs the toolchain to regenerate them, or it needs to trust the committed artefacts. Until
  CI billing is restored this is a local gate; the render script is the thing CI will run.
- The in-page runtime decision stays open and belongs to GRS-0206, alongside GRS-0220's interactive
  client report, which is the other surface that would justify the payload.
- If the runtime cost turns out not to be worth it, the diagrams remain useful as stills and as
  deck assets. Nothing built here is wasted by a no.
