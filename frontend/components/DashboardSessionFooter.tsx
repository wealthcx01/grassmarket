/**
 * Session-aware dashboard footer (GRS-0037). The dashboard (app/page.tsx) is a static server
 * component and can't see the token (it lives in localStorage), so it used to show
 * "Not signed in? Go to sign in" even to a logged-in advisor. This small client component reads the
 * token on mount and renders the right thing — a sign-in link when signed out, and a genuine
 * sign-out when signed in (there was no sign-out control anywhere before).
 */

"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

import { clearToken, getToken } from "@/lib/api";

export function DashboardSessionFooter() {
  const router = useRouter();
  // null = not yet known (server render + first client paint) — avoids a hydration mismatch and a
  // "not signed in" flash for signed-in users.
  const [signedIn, setSignedIn] = useState<boolean | null>(null);

  useEffect(() => {
    setSignedIn(getToken() !== null);
  }, []);

  if (signedIn === null) {
    return <span aria-hidden style={{ visibility: "hidden" }}>—</span>;
  }

  if (!signedIn) {
    return (
      <>
        Not signed in?{" "}
        <Link href="/login" style={{ fontWeight: 500 }}>
          Go to sign in
        </Link>
      </>
    );
  }

  return (
    <>
      Signed in.{" "}
      <button
        type="button"
        onClick={() => {
          clearToken();
          router.replace("/login");
        }}
        style={{
          background: "none",
          border: "none",
          padding: 0,
          font: "inherit",
          color: "var(--color-accent)",
          textDecoration: "underline",
          cursor: "pointer",
        }}
      >
        Sign out
      </button>
    </>
  );
}
