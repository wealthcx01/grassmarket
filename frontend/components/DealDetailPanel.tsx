/**
 * Deal slide-over (GRS-0111 CRM rebuild). Opens when a kanban card is clicked: a right-side panel to
 * inline-edit the prospect (company, sector, website, notes), manage its first-class Contacts
 * (add / edit / promote-primary / remove), move its stage, and read its win-probability + stage
 * timeline. Everything is owner-scoped server-side. `onChanged` reloads the board so edits (e.g. a
 * new primary contact) reflect in the win-probability immediately.
 */

"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";
import Link from "next/link";

import { StageMoveControl } from "@/components/StageMoveControl";
import { WinProbabilityPill } from "@/components/KanbanBoard";
import { api } from "@/lib/api";
import { STAGE_LABEL, type Contact, type PipelineBoardEntry, type PipelineStage, type Prospect, type WinProbability } from "@/lib/types";

function EditableField({
  label,
  value,
  placeholder,
  multiline,
  onSave,
}: {
  label: string;
  value: string;
  placeholder: string;
  multiline?: boolean;
  onSave: (next: string) => Promise<void>;
}) {
  const [draft, setDraft] = useState(value);
  const [saving, setSaving] = useState(false);
  useEffect(() => setDraft(value), [value]);

  async function commit() {
    if (draft === value) return;
    setSaving(true);
    try {
      await onSave(draft.trim());
    } finally {
      setSaving(false);
    }
  }

  const shared = {
    value: draft,
    placeholder,
    disabled: saving,
    onChange: (e: { target: { value: string } }) => setDraft(e.target.value),
    onBlur: commit,
    style: {
      width: "100%",
      padding: "0.4rem 0.55rem",
      fontFamily: "inherit",
      fontSize: "0.85rem",
      color: "var(--color-ink)",
      background: "var(--color-paper)",
      border: "1px solid var(--color-border)",
      borderRadius: "var(--radius)",
    } as React.CSSProperties,
  };

  return (
    <label style={{ display: "block", fontSize: "0.72rem", color: "var(--color-ink-muted)" }}>
      <span style={{ display: "block", marginBottom: "0.2rem" }}>{label}</span>
      {multiline ? (
        <textarea rows={3} {...shared} style={{ ...shared.style, resize: "vertical" }} />
      ) : (
        <input
          type="text"
          {...shared}
          onKeyDown={(e) => {
            if (e.key === "Enter") (e.target as HTMLInputElement).blur();
          }}
        />
      )}
    </label>
  );
}

function ContactsSection({ prospectId, onMirror }: { prospectId: string; onMirror: () => void }) {
  const [contacts, setContacts] = useState<Contact[] | null>(null);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [title, setTitle] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => {
    api.listContacts(prospectId).then(setContacts).catch(() => setContacts([]));
  }, [prospectId]);
  useEffect(load, [load]);

  async function add(e: FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setBusy(true);
    try {
      await api.createContact(prospectId, {
        name: name.trim(),
        email: email.trim() || null,
        title: title.trim() || null,
        is_primary: (contacts ?? []).length === 0, // the first contact is primary by default
      });
      setName("");
      setEmail("");
      setTitle("");
      load();
      onMirror();
    } finally {
      setBusy(false);
    }
  }

  async function makePrimary(id: string) {
    await api.updateContact(prospectId, id, { is_primary: true });
    load();
    onMirror();
  }
  async function remove(id: string) {
    await api.deleteContact(prospectId, id);
    load();
    onMirror();
  }

  return (
    <section style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
      <h3 style={{ margin: 0, fontSize: "0.9rem" }}>Contacts</h3>
      {contacts === null ? (
        <p style={{ margin: 0, fontSize: "0.8rem", color: "var(--color-ink-muted)" }}>Loading…</p>
      ) : contacts.length === 0 ? (
        <p style={{ margin: 0, fontSize: "0.8rem", color: "var(--color-ink-muted)" }}>
          No contacts yet — add the buying unit below.
        </p>
      ) : (
        <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: "0.35rem" }}>
          {contacts.map((c) => (
            <li
              key={c.id}
              style={{ display: "flex", alignItems: "flex-start", gap: "0.5rem", padding: "0.45rem 0.55rem", border: "1px solid var(--color-border)", borderRadius: "var(--radius)", background: "var(--color-paper-raised)" }}
            >
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: "0.85rem", fontWeight: 600 }}>
                  {c.name}
                  {c.is_primary ? (
                    <span className="mono" style={{ marginLeft: "0.4rem", fontSize: "0.6rem", color: "var(--color-accent)", border: "1px solid var(--color-accent)", borderRadius: "999px", padding: "0 0.3rem" }}>
                      primary
                    </span>
                  ) : null}
                </div>
                {c.title ? <div style={{ fontSize: "0.72rem", color: "var(--color-ink-muted)" }}>{c.title}</div> : null}
                {c.email ? (
                  <a href={`mailto:${c.email}`} style={{ fontSize: "0.72rem", color: "var(--color-accent)" }}>
                    {c.email}
                  </a>
                ) : null}
                {c.phone ? <div className="mono" style={{ fontSize: "0.7rem", color: "var(--color-ink-muted)" }}>{c.phone}</div> : null}
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "0.2rem" }}>
                {!c.is_primary ? (
                  <button type="button" className="btn" style={{ fontSize: "0.66rem", padding: "0.1rem 0.4rem" }} onClick={() => makePrimary(c.id)}>
                    Make primary
                  </button>
                ) : null}
                <button type="button" className="btn" style={{ fontSize: "0.66rem", padding: "0.1rem 0.4rem" }} onClick={() => remove(c.id)} title="Remove contact">
                  Remove
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
      <form onSubmit={add} style={{ display: "flex", flexDirection: "column", gap: "0.35rem", borderTop: "1px dashed var(--color-border)", paddingTop: "0.5rem" }}>
        <div style={{ display: "flex", gap: "0.35rem", flexWrap: "wrap" }}>
          <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Name" style={{ ...contactInput, flex: "1 1 8rem" }} />
          <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Title" style={{ ...contactInput, flex: "1 1 7rem" }} />
        </div>
        <div style={{ display: "flex", gap: "0.35rem", flexWrap: "wrap" }}>
          <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" style={{ ...contactInput, flex: "1 1 10rem" }} />
          <button type="submit" className="btn btn-primary" disabled={busy || !name.trim()} style={{ fontSize: "0.75rem" }}>
            Add contact
          </button>
        </div>
      </form>
    </section>
  );
}

const contactInput: React.CSSProperties = {
  padding: "0.35rem 0.5rem",
  fontFamily: "inherit",
  fontSize: "0.8rem",
  color: "var(--color-ink)",
  background: "var(--color-paper)",
  border: "1px solid var(--color-border)",
  borderRadius: "var(--radius)",
};

// The win-probability made legible (GRS-0137): the number, WHY it is what it is, and — when the
// estimate is unsettled — exactly what would sharpen it. Previously this lived only in a hover
// tooltip on the pill (invisible on touch); a shown number deserves its shown reasons.
function WinProbabilityExplainer({ wp }: { wp: WinProbability }) {
  return (
    <section
      style={{
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius)",
        padding: "0.7rem 0.85rem",
        background: "var(--color-paper-raised)",
        display: "flex",
        flexDirection: "column",
        gap: "0.45rem",
      }}
    >
      <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", gap: "0.5rem" }}>
        <h3 style={{ margin: 0, fontSize: "0.9rem" }}>Win probability</h3>
        <span className="mono" style={{ fontSize: "0.62rem", color: "var(--color-ink-faint)" }}>
          rule-based estimate
        </span>
      </div>
      <div style={{ display: "flex", alignItems: "baseline", gap: "0.5rem" }}>
        <span style={{ fontSize: "1.5rem", fontWeight: 700 }}>{wp.score}%</span>
        <span style={{ fontSize: "0.8rem", color: "var(--color-ink-muted)" }}>{wp.label}</span>
      </div>
      {wp.reasons.length ? (
        <div>
          <p style={{ margin: "0 0 0.2rem", fontSize: "0.7rem", color: "var(--color-ink-faint)", textTransform: "uppercase", letterSpacing: "0.05em" }}>Why</p>
          <ul style={{ margin: 0, paddingLeft: "1rem", fontSize: "0.78rem", color: "var(--color-ink-muted)", display: "flex", flexDirection: "column", gap: "0.1rem" }}>
            {wp.reasons.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        </div>
      ) : null}
      {wp.missing_info.length ? (
        <div>
          <p style={{ margin: "0 0 0.2rem", fontSize: "0.7rem", color: "var(--color-ink-faint)", textTransform: "uppercase", letterSpacing: "0.05em" }}>Would sharpen the estimate</p>
          <ul style={{ margin: 0, paddingLeft: "1rem", fontSize: "0.78rem", color: "var(--color-ink-muted)", display: "flex", flexDirection: "column", gap: "0.1rem" }}>
            {wp.missing_info.map((m, i) => (
              <li key={i}>{m}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  );
}

export function DealDetailPanel({
  entry,
  onClose,
  onChanged,
}: {
  entry: PipelineBoardEntry;
  onClose: () => void;
  onChanged: () => void;
}) {
  const prospectId = entry.prospect.id;
  const [prospect, setProspect] = useState<Prospect>(entry.prospect);

  useEffect(() => {
    setProspect(entry.prospect);
    api.getProspect(prospectId).then(setProspect).catch(() => {});
  }, [prospectId, entry.prospect]);

  // Close on Escape.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  async function patch(field: keyof Prospect, value: string) {
    const updated = await api.updateProspect(prospectId, { [field]: value || null });
    setProspect(updated);
    onChanged();
  }

  const onMove = useCallback(
    async (id: string, stage: PipelineStage) => {
      await api.updateProspectStage(id, stage);
      const fresh = await api.getProspect(id);
      setProspect(fresh);
      onChanged();
    },
    [onChanged],
  );

  return (
    <div
      onClick={onClose}
      style={{ position: "fixed", inset: 0, zIndex: 50, background: "rgba(0,0,0,0.35)" }}
    >
      <aside
        role="dialog"
        aria-label={`${prospect.company_name} deal`}
        onClick={(e) => e.stopPropagation()}
        style={{
          position: "fixed",
          top: 0,
          right: 0,
          bottom: 0,
          width: "min(30rem, 92vw)",
          background: "var(--color-paper)",
          borderLeft: "1px solid var(--color-border)",
          boxShadow: "-6px 0 20px rgba(0,0,0,0.18)",
          overflowY: "auto",
          padding: "1.1rem 1.2rem",
          display: "flex",
          flexDirection: "column",
          gap: "1rem",
        }}
      >
        <header style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "0.5rem" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <h2 style={{ margin: 0, fontSize: "1.25rem", fontFamily: "var(--font-serif)" }}>
                {prospect.company_name}
              </h2>
              <WinProbabilityPill wp={entry.win_probability} />
            </div>
            <p className="mono" style={{ margin: "0.2rem 0 0", fontSize: "0.72rem", color: "var(--color-ink-muted)" }}>
              {STAGE_LABEL[prospect.stage]} · entered {new Date(prospect.stage_entered_at).toLocaleDateString()}
            </p>
          </div>
          <button type="button" aria-label="Close" onClick={onClose} className="btn" style={{ fontSize: "1rem", lineHeight: 1 }}>
            ✕
          </button>
        </header>

        <WinProbabilityExplainer wp={entry.win_probability} />

        <div style={{ maxWidth: "14rem" }}>
          <StageMoveControl prospectId={prospectId} currentStage={prospect.stage} onMove={onMove} />
        </div>

        <section style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
          <EditableField label="Company" value={prospect.company_name} placeholder="Company name" onSave={(v) => patch("company_name", v)} />
          <div style={{ display: "flex", gap: "0.6rem", flexWrap: "wrap" }}>
            <div style={{ flex: "1 1 9rem" }}>
              <EditableField label="Sector" value={prospect.sector ?? ""} placeholder="e.g. Wealth" onSave={(v) => patch("sector", v)} />
            </div>
            <div style={{ flex: "1 1 9rem" }}>
              <EditableField label="Website" value={prospect.website ?? ""} placeholder="https://…" onSave={(v) => patch("website", v)} />
            </div>
          </div>
          <EditableField label="Notes" value={prospect.notes ?? ""} placeholder="Qualifying notes…" multiline onSave={(v) => patch("notes", v)} />
        </section>

        <ContactsSection prospectId={prospectId} onMirror={() => api.getProspect(prospectId).then(setProspect).catch(() => {})} />

        <ProspectTimeline prospectId={prospectId} />

        <footer style={{ borderTop: "1px solid var(--color-border)", paddingTop: "0.6rem", fontSize: "0.8rem" }}>
          <Link href={`/prospects/${prospectId}`}>Open full record (workshops, engagements) →</Link>
        </footer>
      </aside>
    </div>
  );
}

function ProspectTimeline({ prospectId }: { prospectId: string }) {
  const [history, setHistory] = useState<{ from_stage: PipelineStage | null; to_stage: PipelineStage; occurred_at: string }[]>([]);
  useEffect(() => {
    api.prospectHistory(prospectId).then(setHistory).catch(() => setHistory([]));
  }, [prospectId]);
  if (history.length === 0) return null;
  const rows = [...history].reverse();
  return (
    <section>
      <h3 style={{ margin: "0 0 0.5rem", fontSize: "0.9rem" }}>Stage history</h3>
      <ol style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: "0.35rem" }}>
        {rows.map((h, i) => (
          <li key={`${h.occurred_at}-${i}`} style={{ display: "flex", gap: "0.5rem", fontSize: "0.78rem" }}>
            <span className="mono" style={{ flex: "0 0 5.5rem", fontSize: "0.68rem", color: "var(--color-ink-muted)" }}>
              {new Date(h.occurred_at).toLocaleDateString()}
            </span>
            <span>
              {h.from_stage ? (
                <>
                  <span style={{ color: "var(--color-ink-muted)" }}>{STAGE_LABEL[h.from_stage]}</span> →{" "}
                  <strong>{STAGE_LABEL[h.to_stage]}</strong>
                </>
              ) : (
                <>Created in <strong>{STAGE_LABEL[h.to_stage]}</strong></>
              )}
            </span>
          </li>
        ))}
      </ol>
    </section>
  );
}
