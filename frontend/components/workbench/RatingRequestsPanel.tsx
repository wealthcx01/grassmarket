"use client";

/**
 * Rating requests (Methodology §9, GRS-0062) — the co-rater's work-queue. Lists every module the
 * consultant has been assigned to rate as an independent second opinion, each linking to the blind
 * rating form. This is how a co-rater discovers the ratings requested of them.
 */

import { useEffect, useState } from "react";
import Link from "next/link";

import { ApiError, api } from "@/lib/api";
import type { RatingRequestSummary } from "@/lib/types";

export function RatingRequestsPanel() {
  const [requests, setRequests] = useState<RatingRequestSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const ctrl = new AbortController();
    api
      .myRatingRequests(ctrl.signal)
      .then(setRequests)
      .catch((err: unknown) => {
        if (err instanceof ApiError && err.status === 0) return;
        setError(err instanceof ApiError ? err.message : "Could not load your rating requests.");
      });
    return () => ctrl.abort();
  }, []);

  return (
    <section style={{ display: "flex", flexDirection: "column", gap: "0.8rem" }}>
      <h3 style={{ fontSize: "1rem", margin: 0 }}>Rating requests</h3>
      <p style={{ fontSize: "0.85rem", color: "var(--color-ink-muted)", margin: 0, maxWidth: "42rem" }}>
        Modules a colleague has asked you to rate as an independent second opinion (§9). You rate
        blind — you never see their ratings — then they resolve consensus.
      </p>

      {error ? (
        <p role="alert" style={{ fontSize: "0.85rem", color: "var(--color-error)" }}>{error}</p>
      ) : requests === null ? (
        <p style={{ fontSize: "0.85rem", color: "var(--color-ink-muted)" }}>Loading…</p>
      ) : requests.length === 0 ? (
        <p style={{ fontSize: "0.85rem", color: "var(--color-ink-muted)" }}>
          No rating requests right now.
        </p>
      ) : (
        <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: "0.5rem" }}>
          {requests.map((r) => (
            <li key={`${r.assessment_id}:${r.module_key}`}>
              <Link
                href={`/rate/${r.assessment_id}/${r.module_key}`}
                className="card-link"
                style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "0.5rem", padding: "0.7rem 0.9rem" }}
              >
                <span>
                  <span style={{ fontWeight: 500 }}>{r.module_name}</span>{" "}
                  <span style={{ color: "var(--color-ink-muted)", fontSize: "0.82rem" }}>· {r.subject}</span>
                </span>
                <span
                  className="mono"
                  style={{ fontSize: "0.7rem", whiteSpace: "nowrap", color: r.submitted ? "var(--color-accent)" : "var(--color-warn)" }}
                >
                  {r.submitted ? "submitted" : "rate now →"}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
