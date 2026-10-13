export function CaseList({ cases, error }: { cases: string[]; error: string | null }) {
  if (error) {
    return <p>The notebook cannot reach the API.</p>;
  }
  if (cases.length === 0) {
    return <p>No synthetic case loaded.</p>;
  }
  return (
    <ul className="space-y-2">
      {cases.map((caseId) => (
        <li key={caseId}>
          <a className="underline" href={`/cases/${caseId}/timeline`}>
            {caseId}
          </a>
        </li>
      ))}
    </ul>
  );
}
