"use client";

import { CaseNav } from "@/components/case-nav";
import { useParams } from "next/navigation";
import type { ReactNode } from "react";

export default function CaseLayout({ children }: { children: ReactNode }) {
  const params = useParams<{ id: string }>();
  return (
    <div className="space-y-6">
      <CaseNav caseId={params.id} />
      {children}
    </div>
  );
}
