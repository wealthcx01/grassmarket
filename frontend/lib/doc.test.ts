/**
 * GRS-0068: the business-profile document helpers. `setProfile` must create the profile when absent,
 * merge partial patches, and never disturb the scoring inputs (subcomponents / metrics / powers).
 * `parseList` must trim and drop empties so a trailing comma doesn't create a blank asset class.
 */

import { describe, expect, it } from "vitest";

import { emptyDoc, parseList, setProfile, subAssessed, setSub } from "@/lib/doc";

describe("setProfile (GRS-0068)", () => {
  it("creates the profile when the document has none", () => {
    const d = setProfile(emptyDoc("Acme"), { country: "United Kingdom" });
    expect(d.profile?.country).toBe("United Kingdom");
    expect(d.profile?.asset_classes).toEqual([]);
    expect(d.subject).toBe("Acme");
  });

  it("merges partial patches without clobbering other fields", () => {
    let d = setProfile(emptyDoc(), { segment: "Retail broker" });
    d = setProfile(d, { regions: ["UK", "EU"] });
    expect(d.profile?.segment).toBe("Retail broker");
    expect(d.profile?.regions).toEqual(["UK", "EU"]);
  });

  it("never disturbs the scoring inputs", () => {
    let d = setSub(emptyDoc(), "FRONTEND_PERFORMANCE", subAssessed("FRONTEND", "FRONTEND_PERFORMANCE", "Advanced", "E2"));
    d = setProfile(d, { country: "US" });
    expect(d.subcomponents).toHaveLength(1);
    expect(d.subcomponents[0]!.level).toBe("Advanced");
  });
});

describe("parseList (GRS-0068)", () => {
  it("trims, splits, and drops empties", () => {
    expect(parseList("equities, funds ,, FX,")).toEqual(["equities", "funds", "FX"]);
    expect(parseList("")).toEqual([]);
    expect(parseList("  ")).toEqual([]);
  });
});
