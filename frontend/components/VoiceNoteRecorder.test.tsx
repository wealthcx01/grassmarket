/**
 * The recorder's rules (GRS-0249, GRS-0255).
 *
 * These are the behaviours that make the consent gate real rather than decorative, plus the two
 * failure modes that cost an advisor their note. The server enforces all of it as well — that is
 * the point — but a UI that only *looks* like it asks for consent is the thing worth pinning down
 * here, because that is what the client actually sees.
 */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { VoiceNoteRecorder } from "@/components/VoiceNoteRecorder";
import { api } from "@/lib/api";
import * as recording from "@/lib/recording";

const WORDING =
  "I'd like to record this session so I can write it up accurately. The recording stays in the " +
  "Bruntsfield advisor system, is transcribed for my notes, and isn't shared outside the " +
  "engagement team. Are you happy for me to record?";

function fakeRecorder() {
  return {
    stop: vi.fn().mockResolvedValue({ blob: new Blob(["hi"]), mimeType: "audio/webm", seconds: 12 }),
    cancel: vi.fn(),
  };
}

beforeEach(() => {
  vi.restoreAllMocks();
  vi.spyOn(recording, "listPendingRecordings").mockResolvedValue([]);
  vi.spyOn(recording, "holdRecording").mockResolvedValue(undefined);
  vi.spyOn(recording, "releaseRecording").mockResolvedValue(undefined);
  vi.spyOn(recording, "recordFailedAttempt").mockResolvedValue(undefined);
  vi.spyOn(recording, "toBase64").mockResolvedValue("YmFzZTY0");
  vi.spyOn(api, "consentLine").mockResolvedValue({ wording: WORDING });
});

function open() {
  render(<VoiceNoteRecorder prospectId="p1" prospectName="Kilmarnock Foods" />);
  fireEvent.click(screen.getByRole("button", { name: "Record a voice note" }));
}

describe("the consent gate", () => {
  it("shows the wording the API serves, not a copy of its own", async () => {
    open();
    fireEvent.click(screen.getByRole("button", { name: "Someone else is here" }));
    await screen.findByText(WORDING);
    expect(api.consentLine).toHaveBeenCalled();
  });

  it("will not record a session at all if the wording cannot be loaded", async () => {
    vi.spyOn(api, "consentLine").mockRejectedValue(new Error("offline"));
    const start = vi.spyOn(recording, "startRecording");
    open();
    fireEvent.click(screen.getByRole("button", { name: "Someone else is here" }));

    await screen.findByText(/Recording without showing the agreed wording/);
    // The point: no fallback to a hardcoded line, and no recording anyway.
    expect(start).not.toHaveBeenCalled();
  });

  it("records nothing when the client does not agree", async () => {
    const start = vi.spyOn(recording, "startRecording");
    open();
    fireEvent.click(screen.getByRole("button", { name: "Someone else is here" }));
    await screen.findByText(WORDING);
    fireEvent.click(screen.getByRole("button", { name: "They did not agree" }));

    expect(start).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: "Record a voice note" })).toBeTruthy();
  });

  it("sends the consent and the wording once they agree", async () => {
    vi.spyOn(recording, "startRecording").mockResolvedValue(fakeRecorder());
    const upload = vi
      .spyOn(api, "uploadRecording")
      .mockResolvedValue({ text: "moving to proposal", consent_confirmed_at: "now" } as never);
    open();
    fireEvent.click(screen.getByRole("button", { name: "Someone else is here" }));
    await screen.findByText(WORDING);
    fireEvent.click(screen.getByRole("button", { name: "They agreed — start recording" }));
    await screen.findByRole("button", { name: "Stop and transcribe" });
    fireEvent.click(screen.getByRole("button", { name: "Stop and transcribe" }));

    await waitFor(() => expect(upload).toHaveBeenCalled());
    const sent = upload.mock.calls[0]![0];
    expect(sent.recording_kind).toBe("recorded_session");
    expect(sent.consent_wording).toBe(WORDING);
    expect(sent.consent_confirmed_at).toBeTruthy();
  });
});

describe("a voice note claims no consent", () => {
  it("never asks for consent, and never sends any", async () => {
    vi.spyOn(recording, "startRecording").mockResolvedValue(fakeRecorder());
    const upload = vi.spyOn(api, "uploadRecording").mockResolvedValue({ text: "note" } as never);
    open();
    fireEvent.click(screen.getByRole("button", { name: "Just me" }));
    await screen.findByRole("button", { name: "Stop and transcribe" });
    // No consent step was shown at all — there was nobody to ask.
    expect(screen.queryByText(WORDING)).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Stop and transcribe" }));

    await waitFor(() => expect(upload).toHaveBeenCalled());
    const sent = upload.mock.calls[0]![0];
    expect(sent.recording_kind).toBe("voice_note");
    expect(sent.consent_confirmed_at).toBeNull();
    expect(sent.consent_wording).toBeNull();
  });
});

describe("nothing is lost", () => {
  it("holds the recording before the first upload attempt", async () => {
    vi.spyOn(recording, "startRecording").mockResolvedValue(fakeRecorder());
    vi.spyOn(api, "uploadRecording").mockResolvedValue({ text: "note" } as never);
    open();
    fireEvent.click(screen.getByRole("button", { name: "Just me" }));
    await screen.findByRole("button", { name: "Stop and transcribe" });
    fireEvent.click(screen.getByRole("button", { name: "Stop and transcribe" }));

    await waitFor(() => expect(recording.holdRecording).toHaveBeenCalled());
    // Held first, released only once the server has it.
    expect(recording.releaseRecording).toHaveBeenCalled();
  });

  it("keeps a failed upload on the device and says so", async () => {
    vi.spyOn(recording, "startRecording").mockResolvedValue(fakeRecorder());
    vi.spyOn(api, "uploadRecording").mockRejectedValue(new Error("no signal"));
    open();
    fireEvent.click(screen.getByRole("button", { name: "Just me" }));
    await screen.findByRole("button", { name: "Stop and transcribe" });
    fireEvent.click(screen.getByRole("button", { name: "Stop and transcribe" }));

    await screen.findByText(/saved on this device/);
    expect(recording.recordFailedAttempt).toHaveBeenCalled();
    expect(recording.releaseRecording).not.toHaveBeenCalled();
  });

  it("does not promise a retry when the browser would not hold the recording", async () => {
    vi.spyOn(recording, "holdRecording").mockRejectedValue(new Error("no storage"));
    vi.spyOn(recording, "startRecording").mockResolvedValue(fakeRecorder());
    vi.spyOn(api, "uploadRecording").mockRejectedValue(new Error("no signal"));
    open();
    fireEvent.click(screen.getByRole("button", { name: "Just me" }));
    await screen.findByRole("button", { name: "Stop and transcribe" });
    fireEvent.click(screen.getByRole("button", { name: "Stop and transcribe" }));

    // The recording is only in this tab, and the advisor is told that rather than told to come
    // back to it later — which would be a promise the browser cannot keep.
    await screen.findByText(/only in this tab/);
    expect(screen.queryByText(/saved on this device/)).toBeNull();
    expect(recording.recordFailedAttempt).not.toHaveBeenCalled();
  });

  it("fails loud when the microphone captured nothing", async () => {
    const empty = fakeRecorder();
    empty.stop = vi.fn().mockRejectedValue(new Error("Nothing was recorded."));
    vi.spyOn(recording, "startRecording").mockResolvedValue(empty);
    const upload = vi.spyOn(api, "uploadRecording");
    open();
    fireEvent.click(screen.getByRole("button", { name: "Just me" }));
    await screen.findByRole("button", { name: "Stop and transcribe" });
    fireEvent.click(screen.getByRole("button", { name: "Stop and transcribe" }));

    await screen.findByText("Nothing was recorded.");
    // An empty recording is never uploaded, so it can never become an empty note.
    expect(upload).not.toHaveBeenCalled();
  });
});
