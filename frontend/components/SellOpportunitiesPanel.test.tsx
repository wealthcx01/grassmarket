/**
 * GRS-0162: the "Recommended to sell" panel renders the deterministic join honestly — the ranked
 * products with their gap evidence and carrot, an honest empty state, silence on 409 (not
 * finalised — the panel simply doesn't apply), and a surfaced error otherwise.
 */

import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { SellOpportunitiesPanel } from "@/components/SellOpportunitiesPanel";
import { ApiError, api } from "@/lib/api";
import type { SellOpportunities } from "@/lib/types";

vi.mock("@/lib/api", async (importActual) => {
  const actual = await importActual<typeof import("@/lib/api")>();
  return { ...actual, api: { ...actual.api, sellOpportunities: vi.fn() } };
});

const mocked = api as unknown as { sellOpportunities: ReturnType<typeof vi.fn> };

const money = (minor: number) => ({
  amount_minor: minor,
  currency: "GBP" as const,
  assumption_register_ref: "test",
});

const payload: SellOpportunities = {
  assessment_id: "a1",
  subject: "Hargreaves Lansdown",
  opportunities: [
    {
      product_id: "connecttrade",
      name: "ConnectTrade",
      pitch: "Upgrades the order/execution stack.",
      gaps: [
        { kind: "module", key: "OEMS", name: "Order & Execution Management", q_m: 0.2, gate_band: "Basic" },
      ],
      not_yet_assessed: ["Trading Experience"],
      carrot: {
        product_id: "connecttrade",
        name: "ConnectTrade",
        yr1_bps: 1500,
        yr2_bps: 1000,
        window_months: 24,
        example_deal: money(10_000_000),
        yr1_commission: money(1_500_000),
        yr2_commission: money(1_000_000),
        schedule_version: "commissions-v7",
      },
    },
  ],
  fit_version: "product-fit-v1",
  coefficient_version: "v1-draft",
  schedule_version: "commissions-v7",
};

describe("SellOpportunitiesPanel", () => {
  beforeEach(() => vi.clearAllMocks());

  it("renders the ranked product with its gap evidence and carrot", async () => {
    mocked.sellOpportunities.mockResolvedValue(payload);
    render(<SellOpportunitiesPanel assessmentId="a1" />);
    expect(await screen.findByText("ConnectTrade")).toBeTruthy();
    // Gap chip: name + display score (0.2 → 20) + the report's band word.
    expect(screen.getByText(/Order & Execution Management · 20 Basic/)).toBeTruthy();
    // The carrot is information alongside, with the honest unassessed note.
    expect(screen.getByText(/Yr-1 15%/)).toBeTruthy(); // formatBps: schedule-exact, no rounding
    expect(screen.getByText(/Not yet assessed \(no claim made\): Trading Experience/)).toBeTruthy();
  });

  it("shows the honest empty state when nothing addresses the report's weak areas", async () => {
    mocked.sellOpportunities.mockResolvedValue({ ...payload, opportunities: [] });
    render(<SellOpportunitiesPanel assessmentId="a1" />);
    expect(await screen.findByText(/nothing honest to recommend/i)).toBeTruthy();
  });

  it("renders nothing on 409 (not finalised — the panel doesn't apply)", async () => {
    mocked.sellOpportunities.mockRejectedValue(new ApiError(409, "finalise first", null));
    const { container } = render(<SellOpportunitiesPanel assessmentId="a1" />);
    await waitFor(() => expect(mocked.sellOpportunities).toHaveBeenCalled());
    expect(container.firstChild).toBeNull();
  });

  it("surfaces a real load failure instead of a silent blank", async () => {
    mocked.sellOpportunities.mockRejectedValue(new ApiError(500, "boom", null));
    render(<SellOpportunitiesPanel assessmentId="a1" />);
    expect(await screen.findByRole("alert")).toBeTruthy();
  });
});
