/**
 * The client report workspace (GRS-0219/0220 wiring).
 *
 * The advisor writes the six sections here, downloads the branded PDF, and issues the link a client
 * opens. Until this page existed the whole client-report stack was unreachable from the app — the
 * content model takes prose as an input, and there was nowhere to write it.
 *
 * Two things it deliberately does NOT do:
 *
 * - It does not draft for you. The narrative is a consultant's judgement about a business; the
 *   score cannot produce it, and generating filler would be the fabrication the content model
 *   refuses. GRS-0222 will offer a drafting assistant, gated by founder approval.
 * - It does not hide the refusal. A report with unwritten sections cannot be rendered or shared,
 *   and the backend's own sentence naming the missing sections is what the advisor sees.
 */

"use client";

import { use, useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

import { ApiError, api, getToken } from "@/lib/api";
import type { ClientReportLink, ReportProseSection, ReportReadReport } from "@/lib/types";

const SECTION_ORDER = [
  "business",
  "advantage",
  "constraint",
  "actions",
  "value",
  "appendix",
] as const;

/** What each section is for, in the advisor's words — the page teaches the shape of the argument. */
const SECTION_GUIDANCE: Record<string, string> = {
  business: "What this firm is and how it makes money, in plain prose. No score belongs here.",
  advantage: "Where durable advantage sits, through the Powers that apply — and where it does not.",
  constraint: "The honest reading of what is holding them back.",
  actions: "What to do about it, with the levers ranked.",
  value: "What that is worth if they act.",
  appendix: "Coefficients, weights, uncertainty method, coverage. P10/P50/P90 may ONLY appear here.",
};

function triggerBlobDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export default function ClientReportPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const router = useRouter();

  const [sections, setSections] = useState<Record<string, ReportProseSection> | null>(null);
  const [links, setLinks] = useState<ClientReportLink[]>([]);
  const [reads, setReads] = useState<Record<string, ReportReadReport>>({});
  const [issued, setIssued] = useState<{ token: string; label: string } | null>(null);
  const [recipient, setRecipient] = useState("");
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const refreshLinks = useCallback(
    async (signal?: AbortSignal) => {
      const rows = await api.listReportLinks(id, signal);
      setLinks(rows);
      const summaries: Record<string, ReportReadReport> = {};
      for (const link of rows) {
        try {
          summaries[link.id] = await api.reportLinkReads(link.id, signal);
        } catch {
          // A missing read summary must not blank the page; the link row still renders.
        }
      }
      setReads(summaries);
    },
    [id]
  );

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    const ctrl = new AbortController();
    api
      .getReportProse(id, ctrl.signal)
      .then((body) => setSections(body.sections))
      .then(() => refreshLinks(ctrl.signal))
      .catch((err: unknown) => {
        if (err instanceof ApiError && err.status === 0 && err.aborted) return;
        if (err instanceof ApiError && err.status === 401) return router.replace("/login");
        setError(err instanceof ApiError ? err.message : "Could not load this report.");
      });
    return () => ctrl.abort();
  }, [id, router, refreshLinks]);

  const setBody = (kind: string, text: string) => {
    setSections((current) => {
      if (!current) return current;
      const existing = current[kind] ?? { heading: kind, body: [], tier: "engaged" as const };
      return {
        ...current,
        // One paragraph per blank-line-separated block — the content model takes a list, and a
        // wall of text is not what a client should be sent.
        [kind]: { ...existing, body: text.split(/\n{2,}/).filter((p) => p.trim()) },
      };
    });
  };

  const save = async () => {
    if (!sections) return;
    setBusy(true);
    setError(null);
    try {
      await api.saveReportProse(id, sections);
      setStatus("Saved.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not save.");
    } finally {
      setBusy(false);
    }
  };

  const download = async () => {
    setBusy(true);
    setError(null);
    setStatus(null);
    try {
      const { blob, filename } = await api.downloadClientReportPdf(id);
      triggerBlobDownload(blob, filename);
      setStatus("PDF downloaded.");
    } catch (err) {
      // A 409 here is the content model refusing an unfinished report. Its sentence names the
      // missing sections, so it is shown as-is rather than replaced with "something went wrong".
      setError(err instanceof ApiError ? err.message : "Could not render the PDF.");
    } finally {
      setBusy(false);
    }
  };

  const share = async () => {
    if (!recipient.trim()) return;
    setBusy(true);
    setError(null);
    setStatus(null);
    try {
      const created = await api.createReportLink(id, { recipient_label: recipient.trim() });
      setIssued({ token: created.token, label: created.link.recipient_label });
      setRecipient("");
      await refreshLinks();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create a link.");
    } finally {
      setBusy(false);
    }
  };

  // Scope 3's other half. The refusal tells the advisor the report needs the founder; this is the
  // button that acts on it, in the same place they were stopped — an instruction with no affordance
  // beside it is a dead end dressed as guidance.
  const sendForReview = async () => {
    setBusy(true);
    setError(null);
    setStatus(null);
    try {
      await api.submitReportForReview(id);
      setStatus("Sent to the founder. It is in their review queue now.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not send it for review.");
    } finally {
      setBusy(false);
    }
  };

  const revoke = async (linkId: string) => {
    setBusy(true);
    try {
      await api.revokeReportLink(linkId);
      setStatus("Link revoked. It stopped working immediately.");
      await refreshLinks();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not revoke that link.");
    } finally {
      setBusy(false);
    }
  };

  if (error && !sections) {
    return (
      <main style={{ maxWidth: "var(--content-max)", margin: "0 auto", padding: "2rem 1.25rem" }}>
        <p role="alert">{error}</p>
      </main>
    );
  }
  if (!sections) {
    return (
      <main style={{ maxWidth: "var(--content-max)", margin: "0 auto", padding: "2rem 1.25rem" }}>
        <p>Loading the report…</p>
      </main>
    );
  }

  return (
    <main style={{ maxWidth: "var(--content-max)", margin: "0 auto", padding: "2rem 1.25rem 4rem" }}>
      <p className="eyebrow">Client report</p>
      <h1 style={{ fontSize: "2rem", margin: "0.3rem 0 0.4rem" }}>What the client reads</h1>
      <p style={{ margin: "0 0 1.5rem", color: "var(--color-ink-muted)", maxWidth: "42rem" }}>
        Six sections, in the order a client reads them: the business first, the score never on its
        own. The same words become the branded PDF and the shared web page, so the two cannot
        disagree in front of a client.{" "}
        <Link href="/deliverables">Back to deliverables</Link>
      </p>

      {error ? (
        <p role="alert" className="callout callout-error" style={{ marginBottom: "1rem" }}>
          {error}
        </p>
      ) : null}
      {status ? (
        <p role="status" style={{ color: "var(--color-accent)", marginBottom: "1rem" }}>
          {status}
        </p>
      ) : null}

      <section aria-labelledby="prose-h">
        <h2 id="prose-h" style={{ fontSize: "1.2rem" }}>
          The narrative
        </h2>
        {SECTION_ORDER.map((kind) => (
          <div key={kind} style={{ marginBottom: "1.25rem" }}>
            <label htmlFor={`s-${kind}`} style={{ display: "block", fontWeight: 500 }}>
              {sections[kind]?.heading ?? kind}
            </label>
            <p
              style={{
                margin: "0.15rem 0 0.35rem",
                fontSize: "0.82rem",
                color: "var(--color-ink-muted)",
              }}
            >
              {SECTION_GUIDANCE[kind]}
            </p>
            <textarea
              id={`s-${kind}`}
              value={(sections[kind]?.body ?? []).join("\n\n")}
              onChange={(e) => setBody(kind, e.target.value)}
              rows={4}
              style={{ width: "100%" }}
              placeholder="Blank lines separate paragraphs."
            />
          </div>
        ))}
        <button type="button" className="btn btn-primary" onClick={save} disabled={busy}>
          {busy ? "Working…" : "Save"}
        </button>
      </section>

      <section aria-labelledby="render-h" style={{ marginTop: "2.5rem" }}>
        <h2 id="render-h" style={{ fontSize: "1.2rem" }}>
          Give it to the client
        </h2>
        <p style={{ color: "var(--color-ink-muted)", fontSize: "0.9rem" }}>
          Both renditions come from the words above. A section left empty stops either from being
          produced — an unfinished report should not be able to look finished.
        </p>
        <button type="button" className="btn" onClick={download} disabled={busy}>
          Download the PDF
        </button>
        <button
          type="button"
          className="btn"
          onClick={sendForReview}
          disabled={busy}
          style={{ marginLeft: "0.5rem" }}
        >
          Send to the founder for review
        </button>

        <div style={{ marginTop: "1.5rem" }}>
          <label htmlFor="recipient" style={{ display: "block", fontWeight: 500 }}>
            Share a link
          </label>
          <p
            style={{
              margin: "0.15rem 0 0.4rem",
              fontSize: "0.82rem",
              color: "var(--color-ink-muted)",
            }}
          >
            No login for the client. The link is the credential, it expires in 30 days, and you can
            revoke it at any time.
          </p>
          <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
            <input
              id="recipient"
              type="text"
              value={recipient}
              onChange={(e) => setRecipient(e.target.value)}
              placeholder="Who is it for? e.g. cfo@client.com"
              style={{ flex: "1 1 18rem" }}
            />
            <button
              type="button"
              className="btn btn-primary"
              onClick={share}
              disabled={busy || !recipient.trim()}
            >
              Create link
            </button>
          </div>
        </div>

        {issued ? (
          <div className="callout" style={{ marginTop: "1rem" }}>
            <p style={{ margin: "0 0 0.3rem", fontWeight: 500 }}>
              Link for {issued.label} — copy it now.
            </p>
            <p style={{ margin: "0 0 0.4rem", fontSize: "0.85rem" }}>
              This is the only time it is shown. It is stored as a hash, so it cannot be shown
              again; if you lose it, issue a new one.
            </p>
            <code className="mono" style={{ wordBreak: "break-all" }}>
              {typeof window !== "undefined" ? window.location.origin : ""}/r/{issued.token}
            </code>
          </div>
        ) : null}

        {links.length ? (
          <table style={{ width: "100%", marginTop: "1.5rem", borderCollapse: "collapse" }}>
            <caption style={{ textAlign: "left", color: "var(--color-ink-muted)" }}>
              Links you have issued, and what was read
            </caption>
            <thead>
              <tr>
                <th scope="col" style={{ textAlign: "left" }}>
                  Recipient
                </th>
                <th scope="col" style={{ textAlign: "left" }}>
                  State
                </th>
                <th scope="col" style={{ textAlign: "left" }}>
                  Read
                </th>
                <th scope="col" />
              </tr>
            </thead>
            <tbody>
              {links.map((link) => {
                const summary = reads[link.id];
                const opened = summary?.sections.filter((s) => s.views > 0) ?? [];
                return (
                  <tr key={link.id} style={{ borderTop: "1px solid var(--color-border)" }}>
                    <td>{link.recipient_label}</td>
                    <td>{summary?.state ?? (link.revoked_at ? "revoked" : "active")}</td>
                    <td>
                      {opened.length
                        ? opened.map((s) => s.section).join(", ")
                        : "not opened yet"}
                    </td>
                    <td style={{ textAlign: "right" }}>
                      {link.revoked_at ? null : (
                        <button
                          type="button"
                          className="btn btn-ghost"
                          onClick={() => revoke(link.id)}
                          disabled={busy}
                        >
                          Revoke
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        ) : null}
      </section>
    </main>
  );
}
