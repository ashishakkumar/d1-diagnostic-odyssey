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
    <ul className="space-y-3">
      {cases.map((item) => (
        <li key={item.slug} className="space-y-1">
          <button type="button" className="underline" onClick={() => onLoad(item.slug)}>
            Load {item.title}
          </button>
          <p className="text-sm text-muted-foreground">{item.blurb}</p>
        </li>
      ))}
    </ul>
  );
}
