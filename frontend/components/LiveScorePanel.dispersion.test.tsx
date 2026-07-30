/**
 * GRS-0227 at the render layer.
 *
 * `lib/dispersion.test.ts` proves the numbers; this proves the advisor actually SEES them. The
 * ticket's acceptance is a statement about what is on screen — "two firms with the same headline
 * score no longer look like the same firm" — so it is asserted against rendered output, not against
 * the helper that feeds it.
 */

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { LiveScorePanel } from "@/components/LiveScorePanel";
import type { IndexBand, LiveScore } from "@/lib/types";

const BAND: IndexBand = { p10: 0.45, p50: 0.55, p90: 0.65, modelled: true };

function score(points: Record<string, number>): LiveScore {
  return {
    scoreable: true,
    blocking: [],
    // Identical headline in both fixtures — the point of the test is that the headline is not the
    // whole story, so it must be held constant while the modules underneath differ.
    v_point: 0.57,
    b_point: 0.6,
    p_point: 0.5,
    l_point: 0.55,
    v: BAND,
    b: BAND,
    p: BAND,
    l_index: BAND,
    module_qm: Object.fromEntries(Object.keys(points).map((k) => [k, BAND])),
    module_qm_point: points,
    module_weights: {},
    overall_uncertainty: "Moderate",
    subcomponents_assessed: 9,
    subcomponents_total: 9,
    coverage: 1,
    engine_version: "test",
    methodology_version: "test",
    coefficient_version: "test",
    uncertainty_version: "test",
  } as unknown as LiveScore;
}

function panel(points: Record<string, number>) {
  return render(
    <LiveScorePanel
      score={score(points)}
      loading={false}
      error={null}
      onRefresh={() => {}}
      moduleLabels={{ frontend: "Frontend", ledger: "Ledger", custody: "Custody" }}
    />,
  );
}

describe("the spread beside the score", () => {
  it("makes two firms with the SAME V read differently", () => {
    const flat = panel({ frontend: 0.55, ledger: 0.55, custody: 0.55 });
    const flatText = screen.getByTestId("live-module-spread").textContent ?? "";
    flat.unmount();

    const lumpy = panel({ frontend: 0.85, ledger: 0.25, custody: 0.55 });
    const lumpyText = screen.getByTestId("live-module-spread").textContent ?? "";
    lumpy.unmount();

    expect(flatText).not.toEqual(lumpyText);
    expect(flatText).toContain("55–55");
    expect(lumpyText).toContain("25–85");
    // Both sentences use the phrase; they must make OPPOSITE claims with it.
    expect(lumpyText).toContain("specific weak spot");
    expect(flatText).toContain("no single weak spot");
    expect(flatText).not.toContain("specific weak spot");
  });

  it("says nothing when a single module has scored, rather than reporting a range of zero", () => {
    // A one-module range is arithmetically zero and would read as "this firm is perfectly even",
    // which is the opposite of true. Silence is the honest render.
    panel({ frontend: 0.55 });
    expect(screen.queryByTestId("live-module-spread")).toBeNull();
  });

  it("never labels the spread, only states it", () => {
    panel({ frontend: 0.85, ledger: 0.25, custody: 0.55 });
    const text = (screen.getByTestId("live-module-spread").textContent ?? "").toLowerCase();
    // No rating gate for dispersion — that would be a scored dimension without a methodology
    // version, which GRS-0223 explicitly declined to introduce.
    for (const banned of ["high dispersion", "low dispersion", "dispersion:"]) {
      expect(text).not.toContain(banned);
    }
  });

  it("is not rendered at all when the assessment is not scoreable", () => {
    render(
      <LiveScorePanel
        score={{ ...score({ frontend: 0.5, ledger: 0.8 }), scoreable: false, blocking: ["x"] }}
        loading={false}
        error={null}
        onRefresh={() => {}}
      />,
    );
    expect(screen.queryByTestId("live-module-spread")).toBeNull();
  });
});
