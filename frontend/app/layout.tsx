import type { Metadata } from "next";
import { Source_Serif_4, Inter, IBM_Plex_Mono } from "next/font/google";
import "./globals.css";
import { AppChrome } from "@/components/AppChrome";

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
        <AppChrome>{children}</AppChrome>
      </body>
    </html>
  );
}
