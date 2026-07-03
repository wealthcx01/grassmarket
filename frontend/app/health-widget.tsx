"use client";

import { useEffect, useState } from "react";
import { API_BASE_URL, ApiError, api, type HealthResponse } from "@/lib/api";

type State =
  | { kind: "loading" }
  | { kind: "ok"; data: HealthResponse }
  | { kind: "error"; message: string };

const DOT: Record<State["kind"], string> = {
  loading: "var(--color-ink-muted)",
  ok: "var(--color-ok)",
  error: "var(--color-error)",
};

/**
 * Backend health widget. Fetches ${NEXT_PUBLIC_API_BASE_URL}/health on mount.
 * Client component so the fetch runs in the browser against the advisor's own session.
 */
export function HealthWidget() {
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    api
      .health(controller.signal)
      .then((data) => setState({ kind: "ok", data }))
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        const message = err instanceof ApiError ? err.message : "Unknown error";
        setState({ kind: "error", message });
      });
    return () => controller.abort();
  }, []);

  return (
    <div
      style={{
        minWidth: "13rem",
        padding: "0.9rem 1rem",
        background: "var(--color-paper-raised)",
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius)",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "0.5rem",
          fontSize: "0.72rem",
          letterSpacing: "0.08em",
          textTransform: "uppercase",
          color: "var(--color-ink-muted)",
        }}
        className="mono"
      >
        <span
          aria-hidden
          style={{
            width: "0.55rem",
            height: "0.55rem",
            borderRadius: "50%",
            background: DOT[state.kind],
          }}
        />
        Backend health
      </div>
      <div style={{ marginTop: "0.5rem", fontSize: "0.9rem" }}>
        {state.kind === "loading" && <span>Checking…</span>}
        {state.kind === "ok" && (
          <span>
            <strong>{state.data.status}</strong>
            {state.data.version ? (
              <span className="mono" style={{ color: "var(--color-ink-muted)" }}>
                {" "}
                · v{state.data.version}
              </span>
            ) : null}
          </span>
        )}
        {state.kind === "error" && (
          <span style={{ color: "var(--color-error)" }}>{state.message}</span>
        )}
      </div>
      <div
        className="mono"
        style={{ marginTop: "0.4rem", fontSize: "0.62rem", color: "var(--color-ink-muted)" }}
      >
        {API_BASE_URL}
      </div>
    </div>
  );
}
