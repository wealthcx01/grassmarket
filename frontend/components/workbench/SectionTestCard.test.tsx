/**
 * The section test (GRS-0226), test-plan item 4.
 *
 * Two properties are worth more than the rest and are asserted directly: the verdict shown is the
 * server's, never the component's own arithmetic; and the explanation appears after answering
 * whether the advisor was right or wrong, because this gate exists to teach rather than to filter.
 */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { SectionTestCard } from "@/components/workbench/SectionTestCard";
import { api } from "@/lib/api";
import type { SectionTest } from "@/lib/types";

vi.mock("@/lib/api", async (importActual) => {
  const actual = await importActual<typeof import("@/lib/api")>();
  return { ...actual, api: { ...actual.api, attemptSectionTest: vi.fn() } };
});

const mocked = api as unknown as { attemptSectionTest: ReturnType<typeof vi.fn> };

const TEST: SectionTest = {
  pass_mark: 0.8,
  questions: [
    {
      prompt: "What decides a workspace's shape?",
      options: ["The data vendor", "The job it is for"],
      answer_index: 1,
      explanation: "The job decides the layout; the vendor only decides what fills it.",
    },
    {
      prompt: "Where does the OpenBB package run?",
      options: ["On your machine", "In their browser"],
      answer_index: 0,
      explanation: "The package is local; Workspace is the browser half of the pair.",
    },
  ],
};

function attempt(over: Record<string, unknown> = {}) {
  return {
    id: "a1",
    owner_consultant_id: "u1",
    course_id: "c1",
    module_id: "m1",
    score: 1,
    passed: true,
    attempted_at: "2026-07-30T09:00:00Z",
    ...over,
  };
}

function renderCard(over: Record<string, unknown> = {}) {
  const onPassed = vi.fn();
  render(
    <SectionTestCard
      slug="product-openbb"
      moduleId="m1"
      test={TEST}
      sectionTitle="Section 1"
      passed={false}
      bestScore={null}
      attempts={0}
      onPassed={onPassed}
      {...over}
    />,
  );
  return { onPassed };
}

/** Answer every question with the option at `pick(questionIndex)`. */
function answerAll(pick: (qi: number) => number) {
  TEST.questions.forEach((q, qi) => {
    const group = screen.getByRole("radiogroup", { name: q.prompt });
    const radios = group.querySelectorAll("input[type=radio]");
    fireEvent.click(radios[pick(qi)]!);
  });
}

beforeEach(() => {
  vi.clearAllMocks();
  mocked.attemptSectionTest.mockResolvedValue(attempt());
});

describe("SectionTestCard (GRS-0226)", () => {
  it("will not submit until every question is answered", () => {
    renderCard();
    const submit = screen.getByRole("button", { name: "Submit answers" });
    expect(submit).toHaveProperty("disabled", true);

    answerAll(() => 0);
    expect(screen.getByRole("button", { name: "Submit answers" })).toHaveProperty("disabled", false);
  });

  it("sends the chosen answers and reports the server's verdict, not its own", async () => {
    const { onPassed } = renderCard();
    answerAll((qi) => TEST.questions[qi]!.answer_index);
    fireEvent.click(screen.getByRole("button", { name: "Submit answers" }));

    await waitFor(() => expect(mocked.attemptSectionTest).toHaveBeenCalledWith("product-openbb", "m1", [1, 0]));
    expect(await screen.findByText(/Passed — 100%/)).toBeTruthy();
    expect(onPassed).toHaveBeenCalled();
  });

  it("believes the server over the answer key it was handed", async () => {
    // Every answer is right by the published tree, but the server says no. The component must
    // show the server's verdict: marking is server-side, and the client never asserts its own pass.
    mocked.attemptSectionTest.mockResolvedValue(attempt({ passed: false, score: 0.5 }));
    const { onPassed } = renderCard();
    answerAll((qi) => TEST.questions[qi]!.answer_index);
    fireEvent.click(screen.getByRole("button", { name: "Submit answers" }));

    expect(await screen.findByText(/Not passed — 50%/)).toBeTruthy();
    expect(onPassed).not.toHaveBeenCalled();
  });

  it("explains every question after answering, right and wrong alike", async () => {
    mocked.attemptSectionTest.mockResolvedValue(attempt({ passed: false, score: 0.5 }));
    renderCard();
    // First right, second wrong — both explanations must appear.
    answerAll((qi) => (qi === 0 ? TEST.questions[0]!.answer_index : 1));
    fireEvent.click(screen.getByRole("button", { name: "Submit answers" }));

    expect(await screen.findByText(/The job decides the layout/)).toBeTruthy();
    expect(screen.getByText(/The package is local/)).toBeTruthy();
    expect(screen.getByText("Correct.")).toBeTruthy();
    expect(screen.getByText("Not quite.")).toBeTruthy();
  });

  it("hides the explanations until the advisor has answered", () => {
    renderCard();
    expect(screen.queryByText(/The job decides the layout/)).toBeNull();
  });

  it("offers a retake after a failure and clears the previous answers", async () => {
    mocked.attemptSectionTest.mockResolvedValue(attempt({ passed: false, score: 0 }));
    renderCard();
    answerAll(() => 0);
    fireEvent.click(screen.getByRole("button", { name: "Submit answers" }));

    const retake = await screen.findByRole("button", { name: "Try again" });
    fireEvent.click(retake);

    expect(screen.queryByText(/The job decides the layout/)).toBeNull();
    expect(screen.getByRole("button", { name: "Submit answers" })).toHaveProperty("disabled", true);
  });

  it("says a section is already passed and does not pretend it is unattempted", () => {
    renderCard({ passed: true, attempts: 2, bestScore: 1 });
    expect(screen.getByText(/Passed — the next section is open/)).toBeTruthy();
    expect(screen.getByText(/2 attempts/)).toBeTruthy();
    expect(screen.getByText(/best 100%/)).toBeTruthy();
  });

  it("surfaces a submit failure instead of leaving the advisor at a dead button", async () => {
    mocked.attemptSectionTest.mockRejectedValue(new Error("network"));
    renderCard();
    answerAll(() => 0);
    fireEvent.click(screen.getByRole("button", { name: "Submit answers" }));

    expect(await screen.findByRole("alert")).toBeTruthy();
  });
});
