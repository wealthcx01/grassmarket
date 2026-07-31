/**
 * GRS-0182: the wizard's two-column grid had no breakpoint, so below ~900px the fixed 20rem rail
 * crushed the content column it is meant to annotate.
 *
 * A media query cannot be exercised in jsdom (`matchMedia` is stubbed and layout is never
 * computed), and rendering the whole WizardClient would mean mocking the entire API surface to
 * assert one class name. So this checks the contract at its two ends instead: the component
 * applies the class, and the stylesheet defines the breakpoint behind it. That is exactly the pair
 * that breaks if someone removes either half, which is the regression worth catching.
 */

import { readFileSync } from "node:fs";
import { join } from "node:path";

import { describe, expect, it } from "vitest";

const ROOT = join(__dirname, "..", "..", "..");
const read = (...parts: string[]) => readFileSync(join(ROOT, ...parts), "utf8");

describe("wizard two-column layout (GRS-0182)", () => {
  const component = read("app", "assessments", "[id]", "WizardClient.tsx");
  const css = read("app", "globals.css");

  it("applies the breakpoint class to the grid wrapper", () => {
    expect(component).toContain('className="wizard-two-col"');
  });

  it("no longer hard-codes the two-column track inline, where no media query can reach it", () => {
    expect(component).not.toContain('gridTemplateColumns: "minmax(0,1fr) 20rem"');
  });

  it("defines the two-column track and a single-column fallback below 900px", () => {
    expect(css).toMatch(/\.wizard-two-col\s*\{[^}]*grid-template-columns:\s*minmax\(0,\s*1fr\)\s+20rem/);
    expect(css).toMatch(/@media\s*\(max-width:\s*900px\)/);
    const breakpoint = css.slice(css.indexOf("@media (max-width: 900px)"));
    expect(breakpoint).toMatch(/\.wizard-two-col\s*\{[^}]*grid-template-columns:\s*minmax\(0,\s*1fr\)\s*;/);
  });

  it("stops the rail being sticky once it is stacked", () => {
    // A sticky element inside a single stacked column just pins to the top oddly.
    const breakpoint = css.slice(css.indexOf("@media (max-width: 900px)"));
    expect(breakpoint).toMatch(/\[data-wizard-rail\][^}]*position:\s*static/);
    expect(component).toContain("data-wizard-rail");
  });
});

/**
 * GRS-0221: the founder reported the "recommended to sell" panel sliding underneath the pinned
 * Platform Value card. Cause: the rail's FIRST CHILD was sticky while its siblings scrolled on in
 * the same grid column. The rail now sticks as one block instead, so nothing shares a column with
 * a pinned element.
 *
 * These are guards, not the proof. The proof is measured on the rendered page — 119px of overlap
 * before, 0px after, at four viewports — in `docs/reviews/GRS-0221-stage6-layout/`. That split is
 * deliberate and is the GRS-0209 lesson: a test comparing style declarations passed while the page
 * was visibly wrong, because geometry is not declarations. What a unit test CAN do is catch the
 * declaration going back, which is the regression that would silently undo the measured fix.
 */
describe("wizard rail stickiness (GRS-0221)", () => {
  const component = read("app", "assessments", "[id]", "WizardClient.tsx");
  const css = read("app", "globals.css");

  it("gives no panel its own stickiness — only the rail container is pinned", () => {
    // The exact regression: someone re-adds position:sticky to a card inside the rail, and it
    // starts covering its siblings again.
    expect(component).not.toMatch(/position:\s*["']sticky["']/);
  });

  it("sticks the rail container itself", () => {
    const rule = css.slice(css.indexOf(".wizard-two-col [data-wizard-rail] {"));
    expect(rule.slice(0, rule.indexOf("}"))).toMatch(/position:\s*sticky/);
  });

  it("caps the pinned rail's height and lets it scroll inside itself", () => {
    // Without this a rail taller than the viewport pins its top and puts its bottom permanently
    // out of reach — no scroll gesture can get there.
    const rule = css.slice(css.indexOf(".wizard-two-col [data-wizard-rail] {"));
    const body = rule.slice(0, rule.indexOf("}"));
    expect(body).toMatch(/max-height:\s*calc\(100vh/);
    expect(body).toMatch(/overflow-y:\s*auto/);
  });

  it("pins the rail clear of the sticky site header, not underneath it", () => {
    // Measured: with top: 1rem the rail sat 44px behind the z-index-50 header, which ate the score
    // card's own heading. The offset must be expressed against the header's height token so the
    // two cannot drift apart.
    const rule = css.slice(css.indexOf(".wizard-two-col [data-wizard-rail] {"));
    const body = rule.slice(0, rule.indexOf("}"));
    expect(body).toMatch(/top:\s*calc\(var\(--topbar-height\)/);
    expect(body).toMatch(/max-height:\s*calc\(100vh\s*-\s*var\(--topbar-height\)/);
  });

  it("drops stickiness entirely on a short viewport", () => {
    // A pinned block with its own scrollbar owning most of a 640px-tall screen is worse than one
    // that simply scrolls with the page.
    const shortVp = css.slice(css.indexOf("@media (max-height: 700px)"));
    expect(shortVp).toMatch(/\[data-wizard-rail\][^}]*position:\s*static/);
  });
});
