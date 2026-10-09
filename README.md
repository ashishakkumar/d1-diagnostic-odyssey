# Multi-omics correlator (plan only)

A research demo, still a plan, for one synthetic person over time. It lines up already-reported facts — a lab value, an HPO term, a variant classification copied from a lab report, a medication — and shows separate cards. The cards are a population rank against a public survey extract, a catalogue comparison of phenotypes to Orphanet frequency bins, a quoted lab classification beside a quoted ClinVar record, and a copied drug–gene sentence. History notes stay on a timeline.

It does not diagnose, order a test, choose a dose, or call a variant. Nothing here runs yet. The design, the sources, and the limits are in [PLAN.md](PLAN.md). Search counts are in [docs/search-log.md](docs/search-log.md). What the critics said about this concept is in [docs/review.md](docs/review.md).

For research use only. Not for use in diagnostic procedures.

## Read this first

1. [PLAN.md](PLAN.md) — dimensions in and out, the Postgres approval gate, the reference-data gap, evaluation, cost, and the clear versus unclear list.
2. [docs/search-log.md](docs/search-log.md) — what was actually looked up. The count is not 1,500.
3. [docs/review.md](docs/review.md) — evaluator, optimizer, investors, clinician, and stack review of this correlator.

## What the cards are allowed to say

A population rank compares an accepted lab value to a pinned public extract and cites that file. A missing row means no rank, not a normal result. A catalogue comparison uses Orphanet frequency bins and says how many diseases had no unique public map. It is not the probability the person has the disease. Every comparison card lists what it did not use: no sequence file, no image, no allele frequency, no credentialed cohort, no dose.

Synthetic patients in the application database can test that plumbing. They cannot validate a real correlation. Credentialed cohorts (UK Biobank, All of Us, MIMIC, GenomeIndia, UDN participant files) are not in the repo.

## When building is approved

The plan’s layout is `apps/web`, `services/api`, `packages/correlator`, `eval/`, and `sql/`. The demo is five synthetic cases, Compose Postgres, and no API key. The approval gate is a Postgres function. LangGraph, MCP, and A2A are not in the layout. That code is not in the tree until the plan is accepted.
