/**
 * Shared record breadcrumb (GRS-0186): Pipeline › {Company} › {this record}. Puts the client's full
 * record (workshops, engagements, stage history) one click from any surface that names the client,
 * so movement between the engagement page and the prospect page never routes through the dashboard.
 */

import Link from "next/link";

export function RecordBreadcrumb({
  prospectId,
  companyName,
  current,
}: {
  prospectId: string;
  companyName: string;
  /** The label for the record currently open (e.g. the engagement title, or "Client record"). */
  current: string;
}) {
  const sep = (
    <span aria-hidden style={{ color: "var(--color-ink-faint)" }}>
      ›
    </span>
  );
  return (
    <nav
      aria-label="Record breadcrumb"
      style={{
        display: "flex",
        flexWrap: "wrap",
        gap: "0.4rem",
        alignItems: "center",
        fontSize: "0.8rem",
        color: "var(--color-ink-muted)",
      }}
    >
      <Link href="/pipeline" style={{ color: "var(--color-ink-muted)" }}>
        Pipeline
      </Link>
      {sep}
      <Link href={`/prospects/${prospectId}`} style={{ color: "var(--color-ink-muted)" }}>
        {companyName}
      </Link>
      {sep}
      <span style={{ color: "var(--color-ink)" }}>{current}</span>
    </nav>
  );
}
