import { EvidenceGrid } from "@/components/editorial/evidence-grid";

export type ComparisonReport = {
  evidence: Array<{
    hpo_id: string;
    source: string;
    version: string;
    orphanet_id?: string | null;
    relation: string;
  }>;
  margin: number | null;
  margin_reason?: "runner_up_ratio_is_zero";
  margin_fact?: string | null;
  abstain_reason?: string;
  leading_orphanet_id?: string;
  abstained: boolean;
};

export function ComparisonPanel({
  report,
  termLabels,
}: {
  report: ComparisonReport;
  termLabels?: Record<string, string>;
}) {
  const first = report.evidence[0];
  return (
    <section className="space-y-5" data-testid="comparison">
      <div className="space-y-2">
        <p className="font-mono-label">What the comparison shows</p>
        <h2 className="font-display text-2xl italic">Catalogue comparison</h2>
        <p className="border-l-2 border-[var(--ed-accent)] pl-3 text-[var(--ed-fg)]">
          This is not a diagnosis. The reported variant is not an input.
        </p>
      </div>

      <EvidenceGrid
        evidence={report.evidence}
        termLabels={termLabels}
        leadingId={report.abstained ? undefined : report.leading_orphanet_id}
      />

      <div className="space-y-2 text-[0.9375rem]">
        {report.abstained ? (
          <p className="font-display text-xl italic text-[var(--ed-fg)]">
            No row is separated from the others. This does not mean you are well.
          </p>
        ) : (
          <p className="text-[var(--ed-fg)]">
            First row {report.leading_orphanet_id}. Source {first?.source} {first?.version}.
          </p>
        )}
        {report.margin_reason === "runner_up_ratio_is_zero" ? (
          <p>The next row has a ratio of zero. The margin is not a finite number.</p>
        ) : null}
        {report.margin_fact ? <p>{report.margin_fact}</p> : null}
        {report.margin != null && !report.abstained ? <p>Margin {report.margin.toFixed(3)}.</p> : null}
        <p data-testid="public-ranker" className="text-[var(--ed-fg-soft)]">
          The rows on this page are the synthetic frequency-bin card. The public-case ranker is Resnik best-match
          average. It abstains when the best score is at or below zero. On the held-out split that ranker beats the
          degree baseline at k=1 and k=5.
        </p>
      </div>

      <details className="ed-details">
        <summary>Show every comparison line</summary>
        <ul className="mt-3 space-y-1 text-sm text-[var(--ed-fg-soft)]">
          {report.evidence.map((term) => (
            <li key={`${term.orphanet_id}-${term.hpo_id}-${term.relation}`} className="num">
              {term.orphanet_id} {term.hpo_id} {term.relation}. {term.source} {term.version}.
            </li>
          ))}
        </ul>
      </details>
    </section>
  );
}
