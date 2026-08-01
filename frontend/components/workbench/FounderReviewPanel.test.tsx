import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { FounderReviewPanel } from "@/components/workbench/FounderReviewPanel";
import { api } from "@/lib/api";
import type { FounderReviewQueueEntry } from "@/lib/types";

vi.mock("@/lib/api", async (importActual) => {
  const actual = await importActual<typeof import("@/lib/api")>();
  return {
    ...actual,
    api: {
      ...actual.api,
      founderReviewQueue: vi.fn(),
      approveCurrentVersion: vi.fn(),
      approveReport: vi.fn(),
    },
  };
});

const mocked = api as unknown as {
  founderReviewQueue: ReturnType<typeof vi.fn>;
  approveCurrentVersion: ReturnType<typeof vi.fn>;
  approveReport: ReturnType<typeof vi.fn>;
};

function entry(over: Partial<FounderReviewQueueEntry> = {}): FounderReviewQueueEntry {
  return {
    id: "a1",
    owner_consultant_id: "c1",
    assessment_id: "a1",
    subject: "Meridian Securities",
    advisor_name: "Alice Advisor",
    advisor_email: "alice@example.com",
    requested_at: "2026-08-01T09:00:00+00:00",
    document_hash: "f".repeat(64),
    previously_approved: false,
    created_at: "2026-08-01T09:00:00+00:00",
    updated_at: "2026-08-01T09:00:00+00:00",
    ...over,
  };
}

describe("FounderReviewPanel — client reports in the queue (GRS-0245)", () => {
  beforeEach(() => vi.clearAllMocks());

  it("shows a pending client report beside assessments, and says which it is", async () => {
    mocked.founderReviewQueue.mockResolvedValue([
      entry(),
      entry({ id: "d1", assessment_id: "a2", deliverable_id: "d1", subject: "WeBull" }),
    ]);
    render(<FounderReviewPanel />);

    expect(await screen.findByText(/Meridian Securities/)).toBeTruthy();
    // The report row is labelled, because "WeBull" alone does not tell the founder whether they
    // are being asked to read a scored document or the words a client will receive.
    expect(await screen.findByText(/WeBull — client report/)).toBeTruthy();
  });

  it("links a report row at the report, not at the assessment", async () => {
    mocked.founderReviewQueue.mockResolvedValue([
      entry({ id: "d1", assessment_id: "a2", deliverable_id: "d1", subject: "WeBull" }),
    ]);
    render(<FounderReviewPanel />);

    const link = (await screen.findByText(/WeBull — client report/)).closest("a");
    expect(link?.getAttribute("href")).toBe("/deliverables/d1/report");
  });

  it("names the sections that changed since the last approval", async () => {
    mocked.founderReviewQueue.mockResolvedValue([
      entry({
        id: "d1",
        assessment_id: "a2",
        deliverable_id: "d1",
        subject: "WeBull",
        previously_approved: true,
        changed_sections: ["constraint", "value"],
      }),
    ]);
    render(<FounderReviewPanel />);

    const changed = await screen.findByTestId("changed-sections");
    expect(changed.textContent).toContain("constraint, value");
  });

  it("says nothing about changes on a first review", async () => {
    // Empty is not "nothing changed" — it is "there is nothing to compare against". Rendering
    // "changed: " with an empty list would be a worse lie than saying nothing.
    mocked.founderReviewQueue.mockResolvedValue([
      entry({ id: "d1", assessment_id: "a2", deliverable_id: "d1", changed_sections: [] }),
    ]);
    render(<FounderReviewPanel />);

    await screen.findByRole("button", { name: /Approve this version/ });
    expect(screen.queryByTestId("changed-sections")).toBeNull();
  });

  it("approves a report through the report endpoint, not the assessment one", async () => {
    mocked.founderReviewQueue.mockResolvedValue([
      entry({ id: "d1", assessment_id: "a2", deliverable_id: "d1", subject: "WeBull" }),
    ]);
    mocked.approveReport.mockResolvedValue({});
    render(<FounderReviewPanel />);

    fireEvent.click(await screen.findByRole("button", { name: /Approve this version/ }));

    await waitFor(() => expect(mocked.approveReport).toHaveBeenCalledWith("d1"));
    // The two approvals are bound to different hashes; sending a report through the assessment
    // endpoint would record a signature on the wrong artefact.
    expect(mocked.approveCurrentVersion).not.toHaveBeenCalled();
  });

  it("still approves an assessment through the assessment endpoint", async () => {
    mocked.founderReviewQueue.mockResolvedValue([entry()]);
    mocked.approveCurrentVersion.mockResolvedValue({});
    render(<FounderReviewPanel />);

    fireEvent.click(await screen.findByRole("button", { name: /Approve this version/ }));

    await waitFor(() => expect(mocked.approveCurrentVersion).toHaveBeenCalledWith("a1"));
    expect(mocked.approveReport).not.toHaveBeenCalled();
  });

  it("keys the two row kinds apart when one assessment has both", async () => {
    // A report is submitted against an assessment that was itself reviewed, so both rows can carry
    // the same assessment_id. Keying on that alone collapsed them into one row.
    mocked.founderReviewQueue.mockResolvedValue([
      entry({ id: "a1", assessment_id: "a1", subject: "Meridian Securities" }),
      entry({ id: "d1", assessment_id: "a1", deliverable_id: "d1", subject: "Meridian Securities" }),
    ]);
    render(<FounderReviewPanel />);

    await screen.findByText(/Meridian Securities — client report/);
    expect(screen.getAllByRole("button", { name: /Approve this version/ })).toHaveLength(2);
  });
});
