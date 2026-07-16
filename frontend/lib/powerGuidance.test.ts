/**
 * GRS-0069: the guided power-card content must cover exactly the 7 registry powers, and every entry
 * must be non-empty. A new power added to the registry without guidance should fail this test — the
 * wizard falls back gracefully (no example button) but the content gap is caught here.
 */

import { describe, expect, it } from "vitest";

import { POWER_GUIDANCE, powerGuidanceKeys } from "@/lib/powerGuidance";

// The 7 Powers registry keys (stable; mirror of bcap_contracts registry).
const REGISTRY_POWER_KEYS = [
  "SCALE_ECONOMIES",
  "NETWORK_ECONOMIES",
  "COUNTER_POSITIONING",
  "SWITCHING_COSTS",
  "BRANDING",
  "CORNERED_RESOURCE",
  "PROCESS_POWER",
];

describe("POWER_GUIDANCE (GRS-0069)", () => {
  it("covers exactly the 7 registry powers", () => {
    expect([...powerGuidanceKeys].sort()).toEqual([...REGISTRY_POWER_KEYS].sort());
  });

  it("has non-empty benefit/barrier hints and an example for every power", () => {
    for (const key of REGISTRY_POWER_KEYS) {
      const g = POWER_GUIDANCE[key]!;
      expect(g.benefitHint.trim().length).toBeGreaterThan(10);
      expect(g.barrierHint.trim().length).toBeGreaterThan(10);
      expect(g.example.trim().length).toBeGreaterThan(20);
    }
  });
});
