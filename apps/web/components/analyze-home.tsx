"use client";

import { ANALYZE_TOUR } from "@/lib/tour";
import { useEffect, useLayoutEffect, useState } from "react";

type Candidate = { hpo_id: string; label: string; score: number; how: string };
type Finding = {
  phrase: string;
  present: boolean;
  onset: string | null;
  label: string | null;
  start: number | null;
  end: number | null;
  candidates: Candidate[];
  chosen: string | null;
  needs_review: boolean;
  source?: string;
};
type Evidence = { query: string; disease_term: string; disease_term_id: string; ic: number; exact: boolean };
type Rank = {
  disease_id: string;
  name: string;
  score: number;
  bar: number;
  evidence: Evidence[];
  against: string[];
  link: string;
};
type Separator = { hpo_id: string; label: string; seen_in: string[] };
type Stage = { id: string; label: string; actor: string; did: string; ms?: number };
type Result = {
  path: string;
  model: string | null;
  path_note: string | null;
  context: { age: unknown; sex: unknown; family_history: unknown; labs: string[] } | null;
  findings: Finding[];
  stages: Stage[];
  ranks: Rank[];
  abstained: boolean;
  reason: string | null;
  discriminators: Separator[];
  catalogue: { diseases: number; terms: number; hpo_version: string };
  attribution: string;
  disclaimer: string;
};
type Stop = { title: string; body: string; footer: string };

export const EXAMPLES: { title: string; note: string }[] = [
  { title: "Four symptoms", note: "seizures, hypotonia, intellectual disability, microcephaly" },
  {
    title: "Tall, long fingers",
    note: "16 year old, very tall with long fingers, lens dislocation in both eyes and a widened aortic root on echo. No learning problems. Father had a similar build.",
  },
  {
    title: "Plain words",
    note: "6 year old girl, fits since age 2, floppy as a baby, small head, slow to talk. No hearing problems. Brother has something similar. Microarray normal.",
  },
  {
    title: "Skin and joints",
    note: "Very stretchy skin, joints that dislocate easily, wide scars after small cuts, easy bruising. No eye problems.",
  },
];

const STAGE_IDS = ["extract", "map", "rank"];

function label(value: unknown): string | null {
  if (value === null || value === undefined || value === "") return null;
  return String(value);
}

export function AnalyzeHome() {
  const [note, setNote] = useState("");
  const [useAi, setUseAi] = useState(true);
  const [aiReady, setAiReady] = useState<boolean | null>(null);
  const [busy, setBusy] = useState(false);
  const [lit, setLit] = useState(0);
  const [result, setResult] = useState<Result | null>(null);
  const [stop, setStop] = useState<Stop | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tour, setTour] = useState<number | null>(null);

  useEffect(() => {
    fetch("/api/ai-status")
      .then((r) => r.json())
      .then((b: { available: boolean }) => setAiReady(b.available))
      .catch(() => setAiReady(false));
    if (new URLSearchParams(window.location.search).get("tour") === "1") setTour(0);
  }, []);

  useEffect(() => {
    if (!busy) return;
    setLit(1);
    const timer = window.setInterval(() => setLit((n) => (n < 2 ? n + 1 : n)), 900);
    return () => window.clearInterval(timer);
  }, [busy]);

  async function run(text: string) {
    setBusy(true);
    setError(null);
    setStop(null);
    setResult(null);
    try {
      const response = await fetch("/api/analyze", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ note: text, use_ai: useAi }),
      });
      const body = await response.json();
      if (response.status === 409) {
        setStop(body.detail as Stop);
      } else if (!response.ok) {
        setError(typeof body.detail === "string" ? body.detail : "The server could not read this note.");
      } else {
        setResult(body as Result);
        setLit(3);
        if (tour === 0) setTour(1);
      }
    } catch {
      setError("The app cannot reach the API.");
    } finally {
      setBusy(false);
    }
  }

  async function choose(index: number, hpoId: string | null) {
    if (!result) return;
    const findings = result.findings.map((f, i) =>
      i === index ? { ...f, chosen: hpoId, needs_review: false } : f,
    );
    const present = findings.filter((f) => f.chosen && f.present).map((f) => f.chosen as string);
    const absent = findings.filter((f) => f.chosen && !f.present).map((f) => f.chosen as string);
    setResult({ ...result, findings });
    const response = await fetch("/api/rerank", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ present, absent }),
    });
    if (response.ok) {
      const body = await response.json();
      setResult((prev) => (prev ? { ...prev, findings, ...body } : prev));
    }
  }

  const pathLine = result
    ? result.path === "rules"
      ? `Extraction: rules (HPO label and synonym matcher). ${result.path_note ?? ""}`
      : `Extraction: language model, ${result.model} via ${result.path === "gemini" ? "Google Gemini" : "OpenRouter"}.`
    : aiReady === false
      ? "No language model is configured on this server, so the rules matcher will run."
      : null;

  return (
    <div className="space-y-8">
      <section className="space-y-3" data-testid="note-box">
        <h1 className="font-display text-3xl">Which rare diseases fit these symptoms?</h1>
        <p className="text-sm text-muted-foreground">
          Paste notes or symptoms in plain words. The note is not stored. {useAi && aiReady
            ? "With AI extraction on, the text is sent to a hosted language model for this one request."
            : null}
        </p>
        <textarea
          className="min-h-36 w-full rounded-md border border-border bg-transparent p-3"
          aria-label="Clinical notes or symptoms"
          placeholder="e.g. 4 year old with seizures, low muscle tone, small head. No hearing loss."
          value={note}
          onChange={(e) => setNote(e.target.value)}
        />
        <div className="flex flex-wrap items-center gap-2">
          {EXAMPLES.map((ex) => (
            <button
              key={ex.title}
              type="button"
              className="font-ui rounded-full border border-border px-3 py-1 text-sm hover:border-terracotta"
              onClick={() => {
                setNote(ex.note);
                void run(ex.note);
              }}
            >
              {ex.title}
            </button>
          ))}
        </div>
        <div className="flex flex-wrap items-center gap-4">
          <button
            type="button"
            className="font-ui rounded-md bg-terracotta px-4 py-2 text-parchment disabled:opacity-40"
            disabled={busy || note.trim().length === 0}
            onClick={() => void run(note.trim())}
          >
            {busy ? "Reading…" : "Find conditions"}
          </button>
          <label className="font-ui flex items-center gap-2 text-sm">
            <input type="checkbox" checked={useAi} onChange={(e) => setUseAi(e.target.checked)} />
            AI extraction
          </label>
          <button type="button" className="font-ui text-sm underline" onClick={() => setTour(0)}>
            Take the tour
          </button>
        </div>
      </section>

      <ol className="font-ui grid grid-cols-3 gap-2 text-sm" aria-label="Steps">
        {STAGE_IDS.map((id, i) => {
          const stage = result?.stages.find((s) => s.id === id);
          const on = lit > i;
          return (
            <li
              key={id}
              className={`rounded-md border p-3 transition-colors ${on ? "border-terracotta" : "border-border opacity-60"}`}
            >
              <span className="block uppercase tracking-wide">{["Extract", "Map", "Rank"][i]}</span>
              <span className="block text-xs text-muted-foreground">
                {stage ? stage.actor : busy && on ? "working…" : "waiting"}
              </span>
              {stage ? <span className="mt-1 block text-xs">{stage.did}</span> : null}
            </li>
          );
        })}
      </ol>

      {pathLine ? (
        <p className="font-ui text-sm" data-testid="path">
          {pathLine}
        </p>
      ) : null}
      {error ? <p role="alert">{error}</p> : null}
      {stop ? (
        <section role="alert" className="rounded-md border-2 border-terracotta p-4">
          <h2 className="font-display text-xl">{stop.title}</h2>
          <p>{stop.body}</p>
          <p className="text-sm">{stop.footer}</p>
        </section>
      ) : null}

      {result ? (
        <>
          <section className="space-y-2" data-testid="findings">
            <h2 className="font-display text-xl">Findings</h2>
            <ul className="flex flex-wrap gap-2">
              {result.findings.map((f, i) => {
                const chosen = f.candidates.find((c) => c.hpo_id === f.chosen);
                return (
                  <li
                    key={`${f.phrase}-${i}`}
                    className={`rounded-md border px-3 py-2 text-sm ${f.needs_review ? "border-dashed border-terracotta" : "border-border"} ${f.present ? "" : "line-through decoration-terracotta"}`}
                  >
                    <span className="font-ui block text-xs text-muted-foreground">
                      “{f.phrase}” {f.present ? "" : "· absent"} {f.source === "rules" ? "· rules" : "· model"} {f.onset ? `· onset ${f.onset}` : ""}
                    </span>
                    {chosen ? (
                      <span>
                        {chosen.label} <span className="font-ui text-xs">{chosen.hpo_id}</span>
                      </span>
                    ) : null}
                    {f.needs_review || f.candidates.length > 1 ? (
                      <select
                        aria-label={`HPO term for ${f.phrase}`}
                        className="font-ui mt-1 block max-w-64 bg-transparent text-xs"
                        value={f.chosen ?? ""}
                        onChange={(e) => void choose(i, e.target.value || null)}
                      >
                        <option value="">{f.needs_review ? "Unsure: pick a term" : "Not used"}</option>
                        {f.candidates.map((c) => (
                          <option key={c.hpo_id} value={c.hpo_id}>
                            {c.label} ({c.how}, {c.score.toFixed(2)})
                          </option>
                        ))}
                      </select>
                    ) : null}
                  </li>
                );
              })}
            </ul>
            {result.context ? (
              <p className="font-ui text-xs text-muted-foreground">
                {[
                  label(result.context.age) && `Age ${label(result.context.age)}`,
                  label(result.context.sex),
                  label(result.context.family_history) && `Family: ${label(result.context.family_history)}`,
                  result.context.labs?.length ? `Results: ${result.context.labs.join("; ")}` : null,
                ]
                  .filter(Boolean)
                  .join(" · ")}
                {" "}(context is shown, not scored)
              </p>
            ) : null}
          </section>

          <section className="space-y-3" data-testid="results">
            <h2 className="font-display text-xl">Worth investigating</h2>
            {result.abstained ? (
              <p className="rounded-md bg-accent p-3 text-sm">
                {result.reason} This does not mean you are well. This is not a diagnosis.
              </p>
            ) : null}
            <ol className="space-y-3">
              {result.ranks.map((r, i) => (
                <li key={r.disease_id} className="border-b border-border pb-3">
                  <div className="flex items-baseline justify-between gap-3">
                    <a className="font-display text-lg underline-offset-2 hover:underline" href={r.link} target="_blank" rel="noreferrer">
                      {i + 1}. {r.name}
                    </a>
                    <span className="font-ui text-xs text-muted-foreground">
                      {r.disease_id} · {r.score.toFixed(2)}
                    </span>
                  </div>
                  <div className="mt-1 h-1 rounded bg-secondary">
                    <div className="h-1 rounded bg-terracotta" style={{ width: `${Math.max(r.bar, 0) * 100}%` }} />
                  </div>
                  <p className="mt-1 text-sm">
                    {r.evidence.map((e) => (e.exact ? e.query : `${e.query} → ${e.disease_term}`)).join(" · ") ||
                      "Only general matches."}
                  </p>
                  {r.against.length ? (
                    <p className="text-xs text-terracotta">Lists findings you marked absent: {r.against.join(", ")}</p>
                  ) : null}
                </li>
              ))}
            </ol>
          </section>

          <section className="space-y-2" data-testid="separate">
            <h2 className="font-display text-xl">What would best separate the top candidates</h2>
            <ul className="space-y-1 text-sm">
              {(result.discriminators ?? []).map((d) => (
                <li key={d.hpo_id}>
                  <span className="font-ui">{d.label}</span>{" "}
                  <span className="text-muted-foreground">listed for {d.seen_in.join(", ")}</span>
                </li>
              ))}
            </ul>
          </section>

          <footer className="space-y-1 text-xs text-muted-foreground">
            <p>{result.disclaimer}</p>
            <p>{result.attribution}</p>
          </footer>
        </>
      ) : null}

      {tour !== null ? <Tour index={tour} onNext={() => setTour(tour + 1 < ANALYZE_TOUR.length ? tour + 1 : null)} onSkip={() => setTour(null)} waiting={tour === 0 && !result} /> : null}
    </div>
  );
}

function Tour({ index, onNext, onSkip, waiting }: { index: number; onNext: () => void; onSkip: () => void; waiting: boolean }) {
  const step = ANALYZE_TOUR[index];
  const [top, setTop] = useState(0);
  useLayoutEffect(() => {
    const node = document.querySelector(`[data-testid="${step.target}"]`);
    if (node instanceof HTMLElement) {
      node.scrollIntoView({ block: "center" });
      const rect = node.getBoundingClientRect();
      setTop(Math.min(rect.bottom + 8, window.innerHeight - 200));
    }
  }, [step]);
  return (
    <div
      role="dialog"
      aria-label={`Tour: ${step.title}`}
      className="fixed left-1/2 z-50 w-[min(28rem,92vw)] -translate-x-1/2 rounded-md border border-terracotta bg-parchment p-4 shadow-lg"
      style={{ top }}
    >
      <p className="font-ui text-xs uppercase tracking-wide text-terracotta">
        {index + 1}/{ANALYZE_TOUR.length} · {step.kicker}
      </p>
      <h3 className="font-display text-lg">{step.title}</h3>
      <p className="text-sm">{step.body}</p>
      <div className="mt-3 flex gap-3">
        <button type="button" className="font-ui rounded-md bg-ink px-3 py-1 text-sm text-parchment disabled:opacity-40" disabled={waiting} onClick={onNext}>
          {waiting ? "Try it first" : index === ANALYZE_TOUR.length - 1 ? "Done" : "Next"}
        </button>
        <button type="button" className="font-ui text-sm underline" onClick={onSkip}>
          Skip
        </button>
      </div>
    </div>
  );
}
