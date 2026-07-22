/**
 * The FINALISED headline V (GRS-0166) — quotes the immutable run's deterministic `v_index` with its
 * STORED P10–P90 band, exactly as the portfolio row and the deliverable do (GRS-0161's consistency
 * rule). Deliberately NOT `BandDisplay`: that component labels its bold figure "P50 (median)",
 * which the locked score is not — it is the deterministic point, with the run's band as context
 * (clamped to include the point, mirroring the deliverable's presentation).
 */

import { toDisplay } from "@/lib/band";
import type { BrokeragePortfolioEntry } from "@/lib/types";

export function LockedScore({ entry }: { entry: BrokeragePortfolioEntry }) {
  if (entry.v_index == null) return null;
  const v = entry.v_index;
  const hasBand = entry.v_p10 != null && entry.v_p90 != null;
  const low = hasBand ? Math.min(entry.v_p10 as number, v) : null;
  const high = hasBand ? Math.max(entry.v_p90 as number, v) : null;
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.15rem" }} data-testid="locked-score">
      <span
        className="mono"
        style={{ fontSize: "0.66rem", letterSpacing: "0.08em", color: "var(--color-ink-muted)" }}
      >
        V — PLATFORM VALUE · FINALISED
      </span>
      <span title="The finalised run's deterministic score, with its stored P10–P90 uncertainty range (Methodology §7)">
        <strong className="mono" style={{ fontSize: "1.25rem" }}>
          {toDisplay(v).toFixed(1)}
        </strong>{" "}
        {low != null && high != null ? (
          <>
            <span className="mono" style={{ fontSize: "0.72rem", color: "var(--color-ink-muted)" }}>
              ({toDisplay(low).toFixed(1)}–{toDisplay(high).toFixed(1)})
            </span>{" "}
            <span
              className="mono"
              style={{ fontSize: "0.6rem", color: "var(--color-ink-faint)", letterSpacing: "0.03em" }}
            >
              P10–P90
            </span>
          </>
        ) : null}
        {entry.uncertainty_rating ? (
          <span className="tag" style={{ marginLeft: "0.35rem", fontSize: "0.62rem" }}>
            {entry.uncertainty_rating}
          </span>
        ) : null}
      </span>
      <p style={{ margin: "0.15rem 0 0", fontSize: "0.68rem", color: "var(--color-ink-faint)" }}>
        The locked score — the same number your portfolio and the deliverable quote.
      </p>
    </div>
  );
}
