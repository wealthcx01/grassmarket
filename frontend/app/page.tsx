import Link from "next/link";
import { FirstRunWalkthrough } from "@/components/FirstRunWalkthrough";
import { WelcomeBanner } from "@/components/WelcomeBanner";

// The advisor's sections, grouped by an intentional IA (GRS-0091): the client-delivery FLOW first
// (prospect → assess → deliver, in that order), then the grow-and-get-paid group. `step` numbers the
// delivery flow because it genuinely is a sequence; the secondary group carries no step.
type Section = {
  title: string;
  href: string;
  blurb: string;
  kicker: string;
  step?: number;
};

const CLIENT_WORK: ReadonlyArray<Section> = [
  {
    step: 1,
    title: "Pipeline",
    href: "/pipeline",
    kicker: "Prospects & workshops",
    blurb: "Prospects, workshops, and kanban stages with time-in-stage flags and a weighted forecast.",
  },
  {
    step: 2,
    title: "Your Portfolio",
    href: "/assessments",
    kicker: "Portfolio · the Platform Power wizard",
    blurb: "Your portfolio of assessments — segment, last score and status at a glance — and the wizard: business metrics, the 7 Powers, and the infrastructure deep dive, scored live with uncertainty bands.",
  },
  {
    step: 3,
    title: "Deliverables",
    href: "/engagements",
    kicker: "Per engagement",
    blurb: "Diagnostic packs, heatmaps, and the modernisation roadmap — generated from a finalised assessment.",
  },
];

const GROW: ReadonlyArray<Section> = [
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

function SectionCard({ section }: { section: Section }) {
  return (
    <Link href={section.href} className="card-link" style={{ padding: "1.25rem 1.35rem", height: "100%" }}>
      <span
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "0.5rem",
        }}
      >
        <p className="eyebrow" style={{ fontSize: "0.62rem", margin: 0 }}>
          {section.kicker}
        </p>
        {section.step ? (
          <span
            aria-hidden
            className="mono"
            style={{ fontSize: "0.7rem", color: "var(--color-ink-faint)" }}
          >
            {String(section.step).padStart(2, "0")}
          </span>
        ) : null}
      </span>
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
          {section.title}
        </span>
        <span aria-hidden className="mono" style={{ color: "var(--color-ink-faint)" }}>
          →
        </span>
      </span>
      <p style={{ margin: "0.5rem 0 0", fontSize: "0.88rem", color: "var(--color-ink-muted)", lineHeight: 1.5 }}>
        {section.blurb}
      </p>
    </Link>
  );
}

export default function DashboardPage() {
  return (
    <div className="stack" style={{ gap: "2.75rem" }}>
      <FirstRunWalkthrough />
      {/* Welcome + context (GRS-0089) */}
      <section>
        <WelcomeBanner />
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
            New to Platform Power? Start with the primer
          </span>
          <span style={{ display: "block", color: "var(--color-ink-muted)", fontSize: "0.9rem", marginTop: "0.15rem" }}>
            B · P · L · V, the four maturity levels, evidence grades, and the benefit-vs-barrier rule — in ten minutes.
          </span>
        </span>
        <span aria-hidden className="mono" style={{ color: "var(--color-accent)", fontSize: "1.1rem" }}>
          →
        </span>
      </Link>

      {/* Your client work — the delivery flow, prioritised (GRS-0091) */}
      <section>
        <div style={{ marginBottom: "1rem" }}>
          <h2 style={{ fontSize: "1.1rem", margin: 0 }}>Your client work</h2>
          <p style={{ margin: "0.25rem 0 0", color: "var(--color-ink-muted)", fontSize: "0.9rem" }}>
            Prospect, assess, deliver — the flow from a lead to a finished Platform Power Report.
          </p>
        </div>
        <ul
          style={{
            listStyle: "none",
            margin: 0,
            padding: 0,
            display: "grid",
            gap: "1rem",
            gridTemplateColumns: "repeat(auto-fit, minmax(16rem, 1fr))",
          }}
        >
          {CLIENT_WORK.map((s) => (
            <li key={s.title}>
              <SectionCard section={s} />
            </li>
          ))}
        </ul>
      </section>

      {/* Grow & get paid — secondary group */}
      <section>
        <h2 style={{ fontSize: "1.1rem", margin: "0 0 1rem" }}>Grow &amp; get paid</h2>
        <ul
          style={{
            listStyle: "none",
            margin: 0,
            padding: 0,
            display: "grid",
            gap: "1rem",
            gridTemplateColumns: "repeat(auto-fit, minmax(18rem, 1fr))",
          }}
        >
          {GROW.map((s) => (
            <li key={s.title}>
              <SectionCard section={s} />
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
