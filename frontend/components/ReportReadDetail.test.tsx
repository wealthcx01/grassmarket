import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import {
  ReportReadDetail,
  readCoverageLabel,
  readWindowLabel,
} from "@/components/ReportReadDetail";
import { formatDwell, isAtCap, readWindow, MAX_DWELL_MS } from "@/lib/readTracking";
import { SECTION_TITLES } from "@/lib/reportSections";

/**
 * GRS-0235. The old display was `Read: business, advantage, constraint` — internal keys, and only
 * the sections that were opened. Both halves of that are what these tests hold down: no key ever
 * reaches the screen, and what was NOT read stays visible, because the gap is the preparation
 * signal.
 */

function row(section: string, over: Partial<Record<string, unknown>> = {}) {
  return {
    section,
    views: 1,
    total_dwell_ms: 45_000,
    first_viewed_at: "2026-08-12T09:14:00Z",
    last_viewed_at: "2026-08-12T09:15:00Z",
    ...over,
  } as never;
}

describe("ReportReadDetail (GRS-0235)", () => {
  it("names every section by its title, never by its key", () => {
    render(<ReportReadDetail sections={[row("business"), row("value")]} />);
    const panel = screen.getByTestId("read-detail");
    for (const title of Object.values(SECTION_TITLES)) {
      expect(within(panel).getByText(title)).toBeTruthy();
    }
    // The keys are what shipped before. None of them may appear as a standalone label.
    for (const key of Object.keys(SECTION_TITLES)) {
      expect(within(panel).queryByText(key)).toBeNull();
    }
  });

  it("shows sections that were not read, rather than omitting them", () => {
    // Only `business` was opened. The other five are the answer to "what should I ask about?".
    render(<ReportReadDetail sections={[row("business")]} />);
    const panel = screen.getByTestId("read-detail");
    expect(within(panel).getAllByText("not read")).toHaveLength(5);
  });

  it("lists sections in reading order, not the order the API returned them", () => {
    render(<ReportReadDetail sections={[row("appendix"), row("business")]} />);
    const titles = screen
      .getAllByRole("listitem")
      .map((li) => li.querySelector(".read-row-title")?.textContent);
    expect(titles).toEqual([
      "The business",
      "Where the advantage sits",
      "What is holding it back",
      "What to do about it",
      "What that is worth",
      "Technical appendix",
    ]);
  });

  it("states what the numbers cannot tell you", () => {
    render(<ReportReadDetail sections={[row("business")]} />);
    const caption = screen.getByTestId("read-detail").querySelector(".read-detail-caption");
    // Three claims the caption must carry: rounding, the cap, and the PDF blind spot.
    expect(caption?.textContent).toMatch(/rounded/i);
    expect(caption?.textContent).toMatch(/six hours/i);
    expect(caption?.textContent).toMatch(/PDF/);
  });

  it("marks a capped figure so 6h is not read as a real number", () => {
    render(<ReportReadDetail sections={[row("business", { total_dwell_ms: MAX_DWELL_MS })]} />);
    expect(screen.getByTestId("read-detail").textContent).toContain("at the cap");
  });
});

describe("the table cell labels", () => {
  it("counts coverage out of six rather than listing what was opened", () => {
    expect(readCoverageLabel([row("business"), row("value")])).toBe("2 of 6 sections");
  });

  it("says so plainly when nothing was opened", () => {
    expect(readCoverageLabel([])).toBe("not opened yet");
    expect(readCoverageLabel([row("business", { views: 0 })])).toBe("not opened yet");
  });

  it("collapses a single visit to one moment, and shows a range when they came back", () => {
    const once = readWindowLabel([
      row("business", { first_viewed_at: "2026-08-12T09:14:00Z", last_viewed_at: null }),
    ]);
    expect(once).not.toContain("→");

    const twice = readWindowLabel([
      row("business", {
        first_viewed_at: "2026-08-12T09:14:00Z",
        last_viewed_at: "2026-08-14T16:02:00Z",
      }),
    ]);
    expect(twice).toContain("→");
  });
});

describe("formatDwell", () => {
  it("rounds to 10s buckets so 47s and 52s do not invite comparison", () => {
    expect(formatDwell(47_000)).toBe("50s");
    expect(formatDwell(52_000)).toBe("50s");
  });

  it("never rounds an opened section down to zero", () => {
    // "0s" beside a view count of 1 reads as a bug, not as a short visit.
    expect(formatDwell(1_500)).toBe("under 10s");
    expect(formatDwell(0)).toBe("—");
  });

  it("carries minutes and hours", () => {
    expect(formatDwell(90_000)).toBe("1m 30s");
    expect(formatDwell(120_000)).toBe("2m");
    expect(formatDwell(3_600_000)).toBe("1h");
    expect(formatDwell(5_400_000)).toBe("1h 30m");
  });

  it("flags the cap at exactly the contract's ceiling", () => {
    expect(isAtCap(MAX_DWELL_MS)).toBe(true);
    expect(isAtCap(MAX_DWELL_MS - 1)).toBe(false);
  });
});

describe("readWindow", () => {
  it("takes the earliest first and latest last across sections, not one section's pair", () => {
    // A client rarely reads in order, so the first section opened is not necessarily `business`.
    const { first, last } = readWindow([
      row("value", {
        first_viewed_at: "2026-08-12T11:00:00Z",
        last_viewed_at: "2026-08-12T11:05:00Z",
      }),
      row("business", {
        first_viewed_at: "2026-08-12T09:00:00Z",
        last_viewed_at: "2026-08-12T09:10:00Z",
      }),
    ]);
    expect(first).toBe("2026-08-12T09:00:00Z");
    expect(last).toBe("2026-08-12T11:05:00Z");
  });

  it("returns nulls when nothing was ever opened", () => {
    expect(readWindow([row("business", { first_viewed_at: null, last_viewed_at: null })])).toEqual({
      first: null,
      last: null,
    });
  });
});
