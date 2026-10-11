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
  const [labels, setLabels] = useState<Record<string, string>>({});
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
    fetch(`/api/cases/${params.id}/timeline`)
      .then(async (response) => {
        if (!response.ok) {
          return;
        }
        const body = (await response.json()) as {
          events: Array<{ kind: string; body: { hpo_id?: string; label?: string } }>;
        };
        const map: Record<string, string> = {};
        for (const event of body.events) {
          if (event.kind === "hpo_term" && event.body.hpo_id && event.body.label) {
            map[event.body.hpo_id] = event.body.label;
          }
        }
        setLabels(map);
      })
      .catch(() => undefined);
  }, [params.id]);

  return (
    <section className="space-y-8">
      <header className="space-y-2">
        <p className="font-mono-label">Step 4 · Hand over</p>
        <h1 className="font-display text-3xl italic md:text-4xl">Summary for a doctor</h1>
        <p className="max-w-[56ch] text-[var(--ed-fg-soft)]">
          What was confirmed, what the public catalogues show about it, and what to ask. Read the comparison first, then
          the page. Neither is a diagnosis.
        </p>
      </header>
      {error ? (
        <p role="alert" className="border border-[var(--ed-accent)] p-3 text-[var(--ed-fg)]">
          {error}
        </p>
      ) : null}
      {report && report.evidence.length > 0 ? <ComparisonPanel report={report} termLabels={labels} /> : null}
      <label className="flex items-center gap-2 font-[family-name:var(--font-label)] text-sm text-[var(--ed-fg-soft)]">
        <input
          type="checkbox"
          className="h-4 w-4 accent-[var(--ed-accent)]"
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
        <p data-testid="population-prior" className="ed-paper max-w-[70ch] p-4 text-[0.9375rem]">{prior}</p>
      ) : null}
      {text ? (
        <SummaryPreview text={text} pdfHref={`/api/cases/${params.id}/summary.pdf`} />
      ) : null}
    </section>
  );
}
