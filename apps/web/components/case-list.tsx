export function CaseList({ cases, error }: { cases: string[]; error: string | null }) {
  if (error) {
    return <p>The notebook cannot reach the API.</p>;
  }
  if (cases.length === 0) {
    return <p>No synthetic case loaded.</p>;
  }
  return (
    <section aria-labelledby="open-cases" className="space-y-3">
      <h2 id="open-cases" className="font-mono-label">Cases already in this notebook</h2>
      <ul className="space-y-1.5">
        {cases.map((caseId) => (
          <li key={caseId}>
            <a
              className="num text-sm text-[var(--ed-fg-soft)] underline hover:text-[var(--ed-accent)]"
              href={`/cases/${caseId}/timeline`}
            >
              {caseId}
            </a>
          </li>
        ))}
      </ul>
    </section>
  );
}
