import type { DemoCaseOut } from "@/src/index";

export type DemoCase = DemoCaseOut;

export function DemoList({
  cases,
  onLoad,
}: {
  cases: DemoCase[];
  onLoad: (slug: string) => void;
}) {
  if (cases.length === 0) {
    return <p>No synthetic demo case is listed.</p>;
  }
  return (
    <section aria-labelledby="demo-cases" className="space-y-3">
      <h2 id="demo-cases" className="font-mono-label">Synthetic demo cases</h2>
      <ul className="divide-y divide-[var(--ed-line)] border-y border-border">
        {cases.map((item) => (
          <li key={item.slug} className="py-4">
            <button
              type="button"
              className="font-display text-xl italic text-[var(--ed-fg)] underline decoration-[var(--ed-line)] underline-offset-4 hover:text-[var(--ed-accent)] hover:decoration-[var(--ed-accent)]"
              onClick={() => onLoad(item.slug)}
            >
              Load {item.title}
            </button>
            <p className="mt-1 text-[0.9375rem] text-muted-foreground">{item.blurb}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}
