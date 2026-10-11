"use client";

import { useEffect, useState } from "react";

type DemoCase = {
  slug: string;
  title: string;
  blurb: string;
};

export default function HomePage() {
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
    <div className="space-y-8">
      <header className="space-y-3">
        <p className="font-ui text-xs uppercase tracking-widest text-terracotta">Synthetic notebook</p>
        <h1 className="font-display text-5xl leading-tight">Pick a note. The software does the rest.</h1>
        <p>
          One click starts the file. No sign-in, no blank notebook, no symptom form. This is not a
          diagnosis.
        </p>
      </header>
      <section className="space-y-3">
        <h2 className="font-display text-2xl">A synthetic case</h2>
        <ul className="space-y-2">
          {demos.map((demo) => (
            <li key={demo.slug}>
              <a
                className="block rounded-md border border-border px-4 py-3 hover:border-terracotta"
                href={`/work?slug=${demo.slug}`}
              >
                <span className="font-ui">{demo.title}</span>
                <span className="mt-1 block text-sm text-muted-foreground">{demo.blurb}</span>
              </a>
            </li>
          ))}
        </ul>
      </section>
      <section className="space-y-3">
        <h2 className="font-display text-2xl">Or paste a short synthetic note</h2>
        <textarea
          className="min-h-32 w-full rounded-md border border-border bg-transparent p-3"
          aria-label="Synthetic note"
          value={note}
          onChange={(event) => setNote(event.target.value)}
        />
        <label className="block font-ui text-sm">
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
      </section>
      {error ? <p>{error}</p> : null}
    </div>
  );
}
