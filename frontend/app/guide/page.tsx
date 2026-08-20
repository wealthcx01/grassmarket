import Link from "next/link";
import type { Metadata } from "next";

import { GuideNav } from "@/components/GuideNav";
import { POWER_GUIDANCE } from "@/lib/powerGuidance";

// The seven Powers (GRS-0094): name + Helmer lifecycle stage from the registry, benefit/barrier/example
// reused from powerGuidance.ts (GRS-0069) so the primer and the wizard stay consistent — not re-authored.
const LIFECYCLE_LABEL: Record<string, string> = {
  origination: "Origination",
  takeoff: "Take-off",
  stability: "Stability",
};

const POWERS: ReadonlyArray<{ key: string; name: string; lifecycle: string }> = [
  { key: "SCALE_ECONOMIES", name: "Scale Economies", lifecycle: "takeoff" },
  { key: "NETWORK_ECONOMIES", name: "Network Economies", lifecycle: "takeoff" },
  { key: "COUNTER_POSITIONING", name: "Counter-Positioning", lifecycle: "origination" },
  { key: "SWITCHING_COSTS", name: "Switching Costs", lifecycle: "takeoff" },
  { key: "BRANDING", name: "Branding", lifecycle: "stability" },
  { key: "CORNERED_RESOURCE", name: "Cornered Resource", lifecycle: "origination" },
  { key: "PROCESS_POWER", name: "Process Power", lifecycle: "stability" },
];

export const metadata: Metadata = {
  title: "How Platform Power works — Advisor Studio",
  description:
    "The advisor guide: what the Platform Power framework measures, how the scoring works, and how to run the studio from a first prospect to a paid engagement.",
};

// The end-to-end pipeline (GRS-0092) — evidence in, board-defensible report out. Numbered because it
// genuinely is a sequence. Copy rewritten to the STYLE-VOICE register in GRS-0175.
const PIPELINE: ReadonlyArray<{ step: string; detail: string }> = [
  {
    step: "Gather evidence and grade it",
    detail:
      "You learn how the platform works, from documents, interviews, dashboards, or your own inspection, and you record how sure you are on a four-point evidence scale. That grade is not paperwork. It is what decides how wide the ranges on the final scores are.",
  },
  {
    step: "Rate each element against a rubric anchor",
    detail:
      "Every subcomponent gets a maturity level against a written anchor that describes what that level looks like in practice. Every power gets a benefit and a barrier. Every business metric gets a value read against its normalisation curve. You make the judgement, and the anchor is what keeps two advisors reaching the same answer from the same facts.",
  },
  {
    step: "The engine computes the three lens scores",
    detail:
      "Business, Power and Infrastructure are each computed as an evidence-weighted blend in which the weakest critical part caps the result, so a module cannot score above its own bottleneck. Nothing is guessed or filled in with a zero. An element you have not assessed stays marked as unassessed and widens the uncertainty instead.",
  },
  {
    step: "The engine models the uncertainty as a range",
    detail:
      "Rather than report a single figure that looks more precise than the evidence supports, the engine re-scores the assessment many times over, moving each input within the confidence its evidence grade allows, and reports the spread. Thin evidence produces a wide range, which is the honest result.",
  },
  {
    step: "Rules turn the scores into the words a board reads",
    detail:
      "The rating a client sees for each module, from Basic to Frontier, comes from rules rather than from rounding the score. A module cannot be rated Advanced while a critical part of it is Basic, however high the arithmetic runs. The rating is what you defend in the room, and the score underneath is what orders your fix list.",
  },
  {
    step: "The value bridge prices the gaps",
    detail:
      "Each upgrade is costed in pounds, the cash-flow levers it moves are valued as a net present value on the client's own baselines, and its strategic worth is stated in words. The three are never collapsed into a single figure, because dividing a score gap into money is the claim that fails technical due diligence fastest.",
  },
];

const LENSES: ReadonlyArray<{ letter: string; name: string; question: string }> = [
  {
    letter: "B",
    name: "Business",
    question:
      "What does this platform achieve economically? Assets under administration, revenue, margins, growth, and the cost of acquiring a customer, taken as hard numbers.",
  },
  {
    letter: "P",
    name: "Power",
    question:
      "What stops a competitor taking the business away? Hamilton Helmer's seven Powers, each scored on the benefit it creates and on the barrier that protects it.",
  },
  {
    letter: "L",
    name: "Infrastructure, the technology Layer",
    question:
      "Is the plumbing an asset or a constraint? Nine modules and fifty-one subcomponents, from the front end a customer touches through to liquidity.",
  },
  {
    letter: "V",
    name: "Platform Value",
    question:
      "The composite headline that blends the other three. The figure a client tends to remember, though, is the bottleneck: the weakest critical link, which strength elsewhere never fully hides.",
  },
];

const LEVELS: ReadonlyArray<{ level: string; test: string }> = [
  {
    level: "Basic",
    test: "It barely exists. Manual, unreliable, or absent, and the people who depend on it feel the pain regularly.",
  },
  {
    level: "Developing",
    test: "It exists, but you would not trust it under pressure. There are gaps, workarounds, and single points of failure.",
  },
  {
    level: "Advanced",
    test: "It reliably does its job. It is automated, monitored, and documented, and there is still room to improve it.",
  },
  {
    level: "Frontier",
    test: "It is a competitive weapon rather than merely adequate. Not every firm needs this, so it should never be presented as the universal target.",
  },
];

// Evidence grades (GRS-0095): plain-English meaning + what actually qualifies + the source, so the
// weakest-to-strongest escalation (client-said, interview, artifact, observed) is obvious.
const GRADES: ReadonlyArray<{ grade: string; source: string; meaning: string; qualifies: string }> = [
  {
    grade: "E1",
    source: "Client-said",
    meaning: "The client told you, and that is all you have. It is an unverified claim.",
    qualifies:
      "A statement made in a meeting or written on a form, such as “our uptime is 99.9%”, with nothing behind it yet.",
  },
  {
    grade: "E2",
    source: "Interview",
    meaning: "You probed the claim in a structured interview with the person who owns the thing.",
    qualifies:
      "You asked how it works, since when, who runs it, and what breaks, and the answers held together under follow-up.",
  },
  {
    grade: "E3",
    source: "Artifact",
    meaning: "You saw the thing itself, in the form of a document, dashboard, configuration, runbook, or metric.",
    qualifies: "A screenshot of the monitor, the incident log, the architecture diagram, or the actual number.",
  },
  {
    grade: "E4",
    source: "Observed",
    meaning: "You watched it work, or inspected it yourself. This is the strongest evidence available.",
    qualifies:
      "You saw a deployment run, watched a failover, or drove the system and confirmed it behaves the way it was described.",
  },
];

const MISTAKES: ReadonlyArray<{ mistake: string; why: string }> = [
  {
    mistake: "Scoring from memory instead of reading the rubric anchor.",
    why: "The anchor is what makes two advisors agree. Without it you are recording an impression, and an impression does not survive challenge.",
  },
  {
    mistake: "Presenting E1 evidence as though it were certain.",
    why: "A wide range is a perfectly respectable result. False precision is not, and it is the thing a technical reviewer tests first.",
  },
  {
    mistake: "Guessing at a rating to avoid marking something as not assessed.",
    why: "Everything else here is built to survive scrutiny, and a guess quietly poisons that. It is the one input the framework cannot recover from.",
  },
  {
    mistake: "Scoring a power on its benefit while leaving the barrier unexamined.",
    why: "An advantage a rival can copy next quarter is a head start, not a power, and the score is meant to tell those two apart.",
  },
  {
    mistake: "Presenting Frontier as the target every module should reach.",
    why: "Frontier means the capability is a competitive weapon. Most firms should be at Advanced in most modules and should spend the money elsewhere.",
  },
  {
    mistake: "Quoting a point score without the range around it.",
    why: "The point on its own claims more precision than the evidence supports, and it hides the very thing that tells a client how much to trust the number.",
  },
  {
    mistake: "Converting a score gap directly into pounds.",
    why: "Score points and currency are kept in separate equations on purpose. A sentence such as “these twelve points are worth £2m” fails due diligence on the spot.",
  },
];

function SectionTitle({ kicker, children }: { kicker: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: "1rem" }}>
      <p className="eyebrow">{kicker}</p>
      <h2 style={{ margin: "0.3rem 0 0", fontSize: "1.35rem" }}>{children}</h2>
    </div>
  );
}

// --- "Working the app" walkthroughs, merged from the former /help page (GRS-0175) ---
// The `id` of each walkthrough is unchanged from /help, so an existing /help#assess deep link
// resolves to the same content under /guide once the redirect has run.

type Step = { do: string; then?: string };
type Walkthrough = {
  id: string;
  kicker: string;
  title: string;
  lead: string;
  steps: readonly Step[];
  note?: { tone: "warn" | "info"; text: string };
  href?: { label: string; to: string };
};

const WALKTHROUGHS: ReadonlyArray<Walkthrough> = [
  {
    id: "start",
    kicker: "Getting started",
    title: "Sign in and find your way around",
    lead: "Access is by invitation. Once you are in, the dashboard is home, and each section on it carries a one-line description of what it is for.",
    steps: [
      {
        do: "Sign in with the email address you were invited on.",
        then: "The Bruntsfield mark in the top left always returns you to the dashboard, so you cannot get lost.",
      },
      {
        do: "If the framework is new to you, read the first half of this guide before you open an assessment.",
        then: "It covers the three lenses, the four maturity levels, and the evidence grades, which is everything the wizard assumes you already know.",
      },
      { do: "Then pick a section: Pipeline, Assessments, Engagements, Workbench, or Earnings." },
    ],
  },
  {
    id: "pipeline",
    kicker: "Pipeline",
    title: "Work your pipeline",
    lead: "Your board holds ten stages, from first contact through to a contracted engagement, with a weighted forecast across them. The forecast is expressed as a count of deals rather than in pounds, so that an early conversation is never mistaken for booked revenue.",
    href: { label: "Open the pipeline", to: "/pipeline" },
    steps: [
      { do: "Add a prospect by typing a company name and pressing Add prospect.", then: "It lands in the first stage." },
      {
        do: "Move a card forward as the relationship progresses. The board decides which moves are legal and reverts one that is not.",
        then: "A card that has sat in one stage too long is flagged as stale, so nothing goes quiet on you.",
      },
      {
        do: "Read the forecast strip: prospects, open deals, and expected won deals, with a win probability for each stage.",
        then: "An empty stage reads as empty on purpose. It is not a loading glitch.",
      },
    ],
  },
  {
    id: "assess",
    kicker: "Assessment",
    title: "Run a Platform Power assessment",
    lead: "The seven-step wizard scores a company across the seven Powers, Platform Value, and the nine infrastructure modules. It saves every edit as you make it, so a partial assessment is always safe to leave and resume.",
    href: { label: "Open assessments", to: "/assessments" },
    steps: [
      {
        do: "Start an assessment for the subject company, then work the steps from left to right: Business Metrics, Powers, then the Infrastructure Deep Dive.",
        then: "Your work saves on its own, and the badge moves from Saving to All changes saved.",
      },
      {
        do: "Rate what you know. For each subcomponent pick a maturity level, then record how sure you are with an evidence grade, from E1 for something you were simply told up to E4 for something you watched work.",
        then: "That grade is what widens or tightens the uncertainty carried on the score.",
      },
      {
        do: "Leave anything you have not looked at marked as Not Assessed, and never guess.",
        then: "Not Assessed is a proper state rather than a gap. It lowers your coverage and widens the range, but it is never counted as a zero.",
      },
      {
        do: "When the assessment is ready, finalise it. Finalising locks the inputs and produces an immutable, versioned scoring run.",
      },
    ],
    // GRS-0244 scope 1. This note described dual rating and Rating Committee sign-off — the peer
    // governance ADR-0041 and Methodology v1.6 made DORMANT. Two sections later the Guide
    // correctly describes the founder gate, so a new advisor read both and could not tell which
    // was true. A page that contradicts itself about who approves their work makes every other
    // claim on it suspect, which is why this counted as a bug rather than stale copy.
    note: {
      tone: "warn",
      text: "Finalising is gated: nothing is finalised until John has read and signed off the assessment as it currently stands. The Summary step shows where that stands and is the next walkthrough. (References elsewhere to a second independent rater and a Rating Committee describe peer governance that is specified, built, and dormant by design — the network is not yet large enough for it to be genuine peer challenge, so the founder holds sign-off instead. Methodology v1.6, ADR-0041.)",
    },
  },
  {
    id: "consensus",
    kicker: "Review and sign-off",
    title: "Send it to John, then finalise",
    lead: "One gate stands between a scored assessment and a finalised one. Nothing goes to a client that John has not read and signed off. You handle this from the Summary step, and it usually takes one message and a day.",
    href: { label: "Open assessments", to: "/assessments" },
    steps: [
      {
        do: "When you are happy with the assessment, press Send to John for review on the Summary step.",
        then: "It appears on his review queue in the Workbench, with your name and the date you sent it.",
      },
      {
        do: "Wait for the approval. The Summary step shows where it stands, so you do not need to chase.",
        then: "Once he approves, the step says so and gives you the date he signed it.",
      },
      {
        do: "Finalise and lock. From there you can generate a client deliverable.",
      },
      {
        do: "If you change anything after the approval, send it again.",
        then: "An approval covers the version it was given for. Editing after sign-off means John has not seen what you are now proposing to send, so the approval stops applying and the record goes back on his queue.",
      },
    ],
    note: {
      tone: "info",
      text: "This is enforced by the platform, not left to convention. Finalising a production assessment without a current approval is refused, and so is generating a client pack from one. Both refusals say why in plain English.",
    },
  },
  {
    id: "read",
    kicker: "Reading a finished score",
    title: "Read the result honestly",
    lead: "A finalised assessment opens straight to Summary and Interpretation, which is the answer rather than another form. Every element of that screen is arranged to show the confidence and its limits at the same time.",
    steps: [
      {
        do: "Read Platform Value as the headline, and quote it with its range rather than on its own.",
        then: "Business, Power and Infrastructure each carry a range of their own, computed the same way.",
      },
      {
        do: "Check the coverage line and the overall uncertainty before you rely on any figure. A line reading 1 of 51 rated, 2% of applicable, uncertainty very high means the number is directional at best.",
        then: "The more subcomponents you assess, the tighter and more defensible the ranges become.",
      },
      {
        do: "Find the likely constraint, which is the weakest module. It is usually the number a client remembers, and it is where the next pound of effort pays back most.",
        then: "The module bars are ordered weakest first for exactly this reason.",
      },
      {
        do: "Read the Platform Power triad as words. Economic, Perceived and Defence value are reported as ordinal ratings such as Emerging or Established, never as decimals.",
        then: "The section on reading the outputs, above, explains why those two kinds of result are kept apart.",
      },
    ],
  },
  {
    id: "client-report",
    kicker: "The client report",
    title: "Write the report the client actually reads",
    lead: "The client report is the document that represents the firm. You write six sections in your own words, the score fills in the arithmetic, and the client reads it as a branded PDF or a web page you send them a link to. It is the newest surface in the studio and the one worth learning first.",
    href: { label: "Open engagements", to: "/engagements" },
    steps: [
      {
        do: "From the engagement, open a deliverable and press Client report.",
        then: "The editor opens, headed with the client's name so you always know whose report you are writing.",
      },
      {
        do: "Write the six sections: the business, where the advantage sits, what is holding it back, what to do about it, what that is worth, and the technical appendix.",
        then: "Each section saves as you go. The report cannot be produced while any of them is empty, and the refusal names the ones still blank.",
      },
      {
        do: "Quote a figure only after declaring it. Any number in your prose has to come from the run.",
        then: "If you type a number the assessment did not produce, the editor refuses and says which one — that guard is what stops a report claiming something the score does not support.",
      },
      {
        do: "Send it to John if the record is client-facing, exactly as with the assessment.",
        then: "The words a client reads are approved separately from the scores. An edit after approval withdraws it, same rule as before.",
      },
      {
        do: "Download the branded PDF, or create a share link for a client who would rather read it in a browser.",
        then: "The PDF is named for the client and the month. The link shows the same content, and you can revoke it at any time.",
      },
    ],
    note: {
      tone: "info",
      text: "Share links record which sections were opened and roughly how long for, and the page tells the reader so in plain words before anything is recorded. You see it back as section titles with coarse times. Treat it as soft evidence: a client who prints the PDF and reads that instead shows as having read nothing.",
    },
  },
  {
    id: "deliver",
    kicker: "Deliverables",
    title: "The document packs",
    lead: "Alongside the client report, an engagement generates .docx packs — a Platform Power Report, an Executive Summary, a Heatmap. These are the internal and technical path: fuller, denser, and drafted by AI for you to approve. Nothing AI-written reaches a client without your sign-off. If you are sending something to a client to read, start with the client report above.",
    href: { label: "Open engagements", to: "/engagements" },
    steps: [
      {
        do: "On the engagement, pick the document and an audience. The audience defaults to Internal draft.",
        then: "An internal draft generates in one click, for your eyes only.",
      },
      {
        do: "For a client document, choose Client-facing. A review step then names the document and lists the release gates it has to clear before you confirm.",
        then: "Cancelling backs out with nothing sent. The extra step is deliberate friction on the one action that leaves the building.",
      },
      {
        do: "Review each AI-drafted section and approve it. A pack is not client-ready while any section is still pending.",
        then: "Download re-checks every gate again before a single byte is written.",
      },
    ],
    note: {
      tone: "info",
      text: "A client-facing pack is released only when the assessment used coefficients ratified for client use, every AI section has been approved, and John has signed off the current version of the document. If a gate is unmet, generation is refused and the reason is stated in plain English.",
    },
  },
  {
    id: "earnings",
    kicker: "Earnings",
    title: "See what you have earned",
    lead: "Your commission, workshop recovery fees, and projections sit in one place, with every figure disclosed plainly and a statement you can download.",
    href: { label: "Open earnings", to: "/earnings" },
    steps: [
      { do: "Read the cards: earned year to date, pending, invoiced, paid, and projected unpaid." },
      {
        do: "Commission lines appear as engagements and recovery fees are recorded against you.",
        then: "You can download a statement whenever you need one.",
      },
    ],
  },
  {
    id: "workbench",
    kicker: "Workbench",
    title: "Sharpen your practice",
    lead: "Certification, the practice arena and power drills sit together in the Workbench. This is how you earn the assessor level that unlocks high-stakes ratings, and how you keep it.",
    href: { label: "Open the workbench", to: "/workbench" },
    steps: [
      { do: "Work the certification ladder, and clear your next action from the bench queue." },
      {
        do: "Run drills and practice-arena sessions to stay calibrated between engagements.",
        then: "Levels and streaks here measure your craft rather than your client or deal activity, and they are visible only to you.",
      },
    ],
  },
];

const PRINCIPLES: ReadonlyArray<{ title: string; body: string }> = [
  {
    title: "Honest about uncertainty",
    body: "Ranges, coverage, and confidence are shown as plainly as the headline number, because a score you cannot yet defend ought to look like one. This is why the tool would rather show you a wide range than a tidy figure it cannot support.",
  },
  {
    title: "Two tracks, kept separate",
    body: "Continuous scores rank what to fix first. Rule-based gates produce the rating word a client reads. The value bridge prices work in pounds. Score points and currency never appear in the same equation, because the moment they do the arithmetic stops meaning anything.",
  },
  {
    title: "A person approves every AI draft",
    body: "Deliverable prose and practice feedback are drafted by AI, and a person has to approve each one before it counts. Nothing drafted by a model reaches a client on its own, and the approval is recorded against the document rather than assumed.",
  },
  {
    title: "Fail loudly rather than fill a gap",
    body: "A missing input or an unmet gate stops the work and says why. The platform never guesses a value, substitutes a default, or quietly fills a gap on your behalf, because a silent fallback is indistinguishable from a real answer once it is in a report.",
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
            style={{ width: "1.6rem", height: "1.6rem", borderRadius: "5px", background: "var(--color-accent-tint)", color: "var(--color-accent)", display: "grid", placeItems: "center", fontSize: "0.78rem", fontWeight: 600 }}
          >
            {i + 1}
          </span>
          <span>
            <span style={{ display: "block", fontWeight: 500, lineHeight: 1.5 }}>{s.do}</span>
            {s.then ? (
              <span style={{ display: "block", color: "var(--color-ink-muted)", fontSize: "0.9rem", marginTop: "0.15rem", lineHeight: 1.5 }}>
                {s.then}
              </span>
            ) : null}
          </span>
        </li>
      ))}
    </ol>
  );
}

/** A worked picture of a modelled range (GRS-0175): a P10 to P90 bar with the deterministic point
 *  marked, drawn from the design tokens (no chart library). Example values: point 61, P10 55, P90 68
 *  on a 40 to 80 axis. */
function RangeStrip() {
  const W = 320;
  const lo = 40;
  const hi = 80;
  const x = (v: number) => ((v - lo) / (hi - lo)) * W;
  const p10 = 55;
  const p90 = 68;
  const point = 61;
  return (
    <figure style={{ margin: 0, maxWidth: `${W}px` }}>
      <svg
        viewBox={`0 0 ${W} 56`}
        width="100%"
        role="img"
        aria-label="A Platform Value of 61 with a likely range from 55 at the tenth percentile to 68 at the ninetieth."
      >
        {/* axis */}
        <line x1={0} y1={34} x2={W} y2={34} stroke="var(--color-border)" strokeWidth={1} />
        {/* the P10 to P90 band */}
        <rect x={x(p10)} y={26} width={x(p90) - x(p10)} height={16} rx={3} fill="var(--color-accent)" opacity={0.18} />
        {/* the deterministic point */}
        <line x1={x(point)} y1={22} x2={x(point)} y2={46} stroke="var(--color-accent)" strokeWidth={2.5} />
        {/* labels */}
        <text x={x(p10)} y={16} fontSize={10} textAnchor="middle" fill="var(--color-ink-muted)">P10 · 55</text>
        <text x={x(point)} y={16} fontSize={10} textAnchor="middle" fill="var(--color-ink)" fontWeight={600}>61</text>
        <text x={x(p90)} y={16} fontSize={10} textAnchor="middle" fill="var(--color-ink-muted)">P90 · 68</text>
      </svg>
      <figcaption style={{ fontSize: "0.72rem", color: "var(--color-ink-faint)", marginTop: "0.2rem" }}>
        The headline of 61 is the deterministic score. The shaded band is the likely range, running from the
        tenth percentile at 55 to the ninetieth at 68.
      </figcaption>
    </figure>
  );
}

export default function GuidePage() {
  return (
    <article className="stack measure" style={{ gap: "2.5rem", margin: "0 auto" }}>
      <GuideNav />
      <header>
        <p className="eyebrow">Advisor guide · Platform Power</p>
        <h1 style={{ margin: "0.4rem 0 0.6rem" }}>How Platform Power works</h1>
        <p style={{ margin: 0, fontSize: "1.05rem", color: "var(--color-ink-muted)", lineHeight: 1.6 }}>
          Platform Power turns what you learn about a client&rsquo;s platform into scores, ratings, and a
          modernisation plan a board can trust. Your judgement is the input, and the framework&rsquo;s job is
          to make that judgement consistent, comparable, and defensible. This guide covers the framework
          first, then the studio itself, from a first prospect to the commission on a finished engagement.
        </p>
      </header>

      {/* Why it exists (GRS-0092) */}
      <section id="why">
        <SectionTitle kicker="The problem it solves">Why Platform Power exists</SectionTitle>
        <p style={{ margin: "0 0 0.75rem", color: "var(--color-ink-muted)", lineHeight: 1.6 }}>
          One question sits under every brokerage and fintech engagement: <strong>can this platform
          create value and hold onto it?</strong> Answering it well means looking at three things at
          once. There are the economics, which say whether the business makes money. There is the
          strategic position, which says what stops a rival taking that business away. And there is the
          technology, which says whether the plumbing is an asset or a liability waiting to surface. Most
          reviews look hard at one of the three and wave at the other two.
        </p>
        <p style={{ margin: 0, color: "var(--color-ink-muted)", lineHeight: 1.6 }}>
          Platform Power scores all three on one comparable scale, works from graded evidence, and prices
          the gaps without pretending to more precision than it has. It does not replace your judgement.
          It takes your judgement and makes it <strong>consistent</strong>, so that two advisors reach the
          same score from the same facts; <strong>comparable</strong>, so that this platform can be set
          against its peers and against its own position last year; and <strong>defensible</strong>, so
          that it survives the technical due diligence a board or an acquirer will put it through.
        </p>
      </section>

      {/* Where it comes from (GRS-0092) */}
      <section id="provenance">
        <SectionTitle kicker="Provenance">Where the framework comes from</SectionTitle>
        <p style={{ margin: "0 0 0.75rem", color: "var(--color-ink-muted)", lineHeight: 1.6 }}>
          The strategy lens was not invented here. <strong>Power</strong> is Hamilton Helmer&rsquo;s{" "}
          <em>7 Powers</em>, the modern canon on durable competitive advantage, and it is used as he
          wrote it: seven structural sources of power, each of which is real only when a genuine{" "}
          <em>benefit</em> is protected by a <em>barrier</em> that a competitor cannot cheaply cross.
        </p>
        <p style={{ margin: 0, color: "var(--color-ink-muted)", lineHeight: 1.6 }}>
          <strong>Infrastructure</strong> comes from the infrastructure deep-dive lineage, which is a
          structured technology assessment of nine modules and fifty-one subcomponents running from the
          front end through to liquidity. Its job is to turn the question of whether the plumbing is an
          asset or a constraint into evidence-graded ratings rather than opinion. <strong>Business</strong>{" "}
          is the hard economic register: assets under administration, revenue, unit economics, and growth.
          Bringing strategy, technology and economics under one graded, uncertainty-aware method is the
          whole idea. Nothing is scored on instinct, and nothing is priced by dividing a score gap into
          pounds.
        </p>
      </section>

      {/* How it works, end to end (GRS-0092) */}
      <section id="how-it-works">
        <SectionTitle kicker="The pipeline">How it works, end to end</SectionTitle>
        <ol style={{ listStyle: "none", margin: 0, padding: 0, display: "grid", gap: "0.75rem", counterReset: "step" }}>
          {PIPELINE.map((p, i) => (
            <li key={p.step} className="card" style={{ padding: "1rem 1.15rem", display: "flex", gap: "1rem", alignItems: "flex-start" }}>
              <span
                aria-hidden
                className="mono"
                style={{
                  flex: "none",
                  width: "1.9rem",
                  height: "1.9rem",
                  borderRadius: "50%",
                  background: "var(--color-accent)",
                  color: "var(--color-paper)",
                  display: "grid",
                  placeItems: "center",
                  fontSize: "0.85rem",
                  fontWeight: 600,
                }}
              >
                {String(i + 1).padStart(2, "0")}
              </span>
              <div>
                <div style={{ fontWeight: 600, fontFamily: "var(--font-serif)", fontSize: "1.02rem" }}>{p.step}</div>
                <p style={{ margin: "0.2rem 0 0", color: "var(--color-ink-muted)", fontSize: "0.9rem", lineHeight: 1.5 }}>{p.detail}</p>
              </div>
            </li>
          ))}
        </ol>
      </section>

      {/* Three lenses + headline */}
      <section id="lenses">
        <SectionTitle kicker="The shape of it">Three lenses, one headline</SectionTitle>
        <p style={{ margin: "0 0 1rem", color: "var(--color-ink-muted)", lineHeight: 1.6 }}>
          An assessment looks at a platform through three lenses and reports a composite headline over
          them. Each lens has a letter, which is the short form you will see on the wizard and in
          reports once the full name has been given.
        </p>
        <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "grid", gap: "0.75rem" }}>
          {LENSES.map((l) => (
            <li key={l.letter} className="card" style={{ padding: "1rem 1.15rem", display: "flex", gap: "1rem", alignItems: "flex-start" }}>
              <span
                aria-hidden
                style={{
                  flex: "none",
                  width: "2.4rem",
                  height: "2.4rem",
                  borderRadius: "var(--radius)",
                  background: "var(--color-accent-tint)",
                  border: "1px solid var(--color-accent-tint-border)",
                  color: "var(--color-accent)",
                  display: "grid",
                  placeItems: "center",
                  fontFamily: "var(--font-serif)",
                  fontWeight: 700,
                  fontSize: "1.15rem",
                }}
              >
                {l.letter}
              </span>
              <div>
                <div style={{ fontWeight: 600, fontFamily: "var(--font-serif)", fontSize: "1.05rem" }}>{l.name}</div>
                <p style={{ margin: "0.2rem 0 0", color: "var(--color-ink-muted)", fontSize: "0.9rem", lineHeight: 1.5 }}>{l.question}</p>
              </div>
            </li>
          ))}
        </ul>
        <p className="callout callout-info" style={{ marginTop: "1rem" }}>
          Sitting on top of the lenses, the client also sees the <strong>Platform Power triad</strong>:
          Economic, Perceived, and Defence value. Each is reported as one of four words, from None
          through Emerging and Established to Wide, and never as a decimal.
        </p>
      </section>

      {/* The lenses in depth — letter to word mapping (GRS-0093) */}
      <section id="letters">
        <SectionTitle kicker="Reading the lenses">What the letters mean</SectionTitle>
        <p style={{ margin: "0 0 1rem", color: "var(--color-ink-muted)", lineHeight: 1.6 }}>
          A <strong>platform</strong>, in this framework, is the whole operating system of a brokerage or
          fintech: its economics, its strategic position, and the technology that runs it.{" "}
          <strong>Platform Power</strong> is how much durable value that whole creates, which is why the
          headline figure is called <strong>Platform Value</strong>. The letters stop being arbitrary
          once you read them together.
        </p>
        <dl style={{ margin: 0, display: "grid", gap: "0.9rem" }}>
          <div>
            <dt style={{ fontFamily: "var(--font-serif)", fontWeight: 600 }}>B, for Business</dt>
            <dd style={{ margin: "0.15rem 0 0", color: "var(--color-ink-muted)", fontSize: "0.92rem", lineHeight: 1.55 }}>
              The economic reality. Does the platform make money, and is that improving? Assets under
              administration, revenue, unit economics and growth, all normalised so that a £2bn platform
              and a £50m one can be compared fairly.
            </dd>
          </div>
          <div>
            <dt style={{ fontFamily: "var(--font-serif)", fontWeight: 600 }}>P, for Power</dt>
            <dd style={{ margin: "0.15rem 0 0", color: "var(--color-ink-muted)", fontSize: "0.92rem", lineHeight: 1.55 }}>
              Taken straight from Helmer&rsquo;s seven Powers. A power counts only where a real{" "}
              <strong>benefit</strong> is protected by a <strong>barrier</strong> that a rival cannot
              cheaply cross, and the engine scores it at whichever of the two is weaker.
            </dd>
          </div>
          <div>
            <dt style={{ fontFamily: "var(--font-serif)", fontWeight: 600 }}>L, for the technology Layer</dt>
            <dd style={{ margin: "0.15rem 0 0", color: "var(--color-ink-muted)", fontSize: "0.92rem", lineHeight: 1.55 }}>
              The infrastructure layer that sits under the business, covering nine modules from the front
              end through to liquidity. The question it answers is whether the plumbing is an{" "}
              <strong>asset</strong> that protects the business or a <strong>constraint</strong> that
              will surface as a problem later.
            </dd>
          </div>
          <div>
            <dt style={{ fontFamily: "var(--font-serif)", fontWeight: 600 }}>V, for Platform Value</dt>
            <dd style={{ margin: "0.15rem 0 0", color: "var(--color-ink-muted)", fontSize: "0.92rem", lineHeight: 1.55 }}>
              The composite headline, blending the other three. The figure a client actually remembers is
              usually the <strong>bottleneck</strong> instead: the weakest critical link, which no amount
              of strength elsewhere fully hides.
            </dd>
          </div>
        </dl>
        <p style={{ marginTop: "1rem", fontSize: "0.9rem", color: "var(--color-ink-muted)", lineHeight: 1.55 }}>
          The <strong>Platform Power triad</strong> re-reads the same evidence as three plain words a
          board understands immediately. <strong>Economic</strong> value asks whether the platform is
          worth money. <strong>Perceived</strong> value asks whether customers feel it. And{" "}
          <strong>Defence</strong> value asks whether it can be protected.
        </p>
      </section>

      {/* Four levels */}
      <section id="maturity">
        <SectionTitle kicker="Rating infrastructure">The four maturity levels</SectionTitle>
        <p style={{ margin: "0 0 1rem", color: "var(--color-ink-muted)", lineHeight: 1.6 }}>
          Every infrastructure subcomponent is rated at one of four levels, against a written anchor that
          describes what that level looks like in a real firm.
        </p>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.92rem" }}>
            <tbody>
              {LEVELS.map((l) => (
                <tr key={l.level} style={{ borderBottom: "1px solid var(--color-border)" }}>
                  <th
                    scope="row"
                    style={{ textAlign: "left", verticalAlign: "top", padding: "0.7rem 1rem 0.7rem 0", width: "9rem", fontFamily: "var(--font-serif)", fontWeight: 600 }}
                  >
                    {l.level}
                  </th>
                  <td style={{ padding: "0.7rem 0", color: "var(--color-ink-muted)", lineHeight: 1.5 }}>{l.test}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p style={{ marginTop: "0.9rem", fontSize: "0.9rem", color: "var(--color-ink-muted)", lineHeight: 1.55 }}>
          Two further states sit outside the ladder, and both are honest answers.{" "}
          <strong>Not Applicable</strong> means the subcomponent is out of scope for this firm, and it
          drops out of the arithmetic entirely, with the remaining weights rebalanced around it.{" "}
          <strong>Not Assessed</strong> means it is in scope but you have no evidence yet. It is never
          scored as a zero, though it does cap what the module can reach and it widens the uncertainty
          range. Marking something Not Assessed is professionalism rather than failure.
        </p>
      </section>

      {/* Evidence grades (GRS-0095) */}
      <section id="evidence-grades">
        <SectionTitle kicker="How sure are you?">Evidence grades drive the ranges</SectionTitle>
        <p style={{ margin: "0 0 1rem", color: "var(--color-ink-muted)", lineHeight: 1.6 }}>
          Every rating carries a second mark for <em>how you know</em>. The four grades climb from the
          weakest form of evidence to the strongest, starting with what a client said, then what you
          probed in an interview, then an artifact you were shown, and finally something you observed
          yourself. Each step is a step from someone having claimed it toward you having seen it.
        </p>
        <ol style={{ listStyle: "none", margin: 0, padding: 0, display: "grid", gap: "0.6rem" }}>
          {GRADES.map((g) => (
            <li key={g.grade} className="card" style={{ padding: "0.9rem 1.1rem", display: "flex", gap: "1rem", alignItems: "flex-start" }}>
              <span className="tag" style={{ flex: "none", background: "var(--color-accent-tint)", color: "var(--color-accent)", borderColor: "var(--color-accent-tint-border)" }}>{g.grade}</span>
              <div>
                <div style={{ fontFamily: "var(--font-serif)", fontWeight: 600, fontSize: "0.98rem" }}>
                  {g.source}
                </div>
                <p style={{ margin: "0.15rem 0 0", fontSize: "0.88rem", color: "var(--color-ink-muted)", lineHeight: 1.5 }}>
                  {g.meaning}
                </p>
                <p style={{ margin: "0.35rem 0 0", fontSize: "0.82rem", color: "var(--color-ink-soft)", lineHeight: 1.5 }}>
                  <strong>What counts:</strong> {g.qualifies}
                </p>
              </div>
            </li>
          ))}
        </ol>
        <p style={{ marginTop: "0.9rem", fontSize: "0.9rem", color: "var(--color-ink-muted)", lineHeight: 1.55 }}>
          The grade is not administrative overhead, because it drives the output directly. Ratings
          carried on E1 evidence produce wide ranges, and E4 ratings produce tight ones. A higher grade
          counts for more because it is closer to the thing itself: a claim can be wrong and a document
          can be out of date, but something you watched work is hard to argue with. In practice the
          difference between a £25k assessment and a £75k one is largely the evidence grade you manage to
          reach.
        </p>
      </section>

      {/* Powers: benefit and barrier */}
      <section id="scoring-powers">
        <SectionTitle kicker="Scoring the seven Powers">Benefit and barrier, with the weaker side winning</SectionTitle>
        <p style={{ margin: "0 0 0.75rem", color: "var(--color-ink-muted)", lineHeight: 1.6 }}>
          For each power you record two things. The <strong>benefit</strong> asks whether there is a real
          economic advantage here. The <strong>barrier</strong> asks what stops a competitor copying it.{" "}
          <strong>The power is then scored at whichever of the two is weaker.</strong> A brilliant benefit
          with no barrier scores None, because competitors will simply copy it, and this is the single
          most common thing new advisors get wrong.
        </p>
        <p style={{ margin: "0 0 0.75rem", color: "var(--color-ink-muted)", lineHeight: 1.6 }}>
          Take a broker whose onboarding converts twice as well as anyone else&rsquo;s. The benefit is
          plainly real and shows up in the acquisition cost. Ask the barrier question, though, and the
          answer is that a competitor could hire the same design agency and match it inside two quarters.
          The power scores None, and what you have found is a head start worth defending rather than a
          moat worth paying for.
        </p>
        <p className="callout callout-warn">
          Every power is always scored, and Not Applicable does not exist for powers. A power that is
          irrelevant to this business is simply weak for this business, and that is itself information
          worth reporting.
        </p>
      </section>

      {/* The seven Powers, one by one (GRS-0094) */}
      <section id="seven-powers">
        <SectionTitle kicker="Helmer’s seven">The seven Powers, one by one</SectionTitle>
        <p style={{ margin: "0 0 1rem", color: "var(--color-ink-muted)", lineHeight: 1.6 }}>
          Each power has a distinct benefit, meaning the advantage the leader enjoys, and a distinct
          barrier, meaning the reason a rival cannot copy it. Each also tends to arise at a particular
          stage of a business&rsquo;s life. <strong>Origination</strong> is where the model is still being
          formed, <strong>Take-off</strong> is rapid growth, and <strong>Stability</strong> is maturity.
          Knowing which stage a platform is in tells you which powers are even available to it.
        </p>
        <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "grid", gap: "0.75rem" }}>
          {POWERS.map((p) => {
            const g = POWER_GUIDANCE[p.key];
            if (!g) return null; // every registry power has guidance (asserted by a test); type guard
            return (
              <li key={p.key} className="card" style={{ padding: "1rem 1.15rem" }}>
                <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", gap: "0.75rem", flexWrap: "wrap" }}>
                  <span style={{ fontFamily: "var(--font-serif)", fontWeight: 600, fontSize: "1.05rem" }}>{p.name}</span>
                  <span className="tag" style={{ fontSize: "0.68rem" }}>{LIFECYCLE_LABEL[p.lifecycle]}</span>
                </div>
                <dl style={{ margin: "0.5rem 0 0", display: "grid", gap: "0.35rem", fontSize: "0.88rem", lineHeight: 1.5 }}>
                  <div style={{ display: "grid", gridTemplateColumns: "5rem 1fr", gap: "0.5rem" }}>
                    <dt style={{ color: "var(--color-accent)", fontWeight: 600 }}>Benefit</dt>
                    <dd style={{ margin: 0, color: "var(--color-ink-muted)" }}>{g.benefitHint}</dd>
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "5rem 1fr", gap: "0.5rem" }}>
                    <dt style={{ color: "var(--color-accent)", fontWeight: 600 }}>Barrier</dt>
                    <dd style={{ margin: 0, color: "var(--color-ink-muted)" }}>{g.barrierHint}</dd>
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "5rem 1fr", gap: "0.5rem" }}>
                    <dt style={{ color: "var(--color-ink-soft)" }}>Example</dt>
                    <dd style={{ margin: 0, color: "var(--color-ink-soft)", fontStyle: "italic" }}>{g.example}</dd>
                  </div>
                </dl>
              </li>
            );
          })}
        </ul>
        <p style={{ marginTop: "0.9rem", fontSize: "0.9rem", color: "var(--color-ink-muted)", lineHeight: 1.55 }}>
          The rule from the previous section applies to every one of these. The score is whichever of
          benefit and barrier is weaker, so a textbook benefit sitting behind a barrier a rival can cross
          in a quarter is not a power at all.
        </p>
      </section>

      {/* Reading the outputs (GRS-0096, rewritten in GRS-0175 so the notation is defined first) */}
      <section id="reading-outputs">
        <SectionTitle kicker="Reading the outputs">Reading the outputs</SectionTitle>
        <div style={{ display: "grid", gap: "1.1rem" }}>
          <div>
            <h3 style={{ margin: "0 0 0.3rem", fontSize: "1rem" }}>What a modelled range is</h3>
            <p style={{ margin: 0, color: "var(--color-ink-muted)", lineHeight: 1.6 }}>
              Every input you enter carries an evidence grade that says how well supported it is. To
              turn that into an honest picture, the tool re-samples each input within the confidence
              its grade allows and re-scores the whole assessment many times over. The result is not
              one number but a spread of possible scores. That spread is the modelled range, and it is
              how the assessment shows its own confidence: strong, well-graded evidence produces a
              narrow spread, and thin or weakly graded evidence produces a wide one.
            </p>
          </div>
          <div>
            <h3 style={{ margin: "0 0 0.3rem", fontSize: "1rem" }}>P10, P50, and P90, in plain words</h3>
            <p style={{ margin: 0, color: "var(--color-ink-muted)", lineHeight: 1.6 }}>
              From that spread of re-scored results, three points are reported. <strong>P50</strong> is
              the median: the value that half of the re-scored results fall below and half fall above,
              so it is the middle of the spread. <strong>P10</strong> is the value that ten percent of
              the results fall below, and <strong>P90</strong> the value that ninety percent fall below.
              Together, P10 to P90 is the likely range: the assessment is fairly confident the true
              score sits between them. A wider P10 to P90 gap means less certainty, because the evidence
              behind it was thinner or more weakly graded.
            </p>
            <div style={{ marginTop: "0.75rem" }}>
              <RangeStrip />
            </div>
          </div>
          <div>
            <h3 style={{ margin: "0 0 0.3rem", fontSize: "1rem" }}>The headline is one number, and it never moves</h3>
            <p style={{ margin: 0, color: "var(--color-ink-muted)", lineHeight: 1.6 }}>
              The headline always quotes the deterministic score: the single value the engine computes
              directly from your inputs, the same value a finalised assessment locks in. The range from
              the re-scoring is shown around it as the honesty band, so you can see how much the
              evidence lets the number move. The headline and the range never disagree, because the
              headline is the point and the range is the context around that same point. When an input
              has no evidence grade, the score cannot be re-sampled, so it is shown as a labelled point
              rather than a falsely narrow range. Quote the range to a technical audience, because the
              single number on its own overstates how precise the assessment is.
            </p>
          </div>
          <div>
            <h3 style={{ margin: "0 0 0.3rem", fontSize: "1rem" }}>What the rating word is for, and what the score is for</h3>
            <p style={{ margin: 0, color: "var(--color-ink-muted)", lineHeight: 1.6 }}>
              Each module carries a rating in words, from Basic to Frontier, and that word comes from
              rules rather than from rounding the score. The word is what a client understands and what
              you defend in a meeting. The continuous score underneath it, which is more precise, is
              what decides which weakness to fix first. So a module can carry a respectable-looking
              number and still be rated Developing, because a critical part of it is weak. That is the
              design rather than a fault. Use the word to communicate and the score to decide the order
              of the work.
            </p>
          </div>
          <div>
            <h3 style={{ margin: "0 0 0.3rem", fontSize: "1rem" }}>The bottleneck sets the score</h3>
            <p style={{ margin: 0, color: "var(--color-ink-muted)", lineHeight: 1.6 }}>
              The weakest critical element caps the whole. A module cannot be rated Advanced if a
              critical part of it is Basic, however strong everything else is, in the same way that a
              chain is only as strong as its weakest link. This is why the headline word can sit below
              what a plain average would suggest, and why the fix that moves the score most is usually
              the bottleneck rather than the part that is already strong.
            </p>
          </div>
          <div>
            <h3 style={{ margin: "0 0 0.3rem", fontSize: "1rem" }}>The value bridge: how a gap is priced</h3>
            <p style={{ margin: 0, color: "var(--color-ink-muted)", lineHeight: 1.6 }}>
              Money is kept in three separate layers that never collapse into one number: the cost to
              upgrade, in pounds; the cash-flow levers it moves, each expressed as a net present value
              on the client&rsquo;s own baselines, in pounds; and the strategic value, stated in words.
              The Upgrade Priority Index says what to do first, and the value bridge says what it is
              worth. Platform Power never says that a score gap is worth a given number of pounds,
              because dividing a score directly into money is the one move that fails technical due
              diligence.
            </p>
          </div>
        </div>
      </section>

      {/* Mistakes */}
      <section id="mistakes">
        <SectionTitle kicker="What gets an assessment rejected">Mistakes to avoid, and why they matter</SectionTitle>
        <ol style={{ listStyle: "none", margin: 0, padding: 0, display: "grid", gap: "0.75rem" }}>
          {MISTAKES.map((m, i) => (
            <li key={m.mistake} style={{ display: "grid", gridTemplateColumns: "1.6rem 1fr", gap: "0.75rem" }}>
              <span
                aria-hidden
                className="mono"
                style={{ width: "1.6rem", height: "1.6rem", borderRadius: "5px", background: "var(--color-accent-tint)", color: "var(--color-accent)", display: "grid", placeItems: "center", fontSize: "0.78rem", fontWeight: 600 }}
              >
                {i + 1}
              </span>
              <span>
                <span style={{ display: "block", fontWeight: 500, lineHeight: 1.5 }}>{m.mistake}</span>
                <span style={{ display: "block", color: "var(--color-ink-muted)", fontSize: "0.9rem", marginTop: "0.15rem", lineHeight: 1.5 }}>
                  {m.why}
                </span>
              </span>
            </li>
          ))}
        </ol>
      </section>

      {/* Scoring, explained in full (GRS-0175): the composite + per-segment weights, at reader
          depth, pointing at the reviewable maths document. */}
      <section id="scoring-explained">
        <SectionTitle kicker="The maths, briefly">Scoring, explained in full</SectionTitle>
        <div style={{ display: "grid", gap: "0.9rem" }}>
          <p style={{ margin: 0, color: "var(--color-ink-muted)", lineHeight: 1.6 }}>
            Platform Value is a weighted average of the three lens scores. Written out, that is{" "}
            <strong>V = θ_B · B + θ_P · P + θ_L · L</strong>, where each θ (the Greek letter theta) is
            the weight given to one lens. The three weights add up to one, and they are not the same for
            every kind of firm, because what drives value differs by segment. These are the weights the
            engine uses today.
          </p>
          <div style={{ overflowX: "auto" }}>
            <table style={{ borderCollapse: "collapse", fontSize: "0.9rem", minWidth: "26rem" }}>
              <thead>
                <tr style={{ textAlign: "left", color: "var(--color-ink-muted)", fontSize: "0.78rem" }}>
                  <th style={{ padding: "0.35rem 0.7rem" }}>Operating model</th>
                  <th style={{ padding: "0.35rem 0.7rem" }}>Business (θ_B)</th>
                  <th style={{ padding: "0.35rem 0.7rem" }}>Powers (θ_P)</th>
                  <th style={{ padding: "0.35rem 0.7rem" }}>Infrastructure (θ_L)</th>
                </tr>
              </thead>
              <tbody className="mono">
                <tr style={{ borderTop: "1px solid var(--color-border)" }}>
                  <td style={{ padding: "0.35rem 0.7rem" }}>Retail brokerage (draft)</td>
                  <td style={{ padding: "0.35rem 0.7rem" }}>0.30</td>
                  <td style={{ padding: "0.35rem 0.7rem" }}>0.30</td>
                  <td style={{ padding: "0.35rem 0.7rem" }}>0.40</td>
                </tr>
                <tr style={{ borderTop: "1px solid var(--color-border)" }}>
                  <td style={{ padding: "0.35rem 0.7rem" }}>Wealth advisory (starter)</td>
                  <td style={{ padding: "0.35rem 0.7rem" }}>0.45</td>
                  <td style={{ padding: "0.35rem 0.7rem" }}>0.30</td>
                  <td style={{ padding: "0.35rem 0.7rem" }}>0.25</td>
                </tr>
                <tr style={{ borderTop: "1px solid var(--color-border)" }}>
                  <td style={{ padding: "0.35rem 0.7rem" }}>Exchange / infrastructure (starter)</td>
                  <td style={{ padding: "0.35rem 0.7rem" }}>0.30</td>
                  <td style={{ padding: "0.35rem 0.7rem" }}>0.37</td>
                  <td style={{ padding: "0.35rem 0.7rem" }}>0.33</td>
                </tr>
              </tbody>
            </table>
          </div>
          <p style={{ margin: 0, color: "var(--color-ink-muted)", lineHeight: 1.6 }}>
            In wealth advisory the franchise economics lead, so Business carries the most weight and
            Infrastructure is trimmed, because there it is largely hygiene whose cost is already priced
            into the Business figures. For an exchange the moat matters most, so Powers is the top term.
            The retail weights are a uniform draft and are still awaiting elicitation, which is why they
            are labelled as draft on screen. The Customer Proposition index is reported alongside
            Platform Value rather than folded into it.
          </p>
          <p style={{ margin: 0, color: "var(--color-ink-muted)", lineHeight: 1.6 }}>
            The full and reviewable account of the maths, covering the composite, module maturity, the
            uncertainty model, and how Hamilton Helmer&rsquo;s framework maps onto it, is in{" "}
            <code>docs/ATLAS-Scoring-Explained.md</code>.
          </p>
          {/* GRS-0237 scope 5. The explainer answers "how does this work?"; a client's CTO asks the
              harder question, "is it any good?" — and that one has its own document now. Named here
              rather than only in the explainer because the advisor who needs it is usually the one
              who has just been asked, and will not think to go via a second hop. */}
          <p style={{ margin: 0, color: "var(--color-ink-muted)", lineHeight: 1.6 }}>
            When a client puts a CTO or a diligence team across the table, the document to hand them
            is the technical white paper, <code>docs/ATLAS-White-Paper-v1.md</code>. It carries the
            formal model, the validation evidence, and a limitations register that states what is
            not yet proven — written expecting the other side to check it.
          </p>
        </div>
      </section>

      {/* Working the app — the walkthroughs merged from the former /help page (GRS-0175). */}
      <section id="working-the-app">
        <SectionTitle kicker="Working the app">From a first prospect to a paid engagement</SectionTitle>
        <p style={{ margin: "0 0 1.4rem", color: "var(--color-ink-muted)", lineHeight: 1.6 }}>
          Everything above is the framework. This second half is the practical walk through the studio
          itself, from a first prospect to a finalised assessment, a client deliverable, and the
          commission that follows.
        </p>
        <div style={{ display: "grid", gap: "2rem" }}>
          {WALKTHROUGHS.map((w) => (
            <div key={w.id} id={w.id} style={{ scrollMarginTop: "5rem" }}>
              <p className="eyebrow">{w.kicker}</p>
              <h3 style={{ fontSize: "1.15rem", margin: "0.35rem 0 0.5rem" }}>{w.title}</h3>
              <p style={{ margin: 0, color: "var(--color-ink-muted)", lineHeight: 1.6 }}>{w.lead}</p>
              <StepList steps={w.steps} />
              {w.note ? (
                <div className={w.note.tone === "warn" ? "callout callout-warn" : "callout callout-info"} style={{ marginTop: "1rem" }}>
                  {w.note.text}
                </div>
              ) : null}
              {w.href ? (
                <p style={{ marginTop: "1rem" }}>
                  <Link href={w.href.to} className="btn btn-secondary">
                    {w.href.label} →
                  </Link>
                </p>
              ) : null}
            </div>
          ))}
        </div>
      </section>

      {/* Principles */}
      <section id="principles">
        <SectionTitle kicker="The rules that never bend">Principles</SectionTitle>
        <p style={{ margin: "0 0 1.2rem", color: "var(--color-ink-muted)", maxWidth: "44rem", lineHeight: 1.6 }}>
          Four commitments shape everything above, and they are the reason a Grassmarket assessment
          holds up in the room.
        </p>
        <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "grid", gap: "1rem", gridTemplateColumns: "repeat(auto-fill, minmax(18rem, 1fr))" }}>
          {PRINCIPLES.map((p) => (
            <li key={p.title} className="card" style={{ padding: "1.1rem 1.25rem" }}>
              <h3 style={{ fontFamily: "var(--font-serif)", fontSize: "1.05rem", margin: "0 0 0.35rem" }}>{p.title}</h3>
              <p style={{ margin: 0, color: "var(--color-ink-muted)", fontSize: "0.92rem", lineHeight: 1.55 }}>{p.body}</p>
            </li>
          ))}
        </ul>
      </section>

      <footer style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap", paddingTop: "0.5rem" }}>
        <Link href="/assessments" className="btn btn-primary">
          Start an assessment
        </Link>
        <Link href="/" className="btn btn-secondary">
          Back to dashboard
        </Link>
      </footer>
    </article>
  );
}
