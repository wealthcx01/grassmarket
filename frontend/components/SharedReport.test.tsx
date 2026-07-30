/**
 * The client-facing shared report (GRS-0220).
 *
 * The client is the one reader who never sees the rest of the product, so what is asserted here is
 * what they are entitled to: the whole story in order, the numbers reachable rather than hidden,
 * and an honest statement that their reading is visible to the sender.
 */

import { render, screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { SharedReport, type SharedReportPayload } from "@/components/SharedReport";

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
