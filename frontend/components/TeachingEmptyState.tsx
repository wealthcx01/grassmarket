/**
 * An empty state that teaches (GRS-0243 scope 4).
 *
 * "No engagements yet." states the obvious and teaches nothing — a first-time user is looking at an
 * empty page precisely because they do not know what fills it. The founder walked every section of
 * the studio and could not tell, from the sections themselves, what any of them was for.
 *
 * Every empty state built with this says three things, in this order, because that is the order the
 * questions arrive in:
 *
 * 1. **What this section is** — one line, and never "you have no X", which is the fact they can
 *    already see.
 * 2. **Where its contents come from** — the chain or the upstream action, named explicitly, because
 *    the reason the page is empty is almost always a step that has not happened somewhere else.
 * 3. **The one thing to do next** — a single link. Two competing calls to action on an empty page
 *    is a choice offered to someone with no basis for making it.
 *
 * Extracted from the Deliverables empty state rather than invented: that one was written first,
 * worked, and would otherwise have been copy-pasted into three more pages and then drifted.
 */

import Link from "next/link";
import type { ReactNode } from "react";

export function TeachingEmptyState({
  testId,
  headline,
  explanation,
  action,
}: {
  testId: string;
  /** What this section is. Never "you have no X" — that is the fact they can already see. */
  headline: string;
  /** Where its contents come from. The chain, named. */
  explanation: ReactNode;
  /** The single next step. */
  action: { href: string; label: string; rest?: ReactNode };
}) {
  return (
    <div
      style={{
        border: "1px solid var(--color-rule)",
        borderRadius: "var(--radius)",
        padding: "1.25rem 1.4rem",
        maxWidth: "44rem",
      }}
      data-testid={testId}
    >
      <p style={{ margin: "0 0 0.6rem", fontWeight: 600 }}>{headline}</p>
      <p style={{ margin: "0 0 0.8rem", color: "var(--color-ink-muted)", lineHeight: 1.6 }}>
        {explanation}
      </p>
      <p style={{ margin: 0, lineHeight: 1.6 }}>
        <Link href={action.href} style={{ fontWeight: 600 }}>
          {action.label}
        </Link>
        {action.rest}
      </p>
    </div>
  );
}
