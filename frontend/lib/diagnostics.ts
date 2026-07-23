/**
 * Pure helpers for the diagnostic visuals (GRS-0070). Kept separate from the SVG so the maths is
 * unit-tested independently of the DOM. All index values are the stored [0,1] domain; the renderer
 * scales to 0–100 via `toDisplay`. We plot the P50 point for the shape visuals (radar / waterfall);
 * full P10/P90 uncertainty stays in the LiveScorePanel bands — these are orientation aids, not a
 * replacement for the honest band.
 */

import type { IndexBand, LiveScore } from "@/lib/types";

/** One lens's additive contribution to V: θ_lens · index_p50. The three sum to V (Methodology §5.4). */
export interface WaterfallStep {
  key: "B" | "P" | "L";
  label: string;
  theta: number;
  index: number; // P50 in [0,1]
  contribution: number; // θ · index, in [0,1]
  cumulativeBefore: number; // running total before this step
  cumulativeAfter: number; // running total after this step
}

export interface Waterfall {
  steps: WaterfallStep[];
  total: number; // Σ contributions (== V.p50 up to rounding)
}

// Terse labels for the compact SVG waterfall axis (GRS-0097 keeps P as "Power"; the fuller L caption
// "the technology Layer" lives in the live-score panel band labels + the primer, where there is room).
const LENS_LABEL: Record<WaterfallStep["key"], string> = {
  B: "Business (B)",
  P: "Power (P)",
  L: "Infrastructure (L)",
};

/** Build the B→P→L→V waterfall, or null if any weight/band is missing (panel then hides). */
export function waterfallSteps(live: LiveScore | null): Waterfall | null {
  if (!live || !live.scoreable) return null;
  // The one-number rule (ADR-0040): the build-up uses the DETERMINISTIC points, so the chart
  // recomposes exactly to the quoted headline (θ_B·B + θ_P·P + θ_L·L = V_point). Falling back to
  // the band P50 only for an older API without points.
  const parts: {
    key: WaterfallStep["key"];
    theta?: number | null;
    point?: number | null;
    band?: IndexBand | null;
  }[] = [
    { key: "B", theta: live.theta_b, point: live.b_point, band: live.b },
    { key: "P", theta: live.theta_p, point: live.p_point, band: live.p },
    { key: "L", theta: live.theta_l, point: live.l_point, band: live.l_index },
  ];
  let cumulative = 0;
  const steps: WaterfallStep[] = [];
  for (const part of parts) {
    if (part.theta == null || (part.point == null && !part.band)) return null;
    const index = part.point ?? (part.band as IndexBand).p50;
    const contribution = part.theta * index;
    const before = cumulative;
    cumulative += contribution;
    steps.push({
      key: part.key,
      label: LENS_LABEL[part.key],
      theta: part.theta,
      index,
      contribution,
      cumulativeBefore: before,
      cumulativeAfter: cumulative,
    });
  }
  return { steps, total: cumulative };
}

/** One module row for the κ_m table: weight SHARE (δ_m normalised over all modules) + its q_m band. */
export interface ModuleWeightRow {
  key: string;
  label: string;
  weightShare: number; // δ_m / Σδ, in [0,1]
  qm: IndexBand | null;
  qmP50: number | null; // convenience for sorting
}

/**
 * Module table rows, sorted weakest q_m first (the bottleneck reads top-down). Weight is shown as a
 * SHARE of the configured module weights so equal draft weights read as an even split, and real
 * elicited weights differentiate. A module with no weight configured falls back to an even share so
 * the column is never blank (fail-soft on DISPLAY only — the engine itself never defaults a weight).
 */
export function moduleWeightRows(
  live: LiveScore | null,
  labels: Record<string, string>,
): ModuleWeightRow[] {
  if (!live || !live.scoreable) return [];
  const keys = Object.keys(live.module_qm);
  const weights = live.module_weights ?? {};
  const totalWeight = keys.reduce((acc, k) => acc + (weights[k] ?? 0), 0);
  const rows: ModuleWeightRow[] = keys.map((k) => {
    const qm = live.module_qm[k] ?? null;
    const rawWeight = weights[k];
    const share =
      totalWeight > 0 && rawWeight != null
        ? rawWeight / totalWeight
        : keys.length > 0
          ? 1 / keys.length
          : 0;
    return {
      key: k,
      label: labels[k] ?? k,
      weightShare: share,
      qm,
      qmP50: qm ? qm.p50 : null,
    };
  });
  rows.sort((a, b) => (a.qmP50 ?? 1) - (b.qmP50 ?? 1));
  return rows;
}

/** Radar spoke: module key, its P50 q_m (radius fraction [0,1]) and the label. */
export interface RadarSpoke {
  key: string;
  label: string;
  value: number; // P50 in [0,1]
}

export function radarSpokes(
  live: LiveScore | null,
  labels: Record<string, string>,
): RadarSpoke[] {
  if (!live || !live.scoreable) return [];
  return Object.entries(live.module_qm).map(([k, band]) => ({
    key: k,
    label: labels[k] ?? k,
    value: band.p50,
  }));
}

/** Cartesian point for spoke `i` of `n` on a unit circle, angle starting at 12 o'clock, clockwise. */
export function spokePoint(
  i: number,
  n: number,
  radiusFraction: number,
  cx: number,
  cy: number,
  r: number,
): { x: number; y: number } {
  const angle = -Math.PI / 2 + (2 * Math.PI * i) / n;
  return {
    x: cx + Math.cos(angle) * r * radiusFraction,
    y: cy + Math.sin(angle) * r * radiusFraction,
  };
}
