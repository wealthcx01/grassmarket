/**
 * Earnings incentive layer (GRS-0133): a cumulative-earnings chart, the two v7 stream split, and
 * light gamification (milestone ladder + a "close this to earn £X" nudge).
 *
 * Every £ figure is a `Money` the Earnings v7 kernel computed — the timeline is aggregated
 * server-side, the carrot rates come from the schedule. The client only PLOTS and COMPARES; it never
 * derives a new pound figure (ADR-0002). Milestone thresholds are display constants, not business
 * figures.
 */

"use client";

import { MoneyAmount } from "@/components/MoneyAmount";
import type { EarningsSummary, EarningsTimeline, ProductCommissionCarrot } from "@/lib/types";

// The gamification ladder — display-only milestones (pence). Not computed from any commission rate.
const MILESTONES_MINOR = [
  500_000, 1_000_000, 2_500_000, 5_000_000, 10_000_000, 25_000_000, 50_000_000, 100_000_000,
];

function nextMilestone(ytdMinor: number): number {
  return MILESTONES_MINOR.find((m) => m > ytdMinor) ?? MILESTONES_MINOR[MILESTONES_MINOR.length - 1]!;
}

function CumulativeChart({ timeline }: { timeline: EarningsTimeline }) {
  const pts = timeline.points;
  if (pts.length === 0) return null;

  const W = 640;
  const H = 180;
  const PAD = 8;
  const maxMinor = Math.max(...pts.map((p) => p.cumulative.amount_minor), 1);
  // Map a point to chart coordinates (rendering math only — never a new £ figure).
  const x = (i: number) => (pts.length === 1 ? W / 2 : PAD + (i * (W - 2 * PAD)) / (pts.length - 1));
  const y = (minor: number) => H - PAD - (minor / maxMinor) * (H - 2 * PAD);

  const line = pts.map((p, i) => `${i === 0 ? "M" : "L"} ${x(i).toFixed(1)} ${y(p.cumulative.amount_minor).toFixed(1)}`).join(" ");
  const area = `${line} L ${x(pts.length - 1).toFixed(1)} ${H - PAD} L ${x(0).toFixed(1)} ${H - PAD} Z`;
  const first = pts[0]!;
  const last = pts[pts.length - 1]!;

  return (
    <div style={{ overflowX: "auto" }}>
      <svg
        viewBox={`0 0 ${W} ${H}`}
        role="img"
        aria-label="Cumulative earnings over time"
        style={{ width: "100%", minWidth: "20rem", height: "auto", display: "block" }}
      >
        <path d={area} fill="var(--color-accent)" opacity={0.12} />
        <path d={line} fill="none" stroke="var(--color-accent)" strokeWidth={2} strokeLinejoin="round" />
        {pts.map((p, i) => (
          <circle key={p.period} cx={x(i)} cy={y(p.cumulative.amount_minor)} r={i === pts.length - 1 ? 4 : 2.5} fill="var(--color-accent)" />
        ))}
        <text x={x(pts.length - 1)} y={y(last.cumulative.amount_minor) - 8} textAnchor="end" fontSize="11" fill="var(--color-ink-muted)" className="mono">
          {last.period}
        </text>
      </svg>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.68rem", color: "var(--color-ink-faint)" }} className="mono">
        <span>{first.period}</span>
        <span>{last.period}</span>
      </div>
    </div>
  );
}

function StreamSplit({ timeline }: { timeline: EarningsTimeline }) {
  const a = timeline.stream_product.amount_minor;
  const b = timeline.stream_consultancy.amount_minor;
  const total = a + b;
  if (total === 0) return null;
  const pctA = Math.round((a / total) * 100);
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem" }}>
      <div aria-hidden style={{ display: "flex", height: "0.5rem", borderRadius: "var(--radius-pill)", overflow: "hidden", background: "var(--color-border)" }}>
        <span style={{ width: `${pctA}%`, background: "var(--color-accent)" }} />
        <span style={{ width: `${100 - pctA}%`, background: "var(--color-ink-muted)" }} />
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.78rem", color: "var(--color-ink-muted)" }}>
        <span>
          <span style={{ color: "var(--color-accent)" }}>●</span> Product (Stream A){" "}
          <MoneyAmount money={timeline.stream_product} />
        </span>
        <span>
          <span style={{ color: "var(--color-ink-muted)" }}>●</span> Consultancy (Stream B){" "}
          <MoneyAmount money={timeline.stream_consultancy} />
        </span>
      </div>
    </div>
  );
}

export function EarningsProgress({
  summary,
  timeline,
  carrots,
}: {
  summary: EarningsSummary;
  timeline: EarningsTimeline;
  carrots: ProductCommissionCarrot[];
}) {
  const ytd = summary.ytd_earned.amount_minor;
  const target = nextMilestone(ytd);
  const pct = Math.min(100, Math.round((ytd / target) * 100)); // a ratio, not a new £ figure
  const targetMoney = { ...summary.ytd_earned, amount_minor: target, assumption_register_ref: "gamify:milestone" };
  const achieved = MILESTONES_MINOR.filter((m) => ytd >= m).length;
  // The richest year-one carrot is the sharpest "next close" nudge.
  const bestCarrot = carrots.slice().sort((x, y) => y.yr1_commission.amount_minor - x.yr1_commission.amount_minor)[0];

  const hasChart = timeline.points.length > 0;

  return (
    <section style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
      <h2 style={{ fontSize: "1.05rem", margin: 0 }}>Your earnings journey</h2>

      {hasChart ? (
        <div className="card" style={{ padding: "1rem 1.15rem", display: "flex", flexDirection: "column", gap: "0.9rem" }}>
          <CumulativeChart timeline={timeline} />
          <StreamSplit timeline={timeline} />
        </div>
      ) : (
        <p style={{ color: "var(--color-ink-muted)", fontSize: "0.9rem" }}>
          Your earnings chart appears here as commission lines are recorded.
        </p>
      )}

      <div style={{ display: "grid", gap: "0.75rem", gridTemplateColumns: "repeat(auto-fit, minmax(15rem, 1fr))" }}>
        {/* Milestone progress */}
        <div className="card" style={{ padding: "0.9rem 1rem", display: "flex", flexDirection: "column", gap: "0.5rem" }}>
          <p className="mono" style={{ margin: 0, fontSize: "0.62rem", letterSpacing: "0.08em", textTransform: "uppercase", color: "var(--color-ink-muted)" }}>
            Next milestone · {achieved} reached
          </p>
          <div aria-hidden style={{ height: "0.5rem", borderRadius: "var(--radius-pill)", background: "var(--color-border)", overflow: "hidden" }}>
            <span style={{ display: "block", height: "100%", width: `${pct}%`, background: "var(--color-accent)" }} />
          </div>
          <p style={{ margin: 0, fontSize: "0.85rem" }}>
            <strong>{pct}%</strong> of the way to <MoneyAmount money={targetMoney} /> earned
          </p>
        </div>

        {/* Forward "you could earn £X" nudge */}
        {bestCarrot ? (
          <div className="card" style={{ padding: "0.9rem 1rem", display: "flex", flexDirection: "column", gap: "0.35rem" }}>
            <p className="mono" style={{ margin: 0, fontSize: "0.62rem", letterSpacing: "0.08em", textTransform: "uppercase", color: "var(--color-ink-muted)" }}>
              Close this next
            </p>
            <p style={{ margin: 0, fontSize: "0.9rem", lineHeight: 1.5 }}>
              Sell <strong>{bestCarrot.name}</strong> and earn{" "}
              <strong style={{ color: "var(--color-accent)" }}>
                <MoneyAmount money={bestCarrot.yr1_commission} />
              </strong>{" "}
              in year one <span style={{ color: "var(--color-ink-faint)" }}>(illustrative deal)</span>.
            </p>
          </div>
        ) : null}
      </div>
    </section>
  );
}
