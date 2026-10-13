export type TourStep = {
  id: string;
  target: "note" | "chips" | "match-grid" | "ranks" | "decision";
  title: string;
  kicker: "Rule" | "Scoring model" | "Person";
  body: string;
  handsOn: boolean;
};

export const TOUR_STEPS: TourStep[] = [
  {
    id: "note",
    target: "note",
    title: "Read",
    kicker: "Rule",
    body: "A fixed lexicon scans this synthetic note and highlights pinned phrases. No language model reads it.",
    handsOn: false,
  },
  {
    id: "chips",
    target: "chips",
    title: "Map",
    kicker: "Rule",
    body: "Each pinned phrase becomes an HPO chip, with the quote beside it. Press Correct on a chip. That edit stays on this screen until you confirm.",
    handsOn: true,
  },
  {
    id: "map",
    target: "match-grid",
    title: "Match",
    kicker: "Rule",
    body: "Each cell is a lookup on the synthetic table. A lit cell means that row lists the term.",
    handsOn: false,
  },
  {
    id: "rank",
    target: "ranks",
    title: "Rank",
    kicker: "Scoring model",
    body: "Resnik best-match average ordered these rows. It is a scoring model on this table, not a language model. This is not a diagnosis.",
    handsOn: false,
  },
  {
    id: "decide",
    target: "decision",
    title: "You decide",
    kicker: "Person",
    body: "Confirm records the chips through the approval gate. The tour does not press Confirm.",
    handsOn: false,
  },
];

export type AnalyzeTourStep = {
  id: string;
  target: "note-box" | "path" | "findings" | "results" | "separate";
  title: string;
  kicker: "Language model" | "Search" | "Scoring model" | "Person";
  body: string;
  handsOn: boolean;
};

export const ANALYZE_TOUR: AnalyzeTourStep[] = [
  {
    id: "box",
    target: "note-box",
    title: "Paste a note",
    kicker: "Person",
    body: "Type symptoms in plain words, or press an example. Press Find conditions to continue.",
    handsOn: true,
  },
  {
    id: "path",
    target: "path",
    title: "Extract",
    kicker: "Language model",
    body: "A language model pulls out each finding, whether it is present or absent, and context such as age and family history. This line says which model ran, or that rules ran because no model was available.",
    handsOn: false,
  },
  {
    id: "findings",
    target: "findings",
    title: "Map",
    kicker: "Search",
    body: "Each finding is matched to a real HPO term by exact, fuzzy and embedding search. The model never invents ids. Dashed chips are unsure: pick the right term and the list re-ranks.",
    handsOn: false,
  },
  {
    id: "results",
    target: "results",
    title: "Rank",
    kicker: "Scoring model",
    body: "Resnik best-match average scores about 12,800 diseases from the public HPO annotations. Absent findings lower a disease's score. Each row shows the matching evidence and links to OMIM or Orphanet.",
    handsOn: false,
  },
  {
    id: "separate",
    target: "separate",
    title: "What would separate them",
    kicker: "Scoring model",
    body: "Findings listed by some top candidates and not others. Asking about these narrows the list. This is not a diagnosis.",
    handsOn: false,
  },
];
