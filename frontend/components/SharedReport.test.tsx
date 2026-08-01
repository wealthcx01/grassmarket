/**
 * The client-facing shared report (GRS-0220).
 *
 * The client is the one reader who never sees the rest of the product, so what is asserted here is
 * what they are entitled to: the whole story in order, the numbers reachable rather than hidden,
 * and an honest statement that their reading is visible to the sender.
 */

import { render, screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  SharedReport,
  reportMarkText,
  type SharedReportPayload,
} from "@/components/SharedReport";

const SECTIONS = ["business", "advantage", "constraint", "actions", "value", "appendix"];

function payload(overrides: Partial<SharedReportPayload> = {}): SharedReportPayload {
  return {
    report: {
      subject: "Deutsche Börse",
      methodology_version: "1.6",
      coefficient_version: "v1-elicited",
      sections: SECTIONS.map((kind) => ({
        kind,
        heading: kind,
        body: [`Prose for ${kind}.`],
        figures:
          kind === "appendix"
            ? [
                {
                  key: "platform_value",
                  label: "Platform Value (0–100)",
                  rendered: "48",
                  source: "run.v_display_0_100",
                },
              ]
            : [],
      })),
    },
    figures: {
      maturity: { labels: ["Front End", "Back Office"], values: [44, 64] },
      value_buildup: { labels: ["Business", "Powers"], values: [68, 27] },
      module_breakdown: { labels: ["Front End", "Back Office"], values: [44, 64] },
    },
    tracking_notice: "The sender can see which sections of this report you open.",
    ...overrides,
  };
}

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true }));
  // jsdom has no IntersectionObserver; tracking must not be what breaks the page.
  vi.stubGlobal(
    "IntersectionObserver",
    class {
      observe() {}
      disconnect() {}
      unobserve() {}
    }
  );
});

describe("SharedReport (GRS-0220)", () => {
  it("tells the story in the content model's order, business first", () => {
    render(<SharedReport payload={payload()} token="t" />);
    const headings = screen.getAllByRole("heading", { level: 2 }).map((h) => h.textContent);
    expect(headings).toEqual([
      "The business",
      "Where the advantage sits",
      "What is holding it back",
      "What to do about it",
      "What that is worth",
    ]);
  });

  it("states the tracking notice on the page, not in a tooltip", () => {
    // Disclosure is the product requirement: no covert tracking.
    render(<SharedReport payload={payload()} token="t" />);
    expect(
      screen.getByText(/sender can see which sections of this report you open/i)
    ).toBeTruthy();
  });

  it("discloses the appendix rather than deleting it", () => {
    const { container } = render(<SharedReport payload={payload()} token="t" />);
    const details = container.querySelector("details.shared-appendix");
    expect(details).toBeTruthy();
    // Closed by default — the body reads as a story — but the numbers are IN the document.
    expect((details as HTMLDetailsElement).open).toBe(false);
    expect(within(details as HTMLElement).getByText(/Platform Value/)).toBeTruthy();
    expect(within(details as HTMLElement).getByText("run.v_display_0_100")).toBeTruthy();
  });

  it("gives every figure a text alternative, so no value is readable only as a bar", () => {
    render(<SharedReport payload={payload()} token="t" />);
    const figures = screen.getAllByRole("img");
    expect(figures.length).toBeGreaterThan(0);
    for (const figure of figures) {
      const label = figure.getAttribute("aria-label") ?? "";
      expect(label).toMatch(/out of 100/);
    }
    // And the numbers appear as text beside the chart, not only in the aria-label.
    expect(screen.getAllByText("44").length).toBeGreaterThan(0);
  });

  it("sends no events at all when tracking is disabled", () => {
    // The advisor's own preview is not a client read.
    render(<SharedReport payload={payload()} token="t" trackingEnabled={false} />);
    expect(fetch).not.toHaveBeenCalled();
  });

  it("names the client and the versions that produced the numbers", () => {
    render(<SharedReport payload={payload()} token="t" />);
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("Deutsche Börse");
    expect(screen.getByText(/Methodology 1.6/)).toBeTruthy();
    expect(screen.getByText(/coefficients v1-elicited/)).toBeTruthy();
  });

  it("renders without a maturity figure when the run has none", () => {
    // A run with no assessed module must not crash the client's page.
    const bare = payload();
    bare.figures = {};
    expect(() => render(<SharedReport payload={bare} token="t" />)).not.toThrow();
  });
});

describe("the non-production mark (GRS-0229)", () => {
  it("marks a sandbox record, persistently and at the top", () => {
    render(
      <SharedReport payload={payload({ non_production: true, draft: true })} token="t" />,
    );
    const mark = screen.getByTestId("report-mark");
    expect(mark.textContent).toContain("NON-PRODUCTION DATA");
    // role=alert, not note: this is the one thing on the page a reader must not miss.
    expect(mark.getAttribute("role")).toBe("alert");
    // The class carries `position: fixed`, which is what makes it survive scrolling. Asserting the
    // hook rather than the computed style, because jsdom does not lay anything out.
    expect(mark.className).toContain("shared-report-mark");
  });

  it("renders nothing for a production, client-approved record", () => {
    render(
      <SharedReport payload={payload({ non_production: false, draft: false })} token="t" />,
    );
    expect(screen.queryByTestId("report-mark")).toBeNull();
  });

  it("marks a draft on a production record, and says so in the PDF's words", () => {
    render(
      <SharedReport payload={payload({ non_production: false, draft: true })} token="t" />,
    );
    const mark = screen.getByTestId("report-mark");
    expect(mark.textContent).toContain("DRAFT");
    expect(mark.textContent).toContain("not client-usable");
    expect(mark.textContent).not.toContain("NON-PRODUCTION");
  });

  it("shows the mark when the flags are absent, because a legacy snapshot is not a safe one", () => {
    // A link issued before GRS-0229 has neither flag in its stored JSON. The backend defaults both
    // to true; this asserts the component agrees rather than silently rendering a clean page.
    const { non_production, draft, ...legacy } = payload({
      non_production: true,
      draft: true,
    });
    void non_production;
    void draft;
    render(<SharedReport payload={legacy as SharedReportPayload} token="t" />);
    const mark = screen.getByTestId("report-mark");
    expect(mark.textContent).toContain("NON-PRODUCTION DATA");
  });

  it("combines both marks when both apply", () => {
    expect(reportMarkText({ non_production: true, draft: true })).toContain("DRAFT");
    expect(reportMarkText({ non_production: true, draft: true })).toContain("NON-PRODUCTION DATA");
    expect(reportMarkText({ non_production: false, draft: false })).toBeNull();
    // Absent is not the same as false, and must not be treated as it.
    expect(reportMarkText({})).toContain("NON-PRODUCTION DATA");
  });
});

describe("figures label their bars and keep meaningful order (GRS-0233)", () => {
  const BUILDUP = {
    labels: ["Business", "Powers", "Infrastructure", "Platform Value"],
    values: [77, 29, 58, 55],
    ordered: true,
  };
  const RANKED = {
    labels: ["Back Office", "Front End", "EMS Gateway"],
    values: [80, 82, 50],
    notes: ["Back Office: scored on 3 of 4.", "Front End: scored on 4 of 4.", "EMS: 2 of 5."],
    ordered: false,
  };

  function figuresFor(over: Record<string, unknown>) {
    return payload({ figures: { ...(payload().figures as object), ...over } } as never);
  }

  it("keeps a composition figure in its declared order", () => {
    // The bug: every figure was sorted ascending, so the build-up rendered
    // Powers -> Platform Value -> Infrastructure -> Business under a caption promising a
    // composition. The sort destroyed the thing the figure was for.
    render(<SharedReport payload={figuresFor({ value_buildup: BUILDUP })} token="t" />);
    const rows = screen.getAllByText(/Business|Powers|Infrastructure|Platform Value/);
    const order = rows.map((r) => r.textContent);
    expect(order.slice(0, 4)).toEqual([
      "Business",
      "Powers",
      "Infrastructure",
      "Platform Value",
    ]);
  });

  it("still sorts a ranked figure weakest-first", () => {
    render(<SharedReport payload={figuresFor({ maturity: RANKED })} token="t" />);
    const labels = screen
      .getAllByText(/Back Office|Front End|EMS Gateway/)
      .map((el) => el.textContent);
    // Weakest-first is what the ranked figure's caption says it is, so it stays.
    expect(labels[0]).toBe("EMS Gateway");
  });

  it("labels every bar with its name and value", () => {
    // Nine solid bars with no labels was the defect. A client should never have to count rows
    // against a separately-sorted table to know which bar is which.
    render(<SharedReport payload={figuresFor({ maturity: RANKED })} token="t" />);
    for (const label of RANKED.labels) {
      // getAllBy, not getBy: a module can legitimately appear in more than one figure on the page.
      expect(screen.getAllByText(label).length).toBeGreaterThan(0);
    }
    for (const value of ["80", "82", "50"]) {
      expect(screen.getAllByText(value).length).toBeGreaterThan(0);
    }
  });

  it("carries each bar's meaning on hover where there is one", () => {
    const { container } = render(
      <SharedReport payload={figuresFor({ maturity: RANKED })} token="t" />,
    );
    const titled = container.querySelectorAll(".shared-bar-row[title]");
    expect(titled.length).toBe(RANKED.labels.length);
  });

  it("renders without notes, because an older snapshot has none", () => {
    // Snapshots issued before GRS-0233 carry no `notes` and no `ordered`. They must still render.
    const legacy = { labels: ["A", "B"], values: [10, 20] };
    render(<SharedReport payload={figuresFor({ maturity: legacy })} token="t" />);
    expect(screen.getByText("A")).toBeTruthy();
  });
});

