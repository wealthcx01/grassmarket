/**
 * GRS-0170: the power-strength control must keep UNRATED and the "None" rating visually and
 * semantically distinct (the D9 conflation the old select committed by showing "None" as the face
 * of an untouched control), and clearing must be possible (click the active segment).
 */

import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { StrengthControl } from "@/components/StrengthControl";

describe("StrengthControl", () => {
  it("unrated (null) shows NO active segment — 'None' is not the default face", () => {
    render(
      <StrengthControl value={null} disabled={false} ariaLabel="Branding benefit" onChange={vi.fn()} />,
    );
    for (const b of screen.getAllByRole("button")) {
      expect(b.getAttribute("aria-pressed")).toBe("false");
    }
  });

  it("'None' is an explicit selectable rating, distinct from unrated", () => {
    const onChange = vi.fn();
    render(
      <StrengthControl value={null} disabled={false} ariaLabel="Branding benefit" onChange={onChange} />,
    );
    fireEvent.click(screen.getByRole("button", { name: "None" }));
    expect(onChange).toHaveBeenCalledWith("None");
  });

  it("clicking the active segment clears back to unrated", () => {
    const onChange = vi.fn();
    render(
      <StrengthControl
        value="Established"
        disabled={false}
        ariaLabel="Branding benefit"
        onChange={onChange}
      />,
    );
    expect(
      screen.getByRole("button", { name: "Established" }).getAttribute("aria-pressed"),
    ).toBe("true");
    fireEvent.click(screen.getByRole("button", { name: "Established" }));
    expect(onChange).toHaveBeenCalledWith(null);
  });

  it("read-only disables every segment", () => {
    render(
      <StrengthControl value="Wide" disabled={true} ariaLabel="Branding benefit" onChange={vi.fn()} />,
    );
    for (const b of screen.getAllByRole("button")) {
      expect((b as HTMLButtonElement).disabled).toBe(true);
    }
  });
});
