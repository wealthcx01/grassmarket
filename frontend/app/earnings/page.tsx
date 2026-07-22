/**
 * My Earnings (GRS-0028 frontend) — the advisor's self-service commission view. Shows the YTD /
 * pending / invoiced / paid summary, the individual commission lines, and a downloadable statement.
 * Everything is principal-scoped on the backend; the client only carries the JWT. Amounts come
 * straight from the API as `Money` and are display-formatted only — never arithmetic (ADR-0002).
 */

"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

import { MoneyAmount } from "@/components/MoneyAmount";
import { ApiError, api, getToken } from "@/lib/api";
import { EarningsProgress } from "@/components/EarningsProgress";
import type {
  CommissionKind,
  CommissionLine,
  EarningsSummary,
  EarningsTimeline,
  PaymentStatus,
  ProductCommissionCarrot,
} from "@/lib/types";

const KIND_LABELS: Record<CommissionKind, string> = {
  engagement: "Engagement",
  workshop_recovery_fee: "Workshop recovery fee",
  retainer: "Retainer",
};

const STATUS_LABELS: Record<PaymentStatus, string> = {
  pending: "Pending",
  invoiced: "Invoiced",
  paid: "Paid",
};

// Muted → accent as a line advances toward paid; a plain visual cue, not a computed value.
const STATUS_COLOR: Record<PaymentStatus, string> = {
  pending: "var(--color-ink-muted)",
  invoiced: "var(--color-ink)",
  paid: "var(--color-accent)",
};

function humanize(value: string | null | undefined): string {
  if (!value) return "—";
  return value.charAt(0).toUpperCase() + value.slice(1).replace(/_/g, " ");
}

// What a commission line is attributed to (GRS-0163): the sourcing for a consultancy line, else the
// represented product's name for a product sale (so the column is never a bare "—" when there's a
// product), falling back to the product id.
function attributionLabel(line: CommissionLine, carrots: ProductCommissionCarrot[]): string {
  if (line.attribution) return humanize(line.attribution);
  if (line.product_id) {
    return carrots.find((c) => c.product_id === line.product_id)?.name ?? humanize(line.product_id);
  }
  return "—";
}

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

export default function EarningsPage() {
  const router = useRouter();
  const [summary, setSummary] = useState<EarningsSummary | null>(null);
  const [lines, setLines] = useState<CommissionLine[] | null>(null);
  const [carrots, setCarrots] = useState<ProductCommissionCarrot[]>([]);
  const [timeline, setTimeline] = useState<EarningsTimeline | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState(false);

  const reload = useCallback((signal?: AbortSignal) => {
    return Promise.all([
      api.earningsSummary(signal),
      api.listCommissions(signal),
      api.productCommissions(signal),
      api.earningsTimeline(signal),
    ])
      .then(([s, l, c, t]) => {
        setSummary(s);
        setLines(l);
        setCarrots(c);
        setTimeline(t);
      })
      .catch((err: unknown) => {
        if (err instanceof ApiError && err.status === 0 && err.aborted) return;
        setError(err instanceof ApiError ? err.message : "Could not load your earnings.");
      });
  }, []);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    const ctrl = new AbortController();
    reload(ctrl.signal);
    return () => ctrl.abort();
  }, [router, reload]);

  async function onDownloadStatement() {
    setDownloading(true);
    try {
      const { blob, filename } = await api.downloadEarningsStatement();
      triggerBlobDownload(blob, filename);
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : "Could not download the statement.");
    } finally {
      setDownloading(false);
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
      <section
        style={{
          display: "flex",
          alignItems: "flex-start",
          justifyContent: "space-between",
          gap: "1rem",
          flexWrap: "wrap",
        }}
      >
        <div>
          <p
            className="mono"
            style={{ margin: 0, fontSize: "0.72rem", letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--color-ink-muted)" }}
          >
            Advisor · your earnings
          </p>
          <h1 style={{ fontSize: "2rem", margin: "0.3rem 0 0" }}>My Earnings</h1>
        </div>
        <button
          type="button"
          onClick={onDownloadStatement}
          disabled={downloading || !summary}
          style={{
            padding: "0.5rem 1.1rem",
            fontSize: "0.9rem",
            color: "var(--color-accent-contrast)",
            background: "var(--color-accent)",
            border: "none",
            borderRadius: "var(--radius)",
            cursor: downloading || !summary ? "not-allowed" : "pointer",
            opacity: downloading || !summary ? 0.6 : 1,
          }}
        >
          {downloading ? "Preparing…" : "Download statement (.docx)"}
        </button>
      </section>

      {error ? (
        <p role="alert" style={{ color: "var(--color-error)", fontSize: "0.9rem" }}>
          {error}
        </p>
      ) : null}

      {summary ? (
        <ul
          style={{
            listStyle: "none",
            margin: 0,
            padding: 0,
            display: "grid",
            gap: "0.75rem",
            gridTemplateColumns: "repeat(auto-fill, minmax(11rem, 1fr))",
          }}
        >
          {(
            [
              { label: "Earned YTD", money: summary.ytd_earned },
              { label: "Pending", money: summary.pending },
              { label: "Invoiced", money: summary.invoiced },
              { label: "Paid", money: summary.paid },
              { label: "Projected unpaid", money: summary.projected_unpaid },
            ] as const
          ).map((stat) => (
            <li
              key={stat.label}
              style={{
                padding: "0.9rem 1rem",
                background: "var(--color-paper-raised)",
                border: "1px solid var(--color-border)",
                borderRadius: "var(--radius)",
              }}
            >
              <p
                className="mono"
                style={{ margin: 0, fontSize: "0.62rem", letterSpacing: "0.08em", textTransform: "uppercase", color: "var(--color-ink-muted)" }}
              >
                {stat.label}
              </p>
              <p style={{ margin: "0.35rem 0 0", fontSize: "1.25rem" }}>
                <MoneyAmount money={stat.money} />
              </p>
            </li>
          ))}
        </ul>
      ) : null}

      {summary && timeline ? (
        <EarningsProgress summary={summary} timeline={timeline} carrots={carrots} />
      ) : null}

      {carrots.length > 0 ? (
        <section>
          <h2 style={{ fontSize: "1rem", margin: "0 0 0.6rem" }}>Product commissions</h2>
          <p style={{ margin: "0 0 0.75rem", color: "var(--color-ink-muted)", fontSize: "0.82rem", maxWidth: "42rem" }}>
            What you earn for selling each represented product — read live from the Earnings schedule
            (never a typed-in number). The £ figures price an illustrative first-year deal.
          </p>
          <ul
            style={{
              listStyle: "none",
              margin: 0,
              padding: 0,
              display: "grid",
              gap: "0.75rem",
              gridTemplateColumns: "repeat(auto-fill, minmax(14rem, 1fr))",
            }}
          >
            {carrots.map((c) => (
              <li
                key={c.product_id}
                style={{ padding: "0.9rem 1rem", background: "var(--color-paper-raised)", border: "1px solid var(--color-border)", borderRadius: "var(--radius)" }}
              >
                <p style={{ margin: 0, fontWeight: 600, fontSize: "0.92rem" }}>{c.name}</p>
                <p className="mono" style={{ margin: "0.35rem 0 0", fontSize: "0.78rem", color: "var(--color-accent)" }}>
                  {c.yr1_bps / 100}% yr1 · {c.yr2_bps / 100}% yr2
                </p>
                <p style={{ margin: "0.35rem 0 0", fontSize: "0.8rem", color: "var(--color-ink-muted)" }}>
                  e.g. <MoneyAmount money={c.yr1_commission} /> then <MoneyAmount money={c.yr2_commission} />
                </p>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {lines === null ? (
        <p>Loading…</p>
      ) : lines.length === 0 ? (
        <p style={{ color: "var(--color-ink-muted)", fontSize: "0.9rem" }}>
          No commission lines yet — they appear here as engagements and workshop recovery fees are
          recorded.
        </p>
      ) : (
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.88rem" }}>
            <thead>
              <tr style={{ textAlign: "left", color: "var(--color-ink-muted)" }}>
                {["Kind", "Amount", "Status", "Earned", "Attribution"].map((h) => (
                  <th
                    key={h}
                    className="mono"
                    style={{ padding: "0.5rem 0.6rem", fontSize: "0.66rem", letterSpacing: "0.06em", textTransform: "uppercase", borderBottom: "1px solid var(--color-border)", fontWeight: 500 }}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {lines.map((line) => (
                <tr key={line.id} style={{ borderBottom: "1px solid var(--color-border)" }}>
                  <td style={{ padding: "0.55rem 0.6rem" }}>{KIND_LABELS[line.kind]}</td>
                  <td style={{ padding: "0.55rem 0.6rem" }}>
                    <MoneyAmount money={line.amount} />
                  </td>
                  <td style={{ padding: "0.55rem 0.6rem", color: STATUS_COLOR[line.payment_status] }}>
                    {STATUS_LABELS[line.payment_status]}
                  </td>
                  <td style={{ padding: "0.55rem 0.6rem", color: "var(--color-ink-muted)" }}>
                    {line.earned_on ?? "—"}
                  </td>
                  <td style={{ padding: "0.55rem 0.6rem", color: "var(--color-ink-muted)" }}>
                    {attributionLabel(line, carrots)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <footer style={{ fontSize: "0.8rem", color: "var(--color-ink-muted)" }}>
        <Link href="/">← Dashboard</Link> · <Link href="/engagements">Engagements</Link>
      </footer>
    </div>
  );
}
