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
