"use client";

import { TourMark } from "@/components/tour-mark";
import {
  type AssemblyFrame,
  type AssemblyStage,
  type OpenedWith,
  assemblyFrames,
  impactLine,
  notePieces,
  stageKind,
} from "@/lib/assemble";
import { TOUR_STEPS } from "@/lib/tour";
import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";

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
  id: AssemblyStage;
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

const STAGE_ORDER: AssemblyStage[] = ["read", "map", "match", "rank"];
const REVIEWER_LABEL = "synthetic-reader";

function youDecideText(stage: AssemblyStage, decide: boolean): string {
  if (decide) {
    return "Confirm these chips, or correct one.";
  }
  switch (stage) {
    case "read":
    case "map":
    case "match":
    case "rank":
      return "Nothing on this stage.";
    default: {
      const leftover: never = stage;
      return leftover;
    }
  }
}

function reducedMotion(): boolean {
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export function WorkPipeline({
  slug,
  note,
  openedWith,
  showTour = false,
  startTour = false,
}: {
  slug: string | null;
  note: string | null;
  openedWith?: OpenedWith;
  showTour?: boolean;
  startTour?: boolean;
}) {
  const [result, setResult] = useState<PipelineResult | null>(null);
  const [stop, setStop] = useState<StopScreen | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [frameIndex, setFrameIndex] = useState(0);
  const [dropped, setDropped] = useState<string[]>([]);
  const [recorded, setRecorded] = useState<string | null>(null);
  const [tourIndex, setTourIndex] = useState<number | null>(null);
  const [tourArmed, setTourArmed] = useState(false);
  const [handsOnDone, setHandsOnDone] = useState(false);
  const how: OpenedWith = openedWith ?? (slug ? "click" : "note");
  const markRefs = useRef<Record<string, HTMLElement | null>>({});
  const chipRefs = useRef<Record<string, HTMLElement | null>>({});

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

  const frames = useMemo(() => (result ? assemblyFrames(result) : []), [result]);
  const frame: AssemblyFrame | undefined = frames[Math.min(frameIndex, Math.max(frames.length - 1, 0))];

  useEffect(() => {
    if (frames.length === 0) {
      return;
    }
    if (reducedMotion()) {
      setFrameIndex(frames.length - 1);
      return;
    }
    setFrameIndex(0);
    let index = 0;
    let timer = window.setTimeout(function advance() {
      index += 1;
      if (index >= frames.length) {
        return;
      }
      setFrameIndex(index);
      timer = window.setTimeout(advance, frames[index]?.ms ?? 0);
    }, frames[0]?.ms ?? 0);
    return () => window.clearTimeout(timer);
  }, [frames]);

  useEffect(() => {
    if (!showTour || !frame?.decide) {
      return;
    }
    if (startTour || tourArmed) {
      setTourIndex(0);
      setTourArmed(false);
      return;
    }
    try {
      if (window.localStorage.getItem("d1-tour-seen") === "1") {
        return;
      }
    } catch {
      return;
    }
    setTourIndex(0);
  }, [showTour, frame?.decide, startTour, tourArmed]);

  function closeTour() {
    try {
      window.localStorage.setItem("d1-tour-seen", "1");
    } catch {
      // The tour still closes when storage is blocked.
    }
    setTourIndex(null);
  }

  function nextTour() {
    if (tourIndex === null) {
      return;
    }
    if (tourIndex + 1 >= TOUR_STEPS.length) {
      closeTour();
      return;
    }
    setTourIndex(tourIndex + 1);
  }

  useLayoutEffect(() => {
    if (!result || !frame || frame.stage !== "map" || frame.chips === 0 || reducedMotion()) {
      return;
    }
    const term = result.terms[frame.chips - 1];
    const from = term ? markRefs.current[term.hpo_id] : null;
    const to = term ? chipRefs.current[term.hpo_id] : null;
    if (!from || !to) {
      return;
    }
    const origin = from.getBoundingClientRect();
    const destination = to.getBoundingClientRect();
    const dx = origin.left - destination.left;
    const dy = origin.top - destination.top;
    to.style.transition = "none";
    to.style.transform = `translate(${dx}px, ${dy}px)`;
    const motion = window.requestAnimationFrame(() => {
      to.style.transition = "transform 360ms ease";
      to.style.transform = "translate(0px, 0px)";
    });
    return () => window.cancelAnimationFrame(motion);
  }, [frame, result]);

  if (stop) {
    return (
      <section className="space-y-3 border border-terracotta px-4 py-6" data-testid="stop">
        <p className="font-ui text-xs uppercase tracking-widest text-terracotta">Stopped</p>
        <h1 className="font-display text-5xl">{stop.title}</h1>
        <p>The read did not continue. Nothing was saved.</p>
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
  const stageCopy = result.stages[stageNow];
  const parts = notePieces(result.note, result.terms, frame.phrases, frame.scanEnd);
  const kept = result.terms.filter((term) => !dropped.includes(term.hpo_id));
  const questions = result.questions.filter((_question, index) => {
    const term = result.terms[index];
    return term ? !dropped.includes(term.hpo_id) : false;
  });
  const positive = result.ranks.filter((rank) => rank.bar > 0);
  const mapRows =
    frame.narrowed && positive.length > 0 ? positive : result.ranks;
  const shownBars = positive.slice(0, frame.bars);

  return (
    <article className="space-y-6" data-testid="pipeline">
      <header className="space-y-2 border-l-2 border-terracotta pl-4">
        <p className="font-ui text-xs uppercase tracking-widest text-terracotta">Case file</p>
        <h1 className="font-display text-4xl leading-tight">The file is assembling.</h1>
        <p className="font-ui text-xs text-muted-foreground">{result.case_id}</p>
        <p className="text-sm" data-testid="method">
          {result.method}
        </p>
        <button
          type="button"
          data-testid="take-tour"
          className="font-ui text-sm underline"
          onClick={() => {
            if (!showTour) {
              window.location.assign("/?tour=1");
              return;
            }
            setHandsOnDone(false);
            if (frame.decide) {
              setTourIndex(0);
            } else {
              setTourArmed(true);
            }
          }}
        >
          Take the tour
        </button>
      </header>
      <ol className="grid gap-2 sm:grid-cols-4">
        {result.stages.map((stage, index) => (
          <li
            key={stage.id}
            data-testid={`stage-${stage.id}`}
            className={`rounded-md border px-3 py-2 ${
              index <= stageNow ? "border-terracotta" : "border-border opacity-40"
            }`}
          >
            <p className="font-ui text-xs uppercase tracking-widest">{stage.label}</p>
            <p className="text-xs">{stageKind(stage.id)}</p>
            <p className="text-xs" data-testid="actor-software">
              Software, not a person.
            </p>
          </li>
        ))}
      </ol>
      <section className="space-y-2" data-testid="stage-caption" aria-live="polite">
        <p className="font-ui text-xs uppercase tracking-widest text-terracotta">
          {stageCopy?.label} · {stageKind(frame.stage)}
        </p>
        <h2 className="font-display text-2xl">What the software did</h2>
        <p data-testid="stage-detail">{stageCopy?.did}</p>
        <h2 className="font-display text-2xl">What you decide</h2>
        <p>{youDecideText(frame.stage, frame.decide)}</p>
      </section>
      <div className="grid gap-6 md:grid-cols-[minmax(0,1.4fr)_minmax(16rem,0.8fr)]">
        <section className="space-y-2" data-testid="note">
          <h2 className="font-ui text-xs uppercase tracking-widest">Note</h2>
          <p className="leading-7">
            {parts.map((part, index) => {
              const marked = part.kind === "mark" ? result.terms.find((term) => term.quote === part.text) : undefined;
              if (part.kind === "mark") {
                return (
                  <mark
                    key={`${part.kind}-${index}`}
                    ref={(node) => {
                      if (marked) {
                        markRefs.current[marked.hpo_id] = node;
                      }
                    }}
                    className="px-0.5"
                  >
                    {part.text}
                  </mark>
                );
              }
              return (
                <span key={`${part.kind}-${index}`} className={part.kind === "scan" ? "scan-window" : undefined}>
                  {part.text}
                </span>
              );
            })}
          </p>
        </section>
        <section className="space-y-2" data-testid="symptom-column">
          <h2 className="font-ui text-xs uppercase tracking-widest">Symptoms</h2>
          {frame.chips === 0 ? <p className="text-sm text-muted-foreground">Phrases land here.</p> : null}
          <ul className="space-y-2" data-testid="chips">
            {result.terms.slice(0, frame.chips).map((term) => {
              const gone = dropped.includes(term.hpo_id);
              return (
                <li
                  key={term.hpo_id}
                  ref={(node) => {
                    chipRefs.current[term.hpo_id] = node;
                  }}
                  className="rounded-md border border-border bg-background px-3 py-2 text-sm"
                >
                  <p className={gone ? "line-through" : ""}>
                    {term.label} {term.hpo_id}
                  </p>
                  <p className="text-xs text-muted-foreground">Quote: {term.quote}</p>
                  {frame.decide && recorded === null ? (
                    <button
                      type="button"
                      className="font-ui text-xs text-terracotta"
                    onClick={() => {
                      setHandsOnDone(true);
                      setDropped((current) =>
                        current.includes(term.hpo_id)
                          ? current.filter((item) => item !== term.hpo_id)
                          : [...current, term.hpo_id],
                      );
                    }}
                    >
                      {gone ? "Restore" : "Correct"}
                    </button>
                  ) : null}
                </li>
              );
            })}
          </ul>
        </section>
      </div>
      {frame.columns > 0 && result.terms.length > 0 ? (
        <section className="space-y-2" data-testid="match-grid">
          <h2 className="font-ui text-xs uppercase tracking-widest">Condition map</h2>
          <div className="overflow-x-auto">
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
                {mapRows.map((rank) => (
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
                              cell?.listed ? "bg-terracotta" : "border border-border"
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
        </section>
      ) : null}
      {shownBars.length > 0 ? (
        <ol className="space-y-3" data-testid="ranks">
          {shownBars.map((rank) => (
            <li key={rank.orphanet_id}>
              <p className="font-ui text-sm">{rank.orphanet_id}</p>
              <div className="h-2 w-full rounded-full bg-border">
                <div
                  className="evidence-bar h-2 rounded-full bg-terracotta"
                  style={{ width: `${Math.round(rank.bar * 100)}%` }}
                />
              </div>
              <p className="text-sm">{rank.reason}</p>
            </li>
          ))}
        </ol>
      ) : null}
      {frame.narrowed && result.abstained && result.abstain_text ? (
        <section className="space-y-2 border border-ink px-4 py-3" data-testid="abstain">
          <p className="font-ui text-xs uppercase tracking-widest">Abstain</p>
          <p>{result.abstain_text}</p>
        </section>
      ) : null}
      {frame.decide && result.gene_line ? <p>{result.gene_line}</p> : null}
      {frame.decide && result.limit_line ? <p>{result.limit_line}</p> : null}
      {frame.decide ? (
        <p data-testid="impact">{impactLine(how)}</p>
      ) : null}
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
      {tourIndex !== null ? (
        <TourMark
          index={tourIndex}
          handsOnDone={handsOnDone}
          onNext={nextTour}
          onSkip={closeTour}
        />
      ) : null}
    </article>
  );
}
