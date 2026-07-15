/**
 * GRS-0039 follow-up: LinkAssessmentControl must not collapse loading / empty / error into a silent
 * no-op. A failed list-load shows an error + Retry (not an invisible control that reads as "nothing
 * to link"); a genuine empty renders nothing; finalised candidates render the picker.
 */

import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { LinkAssessmentControl } from "@/components/LinkAssessmentControl";
import { ApiError, api } from "@/lib/api";
import type { Assessment, Engagement } from "@/lib/types";

vi.mock("@/lib/api", async (importActual) => {
  const actual = await importActual<typeof import("@/lib/api")>();
  return { ...actual, api: { ...actual.api, listAssessments: vi.fn(), linkAssessment: vi.fn() } };
});

const mocked = api as unknown as { listAssessments: ReturnType<typeof vi.fn> };

const engagement = { id: "e1", assessment_ids: [] } as unknown as Engagement;
function finalised(id: string, subject: string): Assessment {
  return { id, subject, state: "finalised" } as unknown as Assessment;
}

describe("LinkAssessmentControl (error/empty/loaded)", () => {
  beforeEach(() => vi.clearAllMocks());

  it("shows an error + Retry when the list load fails (not a silent no-op)", async () => {
    mocked.listAssessments.mockRejectedValue(new ApiError(500, "boom", null));
    render(<LinkAssessmentControl engagement={engagement} onLinked={vi.fn()} />);
    expect(await screen.findByRole("button", { name: /retry/i })).toBeTruthy();
    expect(screen.getByRole("alert")).toBeTruthy();
  });

  it("renders nothing when there are genuinely no finalised candidates", async () => {
    mocked.listAssessments.mockResolvedValue([]);
    const { container } = render(
      <LinkAssessmentControl engagement={engagement} onLinked={vi.fn()} />,
    );
    await waitFor(() => expect(mocked.listAssessments).toHaveBeenCalled());
    expect(container.querySelector("select")).toBeNull();
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("renders the picker when a finalised assessment is available", async () => {
    mocked.listAssessments.mockResolvedValue([finalised("a1", "Meridian")]);
    render(<LinkAssessmentControl engagement={engagement} onLinked={vi.fn()} />);
    expect(await screen.findByRole("button", { name: /^link$/i })).toBeTruthy();
    expect(screen.getByText("Meridian")).toBeTruthy();
  });
});
