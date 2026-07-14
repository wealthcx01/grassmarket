import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { CalibrationPanel } from "@/components/workbench/CalibrationPanel";
import { api } from "@/lib/api";
import type { CalibrationResult, CalibrationSession } from "@/lib/types";

vi.mock("@/lib/api", async (importActual) => {
  const actual = await importActual<typeof import("@/lib/api")>();
  return {
    ...actual,
    api: {
      ...actual.api,
      calibrationSessions: vi.fn(),
      myCalibrationRating: vi.fn(),
      calibrationResult: vi.fn(),
      submitCalibrationRating: vi.fn(),
    },
  };
});

const mocked = api as unknown as {
  calibrationSessions: ReturnType<typeof vi.fn>;
  myCalibrationRating: ReturnType<typeof vi.fn>;
  calibrationResult: ReturnType<typeof vi.fn>;
  submitCalibrationRating: ReturnType<typeof vi.fn>;
};

function session(over: Partial<CalibrationSession> = {}): CalibrationSession {
  return {
    id: "s1",
    owner_consultant_id: "c1",
    title: "Round 1",
    status: "open",
    vignettes: [
      {
        title: "Vignette A",
        excerpt: "A short case excerpt.",
        anchors: [{ subcomponent_key: "OEMS::latency", reference_level: "Advanced" }],
      },
    ],
    opened_at: "2026-07-13T12:00:00+00:00",
    closed_at: null,
    ...over,
  };
}

function result(): CalibrationResult {
  return {
    session_id: "s1",
    computed_at: "2026-07-14T12:00:00+00:00",
    n_raters: 2,
    anchors: [
      { subcomponent_key: "OEMS::latency", n_raters: 2, n_vignettes: 1, kappa_w: 0.81, ac1: 0.83, flagged: false },
    ],
  };
}

describe("CalibrationPanel — blind entry (GRS-0022/0027)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocked.myCalibrationRating.mockRejectedValue(new Error("no rating yet"));
  });

  it("shows blind rating entry and NEVER the result while the session is OPEN", async () => {
    mocked.calibrationSessions.mockResolvedValue([session({ status: "open" })]);
    render(<CalibrationPanel />);

    fireEvent.click(await screen.findByRole("button", { name: /Round 1/ }));

    // The blind rating control is available…
    expect(await screen.findByLabelText(/Rate OEMS::latency in Vignette A/)).toBeTruthy();
    // …the blindness is stated…
    expect(screen.getByText(/stay hidden until the facilitator closes/i)).toBeTruthy();
    // …and the agreement result is NEVER fetched or shown for an open session.
    expect(mocked.calibrationResult).not.toHaveBeenCalled();
    expect(screen.queryByText(/κ_w/)).toBeNull();
  });

  it("reveals the agreement result once the session is CLOSED", async () => {
    mocked.calibrationSessions.mockResolvedValue([session({ status: "closed", closed_at: "2026-07-14T12:00:00+00:00" })]);
    mocked.calibrationResult.mockResolvedValue(result());
    render(<CalibrationPanel />);

    fireEvent.click(await screen.findByRole("button", { name: /Round 1/ }));

    // The result table appears, and no blind rating entry is offered.
    expect(await screen.findByText(/κ_w/)).toBeTruthy();
    expect(screen.getByText("0.81")).toBeTruthy();
    await waitFor(() => expect(mocked.calibrationResult).toHaveBeenCalledWith("s1", expect.anything()));
    expect(screen.queryByLabelText(/Rate OEMS::latency/)).toBeNull();
  });
});
