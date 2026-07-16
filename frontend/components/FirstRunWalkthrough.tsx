/**
 * First-run walkthrough (GRS-0065). A short, skippable orientation shown once on a new advisor's
 * first signed-in visit to the dashboard, then never again (a localStorage flag — a UI preference,
 * not user data). Replayable from the guide via `/?tour=1`. Kept deliberately brief and quiet: no
 * gamification, honest about what the product is — consistent with the platform's ethos.
 */

"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import { getToken } from "@/lib/api";

const SEEN_KEY = "bas.onboarding_seen";

type Slide = { title: string; body: React.ReactNode };

const SLIDES: Slide[] = [
  {
    title: "Welcome to the Advisor Studio",
    body: (
      <>
        This is where you run the Bruntsfield method end to end — from a first prospect to a
        peer-reviewed, finalised assessment and a client deliverable. Ninety seconds to get your
        bearings.
      </>
    ),
  },
  {
    title: "The workflow, in four moves",
    body: (
      <ul style={{ margin: 0, paddingLeft: "1.1rem", display: "grid", gap: "0.5rem" }}>
        <li>
          <b>Pipeline</b> — track prospects across ten stages, with a currency-free forecast.
        </li>
        <li>
          <b>Assessments</b> — score a company with the Platform Power wizard (7 Powers, Platform Value, 9
          infrastructure modules).
        </li>
        <li>
          <b>Deliverables</b> — turn a finalised score into a client report.
        </li>
        <li>
          <b>Earnings</b> — see your commission and fees, with a downloadable statement.
        </li>
      </ul>
    ),
  },
  {
    title: "Honest by design",
    body: (
      <ul style={{ margin: 0, paddingLeft: "1.1rem", display: "grid", gap: "0.5rem" }}>
        <li>Uncertainty is shown as loudly as the headline — never false precision.</li>
        <li>
          Every assessment is peer-reviewed — a second independent rater and committee sign-off —
          before it can finalise.
        </li>
        <li>AI drafts; you approve. Nothing AI-written reaches a client without your sign-off.</li>
      </ul>
    ),
  },
  {
    title: "You're set",
    body: (
      <>
        New to Platform Power? Start with the ten-minute primer. Otherwise, jump into your pipeline — and the{" "}
        <b>Guide</b> in the top bar is always there when you need the how-to.
      </>
    ),
  },
];

export function FirstRunWalkthrough() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [i, setI] = useState(0);
  const dialogRef = useRef<HTMLDivElement>(null);
  const primaryRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!getToken()) return; // only for signed-in advisors
    let forced = false;
    try {
      forced = new URLSearchParams(window.location.search).get("tour") === "1";
    } catch {
      forced = false;
    }
    const seen = (() => {
      try {
        return localStorage.getItem(SEEN_KEY) === "1";
      } catch {
        return false;
      }
    })();
    if (forced || !seen) setOpen(true);
  }, []);

  const dismiss = useCallback(() => {
    try {
      localStorage.setItem(SEEN_KEY, "1");
    } catch {
      /* private mode — the worst case is it shows again, which is harmless */
    }
    setOpen(false);
    // Drop the ?tour=1 param so a refresh doesn't reopen it.
    try {
      if (new URLSearchParams(window.location.search).get("tour")) router.replace("/");
    } catch {
      /* ignore */
    }
  }, [router]);

  const go = useCallback(
    (to: string) => {
      dismiss();
      router.push(to);
    },
    [dismiss, router],
  );

  // Focus the primary action on open / step change; close on Escape; wrap Tab within the dialog.
  useEffect(() => {
    if (!open) return;
    primaryRef.current?.focus();
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") {
        e.preventDefault();
        dismiss();
        return;
      }
      if (e.key === "Tab" && dialogRef.current) {
        const focusable = dialogRef.current.querySelectorAll<HTMLElement>(
          'button, a[href], [tabindex]:not([tabindex="-1"])',
        );
        if (focusable.length === 0) return;
        const first = focusable[0]!;
        const last = focusable[focusable.length - 1]!;
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, i, dismiss]);

  if (!open) return null;
  const last = i === SLIDES.length - 1;
  const slide = SLIDES[i]!;

  return (
    <div
      onClick={dismiss}
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 100,
        background: "rgba(16, 20, 14, 0.55)",
        display: "grid",
        placeItems: "center",
        padding: "1.5rem",
      }}
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="onboarding-title"
        onClick={(e) => e.stopPropagation()}
        style={{
          width: "min(34rem, 100%)",
          background: "var(--color-paper-raised)",
          color: "var(--color-ink)",
          border: "1px solid var(--color-border)",
          borderRadius: "calc(var(--radius) * 1.5)",
          boxShadow: "0 12px 48px rgba(0,0,0,0.28)",
          padding: "1.6rem 1.75rem 1.4rem",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.4rem" }}>
          <p className="eyebrow" style={{ margin: 0 }}>
            Getting started · {i + 1} of {SLIDES.length}
          </p>
          <button
            type="button"
            onClick={dismiss}
            aria-label="Skip the tour"
            style={{ background: "none", border: "none", color: "var(--color-ink-muted)", cursor: "pointer", fontSize: "0.82rem", padding: "0.2rem 0.3rem" }}
          >
            Skip
          </button>
        </div>

        <h2 id="onboarding-title" style={{ margin: "0 0 0.6rem", fontSize: "1.35rem" }}>
          {slide.title}
        </h2>
        <div style={{ color: "var(--color-ink-muted)", fontSize: "0.95rem", lineHeight: 1.6, minHeight: "6.5rem" }}>
          {slide.body}
        </div>

        {/* progress dots */}
        <div style={{ display: "flex", gap: "0.35rem", margin: "1.1rem 0 1.2rem" }} aria-hidden>
          {SLIDES.map((_, j) => (
            <span
              key={j}
              style={{
                width: j === i ? "1.4rem" : "0.5rem",
                height: "0.5rem",
                borderRadius: "999px",
                background: j === i ? "var(--color-accent)" : "var(--color-border)",
                transition: "width 0.15s",
              }}
            />
          ))}
        </div>

        <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", flexWrap: "wrap" }}>
          {i > 0 ? (
            <button type="button" className="btn btn-ghost" onClick={() => setI((v) => v - 1)}>
              ← Back
            </button>
          ) : null}
          <span style={{ flex: 1 }} />
          {last ? (
            <>
              <button type="button" className="btn btn-secondary" onClick={() => go("/guide")}>
                Read the primer
              </button>
              <button ref={primaryRef} type="button" className="btn btn-primary" onClick={() => go("/pipeline")}>
                Go to my pipeline →
              </button>
            </>
          ) : (
            <button ref={primaryRef} type="button" className="btn btn-primary" onClick={() => setI((v) => v + 1)}>
              Next →
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
