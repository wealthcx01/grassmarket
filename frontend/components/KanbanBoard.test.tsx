/**
 * GRS-0176 (vertical Kanban): the board renders ten stage BANDS stacked vertically in lifecycle
 * order, with no horizontal scroll and no per-card stage select. A populated band shows its card
 * (click opens it); an empty band collapses to its label and a zero count, still a drop target.
 */

import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { KanbanBoard } from "@/components/KanbanBoard";
import { PIPELINE_STAGES, type PipelineBoard, type Prospect } from "@/lib/types";

function prospect(over: Partial<Prospect> = {}): Prospect {
  return {
    id: "p1",
    company_name: "Meridian Securities",
    stage: PIPELINE_STAGES[0]!.stage,
    ...over,
  } as unknown as Prospect;
}

function board(entries: PipelineBoard["entries"]): PipelineBoard {
  return { generated_at: "2026-07-15T00:00:00Z", entries };
}

const CARD_ENTRY = {
  prospect: prospect(),
  days_in_stage: 3,
  stale_after_days: 30,
  stale: false,
  win_probability: { score: 10, label: "Cold", reasons: [], missing_info: [] },
};

describe("KanbanBoard vertical layout (GRS-0176)", () => {
  it("renders all ten stage bands, once each, in lifecycle order", () => {
    render(<KanbanBoard board={board([])} onOpen={() => {}} onMove={async () => {}} />);
    const bands = PIPELINE_STAGES.map((s) => screen.getByRole("region", { name: s.label }));
    expect(bands).toHaveLength(PIPELINE_STAGES.length);
    // Document order matches the canonical lifecycle order (a stable, scannable stack).
    const positions = bands.map((b) => b.compareDocumentPosition(bands[0]!));
    positions.slice(1).forEach((p) => expect(p & Node.DOCUMENT_POSITION_PRECEDING).toBeTruthy());
  });

  it("renders a card in its stage band and opens it on click", () => {
    const onOpen = vi.fn();
    render(<KanbanBoard board={board([CARD_ENTRY])} onOpen={onOpen} onMove={async () => {}} />);
    fireEvent.click(screen.getByRole("button", { name: "Open Meridian Securities" }));
    expect(onOpen).toHaveBeenCalledWith("p1");
  });

  it("has no per-card stage select (the combobox moved to the deal panel)", () => {
    render(<KanbanBoard board={board([CARD_ENTRY])} onOpen={() => {}} onMove={async () => {}} />);
    const band = screen.getByRole("region", { name: PIPELINE_STAGES[0]!.label });
    expect(within(band).queryAllByRole("combobox")).toHaveLength(0);
  });

  it("collapses an empty stage to its label with a zero count", () => {
    render(<KanbanBoard board={board([])} onOpen={() => {}} onMove={async () => {}} />);
    const band = screen.getByRole("region", { name: PIPELINE_STAGES[1]!.label });
    expect(within(band).getByText("0")).toBeTruthy();
    // The empty band is still in the DOM as a droppable region (no "No prospects" filler text).
    expect(within(band).queryByText("No prospects")).toBeNull();
  });

  it("does not scroll horizontally (no overflowX on the board wrapper)", () => {
    const { container } = render(
      <KanbanBoard board={board([CARD_ENTRY])} onOpen={() => {}} onMove={async () => {}} />,
    );
    const withOverflowX = Array.from(container.querySelectorAll<HTMLElement>("div")).filter(
      (el) => el.style.overflowX && el.style.overflowX !== "visible",
    );
    expect(withOverflowX).toHaveLength(0);
  });
});
