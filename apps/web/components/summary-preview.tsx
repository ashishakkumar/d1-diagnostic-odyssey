import { Button } from "@/components/ui/button";

export function SummaryPreview({ text, pdfHref }: { text: string; pdfHref: string }) {
  return (
    <article className="space-y-5">
      <div>
        <p className="font-mono-label">The page you would hand over</p>
        <h2 className="font-display mt-1 text-2xl italic">The page itself</h2>
      </div>
      <pre className="ed-paper max-w-[70ch] whitespace-pre-wrap p-5 font-[family-name:var(--font-body)] text-[0.9375rem] leading-relaxed text-[var(--ed-fg)] sm:p-7">
        {text}
      </pre>
      <Button asChild>
        <a href={pdfHref}>Download the one-to-two-page PDF</a>
      </Button>
    </article>
  );
}
