"use client";

import { CaseNav } from "@/components/case-nav";
import { useParams, useSelectedLayoutSegment } from "next/navigation";
import type { ReactNode } from "react";

export default function CaseLayout({ children }: { children: ReactNode }) {
  const params = useParams<{ id: string }>();
  const segment = useSelectedLayoutSegment();
  return (
    <div className="ed-shell max-w-4xl space-y-8 py-10 md:py-14">
      <CaseNav caseId={params.id} current={segment ?? undefined} />
      {children}
    </div>
  );
}
