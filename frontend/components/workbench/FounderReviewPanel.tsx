"use client";

/**
 * Founder review (GRS-0188, ADR-0041) — everything waiting on the founder's signature.
 *
 * An approval names the version of the document it cleared. Approve here and the advisor can
 * finalise and generate a client pack; if they then edit anything, the approval stops matching and
 * the record comes back to this list marked as a re-read. That is why there is no "withdraw"
 * button: there is nothing to withdraw, only a newer version to look at.
 *
 * The panel is mounted only when the server answers the queue, so the gate is the API's and not a
 * second copy of the founder's identity baked into the frontend build.
 */

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";

import { ApiError, api } from "@/lib/api";
import type { FounderReviewQueueEntry } from "@/lib/types";

export function FounderReviewPanel() {
  const [queue, setQueue] = useState<FounderReviewQueueEntry[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  const load = useCallback((signal?: AbortSignal) => {
    return api
      .founderReviewQueue(signal)
      .then(setQueue)
      .catch((err: unknown) => {
        if (err instanceof ApiError && err.status === 0 && err.aborted) return;
        setError(err instanceof ApiError ? err.message : "Could not load the review queue.");
      });
  }, []);

  useEffect(() => {
    const ctrl = new AbortController();
    void load(ctrl.signal);
    return () => ctrl.abort();
  }, [load]);

  async function approve(entry: FounderReviewQueueEntry) {
    setBusy(entry.assessment_id);
    setError(null);
    try {
      await api.approveCurrentVersion(entry.assessment_id);
      await load();
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : "Could not record the approval.");
    } finally {
      setBusy(null);
    }
  }

  return (
    <section style={{ display: "flex", flexDirection: "column", gap: "0.8rem" }}>
      <h3 style={{ fontSize: "1rem", margin: 0 }}>Founder review</h3>
      <p
        style={{
          fontSize: "0.85rem",
          color: "var(--color-ink-muted)",
          margin: 0,
          maxWidth: "42rem",
        }}
      >
        Every assessment that is going to a client comes through here first. Approving signs off the
        document exactly as it stands now. If the advisor changes anything afterwards, the approval
        no longer applies and the record returns to this list, so you are never signing a version
        you have not read.
      </p>

      {error && (
        <p role="alert" style={{ fontSize: "0.85rem", color: "var(--color-danger, #a3312a)" }}>
          {error}
        </p>
      )}

      {queue === null && !error && (
        <p style={{ fontSize: "0.9rem", color: "var(--color-ink-muted)" }}>Loading…</p>
      )}

      {queue !== null && queue.length === 0 && (
        <p style={{ fontSize: "0.9rem", color: "var(--color-ink-muted)" }}>
          Nothing is waiting on you.
        </p>
      )}

      {queue !== null && queue.length > 0 && (
        <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "grid", gap: "0.6rem" }}>
          {queue.map((entry) => (
            <li
              key={entry.assessment_id}
              style={{
                border: "1px solid var(--color-rule)",
                borderRadius: "0.4rem",
                padding: "0.8rem 1rem",
                display: "flex",
                flexWrap: "wrap",
                gap: "0.8rem",
                alignItems: "center",
                justifyContent: "space-between",
              }}
            >
              <div style={{ display: "flex", flexDirection: "column", gap: "0.2rem" }}>
                <Link href={`/assessments/${entry.assessment_id}`} style={{ fontWeight: 600 }}>
                  {entry.subject || "Untitled assessment"}
                </Link>
                <span style={{ fontSize: "0.8rem", color: "var(--color-ink-muted)" }}>
                  {entry.advisor_name} · submitted{" "}
                  {new Date(entry.requested_at).toLocaleDateString()}
                  {entry.previously_approved && " · changed since you approved it"}
                </span>
              </div>
              <button
                type="button"
                onClick={() => void approve(entry)}
                disabled={busy === entry.assessment_id}
              >
                {busy === entry.assessment_id ? "Approving…" : "Approve this version"}
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
