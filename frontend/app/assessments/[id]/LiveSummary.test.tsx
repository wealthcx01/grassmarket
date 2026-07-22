/**
 * GRS-0044: the wizard side-rail Live V must be honest about uncertainty (§7 / ADR-0008). An
 * unmodelled band (modelled=false) has to render as a labelled POINT, never a falsely-confident
 * p10–p90 range. This guards against re-introducing a hand-rolled renderer that bypasses BandDisplay.
 */

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { LiveSummary } from "@/app/assessments/[id]/WizardClient";
import type { LiveScore } from "@/lib/types";

function liveScore(over: Partial<LiveScore> = {}): LiveScore {
  return {
    scoreable: true,
    blocking: [],
    v: { p10: 0.5, p50: 0.5, p90: 0.5, modelled: false },
    b: null,
    p: null,
    l_index: null,
    module_qm: {},
    triad_economic: null,
    triad_perceived: null,
    triad_defence: null,
    overall_uncertainty: "Very High",
    subcomponents_assessed: 3,
    subcomponents_total: 51,
    coverage: null,
    module_weights: {},
    engine_version: "test",
    methodology_version: "test",
    coefficient_version: "test",
    uncertainty_version: "test",
    ...over,
  };
}

describe("LiveSummary (GRS-0044 band honesty)", () => {
  it("shows an unmodelled V as a labelled point, never a range", () => {
    render(<LiveSummary live={liveScore()} />);
    expect(screen.getByTestId("band-point")).toBeDefined();
    expect(screen.queryByTestId("band-range")).toBeNull();
  });

  it("shows a modelled V as a range", () => {
    render(<LiveSummary live={liveScore({ v: { p10: 0.4, p50: 0.5, p90: 0.6, modelled: true } })} />);
    expect(screen.getByTestId("band-range")).toBeDefined();
    expect(screen.queryByTestId("band-point")).toBeNull();
  });

  it("names concretely what's missing when not yet scoreable (GRS-0104)", () => {
    render(
      <LiveSummary
        live={liveScore({
          scoreable: false,
          v: null,
          blocking: ["Enter at least one business metric.", "Rate all 7 Strategic Powers."],
        })}
      />,
    );
    // The opaque "Live V appears once…" jargon is gone; the concrete blockers are shown instead.
    expect(screen.queryByText(/Live V appears once/i)).toBeNull();
    expect(screen.getByText(/Enter at least one business metric/i)).toBeDefined();
    expect(screen.getByText(/Rate all 7 Strategic Powers/i)).toBeDefined();
  });

  it("shows a gentle start prompt before any blockers are known", () => {
    render(<LiveSummary live={liveScore({ scoreable: false, v: null, blocking: [] })} />);
    expect(screen.getByText(/Start rating the steps/i)).toBeDefined();
  });
});

describe("LiveSummary (GRS-0166 finalised-score consistency)", () => {
  const finalEntry = {
    assessment_id: "a1",
    subject: "Revolut",
    state: "finalised",
    provenance: "sandbox",
    v_index: 0.605,
    v_p10: 0.55,
    v_p90: 0.64,
    uncertainty_rating: "Medium",
    updated_at: "2026-07-22T00:00:00Z",
  } as const;

  it("headlines the LOCKED score, not the live median, when finalised", () => {
    // Live recompute says 58.9; the immutable run says 60.5. The rail must quote 60.5 — the same
    // number the portfolio row and the deliverable headline (the GRS-0161 rule, third surface).
    render(
      <LiveSummary
        live={liveScore({ v: { p10: 0.54, p50: 0.589, p90: 0.63, modelled: true } })}
        final={finalEntry}
      />,
    );
    expect(screen.getByTestId("locked-score")).toBeDefined();
    expect(screen.getByText("60.5")).toBeDefined();
    expect(screen.queryByText("58.9")).toBeNull(); // the live median never shows
    expect(screen.getByText(/55\.0–64\.0/)).toBeDefined(); // the STORED band, not the live one
    expect(screen.getByText(/portfolio and the deliverable/i)).toBeDefined();
  });

  it("keeps the live view for a draft (no final entry)", () => {
    render(
      <LiveSummary
        live={liveScore({ v: { p10: 0.4, p50: 0.5, p90: 0.6, modelled: true } })}
        final={null}
      />,
    );
    expect(screen.queryByTestId("locked-score")).toBeNull();
    expect(screen.getByTestId("band-range")).toBeDefined();
  });
});
