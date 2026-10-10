import { NotebookShell } from "@/components/notebook-shell";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata = {
  title: "Notebook",
  description: "For research use only. Not for use in diagnostic procedures.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen">
        <NotebookShell>{children}</NotebookShell>
      </body>
    </html>
  );
}
