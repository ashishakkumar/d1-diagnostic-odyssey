import Link from "next/link";

export function SiteHeader() {
  return (
    <header className="border-b border-border">
      <div className="ed-shell flex flex-wrap items-baseline justify-between gap-x-6 gap-y-2 py-4">
        <Link href="/" className="font-display text-xl italic text-[var(--ed-fg)] no-underline">
          Diagnostic Odyssey
        </Link>
        <nav aria-label="Site" className="flex items-baseline gap-6 font-[family-name:var(--font-label)] text-sm">
          <Link href="/#how" className="text-[var(--ed-fg-soft)] hover:text-[var(--ed-accent)]">
            How it works
          </Link>
          <Link href="/#limits" className="text-[var(--ed-fg-soft)] hover:text-[var(--ed-accent)]">
            Limits
          </Link>
          <Link
            href="/notebook"
            className="border border-[var(--ed-accent)] px-3 py-1 text-[var(--ed-accent)] hover:bg-[var(--ed-accent)] hover:text-[var(--ed-on-accent)]"
          >
            Open the notebook
          </Link>
        </nav>
      </div>
    </header>
  );
}
