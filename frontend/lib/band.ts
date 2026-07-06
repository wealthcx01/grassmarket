/**
 * Honest band rendering (§7 / ADR-0008) — the guarantee that must NOT be lost at the view layer.
 *
 * A band with `modelled = false` is a POINT ESTIMATE: the uncertainty was not modelled, so it MUST
 * be shown as a single point labelled "uncertainty not modelled", never as a (falsely confident)
 * tight range. `describeBand` is the single decision point; every renderer goes through it, and it
 * is unit-tested (band.test.tsx).
 */

import type { IndexBand } from "@/lib/types";

export const NOT_MODELLED_LABEL = "uncertainty not modelled";

export type BandView =
  | { mode: "point"; value: number; label: string }
  | { mode: "range"; low: number; mid: number; high: number };

/** Scale a stored [0,1] index to the 0–100 display convention (ADR-0001 §4). */
export function toDisplay(x: number): number {
  return Math.round(x * 1000) / 10; // one decimal place on the 0–100 scale
}

export function describeBand(band: IndexBand | null | undefined): BandView | null {
  if (!band) return null;
  if (!band.modelled) {
    // Unmodelled → a point, explicitly labelled. NEVER a range.
    return { mode: "point", value: band.p50, label: NOT_MODELLED_LABEL };
  }
  return { mode: "range", low: band.p10, mid: band.p50, high: band.p90 };
}

/** A short human string for a band, honouring the modelled flag. */
export function formatBand(band: IndexBand | null | undefined): string {
  const view = describeBand(band);
  if (!view) return "—";
  if (view.mode === "point") {
    return `${toDisplay(view.value).toFixed(1)} (point · ${view.label})`;
  }
  return `${toDisplay(view.mid).toFixed(1)} (range ${toDisplay(view.low).toFixed(1)}–${toDisplay(
    view.high,
  ).toFixed(1)})`;
}
