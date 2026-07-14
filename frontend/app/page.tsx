import Link from "next/link";
import { HealthWidget } from "./health-widget";

// PRD §1 / §4–7 — the advisor's main sections. `href: null` = built on the backend but
// no dedicated page yet, so the tile renders as a non-clickable "coming soon" card rather
// than a dead link.
const SECTIONS: ReadonlyArray<{ title: string; href: string | null; blurb: string }> = [
  {
    title: "Pipeline",
    href: "/pipeline",
    blurb: "Prospects, workshops, and kanban stages with time-in-stage flags.",
  },
  {
    title: "Assessments",
    href: "/assessments",
    blurb: "ATLAS engine, the 7-step wizard, and live scores with uncertainty bands.",
  },
  {
    title: "Deliverables",
    href: "/engagements",
    blurb: "Diagnostic packs, heatmaps, and the modernisation roadmap — per engagement.",
  },
  {
    title: "Workbench",
    href: "/workbench",
    blurb: "Certification ladder, practice arena, power drills, bench queue.",
  },
  {
    title: "My Earnings",
    href: null,
    blurb: "Commission breakdown, recovery fees, YTD and projections.",
  },
];

export default function DashboardPage() {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "2.5rem" }}>
      <section
        style={{
          display: "flex",
          alignItems: "flex-start",
          justifyContent: "space-between",
          gap: "1.5rem",
          flexWrap: "wrap",
        }}
      >
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
            Advisor dashboard
          </p>
          <h1 style={{ fontSize: "2rem", margin: "0.3rem 0 0.4rem" }}>
            Bruntsfield Advisor Studio
          </h1>
          <p style={{ margin: 0, color: "var(--color-ink-muted)", maxWidth: "38rem" }}>
            The advisor platform of the Bruntsfield Advisory Network — pipeline management,
            ATLAS assessments, client deliverables, and the Workbench. Sign in to your
            engagements, or jump to a section below.
          </p>
        </div>
        <HealthWidget />
      </section>

      <section>
        <h2 style={{ fontSize: "1.05rem", marginBottom: "1rem" }}>Sections</h2>
        <ul
          style={{
            listStyle: "none",
            margin: 0,
            padding: 0,
            display: "grid",
            gap: "1rem",
            gridTemplateColumns: "repeat(auto-fill, minmax(16rem, 1fr))",
          }}
        >
          {SECTIONS.map((s) => {
            const cardStyle = {
              display: "block",
              height: "100%",
              padding: "1.1rem 1.2rem",
              background: "var(--color-paper-raised)",
              border: "1px solid var(--color-border)",
              borderRadius: "var(--radius)",
              textDecoration: "none",
              color: "inherit",
            } as const;
            const inner = (
              <>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "baseline",
                    gap: "0.5rem",
                  }}
                >
                  <span
                    style={{
                      fontFamily: "var(--font-serif)",
                      fontWeight: 600,
                      fontSize: "1.1rem",
                    }}
                  >
                    {s.title}
                  </span>
                  {s.href === null && (
                    <span
                      className="mono"
                      style={{ fontSize: "0.62rem", color: "var(--color-ink-muted)" }}
                    >
                      Coming soon
                    </span>
                  )}
                </div>
                <p
                  style={{
                    margin: "0.4rem 0 0",
                    fontSize: "0.86rem",
                    color: "var(--color-ink-muted)",
                  }}
                >
                  {s.blurb}
                </p>
              </>
            );
            return (
              <li key={s.title}>
                {s.href === null ? (
                  <div style={{ ...cardStyle, opacity: 0.55, cursor: "default" }}>{inner}</div>
                ) : (
                  <Link href={s.href} style={cardStyle}>
                    {inner}
                  </Link>
                )}
              </li>
            );
          })}
        </ul>
      </section>

      <footer style={{ fontSize: "0.8rem", color: "var(--color-ink-muted)" }}>
        Not signed in?{" "}
        <Link href="/login" style={{ fontWeight: 500 }}>
          Go to sign in
        </Link>
      </footer>
    </div>
  );
}
