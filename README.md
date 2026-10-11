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

`make demo` resets the local database and opens the notebook at <http://127.0.0.1:3000>. Sign in with any name, then load one of the five synthetic cases. The page shows a cited catalogue comparison, plain-language term wording, and the country footer. One case abstains. The lab-variant page has a warning-sign button that shows the stop screen and does not save the draft. A checkbox on the summary turns on an experimental population-frequency prior from a checked-in fixture. It does not change the catalogue comparison.

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

A hosted model is not on the notebook path. `complete_with_gemini` calls Gemini first. It reads `GEMINI_API_KEY` or `GOOGLE_API_KEY`, follows every page of `GET https://generativelanguage.googleapis.com/v1beta/models`, and records the newest flash-lite id it chose. An OpenRouter model whose id ends in `:free` runs only after a 429 or `RESOURCE_EXHAUSTED`. Set `OPENROUTER_API_KEY` (or a gitignored `uploads/openrouter.key`) and `OPENROUTER_FREE_MODELS` to a comma-separated list of `:free` ids. With no Gemini key, no fallback key, or no `:free` id, the client returns pinned wording, records provider `gazetteer`, and does not call OpenRouter. That sentence is not cached. Only text marked `SYNTHETIC-ONLY` may be sent. `D4_LLM_LIVE=1` runs one live smoke test; the other tests use stubs.

`make safety-scan` checks the fixed sentences and the country footers.

`make eval-store` downloads the pinned public files and writes `eval/RESULTS.md`. The frequency-bin rows are the catalogue scorer. The term-overlap rows are the stand-in, kept for comparison.

`make ingest-replay` replays local reference archives into a change list. It does not send a variant anywhere.

`make db-up` starts Postgres. It uses `compose.yaml` when Docker is available, and a local PostgreSQL 16 cluster otherwise.

`make db-reset` drops the `app` schema and applies `db/001_roles.sql` and `db/002_gate.sql`.

`make test` resets the database, builds the TypeScript contract, and runs the gate tests and the contract round-trip.

## Read this first

1. [PLAN.md](PLAN.md) — the evidence design, the approval gate, and the two-track decision.
2. [docs/IMPLEMENTATION.md](docs/IMPLEMENTATION.md) — the file tree, what not to build, containers, where it runs, and the build phases.
3. [docs/search-log.md](docs/search-log.md) — what was actually looked up. The count is not 1,500.
4. [docs/review.md](docs/review.md) — critics of the correlator design. The later two-track decision is section 0 of the plan.
