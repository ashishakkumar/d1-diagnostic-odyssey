const LINKS = [
  ["Timeline", "timeline"],
  ["Symptoms", "symptoms"],
  ["Lab variant", "variant"],
  ["Summary", "summary"],
] as const;

export function CaseNav({ caseId }: { caseId: string }) {
  return (
    <nav className="flex flex-wrap gap-3 text-sm">
      <a className="underline" href="/">
        Cases
      </a>
      {LINKS.map(([label, path]) => (
        <a key={path} className="underline" href={`/cases/${caseId}/${path}`}>
          {label}
        </a>
      ))}
    </nav>
  );
}
