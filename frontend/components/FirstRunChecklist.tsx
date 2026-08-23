"use client";

/**
 * The ten-minute first-run path (GRS-0243 scope 5).
 *
 * **Deliberately not a modal tour.** One already exists (`FirstRunWalkthrough`, GRS-0065): four
 * slides, shown once, gone forever. It tells a new advisor what the product is and then leaves them
 * on the same home page they did not understand — which is the state the founder described after
 * walking every section.
 *
 * A checklist is a different instrument and the ticket asks for it specifically. It is *resumable*,
 * so an advisor who reads the primer on Monday still has three items waiting on Tuesday; it sends
 * them to four real places in the product rather than describing them; and it disappears when it is
 * finished rather than when it is dismissed.
 *
 * Both are still on the page, which is the one thing this must not become — see `page.tsx`, where
 * the walkthrough's auto-open is now conditional on the checklist being done.
 *
 * State lives in localStorage. It is a UI preference, not user data: losing it costs an advisor a
 * re-tick, and putting it in the database would mean a migration and an endpoint for something that
 * never leaves one browser.
 */

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

const STORAGE_KEY = "bas.first_run_checklist";

type Step = {
  id: string;
  label: string;
  why: string;
  href: string;
};

/**
 * Four steps, in the order the ticket names them: understand the method, see the output, see the
 * numbers behind the output, then find your own money. Each is a link to something real — reading
 * one finished example is faster than being told what one looks like.
 */
const STEPS: Step[] = [
  {
    id: "primer",
    label: "Read the three lenses in the primer",
    why: "Business, Infrastructure and Powers — what the score is actually made of.",
    href: "/guide#reading-a-score",
  },
  {
    id: "report",
    label: "Open a finished client report",
    why: "The document a client receives, on a demo brokerage. This is the output everything else feeds.",
    href: "/deliverables",
  },
  {
    id: "summary",
    label: "Step through one demo assessment's Summary",
    why: "Where the score comes from, on a firm already assessed for you.",
    href: "/assessments",
  },
  {
    id: "earnings",
    label: "Find your commission schedule",
    why: "What each kind of work pays, read live from the schedule.",
    href: "/earnings",
  },
];

function readDone(): Set<string> {
  if (typeof window === "undefined") return new Set();
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return new Set(Array.isArray(parsed) ? parsed.filter((x) => typeof x === "string") : []);
  } catch {
    // Corrupt or unreadable state starts the checklist over rather than throwing on the home page.
    return new Set();
  }
}

export function FirstRunChecklist() {
  const [done, setDone] = useState<Set<string> | null>(null);

  // Read after mount, never during render: localStorage does not exist on the server, and reading
  // it in the initial state would make the server and client markup disagree.
  useEffect(() => setDone(readDone()), []);

  const tick = useCallback((id: string) => {
    setDone((current) => {
      const next = new Set(current ?? []);
      next.add(id);
      try {
        window.localStorage.setItem(STORAGE_KEY, JSON.stringify([...next]));
      } catch {
        // A browser refusing storage still gets a working checklist for this session.
      }
      return next;
    });
  }, []);

  // `null` means "not read yet" — render nothing rather than flashing a full checklist at an
  // advisor who finished it weeks ago.
  if (done === null) return null;
  if (STEPS.every((step) => done.has(step.id))) return null;

  const completed = STEPS.filter((s) => done.has(s.id)).length;

  return (
    <section
      data-testid="first-run-checklist"
      style={{
        border: "1px solid var(--color-rule)",
        borderRadius: "var(--radius)",
        padding: "1.1rem 1.3rem",
        marginBottom: "1.5rem",
        maxWidth: "44rem",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", gap: "1rem", alignItems: "baseline", flexWrap: "wrap" }}>
        <h2 style={{ margin: 0, fontSize: "1rem" }}>Ten minutes to get your bearings</h2>
        <span className="mono" style={{ fontSize: "0.68rem", color: "var(--color-ink-faint)" }}>
          {completed} of {STEPS.length}
        </span>
      </div>
      <p style={{ margin: "0.4rem 0 0.8rem", fontSize: "0.84rem", color: "var(--color-ink-muted)" }}>
        Four things to look at, in this order. Come back to it — it keeps your place, and disappears
        once you have done all four.
      </p>
      <ol style={{ listStyle: "none", margin: 0, padding: 0, display: "grid", gap: "0.55rem" }}>
        {STEPS.map((step) => {
          const isDone = done.has(step.id);
          return (
            <li
              key={step.id}
              style={{ display: "flex", gap: "0.7rem", alignItems: "baseline", opacity: isDone ? 0.55 : 1 }}
            >
              <span
                className="mono"
                aria-hidden
                style={{ color: isDone ? "var(--color-accent)" : "var(--color-ink-faint)", fontSize: "0.8rem" }}
              >
                {isDone ? "✓" : "○"}
              </span>
              <span style={{ fontSize: "0.86rem" }}>
                {/* Ticking happens on the click that takes them there. Asking an advisor to
                    navigate away and then come back to tick a box is how a checklist stops being
                    used — and the tick is a bookmark, not a claim that they read it carefully. */}
                <Link
                  href={step.href}
                  onClick={() => tick(step.id)}
                  style={{ fontWeight: isDone ? 400 : 600 }}
                >
                  {step.label}
                </Link>
                <span style={{ display: "block", color: "var(--color-ink-faint)", fontSize: "0.78rem" }}>
                  {step.why}
                </span>
              </span>
            </li>
          );
        })}
      </ol>
    </section>
  );
}

/** Whether the checklist is finished — used to keep two orientation devices off one screen. */
export function firstRunChecklistComplete(): boolean {
  const done = readDone();
  return STEPS.every((step) => done.has(step.id));
}
