/**
 * Browser audio capture and the pending-upload queue (GRS-0249 scope 1 and 6).
 *
 * Two jobs, kept out of the component so both can be tested without a DOM:
 *
 * 1. **Capture.** A thin `MediaRecorder` wrapper that also runs a live level meter. The meter is
 *    not decoration. A recording that captured silence — muted mic, a phone that handed us the
 *    wrong input, permission granted to a dead device — looks exactly like a good one until it
 *    comes back empty, and by then the conversation is over. A moving meter is the only proof the
 *    advisor gets that their voice is reaching us.
 *
 * 2. **The queue.** A recording is held in IndexedDB from the moment it stops until the server
 *    answers 201, and re-uploaded on the next load if that never happened. The car park has one
 *    bar; an upload will fail there, and losing the note is the one failure in this feature that
 *    cannot be retried, because the meeting has already happened.
 */

import type { RecordingKind } from "@/lib/types";

/** What the advisor is told when we cannot get a microphone at all. */
export const NO_MICROPHONE_MESSAGE =
  "No microphone. Check the browser has permission to use it, then try again.";

/**
 * Candidate container formats, best first. Safari on iOS produces `audio/mp4` and nothing else;
 * Chrome and Firefox produce WebM. Whisper accepts both, so the browser picks and we record what
 * it actually chose rather than asserting a format it may have ignored.
 */
const PREFERRED_MIME_TYPES = [
  "audio/webm;codecs=opus",
  "audio/webm",
  "audio/mp4",
  "audio/ogg;codecs=opus",
];

export function pickMimeType(): string | null {
  if (typeof MediaRecorder === "undefined") return null;
  for (const type of PREFERRED_MIME_TYPES) {
    if (MediaRecorder.isTypeSupported(type)) return type;
  }
  // An empty string is legal: it tells MediaRecorder to choose. We read back what it picked.
  return "";
}

/** The file extension matching a recorded mime type, so the stored audio opens by double-click. */
export function extensionFor(mimeType: string): string {
  if (mimeType.includes("mp4")) return "m4a";
  if (mimeType.includes("ogg")) return "ogg";
  return "webm";
}

export type RecorderHandle = {
  /** Resolves with the finished audio. Rejects if nothing was captured. */
  stop: () => Promise<{ blob: Blob; mimeType: string; seconds: number }>;
  /** Abandon the recording and release the microphone. Nothing is returned or kept. */
  cancel: () => void;
};

export type RecorderCallbacks = {
  /** 0…1, roughly every animation frame. Drives the level meter. */
  onLevel: (level: number) => void;
  /** Whole seconds since the recording started. */
  onElapsed: (seconds: number) => void;
};

/**
 * Start recording. Throws if the browser has no microphone or the advisor declines permission —
 * never returns a handle that quietly records nothing.
 */
export async function startRecording({
  onLevel,
  onElapsed,
}: RecorderCallbacks): Promise<RecorderHandle> {
  if (typeof navigator === "undefined" || !navigator.mediaDevices?.getUserMedia) {
    throw new Error("This browser cannot record audio. Try Chrome, Safari or Firefox.");
  }
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

  const mimeType = pickMimeType();
  if (mimeType === null) {
    stream.getTracks().forEach((t) => t.stop());
    throw new Error("This browser cannot record audio. Try Chrome, Safari or Firefox.");
  }
  let recorder: MediaRecorder;
  try {
    recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
  } catch (cause) {
    // Releasing the microphone matters here. A browser that rejects the container we asked for
    // would otherwise leave the recording indicator lit with nothing recording, which is both
    // alarming to whoever is in the room and untrue.
    stream.getTracks().forEach((t) => t.stop());
    throw new Error("This browser would not start a recording. Try Chrome, Safari or Firefox.", {
      cause,
    });
  }
  const chunks: Blob[] = [];
  recorder.addEventListener("dataavailable", (event) => {
    if (event.data.size > 0) chunks.push(event.data);
  });

  // The level meter. AudioContext is separate from MediaRecorder — it reads the same stream
  // without touching what is recorded, so metering can fail without costing the recording.
  const startedAt = Date.now();
  let stopped = false;
  let audioContext: AudioContext | null = null;
  let frame = 0;
  let ticker = 0;

  try {
    audioContext = new AudioContext();
    const analyser = audioContext.createAnalyser();
    analyser.fftSize = 512;
    audioContext.createMediaStreamSource(stream).connect(analyser);
    const samples = new Uint8Array(analyser.frequencyBinCount);
    const readLevel = () => {
      if (stopped) return;
      analyser.getByteTimeDomainData(samples);
      // Root mean square around the 128 midpoint, scaled so ordinary speech sits mid-meter.
      let sum = 0;
      for (const sample of samples) {
        const centred = (sample - 128) / 128;
        sum += centred * centred;
      }
      onLevel(Math.min(1, Math.sqrt(sum / samples.length) * 3));
      frame = requestAnimationFrame(readLevel);
    };
    frame = requestAnimationFrame(readLevel);
  } catch {
    // Metering is a comfort, not the recording. If the browser refuses an AudioContext we still
    // record — but the advisor gets no meter, so `onLevel(-1)` tells the UI to say so rather than
    // show a flat bar that looks like silence.
    onLevel(-1);
  }

  ticker = window.setInterval(() => onElapsed(Math.floor((Date.now() - startedAt) / 1000)), 1000);

  const teardown = () => {
    stopped = true;
    if (frame) cancelAnimationFrame(frame);
    window.clearInterval(ticker);
    stream.getTracks().forEach((track) => track.stop());
    audioContext?.close().catch(() => undefined);
  };

  recorder.start(1000); // timeslice, so a crashed tab still leaves whole chunks behind

  return {
    stop: () =>
      new Promise((resolve, reject) => {
        recorder.addEventListener(
          "stop",
          () => {
            const seconds = Math.round((Date.now() - startedAt) / 1000);
            teardown();
            const type = recorder.mimeType || mimeType || "audio/webm";
            const blob = new Blob(chunks, { type });
            if (blob.size === 0) {
              // Fail loud (GRS-0249 scope 5). An empty recording is never uploaded, so it can
              // never become an empty note the advisor mistakes for a real one.
              reject(new Error("Nothing was recorded. The microphone captured no audio."));
              return;
            }
            resolve({ blob, mimeType: type, seconds });
          },
          { once: true },
        );
        recorder.stop();
      }),
    cancel: () => {
      teardown();
      if (recorder.state !== "inactive") recorder.stop();
    },
  };
}

/** Base64 without the `data:...;base64,` prefix, which the API does not want. */
export function toBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(new Error("Could not read the recording."));
    reader.onload = () => {
      const result = String(reader.result ?? "");
      const comma = result.indexOf(",");
      resolve(comma >= 0 ? result.slice(comma + 1) : result);
    };
    reader.readAsDataURL(blob);
  });
}

/* --------------------------------------------------------------- The pending-upload queue */

const DB_NAME = "bas.recordings";
const STORE = "pending";
const DB_VERSION = 1;

/** One recording waiting to reach the server, with everything the upload needs to be retried. */
export type PendingRecording = {
  id: string;
  blob: Blob;
  mimeType: string;
  seconds: number;
  recordedAt: string;
  prospectId: string;
  recordingKind: RecordingKind;
  consentConfirmedAt: string | null;
  consentWording: string | null;
  /** How many upload attempts have failed. Shown to the advisor, never used to give up. */
  attempts: number;
};

function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    if (typeof indexedDB === "undefined") {
      reject(new Error("This browser cannot hold a recording between attempts."));
      return;
    }
    const open = indexedDB.open(DB_NAME, DB_VERSION);
    open.onupgradeneeded = () => {
      if (!open.result.objectStoreNames.contains(STORE)) {
        open.result.createObjectStore(STORE, { keyPath: "id" });
      }
    };
    open.onsuccess = () => resolve(open.result);
    open.onerror = () => reject(open.error ?? new Error("Could not open the recording store."));
  });
}

function transact<T>(mode: IDBTransactionMode, run: (store: IDBObjectStore) => IDBRequest<T>): Promise<T> {
  return openDb().then(
    (db) =>
      new Promise<T>((resolve, reject) => {
        const tx = db.transaction(STORE, mode);
        const request = run(tx.objectStore(STORE));
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error ?? new Error("Recording store failed."));
        tx.oncomplete = () => db.close();
      }),
  );
}

/** Hold a recording before the first upload attempt. Nothing is uploaded that is not held first. */
export function holdRecording(entry: PendingRecording): Promise<unknown> {
  return transact("readwrite", (store) => store.put(entry));
}

/** Release a recording once the server has it. Called only after a 201. */
export function releaseRecording(id: string): Promise<unknown> {
  return transact("readwrite", (store) => store.delete(id));
}

export function listPendingRecordings(): Promise<PendingRecording[]> {
  return transact<PendingRecording[]>("readonly", (store) => store.getAll() as IDBRequest<PendingRecording[]>);
}

export function recordFailedAttempt(entry: PendingRecording): Promise<unknown> {
  return holdRecording({ ...entry, attempts: entry.attempts + 1 });
}
