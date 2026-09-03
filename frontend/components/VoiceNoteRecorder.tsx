/**
 * Record a voice note against a prospect (GRS-0249).
 *
 * The advisor is in a car park after a meeting. They press record, talk, press stop, and the note
 * is transcribed and comes back for review. Four things shape everything below.
 *
 * **The advisor says who was in the room, and it is not a formality.** Someone dictating alone has
 * nobody to ask for consent; a session with a client in it has somebody who must be asked. The
 * consent line is founder-approved and is fetched from the API rather than written here, so there
 * is one copy of it in the system (GRS-0255). A recorded session without consent is refused by the
 * server and stores nothing — no consent, no recording kept.
 *
 * **The meter must move.** A silent recording — muted mic, wrong input, a dead device the browser
 * granted anyway — is indistinguishable from a good one until it comes back empty, and by then the
 * meeting is over.
 *
 * **Nothing is thrown away until the server has it.** The recording is written to IndexedDB before
 * the first upload attempt and released only on a 201. A failed upload leaves it on the phone to
 * retry, because the car park has one bar and the conversation cannot be had again.
 *
 * **A voice note proposes; it never acts.** This component's last step is a transcript for review.
 * Nothing here moves a prospect's stage — non-negotiable #8.
 */

"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { ApiError, api } from "@/lib/api";
import {
  NO_MICROPHONE_MESSAGE,
  extensionFor,
  holdRecording,
  listPendingRecordings,
  recordFailedAttempt,
  releaseRecording,
  startRecording,
  toBase64,
  type PendingRecording,
  type RecorderHandle,
} from "@/lib/recording";
import type { MeetingTranscript, RecordingKind } from "@/lib/types";

type Phase = "idle" | "choosing" | "consent" | "recording" | "uploading" | "done" | "failed";

/**
 * Where the audio goes, said plainly. The transcription provider is hosted OpenAI Whisper
 * (GRS-0251), so client speech leaves our infrastructure. That is a recorded trade, and the
 * advisor deciding whether to press record is the person who needs to know it.
 */
const WHERE_THE_AUDIO_GOES =
  "The recording is stored in Grassmarket and sent to OpenAI Whisper to be transcribed.";

export function VoiceNoteRecorder({
  prospectId,
  prospectName,
  onTranscript,
}: {
  prospectId: string;
  prospectName: string;
  onTranscript?: (transcript: MeetingTranscript) => void;
}) {
  const [phase, setPhase] = useState<Phase>("idle");
  const [kind, setKind] = useState<RecordingKind>("voice_note");
  const [consentWording, setConsentWording] = useState<string | null>(null);
  const [consentError, setConsentError] = useState<string | null>(null);
  const [level, setLevel] = useState(0);
  const [elapsed, setElapsed] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [transcript, setTranscript] = useState<MeetingTranscript | null>(null);
  const [pending, setPending] = useState<PendingRecording[]>([]);
  const handle = useRef<RecorderHandle | null>(null);

  const refreshPending = useCallback(() => {
    listPendingRecordings()
      .then((all) => setPending(all.filter((entry) => entry.prospectId === prospectId)))
      // A browser that will not give us IndexedDB still records; it just cannot hold a failed
      // upload for later. The recorder says so at the point it matters rather than here.
      .catch(() => setPending([]));
  }, [prospectId]);

  useEffect(() => {
    refreshPending();
  }, [refreshPending]);

  // The consent line is fetched once, when the advisor says someone else is in the room. Fetching
  // it — rather than holding a copy here — is what makes the wording single-sourced.
  useEffect(() => {
    if (phase !== "consent" || consentWording !== null) return;
    let cancelled = false;
    api
      .consentLine()
      .then((line) => {
        if (!cancelled) setConsentWording(line.wording);
      })
      .catch(() => {
        if (!cancelled) {
          setConsentError(
            "Could not load the consent wording, so this session cannot be recorded yet. " +
              "Recording without showing the agreed wording is not something this will do.",
          );
        }
      });
    return () => {
      cancelled = true;
    };
  }, [phase, consentWording]);

  async function begin(recordingKind: RecordingKind) {
    setKind(recordingKind);
    setError(null);
    setLevel(0);
    setElapsed(0);
    try {
      handle.current = await startRecording({ onLevel: setLevel, onElapsed: setElapsed });
      setPhase("recording");
    } catch (err: unknown) {
      handle.current = null;
      setError(err instanceof Error ? err.message : NO_MICROPHONE_MESSAGE);
      setPhase("failed");
    }
  }

  async function stopAndUpload(confirmedAt: string | null) {
    const active = handle.current;
    if (!active) return;
    handle.current = null;
    setPhase("uploading");
    let recorded: { blob: Blob; mimeType: string; seconds: number };
    try {
      recorded = await active.stop();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Nothing was recorded.");
      setPhase("failed");
      return;
    }

    const entry: PendingRecording = {
      id: crypto.randomUUID(),
      blob: recorded.blob,
      mimeType: recorded.mimeType,
      seconds: recorded.seconds,
      recordedAt: new Date().toISOString(),
      prospectId,
      recordingKind: kind,
      consentConfirmedAt: kind === "recorded_session" ? confirmedAt : null,
      consentWording: kind === "recorded_session" ? consentWording : null,
      attempts: 0,
    };
    // Held before the first attempt, so a failure mid-upload leaves the recording on the device
    // rather than only in this component's memory. A browser that refuses IndexedDB (private mode,
    // storage disabled) still records — but then the recording lives only in this tab, and the
    // advisor has to be told that rather than promised a retry that cannot happen.
    const held = await holdRecording(entry)
      .then(() => true)
      .catch(() => false);
    await upload(entry, held);
  }

  const upload = useCallback(
    async (entry: PendingRecording, held = true) => {
      setPhase("uploading");
      setError(null);
      try {
        const created = await api.uploadRecording({
          media_base64: await toBase64(entry.blob),
          // The colons in an ISO timestamp are illegal in a Windows filename, and this becomes the
          // name of a file an advisor can download later. Stamped, not random, so the recordings
          // on a prospect sort into the order they were made.
          source_filename: `voice-note-${entry.recordedAt.replace(/[:.]/g, "-")}.${extensionFor(
            entry.mimeType,
          )}`,
          content_type: entry.mimeType,
          source_kind: "audio",
          prospect_id: entry.prospectId,
          recording_kind: entry.recordingKind,
          consent_confirmed_at: entry.consentConfirmedAt,
          consent_wording: entry.consentWording,
          keep_recording: true,
        });
        await releaseRecording(entry.id).catch(() => undefined);
        setTranscript(created);
        setPhase("done");
        onTranscript?.(created);
      } catch (err: unknown) {
        if (held) await recordFailedAttempt(entry).catch(() => undefined);
        const reason =
          err instanceof ApiError ? err.message : "The recording could not be sent.";
        setError(
          held
            ? `${reason} It is saved on this device — send it again from the list above.`
            : `${reason} This browser will not let us hold it, so it is only in this tab: do not ` +
              `close the page, and try again now.`,
        );
        setPhase("failed");
      } finally {
        refreshPending();
      }
    },
    [onTranscript, refreshPending],
  );

  function discard() {
    handle.current?.cancel();
    handle.current = null;
    setPhase("idle");
    setLevel(0);
    setElapsed(0);
  }

  return (
    <section style={panel}>
      <header style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", gap: "0.5rem", flexWrap: "wrap" }}>
        <h2 style={{ fontSize: "1.1rem", margin: 0 }}>Voice note</h2>
        <span style={{ fontSize: "0.75rem", color: "var(--color-ink-muted)" }}>
          Proposes an update for you to review. It never changes the stage on its own.
        </span>
      </header>

      {pending.length > 0 && phase !== "uploading" ? (
        <PendingNotice entries={pending} onRetry={upload} />
      ) : null}

      {phase === "idle" ? (
        <div>
          <button type="button" className="btn btn-primary" onClick={() => setPhase("choosing")}>
            Record a voice note
          </button>
          <p style={caption}>{WHERE_THE_AUDIO_GOES}</p>
        </div>
      ) : null}

      {phase === "choosing" ? (
        <fieldset style={{ border: "1px solid var(--color-border)", borderRadius: "var(--radius)", padding: "0.8rem" }}>
          <legend style={{ fontSize: "0.85rem", padding: "0 0.4rem" }}>Who is here?</legend>
          <p style={{ ...caption, marginTop: 0 }}>
            This decides whether {prospectName} has to agree to being recorded, so it is worth
            getting right.
          </p>
          <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
            <button type="button" className="btn btn-primary" onClick={() => begin("voice_note")}>
              Just me
            </button>
            <button type="button" className="btn" onClick={() => setPhase("consent")}>
              Someone else is here
            </button>
            <button type="button" className="btn" onClick={() => setPhase("idle")}>
              Cancel
            </button>
          </div>
        </fieldset>
      ) : null}

      {phase === "consent" ? (
        <ConsentGate
          wording={consentWording}
          error={consentError}
          onAgreed={() => begin("recorded_session")}
          onCancel={() => setPhase("idle")}
        />
      ) : null}

      {phase === "recording" ? (
        <RecordingView
          level={level}
          elapsed={elapsed}
          kind={kind}
          onStop={() => stopAndUpload(new Date().toISOString())}
          onDiscard={discard}
        />
      ) : null}

      {phase === "uploading" ? (
        <p style={{ fontSize: "0.9rem" }}>
          <strong>Transcribing…</strong>{" "}
          <span style={{ color: "var(--color-ink-muted)" }}>
            Keep this page open. The recording is saved on this device until it arrives.
          </span>
        </p>
      ) : null}

      {phase === "failed" ? (
        <div style={{ ...notice, borderColor: "var(--color-error)", background: "var(--color-error-tint)" }}>
          <strong style={{ fontSize: "0.85rem" }}>That did not work.</strong>
          <p style={{ margin: "0.3rem 0 0.6rem", fontSize: "0.85rem" }}>{error}</p>
          <button type="button" className="btn" onClick={() => setPhase("idle")}>
            Start again
          </button>
        </div>
      ) : null}

      {phase === "done" && transcript ? (
        <TranscriptReview
          transcript={transcript}
          onAnother={() => {
            setTranscript(null);
            setPhase("idle");
          }}
        />
      ) : null}
    </section>
  );
}

function ConsentGate({
  wording,
  error,
  onAgreed,
  onCancel,
}: {
  wording: string | null;
  error: string | null;
  onAgreed: () => void;
  onCancel: () => void;
}) {
  if (error) {
    return (
      <div style={{ ...notice, borderColor: "var(--color-error)", background: "var(--color-error-tint)" }}>
        <p style={{ margin: "0 0 0.6rem", fontSize: "0.85rem" }}>{error}</p>
        <button type="button" className="btn" onClick={onCancel}>
          Back
        </button>
      </div>
    );
  }
  if (wording === null) {
    return <p style={caption}>Loading the consent wording…</p>;
  }
  return (
    <div style={{ ...notice, borderColor: "var(--color-accent-tint-border)", background: "var(--color-accent-tint)" }}>
      <p style={{ margin: "0 0 0.4rem", fontSize: "0.85rem", fontWeight: 600 }}>Read this out, word for word:</p>
      {/* Rendered from the API response and never edited here. What is shown is what gets stored
          as the wording the client agreed to, so the two cannot drift apart. */}
      <blockquote
        style={{
          margin: "0 0 0.8rem",
          padding: "0.7rem 0.9rem",
          background: "var(--color-paper-raised)",
          border: "1px solid var(--color-accent-tint-border)",
          borderRadius: "var(--radius)",
          fontFamily: "var(--font-serif)",
          fontSize: "1rem",
          lineHeight: 1.55,
          overflowWrap: "anywhere",
        }}
      >
        {wording}
      </blockquote>
      <p style={{ ...caption, marginTop: 0 }}>{WHERE_THE_AUDIO_GOES}</p>
      <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
        <button type="button" className="btn btn-primary" onClick={onAgreed}>
          They agreed — start recording
        </button>
        <button type="button" className="btn" onClick={onCancel}>
          They did not agree
        </button>
      </div>
      <p style={{ ...caption, marginBottom: 0 }}>
        If they did not agree, nothing is recorded and nothing is kept.
      </p>
    </div>
  );
}

function RecordingView({
  level,
  elapsed,
  kind,
  onStop,
  onDiscard,
}: {
  level: number;
  elapsed: number;
  kind: RecordingKind;
  onStop: () => void;
  onDiscard: () => void;
}) {
  const minutes = String(Math.floor(elapsed / 60)).padStart(2, "0");
  const seconds = String(elapsed % 60).padStart(2, "0");
  // A meter we could not build reads -1. Saying so beats a flat bar, which looks like silence.
  const metered = level >= 0;
  return (
    <div style={{ ...notice, borderColor: "var(--color-error)" }}>
      <div style={{ display: "flex", alignItems: "center", gap: "0.7rem", flexWrap: "wrap" }}>
        <span aria-hidden style={{ width: "0.7rem", height: "0.7rem", borderRadius: "50%", background: "var(--color-error)", flex: "0 0 auto" }} />
        <strong style={{ fontSize: "0.9rem" }}>
          Recording{kind === "recorded_session" ? " this session" : ""}
        </strong>
        <span className="mono" style={{ fontSize: "1.05rem" }} aria-label={`${elapsed} seconds recorded`}>
          {minutes}:{seconds}
        </span>
      </div>

      {metered ? (
        <div
          role="meter"
          aria-label="Microphone level"
          aria-valuenow={Math.round(level * 100)}
          aria-valuemin={0}
          aria-valuemax={100}
          style={{ height: "0.6rem", background: "var(--color-paper-sunken)", borderRadius: "var(--radius-pill)", overflow: "hidden", margin: "0.7rem 0 0.3rem" }}
        >
          <div style={{ height: "100%", width: `${Math.round(level * 100)}%`, background: "var(--color-accent)", transition: "width 80ms linear" }} />
        </div>
      ) : (
        <p style={{ ...caption, marginBottom: "0.3rem" }}>
          This browser will not show a level meter, so check the recording afterwards.
        </p>
      )}
      <p style={{ ...caption, marginTop: 0 }}>
        {metered ? "The bar should move while you talk. If it does not, your microphone is not being heard." : ""}
      </p>

      <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
        <button type="button" className="btn btn-primary" onClick={onStop}>
          Stop and transcribe
        </button>
        <button type="button" className="btn" onClick={onDiscard}>
          Discard
        </button>
      </div>
    </div>
  );
}

function TranscriptReview({
  transcript,
  onAnother,
}: {
  transcript: MeetingTranscript;
  onAnother: () => void;
}) {
  return (
    <div style={{ ...notice, borderColor: "var(--color-accent-tint-border)" }}>
      <strong style={{ fontSize: "0.85rem" }}>Transcribed. Read it before you use it.</strong>
      {/* Two limits, both learned by rendering a real one.
          `overflowWrap: anywhere` because a transcript is machine output: one long unbroken run —
          a URL, a spelled-out reference, a provider glitch — otherwise widens the whole page
          rather than wrapping, and every other panel on the prospect goes with it.
          `maxHeight` because a twenty-minute note is thousands of pixels of text that would push
          workshops, engagements and stage history off the bottom of the screen. It scrolls in
          place instead. */}
      <p
        style={{
          margin: "0.5rem 0 0.7rem",
          padding: "0.7rem 0.9rem",
          background: "var(--color-paper-sunken)",
          borderRadius: "var(--radius)",
          fontSize: "0.9rem",
          lineHeight: 1.55,
          whiteSpace: "pre-wrap",
          overflowWrap: "anywhere",
          maxHeight: "18rem",
          overflowY: "auto",
        }}
      >
        {transcript.text}
      </p>
      <p style={{ ...caption, marginTop: 0 }}>
        The recording is kept with this note, so a correction can be checked against what was said.
        {transcript.consent_confirmed_at
          ? " Consent was recorded with the exact wording the client agreed to."
          : ""}
      </p>
      <button type="button" className="btn" onClick={onAnother}>
        Record another
      </button>
    </div>
  );
}

function PendingNotice({
  entries,
  onRetry,
}: {
  entries: PendingRecording[];
  onRetry: (entry: PendingRecording) => void;
}) {
  return (
    <div style={{ ...notice, borderColor: "var(--color-warn)", background: "var(--color-warn-tint)" }}>
      <strong style={{ fontSize: "0.85rem" }}>
        {entries.length === 1
          ? "One recording on this device has not reached the server."
          : `${entries.length} recordings on this device have not reached the server.`}
      </strong>
      <ul style={{ listStyle: "none", padding: 0, margin: "0.5rem 0 0" }}>
        {entries.map((entry) => (
          <li key={entry.id} style={{ display: "flex", alignItems: "center", gap: "0.6rem", flexWrap: "wrap", padding: "0.3rem 0" }}>
            <span className="mono" style={{ fontSize: "0.75rem" }}>
              {entry.recordedAt.slice(0, 16).replace("T", " ")} · {entry.seconds}s
            </span>
            <span style={{ fontSize: "0.75rem", color: "var(--color-ink-muted)" }}>
              {entry.attempts === 1 ? "1 failed attempt" : `${entry.attempts} failed attempts`}
            </span>
            <button type="button" className="btn" onClick={() => onRetry(entry)}>
              Send it now
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

const panel: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: "0.7rem",
};

const notice: React.CSSProperties = {
  border: "1px solid var(--color-border)",
  borderRadius: "var(--radius-lg)",
  background: "var(--color-paper-raised)",
  padding: "0.9rem",
};

const caption: React.CSSProperties = {
  fontSize: "0.78rem",
  color: "var(--color-ink-muted)",
  margin: "0.5rem 0",
  lineHeight: 1.5,
};
