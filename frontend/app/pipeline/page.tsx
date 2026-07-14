/**
 * The pipeline board (GRS-0014) — the advisor CRM's main view. Kanban over the ten stages plus the
 * currency-free forecast. Moving a card calls the transition endpoint; the backend owns legality.
 * Scoping is server-enforced; the client only carries the JWT.
 */

"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

import { ForecastPanel } from "@/components/ForecastPanel";
import { KanbanBoard } from "@/components/KanbanBoard";
import { ApiError, api, getToken } from "@/lib/api";
import type { PipelineBoard, PipelineForecast, PipelineStage } from "@/lib/types";

export default function PipelinePage() {
  const router = useRouter();
  const [board, setBoard] = useState<PipelineBoard | null>(null);
  const [forecast, setForecast] = useState<PipelineForecast | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [company, setCompany] = useState("");
  const [creating, setCreating] = useState(false);

  const reload = useCallback((signal?: AbortSignal) => {
    return Promise.all([api.pipelineBoard(signal), api.pipelineForecast(signal)])
      .then(([b, f]) => {
        setBoard(b);
        setForecast(f);
      })
      .catch((err: unknown) => {
        if (err instanceof ApiError && err.status === 0) return;
        setError(err instanceof ApiError ? err.message : "Could not load the pipeline.");
      });
  }, []);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    const ctrl = new AbortController();
    reload(ctrl.signal);
    return () => ctrl.abort();
  }, [router, reload]);

  // The move goes to the backend; on success we reload so the card lands in its new column. On a
  // refusal StageMoveControl reverts and shows the reason — we let that error propagate to it.
  const onMove = useCallback(
    async (id: string, stage: PipelineStage) => {
      await api.updateProspectStage(id, stage);
      await reload();
    },
    [reload],
  );

  async function onCreate(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!company.trim()) return;
    setCreating(true);
    try {
      await api.createProspect(company.trim());
      setCompany("");
      await reload();
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : "Could not create the prospect.");
    } finally {
      setCreating(false);
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
      <section>
        <p
          className="mono"
          style={{ margin: 0, fontSize: "0.72rem", letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--color-ink-muted)" }}
        >
          Advisor CRM · your pipeline
        </p>
        <h1 style={{ fontSize: "2rem", margin: "0.3rem 0 0" }}>Pipeline</h1>
      </section>

      <form onSubmit={onCreate} style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
        <input
          type="text"
          value={company}
          onChange={(e) => setCompany(e.target.value)}
          placeholder="New prospect — company name"
          style={{
            flex: "1 1 18rem",
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

      {error ? (
        <p role="alert" style={{ color: "var(--color-error)", fontSize: "0.9rem" }}>
          {error}
        </p>
      ) : null}

      {forecast ? <ForecastPanel forecast={forecast} /> : null}
      {board ? <KanbanBoard board={board} onMove={onMove} /> : <p>Loading…</p>}

      <footer style={{ fontSize: "0.8rem", color: "var(--color-ink-muted)" }}>
        <Link href="/">← Dashboard</Link> · <Link href="/engagements">Engagements</Link>
      </footer>
    </div>
  );
}
