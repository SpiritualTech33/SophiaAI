import type { Metadata } from "next";
import { Cinzel, Inter } from "next/font/google";
import "./globals.css";
import Starfield from "@/components/cosmic/Starfield";

/**
 * Mental Model:
 *   The two voices of Sophia's type system. Cinzel (a serif with Roman
 *   inscriptional roots) carries the brand and headings — it should feel
 *   carved, eternal. Inter carries the body — neutral, legible, modern.
 *   next/font self-hosts both and exposes them as CSS variables that
 *   globals.css reads through --font-brand / --font-body.
 */
const cinzel = Cinzel({
  subsets: ["latin"],
  variable: "--font-cinzel",
  display: "swap",
});

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "SophiaAI — wisdom, given hands",
  description:
    "A wisdom-grounded agent. Sophia draws on a hand-curated corpus of the " +
    "world's wisdom literature to help humans evolve.",
  icons: { icon: "/favicon.svg" },
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${cinzel.variable} ${inter.variable}`}>
      <body>
        <Starfield />
        {children}
      </body>
    </html>
  );
}
