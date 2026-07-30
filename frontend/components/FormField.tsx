/**
 * One labelled form control (GRS-0209).
 *
 * GRS-0178 restructured the new-assessment form and verified the fix in a unit test that compared
 * style DECLARATIONS. The declarations were already identical, so the test passed and the founder
 * saw the same misalignment again. Measuring the RENDERED page (Chromium, at 1280/1440/1920 — all
 * three identical) named the real defect:
 *
 *   the Operating Model select sat 23.4px BELOW the subject input.
 *
 * One cause, not two. The form grid aligned its cells on their END, and the subject cell is the
 * taller one because this field always renders a caption under its input ("✓ Linked to…", or the
 * unlinked hint). Aligning on the bottom therefore pushed that input UP by the height of its own
 * caption. The two controls were never mismatched in height — both measured 40.9px.
 *
 * This component exists so that cannot come back by accident: every field is label-above-control
 * with the same markup shape, and any caption is rendered BELOW the control, so a field that grows
 * a caption can no longer move its own control. That is the property the previous fix lacked.
 */

import type React from "react";

/**
 * Marks an element as a control in a field row. It carries the shared minimum height, so a control
 * that does not reach it naturally (the submit button) still lines up with the ones that do.
 */
export const FIELD_CONTROL_CLASS = "field-control";

export function FormField({
  label,
  children,
  caption,
  as = "label",
}: {
  label: React.ReactNode;
  /** The control. It should carry `FIELD_CONTROL_CLASS` to share the row's control height. */
  children: React.ReactNode;
  /** Optional helper text. Sits below the control, so it never shifts the control above it. */
  caption?: React.ReactNode;
  /**
   * The wrapper element. `label` (the default) is right for an input or a select: wrapping them
   * associates the two, so clicking the label focuses the control.
   *
   * Use `div` when the cell holds a control that is itself already named — a submit button. A
   * `<button>` is a *labelable* element, so a wrapping `<label>` RENAMES it: the button's
   * accessible name becomes the label's text instead of its own. For the button cell that label is
   * an empty spacer reserving the label row, so wrapping it would leave the submit button
   * announced as blank. A unit test caught exactly that.
   */
  as?: "label" | "div";
}) {
  const Wrapper = as;
  return (
    <Wrapper className="form-field" style={{ fontSize: "0.85rem", minWidth: 0 }}>
      <span style={{ display: "block", marginBottom: "0.3rem", fontWeight: 500 }}>{label}</span>
      {children}
      {caption}
    </Wrapper>
  );
}
