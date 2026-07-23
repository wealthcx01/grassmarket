/**
 * One-click segmented power-strength rating (GRS-0170). Replaces the Powers step's native
 * `<select>`, which displayed "None" — a REAL rating (zero power) — as the face of an untouched
 * control: exactly the rated/unrated conflation the methodology (D9) forbids. Here an unrated
 * side has NO active segment, "None" is an explicit choice, and clicking the active segment
 * clears back to unrated.
 */

"use client";

import type { StrengthRating } from "@/lib/types";
import { STRENGTHS } from "@/lib/types";

const STRENGTH_TITLE: Record<StrengthRating, string> = {
  None: "None — no power on this side (a real zero rating, not 'unrated')",
  Emerging: "Emerging — forming, not yet dependable",
  Established: "Established — more likely than not to persist 5+ years",
  Wide: "Wide — near-certain 5, likely 10+ years",
};

export function StrengthControl({
  value,
  disabled,
  ariaLabel,
  onChange,
}: {
  /** null = UNRATED (no segment active) — first-class, distinct from the "None" rating. */
  value: StrengthRating | null;
  disabled: boolean;
  ariaLabel: string;
  onChange: (next: StrengthRating | null) => void;
}) {
  return (
    <div
      role="group"
      aria-label={ariaLabel}
      style={{ display: "flex", gap: "0.25rem", flexWrap: "wrap", alignItems: "center" }}
    >
      {STRENGTHS.map((s) => {
        const active = value === s;
        return (
          <button
            key={s}
            type="button"
            aria-pressed={active}
            disabled={disabled}
            title={STRENGTH_TITLE[s]}
            onClick={() => onChange(active ? null : s)}
            style={{
              font: "inherit",
              fontSize: "0.72rem",
              padding: "0.28rem 0.55rem",
              cursor: disabled ? "default" : "pointer",
              border: "1px solid var(--color-border)",
              borderRadius: "var(--radius-pill)",
              background: active ? "var(--color-accent)" : "var(--color-paper-raised)",
              color: active ? "var(--color-paper)" : "var(--color-ink)",
              fontWeight: active ? 600 : 400,
              opacity: disabled && !active ? 0.55 : 1,
            }}
          >
            {s}
          </button>
        );
      })}
    </div>
  );
}
