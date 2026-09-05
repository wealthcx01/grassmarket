/**
 * The ladder shows which rungs were climbed (GRS-0242 scope 3).
 *
 * The note under the ladder was not enough on its own. Rendering it revealed that the ladder still
 * filled every rung up to the advisor's marked level — so the picture said "earned" while the
 * sentence beneath it said "granted". A reader trusts the picture.
 *
 * Earned rungs are filled. Rungs held but not evidenced are outlined. The marked level is never
 * hidden or silently reduced: an administrator may grant one, and quietly demoting it on screen
 * would contradict the JWT the rest of the product enforces against.
 */

import { render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { CertificationPanel } from "@/components/workbench/CertificationPanel";
import { api } from "@/lib/api";
import type { CertificationRecord } from "@/lib/types";

function record(over: Partial<CertificationRecord> = {}): CertificationRecord {
  return {
    id: "c1",
    owner_consultant_id: "a1",
    level: "certified_lead",
    earned_level: "trained",
    level_is_evidenced: false,
    coursework_complete: false,
    exam_score: null,
    exam_passed: false,
    shadow_count: 0,
    observed_lead_logged: false,
    observed_lead_signoff_by: null,
    created_at: "2026-09-01T00:00:00Z",
    updated_at: "2026-09-01T00:00:00Z",
    ...over,
  } as CertificationRecord;
}

function rungState(label: string): string | null {
  // Scoped to the ladder: the level name also appears in the provenance note beneath it, and a
  // bare text query would match whichever came first.
  const ladder = screen.getByTestId("certification-ladder");
  return within(ladder).getByText(label).closest("li")?.getAttribute("data-state") ?? null;
}

beforeEach(() => {
  vi.restoreAllMocks();
  vi.spyOn(api, "certificationEvents").mockResolvedValue([]);
  vi.spyOn(api, "courseCertifications").mockResolvedValue([]);
});

describe("the ladder distinguishes climbed from granted", () => {
  it("fills only the rungs the evidence supports", async () => {
    vi.spyOn(api, "certification").mockResolvedValue(record());
    render(<CertificationPanel advisorId="a1" />);
    await waitFor(() => expect(screen.getByTestId("certification-ladder")).toBeTruthy());

    expect(rungState("Trained")).toBe("earned");
    // Marked Certified Lead with an empty ladder — held, not climbed.
    expect(rungState("Shadow")).toBe("granted");
    expect(rungState("Observed Lead")).toBe("granted");
    expect(rungState("Certified Lead")).toBe("granted");
  });

  it("fills every rung when the level was genuinely earned", async () => {
    vi.spyOn(api, "certification").mockResolvedValue(
      record({ level: "certified_lead", earned_level: "certified_lead", level_is_evidenced: true }),
    );
    render(<CertificationPanel advisorId="a1" />);
    await waitFor(() => expect(screen.getByTestId("certification-ladder")).toBeTruthy());

    for (const rung of ["Trained", "Shadow", "Observed Lead", "Certified Lead"]) {
      expect(rungState(rung)).toBe("earned");
    }
    expect(screen.queryByText(/set outside the ladder/)).toBeNull();
  });

  it("leaves rungs above the marked level unreached, not granted", async () => {
    // A Trained advisor has not been *given* Certified Lead; those rungs are simply ahead.
    vi.spyOn(api, "certification").mockResolvedValue(
      record({ level: "trained", earned_level: "trained", level_is_evidenced: true }),
    );
    render(<CertificationPanel advisorId="a1" />);
    await waitFor(() => expect(screen.getByTestId("certification-ladder")).toBeTruthy());

    expect(rungState("Trained")).toBe("earned");
    expect(rungState("Certified Lead")).toBe("unreached");
  });

  it("explains the gap in words under the ladder", async () => {
    vi.spyOn(api, "certification").mockResolvedValue(record());
    render(<CertificationPanel advisorId="a1" />);
    await waitFor(() => expect(screen.getByText(/set outside the ladder/)).toBeTruthy());
    expect(document.body.textContent).toContain("Both are true");
  });
});
