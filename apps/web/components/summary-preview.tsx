import { Button } from "@/components/ui/button";

export function SummaryPreview({ text, pdfHref }: { text: string; pdfHref: string }) {
  return (
    <article className="space-y-4">
      <pre className="whitespace-pre-wrap text-sm">{text}</pre>
      <Button asChild>
        <a href={pdfHref}>Download the one-to-two-page PDF</a>
      </Button>
    </article>
  );
}
