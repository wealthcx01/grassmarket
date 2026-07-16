"use client";

import { useRouter } from "next/navigation";
import Link from "next/link";
import { useEffect, useState, type FormEvent } from "react";
import { API_BASE_URL, ApiError, api } from "@/lib/api";

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

  // Google sign-in hand-off (GRS-0073): the OAuth callback returns the app here with the JWT in the
  // URL *fragment* (#access_token=…) — never a query string, never sent to a server. Store it and
  // continue. (GRS-0074 replaces the fragment with a one-time ?code= exchange for the cross-origin
  // case.)
  useEffect(() => {
    if (typeof window === "undefined") return;
    const hash = window.location.hash;
    if (!hash) return;
    const token = new URLSearchParams(hash.slice(1)).get("access_token");
    if (!token) return;
    window.localStorage.setItem(TOKEN_KEY, token);
    // Strip the token from the URL bar before routing on.
    window.history.replaceState(null, "", window.location.pathname);
    router.push("/");
  }, [router]);

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
