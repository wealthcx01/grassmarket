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
    },
  };
});

const mocked = api as unknown as {
  getPublishedCourse: ReturnType<typeof vi.fn>;
  listLessonCompletions: ReturnType<typeof vi.fn>;
  completeLesson: ReturnType<typeof vi.fn>;
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

  it("marks a lesson complete through the API and reflects it", async () => {
    render(<AcademyReaderPage />);
    const button = await screen.findByRole("button", { name: "Mark complete" });
    fireEvent.click(button);
    await waitFor(() => expect(mocked.completeLesson).toHaveBeenCalledWith("sales-egoist", "l1"));
    // The button flips to a disabled "Completed" once the completion is recorded.
    expect(await screen.findByRole("button", { name: "Completed" })).toBeTruthy();
  });
});
