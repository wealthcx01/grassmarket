import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Advisor Guide — Advisor Studio",
  description: "How to use Grassmarket end to end: pipeline, assessments, deliverables, earnings.",
};

/**
 * The in-platform Advisor Guide (GRS-0057). A practical, plain-language how-to for the whole advisor
 * workflow — distinct from /guide, which is the ATLAS *concepts* primer (B·P·L·V, evidence grades).
 * Static and public: it carries guidance, never a user's data.
 */

type Step = { do: string; then?: string };
type Section = {
  id: string;
  kicker: string;
  title: string;
  lead: string;
  href?: { label: string; to: string };
  steps: Step[];
  note?: { tone: "info" | "warn"; text: string };
};

const SECTIONS: ReadonlyArray<Section> = [
  {
    id: "start",
    kicker: "01 · Getting started",
    title: "Sign in and find your way around",
    lead: "Access is invitation-only. Once you're in, the dashboard is home — five sections, each with a one-line description of what it's for.",
    steps: [
      { do: "Sign in with the email you were invited on.", then: "Forgotten where you are? The Bruntsfield mark, top-left, always returns you to the dashboard." },
      { do: "New to the ATLAS framework? Read the ten-minute primer first — it explains B · P · L · V, the four maturity levels, and evidence grades.", then: "It's linked from the dashboard and from Principles, below." },
      { do: "Pick a section: Pipeline, Assessments, Deliverables, Workbench, or Earnings." },
    ],
  },
  {
    id: "pipeline",
    kicker: "02 · Pipeline",
    title: "Work your pipeline",
    lead: "Your CRM board: ten stages from first contact to a contracted engagement, with a weighted forecast. The forecast is expressed in deal volume — deliberately not pounds — so an early conversation is never mistaken for booked revenue.",
    href: { label: "Open the pipeline", to: "/pipeline" },
    steps: [
      { do: "Add a prospect by typing a company name and pressing Add prospect.", then: "It lands in the first stage." },
      { do: "Move a card forward as the relationship progresses — the board decides which moves are legal and reverts one it isn't.", then: "A card that has sat too long is flagged stale so nothing goes quiet on you." },
      { do: "Read the forecast strip: prospects, open deals, and expected won deals, with a per-stage win probability.", then: "An empty stage reads “No prospects” — that's intentional, not a glitch." },
    ],
  },
  {
    id: "assess",
    kicker: "03 · Assessment",
    title: "Run an ATLAS assessment",
    lead: "The seven-step wizard scores a company across the 7 Powers, Platform Value, and the 9 infrastructure modules. It autosaves every edit, so a partial assessment is always safe to leave and resume.",
    href: { label: "Open assessments", to: "/assessments" },
    steps: [
      { do: "Start an assessment for the subject company, then work the steps left to right: Business Metrics, Strategic Powers, Module Overview, the Infrastructure Deep Dive.", then: "Your work saves automatically — the badge moves from “Saving…” to “All changes saved”." },
      { do: "Rate what you know. For each subcomponent pick a maturity level and record how sure you are with an evidence grade (E1 hearsay → E4 you saw it work).", then: "The grade widens or tightens the uncertainty on the score — honest by design." },
      { do: "Leave anything you haven't looked at as Not Assessed. Never guess.", then: "Not Assessed is a first-class state; it lowers coverage and widens the range, but it never counts as zero." },
      { do: "When it's ready, finalise. Finalising locks the inputs and produces an immutable, versioned scoring run." },
    ],
    note: {
      tone: "warn",
      text: "Finalising is gated on governance: every rated subcomponent needs a second independent rater and a resolved consensus (dual rating, §9), and any high-stakes rating needs Rating Committee sign-off (§8). The wizard tells you exactly what's still outstanding.",
    },
  },
  {
    id: "read",
    kicker: "04 · Reading the score",
    title: "Read the result honestly",
    lead: "A finalised assessment opens straight to Summary & Interpretation — the answer, not a form. Everything here is built to show confidence and its limits together.",
    steps: [
      { do: "Read Platform Value (V) as the headline, always with its P10–P90 range — never the point number alone.", then: "B (Business), P (Strategic Power) and L (Infrastructure) each carry their own range." },
      { do: "Check coverage and the overall uncertainty. “1/51 rated · 2% of applicable · uncertainty Very High” means treat the number as directional.", then: "More assessed subcomponents → tighter, more defensible ranges." },
      { do: "Find the likely constraint — the weakest module. It's usually the number a client remembers, and where the next pound of effort pays back most.", then: "The module bars are ordered weakest-first for exactly this reason." },
      { do: "Read the Platform Power triad in words (Economic, Perceived, Defence — e.g. Established, Emerging). Ordinal ratings, never decimals.", then: "Words rate; numbers rank. They are kept in separate equations on purpose." },
    ],
  },
  {
    id: "deliver",
    kicker: "05 · Deliverables",
    title: "Turn a score into a client document",
    lead: "From an engagement, a finalised assessment generates client documents — a Platform Power Report, Executive Summary, Heatmap, and more. AI drafts the prose; you approve it. Nothing AI-written reaches a client without your sign-off.",
    href: { label: "Open engagements", to: "/engagements" },
    steps: [
      { do: "On the engagement, pick the document and an audience. It defaults to Internal draft.", then: "An internal draft generates in one click, for your eyes." },
      { do: "For a client document, choose Client-facing — the button becomes Review & generate. Confirm on the review step, which names the document and the release gates it must clear.", then: "Cancel backs out with nothing sent. This is deliberate friction on the one action that leaves the building." },
      { do: "Review the AI sections and approve each. A pack is not client-ready while any section is pending.", then: "Download re-checks every gate before a single byte is written." },
    ],
    note: {
      tone: "info",
      text: "A client-facing pack is released only when it uses ratified (client-usable) coefficients, every AI section is approved, and any high-stakes rating has committee sign-off. If a gate is unmet, generation is refused with a plain-English reason.",
    },
  },
  {
    id: "earnings",
    kicker: "06 · Earnings",
    title: "See what you've earned",
    lead: "Your commission, workshop recovery fees, and projections in one place — every figure disclosed plainly, with a downloadable statement.",
    href: { label: "Open earnings", to: "/earnings" },
    steps: [
      { do: "Read the cards: earned YTD, pending, invoiced, paid, and projected unpaid." },
      { do: "Commission lines appear as engagements and recovery fees are recorded.", then: "Download a statement (.docx) whenever you need one." },
    ],
  },
  {
    id: "workbench",
    kicker: "07 · Workbench",
    title: "Sharpen your practice",
    lead: "Certification, practice arena, power drills, and calibration — how you earn and keep the assessor level that unlocks high-stakes ratings.",
    href: { label: "Open the workbench", to: "/workbench" },
    steps: [
      { do: "Work the certification ladder and clear your next action from the bench queue." },
      { do: "Run drills and practice-arena sessions to keep calibrated.", then: "Levels and streaks here are about your craft — not client or deal activity." },
    ],
  },
];

const PRINCIPLES: ReadonlyArray<{ title: string; body: string }> = [
  {
    title: "Honest about uncertainty",
    body: "Ranges, coverage, and confidence are shown as loudly as the headline number. A score you can't yet defend should look like one.",
  },
  {
    title: "Two tracks, never mixed",
    body: "Continuous scores rank what to fix first; rule-based gates produce the headline word; the value bridge prices in pounds. Score-points and currency never share an equation.",
  },
  {
    title: "AI proposes, you approve",
    body: "Meeting extraction, deliverable drafts, and practice feedback are AI-drafted and human-gated. Nothing AI-generated reaches a client without your sign-off.",
  },
  {
    title: "Fail loud, never fake it",
    body: "A missing input or an unmet gate stops and says why. The platform never guesses, defaults, or quietly fills a gap on your behalf.",
  },
];

function StepList({ steps }: { steps: readonly Step[] }) {
  return (
    <ol style={{ listStyle: "none", margin: "1rem 0 0", padding: 0, display: "grid", gap: "0.75rem" }}>
      {steps.map((s, i) => (
        <li key={i} style={{ display: "grid", gridTemplateColumns: "1.6rem 1fr", gap: "0.75rem" }}>
          <span
            aria-hidden
            className="mono"
            style={{
              width: "1.6rem",
              height: "1.6rem",
              borderRadius: "5px",
              background: "var(--color-accent-tint)",
              color: "var(--color-accent)",
              display: "grid",
              placeItems: "center",
              fontSize: "0.78rem",
              fontWeight: 600,
            }}
          >
            {i + 1}
          </span>
          <span>
            <span style={{ display: "block", fontWeight: 500, lineHeight: 1.5 }}>{s.do}</span>
            {s.then && (
              <span style={{ display: "block", color: "var(--color-ink-muted)", fontSize: "0.9rem", marginTop: "0.15rem", lineHeight: 1.5 }}>
                {s.then}
              </span>
            )}
          </span>
        </li>
      ))}
    </ol>
  );
}

export default function HelpPage() {
  return (
    <div className="stack" style={{ gap: "2.75rem" }}>
      {/* Hero */}
      <section style={{ maxWidth: "42rem" }}>
        <p className="eyebrow">Advisor guide</p>
        <h1 style={{ margin: "0.4rem 0 0.6rem" }}>How to use Grassmarket, end to end</h1>
        <p style={{ margin: 0, color: "var(--color-ink-muted)", fontSize: "1.05rem", lineHeight: 1.6 }}>
          A practical walk through the whole advisor workflow — from a first prospect to a finalised
          assessment, a client deliverable, and the commission that follows. For the concepts behind
          the scoring, read{" "}
          <Link href="/guide">the ten-minute ATLAS primer</Link>.
        </p>
      </section>

      {/* Contents */}
      <nav aria-label="Contents" style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
        {SECTIONS.map((s) => (
          <a
            key={s.id}
            href={`#${s.id}`}
            className="pill"
            style={{ textDecoration: "none", fontSize: "0.8rem", padding: "0.35rem 0.8rem" }}
          >
            {s.kicker.split(" · ")[1] ?? s.kicker}
          </a>
        ))}
        <a href="#principles" className="pill" style={{ textDecoration: "none", fontSize: "0.8rem", padding: "0.35rem 0.8rem" }}>
          Principles
        </a>
      </nav>

      {/* Sections */}
      {SECTIONS.map((s) => (
        <section key={s.id} id={s.id} style={{ scrollMarginTop: "5rem", maxWidth: "44rem" }}>
          <p className="eyebrow">{s.kicker}</p>
          <h2 style={{ fontSize: "1.4rem", margin: "0.35rem 0 0.5rem" }}>{s.title}</h2>
          <p style={{ margin: 0, color: "var(--color-ink-muted)", lineHeight: 1.6 }}>{s.lead}</p>
          <StepList steps={s.steps} />
          {s.note && (
            <div className={s.note.tone === "warn" ? "callout callout-warn" : "callout callout-info"} style={{ marginTop: "1rem" }}>
              {s.note.text}
            </div>
          )}
          {s.href && (
            <p style={{ marginTop: "1rem" }}>
              <Link href={s.href.to} className="btn btn-secondary">
                {s.href.label} →
              </Link>
            </p>
          )}
        </section>
      ))}

      {/* Principles */}
      <section id="principles" style={{ scrollMarginTop: "5rem" }}>
        <p className="eyebrow">The rules that never bend</p>
        <h2 style={{ fontSize: "1.4rem", margin: "0.35rem 0 0.5rem" }}>Principles</h2>
        <p style={{ margin: "0 0 1.2rem", color: "var(--color-ink-muted)", maxWidth: "44rem", lineHeight: 1.6 }}>
          Four commitments shape everything above. They&rsquo;re why a Grassmarket assessment holds
          up in the room.
        </p>
        <ul
          style={{
            listStyle: "none",
            margin: 0,
            padding: 0,
            display: "grid",
            gap: "1rem",
            gridTemplateColumns: "repeat(auto-fill, minmax(18rem, 1fr))",
          }}
        >
          {PRINCIPLES.map((p) => (
            <li key={p.title} className="card" style={{ padding: "1.1rem 1.25rem" }}>
              <h3 style={{ fontFamily: "var(--font-serif)", fontSize: "1.05rem", margin: "0 0 0.35rem" }}>{p.title}</h3>
              <p style={{ margin: 0, color: "var(--color-ink-muted)", fontSize: "0.92rem", lineHeight: 1.55 }}>{p.body}</p>
            </li>
          ))}
        </ul>
      </section>

      <footer style={{ fontSize: "0.85rem", color: "var(--color-ink-muted)" }}>
        <Link href="/">← Dashboard</Link> · <Link href="/guide">ATLAS primer</Link>
      </footer>
    </div>
  );
}
