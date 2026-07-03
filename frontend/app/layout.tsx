import type { Metadata } from "next";
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
            height: "var(--topbar-height)",
            display: "flex",
            alignItems: "center",
            padding: "0 1.25rem",
            background: "var(--color-accent)",
            color: "var(--color-accent-contrast)",
            borderBottom: "1px solid rgba(0,0,0,0.15)",
          }}
        >
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
          <span
            className="mono"
            style={{
              marginLeft: "auto",
              fontSize: "0.7rem",
              opacity: 0.7,
              textTransform: "uppercase",
              letterSpacing: "0.08em",
            }}
          >
            Grassmarket · Loop 0
          </span>
        </header>
        <main
          style={{
            maxWidth: "var(--content-max)",
            margin: "0 auto",
            padding: "2.5rem 1.25rem 4rem",
          }}
        >
          {children}
        </main>
      </body>
    </html>
  );
}
