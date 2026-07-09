/**
 * Renders a `Money` value straight from the API (GRS-0014). Display only — it delegates to
 * `formatMoney`, which does no business arithmetic. The £ shown is the £ the API computed.
 */

import { formatMoney } from "@/lib/money";
import type { Money } from "@/lib/types";

export function MoneyAmount({ money }: { money: Money }) {
  return (
    <span className="mono" data-testid="money">
      {formatMoney(money)}
    </span>
  );
}
