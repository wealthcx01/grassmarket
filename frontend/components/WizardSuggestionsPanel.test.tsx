/**
 * AI-assisted wizard input panel (GRS-0101, ADR-0032): renders proposals, Accept fires only for a
 * prefill, Dismiss hides any, and nothing renders when there's nothing to suggest.
 */

import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { WizardSuggestionsPanel } from "@/components/WizardSuggestionsPanel";
import type { WizardSuggestion } from "@/lib/types";

const prefill: WizardSuggestion = {
  id: "prefill:APP_SERVER:X",
  kind: "prefill",
  step: "infrastructure",
  title: "Start X at Advanced?",
  rationale: "Others in App Server are mostly Advanced.",
  module_key: "APP_SERVER",
  subcomponent_key: "X",
  proposed_level: "Advanced",
};

const guidance: WizardSuggestion = {
  id: "coverage:scoreable",
  kind: "guidance",
  step: "summary",
  title: "A few inputs stand between you and a live score",
  rationale: "Rate all 7 Strategic Powers.",
};

describe("WizardSuggestionsPanel (GRS-0101)", () => {
  it("renders nothing when there are no suggestions", () => {
    const { container } = render(
      <WizardSuggestionsPanel suggestions={[]} version="heuristic-v1" onAccept={vi.fn()} onDismiss={vi.fn()} />,
    );
    expect(container.firstChild).toBeNull();
  });

  it("accepts a prefill and is honestly labelled (not 'AI'), gated on an explicit action", () => {
    const onAccept = vi.fn();
    const onDismiss = vi.fn();
    render(
      <WizardSuggestionsPanel suggestions={[prefill]} version="heuristic-v1" onAccept={onAccept} onDismiss={onDismiss} />,
    );
    // Honest labelling (GRS-0136): "Suggestions", not "AI".
    expect(screen.getByRole("heading", { name: "Suggestions" })).toBeTruthy();
    expect(document.body.textContent).not.toMatch(/\bAI\b/);
    // The gate is visible: nothing is applied unless the advisor acts.
    expect(screen.getByText(/never applied unless you act/i)).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Accept" }));
    expect(onAccept).toHaveBeenCalledWith(prefill);
    expect(onDismiss).not.toHaveBeenCalled();
  });

  it("a guidance item has no Accept — only a dismiss", () => {
    const onAccept = vi.fn();
    const onDismiss = vi.fn();
    render(
      <WizardSuggestionsPanel suggestions={[guidance]} version="heuristic-v1" onAccept={onAccept} onDismiss={onDismiss} />,
    );
    expect(screen.queryByRole("button", { name: "Accept" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Got it" }));
    expect(onDismiss).toHaveBeenCalledWith("coverage:scoreable");
    expect(onAccept).not.toHaveBeenCalled();
  });
});
