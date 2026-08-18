/**
 * Home welcome + context (GRS-0089). Greets the signed-in advisor (personalised from the existing
 * client session — no re-fetch), says briefly what the platform does, and orients them: start a first
 * assessment vs. resume the portfolio. It complements — never duplicates — the one-time first-run
 * walkthrough (GRS-0065) and the primer strip below it; this is a persistent greeting, not a tour.
 */

"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { getSession, type Session } from "@/lib/session";

function timeGreeting(): string {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 18) return "Good afternoon";
  return "Good evening";
}

/** A best-effort friendly first name from the email local-part (e.g. "john.gallagher@…" → "John").
 *  Identity comes from the session; we never re-fetch just to greet. */
function firstNameFromEmail(email: string): string | null {
  const local = email.split("@")[0] ?? "";
  const token = local.split(/[._-]/)[0] ?? "";
  if (!token) return null;
  return token.charAt(0).toUpperCase() + token.slice(1);
}

export function WelcomeBanner() {
  // undefined until mounted (the session lives in localStorage, the page is server-rendered), so the
  // first client paint matches the server — no personalised/anonymous greeting flash.
  const [session, setSession] = useState<Session | null | undefined>(undefined);
  useEffect(() => setSession(getSession()), []);

  const name = session ? firstNameFromEmail(session.email) : null;
  const eyebrow =
    session === undefined
      ? "Advisor dashboard"
      : name
        ? `${timeGreeting()}, ${name}`
        : timeGreeting();

  return (
    <div style={{ maxWidth: "44rem" }}>
      <p className="eyebrow">{eyebrow}</p>
      <h1 style={{ margin: "0.4rem 0 0.5rem" }}>Bruntsfield Advisor Studio</h1>
      <p
        style={{
          margin: 0,
          color: "var(--color-ink-muted)",
          fontSize: "1.05rem",
          lineHeight: 1.55,
        }}
      >
        {/* Rewritten under GRS-0243. The sentence this replaces listed the navigation back to the
            reader and survived two rounds of copy work after the founder flagged it, which is why
            it is now in the copy register (`frontend/lib/retiredCopy.ts`) with a test that fails if
            it returns. What a first-time user needs on this screen is what the product DOES, in one
            claim they can judge — not an index of the menu. */}
        You measure what a brokerage&rsquo;s platform is actually worth, and sell the work that
        closes the gap. Every number here traces to a scored assessment you can show a client.
      </p>
      <p style={{ margin: "0.9rem 0 0", fontSize: "0.95rem", lineHeight: 1.55 }}>
        Starting fresh? Begin your{" "}
        <Link href="/assessments" style={{ fontWeight: 600 }}>
          first assessment
        </Link>
        . Picking up where you left off? Your{" "}
        <Link href="/assessments" style={{ fontWeight: 600 }}>
          portfolio
        </Link>{" "}
        and{" "}
        <Link href="/pipeline" style={{ fontWeight: 600 }}>
          pipeline
        </Link>{" "}
        are a click away.
      </p>
    </div>
  );
}
