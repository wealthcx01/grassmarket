/**
 * Review what a voice note suggests, correct it, and confirm (GRS-0249 scope 4).
 *
 * This is the gate. Everything the advisor sees here is a suggestion sitting on a proposal record;
 * the prospect has not moved and will not move until they press confirm — non-negotiable #8, *AI
 * proposes, humans approve*.
 *
 * Three things the screen has to be honest about, and they are why it looks the way it does:
 *
 * **Confirming names what it confirms.** Each field has its own tick. There is no "accept all",
 * because an approval that does not say what it approves is not an approval. Unticked fields are
 * not sent, however confident the extractor was.
 *
 * **A correction is visible as a correction.** Edit a field and the original suggestion stays on
 * screen beneath it. The server keeps both too, so afterwards anyone can tell a corrected field
 * from an accepted one.
 *
 * **What it did not hear is said out loud.** Fields the extractor looked for and could not fill
 * are listed as gaps rather than shown as empty boxes, because an empty box reads like a
 * considered answer of "nothing".
 */

"use client";

import { useMemo, useState } from "react";

import { ApiError, api } from "@/lib/api";
import {
  PIPELINE_FIELD_LABEL,
  STAGE_LABEL,
  type ExtractionConfidence,
  type PipelineField,
  type PipelineStage,
  type VoiceNoteProposal,
} from "@/lib/types";

/** Stages an advisor can pick. The server still refuses an illegal move; this only narrows it. */
const STAGES: PipelineStage[] = [
  "prospect",
  "workshop_scheduled",
  "workshop_delivered",
  "qualified",
  "scoped",
  "contracted",
  "active",
  "delivered",
  "closed",
  "nurture",
];

type Answer = { include: boolean; value: string };

export function ProposalReview({
  proposal,
  onDone,
}: {
  proposal: VoiceNoteProposal;
  onDone: (result: VoiceNoteProposal) => void;
}) {
  // Nothing starts ticked. The advisor opts each field in, which is what makes the confirmation
  // an act rather than a default.
  const [answers, setAnswers] = useState<Record<string, Answer>>(() =>
    Object.fromEntries(
      proposal.fields.map((f) => [f.field, { include: false, value: f.proposed_value ?? "" }]),
    ),
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const chosen = useMemo(
    () => proposal.fields.filter((f) => answers[f.field]?.include).length,
    [proposal.fields, answers],
  );

  function set(field: PipelineField, patch: Partial<Answer>) {
    setAnswers((prev) => ({ ...prev, [field]: { ...prev[field]!, ...patch } }));
  }

  async function confirm() {
    setBusy(true);
    setError(null);
    try {
      const fields: Partial<Record<PipelineField, string | null>> = {};
      for (const f of proposal.fields) {
        const answer = answers[f.field];
        if (answer?.include && answer.value.trim()) fields[f.field] = answer.value.trim();
      }
      onDone(await api.confirmVoiceNoteProposal(proposal.id, fields));
    } catch (err: unknown) {
      // A 409 is the advisor's problem to solve, not a crash: an illegal stage move, a date the
      // server could not read, or no engagement to file the note against. Show the reason.
      setError(err instanceof ApiError ? err.message : "Could not apply the update.");
      setBusy(false);
    }
  }

  async function discard() {
    setBusy(true);
    setError(null);
    try {
      onDone(await api.discardVoiceNoteProposal(proposal.id));
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : "Could not discard the proposal.");
      setBusy(false);
    }
  }

  if (proposal.fields.length === 0) {
    return (
      <div style={notice}>
        <strong style={{ fontSize: "0.85rem" }}>Nothing was suggested from this note.</strong>
        <p style={{ ...caption, marginBottom: 0 }}>
          {proposal.gaps.length > 0
            ? `Listened for ${proposal.gaps
                .map((g) => PIPELINE_FIELD_LABEL[g as PipelineField] ?? g)
                .join(", ")
                .toLowerCase()} and found none of them. Update the prospect yourself if the note said something.`
            : "The transcript is still there to read."}
        </p>
      </div>
    );
  }

  return (
    <div style={notice}>
      <strong style={{ fontSize: "0.85rem" }}>Suggested from this note</strong>
      <p style={{ ...caption, marginTop: "0.2rem" }}>
        Nothing below has happened yet. Tick what you agree with, change anything that is wrong,
        then confirm. What you tick is what gets applied.
      </p>

      <ul style={{ listStyle: "none", padding: 0, margin: "0 0 0.8rem", display: "flex", flexDirection: "column", gap: "0.7rem" }}>
        {proposal.fields.map((f) => {
          const answer = answers[f.field]!;
          const edited = answer.value.trim() !== (f.proposed_value ?? "");
          return (
            <li
              key={f.id}
              style={{
                border: "1px solid var(--color-border)",
                borderRadius: "var(--radius)",
                padding: "0.6rem 0.7rem",
                background: answer.include ? "var(--color-accent-tint)" : "var(--color-paper)",
              }}
            >
              {/* Wraps on a narrow screen: at 393px "Move to stage" already takes two lines, and
                  the confidence tag beside it squeezed both into something cramped. */}
              <label
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "0.4rem 0.5rem",
                  flexWrap: "wrap",
                  cursor: "pointer",
                }}
              >
                <input
                  type="checkbox"
                  checked={answer.include}
                  onChange={(e) => set(f.field, { include: e.target.checked })}
                />
                <span style={{ fontSize: "0.85rem", fontWeight: 600 }}>
                  {PIPELINE_FIELD_LABEL[f.field]}
                </span>
                <ConfidenceTag confidence={f.confidence} />
              </label>

              <div style={{ marginTop: "0.5rem", paddingLeft: "1.4rem" }}>
                {f.field === "stage" ? (
                  <select
                    value={answer.value}
                    onChange={(e) => set(f.field, { value: e.target.value })}
                    style={{ fontSize: "0.85rem", maxWidth: "16rem" }}
                  >
                    {STAGES.map((s) => (
                      <option key={s} value={s}>
                        {STAGE_LABEL[s]}
                      </option>
                    ))}
                  </select>
                ) : f.field === "next_action_on" ? (
                  <input
                    type="date"
                    value={answer.value}
                    onChange={(e) => set(f.field, { value: e.target.value })}
                    style={{ fontSize: "0.85rem" }}
                  />
                ) : (
                  <input
                    type="text"
                    value={answer.value}
                    onChange={(e) => set(f.field, { value: e.target.value })}
                    style={{ fontSize: "0.85rem", width: "100%" }}
                  />
                )}

                {/* The original stays visible once changed. A correction the screen hides is a
                    correction nobody can check. */}
                {edited ? (
                  <p style={{ ...caption, margin: "0.35rem 0 0" }}>
                    Suggested:{" "}
                    <span className="mono" style={{ fontSize: "0.72rem" }}>
                      {f.proposed_value || "nothing"}
                    </span>
                  </p>
                ) : null}
              </div>
            </li>
          );
        })}
      </ul>

      {proposal.gaps.length > 0 ? (
        <p style={{ ...caption, marginTop: 0 }}>
          Nothing heard about:{" "}
          {proposal.gaps.map((g) => PIPELINE_FIELD_LABEL[g as PipelineField] ?? g).join(", ").toLowerCase()}.
        </p>
      ) : null}

      {error ? (
        <p style={{ color: "var(--color-error)", fontSize: "0.82rem", margin: "0 0 0.6rem" }}>{error}</p>
      ) : null}

      <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", alignItems: "center" }}>
        <button type="button" className="btn btn-primary" onClick={confirm} disabled={busy || chosen === 0}>
          {chosen === 0
            ? "Tick what to apply"
            : chosen === 1
              ? "Apply 1 change"
              : `Apply ${chosen} changes`}
        </button>
        <button type="button" className="btn" onClick={discard} disabled={busy}>
          None of this is right
        </button>
      </div>
    </div>
  );
}

function ConfidenceTag({ confidence }: { confidence: ExtractionConfidence }) {
  // Three words, no colour scale. A green "high" would invite the advisor to skim past it, and
  // the machine's confidence is not evidence — it is the machine's opinion of itself.
  return (
    <span
      className="mono"
      style={{
        fontSize: "0.68rem",
        textTransform: "uppercase",
        letterSpacing: "0.04em",
        color: "var(--color-ink-muted)",
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-sm)",
        padding: "0.05rem 0.35rem",
      }}
    >
      {confidence} confidence
    </span>
  );
}

const notice: React.CSSProperties = {
  border: "1px solid var(--color-border)",
  borderRadius: "var(--radius-lg)",
  background: "var(--color-paper-raised)",
  padding: "0.9rem",
};

const caption: React.CSSProperties = {
  fontSize: "0.78rem",
  color: "var(--color-ink-muted)",
  margin: "0.5rem 0",
  lineHeight: 1.5,
};
