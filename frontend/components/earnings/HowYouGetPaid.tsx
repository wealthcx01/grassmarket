/**
 * The orienting block the earnings page never had (GRS-0240 scope 1).
 *
 * Walked as a zero-earnings first-time user, the page opened with five £0.00 cards — Earned YTD,
 * Pending, Invoiced, Paid, Projected unpaid — and never said what any of them meant or how money
 * moved between them. "Projected unpaid" was defined only in a contract docstring. The founder's
 * verdict was "the earnings page is so confusing", and the rates were never the problem: they are
 * right, config-driven, and read live from the schedule. The problem was that the page started with
 * answers to a question it had not asked.
 *
 * So this goes first, above every number.
 *
 * **On the letters.** "Stream A" and "Stream B" are kept and explained here, rather than dropped.
 * They are not only internal vocabulary: the downloadable statement (`earnings/statement.py`) prints
 * "Stream B" as a heading, so an advisor comparing the page to the document they were sent needs
 * the two to agree. What was wrong was labelling one stream and not the other — the worst of both
 * choices, since a lone "B" reads as leftover internals.
 */

const STATES: { name: string; meaning: string }[] = [
  {
    name: "Pending",
    meaning: "The work is done and the commission is yours, but the client has not been invoiced.",
  },
  {
    name: "Invoiced",
    meaning: "The client has been billed. Nothing more is needed from you.",
  },
  {
    name: "Paid",
    meaning: "The client has paid and the commission has been settled to you.",
  },
];

export function HowYouGetPaid() {
  return (
    <section
      data-testid="how-you-get-paid"
      style={{
        padding: "1rem 1.1rem",
        background: "var(--color-paper-raised)",
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius)",
        margin: "0 0 1.25rem",
      }}
    >
      <h2 style={{ fontSize: "1rem", margin: "0 0 0.5rem" }}>How you get paid</h2>

      <p style={{ margin: "0 0 0.8rem", fontSize: "0.86rem", maxWidth: "44rem" }}>
        You earn in two ways. <strong>Selling represented products</strong> — the vendor products
        Bruntsfield represents — pays a percentage of what the client spends
        (<span className="mono">Stream A</span> in your commission schedule).{" "}
        <strong>Delivering consulting</strong> — assessments and engagements you work on — pays a
        percentage of the engagement fee (<span className="mono">Stream B</span>). Both are read
        live from the commission schedule; nothing on this page is typed in by hand.
      </p>

      <p
        className="mono"
        style={{
          margin: "0 0 0.4rem",
          fontSize: "0.62rem",
          letterSpacing: "0.08em",
          textTransform: "uppercase",
          color: "var(--color-ink-faint)",
        }}
      >
        The life of a commission line
      </p>
      {/* An ordered list rather than a drawing: the sequence IS the explanation, it reads on a
          phone, and a screen reader gets it in the right order for free. */}
      <ol
        style={{
          listStyle: "none",
          margin: "0 0 0.7rem",
          padding: 0,
          display: "grid",
          gap: "0.35rem",
        }}
      >
        {STATES.map((state, index) => (
          <li key={state.name} style={{ fontSize: "0.84rem", display: "flex", gap: "0.6rem" }}>
            <span
              className="mono"
              style={{ color: "var(--color-accent)", flex: "0 0 auto", fontSize: "0.76rem" }}
            >
              {index + 1}
            </span>
            <span>
              <strong>{state.name}</strong> — {state.meaning}
            </span>
          </li>
        ))}
      </ol>

      <p style={{ margin: 0, fontSize: "0.82rem", color: "var(--color-ink-muted)", maxWidth: "44rem" }}>
        <strong>Earned YTD</strong> is everything that reached you this calendar year, in any state.{" "}
        <strong>Projected unpaid</strong> is pending plus invoiced — money that is owed to you and
        has not arrived yet. A line is created when an engagement or a product sale is recorded
        against you; you never enter one yourself.
      </p>
    </section>
  );
}

/** The one-line meaning shown on each stat card, so a £0.00 still says what it is (scope 4). */
export const STAT_DEFINITIONS: Record<string, string> = {
  "Earned YTD": "Everything earned this calendar year, in any state.",
  Pending: "Yours, not yet invoiced to the client.",
  Invoiced: "Billed to the client, not yet paid.",
  Paid: "Settled to you.",
  "Projected unpaid": "Pending plus invoiced — owed to you, not yet arrived.",
};
