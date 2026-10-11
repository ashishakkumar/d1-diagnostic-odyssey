"use client";

import { ComparisonPanel, type ComparisonReport } from "@/components/comparison-panel";
import { SummaryPreview } from "@/components/summary-preview";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

export default function SummaryPage() {
  const params = useParams<{ id: string }>();
  const [text, setText] = useState<string>("");
  const [report, setReport] = useState<ComparisonReport | null>(null);
  const [prior, setPrior] = useState<string | null>(null);
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
    fetch(`/api/cases/${params.id}/report`)
      .then(async (response) => {
        if (!response.ok) {
          throw new Error("down");
        }
        return (await response.json()) as ComparisonReport;
      })
      .then(setReport)
      .catch(() => setError("The notebook cannot reach the API."));
  }, [params.id]);

  return (
    <section className="space-y-4">
      <h1 className="text-2xl">Summary for a doctor</h1>
      {error ? <p>{error}</p> : null}
      {report && report.evidence.length > 0 ? <ComparisonPanel report={report} /> : null}
      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          onChange={async (event) => {
            if (!event.target.checked) {
              setPrior(null);
              return;
            }
            const response = await fetch(
              `/api/cases/${params.id}/population-prior?opt_in=true`,
            );
            if (!response.ok) {
              setPrior("The population prior is absent.");
              return;
            }
            const body = (await response.json()) as {
              label?: string;
              limits?: string;
              allele_frequency?: number | null;
              found?: boolean;
              source?: string | null;
              version?: string | null;
            };
            const frequency =
              body.found && body.allele_frequency != null ? ` ${body.allele_frequency}.` : "";
            setPrior(
              `${body.label ?? ""} ${body.source ?? ""} ${body.version ?? ""}.${frequency} ${body.limits ?? ""}`.trim(),
            );
          }}
        />
        Show the experimental population prior
      </label>
      {prior ? (
        <p data-testid="population-prior">{prior}</p>
      ) : null}
      {text ? (
        <SummaryPreview text={text} pdfHref={`/api/cases/${params.id}/summary.pdf`} />
      ) : null}
    </section>
  );
}
