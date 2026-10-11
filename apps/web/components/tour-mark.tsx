"use client";

import { TOUR_STEPS } from "@/lib/tour";
import { useEffect, useLayoutEffect, useState } from "react";

type Box = { top: number; left: number; width: number; height: number };

export function TourMark({
  index,
  handsOnDone,
  onNext,
  onSkip,
}: {
  index: number;
  handsOnDone: boolean;
  onNext: () => void;
  onSkip: () => void;
}) {
  const step = TOUR_STEPS[index];
  const [box, setBox] = useState<Box | null>(null);
  const last = index === TOUR_STEPS.length - 1;
  const waiting = step?.handsOn === true && !handsOnDone;

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onSkip();
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onSkip]);

  useLayoutEffect(() => {
    if (!step) {
      return;
    }
    const node = document.querySelector(`[data-testid="${step.target}"]`);
    if (!(node instanceof HTMLElement)) {
      return;
    }
    const place = () => {
      const rect = node.getBoundingClientRect();
      setBox({ top: rect.top, left: rect.left, width: rect.width, height: rect.height });
    };
    place();
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    node.scrollIntoView({ block: "center", behavior: reduce ? "auto" : "smooth" });
    window.addEventListener("resize", place);
    window.addEventListener("scroll", place, true);
    return () => {
      window.removeEventListener("resize", place);
      window.removeEventListener("scroll", place, true);
    };
  }, [step]);

  if (!step) {
    return null;
  }

  const cardTop = box ? Math.min(box.top + box.height + 12, window.innerHeight - 220) : 16;
  const cardLeft = box ? Math.min(Math.max(16, box.left), window.innerWidth - 320) : 16;

  return (
    <div className="pointer-events-none fixed inset-0 z-40" data-testid="tour">
      {box ? (
        <div
          className="pointer-events-none fixed border-2 border-terracotta"
          style={{ top: box.top - 4, left: box.left - 4, width: box.width + 8, height: box.height + 8 }}
        />
      ) : null}
      <div
        role="dialog"
        aria-modal="false"
        aria-labelledby="tour-title"
        data-testid="tour-card"
        className="pointer-events-auto fixed w-72 space-y-2 border border-ink bg-parchment p-3 shadow-sm"
        style={{ top: cardTop, left: cardLeft }}
      >
        <p className="font-ui text-xs uppercase tracking-widest text-terracotta" data-testid="tour-step">
          {index + 1} of {TOUR_STEPS.length} · {step.kicker}
        </p>
        <h2 id="tour-title" className="font-display text-2xl">
          {step.title}
        </h2>
        <p className="text-sm">{step.body}</p>
        {waiting ? <p className="font-ui text-xs">Press Correct on a chip to continue.</p> : null}
        <div className="flex gap-2">
          <button type="button" className="font-ui text-sm underline" onClick={onSkip}>
            Skip
          </button>
          <button
            type="button"
            className="font-ui rounded-md bg-terracotta px-3 py-1 text-sm text-parchment disabled:opacity-40"
            disabled={waiting}
            onClick={onNext}
          >
            {last ? "Done" : "Next"}
          </button>
        </div>
      </div>
    </div>
  );
}
