/**
 * Module dispersion (GRS-0227) — how uneven a firm is, reported beside its score.
 *
 * GRS-0223 measured why every assessment scores about the same and found the engine innocent: V
 * averages nine modules, seven powers and four metrics, so a firm strong in some places and weak in
 * others is pulled to the middle by construction. Every real firm is a mixed bag, so every real firm
 * lands near the middle. The three showcase firms span 0.058 of V — and 0.45 to 0.60 of module q_m.
 *
 * The scores are not wrong. The report was throwing away the thing that makes them different. A V of
 * 0.57 built from modules spanning 0.20–0.80 is a *different firm* from a V of 0.57 built from
 * modules all at 0.55, and until this module existed both displayed identically.
 *
 * Nothing here is new maths. Every number is a `q_m` the engine already computed; this file only
 * takes their range. It deliberately does NOT produce a band, a label or a rating — no
 * "high/medium/low dispersion" — because that would be a new scored dimension arriving without a
 * methodology version, which is exactly what GRS-0223 declined to do. What it produces is a range
 * and a sentence.
 */

import type { LiveScore } from "./types";

/**
 * One full step of the maturity rubric.
 *
 * `MaturityLevel.score_index` places the four levels at 0.2 / 0.5 / 0.8 / 1.0, so the widest step
 * between adjacent levels is 0.3. That is the threshold used below, and it is the reason the
 * threshold is not an invented percentile: below one full step, every module sits within a single
 * rubric level of every other and calling the firm uneven would be reading noise. At or above it,
 * modules are genuinely at different maturity levels — a fact about the firm, not about the scale.
 */
export const RUBRIC_STEP = 0.3;

export interface ModuleDispersion {
  /** Lowest scoring assessed module. */
  low: number;
  /** Highest scoring assessed module. */
  high: number;
  /** `high - low`. Zero when every assessed module scored the same. */
  spread: number;
  /** Registry key of the weakest assessed module — the one an advisor scopes against. */
  weakestKey: string;
  /** How many modules the range is taken over. One module is a range of zero, honestly. */
  assessed: number;
  /**
   * Whether the modules sit more than one full rubric step apart. Used ONLY to choose the wording
   * and the ordering of the summary bullets — never rendered as a label. See RUBRIC_STEP.
   */
  uneven: boolean;
}

/**
 * The range of the assessed modules' deterministic q_m, or null when there is nothing to report.
 *
 * Reads `module_qm_point`, which the engine populates only for modules that actually scored, so a
 * Not Assessed module contributes nothing to the range exactly as it contributes nothing to L (D9).
 * No fallback to the Monte Carlo bands: their P50 is never the quoted number (ADR-0040), and an
 * unassessed module carries a modelled neutral band that would land in the range as if it had been
 * looked at.
 */
export function moduleDispersion(live: LiveScore | null): ModuleDispersion | null {
  if (!live || !live.scoreable) return null;
  const entries = Object.entries(live.module_qm_point ?? {});
  if (entries.length === 0) return null;

  const [firstKey, firstValue] = entries[0] as [string, number];
  let low = firstValue;
  let high = firstValue;
  let weakestKey = firstKey;
  for (const [key, value] of entries) {
    if (value < low) {
      low = value;
      weakestKey = key;
    }
    if (value > high) high = value;
  }
  const spread = high - low;
  return { low, high, spread, weakestKey, assessed: entries.length, uneven: spread >= RUBRIC_STEP };
}

/**
 * What the range means, in one line — the deliverable of GRS-0227 as much as the figure is.
 *
 * Two sentences, not a scale: an uneven firm is told it has a specific weak spot rather than an
 * average business, and an even one is told the opposite. The module is named because that is what
 * an advisor scopes against; the number is not repeated here, because the bottleneck bullet beside
 * this one already quotes it and two numbers for one quantity is how a report loses an audit.
 */
export function dispersionSentence(d: ModuleDispersion, moduleLabel: string): string {
  if (d.assessed < 2) {
    return `Only one module has scored, so there is no spread to read yet. Assess more before treating this score as a picture of the whole firm.`;
  }
  if (d.spread === 0) {
    return `Every assessed module scored identically. There is no weak spot to attack — this score describes the level of the whole firm, and lifting it means lifting everything.`;
  }
  if (d.uneven) {
    return `This is an uneven business with a specific weak spot, not an average one. ${moduleLabel} is a long way below the rest, so the headline score understates what is strong here and overstates what is broken — scope against the weak module, not the average.`;
  }
  return `This is an evenly built business rather than one with a single weak spot. No module is more than a rubric level from the others, so there is no quick fix that moves the headline — improvement means lifting the whole firm.`;
}
