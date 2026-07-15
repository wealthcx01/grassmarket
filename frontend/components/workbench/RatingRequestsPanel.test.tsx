/**
 * GRS-0062: the co-rater's Rating requests panel lists modules a colleague asked them to rate, each
 * linking to the blind rating form; an empty queue reads as intentional.
 */

import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { RatingRequestsPanel } from "@/components/workbench/RatingRequestsPanel";
import { api } from "@/lib/api";
import type { RatingRequestSummary } from "@/lib/types";

vi.mock("@/lib/api", async (importActual) => {
  const actual = await importActual<typeof import("@/lib/api")>();
  return { ...actual, api: { ...actual.api, myRatingRequests: vi.fn() } };
});
const mocked = api.myRatingRequests as unknown as ReturnType<typeof vi.fn>;

const req: RatingRequestSummary = {
  assessment_id: "a1",
  subject: "Meridian Securities",
  module_key: "APP_SERVER",
  module_name: "Application Server",
  submitted: false,
};

describe("RatingRequestsPanel (GRS-0062)", () => {
  beforeEach(() => vi.clearAllMocks());

  it("lists a request linking to the blind rating form", async () => {
    mocked.mockResolvedValue([req]);
    render(<RatingRequestsPanel />);
    const link = await screen.findByRole("link", { name: /Application Server/ });
    expect(link.getAttribute("href")).toBe("/rate/a1/APP_SERVER");
    expect(screen.getByText(/rate now/)).toBeTruthy();
  });

  it("shows an empty state when there are no requests", async () => {
    mocked.mockResolvedValue([]);
    render(<RatingRequestsPanel />);
    await waitFor(() => expect(mocked).toHaveBeenCalled());
    expect(await screen.findByText(/No rating requests right now/)).toBeTruthy();
  });
});
