/**
 * Diagnostic visuals for a scoreable assessment (GRS-0070): a q_m radar over the nine modules, a
 * B→P→L→V value waterfall, and a module table annotated with each module's weight share (κ_m).
 * Hand-built inline SVG — no charting dependency (consistent with the existing div-bar breakdown).
 *
 * These plot the P50 point for orientation; the honest P10/P90 bands live in the LiveScorePanel. All
 * colour is via CSS custom properties so the panel is theme-aware. If the score isn't scoreable, or
 * the weights are absent, each sub-panel renders nothing rather than a misleading empty chart.
 */

"use client";

import { toDisplay } from "@/lib/band";
import {
  moduleWeightRows,
  radarSpokes,
  spokePoint,
  waterfallSteps,
} from "@/lib/diagnostics";
import { formatBand } from "@/lib/band";
import type { LiveScore } from "@/lib/types";

function Panel({ title, hint, children }: { title: string; hint?: string; children: React.ReactNode }) {
  return (
    <div
      style={{
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-lg)",
        padding: "0.9rem 1rem",
        background: "var(--color-paper-raised)",
      }}
    >
      <h3 style={{ margin: "0 0 0.15rem", fontSize: "0.95rem" }}>{title}</h3>
      {hint ? (
        <p style={{ margin: "0 0 0.6rem", fontSize: "0.75rem", color: "var(--color-ink-muted)" }}>{hint}</p>
      ) : null}
      {children}
    </div>
  );
}

// --- q_m radar --------------------------------------------------------------------------

function QmRadar({ live, labels }: { live: LiveScore; labels: Record<string, string> }) {
  const spokes = radarSpokes(live, labels);
  if (spokes.length < 3) return null;
  const size = 260;
  const cx = size / 2;
  const cy = size / 2;
  const r = size / 2 - 46; // leave room for labels
  const n = spokes.length;

  const rings = [0.25, 0.5, 0.75, 1];
  const polygon = spokes
    .map((s, i) => {
      const pt = spokePoint(i, n, s.value, cx, cy, r);
      return `${pt.x.toFixed(1)},${pt.y.toFixed(1)}`;
    })
    .join(" ");

  return (
    <div style={{ overflowX: "auto" }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} role="img" aria-label="Module maturity radar">
        {/* concentric reference rings */}
        {rings.map((ring) => (
          <polygon
            key={ring}
            points={spokes
              .map((_, i) => {
                const pt = spokePoint(i, n, ring, cx, cy, r);
                return `${pt.x.toFixed(1)},${pt.y.toFixed(1)}`;
              })
              .join(" ")}
            fill="none"
            stroke="var(--color-border)"
            strokeWidth={ring === 1 ? 1.2 : 0.6}
          />
        ))}
        {/* spokes + labels */}
        {spokes.map((s, i) => {
          const end = spokePoint(i, n, 1, cx, cy, r);
          const label = spokePoint(i, n, 1.18, cx, cy, r);
          return (
            <g key={s.key}>
              <line x1={cx} y1={cy} x2={end.x} y2={end.y} stroke="var(--color-border)" strokeWidth={0.6} />
              <text
                x={label.x}
                y={label.y}
                fontSize={8.5}
                textAnchor={Math.abs(label.x - cx) < 8 ? "middle" : label.x < cx ? "end" : "start"}
                dominantBaseline="middle"
                fill="var(--color-ink-muted)"
              >
                {s.label}
              </text>
            </g>
          );
        })}
        {/* the shape */}
        <polygon points={polygon} fill="var(--color-accent-tint)" stroke="var(--color-accent)" strokeWidth={1.6} />
        {spokes.map((s, i) => {
          const pt = spokePoint(i, n, s.value, cx, cy, r);
          return <circle key={s.key} cx={pt.x} cy={pt.y} r={2.4} fill="var(--color-accent)" />;
        })}
      </svg>
    </div>
  );
}

// --- B→P→L→V waterfall ------------------------------------------------------------------

function ValueWaterfall({ live }: { live: LiveScore }) {
  const wf = waterfallSteps(live);
  if (!wf) return null;
  const rowH = 30;
  const gap = 10;
  const labelW = 132;
  const barW = 260;
  const width = labelW + barW + 56;
  const rows = [...wf.steps, null]; // null = the V total row
  const height = rows.length * (rowH + gap) + 8;
  const scale = (x: number) => x * barW; // x in [0,1] → px (0–100 maps to full bar)

  return (
    <div style={{ overflowX: "auto" }}>
      <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Value composition waterfall">
        {wf.steps.map((step, i) => {
          const y = i * (rowH + gap) + 4;
          const x0 = labelW + scale(step.cumulativeBefore);
          const w = Math.max(scale(step.contribution), 1.5);
          return (
            <g key={step.key}>
              <text x={0} y={y + rowH / 2} fontSize={10} dominantBaseline="middle" fill="var(--color-ink)">
                {step.label}
              </text>
              <text x={labelW - 8} y={y + rowH / 2} fontSize={8.5} textAnchor="end" dominantBaseline="middle" fill="var(--color-ink-faint)">
                θ{step.theta.toFixed(2)}
              </text>
              <rect x={x0} y={y} width={w} height={rowH} rx={3} fill="var(--color-accent)" opacity={0.55 + i * 0.15} />
              <text x={x0 + w + 6} y={y + rowH / 2} fontSize={9} dominantBaseline="middle" fill="var(--color-ink-muted)">
                +{toDisplay(step.contribution).toFixed(1)}
              </text>
              {/* connector to next step's start */}
              {i < wf.steps.length - 1 ? (
                <line
                  x1={x0 + w}
                  y1={y + rowH}
                  x2={x0 + w}
                  y2={y + rowH + gap}
                  stroke="var(--color-border-strong)"
                  strokeWidth={0.8}
                  strokeDasharray="2 2"
                />
              ) : null}
            </g>
          );
        })}
        {/* V total */}
        {(() => {
          const y = wf.steps.length * (rowH + gap) + 4;
          const w = Math.max(scale(wf.total), 1.5);
          return (
            <g>
              <text x={0} y={y + rowH / 2} fontSize={10} dominantBaseline="middle" fill="var(--color-ink)" fontWeight={600}>
                Platform Value (V)
              </text>
              <rect x={labelW} y={y} width={w} height={rowH} rx={3} fill="var(--color-accent)" />
              <text x={labelW + w + 6} y={y + rowH / 2} fontSize={9.5} dominantBaseline="middle" fill="var(--color-ink)" fontWeight={600}>
                {toDisplay(wf.total).toFixed(1)}
              </text>
            </g>
          );
        })()}
      </svg>
    </div>
  );
}

// --- module table with κ_m --------------------------------------------------------------

function ModuleTable({ live, labels }: { live: LiveScore; labels: Record<string, string> }) {
  const rows = moduleWeightRows(live, labels);
  if (rows.length === 0) return null;
  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.8rem" }}>
        <thead>
          <tr style={{ textAlign: "left", color: "var(--color-ink-muted)" }}>
            <th style={{ padding: "0.3rem 0.4rem", fontWeight: 600 }}>Module</th>
            <th style={{ padding: "0.3rem 0.4rem", fontWeight: 600 }} title="Module weight share κ_m in the L blend (this coefficient version)">
              Weight κ
            </th>
            <th style={{ padding: "0.3rem 0.4rem", fontWeight: 600 }}>q_m (maturity)</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={row.key} style={{ borderTop: "1px solid var(--color-border)" }}>
              <td style={{ padding: "0.35rem 0.4rem" }}>
                {i === 0 ? <span title="Weakest module — the likely constraint">▸ </span> : null}
                {row.label}
              </td>
              <td className="mono" style={{ padding: "0.35rem 0.4rem", color: "var(--color-ink-muted)" }}>
                {(row.weightShare * 100).toFixed(1)}%
              </td>
              <td className="mono" style={{ padding: "0.35rem 0.4rem" }}>{formatBand(row.qm)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// --- public panel -----------------------------------------------------------------------

export function DiagnosticsPanel({
  live,
  moduleLabels,
}: {
  live: LiveScore | null;
  moduleLabels: Record<string, string>;
}) {
  if (!live?.scoreable) return null;
  const wf = waterfallSteps(live);
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.85rem" }}>
      <Panel
        title="Maturity radar"
        hint="Each spoke is a module's q_m (P50). A dent points to the bottleneck; the outer ring is Frontier."
      >
        <QmRadar live={live} labels={moduleLabels} />
      </Panel>
      {wf ? (
        <Panel
          title="How Platform Value builds up"
          hint="Each lens contributes θ × its score; the three add to V (score domain only — never currency)."
        >
          <ValueWaterfall live={live} />
        </Panel>
      ) : null}
      <Panel title="Module breakdown" hint="Weakest first. κ is the module's weight share in the L blend for this coefficient version.">
        <ModuleTable live={live} labels={moduleLabels} />
      </Panel>
    </div>
  );
}
