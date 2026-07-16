import Link from "next/link";
import type { Metadata } from "next";

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

const GRADES: ReadonlyArray<{ grade: string; meaning: string }> = [
  { grade: "E1", meaning: "The client told you, and that's all you have." },
  { grade: "E2", meaning: "You probed it in a structured interview with the owner." },
  { grade: "E3", meaning: "You saw the artifact — document, dashboard, config, metric." },
  { grade: "E4", meaning: "You watched it work / inspected it yourself." },
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

      {/* Evidence grades */}
      <section>
        <SectionTitle kicker="How sure are you?">Evidence grades drive the ranges</SectionTitle>
        <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "grid", gap: "0.5rem", gridTemplateColumns: "repeat(auto-fit, minmax(13rem, 1fr))" }}>
          {GRADES.map((g) => (
            <li key={g.grade} className="card" style={{ padding: "0.8rem 0.95rem" }}>
              <span className="tag" style={{ background: "var(--color-accent-tint)", color: "var(--color-accent)", borderColor: "var(--color-accent-tint-border)" }}>{g.grade}</span>
              <p style={{ margin: "0.5rem 0 0", fontSize: "0.86rem", color: "var(--color-ink-muted)", lineHeight: 1.45 }}>{g.meaning}</p>
            </li>
          ))}
        </ul>
        <p style={{ marginTop: "0.9rem", fontSize: "0.9rem", color: "var(--color-ink-muted)" }}>
          This isn&rsquo;t bureaucracy — it drives the output. E1 ratings make the ranges wide; E4 makes them tight.
          The difference between a £25k assessment and a £75k one is largely the evidence grade you achieve.
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

      {/* Outputs */}
      <section>
        <SectionTitle kicker="Reading the outputs">Numbers rank; words rate</SectionTitle>
        <p style={{ margin: "0 0 0.6rem", color: "var(--color-ink-muted)", lineHeight: 1.6 }}>
          Scores are <strong>ranges, not points</strong> — &ldquo;V = 61 (55–68)&rdquo;. Never quote a bare point score;
          the range is the honest answer. The continuous scores decide <em>what to fix first</em>; the headline words
          (Basic→Frontier per module) are <em>what you defend in the boardroom</em>, and they come from rules, not
          arithmetic — a module can&rsquo;t be Advanced if a critical part is Basic.
        </p>
        <p style={{ margin: 0, color: "var(--color-ink-muted)", lineHeight: 1.6 }}>
          On money, Platform Power keeps three layers apart and never says &ldquo;your score gap is worth £X&rdquo;: the{" "}
          <strong>cost</strong> of an upgrade, the <strong>cash-flow levers</strong> it moves (each an NPV on the
          client&rsquo;s own baselines), and the <strong>strategic value</strong> (stated in words). The Upgrade Priority
          Index says <em>what first</em>; the value bridge says <em>what it&rsquo;s worth</em>. Never divide one by the other.
        </p>
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
