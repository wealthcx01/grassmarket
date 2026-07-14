"use client";

/**
 * Certification progress (GRS-0023/0027) — the advisor's own ladder state, the evidence each rung
 * needs, and the audit trail of promotions. Read-only here: promotions are admin-recorded server-side.
 */

import { useCallback, useEffect, useState } from "react";

import { ApiError, api } from "@/lib/api";
import type { AssessorLevelValue, CertificationEvent, CertificationRecord } from "@/lib/types";

const LADDER: AssessorLevelValue[] = ["trained", "shadow", "observed_lead", "certified_lead"];
const LEVEL_LABEL: Record<AssessorLevelValue, string> = {
  trained: "Trained",
  shadow: "Shadow",
  observed_lead: "Observed Lead",
  certified_lead: "Certified Lead",
};

export function CertificationPanel({ advisorId }: { advisorId: string }) {
  const [record, setRecord] = useState<CertificationRecord | null>(null);
  const [events, setEvents] = useState<CertificationEvent[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    async (signal?: AbortSignal) => {
      try {
        const [rec, evs] = await Promise.all([
          api.certification(advisorId, signal),
          api.certificationEvents(advisorId, signal),
        ]);
        setRecord(rec);
        setEvents(evs);
      } catch (err) {
        if (err instanceof ApiError && err.status === 0) return;
        setError(err instanceof ApiError ? err.message : "Could not load certification.");
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
    return <p role="alert" style={{ color: "var(--color-error)", fontSize: "0.9rem" }}>{error}</p>;
  }
  if (record === null) {
    return <p style={{ color: "var(--color-ink-muted)", fontSize: "0.85rem" }}>Loading…</p>;
  }

  const currentIndex = LADDER.indexOf(record.level);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      <section>
        <h3 style={{ fontSize: "1rem", margin: "0 0 0.6rem" }}>The ladder</h3>
        <ol style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
          {LADDER.map((level, i) => {
            const reached = i <= currentIndex;
            return (
              <li
                key={level}
                aria-current={level === record.level ? "step" : undefined}
                style={{
                  padding: "0.4rem 0.8rem",
                  borderRadius: "999px",
                  fontSize: "0.8rem",
                  fontWeight: level === record.level ? 600 : 400,
                  border: "1px solid var(--color-border)",
                  background: reached ? "var(--color-accent)" : "var(--color-paper-raised)",
                  color: reached ? "var(--color-accent-contrast)" : "var(--color-ink-muted)",
                }}
              >
                {LEVEL_LABEL[level]}
              </li>
            );
          })}
        </ol>
      </section>

      <section>
        <h3 style={{ fontSize: "1rem", margin: "0 0 0.6rem" }}>Evidence</h3>
        <dl style={{ margin: 0, display: "grid", gridTemplateColumns: "1fr auto", gap: "0.35rem 1rem", fontSize: "0.85rem", maxWidth: "26rem" }}>
          <dt style={{ color: "var(--color-ink-muted)" }}>Coursework</dt>
          <dd style={{ margin: 0, textAlign: "right" }}>{record.coursework_complete ? "Complete" : "Outstanding"}</dd>
          <dt style={{ color: "var(--color-ink-muted)" }}>Rubric exam</dt>
          <dd style={{ margin: 0, textAlign: "right" }}>
            {record.exam_score == null ? "Not taken" : `${Math.round(record.exam_score * 100)}%`}
          </dd>
          <dt style={{ color: "var(--color-ink-muted)" }}>Shadow assessments</dt>
          <dd style={{ margin: 0, textAlign: "right" }}>{record.shadow_count}</dd>
          <dt style={{ color: "var(--color-ink-muted)" }}>Observed lead</dt>
          <dd style={{ margin: 0, textAlign: "right" }}>{record.observed_lead_logged ? "Logged" : "Pending"}</dd>
        </dl>
        <p style={{ margin: "0.6rem 0 0", fontSize: "0.75rem", color: "var(--color-ink-muted)" }}>
          Promotions and the rubric exam are recorded by an administrator — evidence you can earn
          yourself (coursework) updates here automatically.
        </p>
      </section>

      <section>
        <h3 style={{ fontSize: "1rem", margin: "0 0 0.6rem" }}>History</h3>
        {events && events.length > 0 ? (
          <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: "0.4rem" }}>
            {events.map((e) => (
              <li key={e.id} style={{ fontSize: "0.82rem", display: "flex", gap: "0.6rem" }}>
                <span className="mono" style={{ color: "var(--color-ink-muted)", fontSize: "0.72rem", whiteSpace: "nowrap" }}>
                  {e.occurred_at.slice(0, 10)}
                </span>
                <span>
                  {e.kind.replace(/_/g, " ")}
                  {e.to_level ? ` → ${LEVEL_LABEL[e.to_level]}` : ""}
                  {e.detail ? ` (${e.detail})` : ""}
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <p style={{ color: "var(--color-ink-muted)", fontSize: "0.82rem" }}>No promotions recorded yet.</p>
        )}
      </section>
    </div>
  );
}
