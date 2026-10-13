import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export type VariantFields = {
  gene_symbol: string;
  variant: string;
  lab_words: string;
  report_date: string;
};

export function VariantForm({ onSubmit }: { onSubmit: (fields: VariantFields) => void }) {
  return (
    <form
      className="space-y-3"
      onSubmit={(event) => {
        event.preventDefault();
        const data = new FormData(event.currentTarget);
        onSubmit({
          gene_symbol: String(data.get("gene_symbol") ?? "").trim(),
          variant: String(data.get("variant") ?? "").trim(),
          lab_words: String(data.get("lab_words") ?? "").trim(),
          report_date: String(data.get("report_date") ?? ""),
        });
      }}
    >
      <p>Copy the words from the report. This notebook does not classify the variant.</p>
      <label className="block space-y-1 text-sm" htmlFor="gene-symbol">
        Gene, as written on the report
        <Input id="gene-symbol" name="gene_symbol" required />
      </label>
      <label className="block space-y-1 text-sm" htmlFor="variant-text">
        Variant, as written on the report
        <Input id="variant-text" name="variant" required />
      </label>
      <label className="block space-y-1 text-sm" htmlFor="lab-words">
        The lab&apos;s own words
        <Input id="lab-words" name="lab_words" required />
      </label>
      <label className="block space-y-1 text-sm" htmlFor="report-date">
        Report date
        <Input id="report-date" name="report_date" type="date" required />
      </label>
      <Button type="submit">Save what I typed</Button>
    </form>
  );
}
