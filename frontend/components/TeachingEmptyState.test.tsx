import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { TeachingEmptyState } from "@/components/TeachingEmptyState";

/**
 * GRS-0243 scope 4.
 *
 * The founder walked every section of the studio and could not tell, from the sections themselves,
 * what any of them was for. "No engagements yet." is the fact they can already see; it teaches
 * nothing about why the page is empty or what would change that.
 *
 * The rule these hold is the one that makes the component worth having at all: an empty state must
 * not restate the emptiness, and must offer exactly one next step.
 */

const EXAMPLE = {
  testId: "example-empty",
  headline: "Nothing here yet — an engagement is a contract, not a record you create.",
  explanation: <>An engagement opens when a prospect reaches Contracted on the pipeline.</>,
  action: { href: "/pipeline", label: "Open the pipeline" },
};

describe("a teaching empty state", () => {
  it("says what the section is, not that it is empty", () => {
    render(<TeachingEmptyState {...EXAMPLE} />);
    const block = screen.getByTestId("example-empty");
    expect(block.textContent).toContain("an engagement is a contract");
  });

  it("explains where the contents would come from", () => {
    render(<TeachingEmptyState {...EXAMPLE} />);
    expect(screen.getByTestId("example-empty").textContent).toMatch(/reaches Contracted/);
  });

  it("offers exactly one link", () => {
    // Two competing calls to action on an empty page is a choice offered to someone with no basis
    // for making it. The `rest` slot is prose, deliberately not a second link.
    render(<TeachingEmptyState {...EXAMPLE} />);
    expect(screen.getAllByRole("link")).toHaveLength(1);
  });

  it("keeps the trailing prose out of the link's accessible name", () => {
    render(
      <TeachingEmptyState
        {...EXAMPLE}
        action={{ ...EXAMPLE.action, rest: <> and move a prospect to Contracted.</> }}
      />,
    );
    // A screen-reader user hearing "Open the pipeline and move a prospect to Contracted" as one
    // link name cannot tell where the link ends and the sentence begins.
    expect(screen.getByRole("link", { name: "Open the pipeline" })).toBeTruthy();
  });

  it("never opens with 'you have no'", () => {
    // The phrasing the whole ticket is a reaction to. Asserted on the component's own contract so
    // a future empty state cannot quietly reintroduce it through this shape.
    render(<TeachingEmptyState {...EXAMPLE} />);
    expect(screen.getByTestId("example-empty").textContent).not.toMatch(/you have no/i);
  });
});
