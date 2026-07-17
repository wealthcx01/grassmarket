"use client";

/**
 * Bench-time dashboard (GRS-0026/0027) — the advisor's landing state when no engagement is active:
 * the prioritised next-action queue, and their own development metrics. All data is JWT-scoped and
 * self-only server-side; this just renders it.
 */

import { useCallback, useEffect, useState } from "react";

import { ApiError, api } from "@/lib/api";
import type { BenchQueue, PerformanceSummary } from "@/lib/types";

const KIND_LABEL: Record<string, string> = {
  rating_request: "Rating request",
  committee: "Committee review",
  certification: "Certification",
  academy: "Academy",
  drill: "Power drill",
  arena: "Practice arena",
  research: "Opportunity Radar",
};

export function BenchDashboard({ advisorId }: { advisorId: string }) {
  const [queue, setQueue] = useState<BenchQueue | null>(null);
  const [perf, setPerf] = useState<PerformanceSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    async (signal?: AbortSignal) => {
      try {
        const [q, p] = await Promise.all([
          api.benchQueue(signal),
          api.performance(advisorId, signal),
        ]);
        setQueue(q);
        setPerf(p);
      } catch (err) {
        if (err instanceof ApiError && err.status === 0) return;
        setError(err instanceof ApiError ? err.message : "Could not load the bench dashboard.");
      }
    },
    [advisorId],
  );

  useEffect(() => {
    const ctrl = new AbortController();
    void load(ctrl.signal);
    return () => ctrl.abort();
  }, [load]);

  if (error) {
    return (
      <p role="alert" style={{ color: "var(--color-error)", fontSize: "0.9rem" }}>
        {error}
      </p>
    );
  }

  return (
    <div style={{ display: "grid", gap: "1.5rem", gridTemplateColumns: "minmax(0, 1.3fr) minmax(0, 1fr)" }}>
      <section>
        <h3 style={{ fontSize: "1rem", margin: "0 0 0.6rem" }}>Your next actions</h3>
        {queue === null ? (
          <p style={{ color: "var(--color-ink-muted)", fontSize: "0.85rem" }}>Loading…</p>
        ) : (
          <ol style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: "0.6rem" }}>
            {queue.items.map((item) => (
              <li
                key={`${item.kind}-${item.priority}`}
                style={{
                  padding: "0.8rem 0.9rem",
                  border: "1px solid var(--color-border)",
                  borderRadius: "var(--radius)",
                  background: "var(--color-paper-raised)",
                  display: "flex",
                  gap: "0.8rem",
                  alignItems: "baseline",
                }}
              >
                <span
                  className="mono"
                  aria-hidden
                  style={{ fontSize: "0.8rem", color: "var(--color-accent)", fontWeight: 600 }}
                >
                  {item.priority}
                </span>
                <div>
                  <div style={{ display: "flex", gap: "0.5rem", alignItems: "baseline" }}>
                    <strong style={{ fontSize: "0.9rem" }}>{item.title}</strong>
                    <span className="mono" style={{ fontSize: "0.6rem", color: "var(--color-ink-muted)", textTransform: "uppercase" }}>
                      {KIND_LABEL[item.kind] ?? item.kind}
                    </span>
                  </div>
                  <p style={{ margin: "0.25rem 0 0", fontSize: "0.82rem", color: "var(--color-ink-muted)" }}>
                    {item.detail}
                  </p>
                </div>
              </li>
            ))}
          </ol>
        )}
      </section>

      <section>
        <h3 style={{ fontSize: "1rem", margin: "0 0 0.6rem" }}>My performance</h3>
        {perf === null ? (
          <p style={{ color: "var(--color-ink-muted)", fontSize: "0.85rem" }}>Loading…</p>
        ) : (
          <dl style={{ margin: 0, display: "grid", gridTemplateColumns: "1fr auto", gap: "0.35rem 1rem", fontSize: "0.85rem" }}>
            <Metric label="Level" value={perf.level.replace(/_/g, " ")} />
            <Metric label="Engagements active" value={String(perf.engagements_active)} />
            <Metric label="Engagements completed" value={String(perf.engagements_completed)} />
            <Metric label="Pipeline conversion" value={`${Math.round(perf.pipeline_conversion_rate * 100)}%`} />
            <Metric label="Coursework" value={perf.coursework_complete ? "Complete" : "Outstanding"} />
            <Metric label="Exam" value={perf.exam_passed ? "Passed" : "Not passed"} />
            <Metric label="Drills due" value={String(perf.drills_due)} />
            <Metric label="Best drill streak" value={String(perf.drill_best_streak)} />
            <Metric label="Arena sessions scored" value={String(perf.arena_sessions_scored)} />
            <Metric
              label="Best arena completeness"
              value={
                perf.arena_best_completeness == null
                  ? "—"
                  : `${Math.round(perf.arena_best_completeness * 100)}%`
              }
            />
          </dl>
        )}
      </section>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <>
      <dt style={{ color: "var(--color-ink-muted)" }}>{label}</dt>
      <dd style={{ margin: 0, textAlign: "right", fontWeight: 500 }}>{value}</dd>
    </>
  );
}
