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
