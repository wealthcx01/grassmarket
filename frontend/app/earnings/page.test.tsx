import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import EarningsPage from "@/app/earnings/page";
import { ApiError, api } from "@/lib/api";
import type { CommissionLine, EarningsSummary, Money } from "@/lib/types";

// The page redirects to /login without a token and uses the router; give it a stub token + router.
vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn(), push: vi.fn() }),
}));

vi.mock("@/lib/api", async (importActual) => {
  const actual = await importActual<typeof import("@/lib/api")>();
  return {
    ...actual,
    getToken: vi.fn(() => "test-token"),
    api: {
      ...actual.api,
      earningsSummary: vi.fn(),
      listCommissions: vi.fn(),
      productCommissions: vi.fn(),
      consultancyCommissions: vi.fn(),
      earningsTimeline: vi.fn(),
      downloadEarningsStatement: vi.fn(),
    },
  };
});

const mocked = api as unknown as {
  earningsSummary: ReturnType<typeof vi.fn>;
  listCommissions: ReturnType<typeof vi.fn>;
  productCommissions: ReturnType<typeof vi.fn>;
  consultancyCommissions: ReturnType<typeof vi.fn>;
  earningsTimeline: ReturnType<typeof vi.fn>;
  downloadEarningsStatement: ReturnType<typeof vi.fn>;
};

function money(amount_minor: number): Money {
  return { amount_minor, currency: "GBP", assumption_register_ref: "ref:1" };
}

function summary(over: Partial<EarningsSummary> = {}): EarningsSummary {
  return {
    owner_consultant_id: "c1",
    currency: "GBP",
    ytd_earned: money(750000), // £7,500.00 — unique among the fixtures below
    pending: money(250000),
    invoiced: money(0),
    paid: money(500000),
    projected_unpaid: money(250000),
    line_count: 1,
    ...over,
  };
}

function line(over: Partial<CommissionLine> = {}): CommissionLine {
  return {
    id: "l1",
    owner_consultant_id: "c1",
    engagement_id: "e1",
    kind: "engagement",
    amount: money(500000),
    payment_status: "paid",
    earned_on: "2026-07-01",
    tier: "consultant",
    attribution: "self_sourced",
    rate_ref: "rate:v1",
    base_value: money(5000000),
    source_attribution_id: null,
    content_hash: "abc",
    created_at: "2026-07-01T00:00:00+00:00",
    updated_at: "2026-07-01T00:00:00+00:00",
    ...over,
  };
}

describe("EarningsPage (GRS-0035)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // The page loads the live product-commission carrots + the earnings timeline alongside the
    // summary; default to none so each test opts in only to what it asserts.
    mocked.productCommissions.mockResolvedValue([]);
    mocked.consultancyCommissions.mockResolvedValue([]);
    mocked.earningsTimeline.mockResolvedValue({
      owner_consultant_id: "c1",
      currency: "GBP",
      points: [],
      stream_product: { amount_minor: 0, currency: "GBP", assumption_register_ref: "ref" },
      stream_consultancy: { amount_minor: 0, currency: "GBP", assumption_register_ref: "ref" },
    });
  });

  it("renders the summary totals and a commission line", async () => {
    mocked.earningsSummary.mockResolvedValue(summary());
    mocked.listCommissions.mockResolvedValue([line()]);
    render(<EarningsPage />);
    expect(await screen.findByText("Earned YTD")).toBeTruthy();
    expect(await screen.findByText("£7,500.00")).toBeTruthy(); // formatted by MoneyAmount
    expect(screen.getByText("Engagement")).toBeTruthy(); // the line's kind, humanised
    expect(screen.getByText("Self sourced")).toBeTruthy(); // the line's attribution, humanised
  });

  it("shows an empty state when there are no commission lines", async () => {
    mocked.earningsSummary.mockResolvedValue(summary({ line_count: 0 }));
    mocked.listCommissions.mockResolvedValue([]);
    render(<EarningsPage />);
    // GRS-0243 scope 4 replaced this with an empty state that TEACHES. Asserted on the
      // behaviour — the block exists, and it explains rather than restating the emptiness —
      // because the sentence itself is now in the retired-copy register and must not come back.
      const empty = await screen.findByTestId("earnings-empty");
      expect(empty.textContent).toMatch(/created for you|never entered/i);
      // The old wording is NOT asserted against here: it lives in `lib/retiredCopy.ts`, and
      // repeating it as a negative would put the retired sentence back into the source the
      // register scans — which is exactly what it caught when this test first ran.
  });

  it("downloads the statement on demand", async () => {
    mocked.earningsSummary.mockResolvedValue(summary());
    mocked.listCommissions.mockResolvedValue([]);
    mocked.downloadEarningsStatement.mockResolvedValue({
      blob: new Blob(["docx"]),
      filename: "earnings-statement.docx",
    });
    // jsdom has no object-URL API; the download helper needs it.
    (URL as unknown as { createObjectURL: () => string }).createObjectURL = vi.fn(() => "blob:x");
    (URL as unknown as { revokeObjectURL: () => void }).revokeObjectURL = vi.fn();

    render(<EarningsPage />);
    await screen.findByText("Earned YTD"); // wait for summary → the button becomes enabled
    fireEvent.click(screen.getByRole("button", { name: /Download statement/i }));
    await waitFor(() => expect(mocked.downloadEarningsStatement).toHaveBeenCalled());
  });

  it("surfaces an API error message verbatim, not a status code", async () => {
    mocked.earningsSummary.mockRejectedValue(
      new ApiError(409, "Earnings summary spans multiple currencies.", null),
    );
    mocked.listCommissions.mockResolvedValue([]);
    render(<EarningsPage />);
    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain("multiple currencies");
    expect(alert.textContent).not.toContain("409");
  });

  describe("Delivering consulting (Stream B) — GRS-0187, restyled GRS-0240", () => {
    const CARROTS = [
      {
        delivery_type: "consultant_led",
        sourcing: "self_sourced",
        delivery_label: "Consultant-led",
        sourcing_label: "Self-sourced",
        yr1_bps: 6500,
        thereafter_bps: 5500,
        example_deal: { amount_minor: 10000000, currency: "GBP", assumption_register_ref: "x" },
        yr1_commission: { amount_minor: 6500000, currency: "GBP", assumption_register_ref: "x" },
        thereafter_commission: { amount_minor: 5500000, currency: "GBP", assumption_register_ref: "x" },
        schedule_version: "commissions-v7",
      },
    ];

    it("shows the rate card, so a zero balance is not the only thing said about consulting", async () => {
      mocked.earningsSummary.mockResolvedValue(summary());
    mocked.listCommissions.mockResolvedValue([]);
    mocked.consultancyCommissions.mockResolvedValue(CARROTS);
      render(<EarningsPage />);
      // GRS-0240 rewrote this section: the heading names the stream in words with the letter
      // beside it, and the four look-alike cards became a 2x2 whose axes are separate cells. The
      // assertions follow the shipped copy — and are written against the STRUCTURE (a row header
      // and a rate cell) rather than one concatenated string, so the next wording change fails
      // loudly here instead of going quietly red like the deliverables E2E did (GRS-0228).
      const matrix = await screen.findByTestId("consulting-rate-matrix");
      expect(screen.getByRole("heading", { name: /Delivering consulting/ })).toBeTruthy();
      // Twice, and that is right: the "How you get paid" block defines the letter, the section
      // heading uses it. One occurrence would mean the explainer or the label went missing.
      expect(screen.getAllByText("Stream B")).toHaveLength(2);
      expect(within(matrix).getByRole("rowheader", { name: "Consultant-led" })).toBeTruthy();
      expect(within(matrix).getByText(/65% first year/)).toBeTruthy();
      expect(within(matrix).getByText(/55% thereafter/)).toBeTruthy();
    });

    it("says the rates are read live rather than typed in", async () => {
      mocked.earningsSummary.mockResolvedValue(summary());
    mocked.listCommissions.mockResolvedValue([]);
    mocked.consultancyCommissions.mockResolvedValue(CARROTS);
      render(<EarningsPage />);
      expect(await screen.findByText(/read live from the\s+commission schedule, never typed in by hand/)).toBeTruthy();
    });

    it("renders nothing at all if the schedule is unavailable, rather than an empty promise", async () => {
      mocked.consultancyCommissions.mockResolvedValue([]);
      render(<EarningsPage />);
      await screen.findByText(/Earnings/);
      expect(screen.queryByText("Consulting (Stream B)")).toBeNull();
    });
  });
});
