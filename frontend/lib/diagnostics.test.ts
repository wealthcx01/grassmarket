/**
 * GRS-0070: the diagnostic maths must be correct independent of the SVG. The waterfall's three
 * contributions must sum to V; the module-weight column must be a normalised share; and everything
 * must fail-soft to empty when the score isn't scoreable (never a misleading chart).
 */

import { describe, expect, it } from "vitest";

import { moduleWeightRows, radarSpokes, spokePoint, waterfallSteps } from "@/lib/diagnostics";
import type { IndexBand, LiveScore } from "@/lib/types";

const band = (p50: number, modelled = true): IndexBand => ({
  p10: Math.max(0, p50 - 0.1),
  p50,
  p90: Math.min(1, p50 + 0.1),
  modelled,
});

function scoreable(overrides: Partial<LiveScore> = {}): LiveScore {
  return {
    scoreable: true,
    blocking: [],
    v: band(0.5),
    b: band(0.6),
    p: band(0.4),
    l_index: band(0.5),
    module_qm: { APP_SERVER: band(0.3), OEMS: band(0.7), BACKOFFICE: band(0.5) },
    theta_b: 0.3,
    theta_p: 0.3,
    theta_l: 0.4,
    module_weights: { APP_SERVER: 2, OEMS: 1, BACKOFFICE: 1 },
    subcomponents_assessed: 10,
    subcomponents_total: 10,
    coverage: 1,
    engine_version: "1.1",
    methodology_version: "1.1",
    coefficient_version: "draft",
    uncertainty_version: "1.0",
    ...overrides,
  };
}

describe("waterfallSteps (GRS-0070)", () => {
  it("contributions sum to V and step cumulatively", () => {
    const wf = waterfallSteps(scoreable())!;
    expect(wf.steps).toHaveLength(3);
    // 0.3*0.6 + 0.3*0.4 + 0.4*0.5 = 0.18 + 0.12 + 0.20 = 0.5
    expect(wf.total).toBeCloseTo(0.5, 9);
    expect(wf.steps[0]!.contribution).toBeCloseTo(0.18, 9);
    expect(wf.steps[2]!.cumulativeAfter).toBeCloseTo(wf.total, 9);
    // each step starts where the previous ended
    expect(wf.steps[1]!.cumulativeBefore).toBeCloseTo(wf.steps[0]!.cumulativeAfter, 9);
  });

  it("returns null when a weight or band is missing", () => {
    expect(waterfallSteps(scoreable({ theta_b: null }))).toBeNull();
    expect(waterfallSteps(scoreable({ b: null }))).toBeNull();
    expect(waterfallSteps({ ...scoreable(), scoreable: false })).toBeNull();
    expect(waterfallSteps(null)).toBeNull();
  });
});

describe("moduleWeightRows (GRS-0070)", () => {
  it("normalises weights to shares summing to 1 and sorts weakest-first", () => {
    const rows = moduleWeightRows(scoreable(), { APP_SERVER: "App Server" });
    const sum = rows.reduce((a, r) => a + r.weightShare, 0);
    expect(sum).toBeCloseTo(1, 9);
    // APP_SERVER weight 2 of total 4 → 0.5 share
    expect(rows.find((r) => r.key === "APP_SERVER")!.weightShare).toBeCloseTo(0.5, 9);
    // weakest q_m (APP_SERVER 0.3) sorts first
    expect(rows[0]!.key).toBe("APP_SERVER");
    // label falls back to key when unmapped
    expect(rows.find((r) => r.key === "OEMS")!.label).toBe("OEMS");
  });

  it("falls back to an even share when weights are absent, never blank", () => {
    const rows = moduleWeightRows(scoreable({ module_weights: {} }), {});
    expect(rows.every((r) => r.weightShare > 0)).toBe(true);
    expect(rows.reduce((a, r) => a + r.weightShare, 0)).toBeCloseTo(1, 9);
  });

  it("is empty when not scoreable", () => {
    expect(moduleWeightRows({ ...scoreable(), scoreable: false }, {})).toEqual([]);
  });
});

describe("radar geometry", () => {
  it("returns a spoke per module", () => {
    expect(radarSpokes(scoreable(), {})).toHaveLength(3);
  });

  it("spoke 0 at full radius is straight up (12 o'clock)", () => {
    const p = spokePoint(0, 4, 1, 50, 50, 40);
    expect(p.x).toBeCloseTo(50, 6);
    expect(p.y).toBeCloseTo(10, 6);
  });
});
