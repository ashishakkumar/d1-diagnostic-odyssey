import type { ComparisonReport } from "@/components/comparison-panel";

type Evidence = ComparisonReport["evidence"][number];

/**
 * A small evidence matrix: one row per catalogue entry, one column per symptom you confirmed.
 * Filled square = the entry fits that symptom. Open square = it does not fit, or the catalogue
 * does not list it. Shown instead of a score, so the reader can see why an entry leads.
 */
export function EvidenceGrid({
  evidence,
  termLabels = {},
  leadingId,
  maxRows = 6,
}: {
  evidence: Evidence[];
  termLabels?: Record<string, string>;
  leadingId?: string;
  maxRows?: number;
}) {
  const terms: string[] = [];
  const rows = new Map<string, Map<string, Evidence["relation"]>>();
  for (const item of evidence) {
    const id = item.orphanet_id ?? "unmapped";
    if (!terms.includes(item.hpo_id)) {
      terms.push(item.hpo_id);
    }
    if (!rows.has(id)) {
      rows.set(id, new Map());
    }
    rows.get(id)!.set(item.hpo_id, item.relation);
  }
  const ordered = [...rows.entries()]
    .map(([id, cells]) => ({
      id,
      cells,
      fits: terms.filter((t) => cells.get(t) !== "does_not_support").length,
    }))
    .sort((a, b) => (a.id === leadingId ? -1 : b.id === leadingId ? 1 : b.fits - a.fits));
  const shown = ordered.slice(0, maxRows);
  const hidden = ordered.length - shown.length;
  if (terms.length === 0 || shown.length === 0) {
    return null;
  }
  return (
    <figure data-testid="evidence-grid" className="ed-paper p-4 sm:p-6">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[18rem] border-collapse text-left text-[0.9375rem]">
          <caption className="sr-only">
            Which catalogue entries fit each symptom you confirmed
          </caption>
          <thead>
            <tr className="align-bottom">
              <th scope="col" className="pb-3 pr-4 font-mono-label font-normal">
                Catalogue entry
              </th>
              {terms.map((t) => (
                <th key={t} scope="col" className="pb-3 pr-4 text-[0.8125rem] font-normal leading-snug text-[var(--ed-fg)]">
                  <span className="block">{termLabels[t] ?? t}</span>
                  <span className="num block text-xs text-muted-foreground">{t}</span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {shown.map((row, index) => (
              <tr key={row.id} className="border-t border-border">
                <th scope="row" className="num py-2.5 pr-4 text-sm font-normal text-[var(--ed-fg)]">
                  {row.id}
                  {index === 0 && row.id === leadingId ? (
                    <span className="ml-2 border border-[var(--ed-accent)] px-1.5 py-px text-[0.625rem] uppercase tracking-[0.12em] text-[var(--ed-accent)]">
                      leads
                    </span>
                  ) : null}
                </th>
                {terms.map((t) => {
                  const fits = row.cells.get(t) !== "does_not_support";
                  return (
                    <td key={t} className="py-2.5 pr-4">
                      <span
                        role="img"
                        aria-label={fits ? "fits" : "does not fit or not listed"}
                        className="inline-block h-3.5 w-3.5 border"
                        style={{
                          borderColor: fits ? "var(--ed-accent)" : "var(--ed-fg-mute)",
                          background: fits ? "var(--ed-accent)" : "transparent",
                        }}
                      />
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <figcaption className="mt-4 flex flex-wrap items-center gap-x-6 gap-y-1 text-[0.8125rem] text-[var(--ed-fg-soft)]">
        <span className="inline-flex items-center gap-2">
          <span className="inline-block h-3 w-3 border border-[var(--ed-accent)] bg-[var(--ed-accent)]" aria-hidden />
          fits what you confirmed
        </span>
        <span className="inline-flex items-center gap-2">
          <span className="inline-block h-3 w-3 border border-[var(--ed-fg-mute)]" aria-hidden />
          does not fit, or the catalogue does not list it
        </span>
        {hidden > 0 ? <span className="text-muted-foreground">+{hidden} more entries, none fitting better</span> : null}
      </figcaption>
    </figure>
  );
}
