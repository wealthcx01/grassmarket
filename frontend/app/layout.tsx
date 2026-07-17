import type { Metadata } from "next";
import Link from "next/link";
import { Source_Serif_4, Inter, IBM_Plex_Mono } from "next/font/google";
import "./globals.css";
import { AccountMenu } from "@/components/AccountMenu";

// Three faces from the Bruntsfield design system, exposed as CSS variables that
// globals.css consumes (--font-serif / --font-sans / --font-mono).
const sourceSerif = Source_Serif_4({
  subsets: ["latin"],
  variable: "--font-serif",
  display: "swap",
});

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

const ibmPlexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Bruntsfield Advisor Studio",
  description: "Advisor platform for the Bruntsfield Advisory Network.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="en"
      className={`${sourceSerif.variable} ${inter.variable} ${ibmPlexMono.variable}`}
    >
      <body>
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

          <span className="eyebrow" style={{ marginLeft: "auto" }}>
            <span className="eyebrow-id">02</span> — Advisory
          </span>
          <Link
            href="/workbench"
            style={{
              color: "var(--color-ink-soft)",
              textDecoration: "none",
              fontSize: "0.85rem",
              padding: "0.3rem 0.75rem",
              border: "1px solid var(--color-border-strong)",
              borderRadius: "var(--radius-pill)",
            }}
          >
            Workbench
          </Link>
          <Link
            href="/help"
            style={{
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
      </body>
    </html>
  );
}
