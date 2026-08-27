/**
 * Primary navigation (GRS-0186). Five section links with an active state, plus a mobile drawer.
 * Kept as a client component (it needs usePathname + local open state) so the root layout can stay
 * a server component and keep its metadata + font wiring server-side.
 */

"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS: { href: string; label: string }[] = [
  { href: "/pipeline", label: "Pipeline" },
  { href: "/prospecting", label: "Prospecting" },
  { href: "/portfolio", label: "Portfolio" },
  { href: "/engagements", label: "Engagements" },
  { href: "/deliverables", label: "Deliverables" },
  { href: "/workbench", label: "Workbench" },
  { href: "/earnings", label: "Earnings" },
];

function isActive(pathname: string, href: string): boolean {
  return pathname === href || pathname.startsWith(href + "/");
}

function navLinkStyle(active: boolean): React.CSSProperties {
  return {
    color: active ? "var(--color-ink)" : "var(--color-ink-soft)",
    textDecoration: "none",
    fontSize: "0.85rem",
    padding: "0.25rem 0",
    borderBottom: active ? "2px solid var(--color-accent)" : "2px solid transparent",
  };
}

export function PrimaryNav() {
  const pathname = usePathname() ?? "";
  const [mobile, setMobile] = useState(false);
  const [open, setOpen] = useState(false);

  // A media LISTENER (not CSS-only) so the row and the hamburger never both render (GRS-0186).
  useEffect(() => {
    const mq = window.matchMedia("(max-width: 767px)");
    const sync = () => setMobile(mq.matches);
    sync();
    mq.addEventListener("change", sync);
    return () => mq.removeEventListener("change", sync);
  }, []);

  // Escape closes the drawer.
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  if (!mobile) {
    return (
      <nav aria-label="Primary" style={{ display: "flex", gap: "1.1rem", marginLeft: "2rem" }}>
        {LINKS.map((l) => {
          const active = isActive(pathname, l.href);
          return (
            <Link
              key={l.href}
              href={l.href}
              aria-current={active ? "page" : undefined}
              style={navLinkStyle(active)}
            >
              {l.label}
            </Link>
          );
        })}
      </nav>
    );
  }

  return (
    <>
      <button
        type="button"
        aria-label="Open navigation"
        aria-expanded={open}
        aria-controls="primary-nav-drawer"
        onClick={() => setOpen((o) => !o)}
        style={{
          marginLeft: "1rem",
          background: "none",
          border: "1px solid var(--color-border-strong)",
          borderRadius: "var(--radius)",
          padding: "0.35rem 0.6rem",
          cursor: "pointer",
          color: "var(--color-ink)",
          font: "inherit",
        }}
      >
        Menu
      </button>
      {open ? (
        <>
          {/* Scrim: click to close. */}
          <div
            onClick={() => setOpen(false)}
            style={{ position: "fixed", inset: 0, background: "transparent", zIndex: 40 }}
            aria-hidden
          />
          <nav
            id="primary-nav-drawer"
            aria-label="Primary"
            style={{
              position: "absolute",
              left: 0,
              right: 0,
              top: "100%",
              zIndex: 41,
              display: "flex",
              flexDirection: "column",
              background: "var(--color-paper)",
              borderBottom: "1px solid var(--color-border)",
              padding: "0.5rem 1.25rem",
            }}
          >
            {LINKS.map((l) => {
              const active = isActive(pathname, l.href);
              return (
                <Link
                  key={l.href}
                  href={l.href}
                  aria-current={active ? "page" : undefined}
                  onClick={() => setOpen(false)}
                  style={{
                    color: active ? "var(--color-ink)" : "var(--color-ink-soft)",
                    textDecoration: "none",
                    fontSize: "0.95rem",
                    padding: "0.6rem 0",
                    borderBottom: "1px solid var(--color-border)",
                  }}
                >
                  {l.label}
                </Link>
              );
            })}
          </nav>
        </>
      ) : null}
    </>
  );
}
