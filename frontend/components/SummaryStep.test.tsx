/**
 * GRS-0182: the Summary & Interpretation repair.
 *
 * Three things are pinned here because all three were credibility bugs on a record the founder was
 * looking at: the score appeared twice, a FINALISED assessment claimed it was awaiting sign-off,
 * and the column told its story out of order.
 */

import { render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { SummaryStep } from "@/components/steps";
import type {
  AssessmentDocument,
  LiveScore,
  Registry,
  RecordProvenance,
} from "@/lib/types";

// The review panel fetches on mount; this suite is about WHICH surface renders, not its internals,
// so it is stubbed to an identifiable marker. Dual rating and the committee were retired under
// ADR-0041 (GRS-0188) and no longer render anywhere.
vi.mock("@/components/FounderReviewStatus", () => ({
  FounderReviewStatus: () => <div data-testid="founder-review">Founder review status</div>,
}));
vi.mock("@/components/DeliverablePreviewButton", () => ({
  DeliverablePreviewButton: () => <div>Preview deliverable</div>,
}));

const BAND = { p10: 0.55, p50: 0.61, p90: 0.68, modelled: true };

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
  c: 0.42,
  module_qm: { onboarding: BAND, custody: BAND, liquidity: BAND },
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
  module_weights: { onboarding: 0.4, custody: 0.3, liquidity: 0.3 },
  engine_version: "1",
  methodology_version: "1.2",
  coefficient_version: "draft",
  uncertainty_version: "1",
};

const REGISTRY = {
  powers: [],
  modules: [
    // A deliberately long name: the label guard is what stops it colliding with the geometry.
    { key: "onboarding", name: "Customer Trading Experience", subcomponents: [] },
    { key: "custody", name: "Custody", subcomponents: [] },
    { key: "liquidity", name: "Liquidity", subcomponents: [] },
  ],
  metrics: [],
  subcomponent_status: "ok",
  metric_status: "ok",
  c_modules: [],
  c_widgets: [],
  c_status: "ok",
  c_widget_profile: "retail",
} as unknown as Registry;

const DOCUMENT = {
  subject: "Revolut",
  profile: { operating_model: "retail", asset_classes: [], regions: [] },
  subcomponents: [],
  metrics: [],
  powers: [],
  c_subcomponents: [],
  widgets: [],
} as unknown as AssessmentDocument;

function renderStep(over: { readOnly?: boolean; provenance?: RecordProvenance; reviewRequestedAt?: string | null } = {}) {
  return render(
    <SummaryStep
      registry={REGISTRY}
      profiles={[]}
      document={DOCUMENT}
      update={() => {}}
      readOnly={over.readOnly ?? false}
      assessmentId="a1"
      live={LIVE}
      liveLoading={false}
      liveError={null}
      refreshLive={() => {}}
      onFinalise={() => {}}
      finalising={false}
      provenance={over.provenance ?? "production"}
      reviewRequestedAt={over.reviewRequestedAt ?? null}
      onPreviewInSandbox={() => {}}
      previewingSandbox={false}
      clientUsable
      finalEntry={null}
    />,
  );
}

describe("SummaryStep (GRS-0182)", () => {
  describe("one score, not two", () => {
    it("does not render its own score panel — the sticky rail is the single V display", () => {
      const { container } = renderStep();
      // The embedded LiveScorePanel headlined "V — Platform Value" alongside the rail's copy of
      // the same number. Exactly zero of them belong inside the step column now (ADR-0040).
      expect(container.textContent).not.toMatch(/V\s*—\s*Platform Value/i);
      expect(container.querySelector("[data-testid='live-score-panel']")).toBeNull();
    });

    it("still shows the composition detail, so nothing was lost with the panel", () => {
      const { container } = renderStep();
      // The waterfall and radar carry the B/P/L breakdown the removed panel duplicated.
      expect(container.querySelector('svg[aria-label="Value composition waterfall"]')).not.toBeNull();
      expect(container.querySelector('svg[aria-label="Module maturity radar"]')).not.toBeNull();
    });
  });

  describe("governance tells the truth about state", () => {
    it("a finalised production record shows a past-tense record, not a to-do", () => {
      renderStep({ readOnly: true, provenance: "production" });
      expect(screen.getByText("Governance record")).toBeTruthy();
      expect(screen.getByText(/Finalised on the production path/)).toBeTruthy();
      // The bug: a locked assessment rendering "awaiting sign-off".
      expect(screen.queryByText(/awaiting sign-off/i)).toBeNull();
      expect(screen.queryByTestId("founder-review")).toBeNull();
    });

    it("a finalised sandbox record says it was self-approved and watermarked", () => {
      renderStep({ readOnly: true, provenance: "sandbox" });
      expect(screen.getByText(/approved this yourself/)).toBeTruthy();
      expect(screen.getAllByText(/never client-facing/).length).toBeGreaterThan(0);
      expect(screen.queryByText(/awaiting sign-off/i)).toBeNull();
    });

    it("a production draft shows the founder review prompt, which is correct there", () => {
      renderStep({ readOnly: false, provenance: "production" });
      expect(screen.getByTestId("founder-review")).toBeTruthy();
      expect(screen.queryByText("Governance record")).toBeNull();
    });

    it("a sandbox draft shows the record instead, because it needs nobody (ADR-0029)", () => {
      renderStep({ readOnly: false, provenance: "sandbox" });
      expect(screen.queryByTestId("founder-review")).toBeNull();
      expect(screen.getByText("Governance record")).toBeTruthy();
    });
  });

  describe("story order", () => {
    it("reads interpretation, then how V builds up, then the governance record", () => {
      const { container } = renderStep({ readOnly: true, provenance: "production" });
      const text = container.textContent ?? "";
      const interpretation = text.indexOf("What this means");
      const waterfall = text.indexOf("How Platform Value builds up");
      const record = text.indexOf("Governance record");
      expect(interpretation).toBeGreaterThanOrEqual(0);
      expect(record).toBeGreaterThan(interpretation);
      if (waterfall >= 0) {
        expect(waterfall).toBeGreaterThan(interpretation);
        expect(waterfall).toBeLessThan(record);
      }
    });
  });

  describe("the rest of the step is untouched", () => {
    it("still reports the Customer Proposition index and the triad as words", () => {
      renderStep();
      expect(screen.getByText(/Customer Proposition/)).toBeTruthy();
      const triad = screen.getByText("Platform Power triad (ordinal)").parentElement!;
      expect(within(triad).getByText("Established")).toBeTruthy();
    });

    it("still offers the finalise control on a draft", () => {
      renderStep({ readOnly: false });
      expect(screen.getByRole("button", { name: /Finalise & lock inputs/ })).toBeTruthy();
    });

    it("says the inputs are locked on a finalised record", () => {
      renderStep({ readOnly: true });
      expect(screen.getAllByText(/inputs are locked/).length).toBeGreaterThan(0);
    });
  });
});
