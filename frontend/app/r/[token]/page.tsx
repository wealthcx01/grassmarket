/**
 * The public shared-report route (GRS-0220): `/r/<token>`.
 *
 * No login, no session — the token in the path is the credential. Fetched server-side so the report
 * is in the HTML on first paint: a client opening this on a phone should not watch a spinner, and
 * the page should be readable if JavaScript never arrives. Read tracking is the only part that
 * needs the client, and it degrades to simply not recording.
 *
 * An unknown, expired or revoked token all render the SAME "not available" page, because the API
 * deliberately makes them indistinguishable — telling a visitor that a link once existed and was
 * withdrawn is information they are not entitled to.
 */

import type { Metadata } from "next";

import { SharedReport, type SharedReportPayload } from "@/components/SharedReport";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Bruntsfield — platform assessment",
  // A shared client report must never be indexed: the link is the credential.
  robots: { index: false, follow: false, nocache: true },
};

/**
 * Why this distinguishes its failures.
 *
 * The first version returned null for everything and rendered "this report is not available". That
 * is correct for a link that is unknown, expired or revoked — the API makes those three
 * indistinguishable on purpose. It is WRONG for a network blip or a cold API: it tells a client
 * their report does not exist when the truth is that we could not reach it, and it leaves them
 * nothing to retry and us nothing to diagnose from a screenshot.
 *
 * Distinguishing them leaks nothing: a fetch that never got an answer says nothing about whether
 * the link is real.
 */
type FetchOutcome =
  | { kind: "ok"; payload: SharedReportPayload }
  | { kind: "gone" } // the API answered: unknown, expired or revoked
  | { kind: "unreachable" }; // we never got an answer

async function fetchReport(token: string): Promise<FetchOutcome> {
  const base =
    process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/+$/, "") ?? "http://localhost:8000";
  const url = `${base}/shared/report/${encodeURIComponent(token)}`;

  // Two attempts: a container that has just woken can drop the first request, and a client should
  // not have to know that.
  for (let attempt = 0; attempt < 2; attempt++) {
    try {
      const response = await fetch(url, {
        cache: "no-store", // a revoked link must stop working NOW, not at the next cache expiry
        signal: AbortSignal.timeout(8000),
      });
      if (response.status === 404) return { kind: "gone" };
      if (!response.ok) continue; // 5xx — worth one more try
      return { kind: "ok", payload: (await response.json()) as SharedReportPayload };
    } catch {
      // Timeout or transport failure. Fall through to the retry, then report it honestly.
    }
  }
  return { kind: "unreachable" };
}

export default async function SharedReportPage({
  params,
}: {
  params: Promise<{ token: string }>;
}) {
  const { token } = await params;
  const outcome = await fetchReport(token);

  if (outcome.kind === "unreachable") {
    return (
      <main className="shared-report-shell">
        <div className="shared-report-missing">
          <p className="eyebrow">Bruntsfield Advisory Network</p>
          <h1>We could not load this report</h1>
          <p>
            Your link is fine — we could not reach the service just now. Please refresh in a moment.
          </p>
          <p className="mono" style={{ fontSize: "0.75rem", color: "var(--color-ink-muted)" }}>
            reference: upstream-unreachable
          </p>
        </div>
      </main>
    );
  }

  if (outcome.kind === "gone") {
    return (
      <main className="shared-report-shell">
        <div className="shared-report-missing">
          <p className="eyebrow">Bruntsfield Advisory Network</p>
          <h1>This report is not available</h1>
          <p>
            The link may have expired or been withdrawn. Please ask your Bruntsfield contact for a
            new one.
          </p>
          <p className="mono" style={{ fontSize: "0.75rem", color: "var(--color-ink-muted)" }}>
            reference: link-not-active
          </p>
        </div>
      </main>
    );
  }

  // The fixed mark overlays the top of the viewport, so the shell reserves room for it. Driven
  // off the same payload flags the banner is, rather than a second source that could disagree.
  const marked = Boolean(outcome.payload.non_production || outcome.payload.draft);
  return (
    <main className={`shared-report-shell${marked ? " has-mark" : ""}`}>
      <SharedReport payload={outcome.payload} token={token} />
    </main>
  );
}
