/**
 * Renders one index's uncertainty band HONESTLY (§7 / ADR-0008). It delegates the point-vs-range
 * decision entirely to `describeBand`, so the honesty guarantee lives in one tested place: a band
 * with `modelled = false` shows a labelled POINT, never a tight (falsely confident) range.
 */

import { NOT_MODELLED_LABEL, describeBand, toDisplay } from "@/lib/band";
import type { IndexBand } from "@/lib/types";

export function BandDisplay({ label, band }: { label: string; band?: IndexBand | null }) {
  const view = describeBand(band);
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.15rem" }}>
      <span
        className="mono"
        style={{ fontSize: "0.66rem", letterSpacing: "0.08em", color: "var(--color-ink-muted)" }}
      >
        {label}
      </span>
      {view === null ? (
        <span style={{ color: "var(--color-ink-muted)" }}>—</span>
      ) : view.mode === "point" ? (
        <span data-testid="band-point">
          <strong className="mono" style={{ fontSize: "1.25rem" }}>
            {toDisplay(view.value).toFixed(1)}
          </strong>{" "}
          <em style={{ fontSize: "0.7rem", color: "var(--color-warn)" }} title="Methodology §7">
            {view.label}
          </em>
        </span>
      ) : (
        <span data-testid="band-range">
          <strong className="mono" style={{ fontSize: "1.25rem" }}>
            {toDisplay(view.mid).toFixed(1)}
          </strong>{" "}
          <span className="mono" style={{ fontSize: "0.72rem", color: "var(--color-ink-muted)" }}>
            ({toDisplay(view.low).toFixed(1)}–{toDisplay(view.high).toFixed(1)})
          </span>
        </span>
      )}
    </div>
  );
}

/** Re-export so callers can reference the honesty label without reaching into `@/lib/band`. */
export { NOT_MODELLED_LABEL };
