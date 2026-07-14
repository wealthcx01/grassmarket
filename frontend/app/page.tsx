import Link from "next/link";
import { HealthWidget } from "./health-widget";

// PRD §1 / §4–7 — the advisor's main sections. Placeholders until the loops land.
const SECTIONS: ReadonlyArray<{ title: string; href: string; blurb: string; loop: string }> = [
  {
    title: "Pipeline",
    href: "/pipeline",
    blurb: "Prospects, workshops, and kanban stages with time-in-stage flags.",
    loop: "Loop 3",
  },
  {
    title: "Assessments",
    href: "/assessments",
    blurb: "ATLAS engine, the 7-step wizard, and live scores with uncertainty bands.",
    loop: "Loop 1–2",
  },
  {
    title: "Deliverables",
    href: "#",
    blurb: "Diagnostic packs, heatmaps, and the modernisation roadmap.",
    loop: "Loop 4",
  },
  {
    title: "Workbench",
    href: "/workbench",
    blurb: "Certification ladder, practice arena, power drills, bench queue.",
    loop: "Loop 5",
  },
  {
    title: "My Earnings",
    href: "#",
    blurb: "Commission breakdown, recovery fees, YTD and projections.",
    loop: "Loop 6",
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
            The advisor platform of the Bruntsfield Advisory Network. This is the Loop 0
            shell — the sections below are placeholders wired up across the build loops.
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
          {SECTIONS.map((s) => (
            <li key={s.title}>
              <Link
                href={s.href}
                style={{
                  display: "block",
                  height: "100%",
                  padding: "1.1rem 1.2rem",
                  background: "var(--color-paper-raised)",
                  border: "1px solid var(--color-border)",
                  borderRadius: "var(--radius)",
                  textDecoration: "none",
                  color: "inherit",
                }}
              >
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
                  <span
                    className="mono"
                    style={{ fontSize: "0.62rem", color: "var(--color-ink-muted)" }}
                  >
                    {s.loop}
                  </span>
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
              </Link>
            </li>
          ))}
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
