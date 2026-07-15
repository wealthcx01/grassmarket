import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { DeliverablesPanel } from "@/components/DeliverablesPanel";
import { ApiError, api } from "@/lib/api";
import type { Deliverable } from "@/lib/types";

vi.mock("@/lib/api", async (importActual) => {
  const actual = await importActual<typeof import("@/lib/api")>();
  return {
    ...actual,
    api: {
      ...actual.api,
      listDeliverables: vi.fn(),
      generateDeliverable: vi.fn(),
      downloadDeliverable: vi.fn(),
      listNarratives: vi.fn(),
    },
  };
});

const mocked = api as unknown as {
  listDeliverables: ReturnType<typeof vi.fn>;
  generateDeliverable: ReturnType<typeof vi.fn>;
  downloadDeliverable: ReturnType<typeof vi.fn>;
  listNarratives: ReturnType<typeof vi.fn>;
};

function deliverable(over: Partial<Deliverable> = {}): Deliverable {
  return {
    id: "d1",
    owner_consultant_id: "c1",
    engagement_id: "e1",
    type: "platform_power_report",
    title: "Platform Power Report — Meridian",
    ai_generated: false,
    approval_status: "draft",
    approved_by_consultant_id: null,
    mode: "draft_internal",
    scoring_run_id: "r1",
    coefficient_version: "v1-draft-pending-elicitation",
    content_hash: "abc",
    generated_at: "2026-07-13T12:00:00+00:00",
    created_at: "2026-07-13T12:00:00+00:00",
    updated_at: "2026-07-13T12:00:00+00:00",
    ...over,
  };
}

describe("DeliverablesPanel (GRS-0019)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocked.listNarratives.mockResolvedValue([]); // no AI narratives unless a test says otherwise
  });

  it("lists an engagement's deliverables with a distinct Draft badge", async () => {
    mocked.listDeliverables.mockResolvedValue([deliverable()]);
    render(<DeliverablesPanel engagementId="e1" />);
    expect(await screen.findByText("Platform Power Report — Meridian")).toBeTruthy();
    // The internal-draft badge reads "Draft" (never mistaken for a client pack).
    expect(screen.getByText("Draft")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Download" })).toBeTruthy();
  });

  it("shows the empty state when there are no deliverables", async () => {
    mocked.listDeliverables.mockResolvedValue([]);
    render(<DeliverablesPanel engagementId="e1" />);
    expect(await screen.findByText("No deliverables generated yet.")).toBeTruthy();
  });

  it("generates the selected type and reloads the list", async () => {
    mocked.listDeliverables.mockResolvedValueOnce([]).mockResolvedValueOnce([deliverable()]);
    mocked.generateDeliverable.mockResolvedValue(deliverable());
    render(<DeliverablesPanel engagementId="e1" />);
    await screen.findByText("No deliverables generated yet.");

    fireEvent.click(screen.getByRole("button", { name: "Generate" }));

    await waitFor(() =>
      expect(mocked.generateDeliverable).toHaveBeenCalledWith("e1", {
        deliverable_type: "platform_power_report",
        client_facing: false, // the internal-draft default
      }),
    );
    // The list reloads and now shows the generated document.
    expect(await screen.findByText("Platform Power Report — Meridian")).toBeTruthy();
  });

  it("surfaces pending AI sections as a review-gate banner and a not-client-ready row", async () => {
    mocked.listDeliverables.mockResolvedValue([deliverable({ ai_generated: true })]);
    mocked.listNarratives.mockResolvedValue([
      { status: "proposed" } as never,
      { status: "approved" } as never,
    ]);
    render(<DeliverablesPanel engagementId="e1" />);
    // The queue banner warns the pack is not client-ready while a section is unapproved.
    expect(await screen.findByText(/awaiting approval/i)).toBeTruthy();
    // ...and the row shows the count, not "client-ready".
    expect(await screen.findByText(/1 pending/)).toBeTruthy();
  });

  it("surfaces the gate refusal message verbatim, not a status code", async () => {
    mocked.listDeliverables.mockResolvedValue([]);
    mocked.generateDeliverable.mockRejectedValue(
      new ApiError(
        409,
        "Refusing to generate a client-facing deliverable from coefficient set 'v1-draft-pending-elicitation' (client_usable=False).",
        null,
      ),
    );
    render(<DeliverablesPanel engagementId="e1" />);
    await screen.findByText("No deliverables generated yet.");

    // Choose client-facing, which the draft coefficient set refuses — go through the review step.
    fireEvent.click(screen.getByLabelText("Client-facing"));
    fireEvent.click(screen.getByRole("button", { name: "Review & generate" }));
    fireEvent.click(screen.getByRole("button", { name: "Generate client-facing document" }));

    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain("client_usable=False");
    expect(alert.textContent).not.toContain("409");
  });

  it("requires an explicit review step before generating a client-facing document (GRS-0056)", async () => {
    mocked.listDeliverables.mockResolvedValue([]);
    mocked.generateDeliverable.mockResolvedValue(deliverable());
    render(<DeliverablesPanel engagementId="e1" />);
    await screen.findByText("No deliverables generated yet.");

    // Selecting client-facing turns the button into a review action; clicking it does NOT generate.
    fireEvent.click(screen.getByLabelText("Client-facing"));
    fireEvent.click(screen.getByRole("button", { name: "Review & generate" }));
    expect(screen.getByText(/Review before it goes to the client/i)).toBeTruthy();
    expect(mocked.generateDeliverable).not.toHaveBeenCalled();

    // Cancel backs out without generating.
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(screen.queryByText(/Review before it goes to the client/i)).toBeNull();
    expect(mocked.generateDeliverable).not.toHaveBeenCalled();

    // Confirming from the review step generates a client-facing document.
    fireEvent.click(screen.getByRole("button", { name: "Review & generate" }));
    fireEvent.click(screen.getByRole("button", { name: "Generate client-facing document" }));
    await waitFor(() =>
      expect(mocked.generateDeliverable).toHaveBeenCalledWith("e1", {
        deliverable_type: "platform_power_report",
        client_facing: true,
      }),
    );
  });

  it("an internal draft still generates immediately, no review step", async () => {
    mocked.listDeliverables.mockResolvedValue([]);
    mocked.generateDeliverable.mockResolvedValue(deliverable());
    render(<DeliverablesPanel engagementId="e1" />);
    await screen.findByText("No deliverables generated yet.");

    fireEvent.click(screen.getByRole("button", { name: "Generate" }));
    expect(screen.queryByText(/Review before it goes to the client/i)).toBeNull();
    await waitFor(() =>
      expect(mocked.generateDeliverable).toHaveBeenCalledWith("e1", {
        deliverable_type: "platform_power_report",
        client_facing: false,
      }),
    );
  });
});
