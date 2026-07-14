/**
 * Session-aware dashboard footer. The dashboard (app/page.tsx) is a static server component and
 * can't read the token (localStorage), so it used to tell a signed-in advisor "Not signed in?".
 * This reads the token on mount and shows the right thing — a sign-in link when signed out, and a
 * genuine sign-out when signed in (there was no sign-out control anywhere before).
 */

"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

import { clearToken, getToken } from "@/lib/api";

export function DashboardSessionFooter() {
  const router = useRouter();
  // null until mounted — matches the server render, avoiding a hydration mismatch / "signed out" flash.
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
          fontWeight: 500,
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
