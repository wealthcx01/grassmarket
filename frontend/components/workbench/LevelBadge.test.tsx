/**
 * The level says whether it was earned (GRS-0242 scope 3).
 *
 * The bug: Bench reported "Level: certified lead" while the Certification tab beside it showed an
 * empty ladder. Both statements were true and the screen offered no way to know that.
 *
 * The rule these tests hold: an earned level renders plainly, and one granted outside the ladder
 * renders with what the evidence actually supports. The level is never hidden and never silently
 * corrected downward — an administrator may grant one, and quietly demoting it on screen would be
 * its own untruth.
 */

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { LevelBadge, LevelProvenanceNote } from "@/components/workbench/LevelBadge";

describe("LevelBadge", () => {
  it("renders an earned level plainly, with no caveat", () => {
    render(<LevelBadge level="shadow" earnedLevel="shadow" isEvidenced />);
    expect(screen.getByText("Shadow")).toBeTruthy();
    expect(screen.queryByText(/set outside the ladder/)).toBeNull();
  });

  it("flags a level the evidence does not support", () => {
    render(<LevelBadge level="certified_lead" earnedLevel="trained" isEvidenced={false} />);
    expect(screen.getByText("Certified Lead")).toBeTruthy();
    expect(screen.getByText(/set outside the ladder/)).toBeTruthy();
  });

  it("still shows the granted level rather than the earned one", () => {
    // Silently rendering "Trained" would be a second lie, and would contradict the JWT the rest of
    // the product enforces against.
    render(<LevelBadge level="certified_lead" earnedLevel="trained" isEvidenced={false} />);
    expect(screen.queryByText("Trained")).toBeNull();
  });

  it("uses proper titles, never the wire value", () => {
    render(<LevelBadge level="observed_lead" earnedLevel="observed_lead" isEvidenced />);
    expect(screen.getByText("Observed Lead")).toBeTruthy();
    expect(screen.queryByText(/observed_lead/)).toBeNull();
  });
});

describe("LevelProvenanceNote", () => {
  it("says nothing when the level was earned", () => {
    const { container } = render(
      <LevelProvenanceNote level="shadow" earnedLevel="shadow" isEvidenced />,
    );
    expect(container.textContent).toBe("");
  });

  it("names both the marked level and what the evidence supports", () => {
    render(<LevelProvenanceNote level="certified_lead" earnedLevel="trained" isEvidenced={false} />);
    const text = document.body.textContent ?? "";
    expect(text).toContain("Certified Lead");
    expect(text).toContain("Trained");
    // The point of the note: neither screen is wrong, and the reader is told so.
    expect(text).toContain("Both are true");
  });
});
