import { WorkPipeline } from "../../apps/web/components/work-pipeline.tsx";
import { assemblyDuration, assemblyFrames, notePieces } from "../../apps/web/lib/assemble.ts";
import { render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";

const SEPARATED_NOTE =
  "Synthetic note, not a real patient. The hands show long fingers. The face shows flat cheeks.";

test("a case file stays under ten seconds and still moves", () => {
  const longFingers = SEPARATED_NOTE.indexOf("long fingers");
  const flatCheeks = SEPARATED_NOTE.indexOf("flat cheeks");
  const separated = assemblyFrames({
    note: SEPARATED_NOTE,
    terms: [
      { start: longFingers, end: longFingers + "long fingers".length },
      { start: flatCheeks, end: flatCheeks + "flat cheeks".length },
    ],
    ranks: [
      { bar: 1 },
      { bar: 0.4 },
      { bar: 0 },
    ],
  });
  const separatedMs = assemblyDuration(separated);
  expect(separatedMs).toBeGreaterThan(2_000);
  expect(separatedMs).toBeLessThan(10_000);
  expect(separated.at(-1)?.decide).toBe(true);
  expect(separated.some((frame) => frame.stage === "read" && frame.phrases === 0)).toBe(true);
  expect(separated.some((frame) => frame.stage === "map" && frame.chips === 2)).toBe(true);
  expect(separated.some((frame) => frame.narrowed && frame.bars === 2)).toBe(true);

  const crowded = assemblyFrames({
    note: "symptom ".repeat(400),
    terms: Array.from({ length: 8 }, (_, index) => ({ start: index * 8, end: index * 8 + 7 })),
    ranks: Array.from({ length: 10 }, () => ({ bar: 1 })),
  });
  expect(assemblyDuration(crowded)).toBeLessThan(10_000);
});

test("the scan marks a phrase only after the window has passed it", () => {
  const note = "The hands show long fingers.";
  const start = note.indexOf("long fingers");
  const end = start + "long fingers".length;
  const before = notePieces(note, [{ start, end }], 0, start + 4);
  expect(before.some((piece) => piece.kind === "scan")).toBe(true);
  expect(before.some((piece) => piece.kind === "mark")).toBe(false);
  const after = notePieces(note, [{ start, end }], 1, note.length);
  expect(after.some((piece) => piece.kind === "mark" && piece.text === "long fingers")).toBe(true);
});

test("reduced motion opens the decision without playing the scan", async () => {
  vi.stubGlobal(
    "matchMedia",
    vi.fn(() => ({
      matches: true,
      addEventListener: () => undefined,
      removeEventListener: () => undefined,
    })),
  );
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => ({
      ok: true,
      status: 200,
      json: async () => ({
        note: SEPARATED_NOTE,
        case_id: "00000000-0000-4000-8000-0000000000d1",
        method: "Lexicon match. No language model ran.",
        stages: [
          { id: "read", label: "Read", did: "The software scanned the note." },
          { id: "map", label: "Map", did: "Phrases were paired with HPO ids." },
          { id: "match", label: "Match", did: "Each id was checked against the table." },
          { id: "rank", label: "Rank", did: "Rows were ordered. This is not a diagnosis." },
        ],
        terms: [
          {
            hpo_id: "HP:0001166",
            label: "Arachnodactyly",
            plain_words: "long fingers",
            quote: "long fingers",
            start: SEPARATED_NOTE.indexOf("long fingers"),
            end: SEPARATED_NOTE.indexOf("long fingers") + "long fingers".length,
          },
        ],
        cells: [{ orphanet_id: "ORPHA:9000001", hpo_id: "HP:0001166", listed: true }],
        ranks: [{ orphanet_id: "ORPHA:9000001", score: 1, bar: 1, reason: "Lists long fingers." }],
        abstained: false,
        abstain_text: null,
        questions: ["Ask a doctor what this means for you. This is not a diagnosis."],
        limit_line: null,
        gene_line: null,
      }),
    })),
  );
  render(<WorkPipeline slug="separated" note={null} />);
  expect(await screen.findByRole("button", { name: "Confirm these terms" })).toBeInTheDocument();
  expect(screen.getByTestId("impact")).toHaveTextContent("1 click");
  expect(screen.getByTestId("stage-read")).toHaveTextContent("Deterministic");
});
