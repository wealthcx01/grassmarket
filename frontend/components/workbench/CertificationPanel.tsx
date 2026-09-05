"use client";

/**
 * Certification progress (GRS-0023/0027) — the advisor's own ladder state, the evidence each rung
 * needs, and the audit trail of promotions. Read-only here: promotions are admin-recorded server-side.
 */

import { useCallback, useEffect, useState } from "react";

import { LevelProvenanceNote } from "@/components/workbench/LevelBadge";
import { LEVEL_LABEL } from "@/lib/levels";
import { ApiError, api } from "@/lib/api";
import type {
  AssessorLevelValue,
  CertificationEvent,
  CertificationRecord,
  CourseCertification,
  CourseCertificationStatus,
} from "@/lib/types";

const COURSE_CERT_LABEL: Record<CourseCertificationStatus, string> = {
  not_started: "Not started",
  in_progress: "Course done · awaiting sign-off",
  certified: "Certified",
};
const COURSE_CERT_COLOR: Record<CourseCertificationStatus, string> = {
  not_started: "var(--color-ink-muted)",
  in_progress: "var(--color-warn)",
  certified: "var(--color-accent)",
};

const LADDER: AssessorLevelValue[] = ["trained", "shadow", "observed_lead", "certified_lead"];

export function CertificationPanel({ advisorId }: { advisorId: string }) {
  const [record, setRecord] = useState<CertificationRecord | null>(null);
  const [events, setEvents] = useState<CertificationEvent[] | null>(null);
  const [courseCerts, setCourseCerts] = useState<CourseCertification[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    async (signal?: AbortSignal) => {
      try {
        const [rec, evs, certs] = await Promise.all([
          api.certification(advisorId, signal),
          api.certificationEvents(advisorId, signal),
          api.courseCertifications(signal),
        ]);
        setRecord(rec);
        setEvents(evs);
        setCourseCerts(certs);
      } catch (err) {
        if (err instanceof ApiError && err.status === 0 && err.aborted) return;
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
  // Rungs the EVIDENCE supports, which is not the same as rungs the advisor is marked at. Filling
  // the ladder to `currentIndex` drew every rung as achieved, so the picture still said "earned"
  // while the note underneath said "granted" — the contradiction this ticket exists to remove.
  const earnedIndex = LADDER.indexOf(record.earned_level);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      <section>
        <h3 style={{ fontSize: "1rem", margin: "0 0 0.6rem" }}>The ladder</h3>
        <ol
          data-testid="certification-ladder"
          style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", gap: "0.5rem", flexWrap: "wrap" }}
        >
          {LADDER.map((level, i) => {
            const earned = i <= earnedIndex;
            // Held but not earned: at or below the marked level, above what the evidence supports.
            const granted = !earned && i <= currentIndex;
            return (
              <li
                key={level}
                aria-current={level === record.level ? "step" : undefined}
                data-state={earned ? "earned" : granted ? "granted" : "unreached"}
                title={
                  granted
                    ? "Held, but the ladder evidence on record does not support it."
                    : undefined
                }
                style={{
                  padding: "0.4rem 0.8rem",
                  borderRadius: "999px",
                  fontSize: "0.8rem",
                  fontWeight: level === record.level ? 600 : 400,
                  // A granted rung is outlined in amber rather than filled: visibly held, visibly
                  // not the same thing as a rung that was climbed.
                  border: `1px ${granted ? "dashed" : "solid"} ${
                    granted ? "var(--color-warn)" : "var(--color-border)"
                  }`,
                  background: earned ? "var(--color-accent)" : "var(--color-paper-raised)",
                  color: earned
                    ? "var(--color-accent-contrast)"
                    : granted
                      ? "var(--color-warn)"
                      : "var(--color-ink-muted)",
                }}
              >
                {LEVEL_LABEL[level]}
              </li>
            );
          })}
        </ol>
        {/* The reconciliation, said in words directly under the ladder it contradicts. Without it
            the reader sees a level highlighted on a ladder whose rungs are all empty and has to
            guess which screen is lying (GRS-0242 scope 3). */}
        <LevelProvenanceNote
          level={record.level}
          earnedLevel={record.earned_level}
          isEvidenced={record.level_is_evidenced}
        />
      </section>

      {courseCerts.length > 0 ? (
        <section>
          <h3 style={{ fontSize: "1rem", margin: "0 0 0.6rem" }}>Course &amp; product certifications</h3>
          <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: "0.4rem", maxWidth: "30rem" }}>
            {courseCerts.map((c) => (
              <li
                key={c.subject}
                style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "0.75rem", padding: "0.5rem 0.7rem", border: "1px solid var(--color-border)", borderRadius: "var(--radius)", background: "var(--color-paper-raised)", fontSize: "0.85rem" }}
              >
                <span>{c.title}</span>
                <span className="mono" style={{ fontSize: "0.72rem", color: COURSE_CERT_COLOR[c.status] }}>
                  {COURSE_CERT_LABEL[c.status]}
                </span>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

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
