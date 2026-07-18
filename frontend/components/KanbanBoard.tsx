/**
 * The pipeline kanban (GRS-0111 CRM rebuild). Ten stage columns rendered from /pipeline/board.
 * Cards are DRAGGABLE (@dnd-kit) between columns; a drop calls onMove(id, targetStage). The BACKEND
 * owns legality — the parent applies the move optimistically and reverts + surfaces the reason on a
 * 409, so an illegal drop snaps back. A plain click (no drag past ~5px) opens the deal slide-over.
 * StageMoveControl stays on the card as the keyboard/mobile-accessible fallback.
 */

"use client";

import { useState } from "react";
import {
  DndContext,
  DragOverlay,
  KeyboardSensor,
  PointerSensor,
  closestCorners,
  useDraggable,
  useDroppable,
  useSensor,
  useSensors,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import { CSS } from "@dnd-kit/utilities";

import { StageMoveControl } from "@/components/StageMoveControl";
import {
  PIPELINE_STAGES,
  STAGE_LABEL,
  type PipelineBoard,
  type PipelineBoardEntry,
  type PipelineStage,
  type WinProbability,
} from "@/lib/types";

// Semantic band → colour (a probability, never currency; not the accent).
const WIN_BAND_COLOR: Record<string, string> = {
  Strong: "var(--color-accent)",
  Likely: "var(--color-accent)",
  Warming: "var(--color-warn)",
  Cold: "var(--color-ink-muted)",
};

export function WinProbabilityPill({ wp }: { wp: WinProbability }) {
  const color = WIN_BAND_COLOR[wp.label] ?? "var(--color-ink-muted)";
  const gaps = wp.missing_info.length;
  return (
    <span
      className="mono"
      title={
        `Win probability ${wp.score}% · ${wp.label}\n` +
        wp.reasons.join("\n") +
        (gaps ? `\n\nWould sharpen the estimate:\n${wp.missing_info.join("\n")}` : "")
      }
      style={{
        flex: "0 0 auto",
        fontSize: "0.62rem",
        fontWeight: 600,
        color,
        border: `1px solid ${color}`,
        borderRadius: "999px",
        padding: "0 0.35rem",
        whiteSpace: "nowrap",
      }}
    >
      {wp.score}%{gaps ? " ·" : ""}
    </span>
  );
}

function CardBody({ entry }: { entry: PipelineBoardEntry }) {
  const { prospect, days_in_stage, stale, win_probability } = entry;
  const contact = prospect.primary_contact_name;
  return (
    <>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: "0.4rem" }}>
        <span style={{ fontSize: "0.85rem", fontWeight: 600, lineHeight: 1.25 }}>
          {prospect.company_name}
        </span>
        <WinProbabilityPill wp={win_probability} />
      </div>
      {contact || prospect.sector ? (
        <div style={{ marginTop: "0.3rem", display: "flex", flexWrap: "wrap", gap: "0.3rem", alignItems: "center" }}>
          {contact ? (
            <span style={{ fontSize: "0.72rem", color: "var(--color-ink-muted)" }}>{contact}</span>
          ) : null}
          {prospect.sector ? (
            <span className="tag" style={{ fontSize: "0.62rem" }}>
              {prospect.sector}
            </span>
          ) : null}
        </div>
      ) : null}
      <div
        style={{
          marginTop: "0.4rem",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          fontSize: "0.66rem",
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
    </>
  );
}

function DraggableCard({
  entry,
  onOpen,
  onMove,
}: {
  entry: PipelineBoardEntry;
  onOpen: (id: string) => void;
  onMove: (id: string, stage: PipelineStage) => Promise<unknown>;
}) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: entry.prospect.id,
  });
  return (
    <article
      ref={setNodeRef}
      style={{
        background: "var(--color-paper-raised)",
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius)",
        padding: "0.5rem 0.6rem",
        transform: CSS.Translate.toString(transform),
        opacity: isDragging ? 0.35 : 1,
        touchAction: "none",
      }}
    >
      {/* The draggable + clickable surface. A 5px activation constraint keeps a click a click. */}
      <button
        type="button"
        onClick={() => onOpen(entry.prospect.id)}
        {...listeners}
        {...attributes}
        aria-label={`Open ${entry.prospect.company_name}`}
        style={{
          display: "block",
          width: "100%",
          textAlign: "left",
          background: "none",
          border: "none",
          padding: 0,
          cursor: "grab",
          color: "inherit",
          font: "inherit",
        }}
      >
        <CardBody entry={entry} />
      </button>
      <div style={{ marginTop: "0.4rem" }}>
        <StageMoveControl prospectId={entry.prospect.id} currentStage={entry.prospect.stage} onMove={onMove} />
      </div>
    </article>
  );
}

function Column({
  stage,
  label,
  entries,
  onOpen,
  onMove,
}: {
  stage: PipelineStage;
  label: string;
  entries: PipelineBoardEntry[];
  onOpen: (id: string) => void;
  onMove: (id: string, stage: PipelineStage) => Promise<unknown>;
}) {
  const { setNodeRef, isOver } = useDroppable({ id: stage });
  return (
    <section
      ref={setNodeRef}
      aria-label={label}
      style={{
        flex: "0 0 15rem",
        display: "flex",
        flexDirection: "column",
        gap: "0.5rem",
        padding: "0.5rem",
        borderRadius: "var(--radius)",
        background: isOver ? "var(--color-paper-raised)" : "transparent",
        outline: isOver ? "2px dashed var(--color-accent)" : "1px solid var(--color-border)",
        minHeight: "6rem",
        transition: "outline-color 0.12s, background 0.12s",
      }}
    >
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
        <h3 style={{ margin: 0, fontSize: "0.78rem", fontWeight: 600 }}>{label}</h3>
        <span className="mono" style={{ fontSize: "0.7rem", color: "var(--color-ink-muted)" }}>
          {entries.length}
        </span>
      </header>
      {entries.length === 0 ? (
        <p style={{ margin: 0, fontSize: "0.72rem", color: "var(--color-ink-faint)", padding: "0.4rem 0" }}>
          No prospects
        </p>
      ) : (
        entries.map((e) => (
          <DraggableCard key={e.prospect.id} entry={e} onOpen={onOpen} onMove={onMove} />
        ))
      )}
    </section>
  );
}

export function KanbanBoard({
  board,
  onOpen,
  onMove,
}: {
  board: PipelineBoard;
  onOpen: (id: string) => void;
  onMove: (id: string, stage: PipelineStage) => Promise<unknown>;
}) {
  const [activeId, setActiveId] = useState<string | null>(null);
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor),
  );

  const byStage = new Map<PipelineStage, PipelineBoardEntry[]>(
    PIPELINE_STAGES.map((s) => [s.stage, []]),
  );
  for (const entry of board.entries) byStage.get(entry.prospect.stage)?.push(entry);
  const activeEntry = board.entries.find((e) => e.prospect.id === activeId) ?? null;

  function onDragStart(event: DragStartEvent) {
    setActiveId(String(event.active.id));
  }
  function onDragEnd(event: DragEndEvent) {
    setActiveId(null);
    const { active, over } = event;
    if (!over) return;
    const entry = board.entries.find((e) => e.prospect.id === active.id);
    const target = over.id as PipelineStage;
    if (entry && entry.prospect.stage !== target) {
      void onMove(String(active.id), target);
    }
  }

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCorners}
      onDragStart={onDragStart}
      onDragEnd={onDragEnd}
      onDragCancel={() => setActiveId(null)}
    >
      <div style={{ display: "flex", gap: "0.75rem", overflowX: "auto", paddingBottom: "0.5rem" }}>
        {PIPELINE_STAGES.map((s) => (
          <Column
            key={s.stage}
            stage={s.stage}
            label={s.label}
            entries={byStage.get(s.stage) ?? []}
            onOpen={onOpen}
            onMove={onMove}
          />
        ))}
      </div>
      <DragOverlay dropAnimation={null}>
        {activeEntry ? (
          <article
            style={{
              background: "var(--color-paper-raised)",
              border: "1px solid var(--color-accent)",
              borderRadius: "var(--radius)",
              padding: "0.5rem 0.6rem",
              width: "13.8rem",
              boxShadow: "0 6px 18px rgba(0,0,0,0.2)",
              cursor: "grabbing",
            }}
          >
            <CardBody entry={activeEntry} />
          </article>
        ) : null}
      </DragOverlay>
    </DndContext>
  );
}

// Re-export for callers that only need the stage label map.
export { STAGE_LABEL };
