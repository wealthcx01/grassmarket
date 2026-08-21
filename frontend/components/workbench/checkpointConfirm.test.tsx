import { render, screen, waitFor } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { describe, expect, it, vi } from "vitest";

import { SlideView } from "@/components/workbench/SlideDeck";
import type { Slide } from "@/lib/types";

/**
 * GRS-0239 scope 3.
 *
 * The callout said "Do this now:" and offered nothing to do it with — no control, no state, no
 * record — while the content contract promised "the advisor produces something and confirms they
 * did". An instruction with no way to acknowledge it teaches an advisor that the instruction is
 * decorative, which is the same complaint the whole ticket is about.
 */

const checkpoint = (over: Partial<Slide> = {}): Slide =>
  ({
    order: 3,
    kind: "checkpoint",
    title: "Rate a module",
    body: "Body.",
    checkpoint_prompt: "Open the wizard and rate one module.",
    references: [],
    ...over,
  }) as Slide;

const concept = (): Slide =>
  ({ order: 0, kind: "concept", title: "Idea", body: "Body.", references: [] }) as Slide;

describe("the checkpoint confirm control", () => {
  it("offers a control on a checkpoint slide", () => {
    render(<SlideView slide={checkpoint()} onConfirm={vi.fn()} />);
    expect(screen.getByTestId("checkpoint-confirm")).toBeTruthy();
  });

  it("passes the slide's own order, not its index", async () => {
    // The confirmation is keyed on slide POSITION server-side. Sending an index would silently
    // record the wrong checkpoint for every deck that does not start at zero.
    const onConfirm = vi.fn().mockResolvedValue(undefined);
    render(<SlideView slide={checkpoint({ order: 7 })} onConfirm={onConfirm} />);
    fireEvent.click(screen.getByTestId("checkpoint-confirm"));
    await waitFor(() => expect(onConfirm).toHaveBeenCalledWith(7));
  });

  it("shows the confirmed state instead of the button once done", () => {
    render(<SlideView slide={checkpoint()} onConfirm={vi.fn()} confirmed />);
    expect(screen.getByTestId("checkpoint-done")).toBeTruthy();
    expect(screen.queryByTestId("checkpoint-confirm")).toBeNull();
  });

  it("does not offer an un-confirm", () => {
    // A checkpoint records that you DID something. Un-ticking it would be editing the record
    // rather than correcting it — the state to be in if you redo the exercise is "done it twice".
    render(<SlideView slide={checkpoint()} onConfirm={vi.fn()} confirmed />);
    expect(screen.queryByRole("button")).toBeNull();
  });

  it("says so when saving fails, rather than looking like it worked", async () => {
    // The entire value of the control is that the tick corresponds to a record. A silent failure
    // would leave an advisor believing they had confirmed something they had not.
    const onConfirm = vi.fn().mockRejectedValue(new Error("network"));
    render(<SlideView slide={checkpoint()} onConfirm={onConfirm} />);
    fireEvent.click(screen.getByTestId("checkpoint-confirm"));
    expect(await screen.findByRole("alert")).toBeTruthy();
    // And the button comes back, so they can retry.
    expect(screen.getByTestId("checkpoint-confirm")).toBeTruthy();
  });

  it("renders no control at all on a non-checkpoint slide", () => {
    render(<SlideView slide={concept()} onConfirm={vi.fn()} />);
    expect(screen.queryByTestId("checkpoint-confirm")).toBeNull();
  });

  it("renders the prompt without a control when there is nothing to confirm against", () => {
    // A preview with no lesson behind it still shows the instruction; it just cannot record it.
    render(<SlideView slide={checkpoint()} />);
    expect(screen.getByText(/Open the wizard/)).toBeTruthy();
    expect(screen.queryByTestId("checkpoint-confirm")).toBeNull();
  });
});
