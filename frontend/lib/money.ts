/**
 * Money DISPLAY only (GRS-0014, ADR-0002 at the view layer).
 *
 * The API sends `Money` as integer minor units + a currency. This formats that exact figure for
 * the screen — converting minor→major units and grouping digits. It performs NO business
 * arithmetic: it never combines two amounts, never derives a fee from a rate, never multiplies by a
 * count. The £ the user sees is the £ the API computed; the client only renders it.
 */

import type { Money } from "@/lib/types";

const SYMBOL: Record<Money["currency"], string> = { GBP: "£", USD: "$", EUR: "€" };

export function formatMoney(money: Money): string {
  const major = (money.amount_minor / 100).toLocaleString("en-GB", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  return `${SYMBOL[money.currency]}${major}`;
}
