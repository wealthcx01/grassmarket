/**
 * "Your Brokerages" — the advisor's portfolio home (GRS-0071). One row per assessment (server-scoped
 * by JWT): the business, its segment, its last finalised Platform Value, status, and when it was last
 * touched. Create a new one or resume a draft — a partial assessment is valid and autosaves.
 */

"use client";

import { useEffect, useMemo, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

import { FIELD_CONTROL_CLASS, FormField } from "@/components/FormField";
import { toDisplay } from "@/lib/band";
import { ApiError, api, getToken } from "@/lib/api";
import * as doc from "@/lib/doc";
import type { BrokeragePortfolioEntry, RegistryProfile } from "@/lib/types";
import { groupBySubject, type SubjectGroup } from "@/lib/portfolioGrouping";
import { ProvenanceBadge } from "@/components/ProvenanceBadge";
import { EntitySubjectField } from "@/components/EntitySubjectField";
import { NotFoundNotice } from "@/components/NotFoundNotice";

/** One plain explanation of the sandbox path, used by the checkbox and the first-visit note. */
const SANDBOX_EXPLANATION =
  "A practice copy is yours alone. You can finalise it without a second rater or a committee, " +
  "which is how you see a real deliverable draft on your own, and everything it produces is " +
  "watermarked and can never reach a client. You can also make one later from the Summary step " +
  "of any assessment.";

/** Dismissal of the first-visit note. A one-time reading aid, so localStorage rather than
 *  account state on the server: nothing here is worth a row in the database. */
const DEMO_NOTE_KEY = "gm:portfolio:demo-note";

const STATE_LABEL: Record<BrokeragePortfolioEntry["state"], string> = {
  draft: "Draft",
  in_progress: "In progress",
  finalised: "Finalised · locked",
};

function Completeness({ coverage }: { coverage?: number | null }) {
  if (coverage == null) {
    return <span style={{ color: "var(--color-ink-faint)" }}>—</span>;
  }
  const pct = Math.round(coverage * 100);
  return (
    <span
      style={{ display: "inline-flex", alignItems: "center", gap: "0.45rem", minWidth: "5.5rem" }}
      title={`${pct}% of applicable subcomponents rated`}
    >
      <span
        aria-hidden
        style={{
          flex: 1,
          height: "0.4rem",
          borderRadius: "var(--radius-pill)",
          background: "var(--color-border)",
          overflow: "hidden",
          minWidth: "3rem",
        }}
      >
        <span style={{ display: "block", height: "100%", width: `${pct}%`, background: "var(--color-accent)" }} />
      </span>
      <span className="mono" style={{ fontSize: "0.75rem", color: "var(--color-ink-muted)" }}>
        {pct}%
      </span>
    </span>
  );
}

function LastScore({ entry }: { entry: BrokeragePortfolioEntry }) {
  if (entry.v_index == null) {
    return <span style={{ color: "var(--color-ink-faint)" }}>—</span>;
  }
  return (
    <span style={{ display: "inline-flex", alignItems: "baseline", gap: "0.4rem" }}>
      <strong className="mono">{toDisplay(entry.v_index).toFixed(1)}</strong>
      {entry.uncertainty_rating ? (
        <span className="tag" title="Overall uncertainty of the finalised score">
          {entry.uncertainty_rating}
        </span>
      ) : null}
    </span>
  );
}

function CustomerScore({ entry }: { entry: BrokeragePortfolioEntry }) {
  if (entry.c_index == null) {
    return <span style={{ color: "var(--color-ink-faint)" }}>—</span>;
  }
  return <strong className="mono">{toDisplay(entry.c_index).toFixed(1)}</strong>;
}

export default function BrokeragesPage() {
  const router = useRouter();
  const [items, setItems] = useState<BrokeragePortfolioEntry[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [subject, setSubject] = useState("");
  const [entityId, setEntityId] = useState<string | null>(null);
  const [sandbox, setSandbox] = useState(false);
  const [profiles, setProfiles] = useState<RegistryProfile[]>([]);
  const [profileKey, setProfileKey] = useState("retail");
  const [creating, setCreating] = useState(false);
  // Which subject groups are open (GRS-0177). Per-render state on purpose: which rows you last
  // expanded is not worth persisting anywhere.
  const [expanded, setExpanded] = useState<ReadonlySet<string>>(new Set());
  // The first-visit note starts hidden and appears only once we have READ localStorage, so a
  // returning advisor never sees it flash before being dismissed again.
  const [showDemoNote, setShowDemoNote] = useState(false);

  // Prefill the subject when arriving from an engagement's "Start an assessment" CTA (?subject=…).
  const groups = useMemo(() => groupBySubject(items ?? []), [items]);
  const hasVariants = groups.some((g) => g.variants.length > 0);
  const hasDemoRows = (items ?? []).some((e) => e.provenance !== "production");

  function toggleGroup(key: string) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (!next.delete(key)) next.add(key);
      return next;
    });
  }

  function dismissDemoNote() {
    setShowDemoNote(false);
    try {
      window.localStorage.setItem(DEMO_NOTE_KEY, "1");
    } catch {
      // A browser with storage blocked simply shows the note again next visit, which is a
      // better failure than not rendering the portfolio.
    }
  }

  useEffect(() => {
    try {
      setShowDemoNote(window.localStorage.getItem(DEMO_NOTE_KEY) === null);
    } catch {
      setShowDemoNote(true);
    }
  }, []);

  useEffect(() => {
    const s = new URLSearchParams(window.location.search).get("subject");
    if (s) setSubject(s);
  }, []);

  // The operating-model profiles the subject can be assessed under (GRS-0079/0098) — the profile is
  // the same field the wizard's Overview step edits, just chosen at creation.
  useEffect(() => {
    const ctrl = new AbortController();
    api.registryProfiles(ctrl.signal).then(setProfiles).catch(() => {});
    return () => ctrl.abort();
  }, []);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    const ctrl = new AbortController();
    api
      .brokeragePortfolio(ctrl.signal)
      .then(setItems)
      .catch((err: unknown) => {
        if (err instanceof ApiError && err.status === 0 && err.aborted) return;
        if (err instanceof ApiError && err.status === 401) return router.replace("/login");
        setError(err instanceof ApiError ? err.message : "Could not load your portfolio.");
      });
    return () => ctrl.abort();
  }, [router]);

  async function onCreate(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!subject.trim()) return;
    setCreating(true);
    setError(null);
    try {
      const created = await api.createAssessment(
        subject.trim(),
        sandbox ? "sandbox" : "production",
        entityId,
      );
      // Set the operating-model profile at creation (feeds the same mechanism as the wizard's Overview
      // selector, GRS-0079). Retail is the default; only save a non-default so retail stays byte-clean.
      if (profileKey && profileKey !== "retail") {
        await api.saveAssessment(
          created.id,
          doc.setProfile(created.document, { operating_model: profileKey }),
        );
      }
      router.push(`/assessments/${created.id}`);
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : "Could not create the assessment.");
      setCreating(false);
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.75rem" }}>
      <NotFoundNotice noun="assessment" />
      <section>
        <p className="eyebrow" style={{ margin: 0 }}>
          Platform Power · Path A (manual)
        </p>
        <h1 style={{ fontSize: "2rem", margin: "0.3rem 0 0.4rem" }}>Your Portfolio</h1>
        <p style={{ margin: 0, color: "var(--color-ink-muted)", maxWidth: "40rem" }}>
          Your portfolio of assessments. Start a new one or resume a draft — a partial assessment is
          valid and autosaves. A score appears once the assessment is finalised.
        </p>
      </section>

      {/* A two-row grid (GRS-0178). The fields share one baseline because each is a block label
          above its input, so `alignItems: end` lines them up on real content — the old flex row
          did it with a magic-number paddingBottom on the checkbox, which is why the founder saw
          the subject box and the Operating Model dropdown out of alignment. The breakpoint that
          stacks the columns lives in globals.css, since inline styles cannot carry a media query. */}
      <form onSubmit={onCreate} className="form-create-assessment">
        <FormField label="New assessment — subject company">
          <EntitySubjectField
            value={subject}
            entityId={entityId}
            onChange={(s, id) => {
              setSubject(s);
              setEntityId(id);
            }}
          />
        </FormField>
        <FormField label="Operating model">
          <select
            className={FIELD_CONTROL_CLASS}
            value={profileKey}
            onChange={(e) => setProfileKey(e.target.value)}
            style={{
              width: "100%",
              padding: "0.55rem 0.7rem",
              fontFamily: "inherit",
              fontSize: "0.95rem",
              color: "var(--color-ink)",
              background: "var(--color-paper-raised)",
              border: "1px solid var(--color-border)",
              borderRadius: "var(--radius)",
            }}
          >
            {(profiles.length ? profiles : [{ key: "retail", name: "Retail" }]).map((p) => (
              <option key={p.key} value={p.key}>
                {p.name}
              </option>
            ))}
          </select>
        </FormField>
        {/* The button goes through the SAME field wrapper as the two controls (GRS-0209), with an
            empty label reserving the label row. That is deliberate: nudging it down with a computed
            margin is the magic-number compensation GRS-0178 was faulted for, and it drifts the
            moment a label's font-size changes. Reserving the row structurally cannot drift. */}
        <FormField label={<span aria-hidden="true">&nbsp;</span>}>
          <button
            type="submit"
            className={`btn btn-primary ${FIELD_CONTROL_CLASS}`}
            disabled={creating || !subject.trim()}
          >
            {creating ? "Creating…" : "Create and open"}
          </button>
        </FormField>
        {/* Row 2. The explanation is visible text, not only a tooltip: an advisor deciding
            whether to tick this should not have to hover to find out what it does. */}
        <div style={{ gridColumn: "1 / -1", display: "flex", gap: "0.55rem", alignItems: "flex-start" }}>
          <input
            id="sandbox-option"
            type="checkbox"
            checked={sandbox}
            onChange={(e) => setSandbox(e.target.checked)}
            style={{ marginTop: "0.2rem" }}
          />
          <label htmlFor="sandbox-option" style={{ fontSize: "0.82rem", lineHeight: 1.5 }}>
            <span style={{ fontWeight: 500 }}>Make this a private practice copy</span>
            <span style={{ display: "block", color: "var(--color-ink-muted)" }}>
              {SANDBOX_EXPLANATION}
            </span>
          </label>
        </div>
      </form>

      {error ? (
        <p role="alert" style={{ color: "var(--color-error)", fontSize: "0.9rem" }}>
          {error}
        </p>
      ) : null}

      <section>
        <h2 style={{ fontSize: "1.05rem", marginBottom: "1rem" }}>Portfolio</h2>
        {/* A one-time reading aid (GRS-0177). It explains the badges rather than apologising for
            them, and it only appears when there is actually something to explain. */}
        {showDemoNote && hasDemoRows ? (
          <div
            className="callout callout-info"
            style={{ marginBottom: "1rem", display: "grid", gap: "0.5rem", fontSize: "0.85rem", lineHeight: 1.55 }}
          >
            <p style={{ margin: 0 }}>
              Some rows below are badged <strong>Demo</strong> or <strong>Sandbox</strong>. A demo row
              is a seeded illustrative record, here so the studio has something to show; its numbers
              describe nobody&rsquo;s actual platform. A sandbox row is your own private practice
              copy. Neither can reach a client.
              {hasVariants ? (
                <>
                  {" "}
                  Where the same company has been assessed more than once, the records are grouped
                  under one row, and the chip beside the name opens the rest.
                </>
              ) : null}
            </p>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={dismissDemoNote}
              style={{ justifySelf: "start" }}
            >
              Got it
            </button>
          </div>
        ) : null}
        {items === null ? (
          <p style={{ color: "var(--color-ink-muted)" }}>Loading…</p>
        ) : items.length === 0 ? (
          <p style={{ color: "var(--color-ink-muted)" }}>
            No assessments yet. Create one above to begin.
          </p>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.88rem" }}>
              <thead>
                <tr style={{ textAlign: "left", color: "var(--color-ink-muted)", fontSize: "0.78rem" }}>
                  <th style={{ padding: "0.4rem 0.6rem", fontWeight: 600 }}>Subject</th>
                  <th style={{ padding: "0.4rem 0.6rem", fontWeight: 600 }}>Segment</th>
                  {/* Same word, same number as the wizard's "of applicable" figure (GRS-0168) —
                      "Completeness" beside the wizard's "Coverage 100%" read as a contradiction. */}
                  <th style={{ padding: "0.4rem 0.6rem", fontWeight: 600 }} title="Assessed share of the subcomponents applicable to this assessment's operating model — the same figure the wizard shows">
                    Coverage
                  </th>
                  <th style={{ padding: "0.4rem 0.6rem", fontWeight: 600 }} title="Last finalised Platform Value V (0–100)">
                    Platform (V)
                  </th>
                  <th
                    style={{ padding: "0.4rem 0.6rem", fontWeight: 600 }}
                    title="Customer-Proposition index C (0–100) — how good the platform is for a customer. Reported alongside V, not folded into it."
                  >
                    Customer (C)
                  </th>
                  <th style={{ padding: "0.4rem 0.6rem", fontWeight: 600 }}>Status</th>
                  <th style={{ padding: "0.4rem 0.6rem", fontWeight: 600 }}>Last updated</th>
                </tr>
              </thead>
              <tbody>
                {groups.map((group) => (
                  <PortfolioRows
                    key={group.key || group.primary.assessment_id}
                    group={group}
                    expanded={expanded.has(group.key)}
                    onToggle={() => toggleGroup(group.key)}
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <footer style={{ fontSize: "0.8rem", color: "var(--color-ink-muted)" }}>
        <Link href="/">← Back to dashboard</Link>
      </footer>
    </div>
  );
}

/**
 * One subject's rows: the primary record, plus its variants when expanded (GRS-0177).
 *
 * A variant is the SAME company assessed again on a different path, which is exactly what confused
 * the founder's demo. Collapsing them under one subject makes the portfolio read as a list of
 * companies rather than a list of records, and nothing is hidden: the count chip says how many
 * there are and one click shows them, each with its own badge and its own link.
 */
function PortfolioRows({
  group,
  expanded,
  onToggle,
}: {
  group: SubjectGroup;
  expanded: boolean;
  onToggle: () => void;
}) {
  return (
    <>
      <PortfolioRow entry={group.primary} variantCount={group.variants.length} expanded={expanded} onToggle={onToggle} />
      {expanded
        ? group.variants.map((variant) => <PortfolioRow key={variant.assessment_id} entry={variant} isVariant />)
        : null}
    </>
  );
}

function PortfolioRow({
  entry: e,
  variantCount = 0,
  expanded = false,
  onToggle,
  isVariant = false,
}: {
  entry: BrokeragePortfolioEntry;
  variantCount?: number;
  expanded?: boolean;
  onToggle?: () => void;
  isVariant?: boolean;
}) {
  return (
    <tr
      style={{
        borderTop: isVariant ? "1px dashed var(--color-border)" : "1px solid var(--color-border)",
        // A variant is indented and muted so the eye reads it as a child of the row above.
        background: isVariant ? "var(--color-paper-raised)" : undefined,
      }}
    >
        <td style={{ padding: "0.55rem 0.6rem" }}>
          <span style={{ display: "inline-flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap", paddingLeft: isVariant ? "1.25rem" : 0 }}>
            <Link
              href={`/assessments/${e.assessment_id}`}
              style={{ fontFamily: "var(--font-serif)", fontWeight: 600, color: "inherit", textDecoration: "none" }}
            >
              {e.subject || "Untitled"}
            </Link>
            <ProvenanceBadge provenance={e.provenance} />
            {variantCount > 0 && onToggle ? (
              <button
                type="button"
                onClick={onToggle}
                aria-expanded={expanded}
                title="The same company assessed more than once. Open to see the other records."
                style={{
                  fontSize: "0.66rem",
                  cursor: "pointer",
                  padding: "0.15rem 0.5rem",
                  borderRadius: "var(--radius-pill)",
                  border: "1px solid var(--color-border-strong)",
                  background: "none",
                  color: "var(--color-ink-muted)",
                }}
              >
                {expanded ? "−" : "+"}
                {variantCount} {variantCount === 1 ? "variant" : "variants"}
              </button>
            ) : null}
          </span>
          {/* Link to the client record only when the assessment is linked to an
              engagement (GRS-0186) — never a guessed link when it is not. */}
          {e.linked_prospect_id ? (
            <div style={{ marginTop: "0.15rem", fontSize: "0.75rem" }}>
              <Link href={`/prospects/${e.linked_prospect_id}`} style={{ color: "var(--color-ink-muted)" }}>
                Client record →
              </Link>
            </div>
          ) : null}
        </td>
        <td style={{ padding: "0.55rem 0.6rem", color: e.segment ? "inherit" : "var(--color-ink-faint)" }}>
          {e.segment ?? "—"}
        </td>
        <td style={{ padding: "0.55rem 0.6rem" }}>
          <Completeness coverage={e.coverage} />
        </td>
        <td style={{ padding: "0.55rem 0.6rem" }}>
          <LastScore entry={e} />
        </td>
        <td style={{ padding: "0.55rem 0.6rem" }}>
          <CustomerScore entry={e} />
        </td>
        <td style={{ padding: "0.55rem 0.6rem" }}>
          <span
            className="mono"
            style={{
              fontSize: "0.7rem",
              color: e.state === "finalised" ? "var(--color-accent)" : "var(--color-ink-muted)",
            }}
          >
            {STATE_LABEL[e.state]}
          </span>
        </td>
        <td className="mono" style={{ padding: "0.55rem 0.6rem", fontSize: "0.78rem", color: "var(--color-ink-muted)" }}>
          {new Date(e.updated_at).toLocaleDateString()}
        </td>
      </tr>
  );
}
