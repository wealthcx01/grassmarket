"use client";

import { useRouter } from "next/navigation";
import Link from "next/link";
import { useEffect, useState, type FormEvent } from "react";
import { API_BASE_URL, ApiError, api, setTokens } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Google sign-in hand-off (GRS-0074): the OAuth callback returns the app here with a single-use
  // ?code=… (NEVER the JWT). Exchange it server-side over POST for the real token, store that, and
  // continue. The code is stripped from the URL bar immediately.
  useEffect(() => {
    if (typeof window === "undefined") return;
    const code = new URLSearchParams(window.location.search).get("code");
    if (!code) return;
    // Strip the code from the URL before the async exchange so a refresh can't replay it.
    window.history.replaceState(null, "", window.location.pathname);
    let cancelled = false;
    (async () => {
      try {
        const { access_token, refresh_token } = await api.exchangeSession(code);
        if (cancelled) return;
        setTokens(access_token, refresh_token);
        router.push("/");
      } catch (err: unknown) {
        if (cancelled) return;
        setError(err instanceof ApiError ? err.message : "Sign in failed. Please try again.");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [router]);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const { access_token, refresh_token } = await api.login({ email, password });
      setTokens(access_token, refresh_token);
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
    <div style={{ maxWidth: "26rem", margin: "3rem auto 0" }}>
      <div className="card" style={{ padding: "2rem 2rem 2.25rem" }}>
        <p className="eyebrow">Invitation-based access</p>
        <h1 style={{ fontSize: "1.7rem", margin: "0.4rem 0 0.5rem" }}>Sign in</h1>
        <p style={{ margin: "0 0 1.5rem", color: "var(--color-ink-muted)", fontSize: "0.92rem", lineHeight: 1.5 }}>
          Bruntsfield Advisory Network consultants only. Accounts are created by invitation.
        </p>

        <form onSubmit={onSubmit} noValidate>
          <Field id="email" label="Email" type="email" value={email} autoComplete="email" onChange={setEmail} />
          <Field
            id="password"
            label="Password"
            type="password"
            value={password}
            autoComplete="current-password"
            onChange={setPassword}
          />

          {error ? (
            <p role="alert" className="callout callout-error" style={{ margin: "0 0 1rem" }}>
              {error}
            </p>
          ) : null}

          <button
            type="submit"
            className="btn btn-primary"
            disabled={submitting || !email || !password}
            style={{ width: "100%", padding: "0.7rem 1rem", fontSize: "0.95rem" }}
          >
            {submitting ? "Signing in…" : "Sign in"}
          </button>
        </form>

        <div style={{ display: "flex", alignItems: "center", gap: "0.6rem", margin: "1.25rem 0" }}>
          <span className="hr" style={{ flex: 1 }} />
          <span style={{ fontSize: "0.75rem", color: "var(--color-ink-faint)" }}>or</span>
          <span className="hr" style={{ flex: 1 }} />
        </div>

        {/* Google sign-in: a plain link to the backend's OAuth start (backend is the OAuth client). */}
        <a
          href={`${API_BASE_URL}/auth/google/start`}
          className="btn btn-secondary"
          style={{ width: "100%", padding: "0.7rem 1rem", fontSize: "0.95rem", textAlign: "center", textDecoration: "none" }}
        >
          Sign in with Google
        </a>
      </div>

      <p style={{ marginTop: "1.25rem", fontSize: "0.82rem", color: "var(--color-ink-muted)", textAlign: "center" }}>
        <Link href="/">← Back to dashboard</Link>
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
      <span style={{ display: "block", marginBottom: "0.4rem", fontSize: "0.82rem", fontWeight: 500 }}>
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
        style={{ width: "100%" }}
      />
    </label>
  );
}
