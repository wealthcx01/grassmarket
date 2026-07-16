/**
 * Header account/session menu (GRS-0087). Shows the signed-in advisor's identity and a dropdown with
 * Profile, Settings, a link back to the public site, and Log out. Identity comes from the existing
 * client session accessor (`lib/session`) — no re-fetch, no duplicated token logic. Session controls
 * now live here (the header), so the old "Signed in · Sign out" dashboard footer is retired.
 */

"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { clearToken } from "@/lib/api";
import { getSession, type Session } from "@/lib/session";

const PUBLIC_SITE_URL = "https://bruntsfield.capital";

export function AccountMenu() {
  const router = useRouter();
  // null until mounted (the header is server-rendered; the session lives in localStorage), so the
  // first client paint matches the server and there is no signed-in/out hydration flash.
  const [session, setSession] = useState<Session | null | undefined>(undefined);
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setSession(getSession());
  }, []);

  useEffect(() => {
    if (!open) return;
    function onDown(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  function logOut() {
    clearToken();
    setOpen(false);
    router.replace("/login");
  }

  // Before mount, reserve the space with a stable placeholder (avoids layout shift + hydration flash).
  if (session === undefined) {
    return <span aria-hidden style={{ visibility: "hidden", width: "2rem" }} />;
  }

  if (session === null) {
    return (
      <Link href="/login" style={pillLinkStyle}>
        Sign in
      </Link>
    );
  }

  const initial = session.email.trim().charAt(0).toUpperCase() || "?";

  return (
    <div ref={ref} style={{ position: "relative" }}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label="Account menu"
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: "0.5rem",
          background: "none",
          border: "1px solid var(--color-border-strong)",
          borderRadius: "var(--radius-pill)",
          padding: "0.25rem 0.6rem 0.25rem 0.35rem",
          font: "inherit",
          fontSize: "0.85rem",
          color: "var(--color-ink)",
          cursor: "pointer",
        }}
      >
        <span
          aria-hidden
          style={{
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            width: "1.55rem",
            height: "1.55rem",
            borderRadius: "50%",
            background: "var(--color-accent)",
            color: "var(--color-paper)",
            fontSize: "0.8rem",
            fontWeight: 600,
          }}
        >
          {initial}
        </span>
        <span
          style={{
            maxWidth: "12rem",
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
          }}
        >
          {session.email}
        </span>
        <span aria-hidden style={{ fontSize: "0.6rem", color: "var(--color-ink-soft)" }}>
          ▼
        </span>
      </button>

      {open ? (
        <div
          role="menu"
          style={{
            position: "absolute",
            right: 0,
            top: "calc(100% + 0.4rem)",
            minWidth: "13rem",
            background: "var(--color-paper)",
            border: "1px solid var(--color-border)",
            borderRadius: "var(--radius-lg)",
            boxShadow: "0 8px 28px rgba(0,0,0,0.12)",
            padding: "0.4rem",
            zIndex: 60,
          }}
        >
          <div
            style={{
              padding: "0.4rem 0.6rem 0.5rem",
              borderBottom: "1px solid var(--color-border)",
              marginBottom: "0.3rem",
            }}
          >
            <div style={{ fontSize: "0.72rem", color: "var(--color-ink-soft)" }}>Signed in as</div>
            <div
              style={{
                fontSize: "0.85rem",
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
              }}
            >
              {session.email}
            </div>
          </div>
          <Link href="/profile" role="menuitem" style={itemStyle} onClick={() => setOpen(false)}>
            Profile
          </Link>
          <Link href="/settings" role="menuitem" style={itemStyle} onClick={() => setOpen(false)}>
            Settings
          </Link>
          <a
            href={PUBLIC_SITE_URL}
            role="menuitem"
            style={itemStyle}
            onClick={() => setOpen(false)}
          >
            bruntsfield.capital ↗
          </a>
          <button type="button" role="menuitem" onClick={logOut} style={logoutStyle}>
            Log out
          </button>
        </div>
      ) : null}
    </div>
  );
}

const pillLinkStyle: React.CSSProperties = {
  color: "var(--color-ink-soft)",
  textDecoration: "none",
  fontSize: "0.85rem",
  padding: "0.3rem 0.75rem",
  border: "1px solid var(--color-border-strong)",
  borderRadius: "var(--radius-pill)",
};

const itemStyle: React.CSSProperties = {
  display: "block",
  padding: "0.45rem 0.6rem",
  borderRadius: "var(--radius-md)",
  color: "var(--color-ink)",
  textDecoration: "none",
  fontSize: "0.85rem",
};

const logoutStyle: React.CSSProperties = {
  ...itemStyle,
  width: "100%",
  textAlign: "left",
  background: "none",
  border: "none",
  font: "inherit",
  fontSize: "0.85rem",
  color: "var(--color-accent)",
  cursor: "pointer",
};
