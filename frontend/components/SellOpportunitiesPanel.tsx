/**
 * "Recommended to sell" (GRS-0162, ADR-0039) — the deterministic answer to "what do I sell against
 * this report?" for a FINALISED assessment. Products whose authored fit addresses this report's
 * assessed-and-weak targets, deepest gap first. The commission carrot is displayed alongside each
 * recommendation but NEVER drives the ordering (ADR-0002) — the ranking is the gap evidence.
 * Advisor-facing only: this list never appears in a client deliverable.
 */

"use client";

import { useEffect, useState } from "react";

import { ApiError, api } from "@/lib/api";
import { toDisplay } from "@/lib/band";
import { formatMoney } from "@/lib/money";
import type { OpportunityGap, SellOpportunities } from "@/lib/types";

function GapChip({ gap }: { gap: OpportunityGap }) {
  const label =
    gap.kind === "power"
      ? `${gap.name} · ${gap.benefit ?? "—"}/${gap.barrier ?? "—"}`
      : gap.q_m != null
        ? `${gap.name} · ${toDisplay(gap.q_m).toFixed(0)} ${gap.gate_band ?? ""}`.trim()
        : `${gap.name} · gate blocked`;
  const title =
    gap.kind === "power"
      ? `${gap.name}: benefit ${gap.benefit ?? "not assessed"}, barrier ${gap.barrier ?? "not assessed"}`
      : gap.q_m != null
        ? `${gap.name}: module score ${toDisplay(gap.q_m).toFixed(1)} (0–100), report band ${gap.gate_band}`
        : `${gap.name}: rating gate blocked (a critical subcomponent is Not Assessed)`;
  return (
    <span className="tag" title={title} style={{ fontSize: "0.66rem" }}>
      {label}
    </span>
  );
}

export function SellOpportunitiesPanel({ assessmentId }: { assessmentId: string }) {
  const [data, setData] = useState<SellOpportunities | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const ctrl = new AbortController();
    api
      .sellOpportunities(assessmentId, ctrl.signal)
      .then(setData)
      .catch((err: unknown) => {
        if (err instanceof ApiError && err.status === 0 && err.aborted) return;
        // 409 = not finalised yet — the panel simply doesn't apply; anything else surfaces.
        if (err instanceof ApiError && err.status === 409) return;
        setError(err instanceof ApiError ? err.message : "Could not load sell opportunities.");
      });
    return () => ctrl.abort();
  }, [assessmentId]);

  if (error) {
    return (
      <div className="card" style={{ padding: "0.9rem 1rem" }}>
        <p className="eyebrow" style={{ margin: 0 }}>
          Recommended to sell
        </p>
        <p role="alert" style={{ margin: "0.4rem 0 0", color: "var(--color-error)", fontSize: "0.8rem" }}>
          {error}
        </p>
      </div>
    );
  }
  if (data === null) return null; // loading, or 409 (not finalised — nothing to show)

  return (
    <div className="card" style={{ padding: "0.9rem 1rem" }}>
      <p className="eyebrow" style={{ margin: 0 }}>
        Recommended to sell
      </p>
      <p style={{ margin: "0.35rem 0 0.6rem", fontSize: "0.75rem", color: "var(--color-ink-muted)" }}>
        Represented products matched to this report&rsquo;s weak areas — deepest gap first. Ranked by
        the gap evidence only; commission shown for information. Advisor-facing, never client-facing.
      </p>
      {data.opportunities.length === 0 ? (
        <p style={{ margin: 0, fontSize: "0.8rem", color: "var(--color-ink-muted)" }}>
          {/* The segment-not-covered note (GRS-0169) beats the generic empty state — an advisor
              must never read "no recommendations" as "no weak areas". */}
          {data.note ??
            "No represented product addresses this report's weak areas — nothing honest to recommend."}
        </p>
      ) : (
        <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: "0.65rem" }}>
          {data.opportunities.map((o) => (
            <li
              key={o.product_id}
              style={{
                border: "1px solid var(--color-border)",
                borderRadius: "var(--radius)",
                padding: "0.6rem 0.75rem",
                background: "var(--color-paper-raised)",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", gap: "0.5rem", alignItems: "baseline", flexWrap: "wrap" }}>
                <strong style={{ fontSize: "0.85rem" }}>{o.name}</strong>
                <span
                  className="mono"
                  title={`Year-1 rate ${(o.carrot.yr1_bps / 100).toFixed(2)}% — e.g. ${formatMoney(o.carrot.yr1_commission)} on a ${formatMoney(o.carrot.example_deal)} deal (schedule ${o.carrot.schedule_version})`}
                  style={{ fontSize: "0.7rem", color: "var(--color-ink-muted)" }}
                >
                  Yr-1 {(o.carrot.yr1_bps / 100).toFixed(1)}% · e.g. {formatMoney(o.carrot.yr1_commission)}
                </span>
              </div>
              <p style={{ margin: "0.3rem 0 0.4rem", fontSize: "0.76rem", color: "var(--color-ink-muted)" }}>
                {o.pitch}
              </p>
              <div style={{ display: "flex", gap: "0.3rem", flexWrap: "wrap" }}>
                {o.gaps.map((g) => (
                  <GapChip key={`${g.kind}:${g.key}`} gap={g} />
                ))}
              </div>
              {o.not_yet_assessed.length > 0 ? (
                <p style={{ margin: "0.35rem 0 0", fontSize: "0.68rem", color: "var(--color-ink-faint)" }}>
                  Not yet assessed (no claim made): {o.not_yet_assessed.join(", ")}
                </p>
              ) : null}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
