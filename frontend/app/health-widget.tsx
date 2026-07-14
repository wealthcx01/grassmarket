"use client";

import { useEffect, useState } from "react";
import { ApiError, api, type HealthResponse } from "@/lib/api";

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

  const label =
    state.kind === "loading"
      ? "Checking…"
      : state.kind === "ok"
        ? `System ${state.data.status}${state.data.version ? ` · v${state.data.version}` : ""}`
        : "System unreachable";

  return (
    <div
      title={state.kind === "error" ? state.message : undefined}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "0.5rem",
        padding: "0.4rem 0.75rem",
        background: "var(--color-paper-raised)",
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-pill)",
        boxShadow: "var(--shadow-sm)",
        fontSize: "0.78rem",
        color: state.kind === "error" ? "var(--color-error)" : "var(--color-ink-muted)",
        whiteSpace: "nowrap",
      }}
    >
      <span
        aria-hidden
        style={{
          width: "0.5rem",
          height: "0.5rem",
          borderRadius: "50%",
          background: DOT[state.kind],
          boxShadow:
            state.kind === "ok" ? "0 0 0 3px color-mix(in srgb, var(--color-ok) 18%, transparent)" : "none",
        }}
      />
      <span className="mono" style={{ letterSpacing: "0.04em" }}>
        {label}
      </span>
    </div>
  );
}
