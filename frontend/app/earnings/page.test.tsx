import { fireEvent, render, screen, waitFor } from "@testing-library/react";
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
      downloadEarningsStatement: vi.fn(),
    },
  };
});

const mocked = api as unknown as {
  earningsSummary: ReturnType<typeof vi.fn>;
  listCommissions: ReturnType<typeof vi.fn>;
  productCommissions: ReturnType<typeof vi.fn>;
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
    // The page loads the live product-commission carrots alongside the summary; default to none so
    // each test opts in only to what it asserts.
    mocked.productCommissions.mockResolvedValue([]);
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
    expect(await screen.findByText(/No commission lines yet/i)).toBeTruthy();
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
});
