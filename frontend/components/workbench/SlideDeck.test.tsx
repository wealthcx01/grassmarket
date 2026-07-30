/**
 * The slide reader (GRS-0226), test-plan item 4.
 *
 * The reason this file exists is that GRS-0216 wrote 196 slides and GRS-0225 drew nine diagrams
 * that no advisor could see, because nothing rendered `slides`. So the assertions here are
 * deliberately about what reaches the DOM, not about props being passed along.
 */

import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SlideDeck } from "@/components/workbench/SlideDeck";
import type { LessonAsset, Slide } from "@/lib/types";

function slide(over: Partial<Slide> = {}): Slide {
  return {
    order: 0,
    kind: "concept",
    title: "What a widget is",
    body: "A widget is the unit Workspace lays out, and the unit a job is assembled from.",
    asset: null,
    checkpoint_prompt: null,
    references: [],
    ...over,
  } as Slide;
}

/** A minimal valid diagram: one rect the sanitiser accepts. */
function asset(over: Partial<LessonAsset> = {}): LessonAsset {
  return {
    svg: '<svg viewBox="0 0 10 10"><rect x="1" y="1" width="8" height="8" /></svg>',
    alt: "A square standing for one widget on the Workspace canvas.",
    caption: "One widget.",
    ...over,
  } as LessonAsset;
}

describe("SlideDeck (GRS-0226)", () => {
  it("renders nothing at all for a lesson with no slides", () => {
    const { container } = render(<SlideDeck slides={[]} label="Legacy lesson" />);
    expect(container.firstChild).toBeNull();
  });

  it("shows one slide at a time, in order, and moves between them", () => {
    render(
      <SlideDeck
        label="Widgets"
        slides={[
          slide({ order: 1, title: "Second idea" }),
          slide({ order: 0, title: "First idea" }),
        ]}
      />,
    );

    // Authored order wins over array order — a deck is not a list that happens to be sorted.
    expect(screen.getByText("First idea")).toBeTruthy();
    expect(screen.queryByText("Second idea")).toBeNull();
    expect(screen.getByText("Slide 1 of 2")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: /Next/ }));
    expect(screen.getByText("Second idea")).toBeTruthy();
    expect(screen.queryByText("First idea")).toBeNull();
    expect(screen.getByText("Slide 2 of 2")).toBeTruthy();
  });

  it("does not let the advisor step off either end of the deck", () => {
    render(<SlideDeck label="Widgets" slides={[slide(), slide({ order: 1, title: "Last" })]} />);

    expect(screen.getByRole("button", { name: /Previous/ })).toHaveProperty("disabled", true);
    fireEvent.click(screen.getByRole("button", { name: /Next/ }));
    expect(screen.getByRole("button", { name: /Next/ })).toHaveProperty("disabled", true);
  });

  it("names the slide's kind, so a checkpoint does not read as more prose", () => {
    render(
      <SlideDeck
        label="Widgets"
        slides={[slide({ kind: "checkpoint", checkpoint_prompt: "Add a chart widget now." })]}
      />,
    );

    expect(screen.getByText("CHECKPOINT")).toBeTruthy();
    expect(screen.getByText(/Add a chart widget now/)).toBeTruthy();
  });

  it("draws a diagram that sanitises, with its alt text on the image", () => {
    render(<SlideDeck label="Widgets" slides={[slide({ asset: asset() })]} />);

    const drawing = screen.getByRole("img", {
      name: "A square standing for one widget on the Workspace canvas.",
    });
    expect(drawing.tagName.toLowerCase()).toBe("svg");
    expect(screen.getByText("One widget.")).toBeTruthy();
  });

  it("announces a diagram that fails sanitisation rather than dropping it", () => {
    // A <script> is exactly what the sanitiser exists to refuse. The advisor must be told the
    // slide is missing a drawing — a silently blank slide reads as a slide with nothing on it.
    const hostile = asset({ svg: '<svg viewBox="0 0 10 10"><script>alert(1)</script></svg>' });
    render(<SlideDeck label="Widgets" slides={[slide({ asset: hostile })]} />);

    expect(screen.getByText(/failed sanitisation/)).toBeTruthy();
    expect(screen.queryByRole("img")).toBeNull();
    expect(document.querySelector("script")).toBeNull();
  });
});
