"use client";

import { WorkPipeline } from "@/components/work-pipeline";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

export function WorkClient() {
  const params = useSearchParams();
  const slug = params.get("slug");
  const [note, setNote] = useState<string | null>(null);

  useEffect(() => {
    if (slug) {
      return;
    }
    setNote(sessionStorage.getItem("d1-note"));
  }, [slug]);

  if (!slug && note === null) {
    return <p className="font-ui">Reading the note.</p>;
  }
  if (!slug && !note) {
    return <p>Paste a synthetic note on the first page.</p>;
  }
  return (
    <WorkPipeline
      slug={slug}
      note={slug ? null : note}
      openedWith={slug ? "click" : "note"}
      showTour={slug === "separated"}
    />
  );
}
