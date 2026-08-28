/**
 * GRS-0186: the deliverables index renders each row with links to its engagement and client, a
 * working download, and an honest empty state.
 */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("next/navigation", () => ({ useRouter: () => ({ replace: vi.fn(), push: vi.fn() }) }));

vi.mock("@/lib/api", async (importActual) => {
  const actual = await importActual<typeof import("@/lib/api")>();
  return {
    ...actual,
    getToken: () => "tok",
    api: {
      ...actual.api,
      listAllDeliverables: vi.fn(),
      downloadDeliverable: vi.fn(),
    },
  };
});

import DeliverablesPage from "@/app/deliverables/page";
import { api } from "@/lib/api";
import type { DeliverableIndexRow } from "@/lib/types";

const mocked = api as unknown as {
  listAllDeliverables: ReturnType<typeof vi.fn>;
  downloadDeliverable: ReturnType<typeof vi.fn>;
};

const ROW: DeliverableIndexRow = {
  id: "d1",
  type: "executive_summary",
  title: "Executive Summary",
  mode: "draft_internal",
  generated_at: "2026-07-20T00:00:00Z",
  engagement_id: "e1",
  engagement_title: "Revolut delivery",
  prospect_id: "pr1",
  prospect_company_name: "Revolut",
};

describe("DeliverablesPage (GRS-0186)", () => {
  beforeEach(() => vi.clearAllMocks());

  it("renders a row with engagement and client links and downloads on click", async () => {
    mocked.listAllDeliverables.mockResolvedValue([ROW]);
    mocked.downloadDeliverable.mockResolvedValue({ blob: new Blob(["x"]), filename: "d.docx" });
    // jsdom lacks these; the download helper touches them.
    URL.createObjectURL = vi.fn(() => "blob:x");
    URL.revokeObjectURL = vi.fn();
    render(<DeliverablesPage />);

    expect(await screen.findByRole("link", { name: "Revolut delivery" })).toHaveProperty(
      "href",
      expect.stringContaining("/engagements/e1"),
    );
    expect(screen.getByRole("link", { name: "Revolut" }).getAttribute("href")).toBe("/prospects/pr1");
    expect(screen.getByText("Executive Summary")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: /download/i }));
    await waitFor(() =>
      expect(mocked.downloadDeliverable).toHaveBeenCalledWith("d1", { clientFacing: false }),
    );
  });

  it("shows the empty state when there are no deliverables", async () => {
    mocked.listAllDeliverables.mockResolvedValue([]);
    render(<DeliverablesPage />);
    expect(await screen.findByTestId("deliverables-empty")).toBeTruthy();
  });

  it("teaches the chain rather than restating that the table is empty (GRS-0243)", async () => {
    // A first-time user is looking at an empty table precisely because they do not know what fills
    // it, so "No deliverables generated yet" tells them only what they can already see. Every link
    // of the chain is a prerequisite, so every link gets named.
    mocked.listAllDeliverables.mockResolvedValue([]);
    render(<DeliverablesPage />);
    const empty = await screen.findByTestId("deliverables-empty");
    const text = empty.textContent ?? "";
    for (const step of ["assessment", "finalise", "engagement", "deliverable", "client report"]) {
      expect(text).toContain(step);
    }
    // And it offers the two ways forward: build one, or read a finished one.
    expect(text).toMatch(/worked example/i);
    expect(empty.querySelector('a[href="/portfolio"]')).toBeTruthy();
  });
});
