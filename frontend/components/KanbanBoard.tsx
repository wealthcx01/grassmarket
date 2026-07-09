/**
 * The pipeline kanban (GRS-0014). Ten columns (the stages, in order) rendered from /pipeline/board;
 * each card shows time-in-stage and a stale flag. Moving a card goes through StageMoveControl, which
 * lets the backend decide legality and reverts on refusal.
 */

"use client";

import Link from "next/link";

import { StageMoveControl } from "@/components/StageMoveControl";
import {
  PIPELINE_STAGES,
  type PipelineBoard,
  type PipelineBoardEntry,
  type PipelineStage,
} from "@/lib/types";

export function KanbanBoard({
  board,
  onMove,
}: {
  board: PipelineBoard;
  onMove: (id: string, stage: PipelineStage) => Promise<unknown>;
}) {
  const byStage = new Map<PipelineStage, PipelineBoardEntry[]>();
  for (const s of PIPELINE_STAGES) byStage.set(s.stage, []);
  for (const entry of board.entries) byStage.get(entry.prospect.stage)?.push(entry);

  return (
    <div style={{ display: "flex", gap: "0.75rem", overflowX: "auto", paddingBottom: "0.5rem" }}>
      {PIPELINE_STAGES.map((col) => {
        const entries = byStage.get(col.stage) ?? [];
        return (
          <section
            key={col.stage}
            style={{
              flex: "0 0 15rem",
              minWidth: "15rem",
              background: "var(--color-paper)",
              border: "1px solid var(--color-border)",
              borderRadius: "var(--radius)",
              padding: "0.5rem",
            }}
          >
            <header
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "baseline",
                marginBottom: "0.5rem",
              }}
            >
              <span style={{ fontSize: "0.78rem", fontWeight: 600 }}>{col.label}</span>
              <span className="mono" style={{ fontSize: "0.7rem", color: "var(--color-ink-muted)" }}>
                {entries.length}
              </span>
            </header>
            <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
              {entries.map((entry) => (
                <ProspectCard key={entry.prospect.id} entry={entry} onMove={onMove} />
              ))}
            </div>
          </section>
        );
      })}
    </div>
  );
}

function ProspectCard({
  entry,
  onMove,
}: {
  entry: PipelineBoardEntry;
  onMove: (id: string, stage: PipelineStage) => Promise<unknown>;
}) {
  const { prospect, days_in_stage, stale } = entry;
  return (
    <article
      style={{
        background: "var(--color-paper-raised)",
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius)",
        padding: "0.5rem 0.6rem",
      }}
    >
      <Link
        href={`/prospects/${prospect.id}`}
        style={{ fontSize: "0.85rem", fontWeight: 600, textDecoration: "none", color: "inherit" }}
      >
        {prospect.company_name}
      </Link>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          margin: "0.3rem 0",
          fontSize: "0.68rem",
          color: "var(--color-ink-muted)",
        }}
      >
        <span className="mono">{days_in_stage}d in stage</span>
        {stale ? (
          <span
            style={{
              color: "var(--color-warn)",
              fontWeight: 600,
              border: "1px solid var(--color-warn)",
              borderRadius: "999px",
              padding: "0 0.4rem",
            }}
          >
            stale
          </span>
        ) : null}
      </div>
      <StageMoveControl prospectId={prospect.id} currentStage={prospect.stage} onMove={onMove} />
    </article>
  );
}
