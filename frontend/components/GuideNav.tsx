/**
 * Guide navigation shell (GRS-0134). The primer has grown long (GRS-0092–0097 + the Academy/
 * calibration sections), so a single scroll stops working. This adds a table of contents that jumps
 * to any section and tracks the one in view — a sticky rail on wide viewports, a burger drawer on
 * narrow ones. Pure client island over the server-rendered guide; it only needs the section anchors.
 */

"use client";

import { useEffect, useState } from "react";

// Must stay in sync with the `id`s on the guide's <section> elements (frontend/app/guide/page.tsx).
export const GUIDE_SECTIONS: ReadonlyArray<{ id: string; label: string }> = [
  { id: "why", label: "Why it exists" },
  { id: "provenance", label: "Where it comes from" },
  { id: "how-it-works", label: "How it works" },
  { id: "lenses", label: "Three lenses" },
  { id: "letters", label: "What the letters mean" },
  { id: "maturity", label: "Maturity levels" },
  { id: "evidence-grades", label: "Evidence grades" },
  { id: "scoring-powers", label: "Scoring the Powers" },
  { id: "seven-powers", label: "The seven Powers" },
  { id: "reading-outputs", label: "Reading the outputs" },
  { id: "calibration", label: "Calibration" },
  { id: "mistakes", label: "Mistakes to avoid" },
];

export function GuideNav() {
  const [mounted, setMounted] = useState(false);
  const [wide, setWide] = useState(false);
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState<string>(GUIDE_SECTIONS[0]!.id);

  useEffect(() => setMounted(true), []);

  useEffect(() => {
    const mq = window.matchMedia("(min-width: 1200px)");
    const sync = () => setWide(mq.matches);
    sync();
    mq.addEventListener("change", sync);
    return () => mq.removeEventListener("change", sync);
  }, []);

  useEffect(() => {
    const sections = GUIDE_SECTIONS.map((s) => document.getElementById(s.id)).filter(
      (el): el is HTMLElement => el !== null,
    );
    if (sections.length === 0) return;
    const observer = new IntersectionObserver(
      (entries) => {
        // The topmost section currently intersecting the upper part of the viewport wins.
        const visible = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);
        if (visible[0]) setActive(visible[0].target.id);
      },
      { rootMargin: "-10% 0px -70% 0px", threshold: 0 },
    );
    sections.forEach((s) => observer.observe(s));
    return () => observer.disconnect();
  }, []);

  function jump(id: string) {
    const el = document.getElementById(id);
    if (!el) return;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    el.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "start" });
    setActive(id);
    setOpen(false);
  }

  if (!mounted) return null;

  const list = (
    <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: "0.15rem" }}>
      {GUIDE_SECTIONS.map((s) => {
        const isActive = s.id === active;
        return (
          <li key={s.id}>
            <button
              type="button"
              aria-current={isActive ? "true" : undefined}
              onClick={() => jump(s.id)}
              style={{
                display: "block",
                width: "100%",
                textAlign: "left",
                padding: "0.3rem 0.6rem",
                fontSize: "0.82rem",
                lineHeight: 1.35,
                color: isActive ? "var(--color-accent)" : "var(--color-ink-muted)",
                fontWeight: isActive ? 600 : 400,
                background: "none",
                border: "none",
                borderLeft: `2px solid ${isActive ? "var(--color-accent)" : "transparent"}`,
                cursor: "pointer",
              }}
            >
              {s.label}
            </button>
          </li>
        );
      })}
    </ul>
  );

  if (wide) {
    return (
      <nav
        aria-label="On this page"
        style={{
          position: "fixed",
          top: "7rem",
          left: "max(1rem, calc((100vw - var(--content-max)) / 2 - 13rem))",
          width: "12rem",
          maxHeight: "calc(100vh - 9rem)",
          overflowY: "auto",
        }}
      >
        <p className="mono" style={{ margin: "0 0 0.5rem 0.6rem", fontSize: "0.62rem", letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--color-ink-faint)" }}>
          On this page
        </p>
        {list}
      </nav>
    );
  }

  return (
    <>
      <button
        type="button"
        aria-label={open ? "Close guide sections" : "Open guide sections"}
        aria-expanded={open}
        onClick={() => setOpen((o) => !o)}
        style={{
          position: "fixed",
          right: "1.1rem",
          bottom: "1.1rem",
          zIndex: 40,
          width: "3rem",
          height: "3rem",
          borderRadius: "50%",
          border: "1px solid var(--color-border-strong)",
          background: "var(--color-accent)",
          color: "var(--color-paper)",
          fontSize: "1.15rem",
          cursor: "pointer",
          boxShadow: "0 2px 10px rgba(0,0,0,0.18)",
        }}
      >
        {open ? "✕" : "☰"}
      </button>
      {open ? (
        <div
          onClick={() => setOpen(false)}
          style={{ position: "fixed", inset: 0, zIndex: 39, background: "rgba(0,0,0,0.4)" }}
        >
          <nav
            aria-label="On this page"
            onClick={(e) => e.stopPropagation()}
            style={{
              position: "fixed",
              right: 0,
              top: 0,
              bottom: 0,
              width: "min(17rem, 80vw)",
              background: "var(--color-paper-raised)",
              borderLeft: "1px solid var(--color-border)",
              padding: "1.25rem 0.9rem",
              overflowY: "auto",
              boxShadow: "-4px 0 16px rgba(0,0,0,0.15)",
            }}
          >
            <p className="mono" style={{ margin: "0 0 0.75rem 0.6rem", fontSize: "0.66rem", letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--color-ink-muted)" }}>
              On this page
            </p>
            {list}
          </nav>
        </div>
      ) : null}
    </>
  );
}
