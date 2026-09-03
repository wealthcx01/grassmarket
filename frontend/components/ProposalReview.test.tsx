/**
 * The review gate (GRS-0249 scope 4).
 *
 * The server enforces all of this too. What is pinned down here is what the *advisor sees and
 * does*, because a screen that quietly ticks everything for them turns "AI proposes, humans
 * approve" into a formality with a button on it.
 */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ProposalReview } from "@/components/ProposalReview";
import { ApiError, api } from "@/lib/api";
import type { ProposedField, VoiceNoteProposal } from "@/lib/types";

function field(over: Partial<ProposedField> & Pick<ProposedField, "field">): ProposedField {
  return {
    id: `f-${over.field}`,
    owner_consultant_id: "c1",
    proposal_id: "p1",
    transcript_id: "t1",
    proposed_value: null,
    confidence: "high",
    span_start: 0,
    span_end: 10,
    accepted: false,
    confirmed_value: null,
    ...over,
  };
}

const PROPOSAL: VoiceNoteProposal = {
  id: "p1",
  owner_consultant_id: "c1",
  prospect_id: "pr1",
  transcript_id: "t1",
  status: "proposed",
  extractor_version: "fixture-pipeline-extractor-v1",
  gaps: ["comms_note"],
  fields: [
    field({ field: "stage", proposed_value: "workshop_scheduled", confidence: "high" }),
    field({ field: "next_action", proposed_value: "Send the fee schedule", confidence: "medium" }),
  ],
  confirmed_at: null,
  discarded_at: null,
  created_at: "2026-09-03T09:00:00Z",
  updated_at: "2026-09-03T09:00:00Z",
};

beforeEach(() => {
  vi.restoreAllMocks();
});

describe("the approval has to name what it approves", () => {
  it("starts with nothing ticked and confirm unavailable", () => {
    render(<ProposalReview proposal={PROPOSAL} onDone={vi.fn()} />);
    const button = screen.getByRole("button", { name: "Tick what to apply" });
    expect((button as HTMLButtonElement).disabled).toBe(true);
    for (const box of screen.getAllByRole("checkbox")) {
      expect((box as HTMLInputElement).checked).toBe(false);
    }
  });

  it("sends only the fields the advisor ticked", async () => {
    const confirm = vi
      .spyOn(api, "confirmVoiceNoteProposal")
      .mockResolvedValue({ ...PROPOSAL, status: "confirmed" });
    render(<ProposalReview proposal={PROPOSAL} onDone={vi.fn()} />);

    fireEvent.click(screen.getAllByRole("checkbox")[0]!); // the stage only
    fireEvent.click(screen.getByRole("button", { name: "Apply 1 change" }));

    await waitFor(() => expect(confirm).toHaveBeenCalled());
    // The next action was proposed with medium confidence and is NOT sent. Confidence is not
    // consent.
    expect(confirm.mock.calls[0]![1]).toEqual({ stage: "workshop_scheduled" });
  });

  it("sends the advisor's correction, not the suggestion", async () => {
    const confirm = vi
      .spyOn(api, "confirmVoiceNoteProposal")
      .mockResolvedValue({ ...PROPOSAL, status: "confirmed" });
    render(<ProposalReview proposal={PROPOSAL} onDone={vi.fn()} />);

    fireEvent.click(screen.getAllByRole("checkbox")[1]!);
    fireEvent.change(screen.getByDisplayValue("Send the fee schedule"), {
      target: { value: "Send the fee schedule and the case study" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Apply 1 change" }));

    await waitFor(() => expect(confirm).toHaveBeenCalled());
    expect(confirm.mock.calls[0]![1]).toEqual({
      next_action: "Send the fee schedule and the case study",
    });
  });

  it("keeps the original suggestion on screen once it is corrected", () => {
    render(<ProposalReview proposal={PROPOSAL} onDone={vi.fn()} />);
    expect(screen.queryByText(/Suggested:/)).toBeNull();
    fireEvent.change(screen.getByDisplayValue("Send the fee schedule"), {
      target: { value: "Something else entirely" },
    });
    // A correction the screen hides is a correction nobody can check.
    expect(screen.getByText(/Suggested:/)).toBeTruthy();
    expect(screen.getByText("Send the fee schedule")).toBeTruthy();
  });
});

describe("it says what it did not hear", () => {
  it("names the gaps rather than showing empty boxes", () => {
    render(<ProposalReview proposal={PROPOSAL} onDone={vi.fn()} />);
    expect(screen.getByText(/Nothing heard about/)).toBeTruthy();
  });

  it("says so plainly when nothing at all was suggested", () => {
    render(
      <ProposalReview
        proposal={{ ...PROPOSAL, fields: [], gaps: ["stage", "next_action"] }}
        onDone={vi.fn()}
      />,
    );
    expect(screen.getByText("Nothing was suggested from this note.")).toBeTruthy();
    expect(screen.queryByRole("checkbox")).toBeNull();
  });
});

describe("refusals reach the advisor", () => {
  it("shows the reason an illegal move was refused", async () => {
    vi.spyOn(api, "confirmVoiceNoteProposal").mockRejectedValue(
      new ApiError(409, "Illegal pipeline transition prospect → delivered.", null),
    );
    render(<ProposalReview proposal={PROPOSAL} onDone={vi.fn()} />);
    fireEvent.click(screen.getAllByRole("checkbox")[0]!);
    fireEvent.click(screen.getByRole("button", { name: "Apply 1 change" }));

    await screen.findByText("Illegal pipeline transition prospect → delivered.");
  });

  it("lets the advisor reject the whole thing", async () => {
    const discard = vi
      .spyOn(api, "discardVoiceNoteProposal")
      .mockResolvedValue({ ...PROPOSAL, status: "discarded" });
    const onDone = vi.fn();
    render(<ProposalReview proposal={PROPOSAL} onDone={onDone} />);
    fireEvent.click(screen.getByRole("button", { name: "None of this is right" }));

    await waitFor(() => expect(discard).toHaveBeenCalledWith("p1"));
    expect(onDone).toHaveBeenCalled();
  });
});
