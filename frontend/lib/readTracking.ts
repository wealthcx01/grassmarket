/**
 * Turning recorded read events into something an advisor can act on (GRS-0235).
 *
 * The pipeline already records per-section dwell, capped and batched with real care, and the
 * summary endpoint already returns views, total dwell, and first/last-viewed timestamps per
 * section. None of it was displayed: the deliverable page showed internal section keys joined by
 * commas, and dropped the rest. So this module is presentation only — it adds no measurement and
 * changes nothing about what is recorded (GRS-0220's narrow-by-construction rules stand).
 *
 * The governing idea is that dwell is **soft evidence**. It cannot distinguish reading from a tab
 * left open, and it under-counts a client who prints the PDF and reads that instead. Everything
 * here is therefore shaped to inform without inviting over-reading: coarse rounding so nobody
 * compares 47s against 52s, an explicit marker when a figure has hit the six-hour cap, and a
 * caption stating both limits wherever the numbers appear.
 */

/** The API's own ceiling on a single event (`dwell_ms` is `le=6h` in the contract). */
export const MAX_DWELL_MS = 6 * 60 * 60 * 1000;

/** Coarse on purpose: 10s buckets inform without inviting 47s-versus-52s comparisons. */
const ROUND_TO_MS = 10_000;

/**
 * Total dwell for a section, rounded coarsely and phrased as an approximation.
 *
 * Anything under one bucket reads "under 10s" rather than rounding to 0s — a section that was
 * opened is not a section that was not, and "0s" beside a view count of 1 reads as a bug.
 */
export function formatDwell(totalMs: number): string {
  if (totalMs <= 0) return "—";
  if (totalMs < ROUND_TO_MS) return "under 10s";

  const rounded = Math.round(totalMs / ROUND_TO_MS) * ROUND_TO_MS;
  const seconds = Math.round(rounded / 1000);
  if (seconds < 60) return `${seconds}s`;

  const minutes = Math.floor(seconds / 60);
  const remainder = seconds % 60;
  if (minutes < 60) return remainder ? `${minutes}m ${remainder}s` : `${minutes}m`;

  const hours = Math.floor(minutes / 60);
  const leftoverMinutes = minutes % 60;
  return leftoverMinutes ? `${hours}h ${leftoverMinutes}m` : `${hours}h`;
}

/**
 * Whether a section's total has reached the per-event ceiling.
 *
 * Worth flagging separately because a capped figure is the one case where the number is known to be
 * wrong rather than merely imprecise, and an advisor reading "6h" without that context would draw
 * the opposite conclusion from the true one.
 */
export function isAtCap(totalMs: number): boolean {
  return totalMs >= MAX_DWELL_MS;
}

/**
 * A read timestamp in the advisor's own locale, to the minute.
 *
 * To the minute rather than the second because the events are batched — a seconds-precise time
 * would be precision the pipeline does not actually have.
 */
export function formatReadMoment(iso: string | null | undefined): string | null {
  if (!iso) return null;
  const when = new Date(iso);
  if (Number.isNaN(when.getTime())) return null;
  return when.toLocaleString(undefined, {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/** One section's read state, as the table renders it. */
export interface SectionReadRow {
  section: string;
  views: number;
  total_dwell_ms: number;
  first_viewed_at?: string | null;
  last_viewed_at?: string | null;
}

/**
 * First and last moment the recipient opened anything, across all sections.
 *
 * Computed here rather than taken from a single section because a client rarely reads in order:
 * the first section opened is not necessarily `business`, and the last is not necessarily
 * `appendix`.
 */
export function readWindow(sections: readonly SectionReadRow[]): {
  first: string | null;
  last: string | null;
} {
  const firsts = sections.map((s) => s.first_viewed_at).filter((v): v is string => Boolean(v));
  const lasts = sections.map((s) => s.last_viewed_at).filter((v): v is string => Boolean(v));
  return {
    first: firsts.length ? firsts.reduce((a, b) => (a < b ? a : b)) : null,
    last: lasts.length ? lasts.reduce((a, b) => (a > b ? a : b)) : null,
  };
}
