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

export function ComparisonPanel({ report }: { report: ComparisonReport }) {
  const first = report.evidence[0];
  return (
    <section className="space-y-2 rounded-md border border-border p-4" data-testid="comparison">
      <h2 className="text-lg">Catalogue comparison</h2>
      <p>This is not a diagnosis. The reported variant is not an input.</p>
      {report.abstained ? (
        <p>No row is separated from the others. This does not mean you are well.</p>
      ) : (
        <p>
          First row {report.leading_orphanet_id}. Source {first?.source} {first?.version}.
        </p>
      )}
      {report.margin_reason === "runner_up_ratio_is_zero" ? (
        <p>The next row has a ratio of zero. The margin is not a finite number.</p>
      ) : null}
      {report.margin_fact ? <p>{report.margin_fact}</p> : null}
      {report.margin != null && !report.abstained ? (
        <p>Margin {report.margin.toFixed(3)}.</p>
      ) : null}
      <ul className="space-y-1 text-sm">
        {report.evidence.map((term) => (
          <li key={`${term.orphanet_id}-${term.hpo_id}-${term.relation}`}>
            {term.orphanet_id} {term.hpo_id} {term.relation}. {term.source} {term.version}.
          </li>
        ))}
      </ul>
    </section>
  );
}
