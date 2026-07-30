/**
 * Academy reader (GRS-0135): renders a published course's lessons, renders inline **bold** without
 * leaking literal asterisks, and marks a lesson complete through the API.
 */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import AcademyReaderPage from "@/app/workbench/academy/[slug]/page";
import { api } from "@/lib/api";
import type { CourseVersion } from "@/lib/types";

// A STABLE router object — a fresh one each render would change the load() callback identity and
// re-fire the load effect, matching nothing real (next/navigation's useRouter is stable).
const router = { replace: vi.fn(), push: vi.fn() };
vi.mock("next/navigation", () => ({
  useRouter: () => router,
  useParams: () => ({ slug: "sales-egoist" }),
}));

vi.mock("@/lib/api", async (importActual) => {
  const actual = await importActual<typeof import("@/lib/api")>();
  return {
    ...actual,
    getToken: vi.fn(() => "test-token"),
    api: {
      ...actual.api,
      getPublishedCourse: vi.fn(),
      listLessonCompletions: vi.fn(),
      completeLesson: vi.fn(),
      sectionProgress: vi.fn(),
    },
  };
});

const mocked = api as unknown as {
  getPublishedCourse: ReturnType<typeof vi.fn>;
  listLessonCompletions: ReturnType<typeof vi.fn>;
  completeLesson: ReturnType<typeof vi.fn>;
  sectionProgress: ReturnType<typeof vi.fn>;
};

function course(): CourseVersion {
  return {
    course_id: "c1",
    slug: "sales-egoist",
    version: 1,
    published_by_consultant_id: "admin",
    published_at: "2026-07-18T00:00:00Z",
    tree: {
      title: "Sales Egoist",
      summary: "The doctrine.",
      certification_credit: "coursework",
      mandatory_first: true,
      modules: [
        {
          id: "m1",
          title: "The core doctrine",
          order: 0,
          lessons: [
            {
              id: "l1",
              title: "The Zero-Sum Pipeline",
              body: "The pipeline is zero-sum, so for a **retail brokerage** it is booking the workshop.",
              order: 0,
              author: "human",
              video_ref: null,
              drill_topics: ["sales:zero-sum-pipeline"],
              measurement: "Every live account has a dated next step.",
              approved: true,
              approved_by_consultant_id: null,
              approved_at: null,
            },
          ],
        },
      ],
    },
  } as unknown as CourseVersion;
}

beforeEach(() => {
  vi.clearAllMocks();
  mocked.getPublishedCourse.mockResolvedValue(course());
  mocked.listLessonCompletions.mockResolvedValue([]);
  mocked.completeLesson.mockResolvedValue({ lesson_id: "l1" });
  // Sales Egoist is a legacy course: no slides, no section test, so nothing gates and the reader
  // must behave exactly as it did before GRS-0226. That is what these cases still assert.
  mocked.sectionProgress.mockResolvedValue([]);
});

describe("Academy reader (GRS-0135)", () => {
  it("renders the course, its lessons, and inline **bold** without literal asterisks", async () => {
    render(<AcademyReaderPage />);
    expect(await screen.findByRole("heading", { name: "Sales Egoist" })).toBeTruthy();
    expect(screen.getByText("The Zero-Sum Pipeline")).toBeTruthy();
    // The body's **retail brokerage** renders as a <strong>, and no literal "**" leaks into the DOM.
    expect(screen.getByText("retail brokerage").tagName).toBe("STRONG");
    expect(document.body.textContent).not.toContain("**");
  });

  it("gates completion behind active recall, then completes through the API (GRS-0139)", async () => {
    render(<AcademyReaderPage />);
    // You cannot complete without first attempting recall — there is no bare "Mark complete".
    const reveal = await screen.findByRole("button", { name: "Reveal model answer" });
    expect((reveal as HTMLButtonElement).disabled).toBe(true);
    // Attempt recall → reveal the model answer → then complete.
    fireEvent.change(screen.getByLabelText(/Recall answer for/), {
      target: { value: "the pipeline is zero-sum" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Reveal model answer" }));
    fireEvent.click(await screen.findByRole("button", { name: "Mark complete →" }));
    await waitFor(() => expect(mocked.completeLesson).toHaveBeenCalledWith("sales-egoist", "l1"));
    expect(await screen.findByRole("button", { name: "Completed" })).toBeTruthy();
  });
});

/**
 * The gated course (GRS-0226). GRS-0216 wrote slides and a section test per section; until this
 * ticket the reader showed neither, so these cases are about what an advisor can actually see and
 * what the gate actually withholds.
 */
function gatedCourse(): CourseVersion {
  const question = (prompt: string) => ({
    prompt,
    options: ["Wrong", "Right"],
    answer_index: 1,
    explanation: `Because ${prompt}`,
  });
  const section = (id: string, title: string, order: number, lessonTitle: string) => ({
    id,
    title,
    order,
    section_test: { pass_mark: 0.8, questions: [question(`${id} q1`)] },
    lessons: [
      {
        id: `${id}-l1`,
        title: lessonTitle,
        body: "What this lesson is for.",
        order: 0,
        author: "human",
        video_ref: null,
        references: [],
        assets: [],
        slides: [
          {
            order: 0,
            kind: "concept",
            title: `${title} — the first idea`,
            body: "The teaching lives on the slides now, not in the opening paragraph.",
            asset: null,
            references: [],
            checkpoint_prompt: null,
          },
        ],
        drill_topics: [],
        measurement: null,
        approved: true,
        approved_by_consultant_id: null,
        approved_at: null,
      },
    ],
  });
  return {
    course_id: "c2",
    slug: "sales-egoist",
    version: 2,
    published_by_consultant_id: "admin",
    published_at: "2026-07-30T00:00:00Z",
    tree: {
      title: "OpenBB",
      summary: "The rebuilt course.",
      certification_credit: "coursework",
      mandatory_first: true,
      modules: [
        section("m1", "Section one", 0, "Why OpenBB"),
        section("m2", "Section two", 1, "The two products"),
      ],
    },
  } as unknown as CourseVersion;
}

const standing = (moduleId: string, order: number, unlocked: boolean, passed: boolean) => ({
  module_id: moduleId,
  order,
  has_test: true,
  unlocked,
  passed,
  best_score: passed ? 1 : null,
  attempts: passed ? 1 : 0,
});

describe("Academy reader — the gate (GRS-0226)", () => {
  beforeEach(() => {
    mocked.getPublishedCourse.mockResolvedValue(gatedCourse());
    mocked.sectionProgress.mockResolvedValue([
      standing("m1", 0, true, false),
      standing("m2", 1, false, false),
    ]);
  });

  it("shows the slides of an unlocked section", async () => {
    render(<AcademyReaderPage />);
    expect(await screen.findByRole("heading", { name: "OpenBB" })).toBeTruthy();
    expect(screen.getByText("Section one — the first idea")).toBeTruthy();
    expect(screen.getByText("Slide 1 of 1")).toBeTruthy();
  });

  it("withholds a locked section's lessons and says why", async () => {
    render(<AcademyReaderPage />);
    expect(await screen.findByText(/Locked\. Pass the test/)).toBeTruthy();
    // The section's title still shows — an advisor should see what is ahead of them — but its
    // lesson and its slides do not.
    expect(screen.getByText("Section two")).toBeTruthy();
    expect(screen.queryByText("The two products")).toBeNull();
    expect(screen.queryByText("Section two — the first idea")).toBeNull();
  });

  it("offers the test on the open section only", async () => {
    render(<AcademyReaderPage />);
    await screen.findByRole("heading", { name: "OpenBB" });
    expect(screen.getByRole("region", { name: "Section one section test" })).toBeTruthy();
    expect(screen.queryByRole("region", { name: "Section two section test" })).toBeNull();
  });

  it("counts progress in sections passed, not lessons scrolled", async () => {
    mocked.sectionProgress.mockResolvedValue([
      standing("m1", 0, true, true),
      standing("m2", 1, true, false),
    ]);
    render(<AcademyReaderPage />);
    expect(await screen.findByText("1 / 2 sections passed")).toBeTruthy();
    // Lessons read stay visible underneath — they still say where you are — but they are not
    // the headline, because reading is not the same as having learned it.
    expect(screen.getByText(/0 of 2 lessons read/)).toBeTruthy();
  });

  it("claims completion only when every section is passed", async () => {
    mocked.sectionProgress.mockResolvedValue([
      standing("m1", 0, true, true),
      standing("m2", 1, true, true),
    ]);
    render(<AcademyReaderPage />);
    expect(await screen.findByText(/passed every section of this course/)).toBeTruthy();
  });
});
