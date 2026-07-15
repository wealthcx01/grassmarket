import type { Metadata } from "next";
import Link from "next/link";
import { Source_Serif_4, Inter, IBM_Plex_Mono } from "next/font/google";
import "./globals.css";

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
        <header
          style={{
            position: "sticky",
            top: 0,
            zIndex: 50,
            height: "var(--topbar-height)",
            display: "flex",
            alignItems: "center",
            gap: "0.75rem",
            padding: "0 1.5rem",
            background: "var(--color-accent)",
            color: "var(--color-accent-contrast)",
            boxShadow: "0 1px 0 rgba(0,0,0,0.15), 0 6px 20px rgba(26,59,38,0.12)",
          }}
        >
          <Link
            href="/"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.6rem",
              color: "inherit",
              textDecoration: "none",
            }}
          >
            <span
              aria-hidden
              style={{
                width: "1.4rem",
                height: "1.4rem",
                borderRadius: "5px",
                background: "var(--color-accent-contrast)",
                color: "var(--color-accent)",
                fontFamily: "var(--font-serif)",
                fontWeight: 700,
                fontSize: "0.95rem",
                display: "grid",
                placeItems: "center",
                lineHeight: 1,
              }}
            >
              B
            </span>
            <span
              style={{
                fontFamily: "var(--font-serif)",
                fontWeight: 600,
                fontSize: "1rem",
                letterSpacing: "0.01em",
              }}
            >
              Bruntsfield Advisor Studio
            </span>
          </Link>
          <Link
            href="/help"
            style={{
              marginLeft: "auto",
              color: "inherit",
              textDecoration: "none",
              fontSize: "0.85rem",
              opacity: 0.92,
              padding: "0.3rem 0.7rem",
              border: "1px solid rgba(255,255,255,0.28)",
              borderRadius: "999px",
            }}
          >
            Guide
          </Link>
          <span
            className="mono"
            style={{
              fontSize: "0.68rem",
              opacity: 0.72,
              textTransform: "uppercase",
              letterSpacing: "0.1em",
            }}
          >
            Grassmarket
          </span>
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
