# Diagnostic odyssey notebook

For research use only. Not for use in diagnostic procedures.

The safe core is a private notebook for one person: a timeline, HPO terms that person confirms, a variant copied from a lab report, a monthly public-database check matched on the device, and a short PDF for a doctor. Every sentence comes from a fixed template. It does not diagnose.

The experimental track is a separate local container. It can read a VCF and run Exomiser and LIRICAL unchanged, on public or synthetic files only. It is not part of the notebook and it is not for a real user's data unless Ashish later allows that.

This tree is the foundation: one pipeline contract, the Postgres approval gate, and the package skeleton. Notebook screens, scoring, ingest, and the experimental genome engine are not in this tree.

Real records stay on the person's own computer. A hosted database is for synthetic cases only. This foundation does not send text to a model.

## Commands

```text
make setup
make db-up
make db-reset
make lint
make test
```

`make setup` creates a virtualenv, installs the Python and TypeScript packages, and generates types from `contracts/pipeline.schema.json`.

`make db-up` starts Postgres. It uses `compose.yaml` when Docker is available, and a local PostgreSQL 16 cluster otherwise.

`make db-reset` drops the `app` schema and applies `db/001_roles.sql` and `db/002_gate.sql`.

`make test` resets the database, builds the TypeScript contract, and runs the gate tests and the contract round-trip.

## Read this first

1. [PLAN.md](PLAN.md) — the evidence design, the approval gate, and the two-track decision.
2. [docs/IMPLEMENTATION.md](docs/IMPLEMENTATION.md) — the file tree, what not to build, containers, where it runs, and the build phases.
3. [docs/search-log.md](docs/search-log.md) — what was actually looked up. The count is not 1,500.
4. [docs/review.md](docs/review.md) — critics of the correlator design. The later two-track decision is section 0 of the plan.
