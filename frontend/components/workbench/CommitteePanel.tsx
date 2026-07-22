"use client";

/**
 * Rating Committee (GRS-0021/0027/0061) — members-only. Lists the assessments across the network that
 * still have high-stakes ratings awaiting sign-off (the reviewer's work-queue), each linking to the
 * committee review page. Role-gated: the Workbench only mounts it for a committee member or admin,
 * mirroring the server gate (a non-member's queue/decide call is a 403).
 */

import { useEffect, useState } from "react";
import Link from "next/link";

import { ApiError, api } from "@/lib/api";
import type { CommitteeReviewSummary } from "@/lib/types";

export function CommitteePanel() {
  const [queue, setQueue] = useState<CommitteeReviewSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const ctrl = new AbortController();
    api
      .committeeReviewQueue(ctrl.signal)
      .then(setQueue)
      .catch((err: unknown) => {
        if (err instanceof ApiError && err.status === 0 && err.aborted) return;
        setError(err instanceof ApiError ? err.message : "Could not load the committee queue.");
      });
    return () => ctrl.abort();
  }, []);

  return (
    <section style={{ display: "flex", flexDirection: "column", gap: "0.8rem" }}>
      <h3 style={{ fontSize: "1rem", margin: 0 }}>Rating committee</h3>
      <p style={{ fontSize: "0.85rem", color: "var(--color-ink-muted)", margin: 0, maxWidth: "42rem" }}>
        High-stakes ratings (a module gated Frontier, a power Established+, or a triad dimension above
        None) need peer sign-off before an assessment can finalise (§8). Open one to record your
        approve / reject decision — you can never decide on your own assessment (peer challenge).
      </p>

      {error ? (
        <p role="alert" style={{ fontSize: "0.85rem", color: "var(--color-error)" }}>{error}</p>
      ) : queue === null ? (
        <p style={{ fontSize: "0.85rem", color: "var(--color-ink-muted)" }}>Loading the queue…</p>
      ) : queue.length === 0 ? (
        <p style={{ fontSize: "0.85rem", color: "var(--color-ink-muted)" }}>
          Nothing awaiting sign-off right now.
        </p>
      ) : (
        <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: "0.5rem" }}>
          {queue.map((q) => (
            <li key={q.assessment_id}>
              <Link
                href={`/committee/${q.assessment_id}`}
                className="card-link"
                style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "0.5rem", padding: "0.7rem 0.9rem" }}
              >
                <span style={{ fontWeight: 500 }}>{q.subject}</span>
                <span
                  className="mono"
                  style={{ fontSize: "0.7rem", color: "var(--color-warn)", whiteSpace: "nowrap" }}
                >
                  {q.pending_count} awaiting sign-off →
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
