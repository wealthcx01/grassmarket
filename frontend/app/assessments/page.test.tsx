/**
 * GRS-0177: the portfolio page. What is pinned here is the founder's actual complaint — the same
 * company appearing several times with nothing saying why — and the explanation that replaces it.
 */

import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { BrokeragePortfolioEntry, RecordProvenance } from "@/lib/types";

const brokeragePortfolio = vi.fn();
const registryProfiles = vi.fn();

vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn(), replace: vi.fn() }) }));
vi.mock("@/lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api")>();
  return {
    ...actual,
    getToken: () => "token",
    api: {
      brokeragePortfolio: (...a: unknown[]) => brokeragePortfolio(...a),
      registryProfiles: (...a: unknown[]) => registryProfiles(...a),
    },
  };
});

import PortfolioPage from "@/app/assessments/page";

function entry(
  id: string,
  subject: string,
  provenance: RecordProvenance,
  updated = "2026-07-21T00:00:00Z",
): BrokeragePortfolioEntry {
  return {
    assessment_id: id,
    subject,
    segment: "Broker",
    state: "finalised",
    provenance,
    v_index: 61,
    coverage: 0.8,
    updated_at: updated,
  } as BrokeragePortfolioEntry;
}

const DUPLICATED = [
  entry("demo", "Revolut", "demo", "2026-07-22T00:00:00Z"),
  entry("sandbox", "Revolut", "sandbox", "2026-07-21T00:00:00Z"),
  entry("prod", "Revolut", "production", "2026-07-20T00:00:00Z"),
];

async function renderPage(rows: BrokeragePortfolioEntry[]) {
  brokeragePortfolio.mockResolvedValue(rows);
  registryProfiles.mockResolvedValue([{ key: "retail", name: "Retail", client_usable: true }]);
  const result = render(<PortfolioPage />);
  await waitFor(() => expect(brokeragePortfolio).toHaveBeenCalled());
  return result;
}

describe("Portfolio page (GRS-0177)", () => {
  beforeEach(() => {
    brokeragePortfolio.mockReset();
    registryProfiles.mockReset();
    window.localStorage.clear();
  });

  describe("one row per company", () => {
    it("shows a single row for a subject assessed three ways, with a variant count", async () => {
      await renderPage(DUPLICATED);
      await waitFor(() => expect(screen.getAllByRole("link", { name: "Revolut" })).toHaveLength(1));
      expect(screen.getByRole("button", { name: /2 variants/ })).toBeTruthy();
    });

    it("makes the production record the one you act on", async () => {
      const { container } = await renderPage(DUPLICATED);
      await waitFor(() => expect(container.querySelectorAll("tbody tr").length).toBe(1));
      const link = screen.getByRole("link", { name: "Revolut" });
      // The production record, even though the demo row is the most recently updated.
      expect(link.getAttribute("href")).toBe("/assessments/prod");
    });

    it("reveals the other records on demand, each with its own badge and link", async () => {
      const { container } = await renderPage(DUPLICATED);
      await waitFor(() => expect(screen.getByRole("button", { name: /2 variants/ })).toBeTruthy());
      fireEvent.click(screen.getByRole("button", { name: /2 variants/ }));
      await waitFor(() => expect(container.querySelectorAll("tbody tr").length).toBe(3));
      const hrefs = Array.from(container.querySelectorAll('tbody a[href^="/assessments/"]')).map(
        (a) => a.getAttribute("href"),
      );
      expect(hrefs).toEqual(["/assessments/prod", "/assessments/sandbox", "/assessments/demo"]);
      expect(screen.getByText(/Sandbox: non-production/)).toBeTruthy();
      expect(screen.getByText(/Demo: illustrative only/)).toBeTruthy();
    });

    it("collapses again on a second click", async () => {
      const { container } = await renderPage(DUPLICATED);
      const chip = await screen.findByRole("button", { name: /2 variants/ });
      fireEvent.click(chip);
      await waitFor(() => expect(container.querySelectorAll("tbody tr").length).toBe(3));
      fireEvent.click(screen.getByRole("button", { name: /2 variants/ }));
      await waitFor(() => expect(container.querySelectorAll("tbody tr").length).toBe(1));
    });

    it("shows no chip when a company has only one record", async () => {
      await renderPage([entry("only", "Monzo", "production")]);
      await waitFor(() => expect(screen.getByRole("link", { name: "Monzo" })).toBeTruthy());
      expect(screen.queryByRole("button", { name: /variant/ })).toBeNull();
    });
  });

  describe("the first-visit explanation", () => {
    it("explains the badges when there is something to explain", async () => {
      await renderPage(DUPLICATED);
      await waitFor(() => expect(screen.getByText(/seeded illustrative record/)).toBeTruthy());
      // The same phrase deliberately appears on the checkbox too — one explanation, two places.
      expect(screen.getAllByText(/private practice copy/).length).toBeGreaterThan(1);
      expect(screen.getByText(/grouped/)).toBeTruthy();
    });

    it("stays dismissed once dismissed", async () => {
      await renderPage(DUPLICATED);
      const dismiss = await screen.findByRole("button", { name: "Got it" });
      fireEvent.click(dismiss);
      await waitFor(() => expect(screen.queryByText(/seeded illustrative record/)).toBeNull());
      expect(window.localStorage.getItem("gm:portfolio:demo-note")).toBe("1");
    });

    it("does not appear on a portfolio of only production records", async () => {
      await renderPage([entry("p", "Monzo", "production")]);
      await waitFor(() => expect(screen.getByRole("link", { name: "Monzo" })).toBeTruthy());
      expect(screen.queryByText(/seeded illustrative record/)).toBeNull();
    });

    it("does not reappear for a returning advisor", async () => {
      window.localStorage.setItem("gm:portfolio:demo-note", "1");
      await renderPage(DUPLICATED);
      await waitFor(() => expect(screen.getByRole("link", { name: "Revolut" })).toBeTruthy());
      expect(screen.queryByText(/seeded illustrative record/)).toBeNull();
    });
  });

  describe("the sandbox option reads in plain words", () => {
    it("says what a practice copy is, in visible text rather than a tooltip", async () => {
      // GRS-0178: an advisor deciding whether to tick this should not have to hover to find out.
      await renderPage([entry("p", "Monzo", "production")]);
      await screen.findByText(/Make this a private practice copy/);
      const explanation = screen.getByText(/without a second rater or a committee/);
      expect(explanation).toBeTruthy();
      expect(explanation.textContent).toMatch(/never reach a client/);
    });

    it("labels the checkbox so clicking the text toggles it", async () => {
      await renderPage([entry("p", "Monzo", "production")]);
      const checkbox = (await screen.findByLabelText(/Make this a private practice copy/)) as HTMLInputElement;
      expect(checkbox.type).toBe("checkbox");
      expect(checkbox.checked).toBe(false);
      fireEvent.click(checkbox);
      expect(checkbox.checked).toBe(true);
    });
  });

  describe("the creation form is aligned by structure (GRS-0178)", () => {
    it("lays the fields out on a grid rather than a flex row with padded alignment", async () => {
      const { container } = await renderPage([entry("p", "Monzo", "production")]);
      const form = container.querySelector("form") as HTMLElement;
      expect(form.className).toBe("form-create-assessment");
      // The magic number that used to fake the baseline is gone. (0.55rem still appears as
      // ordinary input padding, so the assertion names the property, not the value.)
      expect(form.innerHTML).not.toContain("padding-bottom");
      expect(form.getAttribute("style")).toBeNull();
    });

    it("keeps the three fields and the submit control", async () => {
      await renderPage([entry("p", "Monzo", "production")]);
      expect(screen.getByText(/subject company/i)).toBeTruthy();
      expect(screen.getByText("Operating model")).toBeTruthy();
      expect(screen.getByRole("button", { name: /Create and open/ })).toBeTruthy();
    });
  });

  describe("the rest of the table is unchanged", () => {
    it("still shows segment, coverage and the locked score", async () => {
      const { container } = await renderPage([entry("p", "Monzo", "production")]);
      await waitFor(() => expect(container.querySelector("tbody tr")).not.toBeNull());
      const row = container.querySelector("tbody tr") as HTMLElement;
      expect(within(row).getByText("Broker")).toBeTruthy();
      expect(row.textContent).toContain("61");
    });
  });
});
