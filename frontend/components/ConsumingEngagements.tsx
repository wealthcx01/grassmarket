/**
 * The reverse of the engagement→assessment link (GRS-0116): shows which engagement(s) consume THIS
 * assessment, with a link back to each, so neither screen dead-ends into the other. Filters the
 * advisor's own engagements client-side — no new endpoint, and owner-scoping is inherited from
 * `listEngagements`. Renders nothing when the assessment isn't linked anywhere yet.
 */

"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { Engagement } from "@/lib/types";

export function ConsumingEngagements({ assessmentId }: { assessmentId: string }) {
  const [items, setItems] = useState<Engagement[] | null>(null);

  useEffect(() => {
    const ctrl = new AbortController();
    api
      .listEngagements(ctrl.signal)
      .then((all) => setItems(all.filter((e) => e.assessment_ids.includes(assessmentId))))
      .catch(() => setItems([])); // non-fatal — the wizard works regardless of this reverse view
    return () => ctrl.abort();
  }, [assessmentId]);

  if (!items || items.length === 0) return null;

  return (
    <p style={{ margin: "0.35rem 0 0", fontSize: "0.82rem", color: "var(--color-ink-muted)" }}>
      Consumed by {items.length === 1 ? "engagement" : "engagements"}:{" "}
      {items.map((e, i) => (
        <span key={e.id}>
          {i > 0 ? ", " : ""}
          <Link href={`/engagements/${e.id}`} style={{ fontWeight: 500 }}>
            {e.title}
          </Link>
        </span>
      ))}
    </p>
  );
}
