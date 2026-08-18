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
import type {
  ClientReportLink,
  DeclaredFigure,
  ReportProseSection,
  ReportReadReport,
} from "@/lib/types";

const SECTION_ORDER = [
  "business",
  "advantage",
  "constraint",
  "actions",
  "value",
  "appendix",
] as const;

/** Reader-facing names, matching `bcap_contracts.client_report.SECTION_TITLES`. Used for the
 *  empty-section hint so it names sections the way the page and the report do, never by key. */
const SECTION_TITLES: Record<string, string> = {
  business: "The business",
  advantage: "Where the advantage sits",
  constraint: "What is holding it back",
  actions: "What to do about it",
  value: "What that is worth",
  appendix: "Technical appendix",
};

/** Operating-model keys are stored; a reader should not have to decode one. */
function humanModel(key: string): string {
  // The keys are `retail`, `wealth` and `exchange` — `RETAIL_PROFILE_KEY` in
  // `bcap_contracts.registry`, not the `retail_brokerage` this first guessed. The badge showed the
  // raw key on staging as a result: the property was right and the fixture was wrong, so the test
  // passed while the page was wrong. Both are keyed off the real values now.
  return (
    {
      retail: "Retail brokerage",
      wealth: "Wealth",
      exchange: "Exchange",
    }[key] ?? key.replace(/_/g, " ")
  );
}

/** "The business and What that is worth" — an English list, not a JSON array at a human. */
function listSections(keys: string[]): string {
  const names = keys.map((k) => SECTION_TITLES[k] ?? k);
  if (names.length <= 1) return names.join("");
  return `${names.slice(0, -1).join(", ")} and ${names[names.length - 1]}`;
}

/** Where the last action's message goes: beside the button that caused it (GRS-0230 scope 1). */
type Feedback = { action: "save" | "download" | "share"; kind: "ok" | "error"; message: string };

function Feedback({ for: action, from }: { for: Feedback["action"]; from: Feedback | null }) {
  if (!from || from.action !== action) return null;
  return (
    <p
      role={from.kind === "error" ? "alert" : "status"}
      className={from.kind === "error" ? "callout callout-error" : "callout"}
      style={{ marginTop: "0.6rem" }}
      data-testid={`feedback-${action}`}
    >
      {from.message}
    </p>
  );
}

/** The figures this section may state, and a one-click way to use one. */
function FigurePalette({
  figures,
  onInsert,
}: {
  figures: DeclaredFigure[];
  onInsert: (rendered: string) => void;
}) {
  if (figures.length === 0) {
    // Silence here is what made the gate a dead end, so say why there is nothing rather than
    // rendering an empty strip.
    return (
      <p className="figure-palette-empty">
        This section quotes no figures from the run, so any number in it will be refused. Prices
        come from the value bridge on the deliverable, not from this editor.
      </p>
    );
  }
  return (
    <div className="figure-palette">
      <span className="figure-palette-label">Figures you can quote here:</span>
      {figures.map((f) => (
        <button
          key={f.key}
          type="button"
          className="figure-chip"
          onClick={() => onInsert(f.rendered)}
          title={`${f.label} — from ${f.source}`}
        >
          <span className="figure-chip-value">{f.rendered}</span>
          <span className="figure-chip-label">{f.label}</span>
        </button>
      ))}
    </div>
  );
}

/** What each section is for, in the advisor's words — the page teaches the shape of the argument. */
const SECTION_GUIDANCE: Record<string, string> = {
  business: "What this firm is and how it makes money, in plain prose. No score belongs here.",
  advantage: "Where durable advantage sits, through the Powers that apply — and where it does not.",
  constraint: "The honest reading of what is holding them back.",
  actions: "What to do about it, with the levers ranked.",
  value: "What that is worth if they act.",
  // GRS-0232 scope 3: say what is checked here, so the rule is met by reading rather than by
  // refusal — the same principle as showing the declared figures (GRS-0230 scope 3).
  appendix:
    "Coefficients, weights, uncertainty method, coverage. P10/P50/P90 may ONLY appear here. " +
    "Every number still has to be one the run declares, and any methodology, coefficient or " +
    "engine version you state is checked against the run's own — the appendix is the audit trail, " +
    "so it is the one section that must not contradict it.",
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
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const [figures, setFigures] = useState<Record<string, DeclaredFigure[]>>({});
  // GRS-0231. Two report editors were pixel-identical and titled "What the client reads"; the only
  // place the firm's name existed was the URL. An advisor with two engagements open in two tabs
  // would eventually write one client's constraint into the other's report, and nothing on the page
  // could catch it.
  const [identity, setIdentity] = useState<{
    subject: string | null;
    engagement_title: string | null;
    provenance: string | null;
    operating_model: string | null;
  }>({ subject: null, engagement_title: null, provenance: null, operating_model: null });

  // Which sections have no words in them. Drives the Create-link hint, so the reason a control is
  // disabled comes from the same data the server will refuse on.
  const unwritten = SECTION_ORDER.filter(
    (kind) => !(sections?.[kind]?.body ?? []).some((p) => p && p.trim()),
  );
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
      .then((body) => {
        setSections(body.sections);
        // The vocabulary the gate accepts, shown BEFORE it teaches by refusal.
        setFigures(body.available_figures ?? {});
        setIdentity({
          subject: body.subject ?? null,
          engagement_title: body.engagement_title ?? null,
          provenance: body.provenance ?? null,
          operating_model: body.operating_model ?? null,
        });
      })
      .then(() => refreshLinks(ctrl.signal))
      .catch((err: unknown) => {
        if (err instanceof ApiError && err.status === 0 && err.aborted) return;
        if (err instanceof ApiError && err.status === 401) return router.replace("/login");
        setError(err instanceof ApiError ? err.message : "Could not load this report.");
      });
    return () => ctrl.abort();
  }, [id, router, refreshLinks]);

  /** Append a declared figure to a section's prose (GRS-0230 scope 3).

   *  Appended to the last paragraph rather than inserted at the caret: a controlled textarea does
   *  not expose a caret position to this component without a ref per section, and the advisor is
   *  going to write a sentence around the number either way. Getting the digits exactly right is
   *  the part that matters, because the gate compares strings.
   */
  const appendToBody = useCallback((kind: string, rendered: string) => {
    setSections((current) => {
      if (!current) return current;
      const existing = current[kind];
      if (!existing) return current;  // a section the six-key shape does not have
      const body = [...(existing.body ?? [])];
      const last = body.length > 0 ? body.length - 1 : 0;
      body[last] = body[last] ? `${body[last]} ${rendered}` : rendered;
      return { ...current, [kind]: { ...existing, body } };
    });
  }, []);

  // GRS-0231 scope 2. Two open editors were indistinguishable in the tab strip, which is where an
  // advisor actually switches between them.
  useEffect(() => {
    if (!identity.subject) return;
    const previous = document.title;
    document.title = `Client report — ${identity.subject}`;
    return () => {
      document.title = previous;
    };
  }, [identity.subject]);

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
      setFeedback({ action: "save", kind: "ok", message: "Saved." });
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Could not save.";
      setError(message);
      setFeedback({ action: "save", kind: "error", message });
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
      // Names the client: one more chance to catch a cross-client mistake at the moment of export,
      // which is the last point at which catching it is free.
      const confirmation = identity.subject
        ? `PDF downloaded — ${identity.subject}.`
        : "PDF downloaded.";
      setStatus(confirmation);
      setFeedback({ action: "download", kind: "ok", message: confirmation });
    } catch (err) {
      // A 409 here is the content model refusing an unfinished report. Its sentence names the
      // missing sections, so it is shown as-is rather than replaced with "something went wrong".
      const message = err instanceof ApiError ? err.message : "Could not render the PDF.";
      setError(message);
      setFeedback({ action: "download", kind: "error", message });
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
      const message = err instanceof ApiError ? err.message : "Could not create a link.";
      setError(message);
      setFeedback({ action: "share", kind: "error", message });
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
      {/* The client's name IS the heading. "What the client reads" described the page and named
          nobody, which is the whole defect: on a surface where the same words become a branded PDF
          and a public link, whose words these are is the context that matters most. */}
      <h1 style={{ fontSize: "2rem", margin: "0.3rem 0 0.4rem" }} data-testid="report-subject">
        {identity.subject ?? "Client report"}
      </h1>
      <div className="report-identity" data-testid="report-identity">
        {identity.engagement_title ? <span>{identity.engagement_title}</span> : null}
        {identity.operating_model ? (
          <span className="badge">{humanModel(identity.operating_model)}</span>
        ) : null}
        {identity.provenance && identity.provenance !== "production" ? (
          <span className="badge badge-warn">{identity.provenance.toUpperCase()}</span>
        ) : null}
      </div>
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
            <label
              id={`l-${kind}`}
              htmlFor={`s-${kind}`}
              style={{ display: "block", fontWeight: 500 }}
            >
              {sections[kind]?.heading ?? SECTION_TITLES[kind] ?? kind}
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
              /* GRS-0231 scope 3. All six shared one accessible name — the placeholder — so a
                 screen-reader user could not tell the Business section from the Appendix. The
                 visible label is the accessible name now; the placeholder is only a hint. */
              aria-labelledby={`l-${kind}`}
              value={(sections[kind]?.body ?? []).join("\n\n")}
              onChange={(e) => setBody(kind, e.target.value)}
              rows={4}
              style={{ width: "100%" }}
              placeholder="Blank lines separate paragraphs."
            />
            {/* GRS-0230 scope 3. The gate refuses any number the run does not declare, and the
                editor used to show none of them — so the section titled "What that is worth" could
                not state what anything was worth, with no way out but guessing. These are the same
                figures the assembler uses, so what is offered and what is accepted cannot differ.
                Clicking one appends it, because the alternative is retyping a number by hand into a
                field that refuses mistyped numbers. */}
            <FigurePalette
              figures={figures[kind] ?? []}
              onInsert={(rendered) => appendToBody(kind, rendered)}
            />
          </div>
        ))}
        <button type="button" className="btn btn-primary" onClick={save} disabled={busy}>
          {busy ? "Working…" : "Save"}
        </button>
        {/* GRS-0230 scope 1. The tester clicked Save, saw nothing, and only found the message by
            scrolling to the top of the page. Feedback belongs where the click happened; the
            top-of-page strip stays as well, because a long form can scroll the button off screen
            too. */}
        <Feedback for="save" from={feedback} />
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
        <Feedback for="download" from={feedback} />
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
              disabled={busy || !recipient.trim() || unwritten.length > 0}
            >
              Create link
            </button>
          </div>
          {/* GRS-0230 scope 5. The button used to sit inert with no reason. Naming the empty
              sections turns a dead control into an instruction. */}
          {unwritten.length > 0 ? (
            <p className="hint" data-testid="create-link-hint">
              Write and save all six sections first — {listSections(unwritten)}{" "}
              {unwritten.length === 1 ? "is" : "are"} still empty.
            </p>
          ) : null}
          <Feedback for="share" from={feedback} />
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
