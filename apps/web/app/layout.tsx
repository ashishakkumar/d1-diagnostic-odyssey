import { NotebookShell } from "@/components/notebook-shell";
import { SiteHeader } from "@/components/editorial/site-header";
import { Literata, Playfair_Display, Space_Grotesk } from "next/font/google";
import type { ReactNode } from "react";
import "./globals.css";

// Same three families as ashk.in's Editorial theme.
const playfair = Playfair_Display({
  subsets: ["latin"],
  style: ["normal", "italic"],
  variable: "--font-playfair",
  display: "swap",
});
const literata = Literata({
  subsets: ["latin"],
  style: ["normal", "italic"],
  variable: "--font-literata",
  display: "swap",
});
const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-space-grotesk",
  display: "swap",
});

export const metadata = {
  title: "Diagnostic Odyssey: a notebook for the search for a rare-disease diagnosis",
  description:
    "Research prototype with synthetic data. Confirm symptoms in plain words, compare them with public rare-disease catalogues, and bring clear questions to a doctor. Not a diagnostic tool.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className={`${playfair.variable} ${literata.variable} ${spaceGrotesk.variable}`}>
      <body className="min-h-screen">
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:z-50 focus:bg-[var(--ed-bg-elev)] focus:px-3 focus:py-2"
        >
          Skip to content
        </a>
        <SiteHeader />
        <NotebookShell>{children}</NotebookShell>
      </body>
    </html>
  );
}
