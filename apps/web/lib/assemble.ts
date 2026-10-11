export type AssemblyStage = "read" | "map" | "match" | "rank";

export type AssemblyFrame = {
  stage: AssemblyStage;
  scanEnd: number;
  phrases: number;
  chips: number;
  columns: number;
  narrowed: boolean;
  bars: number;
  decide: boolean;
  ms: number;
};

export type NotePiece = {
  text: string;
  kind: "plain" | "mark" | "scan";
};

const SCAN_BUDGET = 24;
const SCAN_MS = 55;
const SCAN_WINDOW = 14;

export const PAGE_IMPACT =
  "This file opened with the page. The previous notebook asked for a name, Continue, and Load. Confirm is the decision that is still yours.";

export const CASE_IMPACT =
  "Name, Continue, and Load were 3 actions. This file opened on 1 click. Confirm is the decision that is still yours.";

export const NOTE_IMPACT =
  "You supplied the note. Read, Map, and Match are rules. Rank is a scoring model on this table. Confirm is the decision that is still yours.";

export type OpenedWith = "page" | "click" | "note";

export function stageKind(stage: AssemblyStage): "Rule" | "Scoring model" {
  switch (stage) {
    case "read":
    case "map":
    case "match":
      return "Rule";
    case "rank":
      return "Scoring model";
    default: {
      const leftover: never = stage;
      return leftover;
    }
  }
}

export function paceMs(units: number): number {
  if (units <= 3) {
    return 380;
  }
  if (units <= 6) {
    return 220;
  }
  return 120;
}

function frame(
  stage: AssemblyStage,
  noteLength: number,
  phrases: number,
  chips: number,
  columns: number,
  narrowed: boolean,
  bars: number,
  decide: boolean,
  ms: number,
): AssemblyFrame {
  return {
    stage,
    scanEnd: noteLength,
    phrases,
    chips,
    columns,
    narrowed,
    bars,
    decide,
    ms,
  };
}

export function assemblyFrames(input: {
  note: string;
  terms: Array<{ start: number; end: number }>;
  ranks: Array<{ bar: number }>;
}): AssemblyFrame[] {
  const note = input.note;
  const terms = [...input.terms].sort((left, right) => left.start - right.start);
  const positive = input.ranks.filter((rank) => rank.bar > 0).length;
  const pace = paceMs(Math.max(terms.length, positive, 1));
  const frames: AssemblyFrame[] = [];
  const step = Math.max(1, Math.ceil(Math.max(note.length, 1) / SCAN_BUDGET));
  let scanEnd = 0;
  const pushScan = (end: number) => {
    let phrases = 0;
    for (const term of terms) {
      if (term.end <= end) {
        phrases += 1;
      }
    }
    frames.push({
      stage: "read",
      scanEnd: end,
      phrases,
      chips: 0,
      columns: 0,
      narrowed: false,
      bars: 0,
      decide: false,
      ms: SCAN_MS,
    });
  };
  if (note.length === 0) {
    pushScan(0);
  } else {
    while (scanEnd < note.length) {
      scanEnd = Math.min(note.length, scanEnd + step);
      pushScan(scanEnd);
    }
  }
  const phraseCount = terms.length;
  if (phraseCount === 0) {
    frames.push(frame("map", note.length, 0, 0, 0, false, 0, false, pace));
    frames.push(frame("match", note.length, 0, 0, 0, false, 0, false, pace));
  } else {
    for (let chips = 1; chips <= phraseCount; chips += 1) {
      frames.push(frame("map", note.length, phraseCount, chips, 0, false, 0, false, pace));
    }
    for (let columns = 1; columns <= phraseCount; columns += 1) {
      frames.push(frame("match", note.length, phraseCount, phraseCount, columns, false, 0, false, pace));
    }
  }
  frames.push(frame("rank", note.length, phraseCount, phraseCount, phraseCount, true, 0, false, pace));
  for (let bars = 1; bars <= positive; bars += 1) {
    frames.push(frame("rank", note.length, phraseCount, phraseCount, phraseCount, true, bars, false, pace));
  }
  frames.push(frame("rank", note.length, phraseCount, phraseCount, phraseCount, true, positive, true, 0));
  return frames;
}

export function assemblyDuration(frames: AssemblyFrame[]): number {
  const decideAt = frames.findIndex((item) => item.decide);
  if (decideAt <= 0) {
    return 0;
  }
  return frames.slice(0, decideAt).reduce((sum, item) => sum + item.ms, 0);
}

export function notePieces(
  note: string,
  terms: Array<{ start: number; end: number }>,
  shown: number,
  scanEnd: number,
): NotePiece[] {
  const marked = Array.from({ length: note.length }, () => false);
  for (const term of terms.slice(0, shown)) {
    for (let index = term.start; index < term.end && index < note.length; index += 1) {
      marked[index] = true;
    }
  }
  const windowStart = Math.max(0, scanEnd - SCAN_WINDOW);
  const pieces: NotePiece[] = [];
  let index = 0;
  while (index < note.length) {
    const kind: NotePiece["kind"] = marked[index]
      ? "mark"
      : index >= windowStart && index < scanEnd
        ? "scan"
        : "plain";
    let next = index + 1;
    while (next < note.length) {
      const nextKind: NotePiece["kind"] = marked[next]
        ? "mark"
        : next >= windowStart && next < scanEnd
          ? "scan"
          : "plain";
      if (nextKind !== kind) {
        break;
      }
      next += 1;
    }
    pieces.push({ text: note.slice(index, next), kind });
    index = next;
  }
  return pieces;
}

export function impactLine(openedWith: OpenedWith): string {
  switch (openedWith) {
    case "page":
      return PAGE_IMPACT;
    case "click":
      return CASE_IMPACT;
    case "note":
      return NOTE_IMPACT;
    default: {
      const leftover: never = openedWith;
      return leftover;
    }
  }
}
