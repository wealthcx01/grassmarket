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

async function fetchReport(token: string): Promise<SharedReportPayload | null> {
  const base =
    process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/+$/, "") ?? "http://localhost:8000";
  try {
    const response = await fetch(`${base}/shared/report/${encodeURIComponent(token)}`, {
      cache: "no-store", // a revoked link must stop working NOW, not at the next cache expiry
    });
    if (!response.ok) return null;
    return (await response.json()) as SharedReportPayload;
  } catch {
    return null;
  }
}

export default async function SharedReportPage({
  params,
}: {
  params: Promise<{ token: string }>;
}) {
  const { token } = await params;
  const payload = await fetchReport(token);

  if (!payload) {
    return (
      <main className="shared-report-shell">
        <div className="shared-report-missing">
          <p className="eyebrow">Bruntsfield Advisory Network</p>
          <h1>This report is not available</h1>
          <p>
            The link may have expired or been withdrawn. Please ask your Bruntsfield contact for a
            new one.
          </p>
        </div>
      </main>
    );
  }

  return (
    <main className="shared-report-shell">
      <SharedReport payload={payload} token={token} />
    </main>
  );
}
