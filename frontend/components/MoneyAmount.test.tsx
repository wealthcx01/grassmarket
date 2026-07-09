import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { MoneyAmount } from "@/components/MoneyAmount";
import { formatMoney } from "@/lib/money";
import type { Money } from "@/lib/types";

const fee: Money = {
  amount_minor: 750000,
  currency: "GBP",
  assumption_register_ref: "recovery-fees-v1:advisor",
};

describe("Money display (ADR-0002 at the view layer)", () => {
  it("renders the API's amount + currency verbatim, not a recomputation", () => {
    render(<MoneyAmount money={fee} />);
    // £7,500.00 comes straight from amount_minor=750000 — the client never derives it from a rate.
    expect(screen.getByTestId("money").textContent).toBe("£7,500.00");
  });

  it("formats different currencies from the object", () => {
    expect(formatMoney({ amount_minor: 100000, currency: "USD", assumption_register_ref: "x" })).toBe(
      "$1,000.00",
    );
    expect(formatMoney({ amount_minor: 12345, currency: "EUR", assumption_register_ref: "x" })).toBe(
      "€123.45",
    );
  });
});
