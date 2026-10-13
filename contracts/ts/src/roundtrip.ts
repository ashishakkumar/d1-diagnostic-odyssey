import { readFileSync } from "node:fs";

import type { Pipeline } from "./generated.js";

const raw = JSON.parse(readFileSync(process.argv[2], "utf8")) as Pipeline;
const keys = [
  "case",
  "hpo_term_drafts",
  "accepted_terms",
  "lab_reported_variants",
  "evidence",
  "change_events",
  "approvals",
] as const satisfies readonly (keyof Pipeline)[];

for (const key of keys) {
  if (!(key in raw)) {
    throw new Error(`missing ${key}`);
  }
}

const version = raw.case.metaData.phenopacketSchemaVersion;
if (!version.startsWith("2")) {
  throw new Error("case is not a Phenopacket schema v2 document");
}

process.stdout.write(`${JSON.stringify(raw)}\n`);
