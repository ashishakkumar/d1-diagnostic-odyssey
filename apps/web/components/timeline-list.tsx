import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export type TimelineEvent = {
  at: string;
  kind: string;
  body: Record<string, unknown>;
};

function describe(event: TimelineEvent): string {
  const body = event.body;
  if (event.kind === "hpo_term") {
    const base = `${String(body.label)} (${String(body.hpo_id)}), marked ${String(body.presence)}.`;
    const explanation = body.explanation;
    if (typeof explanation === "string" && explanation) {
      return `${base} ${explanation}`;
    }
    return base;
  }
  if (event.kind === "lab_reported_variant") {
    const variation = body.variation as { expressions?: Array<{ value?: string }> } | undefined;
    const variant = variation?.expressions?.[0]?.value ?? "";
    const gene = String(body.gene_symbol);
    const dated = String(body.report_date);
    const words = String(body.lab_words);
    return `Gene ${gene}. Variant ${variant}. Report date ${dated}. The lab's words: ${words}.`;
  }
  return event.kind;
}

export function TimelineList({ events }: { events: TimelineEvent[] }) {
  if (events.length === 0) {
    return <p>Nothing has been accepted on this case yet.</p>;
  }
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>When</TableHead>
          <TableHead>What was accepted</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {events.map((event) => (
          <TableRow key={`${event.at}-${event.kind}-${describe(event)}`}>
            <TableCell>{event.at}</TableCell>
            <TableCell>{describe(event)}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
