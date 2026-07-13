import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { NarrativeReview } from "@/components/NarrativeReview";
import { ApiError, api } from "@/lib/api";
import type { AINarrative } from "@/lib/types";

vi.mock("@/lib/api", async (importActual) => {
  const actual = await importActual<typeof import("@/lib/api")>();
  return {
    ...actual,
    api: {
      ...actual.api,
      listNarratives: vi.fn(),
      proposeNarratives: vi.fn(),
      approveNarrative: vi.fn(),
    },
  };
});

const mocked = api as unknown as {
  listNarratives: ReturnType<typeof vi.fn>;
  proposeNarratives: ReturnType<typeof vi.fn>;
  approveNarrative: ReturnType<typeof vi.fn>;
};

function narrative(over: Partial<AINarrative> = {}): AINarrative {
  return {
    id: "n1",
    owner_consultant_id: "c1",
    deliverable_id: "d1",
    scoring_run_id: "r1",
    section: "interpretation",
    status: "proposed",
    proposed_text: "The binding constraint on V is the platform layer.",
    drafter_version: "template-drafter-v1",
    prompt_template_version: "narrative-templates-v1",
    author_tier: "venture_associate",
    final_text: null,
    approved_by_consultant_id: null,
    approved_at: null,
    edit_summary: null,
    created_at: "2026-07-13T12:00:00+00:00",
    updated_at: "2026-07-13T12:00:00+00:00",
    ...over,
  };
}

describe("NarrativeReview (GRS-0019 slice 2)", () => {
  beforeEach(() => vi.clearAllMocks());

  it("drafts AI narratives from the empty state", async () => {
    mocked.listNarratives.mockResolvedValueOnce([]).mockResolvedValueOnce([narrative()]);
    mocked.proposeNarratives.mockResolvedValue([narrative()]);
    render(<NarrativeReview deliverableId="d1" />);
    fireEvent.click(await screen.findByRole("button", { name: "Draft AI narratives" }));
    await waitFor(() => expect(mocked.proposeNarratives).toHaveBeenCalledWith("d1"));
    expect(await screen.findByText("Interpretation")).toBeTruthy();
  });

  it("shows the AI draft alongside an editable version and approves the edit", async () => {
    mocked.listNarratives
      .mockResolvedValueOnce([narrative()])
      .mockResolvedValueOnce([narrative({ status: "approved", final_text: "Edited text.", approved_by_consultant_id: "c1", approved_at: "2026-07-13T12:30:00+00:00", edit_summary: "approved without edits" })]);
    mocked.approveNarrative.mockResolvedValue(narrative({ status: "approved", section: "interpretation" }));
    render(<NarrativeReview deliverableId="d1" />);

    // The editable box appears, defaulting to the AI draft.
    const box = await screen.findByRole("textbox", { name: /Edit Interpretation/ });
    expect((box as HTMLTextAreaElement).value).toContain("binding constraint on V");
    fireEvent.change(box, { target: { value: "Consultant-edited interpretation." } });
    fireEvent.click(await screen.findByRole("button", { name: "Approve edited" }));

    await waitFor(() =>
      expect(mocked.approveNarrative).toHaveBeenCalledWith("n1", {
        final_text: "Consultant-edited interpretation.",
      }),
    );
  });

  it("surfaces the seniority-gate refusal as a plain message", async () => {
    mocked.listNarratives.mockResolvedValue([narrative()]);
    mocked.approveNarrative.mockRejectedValue(
      new ApiError(
        409,
        "A narrative authored under tier 'venture_associate' requires senior (Consultant-tier) approval; approver tier 'venture_associate' is not senior.",
        null,
      ),
    );
    render(<NarrativeReview deliverableId="d1" />);
    // Not edited → "Approve as drafted"; a Venture Associate cannot self-approve → gate refusal.
    fireEvent.click(await screen.findByRole("button", { name: "Approve as drafted" }));
    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain("requires senior");
    expect(alert.textContent).not.toContain("409");
  });

  it("renders the approval trail for an approved narrative", async () => {
    mocked.listNarratives.mockResolvedValue([
      narrative({
        status: "approved",
        final_text: "Approved interpretation.",
        approved_by_consultant_id: "abcdef12-0000",
        approved_at: "2026-07-13T12:30:00+00:00",
        edit_summary: "approved without edits",
      }),
    ]);
    render(<NarrativeReview deliverableId="d1" />);
    expect(await screen.findByText("Approved interpretation.")).toBeTruthy();
    expect(screen.getByText(/Approved by abcdef12/)).toBeTruthy();
  });
});
