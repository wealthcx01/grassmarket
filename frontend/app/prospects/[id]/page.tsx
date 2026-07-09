/**
 * Prospect detail (GRS-0014) — the CRM hub for one prospect: its stage (movable, backend-validated),
 * its workshops (schedule → deliver, from here), and its engagements (open one once contracted).
 */

"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";

import { StageMoveControl } from "@/components/StageMoveControl";
import { ApiError, api, getToken } from "@/lib/api";
import { STAGE_LABEL, type Engagement, type PipelineStage, type Prospect, type Workshop } from "@/lib/types";

const CONTRACTED_OR_BEYOND: PipelineStage[] = ["contracted", "active", "delivered"];

export default function ProspectDetailPage() {
  const router = useRouter();
  const params = useParams<{ id: string }>();
  const id = params.id;

  const [prospect, setProspect] = useState<Prospect | null>(null);
  const [workshops, setWorkshops] = useState<Workshop[]>([]);
  const [engagements, setEngagements] = useState<Engagement[]>([]);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(
    (signal?: AbortSignal) =>
      Promise.all([
        api.getProspect(id, signal),
        api.listWorkshops(signal),
        api.listEngagements(signal),
      ])
        .then(([p, ws, es]) => {
          setProspect(p);
          setWorkshops(ws.filter((w) => w.prospect_id === id));
          setEngagements(es.filter((e) => e.prospect_id === id));
        })
        .catch((err: unknown) => {
          if (err instanceof ApiError && err.status === 0) return;
          if (err instanceof ApiError && err.status === 404) return router.replace("/pipeline");
          setError(err instanceof ApiError ? err.message : "Could not load the prospect.");
        }),
    [id, router],
  );

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    const ctrl = new AbortController();
    reload(ctrl.signal);
    return () => ctrl.abort();
  }, [router, reload]);

  const onMove = useCallback(
    async (pid: string, stage: PipelineStage) => {
      await api.updateProspectStage(pid, stage);
      await reload();
    },
    [reload],
  );

  if (error) return <p style={{ color: "var(--color-error)" }}>{error}</p>;
  if (!prospect) return <p>Loading…</p>;

  const canEngage = CONTRACTED_OR_BEYOND.includes(prospect.stage);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem", maxWidth: "48rem" }}>
      <div>
        <Link href="/pipeline" style={{ fontSize: "0.8rem" }}>
          ← Pipeline
        </Link>
        <h1 style={{ fontSize: "1.6rem", margin: "0.2rem 0 0.3rem" }}>{prospect.company_name}</h1>
        <p style={{ margin: 0, color: "var(--color-ink-muted)", fontSize: "0.85rem" }}>
          Stage <strong>{STAGE_LABEL[prospect.stage]}</strong> · entered{" "}
          {new Date(prospect.stage_entered_at).toLocaleDateString()}
        </p>
        <div style={{ maxWidth: "16rem", marginTop: "0.5rem" }}>
          <StageMoveControl prospectId={prospect.id} currentStage={prospect.stage} onMove={onMove} />
        </div>
      </div>

      <WorkshopsSection prospectId={id} workshops={workshops} onChanged={reload} />
      <EngagementsSection prospectId={id} engagements={engagements} canEngage={canEngage} />
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section>
      <h2 style={{ fontSize: "1.1rem", marginBottom: "0.6rem" }}>{title}</h2>
      {children}
    </section>
  );
}

function WorkshopsSection({
  prospectId,
  workshops,
  onChanged,
}: {
  prospectId: string;
  workshops: Workshop[];
  onChanged: () => Promise<unknown>;
}) {
  const [scheduledFor, setScheduledFor] = useState("");
  const [brief, setBrief] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function schedule(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await api.createWorkshop({
        prospect_id: prospectId,
        scheduled_for: scheduledFor || null,
        pre_workshop_brief: brief || null,
      });
      setScheduledFor("");
      setBrief("");
      await onChanged();
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : "Could not schedule the workshop.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Section title="Workshops">
      {workshops.length === 0 ? (
        <p style={{ color: "var(--color-ink-muted)", fontSize: "0.85rem" }}>None scheduled yet.</p>
      ) : (
        <ul style={{ listStyle: "none", padding: 0, margin: "0 0 0.75rem", display: "flex", flexDirection: "column", gap: "0.4rem" }}>
          {workshops.map((w) => (
            <li key={w.id}>
              <Link
                href={`/workshops/${w.id}`}
                style={{ display: "block", padding: "0.5rem 0.7rem", border: "1px solid var(--color-border)", borderRadius: "var(--radius)", background: "var(--color-paper-raised)", textDecoration: "none", color: "inherit" }}
              >
                <strong style={{ fontSize: "0.85rem" }}>{w.state === "delivered" ? "Delivered" : "Scheduled"}</strong>{" "}
                <span className="mono" style={{ fontSize: "0.72rem", color: "var(--color-ink-muted)" }}>
                  {w.state === "delivered" ? w.delivered_on : (w.scheduled_for ?? "date TBD")}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
      <form onSubmit={schedule} style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", alignItems: "center" }}>
        <input type="date" value={scheduledFor} onChange={(e) => setScheduledFor(e.target.value)} style={inputStyle} />
        <input type="text" value={brief} onChange={(e) => setBrief(e.target.value)} placeholder="Pre-workshop brief (optional)" style={{ ...inputStyle, flex: "1 1 16rem" }} />
        <button type="submit" disabled={busy} style={btnStyle}>
          Schedule workshop
        </button>
      </form>
      {error ? <p style={{ color: "var(--color-error)", fontSize: "0.8rem" }}>{error}</p> : null}
    </Section>
  );
}

function EngagementsSection({
  prospectId,
  engagements,
  canEngage,
}: {
  prospectId: string;
  engagements: Engagement[];
  canEngage: boolean;
}) {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function open(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const created = await api.createEngagement({ prospect_id: prospectId, title: title.trim() });
      router.push(`/engagements/${created.id}`);
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : "Could not open the engagement.");
      setBusy(false);
    }
  }

  return (
    <Section title="Engagements">
      {engagements.length === 0 ? (
        <p style={{ color: "var(--color-ink-muted)", fontSize: "0.85rem" }}>None yet.</p>
      ) : (
        <ul style={{ listStyle: "none", padding: 0, margin: "0 0 0.75rem", display: "flex", flexDirection: "column", gap: "0.4rem" }}>
          {engagements.map((eng) => (
            <li key={eng.id}>
              <Link href={`/engagements/${eng.id}`} style={{ color: "inherit" }}>
                {eng.title} <span className="mono" style={{ fontSize: "0.72rem", color: "var(--color-ink-muted)" }}>· {eng.status}</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
      {canEngage ? (
        <form onSubmit={open} style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
          <input type="text" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Engagement title" required style={{ ...inputStyle, flex: "1 1 16rem" }} />
          <button type="submit" disabled={busy || !title.trim()} style={btnStyle}>
            Open engagement
          </button>
        </form>
      ) : (
        <p style={{ color: "var(--color-ink-muted)", fontSize: "0.8rem" }}>
          Move this prospect to Contracted to open an engagement.
        </p>
      )}
      {error ? <p style={{ color: "var(--color-error)", fontSize: "0.8rem" }}>{error}</p> : null}
    </Section>
  );
}

const inputStyle: React.CSSProperties = {
  padding: "0.45rem 0.6rem",
  fontFamily: "inherit",
  fontSize: "0.85rem",
  border: "1px solid var(--color-border)",
  borderRadius: "var(--radius)",
  background: "var(--color-paper-raised)",
};

const btnStyle: React.CSSProperties = {
  padding: "0.45rem 1rem",
  fontSize: "0.85rem",
  color: "var(--color-accent-contrast)",
  background: "var(--color-accent)",
  border: "none",
  borderRadius: "var(--radius)",
  cursor: "pointer",
};
