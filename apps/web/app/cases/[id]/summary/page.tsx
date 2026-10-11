"use client";

import { SummaryPreview } from "@/components/summary-preview";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

export default function SummaryPage() {
  const params = useParams<{ id: string }>();
  const [text, setText] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`/api/cases/${params.id}/summary`)
      .then(async (response) => {
        if (!response.ok) {
          throw new Error("down");
        }
        return response.text();
      })
      .then(setText)
      .catch(() => setError("The notebook cannot reach the API."));
  }, [params.id]);

  return (
    <section className="space-y-4">
      <h1 className="text-2xl">Summary for a doctor</h1>
      {error ? <p>{error}</p> : null}
      {text ? (
        <SummaryPreview text={text} pdfHref={`/api/cases/${params.id}/summary.pdf`} />
      ) : null}
    </section>
  );
}
