/**
 * One labelled form control (GRS-0209).
 *
 * GRS-0178 restructured the new-assessment form and its fix was verified in a unit test rather than
 * against a rendered page, so the founder saw the same misalignment again. Two causes, both
 * invisible to a test that compares style declarations, because the declarations were already
 * identical:
 *
 *  1. The subject field always renders a caption under its input, and the grid aligned cells on
 *     their BOTTOM — so the caption pushed that input 17.6px out of line with the select.
 *  2. A native `<select>` computes ~2px taller than an `<input>` at the same padding, font-size and
 *     border. That is the select's intrinsic content height, not a style anyone wrote.
 *
 * This component exists so neither can come back by accident: every field is label-above-control
 * with the same markup shape, and every control carries `field-control`, which resolves to the one
 * `--field-control-height` token. A caption is rendered BELOW the control and therefore cannot move
 * it, which is the property the previous fix lacked.
 */

import type React from "react";

export const FIELD_CONTROL_CLASS = "field-control";

export function FormField({
  label,
  children,
  caption,
}: {
  label: React.ReactNode;
  /** The control. It must carry `FIELD_CONTROL_CLASS` to share the row's height token. */
  children: React.ReactNode;
  /** Optional helper text. Sits below the control, so it never shifts the control above it. */
  caption?: React.ReactNode;
}) {
  return (
    <label className="form-field" style={{ fontSize: "0.85rem", minWidth: 0 }}>
      <span style={{ display: "block", marginBottom: "0.3rem", fontWeight: 500 }}>{label}</span>
      {children}
      {caption}
    </label>
  );
}
