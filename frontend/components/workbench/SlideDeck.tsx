/**
 * The slide reader (GRS-0226) — the surface that finally shows GRS-0216's 196 slides and
 * GRS-0225's diagrams to an advisor.
 *
 * One slide at a time, deliberately. The founder's standard is "20-40 slides of interactive
 * detail", and a lesson rendered as one long scroll is the paragraph problem again with more
 * words in it: nothing marks where one idea ends and the next begins, and a checkpoint slide
 * scrolls past as prose rather than stopping the advisor to do something.
 *
 * Slide assets reuse `LessonBody`'s sanitising `Asset` renderer rather than a second copy of it,
 * so a diagram that fails sanitisation is announced in both places identically.
 */

"use client";

import { useState } from "react";

import { renderMarkdown } from "@/lib/markdown";
import type { Slide, SlideKind } from "@/lib/types";

import { LessonAssetFigure } from "./LessonBody";
import { LessonReferences } from "./LessonReferences";

/** What each kind is called in the reader, and the colour that carries it. */
const KIND_LABEL: Record<SlideKind, string> = {
  concept: "Concept",
  walkthrough: "Walkthrough",
  example: "Example",
  checkpoint: "Checkpoint",
};

const KIND_COLOR: Record<SlideKind, string> = {
  concept: "var(--color-ink-muted)",
  walkthrough: "var(--color-accent)",
  example: "var(--color-ink-muted)",
  checkpoint: "var(--color-accent)",
};

export function SlideView({
  slide,
  onConfirm,
  confirmed = false,
}: {
  slide: Slide;
  /** GRS-0239 scope 3. Absent when the deck has no lesson to confirm against (e.g. a preview). */
  onConfirm?: (slideOrder: number) => Promise<void> | void;
  confirmed?: boolean;
}) {
  return (
    <div>
      <div style={{ display: "flex", alignItems: "baseline", gap: "0.5rem", flexWrap: "wrap" }}>
        <span
          className="mono"
          style={{ fontSize: "0.6rem", fontWeight: 600, color: KIND_COLOR[slide.kind] }}
        >
          {KIND_LABEL[slide.kind].toUpperCase()}
        </span>
        <h4 style={{ margin: 0, fontSize: "0.95rem" }}>{slide.title}</h4>
      </div>
      <div style={{ marginTop: "0.5rem" }}>{renderMarkdown(slide.body)}</div>
      {slide.asset ? <LessonAssetFigure asset={slide.asset} /> : null}
      {slide.checkpoint_prompt ? (
        <div
          className="callout"
          style={{
            marginTop: "0.8rem",
            borderLeft: "2px solid var(--color-accent)",
            paddingLeft: "0.6rem",
            fontSize: "0.85rem",
          }}
        >
          <p style={{ margin: 0 }}>
            <strong>Do this now: </strong>
            {slide.checkpoint_prompt}
          </p>
          {/* GRS-0239 scope 3. Until now this callout said "Do this now" and offered nothing to do
              it WITH — no control, no state, no record — while the content contract promised "the
              advisor produces something and confirms they did". An instruction with no way to
              acknowledge it teaches an advisor that the instruction is decorative. */}
          {onConfirm ? (
            <CheckpointConfirm
              slideOrder={slide.order}
              confirmed={confirmed}
              onConfirm={onConfirm}
            />
          ) : null}
        </div>
      ) : null}
      {/* GRS-0239 scope 2: a footnote, not a card strip. Every claim stays sourced — that is
          doctrine — but a slide should read as teaching, not as a set of links. */}
      <LessonReferences references={slide.references} variant="footnote" />
    </div>
  );
}

export function SlideDeck({
  slides,
  label,
  onConfirmCheckpoint,
  confirmedOrders,
}: {
  slides: readonly Slide[];
  label: string;
  onConfirmCheckpoint?: (slideOrder: number) => Promise<void> | void;
  /** Slide positions this advisor has already confirmed (GRS-0239 scope 3). */
  confirmedOrders?: ReadonlySet<number>;
}) {
  const ordered = [...slides].sort((a, b) => a.order - b.order);
  const [index, setIndex] = useState(0);
  if (ordered.length === 0) return null;
  // Guard the index rather than trust it: `slides` can change under the component when a course
  // is republished, and an out-of-range index would render nothing with no explanation.
  const current = ordered[Math.min(index, ordered.length - 1)]!;
  const position = Math.min(index, ordered.length - 1);

  return (
    <section
      aria-label={`${label} slides`}
      style={{
        marginTop: "0.7rem",
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius)",
        background: "var(--color-paper)",
        padding: "0.9rem 1rem",
      }}
    >
      <SlideView
        slide={current}
        onConfirm={onConfirmCheckpoint}
        confirmed={confirmedOrders?.has(current.order) ?? false}
      />

      <div
        style={{
          marginTop: "1rem",
          paddingTop: "0.7rem",
          borderTop: "1px solid var(--color-border)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "0.6rem",
        }}
      >
        <button
          type="button"
          className="btn"
          disabled={position === 0}
          onClick={() => setIndex(position - 1)}
          style={{ fontSize: "0.76rem" }}
        >
          ← Previous
        </button>
        <span className="mono" style={{ fontSize: "0.68rem", color: "var(--color-ink-faint)" }}>
          Slide {position + 1} of {ordered.length}
        </span>
        <button
          type="button"
          className="btn"
          disabled={position === ordered.length - 1}
          onClick={() => setIndex(position + 1)}
          style={{ fontSize: "0.76rem" }}
        >
          Next →
        </button>
      </div>
    </section>
  );
}


/**
 * The "I did this" control on a checkpoint slide (GRS-0239 scope 3).
 *
 * Self-reported and deliberately so: nothing here can verify that an advisor really opened the
 * wizard and rated a module. What it can do is make the claim explicit and recorded, which is the
 * difference between a lesson you worked through and one you scrolled past.
 *
 * It does NOT un-confirm. A checkpoint is a record that you did something, and un-ticking it would
 * be editing that record rather than correcting it — the state to be in if you want to redo the
 * exercise is "done it twice", not "never did it".
 */
function CheckpointConfirm({
  slideOrder,
  confirmed,
  onConfirm,
}: {
  slideOrder: number;
  confirmed: boolean;
  onConfirm: (slideOrder: number) => Promise<void> | void;
}) {
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);

  if (confirmed) {
    return (
      <p
        className="mono"
        style={{ margin: "0.5rem 0 0", fontSize: "0.68rem", color: "var(--color-accent)" }}
        data-testid="checkpoint-done"
      >
        ✓ You confirmed you did this
      </p>
    );
  }

  return (
    <div style={{ marginTop: "0.5rem" }}>
      <button
        type="button"
        className="btn btn-ghost"
        disabled={busy}
        data-testid="checkpoint-confirm"
        onClick={async () => {
          setBusy(true);
          setFailed(false);
          try {
            await onConfirm(slideOrder);
          } catch {
            // A failed confirmation must not silently look like a success — the whole value of the
            // control is that the record is true. Say so and let them retry.
            setFailed(true);
          } finally {
            setBusy(false);
          }
        }}
      >
        {busy ? "Saving…" : "I did this"}
      </button>
      {failed ? (
        <p role="alert" style={{ margin: "0.35rem 0 0", fontSize: "0.75rem" }}>
          That did not save. Try again.
        </p>
      ) : null}
    </div>
  );
}
