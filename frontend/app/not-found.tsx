import Link from "next/link";

/**
 * Global 404 (GRS-0143). A cold user who mistypes a URL, follows a stale link, or opens a record that
 * doesn't exist should land on a way back — not a bare Next.js 404 with no navigation (stress-test
 * finding). Rendered inside the app shell (header + main from layout.tsx), so this is just the body.
 */

const LINKS: { href: string; label: string; hint: string }[] = [
  { href: "/", label: "Dashboard", hint: "Your home for the advisor studio" },
  { href: "/pipeline", label: "Pipeline", hint: "Prospects, workshops, and stages" },
  { href: "/assessments", label: "Your Portfolio", hint: "Assessments and the Platform Power wizard" },
  { href: "/engagements", label: "Engagements", hint: "Client work and deliverables" },
  { href: "/workbench", label: "Workbench", hint: "Certification, Academy, and practice" },
];

export default function NotFound() {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem", maxWidth: "40rem" }}>
      <div>
        <p
          className="mono"
          style={{
            margin: 0,
            fontSize: "0.72rem",
            letterSpacing: "0.1em",
            textTransform: "uppercase",
            color: "var(--color-ink-muted)",
          }}
        >
          404 · page not found
        </p>
        <h1 style={{ fontSize: "2rem", margin: "0.3rem 0 0.4rem" }}>We couldn&apos;t find that page</h1>
        <p style={{ margin: 0, color: "var(--color-ink-muted)", fontSize: "0.95rem" }}>
          The address may be mistyped, the link may be out of date, or the record may no longer exist.
          Here&apos;s where you can pick up.
        </p>
      </div>

      <ul
        style={{
          listStyle: "none",
          padding: 0,
          margin: 0,
          display: "flex",
          flexDirection: "column",
          gap: "0.5rem",
        }}
      >
        {LINKS.map((l) => (
          <li key={l.href}>
            <Link
              href={l.href}
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "baseline",
                gap: "0.75rem",
                padding: "0.7rem 0.9rem",
                border: "1px solid var(--color-border)",
                borderRadius: "var(--radius)",
                background: "var(--color-paper-raised)",
                textDecoration: "none",
                color: "inherit",
              }}
            >
              <span style={{ fontFamily: "var(--font-serif)", fontWeight: 600 }}>{l.label}</span>
              <span style={{ fontSize: "0.75rem", color: "var(--color-ink-muted)" }}>{l.hint}</span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
