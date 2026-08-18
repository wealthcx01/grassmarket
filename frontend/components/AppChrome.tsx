/**
 * The advisor-app chrome (GRS-0220 wiring).
 *
 * Extracted from the root layout for one reason: the shared client report at `/r/<token>` is read
 * by a CLIENT, not an advisor. Rendering the app's header there showed them a "Sign in" button, a
 * "Guide" link and the advisor's own account avatar — which is confusing, leaks that this is an
 * internal tool, and (the avatar being positioned) overlapped the report's first figure.
 *
 * A route group with its own root layout would be the Next-idiomatic escape, but it means moving
 * every existing route into a group. Hiding the chrome on the one public path is smaller, and it
 * keeps the public surface a deliberate exception rather than a structural fork.
 */

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { AccountMenu } from "@/components/AccountMenu";
import { ActingAsBanner } from "@/components/ActingAsBanner";
import { PrimaryNav } from "@/components/PrimaryNav";

/** Paths rendered bare, with no advisor chrome and no layout gutter. */
function isPublicSurface(pathname: string | null): boolean {
  return Boolean(pathname?.startsWith("/r/"));
}

export function AppChrome({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  if (isPublicSurface(pathname)) {
    // The page owns its own <main> and measure. No header, no wrapper — a client's report should
    // look like a document, not like a page inside someone else's application.
    return <>{children}</>;
  }

  return (
    <>
      {/* Above the header, and fixed: an admin who forgets they are acting as an advisor will read
          that advisor's pipeline as their own and write as them without noticing (GRS-0208). It
          renders nothing when not acting-as. */}
      <ActingAsBanner />
      {/* BC site chrome: paper header + hairline rule (not a colour bar), the Bruntsfield
          wordmark lockup with the "ADVISORY" sub-label in accent green. Matches the
          bruntsfield.capital header so the login redirect reads as one continuous site. */}
      <header
        style={{
          position: "sticky",
          top: 0,
          zIndex: 50,
          minHeight: "var(--topbar-height)",
          display: "flex",
          alignItems: "center",
          gap: "1rem",
          padding: "0 1.5rem",
          background: "var(--color-paper)",
          color: "var(--color-ink)",
          borderBottom: "1px solid var(--color-border)",
        }}
      >
        <Link
          href="/"
          aria-label="Bruntsfield Advisory — home"
          style={{
            display: "inline-flex",
            flexDirection: "column",
            justifyContent: "center",
            lineHeight: 1,
            color: "inherit",
            textDecoration: "none",
          }}
        >
          <span
            style={{
              fontFamily: "var(--font-serif)",
              fontWeight: 500,
              fontSize: "1.35rem",
              letterSpacing: "-0.012em",
              color: "var(--color-ink)",
            }}
          >
            Bruntsfield
          </span>
          <span
            style={{
              fontFamily: "var(--font-sans)",
              fontWeight: 500,
              fontSize: "0.62rem",
              letterSpacing: "0.42em",
              textTransform: "uppercase",
              color: "var(--color-accent)",
              marginTop: "3px",
            }}
          >
            Advisory
          </span>
        </Link>

        {/* Primary section navigation (GRS-0186), with a mobile drawer. */}
        <PrimaryNav />

        <Link
          href="/guide"
          style={{
            marginLeft: "auto",
            color: "var(--color-ink-soft)",
            textDecoration: "none",
            fontSize: "0.85rem",
            padding: "0.3rem 0.75rem",
            border: "1px solid var(--color-border-strong)",
            borderRadius: "var(--radius-pill)",
          }}
        >
          Guide
        </Link>
        <AccountMenu />
      </header>
      <main
        style={{
          maxWidth: "var(--content-max)",
          margin: "0 auto",
          padding: "3rem 1.5rem 5rem",
        }}
      >
        {children}
      </main>
    </>
  );
}
