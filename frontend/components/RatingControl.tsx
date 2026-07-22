/**
 * One-click segmented maturity rating (GRS-0165, the GRS-0160 "faster rating control" scope item).
 * Replaces the per-row native `<select>` in the Infrastructure and Customer-Proposition steps:
 * four maturity levels plus the two first-class non-score states, each a single click — no popup,
 * keyboard-tabbable buttons. Clicking the active segment clears back to unrated (so a mis-click is
 * one click to undo, and "unrated" needs no seventh segment).
 */

"use client";

import type { MaturityLevel } from "@/lib/types";
import { MATURITY_LEVELS } from "@/lib/types";

export type RatingChoice = "" | MaturityLevel | "Not Applicable" | "Not Assessed";

const STATE_SEGMENTS: { value: RatingChoice; label: string; title: string }[] = [
  {
    value: "Not Applicable",
    label: "N/A",
    title: "Not Applicable — removed from the module's weighting (renormalised), never zero-filled",
  },
  {
    value: "Not Assessed",
    label: "Not assessed",
    title: "Explicitly not assessed — contributes to no score (first-class, never a zero)",
  },
];

function Segment({
  active,
  disabled,
  label,
  title,
  onClick,
  muted,
}: {
  active: boolean;
  disabled: boolean;
  label: string;
  title: string;
  onClick: () => void;
  muted?: boolean;
}) {
  return (
    <button
      type="button"
      aria-pressed={active}
      disabled={disabled}
      title={title}
      onClick={onClick}
      style={{
        font: "inherit",
        fontSize: "0.72rem",
        padding: "0.28rem 0.55rem",
        cursor: disabled ? "default" : "pointer",
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-pill)",
        background: active ? "var(--color-accent)" : "var(--color-paper-raised)",
        color: active ? "var(--color-paper)" : muted ? "var(--color-ink-muted)" : "var(--color-ink)",
        fontWeight: active ? 600 : 400,
        opacity: disabled && !active ? 0.55 : 1,
      }}
    >
      {label}
    </button>
  );
}

export function RatingControl({
  choice,
  disabled,
  ariaLabel,
  onChange,
}: {
  choice: RatingChoice;
  disabled: boolean;
  /** The subcomponent name — names the group for screen readers. */
  ariaLabel: string;
  onChange: (next: RatingChoice) => void;
}) {
  // Click the active segment → back to unrated ("" — one-click undo for a mis-click).
  const pick = (value: RatingChoice) => onChange(choice === value ? "" : value);
  return (
    <div
      role="group"
      aria-label={`Rate ${ariaLabel}`}
      style={{ display: "flex", gap: "0.25rem", flexWrap: "wrap", alignItems: "center" }}
    >
      {MATURITY_LEVELS.map((level) => (
        <Segment
          key={level}
          active={choice === level}
          disabled={disabled}
          label={level}
          title={`Rate ${ariaLabel}: ${level}`}
          onClick={() => pick(level)}
        />
      ))}
      <span aria-hidden style={{ width: "0.25rem" }} />
      {STATE_SEGMENTS.map((s) => (
        <Segment
          key={s.value}
          active={choice === s.value}
          disabled={disabled}
          label={s.label}
          title={s.title}
          onClick={() => pick(s.value)}
          muted
        />
      ))}
    </div>
  );
}
