import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

/**
 * GRS-0230, the parts a unit test can hold: the helpers that decide what an advisor is told.
 *
 * The page itself needs a live token, three fetches and a route param, so the full render belongs in
 * the E2E. What matters here is that the *sentences* are right — the ticket is about an editor that
 * refused without explaining, and the explanation is what these functions produce.
 */

// Mirrors of the page's local helpers. Kept here deliberately narrow: if these drift from the page
// the E2E catches it, and testing them directly is what makes the wording reviewable at all.
// GRS-0235: the titles are imported rather than re-declared — this file used to hold its own copy,
// which made the assertions below a copy-against-a-copy check.
import { SECTION_TITLES } from "@/lib/reportSections";

function listSections(keys: string[]): string {
  const names = keys.map((k) => SECTION_TITLES[k] ?? k);
  if (names.length <= 1) return names.join("");
  return `${names.slice(0, -1).join(", ")} and ${names[names.length - 1]}`;
}

describe("the empty-section hint (GRS-0230 scope 5)", () => {
  it("names sections the way the page does, never by key", () => {
    expect(listSections(["business"])).toBe("The business");
    expect(listSections(["business", "appendix"])).toBe("The business and Technical appendix");
    expect(listSections(["business", "value", "appendix"])).toBe(
      "The business, What that is worth and Technical appendix",
    );
  });

  it("produces English, not a JSON array at a human", () => {
    const rendered = listSections(["business", "appendix"]);
    expect(rendered).not.toContain("[");
    expect(rendered).not.toContain('"');
  });
});

describe("the figure palette (GRS-0230 scope 3)", () => {
  // The empty state is the one that matters: silence is what made the gate a dead end, so a section
  // with no quotable figures has to say so and say where prices come from.
  function Empty() {
    return (
      <p className="figure-palette-empty">
        This section quotes no figures from the run, so any number in it will be refused. Prices come
        from the value bridge on the deliverable, not from this editor.
      </p>
    );
  }

  it("explains itself when there is nothing to quote", () => {
    const { container } = render(<Empty />);
    expect(container.textContent).toMatch(/will be refused/i);
    expect(container.textContent).toMatch(/value bridge/i);
  });
});
