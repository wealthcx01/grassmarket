/**
 * The kanban move control (GRS-0014). Picking a target stage calls `onMove` — but the BACKEND owns
 * legality. The move is applied optimistically; if the backend refuses (an illegal transition is a
 * 409), the card **reverts** to its previous stage and the reason is surfaced. It never silently
 * allows or fakes a move the backend rejected.
 */

"use client";

import { useState } from "react";

import { ApiError } from "@/lib/api";
import { PIPELINE_STAGES, type PipelineStage } from "@/lib/types";

export function StageMoveControl({
  prospectId,
  currentStage,
  onMove,
}: {
  prospectId: string;
  currentStage: PipelineStage;
  onMove: (id: string, stage: PipelineStage) => Promise<unknown>;
}) {
  const [stage, setStage] = useState<PipelineStage>(currentStage);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function change(next: PipelineStage) {
    if (next === stage) return;
    const previous = stage;
    setStage(next); // optimistic
    setError(null);
    setBusy(true);
    try {
      await onMove(prospectId, next);
    } catch (err: unknown) {
      setStage(previous); // the backend refused — revert, never fake the move
      setError(err instanceof ApiError ? err.message : "Move failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <select
        aria-label="Move stage"
        data-testid="stage-select"
        value={stage}
        disabled={busy}
        onChange={(e) => change(e.target.value as PipelineStage)}
        style={{
          width: "100%",
          fontSize: "0.72rem",
          padding: "0.2rem 0.3rem",
          border: "1px solid var(--color-border)",
          borderRadius: "var(--radius)",
          background: "var(--color-paper)",
        }}
      >
        {PIPELINE_STAGES.map((s) => (
          <option key={s.stage} value={s.stage}>
            {s.label}
          </option>
        ))}
      </select>
      {error ? (
        <p
          role="alert"
          data-testid="move-error"
          style={{ margin: "0.3rem 0 0", fontSize: "0.7rem", color: "var(--color-error)" }}
        >
          {error}
        </p>
      ) : null}
    </div>
  );
}
