import { NotebookShell } from "@/components/notebook-shell";
import type { ReactNode } from "react";
import { Literata, Playfair_Display, Space_Grotesk } from "next/font/google";
import "./globals.css";

const playfair = Playfair_Display({
  subsets: ["latin"],
  variable: "--font-playfair",
});

const literata = Literata({
  subsets: ["latin"],
  variable: "--font-literata",
});

const grotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-grotesk",
});

export const metadata = {
  title: "Diagnostic Odyssey",
  description: "For research use only. Not for use in diagnostic procedures.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html
      lang="en"
      className={`${playfair.variable} ${literata.variable} ${grotesk.variable}`}
    >
      <body className="min-h-screen font-serif text-ink">
        <NotebookShell>{children}</NotebookShell>
      </body>
    </html>
  );
}
