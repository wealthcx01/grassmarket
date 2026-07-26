/**
 * GRS-0182: the diagnostic charts were fixed-pixel SVGs, so they overflowed a narrow column and
 * their labels collided with the geometry. These tests pin the two properties that fixes: the
 * charts scale from their viewBox, and a long label is truncated in the drawing while the full
 * name survives in a `<title>`.
 */

import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { DiagnosticsPanel } from "@/components/Diagnostics";
import type { LiveScore } from "@/lib/types";

const BAND = { p10: 0.5, p50: 0.6, p90: 0.7, modelled: true };

const LONG_NAME = "Customer Trading Experience";

const LIVE: LiveScore = {
  scoreable: true,
  v_point: 0.61,
  b_point: 0.6,
  p_point: 0.55,
  l_point: 0.66,
  blocking: [],
  v: BAND,
  b: BAND,
  p: BAND,
  l_index: BAND,
  c: null,
  module_qm: { onboarding: BAND, custody: BAND, liquidity: BAND, risk: BAND },
  triad_economic: "Established",
  triad_perceived: "Emerging",
  triad_defence: "Emerging",
  overall_uncertainty: "Medium",
  subcomponents_assessed: 40,
  subcomponents_total: 51,
  coverage: 0.78,
  theta_b: 0.3,
  theta_p: 0.3,
  theta_l: 0.4,
  module_weights: { onboarding: 0.3, custody: 0.3, liquidity: 0.2, risk: 0.2 },
  engine_version: "1",
  methodology_version: "1.2",
  coefficient_version: "draft",
  uncertainty_version: "1",
};

const LABELS: Record<string, string> = {
  onboarding: LONG_NAME,
  custody: "Custody",
  liquidity: "Liquidity",
  risk: "Risk",
};

function draw() {
  return render(<DiagnosticsPanel live={LIVE} moduleLabels={LABELS} />).container;
}

describe("DiagnosticsPanel charts (GRS-0182)", () => {
  describe("they scale instead of overflowing", () => {
    it("renders the radar from its viewBox at full container width", () => {
      const svg = draw().querySelector('svg[aria-label="Module maturity radar"]')!;
      expect(svg.getAttribute("viewBox")).toBe("0 0 260 260");
      expect(svg.getAttribute("width")).toBe("100%");
      // The fixed pixel height is what stopped it shrinking; it must be gone.
      expect(svg.getAttribute("height")).toBeNull();
    });

    it("renders the waterfall from its viewBox at full container width", () => {
      const svg = draw().querySelector('svg[aria-label="Value composition waterfall"]')!;
      expect(svg.getAttribute("viewBox")).toMatch(/^0 0 \d+ \d+$/);
      expect(svg.getAttribute("width")).toBe("100%");
      expect(svg.getAttribute("height")).toBeNull();
      expect(svg.getAttribute("preserveAspectRatio")).toBe("xMinYMin meet");
    });

    it("keeps the overflow wrapper as a last-resort safety net", () => {
      const svg = draw().querySelector('svg[aria-label="Module maturity radar"]')!;
      expect((svg.parentElement as HTMLElement).style.overflowX).toBe("auto");
    });
  });

  describe("long labels stop colliding", () => {
    it("truncates a long module name in the radar but keeps it whole in a title", () => {
      const svg = draw().querySelector('svg[aria-label="Module maturity radar"]')!;
      const texts = Array.from(svg.querySelectorAll("text"));
      const drawn = texts.map((t) => t.childNodes[t.childNodes.length - 1]?.textContent ?? "");
      // Nothing drawn is the full 27-character name…
      expect(drawn).not.toContain(LONG_NAME);
      expect(drawn.some((d) => d.endsWith("…"))).toBe(true);
      // …but the full name is recoverable on hover and by a screen reader.
      const titles = Array.from(svg.querySelectorAll("title")).map((t) => t.textContent);
      expect(titles).toContain(LONG_NAME);
    });

    it("leaves a short label alone", () => {
      const svg = draw().querySelector('svg[aria-label="Module maturity radar"]')!;
      expect(svg.textContent).toContain("Custody");
      expect(svg.textContent).not.toContain("Custody…");
    });

    it("guards the waterfall lens labels the same way", () => {
      const svg = draw().querySelector('svg[aria-label="Value composition waterfall"]')!;
      // Every visible label is within the guard length, ellipsis included.
      for (const text of Array.from(svg.querySelectorAll("text"))) {
        const drawn = text.childNodes[text.childNodes.length - 1]?.textContent ?? "";
        expect(drawn.length).toBeLessThanOrEqual(24);
      }
    });
  });

  it("still renders the weighted module table inside a scrollable wrapper", () => {
    const table = draw().querySelector("table")!;
    expect((table.parentElement as HTMLElement).style.overflowX).toBe("auto");
    expect(table.textContent).toContain(LONG_NAME);
  });
});
