import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { LessonObjective } from "@/components/workbench/LessonBody";
import { LessonReferences } from "@/components/workbench/LessonReferences";
import type { SourceRef } from "@/lib/types";

/**
 * GRS-0239 scopes 1 and 2.
 *
 * The founder's words were: "the lessons are horrible and just tell me what I should learn as
 * opposed to actually being lessons? It just reference links". Both halves of that sentence were
 * describing the LAYOUT, not the content — the teaching was always there, it was just second.
 *
 * These hold down the two decisions that fix it.
 */

const REFS: SourceRef[] = [
  { kind: "docs", title: "OpenBB Workspace docs", url: "https://docs.openbb.co/workspace" },
  { kind: "blog", title: "Why we built it", url: "https://openbb.co/blog/why" },
];

describe("the objective panel (scope 1)", () => {
  it("labels itself as an objective rather than pretending to be the lesson", () => {
    render(<LessonObjective body="By the end of this lesson you can size a data gap." />);
    const panel = screen.getByTestId("lesson-objective");
    expect(panel.textContent).toMatch(/What you['’]ll be able to do/i);
    expect(panel.textContent).toContain("size a data gap");
  });

  it("renders nothing at all when there is no objective to state", () => {
    // An empty panel with a heading is worse than no panel: it implies content was lost.
    const { container } = render(<LessonObjective body="   " />);
    expect(container.querySelector("[data-testid='lesson-objective']")).toBeNull();
  });
});

describe("references (scope 2)", () => {
  it("defaults to cards, which is right at the end of a lesson", () => {
    render(<LessonReferences references={REFS} />);
    expect(screen.queryByTestId("reference-footnote")).toBeNull();
    expect(screen.getByText("OpenBB Workspace docs")).toBeTruthy();
  });

  it("collapses to one line on a slide, so the slide reads as teaching", () => {
    // 139 of OpenBB's 196 slides carry references. A card strip under every one of them made each
    // slide look like a pointer somewhere else — which is the founder's "it just reference links".
    render(<LessonReferences references={REFS} variant="footnote" />);
    const footnote = screen.getByTestId("reference-footnote");
    expect(footnote.tagName.toLowerCase()).toBe("details");
    expect(footnote.querySelector("summary")?.textContent).toMatch(/2 sources/);
  });

  it("still names every source when expanded — the depth rule is untouched", () => {
    // Sourcing every claim is doctrine. This ticket changes the DISPLAY, never what must be cited.
    render(<LessonReferences references={REFS} variant="footnote" />);
    for (const ref of REFS) {
      expect(screen.getByText(ref.title)).toBeTruthy();
    }
  });

  it("says 'Source' rather than '1 sources' for a single citation", () => {
    render(<LessonReferences references={[REFS[0]!]} variant="footnote" />);
    const summary = screen.getByTestId("reference-footnote").querySelector("summary");
    expect(summary?.textContent).toMatch(/^Source:/);
  });

  it("renders nothing when there is nothing to cite", () => {
    const { container } = render(<LessonReferences references={[]} variant="footnote" />);
    expect(container.innerHTML).toBe("");
  });
});
