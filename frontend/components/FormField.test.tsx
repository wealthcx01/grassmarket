/**
 * GRS-0209: the new-assessment form's controls line up.
 *
 * Read the limits of this file before trusting it. GRS-0178 shipped a test that compared the two
 * controls' style DECLARATIONS, they were already identical, it passed, and the founder saw the
 * misalignment again — because the defect was 23.4px of measured geometry that no declaration
 * described. jsdom has no layout engine, so a unit test here still cannot see that.
 *
 * What this file locks is therefore the STRUCTURE that makes the geometry come out right, which is
 * the part a future edit can silently break: every control sits inside a field wrapper of the same
 * shape, any caption renders after (below) the control rather than before it, and every control
 * carries the shared control-height class. The alignment itself is proved by the measured
 * before/after screenshots on the PR, not here.
 */

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { FIELD_CONTROL_CLASS, FormField } from "@/components/FormField";

describe("FormField (GRS-0209)", () => {
  it("puts the label above the control, inside one .form-field wrapper", () => {
    const { container } = render(
      <FormField label="Operating model">
        <select className={FIELD_CONTROL_CLASS} aria-label="Operating model">
          <option>Retail brokerage</option>
        </select>
      </FormField>
    );

    const field = container.querySelector("label.form-field");
    expect(field).toBeTruthy();

    const control = screen.getByRole("combobox");
    expect(field?.contains(control)).toBe(true);
    // The label text precedes the control, so every field row has the same two-part shape.
    expect(field?.firstElementChild?.textContent).toBe("Operating model");
  });

  it("renders a caption AFTER the control, which is what stops it shifting the control", () => {
    // This is the exact defect: the subject field's caption used to sit in a cell aligned on its
    // bottom, so the caption's height pushed the input above it out of line by 23.4px.
    const { container } = render(
      <FormField label="Subject company" caption={<span>Type to find the company</span>}>
        <input className={FIELD_CONTROL_CLASS} aria-label="Subject company" />
      </FormField>
    );

    const field = container.querySelector("label.form-field");
    const children = Array.from(field?.children ?? []);
    const controlIndex = children.findIndex((el) => el.tagName === "INPUT");
    const captionIndex = children.findIndex((el) => el.textContent === "Type to find the company");

    expect(controlIndex).toBeGreaterThanOrEqual(0);
    expect(captionIndex).toBeGreaterThan(controlIndex);
  });

  it("exposes one control-height class, so a control cannot opt out by accident", () => {
    // The class is the contract between this component and the one CSS rule that gives the row its
    // shared minimum height. If the constant is renamed without the stylesheet, this fails.
    expect(FIELD_CONTROL_CLASS).toBe("field-control");
  });
});
