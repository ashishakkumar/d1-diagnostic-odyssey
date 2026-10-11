"use client";

import { useEffect, useMemo, useState } from "react";

type Term = {
  hpo_id: string;
  label: string;
  plain_words: string;
  quote: string;
  start: number;
  end: number;
};

type Rank = {
  orphanet_id: string;
  score: number;
  bar: number;
  reason: string;
};

type Cell = {
  orphanet_id: string;
  hpo_id: string;
  listed: boolean;
};

type Stage = {
  id: "read" | "map" | "match" | "rank";
  label: string;
  did: string;
};

export type PipelineResult = {
  note: string;
  case_id: string;
  method: string;
  stages: Stage[];
  terms: Term[];
  cells: Cell[];
  ranks: Rank[];
  abstained: boolean;
  abstain_text: string | null;
  questions: string[];
  limit_line: string | null;
  gene_line: string | null;
};

type StopScreen = {
  title: string;
  body: string;
  footer: string;
  matched: string[];
};

type Frame = {
  stage: Stage["id"];
  phrases: number;
  chips: number;
  columns: number;
  bars: number;
  decide: boolean;
};

const STAGE_ORDER: Stage["id"][] = ["read", "map", "match", "rank"];
const REVIEWER_LABEL = "synthetic-reader";

function framesFor(result: PipelineResult): Frame[] {
  const terms = result.terms.length;
  const frames: Frame[] = [];
  const push = (frame: Omit<Frame, "decide"> & { decide?: boolean }) => {
    frames.push({ decide: false, ...frame });
  };
  push({ stage: "read", phrases: 0, chips: 0, columns: 0, bars: 0 });
  for (let index = 1; index <= terms; index += 1) {
    push({ stage: "read", phrases: index, chips: 0, columns: 0, bars: 0 });
  }
  push({ stage: "map", phrases: terms, chips: 0, columns: 0, bars: 0 });
  for (let index = 1; index <= terms; index += 1) {
    push({ stage: "map", phrases: terms, chips: index, columns: 0, bars: 0 });
  }
  push({ stage: "match", phrases: terms, chips: terms, columns: 0, bars: 0 });
  for (let index = 1; index <= terms; index += 1) {
    push({ stage: "match", phrases: terms, chips: terms, columns: index, bars: 0 });
  }
  push({ stage: "rank", phrases: terms, chips: terms, columns: terms, bars: 0 });
  for (let index = 1; index <= result.ranks.length; index += 1) {
    push({ stage: "rank", phrases: terms, chips: terms, columns: terms, bars: index });
  }
  frames.push({
    stage: "rank",
    phrases: terms,
    chips: terms,
    columns: terms,
    bars: result.ranks.length,
    decide: true,
  });
  return frames;
}

function noteParts(note: string, terms: Term[], shown: number) {
  const active = terms.slice(0, shown);
  const parts: Array<{ text: string; hit: boolean }> = [];
  let cursor = 0;
  for (const term of active) {
    if (term.start > cursor) {
      parts.push({ text: note.slice(cursor, term.start), hit: false });
    }
    parts.push({ text: note.slice(term.start, term.end), hit: true });
    cursor = term.end;
  }
  if (cursor < note.length) {
    parts.push({ text: note.slice(cursor), hit: false });
  }
  return parts;
}

export function WorkPipeline({
  slug,
  note,
}: {
  slug: string | null;
  note: string | null;
}) {
  const [result, setResult] = useState<PipelineResult | null>(null);
  const [stop, setStop] = useState<StopScreen | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [frameIndex, setFrameIndex] = useState(0);
  const [dropped, setDropped] = useState<string[]>([]);
  const [recorded, setRecorded] = useState<string | null>(null);

  useEffect(() => {
    const payload = slug ? { slug } : { note };
    fetch("/api/pipeline", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(payload),
    })
      .then(async (response) => {
        if (response.status === 409) {
          const body = (await response.json()) as { detail: StopScreen };
          setStop(body.detail);
          return;
        }
        if (!response.ok) {
          throw new Error("down");
        }
        setResult((await response.json()) as PipelineResult);
      })
      .catch(() => setError("The notebook cannot reach the API."));
  }, [slug, note]);

  const frames = useMemo(() => (result ? framesFor(result) : []), [result]);
  const frame = frames[Math.min(frameIndex, Math.max(frames.length - 1, 0))];

  useEffect(() => {
    if (!result || frames.length === 0) {
      return;
    }
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setFrameIndex(frames.length - 1);
      return;
    }
    const timer = window.setInterval(() => {
      setFrameIndex((current) => (current + 1 >= frames.length ? current : current + 1));
    }, 140);
    return () => window.clearInterval(timer);
  }, [result, frames.length]);

  if (stop) {
    return (
      <section className="space-y-3" data-testid="stop">
        <p className="font-ui text-xs uppercase tracking-widest text-terracotta">Stopped</p>
        <h1 className="font-display text-4xl">{stop.title}</h1>
        <p>{stop.body}</p>
        <p>{stop.footer}</p>
      </section>
    );
  }
  if (error && !result) {
    return <p>{error}</p>;
  }
  if (!result || !frame) {
    return <p className="font-ui">Reading the note.</p>;
  }

  const stageNow = STAGE_ORDER.indexOf(frame.stage);
  const parts = noteParts(result.note, result.terms, frame.phrases);
  const kept = result.terms.filter((term) => !dropped.includes(term.hpo_id));
  const questions = result.questions.filter((_question, index) => {
    const term = result.terms[index];
    return term ? !dropped.includes(term.hpo_id) : false;
  });

  return (
    <div className="space-y-8" data-testid="pipeline">
      <header className="space-y-2">
        <p className="font-ui text-xs uppercase tracking-widest text-terracotta">Software at work</p>
        <h1 className="font-display text-4xl">One note, then the software reads it.</h1>
        <p className="text-sm" data-testid="method">
          {result.method}
        </p>
      </header>
      <ol className="grid gap-2 sm:grid-cols-4">
        {result.stages.map((stage, index) => (
          <li
            key={stage.id}
            data-testid={`stage-${stage.id}`}
            className={`rounded-md border px-3 py-2 ${
              index <= stageNow ? "border-terracotta" : "border-border opacity-50"
            }`}
          >
            <p className="font-ui text-xs uppercase tracking-widest">{stage.label}</p>
            <p className="text-xs" data-testid="actor-software">
              Software, not a person.
            </p>
          </li>
        ))}
      </ol>
      <section className="space-y-2" data-testid="stage-detail">
        <h2 className="font-display text-2xl">{result.stages[stageNow]?.label}</h2>
        <p>{result.stages[stageNow]?.did}</p>
      </section>
      <section className="space-y-3" data-testid="note">
        <p className="leading-7">
          {parts.map((part, index) =>
            part.hit ? (
              <mark key={`${part.text}-${index}`} className="bg-terracotta/20 px-0.5">
                {part.text}
              </mark>
            ) : (
              <span key={`${part.text}-${index}`}>{part.text}</span>
            ),
          )}
        </p>
      </section>
      {frame.chips > 0 ? (
        <ul className="flex flex-wrap gap-2" data-testid="chips">
          {result.terms.slice(0, frame.chips).map((term) => {
            const gone = dropped.includes(term.hpo_id);
            return (
              <li key={term.hpo_id} className="rounded-md border border-border px-3 py-2 text-sm">
                <p className={gone ? "line-through" : ""}>
                  {term.label} {term.hpo_id}
                </p>
                <p className="text-xs text-muted-foreground">Quote: {term.quote}</p>
                {frame.decide && recorded === null ? (
                  <button
                    type="button"
                    className="font-ui text-xs text-terracotta"
                    onClick={() =>
                      setDropped((current) =>
                        current.includes(term.hpo_id)
                          ? current.filter((item) => item !== term.hpo_id)
                          : [...current, term.hpo_id],
                      )
                    }
                  >
                    {gone ? "Restore" : "Correct"}
                  </button>
                ) : null}
              </li>
            );
          })}
        </ul>
      ) : null}
      {frame.columns > 0 && result.terms.length > 0 ? (
        <div className="overflow-x-auto" data-testid="match-grid">
          <table className="w-full border-collapse text-left text-sm">
            <thead>
              <tr>
                <th className="p-1 font-ui text-xs">Row</th>
                {result.terms.slice(0, frame.columns).map((term) => (
                  <th key={term.hpo_id} className="p-1 font-ui text-xs">
                    {term.hpo_id}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {result.ranks.map((rank) => (
                <tr key={rank.orphanet_id}>
                  <td className="p-1 font-ui text-xs">{rank.orphanet_id}</td>
                  {result.terms.slice(0, frame.columns).map((term) => {
                    const cell = result.cells.find(
                      (item) => item.orphanet_id === rank.orphanet_id && item.hpo_id === term.hpo_id,
                    );
                    return (
                      <td key={term.hpo_id} className="p-1">
                        <span
                          className={`inline-block h-4 w-4 rounded-sm ${
                            cell?.listed ? "bg-terracotta" : "bg-border"
                          }`}
                        />
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
      {frame.bars > 0 ? (
        <ol className="space-y-3" data-testid="ranks">
          {result.ranks.slice(0, frame.bars).map((rank) => (
            <li key={rank.orphanet_id}>
              <p className="font-ui text-sm">{rank.orphanet_id}</p>
              <div className="h-2 w-full rounded-full bg-border">
                <div
                  className="h-2 rounded-full bg-terracotta"
                  style={{ width: `${Math.round(rank.bar * 100)}%` }}
                />
              </div>
              <p className="text-sm">{rank.reason}</p>
            </li>
          ))}
        </ol>
      ) : null}
      {frame.decide && result.abstained && result.abstain_text ? (
        <p data-testid="abstain">{result.abstain_text}</p>
      ) : null}
      {frame.decide && result.gene_line ? <p>{result.gene_line}</p> : null}
      {frame.decide && result.limit_line ? <p>{result.limit_line}</p> : null}
      {frame.decide ? (
        <section className="space-y-3 border-t border-border pt-4" data-testid="decision">
          <p className="font-ui text-xs uppercase tracking-widest text-terracotta" data-testid="actor-person">
            You decide
          </p>
          <h2 className="font-display text-2xl">Confirm or correct</h2>
          <p>The software stopped. Confirm the chips, or correct one first. One click records them.</p>
          <ul className="space-y-2 text-sm" data-testid="questions">
            {questions.map((question) => (
              <li key={question}>{question}</li>
            ))}
          </ul>
          {error ? <p>{error}</p> : null}
          {recorded ? (
            <p data-testid="recorded">
              Recorded through the approval gate. Reviewer {recorded}. This is not a diagnosis.
            </p>
          ) : (
            <button
              type="button"
              className="font-ui rounded-md bg-terracotta px-4 py-2 text-parchment disabled:opacity-40"
              disabled={kept.length === 0}
              onClick={() => {
                void fetch("/api/pipeline/confirm", {
                  method: "POST",
                  headers: { "content-type": "application/json" },
                  body: JSON.stringify({
                    case_id: result.case_id,
                    terms: kept.map((term) => ({ hpo_id: term.hpo_id, label: term.label })),
                  }),
                })
                  .then(async (response) => {
                    if (!response.ok) {
                      setError("The notebook cannot reach the API.");
                      return;
                    }
                    const body = (await response.json()) as { reviewer?: string };
                    setRecorded(body.reviewer ?? REVIEWER_LABEL);
                  })
                  .catch(() => setError("The notebook cannot reach the API."));
              }}
            >
              Confirm these terms
            </button>
          )}
        </section>
      ) : null}
    </div>
  );
}
