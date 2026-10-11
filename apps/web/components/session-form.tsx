import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function SessionForm({ onSubmit }: { onSubmit: (name: string) => void }) {
  return (
    <form
      className="max-w-sm space-y-4"
      onSubmit={(event) => {
        event.preventDefault();
        const data = new FormData(event.currentTarget);
        onSubmit(String(data.get("name") ?? "").trim());
      }}
    >
      <label className="block space-y-1 font-[family-name:var(--font-label)] text-sm" htmlFor="session-name">
        Your name for this notebook
        <Input id="session-name" name="name" required autoComplete="nickname" />
      </label>
      <Button type="submit">Continue</Button>
    </form>
  );
}
