/**
 * GRS-0181: paging the long wizard steps one module at a time.
 *
 * The founder's instinct was that "a long list may be daunting to an advisor, but lots of smaller
 * pages may be easier to handle". What matters in these tests is that paging changes only WHICH
 * module is on screen — the ratings, the document, and the autosave path are untouched — and that
 * an advisor can always see how much is left and get back to the old view.
 */

import { fireEvent, render, screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { InfrastructureDeepDiveStep, CustomerPropositionStep } from "@/components/steps";
import type { StepProps } from "@/components/steps";
import type { AssessmentDocument, Registry } from "@/lib/types";

vi.mock("@/components/GuidancePanel", () => ({ GuidancePanel: () => <div>guidance</div> }));

const MODULES = [
  { key: "front", name: "Front End", subcomponents: [{ key: "f1", name: "Sign-up", critical: false }] },
  { key: "mid", name: "Middle Office", subcomponents: [{ key: "m1", name: "Booking", critical: false }] },
  { key: "liq", name: "Liquidity", subcomponents: [{ key: "l1", name: "Routing", critical: false }] },
];

const REGISTRY = {
  powers: [],
  modules: MODULES,
  metrics: [],
  subcomponent_status: "ok",
  metric_status: "ok",
  c_modules: [
    { key: "c1", name: "Onboarding", subcomponents: [{ key: "cs1", name: "KYC", critical: false }] },
    { key: "c2", name: "Trading", subcomponents: [{ key: "cs2", name: "Order ticket", critical: false }] },
  ],
  c_widgets: [{ key: "w1", name: "Watchlist", category: "Discovery", rarity: "Common" }],
  c_status: "ok",
  c_widget_profile: "retail",
} as unknown as Registry;

const DOCUMENT = {
  subject: "Revolut",
  profile: { operating_model: "retail", asset_classes: [], regions: [] },
  subcomponents: [],
  metrics: [],
  powers: [],
  c_subcomponents: [],
  widgets: [],
} as unknown as AssessmentDocument;

function props(over: Partial<StepProps> = {}): StepProps {
  return {
    registry: REGISTRY,
    profiles: [],
    document: DOCUMENT,
    update: vi.fn(),
    readOnly: false,
    assessmentId: "a1",
    live: null,
    liveLoading: false,
    liveError: null,
    refreshLive: vi.fn(),
    onFinalise: vi.fn(),
    finalising: false,
    provenance: "production",
    onPreviewInSandbox: vi.fn(),
    previewingSandbox: false,
    clientUsable: true,
    finalEntry: null,
    ...over,
  } as StepProps;
}

describe("Infrastructure step paging (GRS-0181)", () => {
  beforeEach(() => window.localStorage.clear());

  it("shows one module at a time by default, so a first-time advisor gets small pages", () => {
    render(<InfrastructureDeepDiveStep {...props()} />);
    expect(screen.getByText("Sign-up")).toBeTruthy();
    expect(screen.queryByText("Booking")).toBeNull();
    expect(screen.queryByText("Routing")).toBeNull();
  });

  it("says where you are and how much is left", () => {
    render(<InfrastructureDeepDiveStep {...props()} />);
    expect(screen.getByText("1 of 3")).toBeTruthy();
  });

  it("moves between modules, not between subcomponents", () => {
    render(<InfrastructureDeepDiveStep {...props()} />);
    fireEvent.click(screen.getByRole("button", { name: /Next module/ }));
    expect(screen.getByText("Booking")).toBeTruthy();
    expect(screen.queryByText("Sign-up")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: /Previous module/ }));
    expect(screen.getByText("Sign-up")).toBeTruthy();
  });

  it("stops at both ends rather than wrapping", () => {
    render(<InfrastructureDeepDiveStep {...props()} />);
    expect((screen.getByRole("button", { name: /Previous module/ }) as HTMLButtonElement).disabled).toBe(true);
    fireEvent.click(screen.getByRole("button", { name: /Next module/ }));
    fireEvent.click(screen.getByRole("button", { name: /Next module/ }));
    expect((screen.getByRole("button", { name: /Next module/ }) as HTMLButtonElement).disabled).toBe(true);
  });

  it("jumps straight to a module from the chip list", () => {
    render(<InfrastructureDeepDiveStep {...props()} />);
    const nav = screen.getByRole("navigation", { name: "Modules" });
    fireEvent.click(within(nav).getByRole("button", { name: /Liquidity/ }));
    expect(screen.getByText("Routing")).toBeTruthy();
    expect(screen.getByText("3 of 3")).toBeTruthy();
  });

  it("shows each module's progress on its chip, so nothing is hidden by paging", () => {
    render(<InfrastructureDeepDiveStep {...props()} />);
    const nav = screen.getByRole("navigation", { name: "Modules" });
    expect(within(nav).getByRole("button", { name: /Front End/ }).textContent).toContain("0/1");
    expect(within(nav).getAllByRole("button")).toHaveLength(3);
  });

  it("reports its position so the stepper can show it", () => {
    const onSubStepChange = vi.fn();
    render(<InfrastructureDeepDiveStep {...props({ onSubStepChange })} />);
    expect(onSubStepChange).toHaveBeenCalledWith("module 1 of 3");
    fireEvent.click(screen.getByRole("button", { name: /Next module/ }));
    expect(onSubStepChange).toHaveBeenCalledWith("module 2 of 3");
  });

  describe("the show-all escape hatch", () => {
    it("returns every module to one page", () => {
      render(<InfrastructureDeepDiveStep {...props()} />);
      fireEvent.click(screen.getByRole("button", { name: /Show all modules on one page/ }));
      expect(screen.getByText("Sign-up")).toBeTruthy();
      expect(screen.getByText("Booking")).toBeTruthy();
      expect(screen.getByText("Routing")).toBeTruthy();
      expect(screen.queryByRole("button", { name: /Next module/ })).toBeNull();
    });

    it("brings back Expand all / Collapse all, which only means something in show-all", () => {
      render(<InfrastructureDeepDiveStep {...props()} />);
      expect(screen.queryByRole("button", { name: /Collapse all|Expand all/ })).toBeNull();
      fireEvent.click(screen.getByRole("button", { name: /Show all modules on one page/ }));
      expect(screen.getByRole("button", { name: /Collapse all|Expand all/ })).toBeTruthy();
    });

    it("remembers the preference for next time", () => {
      const first = render(<InfrastructureDeepDiveStep {...props()} />);
      fireEvent.click(screen.getByRole("button", { name: /Show all modules on one page/ }));
      expect(window.localStorage.getItem("gm:wizard:show-all-modules")).toBe("1");
      first.unmount();
      render(<InfrastructureDeepDiveStep {...props()} />);
      expect(screen.getByText("Booking")).toBeTruthy();
    });

    it("clears the stepper sub-position, because there is no position in show-all", () => {
      const onSubStepChange = vi.fn();
      render(<InfrastructureDeepDiveStep {...props({ onSubStepChange })} />);
      onSubStepChange.mockClear();
      fireEvent.click(screen.getByRole("button", { name: /Show all modules on one page/ }));
      expect(onSubStepChange).toHaveBeenCalledWith(null);
    });
  });

  it("still records a rating through the unchanged update path", () => {
    const update = vi.fn();
    render(<InfrastructureDeepDiveStep {...props({ update })} />);
    fireEvent.click(screen.getByRole("button", { name: "Advanced" }));
    expect(update).toHaveBeenCalled();
  });
});

describe("Customer Proposition step paging (GRS-0181)", () => {
  beforeEach(() => window.localStorage.clear());

  it("pages the C modules and adds the widget checklist as the last page", () => {
    render(<CustomerPropositionStep {...props()} />);
    expect(screen.getByText("KYC")).toBeTruthy();
    expect(screen.getByText("1 of 3")).toBeTruthy(); // 2 modules + the checklist
    const nav = screen.getByRole("navigation", { name: "Modules" });
    expect(within(nav).getByRole("button", { name: /Widget checklist/ })).toBeTruthy();
  });

  it("reaches the widget checklist by paging to the end", () => {
    render(<CustomerPropositionStep {...props()} />);
    const nav = screen.getByRole("navigation", { name: "Modules" });
    fireEvent.click(within(nav).getByRole("button", { name: /Widget checklist/ }));
    // Scoped to the heading: the step intro also names the checklist in prose.
    expect(screen.getByRole("heading", { name: "Level-1 widget checklist" })).toBeTruthy();
    expect(screen.queryByText("KYC")).toBeNull();
  });

  it("leaves the not-modelled segment branch alone — there is nothing to page", () => {
    const exchangeRegistry = { ...REGISTRY, c_modules: [] } as unknown as Registry;
    render(
      <CustomerPropositionStep
        {...props({
          registry: exchangeRegistry,
          document: {
            ...DOCUMENT,
            profile: { operating_model: "exchange", asset_classes: [], regions: [] },
          } as unknown as AssessmentDocument,
        })}
      />,
    );
    expect(screen.getByText(/not yet modelled/)).toBeTruthy();
    expect(screen.queryByRole("navigation", { name: "Modules" })).toBeNull();
  });
});
