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

export function SlideView({ slide }: { slide: Slide }) {
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
        <p
          className="callout"
          style={{
            marginTop: "0.8rem",
            borderLeft: "2px solid var(--color-accent)",
            paddingLeft: "0.6rem",
            fontSize: "0.85rem",
          }}
        >
          <strong>Do this now: </strong>
          {slide.checkpoint_prompt}
        </p>
      ) : null}
      <LessonReferences references={slide.references} />
    </div>
  );
}

export function SlideDeck({ slides, label }: { slides: readonly Slide[]; label: string }) {
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
      <SlideView slide={current} />

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
