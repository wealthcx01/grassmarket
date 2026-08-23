import { render, screen, waitFor } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { FirstRunChecklist, firstRunChecklistComplete } from "@/components/FirstRunChecklist";
import { HomeSectionState } from "@/components/HomeSectionState";
import { api } from "@/lib/api";

vi.mock("@/lib/api", async (importActual) => {
  const actual = await importActual<typeof import("@/lib/api")>();
  return {
    ...actual,
    api: {
      ...actual.api,
      pipelineBoard: vi.fn(),
      listAssessments: vi.fn(),
      listAllDeliverables: vi.fn(),
      earningsSummary: vi.fn(),
    },
  };
});

const mocked = api as unknown as {
  pipelineBoard: ReturnType<typeof vi.fn>;
  listAssessments: ReturnType<typeof vi.fn>;
  listAllDeliverables: ReturnType<typeof vi.fn>;
  earningsSummary: ReturnType<typeof vi.fn>;
};

/**
 * GRS-0243 scopes 3 and 5. The founder walked every section and said none of it made sense. Two
 * things follow: the home page has to say what is actually waiting for them, and a new advisor
 * needs a path through the product rather than five descriptions of it.
 */

describe("the live one-liner on a home card (scope 3)", () => {
  beforeEach(() => vi.clearAllMocks());

  it("says what is waiting, not what the section is", async () => {
    mocked.pipelineBoard.mockResolvedValue({
      generated_at: "x",
      entries: [{ stale: true }, { stale: false }, { stale: false }],
    });
    render(<HomeSectionState section="pipeline" />);
    const line = await screen.findByTestId("home-state-pipeline");
    expect(line.textContent).toContain("3 in the pipeline");
    expect(line.textContent).toContain("1 going stale");
  });

  it("says what would put a number there when there is nothing", async () => {
    // "0 prospects" is noise. The empty case has to teach, same rule as the section empty states.
    mocked.pipelineBoard.mockResolvedValue({ generated_at: "x", entries: [] });
    render(<HomeSectionState section="pipeline" />);
    const line = await screen.findByTestId("home-state-pipeline");
    expect(line.textContent).toMatch(/add one to start/i);
    expect(line.textContent).not.toMatch(/^0 /);
  });

  it("omits a zero count rather than printing it", async () => {
    mocked.listAssessments.mockResolvedValue([{ state: "finalised" }, { state: "finalised" }]);
    render(<HomeSectionState section="portfolio" />);
    const line = await screen.findByTestId("home-state-portfolio");
    expect(line.textContent).toBe("2 assessed, all finalised");
  });

  it("renders NOTHING when the fetch fails", async () => {
    // The one that matters. An advisor reading "no deliverables" during an outage will act on it —
    // silence is the only honest output when we do not know.
    mocked.listAllDeliverables.mockRejectedValue(new Error("network"));
    const { container } = render(<HomeSectionState section="deliverables" />);
    await waitFor(() => expect(mocked.listAllDeliverables).toHaveBeenCalled());
    expect(container.querySelector("[data-testid='home-state-deliverables']")).toBeNull();
  });

  it("does not invent a count for the Workbench", async () => {
    // A number of courses is decorative metadata, which is the thing this ticket is about.
    render(<HomeSectionState section="workbench" />);
    const line = await screen.findByTestId("home-state-workbench");
    expect(line.textContent).not.toMatch(/\d/);
  });
});

describe("the first-run checklist (scope 5)", () => {
  beforeEach(() => {
    window.localStorage.clear();
    vi.clearAllMocks();
  });

  it("shows four steps and its progress", async () => {
    render(<FirstRunChecklist />);
    const card = await screen.findByTestId("first-run-checklist");
    expect(card.textContent).toContain("0 of 4");
    expect(screen.getAllByRole("link")).toHaveLength(4);
  });

  it("ticks a step on the click that navigates, and keeps it", async () => {
    // Asking an advisor to navigate away and come back to tick a box is how a checklist stops
    // being used. The tick is a bookmark, not a claim they read it carefully.
    const { unmount } = render(<FirstRunChecklist />);
    fireEvent.click(await screen.findByRole("link", { name: /three lenses/i }));
    unmount();

    render(<FirstRunChecklist />);
    expect((await screen.findByTestId("first-run-checklist")).textContent).toContain("1 of 4");
  });

  it("disappears once all four are done", async () => {
    window.localStorage.setItem(
      "bas.first_run_checklist",
      JSON.stringify(["primer", "report", "summary", "earnings"]),
    );
    const { container } = render(<FirstRunChecklist />);
    await waitFor(() =>
      expect(container.querySelector("[data-testid='first-run-checklist']")).toBeNull(),
    );
  });

  it("starts over rather than throwing on corrupt state", async () => {
    window.localStorage.setItem("bas.first_run_checklist", "{not json");
    render(<FirstRunChecklist />);
    expect((await screen.findByTestId("first-run-checklist")).textContent).toContain("0 of 4");
  });

  it("reports completion so two orientation devices never share a screen", () => {
    expect(firstRunChecklistComplete()).toBe(false);
    window.localStorage.setItem(
      "bas.first_run_checklist",
      JSON.stringify(["primer", "report", "summary", "earnings"]),
    );
    expect(firstRunChecklistComplete()).toBe(true);
  });
});
