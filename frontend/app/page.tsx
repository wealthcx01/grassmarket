import Link from "next/link";
import { FirstRunWalkthrough } from "@/components/FirstRunWalkthrough";

// PRD §1 / §4–7 — the advisor's main sections. Every section has a live page.
const SECTIONS: ReadonlyArray<{ title: string; href: string; blurb: string; kicker: string }> = [
  {
    title: "Pipeline",
    href: "/pipeline",
    kicker: "Prospects & workshops",
    blurb: "Prospects, workshops, and kanban stages with time-in-stage flags and a weighted forecast.",
  },
  {
    title: "Your Brokerages",
    href: "/assessments",
    kicker: "Portfolio · the ATLAS wizard",
    blurb: "Your portfolio of assessments — segment, last score and status at a glance — and the 7-step wizard: business metrics, the 7 Powers, and the infrastructure deep dive, scored live with uncertainty bands.",
  },
  {
    title: "Deliverables",
    href: "/engagements",
    kicker: "Per engagement",
    blurb: "Diagnostic packs, heatmaps, and the modernisation roadmap — generated from a finalised assessment.",
  },
  {
    title: "Workbench",
    href: "/workbench",
    kicker: "Certification & practice",
    blurb: "Certification ladder, practice arena, power drills, calibration, and the bench queue.",
  },
  {
    title: "My Earnings",
    href: "/earnings",
    kicker: "Commission & fees",
    blurb: "Commission breakdown, workshop recovery fees, YTD and projections — with a downloadable statement.",
  },
];

export default function DashboardPage() {
  return (
    <div className="stack" style={{ gap: "2.75rem" }}>
      <FirstRunWalkthrough />
      {/* Hero */}
      <section
        style={{
          display: "flex",
          alignItems: "flex-start",
          justifyContent: "space-between",
          gap: "1.5rem",
          flexWrap: "wrap",
        }}
      >
        <div style={{ maxWidth: "40rem" }}>
          <p className="eyebrow">Advisor dashboard</p>
          <h1 style={{ margin: "0.4rem 0 0.5rem" }}>Bruntsfield Advisor Studio</h1>
          <p style={{ margin: 0, color: "var(--color-ink-muted)", fontSize: "1.05rem", lineHeight: 1.55 }}>
            The advisor platform of the Bruntsfield Advisory Network — pipeline management, ATLAS
            assessments, client deliverables, and the Workbench. Jump to a section below, or start
            with the primer if ATLAS is new to you.
          </p>
        </div>
      </section>

      {/* New-advisor primer strip */}
      <Link
        href="/guide"
        className="card-link"
        style={{
          padding: "1.15rem 1.35rem",
          display: "flex",
          alignItems: "center",
          gap: "1rem",
          background:
            "linear-gradient(180deg, var(--color-accent-tint) 0%, var(--color-paper-raised) 100%)",
          borderColor: "var(--color-accent-tint-border)",
        }}
      >
        <span
          aria-hidden
          style={{
            flex: "none",
            width: "2.4rem",
            height: "2.4rem",
            borderRadius: "var(--radius)",
            background: "var(--color-accent)",
            color: "var(--color-accent-contrast)",
            display: "grid",
            placeItems: "center",
            fontFamily: "var(--font-serif)",
            fontWeight: 700,
          }}
        >
          ?
        </span>
        <span style={{ flex: 1 }}>
          <span style={{ display: "block", fontWeight: 600, fontFamily: "var(--font-serif)", fontSize: "1.05rem" }}>
            New to ATLAS? Start with the primer
          </span>
          <span style={{ display: "block", color: "var(--color-ink-muted)", fontSize: "0.9rem", marginTop: "0.15rem" }}>
            B · P · L · V, the four maturity levels, evidence grades, and the benefit-vs-barrier rule — in ten minutes.
          </span>
        </span>
        <span aria-hidden className="mono" style={{ color: "var(--color-accent)", fontSize: "1.1rem" }}>
          →
        </span>
      </Link>

      {/* Sections */}
      <section>
        <h2 style={{ fontSize: "1.1rem", marginBottom: "1rem" }}>Sections</h2>
        <ul
          style={{
            listStyle: "none",
            margin: 0,
            padding: 0,
            display: "grid",
            gap: "1rem",
            gridTemplateColumns: "repeat(auto-fill, minmax(17rem, 1fr))",
          }}
        >
          {SECTIONS.map((s) => (
            <li key={s.title}>
              <Link href={s.href} className="card-link" style={{ padding: "1.25rem 1.35rem", height: "100%" }}>
                <p className="eyebrow" style={{ fontSize: "0.62rem" }}>
                  {s.kicker}
                </p>
                <span
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    gap: "0.5rem",
                    margin: "0.35rem 0 0",
                  }}
                >
                  <span style={{ fontFamily: "var(--font-serif)", fontWeight: 600, fontSize: "1.2rem" }}>
                    {s.title}
                  </span>
                  <span aria-hidden className="mono" style={{ color: "var(--color-ink-faint)" }}>
                    →
                  </span>
                </span>
                <p style={{ margin: "0.5rem 0 0", fontSize: "0.88rem", color: "var(--color-ink-muted)", lineHeight: 1.5 }}>
                  {s.blurb}
                </p>
              </Link>
            </li>
          ))}
        </ul>
      </section>

    </div>
  );
}
