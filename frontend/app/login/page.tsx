"use client";

import { useRouter } from "next/navigation";
import Link from "next/link";
import { useState, type FormEvent } from "react";
import { ApiError, api } from "@/lib/api";

// Placeholder token storage key. Loop 6 replaces this with real session management
// (httpOnly cookie / refresh flow matching the Holy Corner claim shape). Storing an
// access token in localStorage is a skeleton stand-in only.
const TOKEN_KEY = "bas.access_token";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const { access_token } = await api.login({ email, password });
      if (typeof window !== "undefined") {
        window.localStorage.setItem(TOKEN_KEY, access_token);
      }
      router.push("/");
    } catch (err: unknown) {
      const message =
        err instanceof ApiError ? err.message : "Sign in failed. Please try again.";
      setError(message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div style={{ maxWidth: "24rem", margin: "2rem auto 0" }}>
      <p
        className="mono"
        style={{
          margin: 0,
          fontSize: "0.72rem",
          letterSpacing: "0.1em",
          textTransform: "uppercase",
          color: "var(--color-ink-muted)",
        }}
      >
        Invitation-based access
      </p>
      <h1 style={{ fontSize: "1.6rem", margin: "0.3rem 0 0.4rem" }}>Sign in</h1>
      <p style={{ margin: "0 0 1.5rem", color: "var(--color-ink-muted)", fontSize: "0.9rem" }}>
        Bruntsfield Advisory Network consultants only. Accounts are created by invitation.
      </p>

      <form onSubmit={onSubmit} noValidate>
        <Field
          id="email"
          label="Email"
          type="email"
          value={email}
          autoComplete="email"
          onChange={setEmail}
        />
        <Field
          id="password"
          label="Password"
          type="password"
          value={password}
          autoComplete="current-password"
          onChange={setPassword}
        />

        {error ? (
          <p
            role="alert"
            style={{
              margin: "0 0 1rem",
              padding: "0.6rem 0.75rem",
              fontSize: "0.85rem",
              color: "var(--color-error)",
              background: "rgba(138, 32, 32, 0.06)",
              border: "1px solid rgba(138, 32, 32, 0.25)",
              borderRadius: "var(--radius)",
            }}
          >
            {error}
          </p>
        ) : null}

        <button
          type="submit"
          disabled={submitting || !email || !password}
          style={{
            width: "100%",
            padding: "0.7rem 1rem",
            fontSize: "0.95rem",
            fontWeight: 500,
            color: "var(--color-accent-contrast)",
            background: "var(--color-accent)",
            border: "none",
            borderRadius: "var(--radius)",
            cursor: submitting ? "progress" : "pointer",
            opacity: submitting || !email || !password ? 0.6 : 1,
          }}
        >
          {submitting ? "Signing in…" : "Sign in"}
        </button>
      </form>

      <p style={{ marginTop: "1.5rem", fontSize: "0.8rem", color: "var(--color-ink-muted)" }}>
        <Link href="/">Back to dashboard</Link>
      </p>
    </div>
  );
}

function Field(props: {
  id: string;
  label: string;
  type: "email" | "password";
  value: string;
  autoComplete: string;
  onChange: (value: string) => void;
}) {
  return (
    <label htmlFor={props.id} style={{ display: "block", marginBottom: "1rem" }}>
      <span
        style={{
          display: "block",
          marginBottom: "0.35rem",
          fontSize: "0.8rem",
          fontWeight: 500,
        }}
      >
        {props.label}
      </span>
      <input
        id={props.id}
        name={props.id}
        type={props.type}
        value={props.value}
        autoComplete={props.autoComplete}
        required
        onChange={(e) => props.onChange(e.target.value)}
        style={{
          width: "100%",
          padding: "0.6rem 0.75rem",
          fontSize: "0.95rem",
          fontFamily: "var(--font-sans)",
          color: "var(--color-ink)",
          background: "var(--color-paper-raised)",
          border: "1px solid var(--color-border)",
          borderRadius: "var(--radius)",
        }}
      />
    </label>
  );
}
