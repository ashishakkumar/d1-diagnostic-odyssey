const LINKS = [
  ["Timeline", "timeline"],
  ["Symptoms", "symptoms"],
  ["Lab variant", "variant"],
  ["Summary", "summary"],
] as const;

export function CaseNav({ caseId, current }: { caseId: string; current?: string }) {
  return (
    <nav aria-label="This case" className="border-b border-border">
      <ol className="flex flex-wrap items-baseline gap-x-7 gap-y-2 pb-3 font-[family-name:var(--font-label)] text-sm">
        <li>
          <a className="text-muted-foreground hover:text-[var(--ed-accent)]" href="/notebook">
            ← Cases
          </a>
        </li>
        {LINKS.map(([label, path], i) => {
          const active = current === path;
          return (
            <li key={path}>
              <a
                className={
                  active
                    ? "border-b-2 border-[var(--ed-accent)] pb-2.5 text-[var(--ed-fg)]"
                    : "text-[var(--ed-fg-soft)] hover:text-[var(--ed-accent)]"
                }
                aria-current={active ? "page" : undefined}
                href={`/cases/${caseId}/${path}`}
              >
                <span aria-hidden className="num mr-1.5 text-xs text-muted-foreground">
                  {i + 1}
                </span>
                {label}
              </a>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
