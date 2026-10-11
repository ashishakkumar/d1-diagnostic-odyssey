# Frequency-bin 0.0.2 measurement

For research use only. Not for use in diagnostic procedures.

This note is for the finish branch to merge with pull request #8 (`cursor/corpus-background-margin-7b44` into `cursor/integrate-safe-core-e84c`). `PLAN.md` is unchanged. The screen stays a catalogue comparison. These rows are not a benefit to a real patient, not a probability for a person outside this public set, and not a diagnosis.

## What was measured

Phenopacket Store 0.1.27, sha256 `d0c70005bb09b87035087516252b6b539fbc0415be7c664b73c9cde7eedf205a`. Orphadata Science `en_product4`, sha256 `4f44e8a61201399911aa1ba44a293c0ccaa5ce11272c47d40862255cb72f6b32`, 116664 association rows. Mondo `v2026-10-06`. Excluded diseases 531. Packets scored 4815. Tool `frequency-bin` `0.0.2`.

`P(feature | not this disease) = (k + 1) / (n + 2)` on every disorder in that file, including disorders that are not ranked. A missing row contributes a ratio of 1. `CLOSE_DISEASE_COUNT` stays 10 and `CLOSE_FACTOR` stays 2.0. `phenotype.hpoa` was not loaded.

The counts below are the frequency-bin table in `eval/RESULTS.md`. The older 0.0.1 rows are still in that file. Compare only with those rows. The command stdout prints the term-overlap leave-one-out stand-in first (`top1=3806/4815`). That stand-in is inflated and is not this table.

| degradation | top-1 | top-3 | top-10 | abstain |
| --- | --- | --- | --- | --- |
| full | 1395/4815 | 1732/4815 | 2026/4815 | 1645/4815 |
| fewer | 868/4815 | 1131/4815 | 1446/4815 | 2054/4815 |
| vaguer | 262/4815 | 487/4815 | 735/4815 | 1651/4815 |
| patient | 127/4815 | 225/4815 | 385/4815 | 1968/4815 |

Same run, packet created dates only: cutoff 2026-06-23, before=10377, after=0, undated=0. The packet created timestamp is not a publication date. This check is not a pass.

A runner-up lower ratio of 0 leaves the numeric margin unset. `margin_fact` names the cause (an excluded term, an obligate bin against an excluded observation, both, both ratios at 0, no runner-up, or a non-finite margin).

## Not measured, so not a pass

`PLAN.md` requires the catalogue comparison to beat the degree baseline at k = 1 and k = 5 on both percentage@k and precision@k. Percentage@k there is hits over the 249 unique-map diseases. That baseline was not run. Those four numbers are not a pass.

A held-out packet split was not run. It is not a pass.

Abstention constants were not refit on this store run. Full-detail abstention moved from 1653/4815 to 1645/4815. Vaguer abstention moved from 2352/4815 to 1651/4815, and patient abstention from 2731/4815 to 1968/4815, because a missing row now contributes a ratio of 1. Leave `CLOSE_DISEASE_COUNT` and `CLOSE_FACTOR` as they are.

## Store command log

```
PYTHONPATH="eval:contracts/src:services/scoring:services/ingest/src" .venv/bin/python -m d1_eval store --data data/eval --out eval/RESULTS.md
level=full
level=fewer
level=vaguer
level=patient
frequency level=full
frequency level=fewer
frequency level=vaguer
frequency level=patient
excluded_diseases=531
packets_scored=4815
packets_not_unique=5562
packets_skipped=0
top1=3806/4815
top3=4369/4815
top10=4606/4815
no_confident=104/4815
orphanet=en_product4 sha256 4f44e8a61201399911aa1ba44a293c0ccaa5ce11272c47d40862255cb72f6b32 rows 116664
EXIT:0
```

The `top1=3806/4815` line is the term-overlap stand-in. The frequency-bin counts are the table above.

## Checks after the scorer change

`make lint` ended `LINT_EXIT:0` (ruff check passed, 63 files already formatted, contracts tsc ok, web tsc ok).

`make safety-scan` printed `safety-scan: ok` and `SAFETY_EXIT:0`.

`make test` after this note change ended `184 passed, 1 warning in 3.38s` and `TEST_EXIT:0`. The warning is `StarletteDeprecationWarning` from `fastapi/testclient.py` about httpx.
