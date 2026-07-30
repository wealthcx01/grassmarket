/**
 * The real course diagrams, through the real sanitiser (GRS-0225).
 *
 * `svg.test.ts` proves the sanitiser refuses what it should. This proves it *accepts* the nine
 * drawings the OpenBB course actually ships, which is the failure that would otherwise reach an
 * advisor: `sanitizeSvg` rejects a whole document rather than stripping part of it, so one
 * unexpected attribute turns a diagram into "a diagram on this lesson failed sanitisation".
 *
 * It reads the committed `.svg` files rather than a fixture, so adding a construct to
 * `design/motion/svg_export.py` that the allowlist does not cover fails here rather than in front
 * of the founder. The Python side (`tests/test_course_diagrams.py`) asserts those files match the
 * strings the course serves.
 */
import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";

import { describe, expect, it } from "vitest";

import { sanitizeSvg, type SvgElementNode } from "@/lib/svg";

const BUILD = join(import.meta.dirname, "..", "..", "design", "motion", "build", "openbb");
const diagrams = readdirSync(BUILD)
  .filter((f) => f.endsWith(".svg"))
  .sort();

describe("course diagrams", () => {
  it("finds the committed diagrams", () => {
    // A directory read that matched nothing would make every case below vacuously pass.
    expect(diagrams.length).toBeGreaterThanOrEqual(9);
  });

  it.each(diagrams)("%s survives sanitisation", (file) => {
    const tree = sanitizeSvg(readFileSync(join(BUILD, file), "utf8"));
    expect(tree).not.toBeNull();
  });

  it.each(diagrams)("%s keeps its viewBox, so it scales in the page", (file) => {
    const tree = sanitizeSvg(readFileSync(join(BUILD, file), "utf8")) as SvgElementNode;
    expect(tree.attributes.viewBox).toMatch(/^0 0 \d+ \d+$/);
  });

  it.each(diagrams)("%s still has its shapes after sanitisation", (file) => {
    const tree = sanitizeSvg(readFileSync(join(BUILD, file), "utf8")) as SvgElementNode;
    // A document can survive the sanitiser and arrive empty if every child were dropped; it does
    // not strip, but asserting the drawing is still here costs one line.
    expect(tree.children.length).toBeGreaterThan(5);
    const kinds = new Set(
      tree.children.filter((c) => c.type === "element").map((c) => c.name),
    );
    expect(kinds.has("g") || kinds.has("text")).toBe(true);
  });
});
