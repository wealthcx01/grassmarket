# Motion and diagrams

Course diagrams and UI motion, authored as JSON and compiled to real `.riv` files with
[`George-RD/rive-rs-cli`](https://github.com/George-RD/rive-rs-cli) (MIT). See
`docs/adr/ADR-0049-motion-system.md` for what was verified and what is still open, and
`docs/tickets/GRS-0225-course-diagrams.md` for why these particular diagrams exist.

```
authoring.py                 shared palette, type scale and layout helpers
courses/openbb/build.py      writes one JSON scene per diagram
courses/openbb/*.json        the scene specs — this is the source, review these
assets/fonts/                vendored Inter subset, SIL OFL 1.1, licence beside it
build/                       generated .riv, rendered stills and .svg, all committed
render.sh                    generate + validate + render, and FAIL on a blank frame
svg_export.py                the same scenes to SVG — this is what the course serves
```

## Two renderers, one source

A scene has three outputs and they all come from the JSON, never from each other:

| Output | Made by | Used for |
|---|---|---|
| `.riv` | `rive-cli generate` | motion, and the runtime decision still open in GRS-0206 |
| `frame_*.png` | `rive-cli render` | reviewing the drawing in a PR; deck assets |
| `.svg` | `svg_export.py` | what the Academy actually serves, via `LessonAsset` |

`rive-cli` has no vector output — `render` writes PNG and `SVGAsset` is an input type only — and
`LessonAsset` refuses raster, so the SVG is emitted from the scene rather than converted from the
`.riv`. See ADR-0049's 2026-07-29 amendment.

## Regenerating

```bash
uv run python design/motion/courses/openbb/build.py     # scenes
RIVE_CLI=/path/to/rive-cli design/motion/render.sh      # .riv + stills
uv run python design/motion/svg_export.py               # .svg + the content module
```

The last one also rewrites `src/grassmarket/workbench/content/openbb_diagrams.py`, which is the
generated module the course imports. `tests/test_course_diagrams.py` fails if it has drifted from
the scenes, so forgetting this step is caught rather than shipped.

## Checking the SVG against the Rive render

The two renderers can disagree, so the still is the reference. Render the SVG in Chromium with the
vendored font at the artboard size, then compare per-region ink coverage against `frame_00000.png`
— downscale both to a coarse grid and compare cell luminance. As of 2026-07-29 all nine agree to
within a mean absolute difference of 1.3/255, worst single region 42; the differences are text
metrics, since Rive lays out text itself and a browser lays out SVG text. A structural comparison
is the right one here — per-pixel would fail on antialiasing alone.

This needs the toolchain and a browser, so it is a local gate. CI checks everything that does not:
export, drift, the sanitiser allowlist, and the emitter's refusals.

`rive-cli` has no published releases yet, so build it from source with `cargo build --release`.
The Rust toolchain is a build-time dependency only; the product ships the output.

**Chromium.** `rive-cli` launches Chromium without `--no-sandbox`, which is the right default. On a
host with unprivileged user namespaces restricted (Ubuntu 23.10+ AppArmor) Chromium aborts with
`No usable sandbox!` and the render times out waiting for DevTools. Point `RIVE_CHROME` at a shim
that adds the flag rather than changing the tool.

## Two rules that will catch you

**Rive paints the FIRST declared sibling on top** — the reverse of SVG and every design tool, and
silent when you get it wrong. `stack()` exists so you write front-first on purpose. Two of these
seven diagrams shipped their first render with arrowheads hidden behind the boxes they pointed at.

**A font asset's `source` must resolve inside the project owning the scene**, which is why Inter is
vendored here rather than referenced from the toolchain.

## Animation

`linked_parameters` is animated; the rest are static, and a static diagram is the right default.
Motion is for a diagram whose subject IS movement — here, one field changing and three widgets
following it, which is the demo an advisor gives.

Two format rules shaped how it is built:

- **Text content is not animatable.** Only `font_size`, `line_height`, `letter_spacing` and the
  transform properties are. So the ticker changing is a cross-fade between two text runs stacked at
  the same position, not an edit.
- **`stroke.thickness` is not animatable either.** The signal travelling down the wire is a colour
  change on filled rectangles, which is why `line()` builds a filled rectangle rather than a
  stroked path.

Everything eases. Linear interpolation is the giveaway of a diagram animated by a machine rather
than designed, and avoiding it costs one field.

## What the check does and does not prove

`render.sh` fails a blank frame or an implausibly low colour count. That catches a scene that drew
nothing. It does **not** catch a scene that drew the wrong thing: the first AGPL render ran its
right-hand box off the artboard and into its neighbour, and passed every check. The committed
stills exist so a human can see that in review.

For an animated scene it also samples six frames across the loop and **fails if they are
byte-identical**, which is the real check for "the animation is not animating". Distinct colour
counts are the documented false negative: they can stay identical while the picture changes, and
stay identical while it does not. Rendering is deterministic, so hashes are stable.
