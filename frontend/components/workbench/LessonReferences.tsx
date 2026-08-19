/**
 * Cited sources (GRS-0190, restyled GRS-0239).
 *
 * A reference is a claim about where the material came from, so the display shows the kind and the
 * host rather than only a title: a reader can tell a vendor's own documentation from a blog post
 * before they click.
 *
 * **Two presentations, because the same data plays two roles.** The founder's complaint was that
 * the lessons "just tell me what I should learn ... it just reference links" — and 139 of OpenBB's
 * 196 slides carry references, each of which rendered a strip of link *cards* under the slide body.
 * Sourcing every claim is doctrine and stays; a card strip on every slide made each slide look like
 * a pointer somewhere else rather than the teaching itself.
 *
 * So: `variant="footnote"` (the default on a slide) is one quiet line that expands on demand, and
 * `variant="cards"` is the original strip, used where sources ARE the point — at the end of a
 * lesson, where a reader has finished and is looking for what to read next.
 */

import { hostOf } from "@/lib/markdown";
import type { SourceRef, SourceRefKind } from "@/lib/types";

const KIND_LABEL: Record<SourceRefKind, string> = {
  docs: "Docs",
  video: "Video",
  blog: "Article",
  repo: "Repo",
};

export function LessonReferences({
  references,
  variant = "cards",
}: {
  references: readonly SourceRef[];
  variant?: "cards" | "footnote";
}) {
  if (references.length === 0) return null;
  if (variant === "footnote") return <ReferenceFootnote references={references} />;
  return (
    <section style={{ marginTop: "1rem" }}>
      <p className="mono" style={{ margin: "0 0 0.4rem", fontSize: "0.66rem", letterSpacing: "0.08em", textTransform: "uppercase", color: "var(--color-ink-faint)" }}>
        Sources
      </p>
      <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "grid", gap: "0.4rem" }}>
        {references.map((reference) => (
          <li key={`${reference.kind}:${reference.url}`}>
            <a
              href={reference.url}
              target="_blank"
              rel="noopener noreferrer"
              className="card"
              style={{ display: "flex", alignItems: "baseline", gap: "0.6rem", padding: "0.55rem 0.8rem", textDecoration: "none", flexWrap: "wrap" }}
            >
              <span className="tag" style={{ fontSize: "0.64rem", flex: "none" }}>
                {KIND_LABEL[reference.kind]}
              </span>
              <span style={{ fontSize: "0.86rem", fontWeight: 500 }}>{reference.title}</span>
              <span className="mono" style={{ fontSize: "0.7rem", color: "var(--color-ink-faint)", marginLeft: "auto" }}>
                {hostOf(reference.url)} ↗
              </span>
            </a>
          </li>
        ))}
      </ul>
    </section>
  );
}


/**
 * The quiet form: one line, expanding to the same links.
 *
 * Native `<details>` rather than a hand-rolled disclosure — it is keyboard-operable and
 * screen-reader-announced for free, and this is a footnote, not a place to spend a11y budget
 * re-implementing a built-in.
 */
function ReferenceFootnote({ references }: { references: readonly SourceRef[] }) {
  const hosts = Array.from(new Set(references.map((r) => hostOf(r.url))));
  return (
    <details style={{ marginTop: "0.7rem" }} data-testid="reference-footnote">
      <summary
        style={{ fontSize: "0.72rem", color: "var(--color-ink-faint)", cursor: "pointer" }}
      >
        {references.length === 1 ? "Source" : `${references.length} sources`}
        {": "}
        {hosts.slice(0, 2).join(", ")}
        {hosts.length > 2 ? ` +${hosts.length - 2}` : ""}
      </summary>
      <ul style={{ listStyle: "none", margin: "0.4rem 0 0", padding: 0, display: "grid", gap: "0.25rem" }}>
        {references.map((reference) => (
          <li key={`${reference.kind}:${reference.url}`} style={{ fontSize: "0.76rem" }}>
            <a href={reference.url} target="_blank" rel="noopener noreferrer">
              {reference.title}
            </a>{" "}
            <span className="mono" style={{ fontSize: "0.68rem", color: "var(--color-ink-faint)" }}>
              {KIND_LABEL[reference.kind]} · {hostOf(reference.url)} ↗
            </span>
          </li>
        ))}
      </ul>
    </details>
  );
}
