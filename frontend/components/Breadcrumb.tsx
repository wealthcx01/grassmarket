/**
 * Shared breadcrumb / back-link (GRS-0118). One component so every detail screen shows its place in
 * the flow (Pipeline → Prospect → Engagement → Assessment) and always has a reliable way back, instead
 * of ad-hoc per-screen "← X" links that left users dead-ending. `trail` is the ancestor links (each
 * clickable); `current` is the page you're on (not a link).
 */

import Link from "next/link";

export interface Crumb {
  label: string;
  href: string;
}

export function Breadcrumb({ trail, current }: { trail: readonly Crumb[]; current: string }) {
  return (
    <nav
      aria-label="Breadcrumb"
      style={{
        display: "flex",
        flexWrap: "wrap",
        alignItems: "center",
        gap: "0.4rem",
        fontSize: "0.82rem",
        color: "var(--color-ink-soft)",
      }}
    >
      {trail.map((c) => (
        <span key={c.href} style={{ display: "inline-flex", alignItems: "center", gap: "0.4rem" }}>
          <Link href={c.href} style={{ color: "var(--color-ink-muted)" }}>
            {c.label}
          </Link>
          <span aria-hidden style={{ color: "var(--color-ink-faint)" }}>
            /
          </span>
        </span>
      ))}
      <span aria-current="page" style={{ color: "var(--color-ink)", fontWeight: 500 }}>
        {current}
      </span>
    </nav>
  );
}
