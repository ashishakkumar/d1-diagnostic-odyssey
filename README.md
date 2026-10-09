# Rare-disease case file (plan only)

A longitudinal diagnostic-odyssey case file: time-ordered Phenopackets v2 snapshots, human-accepted HPO drafts, disease and gene scores computed in code, a next question, ClinVar observations, and trial links. Similar-patient matching stays off unless a trusted Matchmaker Exchange node exists.

Nothing here runs yet. The design, the sources, and the limits are in [PLAN.md](PLAN.md). Search counts are in [docs/search-log.md](docs/search-log.md).

This is not a clinic workflow that closes a request. It keeps a chart across years and recomputes a rank when the chart or the knowledge base changes. A person accepts every phenotype and every gene before the rank moves.

## Read this first

1. [PLAN.md](PLAN.md) — problem, solution, stack, data, evaluation, cost, and the clear versus unclear list.
2. [docs/search-log.md](docs/search-log.md) — what was actually looked up.

## When building is approved

The plan’s layout is `apps/web`, `services/api`, `services/mcp`, `services/literature`, `packages/scorer`, `eval/`, and `sql/`. The demo is five synthetic cases and does not need an API key. That code is not in the tree until the plan is accepted.
