import { NoticeFooter } from "@/components/notice-footer";
import type { ReactNode } from "react";

export function NotebookShell({ children }: { children: ReactNode }) {
  return (
    <>
      <main id="main" className="min-h-[70vh]">
        {children}
      </main>
      <NoticeFooter />
    </>
  );
}
