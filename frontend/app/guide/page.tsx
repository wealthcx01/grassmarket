import Link from "next/link";
import type { Metadata } from "next";

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
  description: "A ten-minute primer on the Platform Power framework for new advisors.",
};

// The end-to-end pipeline (GRS-0092) — evidence in, board-defensible report out. Numbered because it
// genuinely is a sequence.
const PIPELINE: ReadonlyArray<{ step: string; detail: string }> = [
  {
    step: "Gather evidence and grade it",
    detail:
      "You learn how the platform works — from documents, interviews, dashboards, or your own inspection — and record how sure you are (E1–E4). The grade is not bureaucracy; it decides how wide the final ranges are.",
  },
  {
    step: "Rate each element against a rubric anchor",
    detail:
      "Every subcomponent gets a maturity level (Basic → Frontier) against a written anchor, every power a benefit and a barrier, every business metric a value against its normalisation curve. You judge; the anchor keeps two advisors consistent.",
  },
  {
    step: "The engine computes B, P and L",
    detail:
      "Each index is an evidence-weighted blend where the weakest critical part caps the score — a module can't outrun its bottleneck. Nothing is guessed or zero-filled: Not Assessed stays first-class and simply widens the uncertainty.",
  },
  {
    step: "Monte Carlo turns grades into honest ranges",
    detail:
      "Instead of a false-precise point, the engine simulates the assessment thousands of times within the bounds your evidence grades allow, and reports P10 / P50 / P90. Weak evidence → wide range, honestly.",
  },
  {
    step: "Rule-based gates produce the headline words",
    detail:
      "The words a board sees (Basic → Frontier per module, the triad ordinals) come from rules, not arithmetic: a module can't be Advanced if a critical part is Basic. Numbers rank what to fix; words rate what you defend.",
  },
  {
    step: "The value bridge prices the gaps",
    detail:
      "Upgrades are costed (£), the cash-flow levers they move are valued (NPV on the client's own baselines), and strategic worth is stated in words — never “your score gap is worth £X”. The result is the Platform Power Report a board can trust.",
  },
];

const LENSES: ReadonlyArray<{ letter: string; name: string; question: string }> = [
  { letter: "B", name: "Business", question: "What does this platform achieve economically? Hard numbers — AUA, revenue, margins, growth, acquisition costs." },
  { letter: "P", name: "Power", question: "What stops a competitor taking it away? Helmer's 7 Powers, each scored on benefit AND barrier." },
  { letter: "L", name: "Infrastructure · the technology Layer", question: "Is the plumbing an asset or a constraint? 9 modules, 51 subcomponents, front end to liquidity." },
  { letter: "V", name: "Platform Value", question: "The composite headline. But the number clients remember is usually the bottleneck — the weakest link." },
];

const LEVELS: ReadonlyArray<{ level: string; test: string }> = [
  { level: "Basic", test: "It barely exists. Manual, unreliable, or absent; people feel the pain regularly." },
  { level: "Developing", test: "It exists but you wouldn't trust it under pressure. Gaps, workarounds, single points of failure." },
  { level: "Advanced", test: "It reliably does its job. Automated, monitored, documented. Still improvable." },
  { level: "Frontier", test: "It's a competitive weapon, not just adequate. Not every firm needs it — and it should never be the universal target." },
];

// Evidence grades (GRS-0095): plain-English meaning + what actually qualifies + the source, so the
// weakest→strongest escalation (client-said → interview → artifact → observed) is obvious.
const GRADES: ReadonlyArray<{ grade: string; source: string; meaning: string; qualifies: string }> = [
  {
    grade: "E1",
    source: "Client-said",
    meaning: "The client told you, and that's all you have — an unverified claim.",
    qualifies: "A statement in a meeting or a form: “our uptime is 99.9%”, with nothing behind it yet.",
  },
  {
    grade: "E2",
    source: "Interview",
    meaning: "You probed it in a structured interview with the person who owns it.",
    qualifies: "You asked how, since when, who runs it, what breaks — and the answers held together.",
  },
  {
    grade: "E3",
    source: "Artifact",
    meaning: "You saw the thing itself — a document, dashboard, config, runbook, or metric.",
    qualifies: "A screenshot of the monitor, the incident log, the architecture diagram, the actual number.",
  },
  {
    grade: "E4",
    source: "Observed",
    meaning: "You watched it work or inspected it yourself — the strongest evidence.",
    qualifies: "You saw a deploy run, watched failover, or drove the system and confirmed it behaves as claimed.",
  },
];

const MISTAKES: readonly string[] = [
  "Scoring from memory instead of the rubric anchor.",
  "E1 evidence dressed up as certainty — wide ranges are fine; false precision is not.",
  "Avoiding “Not Assessed” by guessing. Guessing is the one thing the framework cannot survive.",
  "Powers scored on benefit alone, barrier unexamined.",
  "Frontier presented as the universal target.",
  "Quoting point scores without ranges.",
  "Converting score gaps straight to pounds — the one sentence that fails technical due diligence instantly.",
];

function SectionTitle({ kicker, children }: { kicker: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: "1rem" }}>
      <p className="eyebrow">{kicker}</p>
      <h2 style={{ margin: "0.3rem 0 0", fontSize: "1.35rem" }}>{children}</h2>
    </div>
  );
}

export default function GuidePage() {
  return (
    <article className="stack measure" style={{ gap: "2.5rem", margin: "0 auto" }}>
      <header>
        <p className="eyebrow">Advisor primer · Platform Power</p>
        <h1 style={{ margin: "0.4rem 0 0.6rem" }}>How Platform Power works</h1>
        <p style={{ margin: 0, fontSize: "1.05rem", color: "var(--color-ink-muted)", lineHeight: 1.6 }}>
          Platform Power turns what you learn about a client&rsquo;s platform into scores, ratings, and a
          modernisation plan a board can trust. Your judgment is the input; the framework&rsquo;s job is
          to make it consistent, comparable, and defensible. Here&rsquo;s the whole thing in ten minutes.
        </p>
      </header>

      {/* Why it exists (GRS-0092) */}
      <section>
        <SectionTitle kicker="The problem it solves">Why Platform Power exists</SectionTitle>
        <p style={{ margin: "0 0 0.75rem", color: "var(--color-ink-muted)", lineHeight: 1.6 }}>
          One question sits under every brokerage or fintech engagement: <strong>can this platform
          create value and hold onto it?</strong> Answering it well means looking at three things at
          once — the economics (does it make money?), the strategy (what stops a rival taking the
          business?), and the technology (is the plumbing an asset or a liability?). Most reviews look
          hard at one and hand-wave the other two.
        </p>
        <p style={{ margin: 0, color: "var(--color-ink-muted)", lineHeight: 1.6 }}>
          Platform Power scores all three on one comparable scale, from graded evidence, and prices the
          gaps honestly. The point is not to replace your judgement — it is your judgement, made{" "}
          <strong>consistent</strong> (two advisors reach the same score from the same facts),{" "}
          <strong>comparable</strong> (this platform against its peers and against last year), and{" "}
          <strong>defensible</strong> (it survives a board&rsquo;s — or an acquirer&rsquo;s — technical
          due diligence).
        </p>
      </section>

      {/* Where it comes from (GRS-0092) */}
      <section>
        <SectionTitle kicker="Provenance">Where the framework comes from</SectionTitle>
        <p style={{ margin: "0 0 0.75rem", color: "var(--color-ink-muted)", lineHeight: 1.6 }}>
          The strategy lens is not invented here. <strong>P (Power)</strong> is Hamilton Helmer&rsquo;s{" "}
          <em>7 Powers</em> — the modern canon on durable competitive advantage — used verbatim: seven
          structural sources of power, each real only when a genuine <em>benefit</em> is protected by a
          <em> barrier</em> a competitor cannot cheaply cross.
        </p>
        <p style={{ margin: 0, color: "var(--color-ink-muted)", lineHeight: 1.6 }}>
          <strong>L (Infrastructure · the technology Layer)</strong> comes from the infrastructure
          deep-dive lineage — a structured technology assessment of nine modules and fifty-one
          subcomponents, front end to liquidity, that turns &ldquo;is the plumbing an asset or a
          constraint?&rdquo; into evidence-graded ratings rather than opinion. <strong>B (Business)</strong>{" "}
          is the hard economic register — AUA, revenue, unit economics, growth. Bringing strategy,
          technology and economics under one graded, uncertainty-aware method is the whole idea:
          nothing is scored on gut feel, and nothing is priced by dividing a score gap into pounds.
        </p>
      </section>

      {/* How it works, end to end (GRS-0092) */}
      <section>
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
      <section>
        <SectionTitle kicker="The shape of it">Three lenses, one headline</SectionTitle>
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
          On top of these, the client sees the <strong>Platform Power triad</strong> — Economic, Perceived, and
          Defence Value — always as words (None / Emerging / Established / Wide), never decimals.
        </p>
      </section>

      {/* The lenses in depth — letter↔word mapping (GRS-0093) */}
      <section>
        <SectionTitle kicker="Reading the lenses">What the letters mean</SectionTitle>
        <p style={{ margin: "0 0 1rem", color: "var(--color-ink-muted)", lineHeight: 1.6 }}>
          A <strong>&ldquo;platform&rdquo;</strong> here is the whole operating system of a brokerage or
          fintech — its economics, its strategic position, and the technology that runs it.{" "}
          <strong>&ldquo;Platform Power&rdquo;</strong> is how much durable value that whole creates, which
          is why the headline is <strong>V, Platform Value</strong>. The letters are not arbitrary once you
          read them:
        </p>
        <dl style={{ margin: 0, display: "grid", gap: "0.9rem" }}>
          <div>
            <dt style={{ fontFamily: "var(--font-serif)", fontWeight: 600 }}>B — Business</dt>
            <dd style={{ margin: "0.15rem 0 0", color: "var(--color-ink-muted)", fontSize: "0.92rem", lineHeight: 1.55 }}>
              The economic reality: does it make money, and is that improving? AUA, revenue, unit
              economics, growth — the hard numbers, normalised so a £2bn platform and a £50m one compare
              fairly.
            </dd>
          </div>
          <div>
            <dt style={{ fontFamily: "var(--font-serif)", fontWeight: 600 }}>P — Power</dt>
            <dd style={{ margin: "0.15rem 0 0", color: "var(--color-ink-muted)", fontSize: "0.92rem", lineHeight: 1.55 }}>
              The letter is literally <em>Power</em>. Straight from Helmer&rsquo;s seven Powers: a power
              counts only when a real <strong>benefit</strong> is protected by a <strong>barrier</strong> a
              rival cannot cheaply cross — and the engine takes the <strong>weaker</strong> of the two.
            </dd>
          </div>
          <div>
            <dt style={{ fontFamily: "var(--font-serif)", fontWeight: 600 }}>L — Infrastructure · the technology Layer</dt>
            <dd style={{ margin: "0.15rem 0 0", color: "var(--color-ink-muted)", fontSize: "0.92rem", lineHeight: 1.55 }}>
              The letter is <em>Layer</em> — the technology layer under the business. Nine modules, front
              end to liquidity: is the plumbing an <strong>asset</strong> (a moat) or a{" "}
              <strong>constraint</strong> (a liability waiting to surface)?
            </dd>
          </div>
          <div>
            <dt style={{ fontFamily: "var(--font-serif)", fontWeight: 600 }}>V — Platform Value</dt>
            <dd style={{ margin: "0.15rem 0 0", color: "var(--color-ink-muted)", fontSize: "0.92rem", lineHeight: 1.55 }}>
              The composite headline that blends B, P and L. But the number a client remembers is usually
              the <strong>bottleneck</strong> — the weakest critical link, which no amount of strength
              elsewhere fully hides.
            </dd>
          </div>
        </dl>
        <p style={{ marginTop: "1rem", fontSize: "0.9rem", color: "var(--color-ink-muted)", lineHeight: 1.55 }}>
          Sitting on top, the <strong>Platform Power triad</strong> re-reads the same evidence as three
          plain words a board understands instantly: <strong>Economic</strong> value (is it worth money?),{" "}
          <strong>Perceived</strong> value (do customers feel it?), and <strong>Defence</strong> value (can
          it be protected?).
        </p>
      </section>

      {/* Four levels */}
      <section>
        <SectionTitle kicker="Rating infrastructure">The four maturity levels</SectionTitle>
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
        <p style={{ marginTop: "0.9rem", fontSize: "0.9rem", color: "var(--color-ink-muted)" }}>
          Two honest states sit outside the ladder: <strong>Not Applicable</strong> (out of scope — drops out of the
          maths) and <strong>Not Assessed</strong> (in scope but no evidence — never scored as zero, but it caps the
          module&rsquo;s ceiling and widens the uncertainty range). Marking things Not Assessed is professionalism, not failure.
        </p>
      </section>

      {/* Evidence grades (GRS-0095) */}
      <section>
        <SectionTitle kicker="How sure are you?">Evidence grades drive the ranges</SectionTitle>
        <p style={{ margin: "0 0 1rem", color: "var(--color-ink-muted)", lineHeight: 1.6 }}>
          Every rating carries a grade for <em>how you know</em>. The four climb from weakest to
          strongest — <strong>client-said → interview → artifact → observed</strong> — and each step up
          is a step from &ldquo;someone claimed it&rdquo; toward &ldquo;I saw it with my own eyes&rdquo;.
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
          This isn&rsquo;t bureaucracy — it drives the output. E1 ratings make the ranges wide; E4 makes them
          tight. A higher grade is stronger because it is <em>closer to the thing itself</em>: a claim can
          be wrong, a document can be stale, but something you watched work is hard to argue with. The
          difference between a £25k assessment and a £75k one is largely the evidence grade you achieve.
        </p>
      </section>

      {/* Powers: benefit and barrier */}
      <section>
        <SectionTitle kicker="Scoring the 7 Powers">Benefit and barrier — the weaker side wins</SectionTitle>
        <p style={{ margin: "0 0 0.75rem", color: "var(--color-ink-muted)", lineHeight: 1.6 }}>
          For each power you record a <strong>benefit</strong> (is there a real economic advantage?) and a{" "}
          <strong>barrier</strong> (what stops a competitor copying it?). <strong>The power&rsquo;s strength is
          whichever side is weaker.</strong> A brilliant benefit with no barrier is worth None — competitors just
          copy it. This is the single most common thing new advisors get wrong.
        </p>
        <p className="callout callout-warn">
          Every power is always scored — &ldquo;not applicable&rdquo; doesn&rsquo;t exist for powers. A power that&rsquo;s
          irrelevant to this business is simply weak, and that&rsquo;s information.
        </p>
      </section>

      {/* The seven Powers, one by one (GRS-0094) */}
      <section>
        <SectionTitle kicker="Helmer's seven">The seven Powers, one by one</SectionTitle>
        <p style={{ margin: "0 0 1rem", color: "var(--color-ink-muted)", lineHeight: 1.6 }}>
          Each has a distinct <strong>benefit</strong> (the advantage the leader enjoys) and{" "}
          <strong>barrier</strong> (why a rival can&rsquo;t copy it), and each tends to arise at a
          particular stage of a business&rsquo;s life — <strong>Origination</strong> (the model is being
          formed), <strong>Take-off</strong> (rapid growth), or <strong>Stability</strong> (maturity). Knowing
          the stage-fit tells you which powers are even <em>available</em> to a platform at its age.
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
          Remember the rule from above: for each of these, the score is the <strong>weaker</strong> of
          benefit and barrier. A textbook benefit with a barrier a rival can cross in a quarter is not a
          power — it&rsquo;s a head start.
        </p>
      </section>

      {/* Reading the outputs (GRS-0096) */}
      <section>
        <SectionTitle kicker="Reading the outputs">Reading the outputs</SectionTitle>
        <div style={{ display: "grid", gap: "1.1rem" }}>
          <div>
            <h3 style={{ margin: "0 0 0.3rem", fontSize: "1rem" }}>Ranges, not points</h3>
            <p style={{ margin: 0, color: "var(--color-ink-muted)", lineHeight: 1.6 }}>
              A result is a range — &ldquo;V = 61 (55&ndash;68)&rdquo; — never a bare number. The middle
              (P50) is the best estimate; the ends (P10 / P90) are how far it could reasonably sit given
              how good your evidence was. Weak evidence widens the range honestly; that is a feature, not a
              hedge. <strong>Quote the range, always.</strong> A point score alone is the fastest way to
              lose a technical audience.
            </p>
          </div>
          <div>
            <h3 style={{ margin: "0 0 0.3rem", fontSize: "1rem" }}>Words rate; numbers rank</h3>
            <p style={{ margin: 0, color: "var(--color-ink-muted)", lineHeight: 1.6 }}>
              Two outputs, two jobs. The <strong>rating</strong> — the headline <em>word</em> (Basic →
              Frontier per module, the triad ordinals) — is what a board understands and what you defend;
              it comes from <em>rules</em>, not arithmetic. The <strong>ranking</strong> — the continuous
              score — is what decides <em>what to fix first</em>. Use the word to communicate, the number
              to prioritise; don&rsquo;t swap their jobs.
            </p>
          </div>
          <div>
            <h3 style={{ margin: "0 0 0.3rem", fontSize: "1rem" }}>The bottleneck sets the score</h3>
            <p style={{ margin: 0, color: "var(--color-ink-muted)", lineHeight: 1.6 }}>
              The weakest <em>critical</em> element caps the whole. A module can&rsquo;t be Advanced if a
              critical part is Basic, however strong everything else is — just as a chain is only as strong
              as its weakest link. This is why the headline word can sit below what a simple average would
              suggest, and why the fix that moves the score most is usually the bottleneck, not the
              already-strong part.
            </p>
          </div>
          <div>
            <h3 style={{ margin: "0 0 0.3rem", fontSize: "1rem" }}>The value bridge — how a gap is priced</h3>
            <p style={{ margin: 0, color: "var(--color-ink-muted)", lineHeight: 1.6 }}>
              Money is kept in three layers that never collapse into one number: the <strong>cost</strong>{" "}
              to upgrade (£), the <strong>cash-flow levers</strong> it moves (each an NPV on the client&rsquo;s
              own baselines, £), and the <strong>strategic value</strong> (stated in words). The Upgrade
              Priority Index says <em>what to do first</em>; the value bridge says <em>what it&rsquo;s
              worth</em>. Platform Power never says &ldquo;your score gap is worth £X&rdquo; — dividing a
              score into pounds is the one sentence that fails technical due diligence instantly.
            </p>
          </div>
        </div>
      </section>

      {/* What calibration is (GRS-0130) */}
      <section>
        <SectionTitle kicker="Staying aligned">What a calibration session is</SectionTitle>
        <div className="card" style={{ padding: "1.15rem 1.3rem", display: "flex", flexDirection: "column", gap: "0.6rem" }}>
          <p style={{ margin: 0, color: "var(--color-ink-muted)", fontSize: "0.95rem", lineHeight: 1.6 }}>
            A <strong>calibration session</strong> is how assessors stay aligned so the same evidence
            earns the same rating no matter who scores it. A facilitator poses a set of shared
            vignettes — short, real assessment situations, drawn from the Academy courses (the Sales
            Egoist doctrine and the product content) rather than generic filler — and every
            participant rates them <em>blind</em>, without seeing the others&apos; answers.
          </p>
          <p style={{ margin: 0, color: "var(--color-ink-muted)", fontSize: "0.95rem", lineHeight: 1.6 }}>
            When the session closes, the ratings are revealed together and the spread is measured:
            where assessors diverged, the group discusses why and converges on the rubric&apos;s
            intent. Calibration is a <strong>governance</strong> control — its result is recorded —
            which is what makes it different from the Practice Arena, where the AI-drafted feedback
            is a self-only training aid, clearly labelled and never a recorded approval.
          </p>
        </div>
      </section>

      {/* Mistakes */}
      <section>
        <SectionTitle kicker="Don't do this">Mistakes that get assessments rejected</SectionTitle>
        <ol style={{ margin: 0, paddingLeft: "1.15rem", color: "var(--color-ink-muted)", lineHeight: 1.7, fontSize: "0.95rem" }}>
          {MISTAKES.map((m) => (
            <li key={m} style={{ marginBottom: "0.3rem" }}>{m}</li>
          ))}
        </ol>
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
