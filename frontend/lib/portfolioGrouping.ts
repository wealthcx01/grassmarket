/**
 * Group a portfolio by subject (GRS-0177).
 *
 * The founder's own demo showed Revolut, Hargreaves Lansdown and WeBull twice each — a seeded
 * DEMO row and a SANDBOX row from a staging run, with identical scores — and nothing on the page
 * said why. Grouping is done here rather than in the API because it is a reading aid, not a change
 * to what the advisor owns: every record still exists and is still reachable, they are just no
 * longer presented as if they were different companies.
 *
 * The primary row is the one an advisor should act on, which is the most real record they hold:
 * production before sandbox before demo, then the most recently updated. That ordering matters
 * more than recency, because a fresh demo row is still a demo row.
 */

import type { BrokeragePortfolioEntry, RecordProvenance } from "@/lib/types";

/** Lower sorts first. A production record outranks a practice copy outranks a seeded illustration. */
const PROVENANCE_RANK: Record<RecordProvenance, number> = {
  production: 0,
  sandbox: 1,
  demo: 2,
};

export interface SubjectGroup {
  /** The trimmed, case-folded key the rows were grouped on. */
  key: string;
  /** The row to show and act on. */
  primary: BrokeragePortfolioEntry;
  /** Every other record for the same subject, in the same ranked order. */
  variants: BrokeragePortfolioEntry[];
}

function rank(entry: BrokeragePortfolioEntry): [number, number] {
  const updated = Date.parse(entry.updated_at);
  return [
    PROVENANCE_RANK[entry.provenance] ?? PROVENANCE_RANK.demo,
    // Negated so the most recent sorts first within a provenance tier.
    Number.isNaN(updated) ? 0 : -updated,
  ];
}

export function groupBySubject(entries: readonly BrokeragePortfolioEntry[]): SubjectGroup[] {
  const buckets = new Map<string, BrokeragePortfolioEntry[]>();
  const order: string[] = [];
  for (const entry of entries) {
    // An untitled record groups with other untitled records rather than with everything.
    const key = (entry.subject ?? "").trim().toLowerCase();
    if (!buckets.has(key)) {
      buckets.set(key, []);
      order.push(key);
    }
    buckets.get(key)!.push(entry);
  }
  return order.map((key) => {
    const rows = [...buckets.get(key)!].sort((a, b) => {
      const [ra, ua] = rank(a);
      const [rb, ub] = rank(b);
      return ra - rb || ua - ub;
    });
    return { key, primary: rows[0]!, variants: rows.slice(1) };
  });
}
