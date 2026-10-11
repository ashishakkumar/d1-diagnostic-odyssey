# Diagnostic odyssey notebook

For research use only. Not for use in diagnostic procedures.

The safe core is a private notebook for one person: a timeline, HPO terms that person confirms, a variant copied from a lab report, a monthly public-database check matched on the device, and a short PDF for a doctor. Every sentence comes from a fixed template. It does not diagnose.

The experimental track is a separate local container. It can read a VCF and run Exomiser and LIRICAL unchanged, on public or synthetic files only. It is not part of the notebook and it is not for a real user's data unless Ashish later allows that.

This tree is the safe core: the pipeline contract, the Postgres approval gate, the notebook, the catalogue scorer, the sentence scanner, and the local reference watcher. The experimental genome engine is not in this tree.

Real records stay on the person's own computer. A hosted database is for synthetic cases only. This foundation does not send text to a model.

## Commands

```text
make setup
make db-up
make db-reset
make lint
make safety-scan
make test
make eval-store
make ingest-replay
```

`make setup` creates a virtualenv, installs the Python and TypeScript packages, and generates types from `contracts/pipeline.schema.json`.

`make safety-scan` checks the fixed sentences and the country footers.

`make eval-store` downloads the pinned public files and writes `eval/RESULTS.md`. The frequency-bin rows are the catalogue scorer. The term-overlap rows are the stand-in, kept for comparison.

`make ingest-replay` replays local reference archives into a change list. It does not send a variant anywhere.

`make db-up` starts Postgres. It uses `compose.yaml` when Docker is available, and a local PostgreSQL 16 cluster otherwise.

`make db-reset` drops the `app` schema and applies `db/001_roles.sql` and `db/002_gate.sql`.

`make test` resets the database, builds the TypeScript contract, and runs the gate tests and the contract round-trip.

## Catalogue comparison

The scorer is ordinary code. It does not call a model.

For a term a disorder lists, the likelihood ratio is the Orphanet bin bound divided by P(feature | not this disease). That rate comes from Orphadata Science `en_product4` (CC BY 4.0), every disorder in the file that has an HPO association, including disorders that are not ranked. A disorder counts as having the feature when the bin is not excluded. For the disorder being scored, k is how many other disorders have the feature and n is how many other disorders are in the file. The rate is (k + 1) / (n + 2). The added counts are a uniform prior: a term no other disorder lists is not treated as impossible, and a term every other disorder lists does not make the absent-feature rate zero. The prior is frozen. It was not fitted to Phenopacket Store.

`phenotype.hpoa` is not used. Its annotation guide says inferred rows are parsed from OMIM, and OMIM has to be contacted before another product reuses them.

When a disorder has no row for a term, the frequency used for that disorder is the same rate, so the ratio is 1. A missing row is not evidence.

Abstention stays at 10 disorders within a factor of 2, and at a flip of the first row between the bin bounds. Those constants were not refit.

When the runner-up's lower ratio is 0 because a present term is in the excluded bin, the margin is not a finite number. The report says the runner-up has an excluded term and names it. A lower ratio of 0 because the person does not have a term the catalogue marks obligate is described that way, and is not called an excluded term. One scoreable disorder is reported as no runner-up.

## Read this first

1. [PLAN.md](PLAN.md) — the evidence design, the approval gate, and the two-track decision.
2. [docs/IMPLEMENTATION.md](docs/IMPLEMENTATION.md) — the file tree, what not to build, containers, where it runs, and the build phases.
3. [docs/search-log.md](docs/search-log.md) — what was actually looked up. The count is not 1,500.
4. [docs/review.md](docs/review.md) — critics of the correlator design. The later two-track decision is section 0 of the plan.
