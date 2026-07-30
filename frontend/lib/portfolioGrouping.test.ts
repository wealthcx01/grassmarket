/**
 * GRS-0177: grouping the portfolio by subject. The founder's demo showed three companies twice
 * each with identical scores and nothing explaining why, so the ordering rule here — most real
 * record first — is the thing worth pinning.
 */

import { describe, expect, it } from "vitest";

import { groupBySubject } from "@/lib/portfolioGrouping";
import type { BrokeragePortfolioEntry, RecordProvenance } from "@/lib/types";

function entry(
  id: string,
  subject: string,
  provenance: RecordProvenance,
  updated = "2026-07-21T00:00:00Z",
): BrokeragePortfolioEntry {
  return {
    assessment_id: id,
    subject,
    segment: null,
    state: "finalised",
    provenance,
    updated_at: updated,
  } as BrokeragePortfolioEntry;
}

describe("groupBySubject (GRS-0177)", () => {
  it("collapses the same company assessed on several paths into one group", () => {
    const groups = groupBySubject([
      entry("d", "Revolut", "demo"),
      entry("s", "Revolut", "sandbox"),
      entry("p", "Revolut", "production"),
    ]);
    expect(groups).toHaveLength(1);
    expect(groups[0]!.primary.assessment_id).toBe("p");
    expect(groups[0]!.variants.map((v) => v.assessment_id)).toEqual(["s", "d"]);
  });

  it("picks the production record regardless of input order", () => {
    const rows = [entry("s", "Revolut", "sandbox"), entry("p", "Revolut", "production")];
    expect(groupBySubject(rows)[0]!.primary.assessment_id).toBe("p");
    expect(groupBySubject([...rows].reverse())[0]!.primary.assessment_id).toBe("p");
  });

  it("prefers a real record over a merely newer one", () => {
    // A fresh demo row is still a demo row: provenance outranks recency.
    const groups = groupBySubject([
      entry("new-demo", "WeBull", "demo", "2026-07-25T00:00:00Z"),
      entry("old-prod", "WeBull", "production", "2026-01-01T00:00:00Z"),
    ]);
    expect(groups[0]!.primary.assessment_id).toBe("old-prod");
  });

  it("breaks a provenance tie on the most recent update", () => {
    const groups = groupBySubject([
      entry("older", "WeBull", "sandbox", "2026-07-01T00:00:00Z"),
      entry("newer", "WeBull", "sandbox", "2026-07-20T00:00:00Z"),
    ]);
    expect(groups[0]!.primary.assessment_id).toBe("newer");
  });

  it("matches on trimmed, case-folded subjects", () => {
    const groups = groupBySubject([
      entry("a", "Hargreaves Lansdown", "production"),
      entry("b", "  hargreaves lansdown ", "sandbox"),
    ]);
    expect(groups).toHaveLength(1);
    expect(groups[0]!.variants).toHaveLength(1);
  });

  it("leaves a single-record subject with no variants", () => {
    const groups = groupBySubject([entry("only", "Monzo", "production")]);
    expect(groups[0]!.variants).toEqual([]);
  });

  it("keeps distinct companies apart and in first-seen order", () => {
    const groups = groupBySubject([
      entry("a", "Monzo", "production"),
      entry("b", "Starling", "production"),
      entry("c", "Monzo", "demo"),
    ]);
    expect(groups.map((g) => g.primary.subject)).toEqual(["Monzo", "Starling"]);
    expect(groups[0]!.variants).toHaveLength(1);
  });

  it("groups untitled records together rather than with everything else", () => {
    const groups = groupBySubject([
      entry("a", "", "production"),
      entry("b", "", "demo"),
      entry("c", "Monzo", "production"),
    ]);
    expect(groups).toHaveLength(2);
    expect(groups[0]!.variants).toHaveLength(1);
  });

  it("handles an empty portfolio", () => {
    expect(groupBySubject([])).toEqual([]);
  });

  it("tolerates an unparseable timestamp instead of throwing", () => {
    const groups = groupBySubject([
      entry("a", "Monzo", "sandbox", "not-a-date"),
      entry("b", "Monzo", "sandbox", "2026-07-20T00:00:00Z"),
    ]);
    expect(groups).toHaveLength(1);
    expect(groups[0]!.variants).toHaveLength(1);
  });
});
