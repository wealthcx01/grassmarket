/**
 * Cited sources on a lesson, as link cards (GRS-0190).
 *
 * A reference is a claim about where the material came from, so the card shows the kind and the
 * host rather than only a title: a reader can see they are being sent to docs.openbb.co before
 * they click, and can tell a vendor's own documentation from a blog post.
 */

import { hostOf } from "@/lib/markdown";
import type { SourceRef, SourceRefKind } from "@/lib/types";

const KIND_LABEL: Record<SourceRefKind, string> = {
  docs: "Docs",
  video: "Video",
  blog: "Article",
  repo: "Repo",
};

export function LessonReferences({ references }: { references: readonly SourceRef[] }) {
  if (references.length === 0) return null;
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
