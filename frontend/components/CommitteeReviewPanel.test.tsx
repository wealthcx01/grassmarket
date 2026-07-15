/**
 * GRS-0061: the committee panel shows every high-stakes item's status, but only a committee member
 * (not the owner) gets the approve/reject controls — mirroring the server's peer-challenge gate.
 */

import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { CommitteeReviewPanel } from "@/components/CommitteeReviewPanel";
import { api } from "@/lib/api";
import { getSession } from "@/lib/session";
import type { CommitteeQueueEntry } from "@/lib/types";

vi.mock("@/lib/api", async (importActual) => {
  const actual = await importActual<typeof import("@/lib/api")>();
  return { ...actual, api: { ...actual.api, committeeQueue: vi.fn(), decideCommitteeItem: vi.fn() } };
});
vi.mock("@/lib/session", () => ({ getSession: vi.fn() }));

const mockedQueue = api.committeeQueue as unknown as ReturnType<typeof vi.fn>;
const mockedSession = getSession as unknown as ReturnType<typeof vi.fn>;

const entry: CommitteeQueueEntry = {
  item: { item_type: "triad", item_key: "economic_value", rating: "Established", label: "Economic Value", reason: "Triad rating above None." },
  decision: null,
};

describe("CommitteeReviewPanel (GRS-0061)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedQueue.mockResolvedValue([entry]);
  });

  it("shows the item + status but NO decide controls to a non-committee owner", async () => {
    mockedSession.mockReturnValue({ isCommittee: false, consultantId: "owner" });
    render(<CommitteeReviewPanel assessmentId="a1" />);
    expect(await screen.findByText("Economic Value")).toBeTruthy();
    expect(screen.getByText(/Awaiting sign-off/)).toBeTruthy();
    expect(screen.queryByRole("button", { name: /Review this rating/ })).toBeNull();
  });

  it("gives a committee member the approve/reject controls", async () => {
    mockedSession.mockReturnValue({ isCommittee: true, consultantId: "member" });
    render(<CommitteeReviewPanel assessmentId="a1" />);
    const review = await screen.findByRole("button", { name: /Review this rating/ });
    expect(review).toBeTruthy();
  });

  it("renders nothing when there are no high-stakes items", async () => {
    mockedSession.mockReturnValue({ isCommittee: true, consultantId: "member" });
    mockedQueue.mockResolvedValue([]);
    const { container } = render(<CommitteeReviewPanel assessmentId="a1" />);
    await waitFor(() => expect(mockedQueue).toHaveBeenCalled());
    expect(container.querySelector("section")).toBeNull();
  });
});
