"use client";

/**
 * Rating Committee (GRS-0021/0027) — members-only. Sign-off happens in the context of a specific
 * assessment (the committee queue is per-assessment, on the assessment's page), so this panel is the
 * members' entry point and explainer. Its very presence is role-gated: the Workbench only mounts it
 * for a committee member or admin, mirroring the server gate (a non-member's decide call is a 403).
 */

import Link from "next/link";

export function CommitteePanel() {
  return (
    <section style={{ display: "flex", flexDirection: "column", gap: "0.8rem" }}>
      <h3 style={{ fontSize: "1rem", margin: 0 }}>Rating committee</h3>
      <p style={{ fontSize: "0.85rem", color: "var(--color-ink-muted)", margin: 0, maxWidth: "40rem" }}>
        You are a committee member. High-stakes ratings (a module gated Frontier, or a power rated
        Wide) need peer sign-off before an assessment can finalise (Methodology §8). Open an
        assessment awaiting sign-off to record your approve / reject decision — you cannot decide on
        your own assessment (peer challenge).
      </p>
      <Link href="/assessments" style={{ fontSize: "0.85rem", fontWeight: 500 }}>
        Go to assessments →
      </Link>
    </section>
  );
}
