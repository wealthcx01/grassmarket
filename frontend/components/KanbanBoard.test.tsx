/**
 * GRS-0055 (UX audit): an empty pipeline stage must read as intentionally empty ("No prospects"),
 * not a blank void; a populated stage renders its prospect card.
 */

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

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

describe("KanbanBoard empty states (GRS-0055)", () => {
  it("shows a 'No prospects' placeholder in every empty stage", () => {
    render(<KanbanBoard board={board([])} onMove={async () => {}} />);
    expect(screen.getAllByText("No prospects").length).toBe(PIPELINE_STAGES.length);
  });

  it("renders the prospect card in a populated stage and no placeholder there", () => {
    const entry = { prospect: prospect(), days_in_stage: 3, stale_after_days: 30, stale: false };
    render(<KanbanBoard board={board([entry])} onMove={async () => {}} />);
    expect(screen.getByText("Meridian Securities")).toBeTruthy();
    // One fewer empty column than the total number of stages.
    expect(screen.getAllByText("No prospects").length).toBe(PIPELINE_STAGES.length - 1);
  });
});
