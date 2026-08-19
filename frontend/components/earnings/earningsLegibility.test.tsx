import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ConsultingRateMatrix } from "@/components/earnings/ConsultingRateMatrix";
import { HowYouGetPaid, STAT_DEFINITIONS } from "@/components/earnings/HowYouGetPaid";
import type { ConsultancyCommissionCarrot } from "@/lib/types";

/**
 * GRS-0240. The founder's verdict was "the earnings page is so confusing", walked as a
 * zero-earnings first-time user. The rates were never the problem — they are config-driven and
 * correct. The problem was that the page opened with five undefined £0.00 cards and used four
 * undefined terms in a rate grid that wasn't a grid.
 *
 * These hold the vocabulary and the definitions in place, because that is what regressed last time
 * (this page has already needed one legibility patch).
 */

const money = (amount: number) => ({ amount_minor: amount * 100, currency: "GBP" }) as never;

const CARROTS: ConsultancyCommissionCarrot[] = [
  {
    delivery_type: "bruntsfield_led",
    sourcing: "self_sourced",
    delivery_label: "Bruntsfield-led",
    sourcing_label: "Self-sourced",
    yr1_bps: 6500,
    thereafter_bps: 5500,
    example_deal: money(100_000),
    yr1_commission: money(65_000),
    thereafter_commission: money(55_000),
    schedule_version: "v7",
  },
  {
    delivery_type: "consultant_led",
    sourcing: "self_sourced",
    delivery_label: "Consultant-led",
    sourcing_label: "Self-sourced",
    yr1_bps: 7500,
    thereafter_bps: 6500,
    example_deal: money(100_000),
    yr1_commission: money(75_000),
    thereafter_commission: money(65_000),
    schedule_version: "v7",
  },
  {
    delivery_type: "bruntsfield_led",
    sourcing: "bruntsfield_sourced",
    delivery_label: "Bruntsfield-led",
    sourcing_label: "Bruntsfield-sourced",
    yr1_bps: 4500,
    thereafter_bps: 3500,
    example_deal: money(100_000),
    yr1_commission: money(45_000),
    thereafter_commission: money(35_000),
    schedule_version: "v7",
  },
];

describe("How you get paid (scope 1)", () => {
  it("names both streams, with the letters the statement also uses", () => {
    // Not a style choice: `earnings/statement.py` prints "Stream B" as a heading, so an advisor
    // comparing page to document needs the two to agree. Labelling one and not the other was the
    // original defect.
    render(<HowYouGetPaid />);
    const block = screen.getByTestId("how-you-get-paid");
    expect(block.textContent).toContain("Stream A");
    expect(block.textContent).toContain("Stream B");
  });

  it("explains the three states a commission line moves through, in order", () => {
    render(<HowYouGetPaid />);
    const text = screen.getByTestId("how-you-get-paid").textContent ?? "";
    expect(text.indexOf("Pending")).toBeLessThan(text.indexOf("Invoiced"));
    expect(text.indexOf("Invoiced")).toBeLessThan(text.indexOf("Paid"));
  });

  it("defines projected unpaid on the page, not only in a docstring", () => {
    // It was defined *only* in a contract docstring, which no advisor will ever read.
    render(<HowYouGetPaid />);
    expect(screen.getByTestId("how-you-get-paid").textContent).toMatch(
      /projected unpaid.*pending plus invoiced/i,
    );
  });

  it("says an advisor never creates a line themselves", () => {
    render(<HowYouGetPaid />);
    expect(screen.getByTestId("how-you-get-paid").textContent).toMatch(/never enter one yourself/i);
  });
});

describe("stat definitions (scope 4)", () => {
  it("covers every card on the page, so no £0.00 is unexplained", () => {
    for (const label of ["Earned YTD", "Pending", "Invoiced", "Paid", "Projected unpaid"]) {
      expect(STAT_DEFINITIONS[label], `${label} has no definition`).toBeTruthy();
    }
  });
});

describe("the consulting rate matrix (scope 3)", () => {
  it("renders a real 2x2 with both axes labelled", () => {
    render(<ConsultingRateMatrix carrots={CARROTS} />);
    const table = screen.getByTestId("consulting-rate-matrix");
    expect(within(table).getByText("Bruntsfield-sourced")).toBeTruthy();
    expect(within(table).getByRole("rowheader", { name: "Consultant-led" })).toBeTruthy();
  });

  it("defines both axis terms in the caption", () => {
    render(<ConsultingRateMatrix carrots={CARROTS} />);
    const caption = screen.getByTestId("consulting-rate-matrix").querySelector("caption");
    expect(caption?.textContent).toMatch(/who delivers it/i);
    expect(caption?.textContent).toMatch(/who brought it in/i);
  });

  it("uses one vocabulary — 'first year' and 'thereafter', never yr1/yr2", () => {
    // The page previously mixed "yr1/yr2" (products) with "first year / thereafter" (consulting)
    // for the same concept.
    const text = render(<ConsultingRateMatrix carrots={CARROTS} />).container.textContent ?? "";
    expect(text).toMatch(/first year/);
    expect(text).toMatch(/thereafter/);
    expect(text).not.toMatch(/yr1|yr2/i);
  });

  it("says so when the schedule has no rate for a cell, rather than leaving it blank", () => {
    // A blank box in a rate table reads as 0%. Only three of the four cells are supplied here.
    render(<ConsultingRateMatrix carrots={CARROTS} />);
    expect(screen.getByText("Not in the schedule")).toBeTruthy();
  });

  it("marks example money as illustrative in the number's own presentation", () => {
    // On a money page, an example styled like a balance invites exactly the wrong trust.
    render(<ConsultingRateMatrix carrots={CARROTS} />);
    expect(screen.getAllByText(/Illustrative:/).length).toBeGreaterThan(0);
  });

  it("builds the axes from the carrots, so a schedule change reflows with no frontend edit", () => {
    const renamed = CARROTS.map((c) =>
      c.delivery_type === "consultant_led" ? { ...c, delivery_label: "Advisor-led" } : c,
    );
    render(<ConsultingRateMatrix carrots={renamed} />);
    expect(screen.getByRole("rowheader", { name: "Advisor-led" })).toBeTruthy();
  });

  it("renders nothing when the schedule returns no consulting rates", () => {
    const { container } = render(<ConsultingRateMatrix carrots={[]} />);
    expect(container.innerHTML).toBe("");
  });
});
