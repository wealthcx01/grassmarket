/**
 * The pipeline board (GRS-0111 CRM rebuild) — the advisor CRM's main view. A KPI strip, search +
 * filters, a drag-and-drop kanban over the ten stages, and a click-to-open deal slide-over. Moving a
 * card is optimistic; the backend owns legality, so an illegal drop reverts with the reason. Scoping
 * is server-enforced; the client only carries the JWT.
 */

"use client";

import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

import { KanbanBoard } from "@/components/KanbanBoard";
import { DealDetailPanel } from "@/components/DealDetailPanel";
import { ApiError, api, clearToken, getToken } from "@/lib/api";
import type { PipelineBoard, PipelineBoardEntry, PipelineForecast, PipelineStage } from "@/lib/types";

function Kpi({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div
      style={{
        padding: "0.7rem 0.9rem",
        background: "var(--color-paper-raised)",
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius)",
        minWidth: "8rem",
      }}
    >
      <p className="mono" style={{ margin: 0, fontSize: "0.6rem", letterSpacing: "0.08em", textTransform: "uppercase", color: "var(--color-ink-muted)" }}>
        {label}
      </p>
      <p style={{ margin: "0.25rem 0 0", fontSize: "1.4rem", fontWeight: 600 }}>{value}</p>
      {hint ? <p style={{ margin: "0.1rem 0 0", fontSize: "0.68rem", color: "var(--color-ink-faint)" }}>{hint}</p> : null}
    </div>
  );
}

export default function PipelinePage() {
  const router = useRouter();
  const [board, setBoard] = useState<PipelineBoard | null>(null);
  const [forecast, setForecast] = useState<PipelineForecast | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [company, setCompany] = useState("");
  const [creating, setCreating] = useState(false);
  const [query, setQuery] = useState("");
  const [staleOnly, setStaleOnly] = useState(false);
  const [openId, setOpenId] = useState<string | null>(null);

  const reload = useCallback(
    (signal?: AbortSignal) => {
      return Promise.all([api.pipelineBoard(signal), api.pipelineForecast(signal)])
        .then(([b, f]) => {
          setBoard(b);
          setForecast(f);
        })
        .catch((err: unknown) => {
          if (err instanceof ApiError && err.status === 0) return;
          if (err instanceof ApiError && err.status === 401) {
            clearToken();
            router.replace("/login");
            return;
          }
          setError(err instanceof ApiError ? err.message : "Could not load the pipeline.");
        });
    },
    [router],
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

  // Optimistic move: land the card immediately, then confirm with the backend. On a 409 (illegal
  // move) the reload restores the true state and we surface the reason.
  const onMove = useCallback(
    async (id: string, stage: PipelineStage) => {
      setNotice(null);
      setBoard((prev) =>
        prev
          ? {
              ...prev,
              entries: prev.entries.map((e) =>
                e.prospect.id === id ? { ...e, prospect: { ...e.prospect, stage } } : e,
              ),
            }
          : prev,
      );
      try {
        await api.updateProspectStage(id, stage);
        await reload();
      } catch (err: unknown) {
        await reload(); // snap back to the truth
        setNotice(err instanceof ApiError ? err.message : "That move isn't allowed.");
        throw err;
      }
    },
    [reload],
  );

  async function onCreate(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!company.trim()) return;
    setCreating(true);
    try {
      await api.createProspect({ company_name: company.trim() });
      setCompany("");
      await reload();
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : "Could not create the prospect.");
    } finally {
      setCreating(false);
    }
  }

  const filtered = useMemo<PipelineBoard | null>(() => {
    if (!board) return null;
    const q = query.trim().toLowerCase();
    const entries = board.entries.filter((e) => {
      if (staleOnly && !e.stale) return false;
      if (!q) return true;
      const hay = `${e.prospect.company_name} ${e.prospect.primary_contact_name ?? ""} ${e.prospect.sector ?? ""}`.toLowerCase();
      return hay.includes(q);
    });
    return { ...board, entries };
  }, [board, query, staleOnly]);

  const staleCount = board?.entries.filter((e) => e.stale).length ?? 0;
  const openEntry: PipelineBoardEntry | null =
    (openId && board?.entries.find((e) => e.prospect.id === openId)) || null;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.1rem" }}>
      <section style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", flexWrap: "wrap", gap: "0.75rem" }}>
        <div>
          <p className="mono" style={{ margin: 0, fontSize: "0.72rem", letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--color-ink-muted)" }}>
            Advisor CRM · your pipeline
          </p>
          <h1 style={{ fontSize: "2rem", margin: "0.3rem 0 0" }}>Pipeline</h1>
        </div>
        <form onSubmit={onCreate} style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
          <input
            type="text"
            value={company}
            onChange={(e) => setCompany(e.target.value)}
            placeholder="New prospect — company name"
            style={{
              flex: "1 1 16rem",
              padding: "0.5rem 0.7rem",
              fontFamily: "inherit",
              border: "1px solid var(--color-border)",
              borderRadius: "var(--radius)",
              background: "var(--color-paper-raised)",
            }}
          />
          <button type="submit" className="btn btn-primary" disabled={creating || !company.trim()}>
            {creating ? "Adding…" : "Add prospect"}
          </button>
        </form>
      </section>

      {/* KPI strip */}
      {forecast ? (
        <div style={{ display: "flex", gap: "0.6rem", flexWrap: "wrap" }}>
          <Kpi label="Prospects" value={String(forecast.total_prospects)} />
          <Kpi label="Open" value={String(forecast.open_prospects)} hint="not terminal" />
          <Kpi label="Expected wins" value={forecast.weighted_expected_deals.toFixed(1)} hint="open pipeline, Σ win-probabilities" />
          <Kpi label="Stale" value={String(staleCount)} hint="past time-in-stage" />
        </div>
      ) : null}

      {/* Search + filters */}
      <div style={{ display: "flex", gap: "0.6rem", alignItems: "center", flexWrap: "wrap" }}>
        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search company, contact, sector…"
          aria-label="Search prospects"
          style={{ flex: "1 1 16rem", padding: "0.45rem 0.7rem", fontFamily: "inherit", border: "1px solid var(--color-border)", borderRadius: "var(--radius)", background: "var(--color-paper-raised)" }}
        />
        <label style={{ display: "inline-flex", alignItems: "center", gap: "0.4rem", fontSize: "0.82rem", color: "var(--color-ink-muted)" }}>
          <input type="checkbox" checked={staleOnly} onChange={(e) => setStaleOnly(e.target.checked)} />
          Stale only
        </label>
      </div>

      {error ? (
        <p role="alert" style={{ color: "var(--color-error)", fontSize: "0.9rem" }}>
          {error}
        </p>
      ) : null}
      {notice ? (
        <p role="status" style={{ color: "var(--color-warn)", fontSize: "0.85rem" }}>
          {notice}
        </p>
      ) : null}

      {filtered ? (
        <KanbanBoard board={filtered} onOpen={setOpenId} onMove={onMove} />
      ) : (
        <p>Loading…</p>
      )}

      {openEntry ? (
        <DealDetailPanel entry={openEntry} onClose={() => setOpenId(null)} onChanged={reload} />
      ) : null}

      <footer style={{ fontSize: "0.8rem", color: "var(--color-ink-muted)" }}>
        <Link href="/">← Dashboard</Link> · <Link href="/engagements">Engagements</Link>
      </footer>
    </div>
  );
}
