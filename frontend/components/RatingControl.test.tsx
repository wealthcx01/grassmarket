/**
 * GRS-0165: the segmented rating control must make exactly the same transitions the old select
 * made — one click rates, clicking the active segment clears back to unrated, the two non-score
 * states are first-class, and read-only disables everything.
 */

import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { RatingControl } from "@/components/RatingControl";

describe("RatingControl", () => {
  it("renders all four maturity levels plus the two non-score states", () => {
    render(<RatingControl choice="" disabled={false} ariaLabel="Hosting" onChange={vi.fn()} />);
    for (const label of ["Basic", "Developing", "Advanced", "Frontier", "N/A", "Not assessed"]) {
      expect(screen.getByRole("button", { name: new RegExp(label, "i") })).toBeTruthy();
    }
    expect(screen.getByRole("group", { name: "Rate Hosting" })).toBeTruthy();
  });

  it("one click rates; the active segment is pressed", () => {
    const onChange = vi.fn();
    render(
      <RatingControl choice="Advanced" disabled={false} ariaLabel="Hosting" onChange={onChange} />,
    );
    expect(
      screen.getByRole("button", { name: /Advanced/ }).getAttribute("aria-pressed"),
    ).toBe("true");
    fireEvent.click(screen.getByRole("button", { name: /Basic/ }));
    expect(onChange).toHaveBeenCalledWith("Basic");
  });

  it("clicking the active segment clears back to unrated (one-click undo)", () => {
    const onChange = vi.fn();
    render(
      <RatingControl choice="Advanced" disabled={false} ariaLabel="Hosting" onChange={onChange} />,
    );
    fireEvent.click(screen.getByRole("button", { name: /Advanced/ }));
    expect(onChange).toHaveBeenCalledWith("");
  });

  it("selects the non-score states as first-class choices", () => {
    const onChange = vi.fn();
    render(<RatingControl choice="" disabled={false} ariaLabel="Hosting" onChange={onChange} />);
    fireEvent.click(screen.getByRole("button", { name: "N/A" }));
    expect(onChange).toHaveBeenCalledWith("Not Applicable");
    fireEvent.click(screen.getByRole("button", { name: /not assessed/i }));
    expect(onChange).toHaveBeenCalledWith("Not Assessed");
  });

  it("read-only disables every segment", () => {
    render(<RatingControl choice="Basic" disabled={true} ariaLabel="Hosting" onChange={vi.fn()} />);
    for (const b of screen.getAllByRole("button")) {
      expect((b as HTMLButtonElement).disabled).toBe(true);
    }
  });
});
