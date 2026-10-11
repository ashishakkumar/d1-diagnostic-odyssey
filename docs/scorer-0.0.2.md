# Frequency-bin 0.0.2

For research use only. Not for use in diagnostic procedures.

This note is the measurement for the scorer that ships. It brings the corpus-background work from pull request #8 (`cursor/corpus-background-margin-7b44`) onto the finish branch. `PLAN.md` is unchanged. The screen stays a catalogue comparison. These rows are not a benefit to a real patient, not a probability for a person outside this public set, and not a diagnosis.

## What ships

Frequency-bin 0.0.2 ships. Term-overlap-loo does not.

`P(feature | not this disease) = (k + 1) / (n + 2)` on every disorder in Orphadata Science `en_product4`, including disorders that are not ranked. A missing row contributes a ratio of 1. `CLOSE_DISEASE_COUNT` stays 10 and `CLOSE_FACTOR` stays 2.0. `phenotype.hpoa` is not loaded. The prior counts were not fitted to Phenopacket Store.

Term-overlap-loo full-set top-1 is 3806/4815, with 104/4815 abstentions. It is higher because the catalogue is other packets in the same store release, with only the packet being scored left out. That uses the labels the score is judged against. A held-out packet split does not fix it: the catalogue for a test packet still includes train packets. It is printed, labeled `term-overlap-loo`, and not shipped.

An ancestor climb (depth 8, stop at HP:0000001 and HP:0000118) was measured on the older flat background of 0.05. Full-set top-1 fell from 1292/4815 to 841/4815. That climb was not rerun on the corpus background, so 841/4815 is not a 0.0.2 result. The notebook and `d1_eval store` do not pass a parent map. The function remains for a caller that passes parents. Thresholds were not refit on a training split or on the held-out split.

## NOT MEASURED / pending

`PLAN.md` requires the catalogue comparison to beat a degree baseline at k = 1 and k = 5 on both percentage@k and precision@k, with percentage@k over the 249 unique-map diseases. The degree baseline is NOT MEASURED / pending. precision@k at k = 1 and k = 5 is NOT MEASURED / pending. Those bars are not a pass.

A decoy gene does not change the disease rank in `tests/eval/test_harness.py`. A store-scale decoy-gene evaluation is NOT MEASURED / pending.

## 0.0.1, kept for comparison

Flat background 0.05 and a missing-row ratio of 0.01 / 0.05. Full-set top-1 1292/4815, top-3 1589/4815, top-10 1953/4815, no-confident 1653/4815. Held-out full top-1 on that scorer was 1046/3890 train and 246/925 test. Those held-out rows are not the 0.0.2 result. The older document is archived at the bottom of `eval/RESULTS.md` when the 0.0.2 run is written.

## 0.0.2 re-run on this branch

`d1_eval store` was run again after this background was wired into the shipped scorer. Store 0.1.27, sha256 `d0c70005bb09b87035087516252b6b539fbc0415be7c664b73c9cde7eedf205a`. Orphadata `en_product4` sha256 `4f44e8a61201399911aa1ba44a293c0ccaa5ce11272c47d40862255cb72f6b32`, 116664 rows. Excluded diseases 531. Packets scored 4815. Packets skipped 0. The command printed `frequency-bin top1=1395/4815` and a separate `term-overlap-loo top1=3806/4815`.

| degradation | top-1 | top-3 | top-10 | abstain |
| --- | --- | --- | --- | --- |
| full | 1395/4815 | 1732/4815 | 2026/4815 | 1645/4815 |
| fewer | 868/4815 | 1131/4815 | 1446/4815 | 2054/4815 |
| vaguer | 262/4815 | 487/4815 | 735/4815 | 1651/4815 |
| patient | 127/4815 | 225/4815 | 385/4815 | 1968/4815 |

Held-out split, same run, not used to choose a threshold, a background, or a bin edge. SHA-256 of the packet id, modulo 5, remainder 0 is test (3890 train, 925 test). 1129 + 266 = 1395.

| degradation | train top-1 | test top-1 |
| --- | --- | --- |
| full | 1129/3890 | 266/925 |
| fewer | 705/3890 | 163/925 |
| vaguer | 211/3890 | 51/925 |
| patient | 100/3890 | 27/925 |

A zero runner-up leaves `margin` unset, sets `margin_reason` to `runner_up_ratio_is_zero`, and sets `margin_fact` to the term that made the ratio 0.
