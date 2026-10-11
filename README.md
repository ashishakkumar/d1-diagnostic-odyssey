# Diagnostic odyssey notebook

For research use only. Not for use in diagnostic procedures.

The safe core is a private notebook for one person: a timeline, HPO terms that person confirms, a variant copied from a lab report, a monthly public-database check matched on the device, and a short PDF for a doctor. Every sentence comes from a fixed template. It does not diagnose.

The experimental track is a separate local container. It can read a VCF and run Exomiser and LIRICAL unchanged, on public or synthetic files only. It is not part of the notebook and it is not for a real user's data unless Ashish later allows that.

This tree is the safe core: the pipeline contract, the Postgres approval gate, the notebook, the catalogue scorer, the sentence scanner, and the local reference watcher. The experimental genome engine is not in this tree.

Real records stay on the person's own computer. A hosted database is for synthetic cases only. This foundation does not send text to a model.

## Commands

```text
make setup
make demo
```

`make setup` creates a virtualenv, installs the Python and TypeScript packages, and generates types from `contracts/pipeline.schema.json` and from the FastAPI app.

`make demo` resets the local database and opens the notebook at <http://127.0.0.1:3000>. One step: pick a synthetic case, or paste or upload a short synthetic note. There is no sign-in wall and no symptom form. The next screen runs Read, Map, Match, and Rank. Extraction is a fixed lexicon. No language model ran. The free-tier quota is closed until 2026-10-12 00:00 UTC. Ranks are Resnik best-match average on the ten-row synthetic table, not the 249-disease held-out run. The person confirms or corrects the chips. That click is the only write on this path, and it goes through `app.apply_decision`. A warning-sign note returns 409 and is not saved. The frequency-bin card, with its cited comparison and the opt-in allele-frequency prior, is still the summary after `POST /demo/cases/{slug}/load`. It is not the landing ranker.

```text
make db-up
make db-reset
make lint
make safety-scan
make test
make e2e
make eval-store
make ingest-replay
make openapi
```

`make e2e` runs the same path in a browser and writes screenshots under `docs/demo-screenshots/`.

`make openapi` rewrites `contracts/openapi.json` and `contracts/ts/src/api.ts` from the running app's routes. `make test` fails if those files drift.

A hosted model is not on the notebook path. `complete_with_gemini` calls Gemini first. It reads `GEMINI_API_KEY` or `GOOGLE_API_KEY`, follows every page of `GET https://generativelanguage.googleapis.com/v1beta/models`, and records the newest flash-lite id it chose. An OpenRouter model whose id ends in `:free` runs only after a 429 or `RESOURCE_EXHAUSTED`. Set `OPENROUTER_API_KEY` (or a gitignored `uploads/openrouter.key`). When `OPENROUTER_FREE_MODELS` is unset or blank, the client uses the checked-in priced-zero list in `d4_llm.fallback` (`google/gemma-4-31b-it:free`, then two more `:free` ids). A set value replaces that list and must end in `:free`. With no Gemini key or no fallback key, the client returns pinned wording, records provider `gazetteer`, and does not call OpenRouter. That sentence is not cached. Only text marked `SYNTHETIC-ONLY` may be sent. `D4_LLM_LIVE=1` runs one live smoke test; the other tests use stubs.

`make safety-scan` checks the fixed sentences and the country footers.

`make eval-store` downloads the pinned public files and writes `eval/RESULTS.md`. The synthetic notebook card is frequency-bin 0.0.2: the bin bound divided by a leave-one-out rate `(k + 1) / (n + 2)` from Orphadata Science `en_product4`, including disorders that are not ranked. A missing row has ratio 1. That card's abstention stays at 10 diseases within a factor of 2. Those constants were not refit. The command prints frequency-bin totals and a line labeled `term-overlap-loo`. That stand-in reads labels from other packets in the same release, so it is not shipped. `python -m d1_eval bars` writes the frequency-bin comparison to `eval/bars-0.0.2.md`. Frequency-bin does not beat the degree baseline at k = 1 or k = 5. The public-case ranker is Resnik best-match average, chosen on a fit/validation split and scored once on the held-out packets in `eval/bars-resnik.md`. On that held-out split it beats the degree baseline at k = 1 and k = 5. It abstains when the best score is at or below zero. The comparison panel says this in plain language. The rows on that panel stay the synthetic frequency-bin card.

`make ingest-replay` replays local reference archives into a change list. It does not send a variant anywhere.

`make db-up` starts Postgres. It uses `compose.yaml` when Docker is available, and a local PostgreSQL 16 cluster otherwise.

`make db-reset` drops the `app` schema and applies `db/001_roles.sql` and `db/002_gate.sql`.

`make test` resets the database, builds the TypeScript contract, and runs the gate tests and the contract round-trip.

## Read this first

1. [PLAN.md](PLAN.md) — the evidence design, the approval gate, and the two-track decision.
2. [docs/IMPLEMENTATION.md](docs/IMPLEMENTATION.md) — the file tree, what not to build, containers, where it runs, and the build phases.
3. [docs/search-log.md](docs/search-log.md) — what was actually looked up. The count is not 1,500.
4. [docs/review.md](docs/review.md) — critics of the correlator design. The later two-track decision is section 0 of the plan.
