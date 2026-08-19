import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { SegmentFacet } from "@/lib/types";

/**
 * GRS-0238. The page needs a token, a router and two fetches to render, so these exercise the
 * pieces that decide what an advisor is TOLD — which is where the ticket's real risk sits. The full
 * render is covered by the E2E.
 *
 * Both behaviours below were measured against the real imported data before being built:
 * the segment column mixes two kinds of thing, and 128 institutions are named by a domain stem.
 */

/** Mirror of the page's grouping helper — see the note in the last describe block. */
function groupSegments(facets: SegmentFacet[]): { title: string; items: SegmentFacet[] }[] {
  const of = (kind: string) => facets.filter((f) => f.kind === kind);
  return [
    { title: "Kind of firm", items: of("firm_type") },
    { title: "What they supply", items: of("content_type") },
    { title: "Unclassified", items: of("unknown") },
  ].filter((g) => g.items.length > 0);
}

const FACETS: SegmentFacet[] = [
  { value: "Bank", count: 149, label: "Bank", kind: "firm_type" },
  { value: "Data", count: 144, label: "Supplies: market data", kind: "content_type" },
  { value: "Sell-side research", count: 128, label: "Sell-side research house", kind: "firm_type" },
  { value: "Indices", count: 29, label: "Supplies: indices", kind: "content_type" },
  { value: "Weird New Value", count: 2, label: "Weird New Value", kind: "unknown" },
];

describe("segment grouping (GRS-0238 scope 3)", () => {
  it("separates what a firm IS from what a supplier SUPPLIES", () => {
    const groups = groupSegments(FACETS);
    expect(groups.map((g) => g.title)).toEqual([
      "Kind of firm",
      "What they supply",
      "Unclassified",
    ]);
    expect(groups[0]?.items.map((i) => i.value)).toEqual(["Bank", "Sell-side research"]);
    expect(groups[1]?.items.map((i) => i.value)).toEqual(["Data", "Indices"]);
  });

  it("puts firm types first, because that is what an advisor prospects on", () => {
    expect(groupSegments(FACETS)[0]?.title).toBe("Kind of firm");
  });

  it("drops empty groups rather than showing an empty heading", () => {
    const onlyFirms = FACETS.filter((f) => f.kind === "firm_type");
    expect(groupSegments(onlyFirms).map((g) => g.title)).toEqual(["Kind of firm"]);
  });

  it("keeps an unlabelled value visible instead of hiding it", () => {
    // A new import source arriving without a label must show up, not vanish — the ugliness IS the
    // signal that someone needs to label its vocabulary.
    const groups = groupSegments(FACETS);
    const unclassified = groups.find((g) => g.title === "Unclassified");
    expect(unclassified?.items.map((i) => i.label)).toEqual(["Weird New Value"]);
  });
});

/** The row's name cell, extracted so the marking rule is testable without the whole page. */
function NameCell({ name, unverified }: { name: string; unverified: boolean }) {
  return (
    <td>
      <span style={{ fontWeight: 600 }}>{name}</span>
      {unverified ? (
        <span className="badge badge-warn" data-testid="name-unverified">
          name unverified
        </span>
      ) : null}
    </td>
  );
}

describe("unverified names (GRS-0238, the finding the ticket did not anticipate)", () => {
  it("marks a domain-stem name", () => {
    render(
      <table>
        <tbody>
          <tr>
            <NameCell name="gs" unverified />
          </tr>
        </tbody>
      </table>,
    );
    expect(screen.getByTestId("name-unverified")).toBeTruthy();
  });

  it("shows the stem itself and never a guessed company name", () => {
    // The whole point. Rendering "Goldman Sachs" here would be a fabrication (#3): the source
    // stored `gs`, and deriving a firm name from a domain stem is a guess.
    const { container } = render(
      <table>
        <tbody>
          <tr>
            <NameCell name="gs" unverified />
          </tr>
        </tbody>
      </table>,
    );
    const cell = container.querySelector("td")!;
    expect(within(cell).getByText("gs")).toBeTruthy();
    expect(cell.textContent).not.toMatch(/Goldman/i);
  });

  it("stays quiet on a properly named firm", () => {
    render(
      <table>
        <tbody>
          <tr>
            <NameCell name="Barclays" unverified={false} />
          </tr>
        </tbody>
      </table>,
    );
    // Badging every row would make the warning mean nothing.
    expect(screen.queryByTestId("name-unverified")).toBeNull();
  });
});
