/**
 * Renders one index's uncertainty band HONESTLY (§7 / ADR-0008). It delegates the point-vs-range
 * decision entirely to `describeBand`, so the honesty guarantee lives in one tested place: a band
 * with `modelled = false` shows a labelled POINT, never a tight (falsely confident) range.
 */

import { NOT_MODELLED_LABEL, describeBand, toDisplay } from "@/lib/band";
import type { IndexBand } from "@/lib/types";

export function BandDisplay({
  label,
  band,
  point,
}: {
  label: string;
  band?: IndexBand | null;
  /** The one-number rule (ADR-0040): when given, THIS deterministic point is the bold figure and
   *  the band (clamped to include it) is the modelled range — the band's P50 is never headlined.
   *  Without it, legacy band rendering applies. */
  point?: number | null;
}) {
  const view = describeBand(band);
  if (point != null && view !== null && view.mode === "range") {
    const low = Math.min(view.low, point);
    const high = Math.max(view.high, point);
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: "0.15rem" }}>
        <span
          className="mono"
          style={{ fontSize: "0.66rem", letterSpacing: "0.08em", color: "var(--color-ink-muted)" }}
        >
          {label}
        </span>
        <span
          data-testid="band-det-point"
          title="The deterministic score (Methodology §5) — the number a finalised run stores — with the modelled P10–P90 uncertainty range around it (§7, ADR-0040)"
        >
          <strong className="mono" style={{ fontSize: "1.25rem" }}>
            {toDisplay(point).toFixed(1)}
          </strong>{" "}
          <span className="mono" style={{ fontSize: "0.72rem", color: "var(--color-ink-muted)" }}>
            ({toDisplay(low).toFixed(1)}–{toDisplay(high).toFixed(1)})
          </span>{" "}
          <span
            className="mono"
            style={{ fontSize: "0.6rem", color: "var(--color-ink-faint)", letterSpacing: "0.03em" }}
          >
            point · modelled P10–P90
          </span>
        </span>
      </div>
    );
  }
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
        // The bold figure is the P50 (median); the parenthesised range is P10–P90. Label the
        // percentiles explicitly (GRS-0153) — a quant reader must not have to guess whether the
        // bounds are P10/P90, P5/P95 or ±1σ (mock-advisor: Elena/Deutsche Börse).
        <span
          data-testid="band-range"
          title="P50 (median) with the P10–P90 uncertainty range (Methodology §7)"
        >
          <strong className="mono" style={{ fontSize: "1.25rem" }}>
            {toDisplay(view.mid).toFixed(1)}
          </strong>{" "}
          <span className="mono" style={{ fontSize: "0.72rem", color: "var(--color-ink-muted)" }}>
            ({toDisplay(view.low).toFixed(1)}–{toDisplay(view.high).toFixed(1)})
          </span>{" "}
          <span
            className="mono"
            style={{ fontSize: "0.6rem", color: "var(--color-ink-faint)", letterSpacing: "0.03em" }}
          >
            P50 · P10–P90
          </span>
        </span>
      )}
    </div>
  );
}

/** Re-export so callers can reference the honesty label without reaching into `@/lib/band`. */
export { NOT_MODELLED_LABEL };
