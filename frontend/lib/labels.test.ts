/**
 * GRS-0046: humanizeKeysInText must humanize real registry keys but leave ordinary uppercase text
 * (currency pairs, A/B, TCP/IP) untouched, and never leak a raw UUID.
 */

import { describe, expect, it } from "vitest";

import { humanizeKey, humanizeKeysInText, summarizeBlocking } from "@/lib/labels";

describe("humanizeKey", () => {
  it("humanizes snake_case and MODULE/SUBCOMPONENT keys", () => {
    expect(humanizeKey("BACK_OFFICE")).toBe("Back Office");
    expect(humanizeKey("CORNERED_RESOURCE")).toBe("Cornered Resource");
    expect(humanizeKey("MARKET_DATA/MARKET_DATA_DEPTH_QUALITY")).toBe("Market Data · Depth Quality");
  });
});

describe("humanizeKeysInText (GRS-0046)", () => {
  it("humanizes real registry keys embedded in prose", () => {
    expect(humanizeKeysInText("BACK_OFFICE is solo-rated")).toBe("Back Office is solo-rated");
    expect(humanizeKeysInText("Fix FRONTEND/FRONTEND_PERFORMANCE next")).toContain("·");
  });

  it("leaves ordinary uppercase text (no underscore) untouched", () => {
    expect(humanizeKeysInText("EUR/USD exposure is unhedged")).toBe("EUR/USD exposure is unhedged");
    expect(humanizeKeysInText("Run an A/B test")).toBe("Run an A/B test");
    expect(humanizeKeysInText("TCP/IP latency")).toBe("TCP/IP latency");
    expect(humanizeKeysInText("Q1/Q2 revenue dip")).toBe("Q1/Q2 revenue dip");
  });

  it("redacts a raw UUID", () => {
    const out = humanizeKeysInText("assessment 550e8400-e29b-41d4-a716-446655440000 is solo-rated");
    expect(out).not.toContain("550e8400");
    expect(out).toContain("solo-rated");
  });
});

describe("summarizeBlocking is unaffected by ordinary text", () => {
  it("keeps a currency-pair reason readable", () => {
    const { reasons } = summarizeBlocking(["EUR/USD exposure needs review."]);
    expect(reasons[0]).toBe("EUR/USD exposure needs review.");
  });
});
