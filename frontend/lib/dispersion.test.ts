/**
 * Module dispersion (GRS-0227).
 *
 * The headline test is the ticket's own acceptance: two firms with the SAME V and very different
 * module spreads must not read the same. Everything else here guards the ways that could be true on
 * paper and wrong in practice — an unassessed module sneaking into the range, a single-module
 * assessment dividing by nothing, a flat firm rendering an empty state.
 */

import { describe, expect, it } from "vitest";

import { RUBRIC_STEP, dispersionSentence, moduleDispersion } from "./dispersion";
import type { IndexBand, LiveScore } from "./types";

const BAND: IndexBand = { p10: 0.4, p50: 0.5, p90: 0.6, modelled: true };

function score(points: Record<string, number>, over: Partial<LiveScore> = {}): LiveScore {
  return {
    scoreable: true,
    blocking: [],
    v_point: 0.57,
    module_qm: Object.fromEntries(Object.keys(points).map((k) => [k, BAND])),
    module_qm_point: points,
    module_weights: {},
    subcomponents_assessed: 9,
    subcomponents_total: 9,
    engine_version: "test",
    methodology_version: "test",
    coefficient_version: "test",
    uncertainty_version: "test",
    ...over,
  } as LiveScore;
}

describe("moduleDispersion", () => {
  it("distinguishes two firms with the SAME score and different spreads", () => {
    // The whole reason the ticket exists. Both average 0.5; one is flat, one is broken in one place.
    const flat = moduleDispersion(score({ a: 0.5, b: 0.5, c: 0.5 }));
    const lumpy = moduleDispersion(score({ a: 0.2, b: 0.5, c: 0.8 }));

    expect(flat).not.toBeNull();
    expect(lumpy).not.toBeNull();
    expect(flat!.spread).toBe(0);
    expect(lumpy!.spread).toBeCloseTo(0.6);
    expect(flat!.uneven).toBe(false);
    expect(lumpy!.uneven).toBe(true);

    // And they must SAY different things, not merely hold different numbers.
    expect(dispersionSentence(flat!, "Frontend")).not.toEqual(
      dispersionSentence(lumpy!, "Frontend"),
    );
  });

  it("names the weakest module, because that is what an advisor scopes against", () => {
    const d = moduleDispersion(score({ frontend: 0.8, ledger: 0.2, custody: 0.5 }));
    expect(d!.weakestKey).toBe("ledger");
    expect(d!.low).toBeCloseTo(0.2);
    expect(d!.high).toBeCloseTo(0.8);
    expect(dispersionSentence(d!, "Ledger")).toContain("Ledger");
  });

  it("takes the range over assessed modules only (D9)", () => {
    // `module_qm_point` carries only modules that scored, so an unassessed module is absent — not
    // zero, not a neutral default. The range must therefore ignore it entirely, exactly as L does.
    const withUnassessed = score(
      { a: 0.5, b: 0.8 },
      // The MC bands include a modelled neutral for the unassessed module; the range must not read it.
      { module_qm: { a: BAND, b: BAND, unassessed: BAND } },
    );
    const d = moduleDispersion(withUnassessed);
    expect(d!.assessed).toBe(2);
    expect(d!.low).toBeCloseTo(0.5);
  });

  it("reports a flat firm as a spread of zero without an empty state", () => {
    const d = moduleDispersion(score({ a: 0.5, b: 0.5 }));
    expect(d!.spread).toBe(0);
    expect(d!.low).toBe(d!.high);
    expect(dispersionSentence(d!, "Frontend")).toContain("identically");
  });

  it("does not divide by anything when a single module has scored", () => {
    const d = moduleDispersion(score({ a: 0.5 }));
    expect(d!.assessed).toBe(1);
    expect(d!.spread).toBe(0);
    expect(Number.isFinite(d!.spread)).toBe(true);
    // And it says so rather than claiming the firm is even.
    expect(dispersionSentence(d!, "Frontend")).toContain("one module");
  });

  it("returns null when there is nothing to report", () => {
    expect(moduleDispersion(null)).toBeNull();
    expect(moduleDispersion(score({}, { scoreable: false }))).toBeNull();
    expect(moduleDispersion(score({}))).toBeNull();
  });

  it("threshold is one full rubric step, not an invented percentile", () => {
    // MaturityLevel.score_index sits at 0.2/0.5/0.8/1.0 — the widest adjacent step is 0.3.
    expect(RUBRIC_STEP).toBeCloseTo(0.3);
    // Exactly one step apart counts as uneven; a hair under does not.
    expect(moduleDispersion(score({ a: 0.5, b: 0.5 + RUBRIC_STEP }))!.uneven).toBe(true);
    expect(moduleDispersion(score({ a: 0.5, b: 0.5 + RUBRIC_STEP - 0.001 }))!.uneven).toBe(false);
  });
});

describe("dispersionSentence", () => {
  it("never emits a rating word for the spread itself", () => {
    // GRS-0223 declined to add a scored dimension without a methodology version, and so does this.
    // A "High dispersion" label would be exactly that arriving through the back door.
    const cases = [
      moduleDispersion(score({ a: 0.2, b: 0.8 }))!,
      moduleDispersion(score({ a: 0.5, b: 0.5 }))!,
      moduleDispersion(score({ a: 0.45, b: 0.55 }))!,
      moduleDispersion(score({ a: 0.5 }))!,
    ];
    for (const d of cases) {
      const text = dispersionSentence(d, "Frontend").toLowerCase();
      for (const banned of ["high dispersion", "low dispersion", "medium dispersion", "rated"]) {
        expect(text).not.toContain(banned);
      }
      // It is prose an advisor can read aloud, not a scale reading.
      expect(text.length).toBeGreaterThan(60);
    }
  });

  it("tells an uneven firm it has a weak spot and an even firm the opposite", () => {
    const uneven = dispersionSentence(moduleDispersion(score({ a: 0.2, b: 0.8 }))!, "Ledger");
    const even = dispersionSentence(moduleDispersion(score({ a: 0.45, b: 0.55 }))!, "Ledger");
    expect(uneven).toContain("weak spot");
    expect(even).toContain("evenly built");
    expect(even).not.toContain("specific weak spot");
  });
});
