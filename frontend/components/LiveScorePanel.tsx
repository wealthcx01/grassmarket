/**
 * The live-score panel — V/L/B/P and per-module q_m, each rendered through `BandDisplay` so the
 * ADR-0008 honesty flag is honoured (an unmodelled B or P shows a point, never a tight range). It
 * also surfaces the platform BOTTLENECK (the weakest module by q_m — "numbers rank", per the guide)
 * and the full module breakdown, and turns raw blocking/finalise keys into human prose.
 */

import { BandDisplay } from "@/components/BandDisplay";
import { LockedScore } from "@/components/LockedScore";
import { toDisplay } from "@/lib/band";
import { humanizeKey, summarizeBlocking } from "@/lib/labels";
import type { BrokeragePortfolioEntry, IndexBand, LiveScore } from "@/lib/types";

export function LiveScorePanel({
  score,
  loading,
  error,
  onRefresh,
  moduleLabels,
  profileKey,
  clientUsable,
  final,
}: {
  score: LiveScore | null;
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
  moduleLabels?: Record<string, string>;
  profileKey?: string;
  clientUsable?: boolean;
  /** The finalised portfolio row (GRS-0166): when present with a v_index, the headline V is the
   *  LOCKED score (the number the portfolio and deliverable quote), never a live-MC median. The
   *  L/B/P and module diagnostics stay live-derived — deterministic on locked inputs. */
  final?: BrokeragePortfolioEntry | null;
}) {
  return (
    <aside
      className="card"
      style={{ position: "sticky", top: "1rem", padding: "1.1rem 1.15rem" }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: "0.6rem" }}>
        <h3 style={{ margin: 0, fontSize: "1rem" }}>Live score</h3>
        <button type="button" className="btn btn-ghost" onClick={onRefresh} disabled={loading} style={{ padding: "0.25rem 0.6rem", fontSize: "0.78rem" }}>
          {loading ? "…" : "Refresh"}
        </button>
      </div>

      {/* Non-retail profiles score on draft weights (GRS-0152) — the caveat must travel with the
          NUMBER, not live only on the Overview step, so an advisor never quotes a V without it. */}
      <ProvisionalScoreBanner profileKey={profileKey} clientUsable={clientUsable} />

      {error ? (
        <Blocking heading="Score unavailable" blocking={error} tone="error" />
      ) : !score ? (
        <p style={{ color: "var(--color-ink-muted)", fontSize: "0.85rem", margin: 0 }}>
          Enter data to see a live score.
        </p>
      ) : !score.scoreable ? (
        <>
          <Blocking heading="Not yet scoreable" blocking={score.blocking} tone="warn" />
          <Coverage score={score} />
        </>
      ) : (
        <div className="stack" style={{ gap: "0.85rem" }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem 1rem" }}>
            {final?.v_index != null ? (
              <LockedScore entry={final} />
            ) : (
              <BandDisplay label="V — PLATFORM VALUE" band={score.v} point={score.v_point} />
            )}
            {/* The one-number rule (ADR-0040): every headline bolds the deterministic point; the
                band supplies the modelled range only. */}
            <BandDisplay
              label="L — INFRASTRUCTURE · THE TECHNOLOGY LAYER"
              band={score.l_index}
              point={score.l_point}
            />
            <BandDisplay label="B — BUSINESS" band={score.b} point={score.b_point} />
            <BandDisplay label="P — POWER" band={score.p} point={score.p_point} />
          </div>

          <Bottleneck score={score} moduleLabels={moduleLabels} />
          <ModuleBreakdown score={score} moduleLabels={moduleLabels} />

          <div className="hr" />
          <p style={{ margin: 0, fontSize: "0.78rem", color: "var(--color-ink-muted)" }}>
            Assessment uncertainty:{" "}
            <strong style={{ color: "var(--color-ink)" }}>{score.overall_uncertainty ?? "—"}</strong>
          </p>
          <Coverage score={score} />
        </div>
      )}
    </aside>
  );
}

/** The draft-profile caveat, rendered wherever a non-retail SCORE is shown (GRS-0152). Retail scores
 *  on the ratified/elicited set, so it renders nothing there. Kept next to the score, not just on the
 *  Overview step, so a finalised non-retail V is never quoted without its provisional flag. */
export function ProvisionalScoreBanner({
  profileKey,
  clientUsable,
}: {
  profileKey?: string;
  clientUsable?: boolean;
}) {
  // Show the caveat only for a non-retail profile that is NOT client-usable. An activated segment
  // (wealth/exchange, ADR-0037/GRS-0156) is client-usable → no caveat; a future draft profile still
  // carries it. Retail is the default and never shows it.
  if (!profileKey || profileKey === "retail" || clientUsable) return null;
  return (
    <div
      className="callout callout-warn"
      role="note"
      style={{ padding: "0.5rem 0.7rem", marginBottom: "0.7rem", fontSize: "0.74rem", lineHeight: 1.45 }}
    >
      <strong>Indicative — not client-usable.</strong> The {profileKey} operating model scores on{" "}
      <strong>draft</strong> weights and criticals (pending elicitation). Use it to prioritise
      internally; it must not be quoted to a client until the segment weights are ratified.
    </div>
  );
}

function label(key: string, moduleLabels?: Record<string, string>): string {
  return moduleLabels?.[key] ?? humanizeKey(key);
}

/** Modules sorted weakest → strongest by q_m P50 (display scale). */
function sortedModules(score: LiveScore): Array<[string, IndexBand, number]> {
  return Object.entries(score.module_qm)
    .map(([k, band]) => [k, band, toDisplay(band.p50)] as [string, IndexBand, number])
    .sort((a, b) => a[2] - b[2]);
}

function Bottleneck({ score, moduleLabels }: { score: LiveScore; moduleLabels?: Record<string, string> }) {
  const mods = sortedModules(score);
  const weakest = mods[0];
  if (!weakest) return null;
  const [key, , value] = weakest;
  // Below half coverage the weakest module is unreliable — an unassessed module carries a modelled
  // neutral band and can rank weakest just because it hasn't been looked at, so label the callout
  // provisional rather than a confident constraint (GRS-0145).
  const lowCoverage = score.coverage != null && score.coverage < 0.5;
  return (
    <div className="callout callout-warn" style={{ padding: "0.6rem 0.75rem" }}>
      <span className="mono" style={{ fontSize: "0.6rem", letterSpacing: "0.08em", textTransform: "uppercase", opacity: 0.8 }}>
        {lowCoverage ? "Likely constraint · provisional" : "Likely constraint"}
      </span>
      <div style={{ marginTop: "0.15rem", fontSize: "0.9rem", color: "var(--color-ink)" }}>
        <strong>{label(key, moduleLabels)}</strong>{" "}
        <span className="mono" style={{ color: "var(--color-ink-muted)", fontSize: "0.8rem" }}>
          q<sub>m</sub> {value.toFixed(1)}
        </span>
      </div>
      {lowCoverage ? (
        <div style={{ marginTop: "0.3rem", fontSize: "0.7rem", color: "var(--color-ink-muted)" }}>
          Only {Math.round((score.coverage as number) * 100)}% assessed — a module can rank weakest just because it
          isn&rsquo;t assessed yet. Assess more before acting on this.
        </div>
      ) : null}
    </div>
  );
}

function ModuleBreakdown({ score, moduleLabels }: { score: LiveScore; moduleLabels?: Record<string, string> }) {
  const mods = sortedModules(score);
  if (mods.length === 0) return null;
  return (
    <div>
      <p className="mono" style={{ margin: "0 0 0.4rem", fontSize: "0.62rem", letterSpacing: "0.08em", textTransform: "uppercase", color: "var(--color-ink-muted)" }}>
        Modules · weakest first
      </p>
      <ul className="stack" style={{ listStyle: "none", margin: 0, padding: 0, gap: "0.4rem" }}>
        {mods.map(([key, , value], i) => (
          <li key={key} style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: "0.5rem", alignItems: "center" }}>
            <div style={{ minWidth: 0 }}>
              <div style={{ fontSize: "0.8rem", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                {label(key, moduleLabels)}
              </div>
              <div
                aria-hidden
                style={{ height: "4px", borderRadius: "999px", background: "var(--color-paper-sunken)", overflow: "hidden", marginTop: "0.2rem" }}
              >
                <div
                  style={{
                    height: "100%",
                    width: `${Math.max(2, Math.min(100, value))}%`,
                    background: i === 0 ? "var(--color-warn)" : "var(--color-accent)",
                    borderRadius: "999px",
                  }}
                />
              </div>
            </div>
            <span className="mono" style={{ fontSize: "0.78rem", color: "var(--color-ink-muted)", fontVariantNumeric: "tabular-nums" }}>
              {value.toFixed(1)}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function Blocking({
  heading,
  blocking,
  tone,
}: {
  heading: string;
  blocking: string[] | string;
  tone: "warn" | "error";
}) {
  const { headline, reasons } = summarizeBlocking(blocking);
  const color = tone === "error" ? "var(--color-error)" : "var(--color-warn)";
  return (
    <div>
      <p style={{ margin: "0 0 0.4rem", color, fontSize: "0.85rem", fontWeight: 500 }}>{heading}</p>
      {headline ? (
        <p style={{ margin: "0 0 0.4rem", fontSize: "0.83rem", color: "var(--color-ink)" }}>{headline}</p>
      ) : null}
      {reasons.length > 0 ? (
        <ul style={{ margin: 0, paddingLeft: "1.1rem", fontSize: "0.82rem", color: "var(--color-ink)" }}>
          {reasons.map((r) => (
            <li key={r} style={{ marginBottom: "0.15rem" }}>
              {r}
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}

function Coverage({ score }: { score: LiveScore }) {
  const pct = score.coverage != null ? Math.round(score.coverage * 100) : null;
  return (
    <p style={{ margin: 0, fontSize: "0.75rem", color: "var(--color-ink-muted)" }}>
      Coverage: {score.subcomponents_assessed}/{score.subcomponents_total} subcomponents
      {pct != null ? ` (${pct}% of applicable)` : ""}
    </p>
  );
}
