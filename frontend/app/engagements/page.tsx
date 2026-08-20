/**
 * Engagements index (GRS-0014) — the consultant's own engagements (server-scoped). Read-only list;
 * engagements are opened from a contracted prospect's detail page.
 */

"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

import { ProvenanceBadge } from "@/components/ProvenanceBadge";

import { NotFoundNotice } from "@/components/NotFoundNotice";
import { ApiError, api, getToken } from "@/lib/api";
import type { Engagement } from "@/lib/types";

export default function EngagementsPage() {
  const router = useRouter();
  const [items, setItems] = useState<Engagement[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    const ctrl = new AbortController();
    api
      .listEngagements(ctrl.signal)
      .then(setItems)
      .catch((err: unknown) => {
        if (err instanceof ApiError && err.status === 0 && err.aborted) return;
        if (err instanceof ApiError && err.status === 401) return router.replace("/login");
        setError(err instanceof ApiError ? err.message : "Could not load engagements.");
      });
    return () => ctrl.abort();
  }, [router]);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem", maxWidth: "42rem" }}>
      <NotFoundNotice noun="engagement" />
      <div>
        <Link href="/pipeline" style={{ fontSize: "0.8rem" }}>
          ← Pipeline
        </Link>
        <h1 style={{ fontSize: "2rem", margin: "0.2rem 0 0" }}>Engagements</h1>
      </div>

      {error ? <p style={{ color: "var(--color-error)" }}>{error}</p> : null}

      {items === null ? (
        <p style={{ color: "var(--color-ink-muted)" }}>Loading…</p>
      ) : items.length === 0 ? (
        <p style={{ color: "var(--color-ink-muted)" }}>
          No engagements yet. Open one from a contracted prospect.
        </p>
      ) : (
        <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: "0.5rem" }}>
          {items.map((e) => (
            <li key={e.id}>
              <Link
                href={`/engagements/${e.id}`}
                style={{ display: "flex", justifyContent: "space-between", padding: "0.7rem 0.9rem", border: "1px solid var(--color-border)", borderRadius: "var(--radius)", background: "var(--color-paper-raised)", textDecoration: "none", color: "inherit" }}
              >
                {/* GRS-0241 scopes 1 and 3. The badge is the portfolio's own component, so a demo
                    engagement is labelled the same way a demo assessment is — the founder saw
                    duplicate demo rows here twice and nothing distinguished them from real work.
                    "comms" was internal shorthand, and a count of zero communications on every row
                    is metadata with no information in it, so it is spelled out and hidden at 0. */}
                <span style={{ fontFamily: "var(--font-serif)", fontWeight: 600, display: "flex", gap: "0.5rem", alignItems: "baseline", flexWrap: "wrap" }}>
                  {e.title}
                  <ProvenanceBadge provenance={e.provenance} />
                </span>
                <span className="mono" style={{ fontSize: "0.72rem", color: "var(--color-ink-muted)" }}>
                  {e.status}
                  {e.comms_log.length
                    ? ` · ${e.comms_log.length} ${e.comms_log.length === 1 ? "communication" : "communications"}`
                    : ""}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
