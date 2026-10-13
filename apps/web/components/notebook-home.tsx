"use client";

import { WorkPipeline } from "@/components/work-pipeline";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

type DemoCase = {
  slug: string;
  title: string;
  blurb: string;
};

export function NotebookHome() {
  const params = useSearchParams();
  const chosen = params.get("slug");
  const slug = chosen ?? "separated";
  const [demos, setDemos] = useState<DemoCase[]>([]);
  const [note, setNote] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/demo/cases")
      .then(async (response) => {
        if (!response.ok) {
          throw new Error("down");
        }
        return (await response.json()) as { cases: DemoCase[] };
      })
      .then((body) => setDemos(body.cases))
      .catch(() => setError("The notebook cannot reach the API."));
  }, []);

  return (
    <div className="space-y-6">
      <details className="text-sm" data-testid="what-is-this">
        <summary className="cursor-pointer font-ui">What is this?</summary>
        <div className="mt-2 space-y-2" data-testid="what-is-this-body">
          <p>A synthetic case file. This is not a diagnosis.</p>
          <p>
            Read, Map, and Match are rules: a fixed lexicon, then a lookup on the ten-row synthetic
            table. No language model ran.
          </p>
          <p>
            Rank is Resnik best-match average, a scoring model on that table. It is not a language
            model, and it is not the 249-disease held-out run.
          </p>
          <p>Confirm is the only write. It goes through the approval gate.</p>
        </div>
      </details>
      <WorkPipeline
        slug={slug}
        note={null}
        openedWith={chosen ? "click" : "page"}
        showTour={slug === "separated"}
        startTour={params.get("tour") === "1"}
      />
      <details className="text-sm" data-testid="another-note">
        <summary className="cursor-pointer font-ui">Another synthetic note</summary>
        <div className="mt-3 space-y-3">
          <ul className="space-y-2">
            {demos.map((demo) => (
              <li key={demo.slug}>
                <a className="font-ui underline" href={`/examples?slug=${demo.slug}`}>
                  {demo.title}
                </a>
                <span className="mt-1 block text-muted-foreground">{demo.blurb}</span>
              </li>
            ))}
          </ul>
          <textarea
            className="min-h-24 w-full rounded-md border border-border bg-transparent p-3"
            aria-label="Synthetic note"
            value={note}
            onChange={(event) => setNote(event.target.value)}
          />
          <label className="block font-ui">
            Upload a text file
            <input
              className="mt-1 block"
              type="file"
              accept="text/plain,.txt"
              aria-label="Upload a synthetic note"
              onChange={(event) => {
                const file = event.target.files?.[0];
                if (!file) {
                  return;
                }
                void file.text().then((text) => {
                  sessionStorage.setItem("d1-note", text);
                  window.location.assign("/work");
                });
              }}
            />
          </label>
          <button
            type="button"
            className="font-ui rounded-md bg-terracotta px-4 py-2 text-parchment disabled:opacity-40"
            disabled={note.trim().length === 0}
            onClick={() => {
              sessionStorage.setItem("d1-note", note.trim());
              window.location.assign("/work");
            }}
          >
            Read this note
          </button>
          {error ? <p>{error}</p> : null}
        </div>
      </details>
    </div>
  );
}
