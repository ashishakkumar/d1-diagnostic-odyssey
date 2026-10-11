"use client";

import { CaseList } from "@/components/case-list";
import { DemoList, type DemoCase } from "@/components/demo-list";
import { SessionForm } from "@/components/session-form";
import { Button } from "@/components/ui/button";
import { useEffect, useState } from "react";

export default function HomePage() {
  const [cases, setCases] = useState<string[]>([]);
  const [demos, setDemos] = useState<DemoCase[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/cases")
      .then(async (response) => {
        if (!response.ok) {
          throw new Error("down");
        }
        return (await response.json()) as { cases: string[] };
      })
      .then((body) => setCases(body.cases))
      .catch(() => setError("down"));
    fetch("/api/demo/cases")
      .then(async (response) => {
        if (!response.ok) {
          return;
        }
        const body = (await response.json()) as { cases: DemoCase[] };
        setDemos(body.cases);
      })
      .catch(() => setError("down"));
    fetch("/api/session", { credentials: "include" })
      .then(async (response) => {
        if (!response.ok) {
          return;
        }
        const body = (await response.json()) as { name: string };
        setName(body.name);
      })
      .catch(() => setError("down"));
  }, []);

  return (
    <div className="ed-shell max-w-3xl space-y-8 py-12 md:py-16">
      <header className="space-y-3">
        <p className="font-mono-label">The notebook</p>
        <h1 className="font-display text-4xl italic leading-tight md:text-5xl">Notebook</h1>
        <p className="deck max-w-[52ch]">
          One case. Terms you confirm, a variant you type from a report, and a short page for a doctor. Everything here
          is synthetic.
        </p>
        <p className="text-sm text-muted-foreground">
          New here? <a className="underline hover:text-[var(--ed-accent)]" href="/">Read what this is first.</a>
        </p>
      </header>
      {name ? (
        <p className="font-[family-name:var(--font-label)] text-sm">Signed in as {name}.</p>
      ) : (
        <SessionForm
          onSubmit={async (typed) => {
            const response = await fetch("/api/session", {
              method: "POST",
              credentials: "include",
              headers: { "content-type": "application/json" },
              body: JSON.stringify({ name: typed }),
            });
            if (response.ok) {
              setName(typed);
            }
          }}
        />
      )}
      <div>
        <Button
          type="button"
          variant="outline"
          onClick={() => {
            window.location.assign(`/cases/${crypto.randomUUID()}/timeline`);
          }}
        >
          Open a synthetic case
        </Button>
      </div>
      {name ? (
        <DemoList
          cases={demos}
          onLoad={async (slug) => {
            const response = await fetch(`/api/demo/cases/${slug}/load`, {
              method: "POST",
              credentials: "include",
            });
            if (!response.ok) {
              setError("down");
              return;
            }
            const body = (await response.json()) as { case_id: string };
            window.location.assign(`/cases/${body.case_id}/summary`);
          }}
        />
      ) : (
        <p className="text-[var(--ed-fg-soft)]">Sign in to load a synthetic demo case.</p>
      )}
      <CaseList cases={cases} error={error} />
    </div>
  );
}
