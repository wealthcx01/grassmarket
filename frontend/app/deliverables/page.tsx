/**
 * Deliverables index (GRS-0186) — the advisor's own generated deliverables in one place, so a
 * document is reachable from the nav rather than only through a Kanban card slide-over. Owner-scoped
 * on the backend; each row links to its engagement and its client record.
 */

"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { TeachingEmptyState } from "@/components/TeachingEmptyState";

import { ApiError, api, getToken } from "@/lib/api";
import { TYPE_LABEL } from "@/lib/deliverableLabels";
import type { DeliverableIndexRow } from "@/lib/types";

function triggerBlobDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export default function DeliverablesPage() {
  const router = useRouter();
  const [rows, setRows] = useState<DeliverableIndexRow[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState<string | null>(null);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    const ctrl = new AbortController();
    api
      .listAllDeliverables(ctrl.signal)
      .then(setRows)
      .catch((err: unknown) => {
        if (err instanceof ApiError && err.status === 0 && err.aborted) return;
        if (err instanceof ApiError && err.status === 401) return router.replace("/login");
        setError(err instanceof ApiError ? err.message : "Could not load your deliverables.");
      });
    return () => ctrl.abort();
  }, [router]);

  async function onDownload(row: DeliverableIndexRow) {
    setDownloading(row.id);
    setError(null);
    try {
      const { blob, filename } = await api.downloadDeliverable(row.id, {
        clientFacing: row.mode === "client",
      });
      triggerBlobDownload(blob, filename);
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : "Could not download the deliverable.");
    } finally {
      setDownloading(null);
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
      <section>
        <p className="eyebrow" style={{ margin: 0 }}>
          Advisor · your deliverables
        </p>
        <h1 style={{ fontSize: "2rem", margin: "0.3rem 0 0" }}>Deliverables</h1>
        <p style={{ margin: "0.4rem 0 0", color: "var(--color-ink-muted)", maxWidth: "42rem" }}>
          Every deliverable you have generated, newest first. Each row opens its engagement, and the
          company name opens the full client record.
        </p>
      </section>

      {error ? (
        <p role="alert" style={{ color: "var(--color-error)", fontSize: "0.9rem" }}>
          {error}
        </p>
      ) : null}

      {rows === null ? (
        <p style={{ color: "var(--color-ink-muted)" }}>Loading…</p>
      ) : rows.length === 0 ? (
        /* GRS-0243 scope 4. Written first, then extracted into `TeachingEmptyState` so the three
           other sections say their piece the same way instead of each inventing a shape. */
        <TeachingEmptyState
          testId="deliverables-empty"
          headline="Nothing here yet — deliverables are produced, not created."
          explanation={
            <>
              A deliverable comes out of a scored assessment, so the chain runs:{" "}
              <strong>assessment → finalise → engagement → deliverable → client report</strong>.
              Each step needs the one before it, which is why this page stays empty until an
              assessment is finalised and attached to an engagement.
            </>
          }
          action={{
            href: "/portfolio",
            label: "Start an assessment",
            rest: (
              <>
                {" "}
                to begin the chain, or open one of the worked examples on a demo brokerage to see a
                finished client report before you build one.
              </>
            ),
          }}
        />
      ) : (
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.88rem" }}>
            <thead>
              <tr style={{ textAlign: "left", color: "var(--color-ink-muted)", fontSize: "0.78rem" }}>
                <th style={{ padding: "0.4rem 0.6rem", fontWeight: 600 }}>Subject / Engagement</th>
                <th style={{ padding: "0.4rem 0.6rem", fontWeight: 600 }}>Type</th>
                <th style={{ padding: "0.4rem 0.6rem", fontWeight: 600 }}>Audience</th>
                <th style={{ padding: "0.4rem 0.6rem", fontWeight: 600 }}>Generated</th>
                <th style={{ padding: "0.4rem 0.6rem", fontWeight: 600 }}></th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.id} style={{ borderTop: "1px solid var(--color-border)" }}>
                  <td style={{ padding: "0.55rem 0.6rem" }}>
                    <Link
                      href={`/engagements/${row.engagement_id}`}
                      style={{ fontWeight: 600, color: "inherit", textDecoration: "none" }}
                    >
                      {row.engagement_title}
                    </Link>
                    <div style={{ fontSize: "0.78rem", marginTop: "0.1rem" }}>
                      <Link
                        href={`/prospects/${row.prospect_id}`}
                        style={{ color: "var(--color-ink-muted)" }}
                      >
                        {row.prospect_company_name}
                      </Link>
                    </div>
                  </td>
                  <td style={{ padding: "0.55rem 0.6rem" }}>{TYPE_LABEL[row.type]}</td>
                  <td style={{ padding: "0.55rem 0.6rem" }}>
                    <span className="tag" style={{ fontSize: "0.66rem" }}>
                      {row.mode === "client" ? "Client" : "Draft"}
                    </span>
                  </td>
                  <td
                    className="mono"
                    style={{ padding: "0.55rem 0.6rem", fontSize: "0.78rem", color: "var(--color-ink-muted)" }}
                  >
                    {row.generated_at ? new Date(row.generated_at).toLocaleDateString() : "—"}
                  </td>
                  <td style={{ padding: "0.55rem 0.6rem" }}>
                    <div style={{ display: "flex", gap: "0.4rem", justifyContent: "flex-end" }}>
                      {/* The client report (GRS-0219/0220): where the advisor writes the narrative,
                          renders the branded PDF and issues the client's link. */}
                      <Link
                        href={`/deliverables/${row.id}/report`}
                        className="btn btn-secondary"
                        style={{ padding: "0.3rem 0.7rem", fontSize: "0.8rem" }}
                      >
                        Client report
                      </Link>
                      <button
                        type="button"
                        className="btn btn-secondary"
                        style={{ padding: "0.3rem 0.7rem", fontSize: "0.8rem" }}
                        disabled={downloading === row.id}
                        onClick={() => onDownload(row)}
                      >
                        {downloading === row.id ? "Preparing…" : "Download"}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <footer style={{ fontSize: "0.8rem", color: "var(--color-ink-muted)" }}>
        <Link href="/">← Back to dashboard</Link>
      </footer>
    </div>
  );
}
