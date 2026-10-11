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
    <div className="space-y-6">
      <h1 className="text-2xl">Notebook</h1>
      <p>One case. Terms you confirm, a variant you type from a report, and a short page for a doctor.</p>
      {name ? (
        <p>Signed in as {name}.</p>
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
      <Button
        type="button"
        onClick={() => {
          window.location.assign(`/cases/${crypto.randomUUID()}/timeline`);
        }}
      >
        Open a synthetic case
      </Button>
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
        <p>Sign in to load a synthetic demo case.</p>
      )}
      <CaseList cases={cases} error={error} />
    </div>
  );
}
