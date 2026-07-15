/**
 * Committee review of one assessment (GRS-0061). A committee member reaches this from the Workbench
 * Committee tab; unlike the owner's wizard, it loads through the committee-accessible queue endpoint
 * (`get_assessment_for_committee`), so a reviewer can sign off an assessment that isn't theirs.
 */

"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";

import { CommitteeReviewPanel } from "@/components/CommitteeReviewPanel";
import { getToken } from "@/lib/api";
import { getSession } from "@/lib/session";

export default function CommitteeReviewPage() {
  const router = useRouter();
  const params = useParams<{ assessmentId: string }>();
  const assessmentId = params.assessmentId;
  const [ready, setReady] = useState(false);
  const [allowed, setAllowed] = useState(false);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    // The committee surface is for committee members / admins; a plain consultant has no work here.
    setAllowed(getSession()?.isCommittee ?? false);
    setReady(true);
  }, [router]);

  if (!ready) return <p>Loading…</p>;
  if (!allowed) {
    return (
      <div style={{ maxWidth: "40rem" }}>
        <p className="eyebrow">Rating committee</p>
        <h1 style={{ margin: "0.3rem 0 0.6rem" }}>Committee review</h1>
        <p style={{ color: "var(--color-ink-muted)" }}>
          This surface is for Rating Committee members. If you own this assessment, its sign-off
          status is shown on the assessment&rsquo;s Summary step.
        </p>
        <p style={{ marginTop: "1rem" }}>
          <Link href="/workbench" className="btn btn-secondary">
            ← Back to the Workbench
          </Link>
        </p>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem", maxWidth: "44rem" }}>
      <div>
        <Link href="/workbench" style={{ fontSize: "0.82rem" }}>
          ← Workbench · Committee
        </Link>
        <p className="eyebrow" style={{ marginTop: "0.5rem" }}>
          Rating committee · sign-off
        </p>
        <h1 style={{ fontSize: "1.6rem", margin: "0.3rem 0 0.4rem" }}>Review high-stakes ratings</h1>
        <p style={{ margin: 0, color: "var(--color-ink-muted)", fontSize: "0.92rem", lineHeight: 1.55 }}>
          Approve or reject each high-stakes rating with a recorded rationale (§8). Peer challenge:
          you can never sign off your own assessment.
        </p>
      </div>
      <CommitteeReviewPanel assessmentId={assessmentId} />
    </div>
  );
}
