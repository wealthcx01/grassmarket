/**
 * The pipeline forecast (GRS-0014). Deal-VOLUME, probability-weighted — **currency-free**. The API
 * sends no £ here (that's GRS-0012 recovery fees, shown from Money elsewhere), so this renders none.
 */

import { STAGE_LABEL, type PipelineForecast } from "@/lib/types";

export function ForecastPanel({ forecast }: { forecast: PipelineForecast }) {
  return (
    <div
      style={{
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius)",
        padding: "0.9rem 1rem",
        background: "var(--color-paper-raised)",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "baseline",
          flexWrap: "wrap",
          gap: "0.25rem 0.5rem",
        }}
      >
        <h2 style={{ fontSize: "1rem", margin: 0 }}>Pipeline forecast</h2>
        <span className="mono" style={{ fontSize: "0.68rem", color: "var(--color-ink-muted)" }}>
          deal volume · not £
        </span>
      </div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: "0.75rem 1.5rem", margin: "0.6rem 0 0.8rem" }}>
        <Stat label="Prospects" value={String(forecast.total_prospects)} />
        <Stat label="Open" value={String(forecast.open_prospects)} />
        <Stat
          label="Expected won deals"
          value={forecast.weighted_expected_deals.toFixed(2)}
          hint="Σ close-probability across the book"
        />
      </div>
      {/* The table scrolls within the panel on narrow viewports rather than forcing the whole
          panel (and the page) to overflow horizontally. */}
      <div style={{ overflowX: "auto" }}>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.78rem" }}>
        <thead>
          <tr style={{ textAlign: "left", color: "var(--color-ink-muted)" }}>
            <th style={{ padding: "0.2rem 0" }}>Stage</th>
            <th style={{ padding: "0.2rem 0", textAlign: "right" }}>Count</th>
            <th style={{ padding: "0.2rem 0", textAlign: "right" }}>P(win)</th>
            <th style={{ padding: "0.2rem 0", textAlign: "right" }}>Weighted</th>
          </tr>
        </thead>
        <tbody>
          {forecast.stages
            .filter((s) => s.count > 0)
            .map((s) => (
              <tr key={s.stage} style={{ borderTop: "1px solid var(--color-border)" }}>
                <td style={{ padding: "0.25rem 0" }}>{STAGE_LABEL[s.stage]}</td>
                <td className="mono" style={{ padding: "0.25rem 0", textAlign: "right" }}>
                  {s.count}
                </td>
                <td className="mono" style={{ padding: "0.25rem 0", textAlign: "right" }}>
                  {(s.close_probability * 100).toFixed(0)}%
                </td>
                <td className="mono" style={{ padding: "0.25rem 0", textAlign: "right" }}>
                  {s.weighted_deals.toFixed(2)}
                </td>
              </tr>
            ))}
        </tbody>
      </table>
      </div>
    </div>
  );
}

function Stat({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div>
      <div className="mono" style={{ fontSize: "1.4rem" }}>
        {value}
      </div>
      <div style={{ fontSize: "0.68rem", color: "var(--color-ink-muted)" }} title={hint}>
        {label}
      </div>
    </div>
  );
}
