# Frequency-bin 0.0.2

For research use only. Not for use in diagnostic procedures.

This note is the measurement for the synthetic frequency-bin card. It brings the corpus-background work from pull request #8 (`cursor/corpus-background-margin-7b44`) onto the finish branch. `PLAN.md` is unchanged. The screen stays a catalogue comparison. These rows are not a benefit to a real patient, not a probability for a person outside this public set, and not a diagnosis.

## What ships

The synthetic notebook card is frequency-bin 0.0.2. Term-overlap-loo does not ship. Frequency-bin does not beat the degree baseline, so it is not the public-case ranker. The public-case ranker is Resnik best-match average. It was chosen on fit and validation, then scored once on the held-out split. That measurement is [../eval/bars-resnik.md](../eval/bars-resnik.md). On the 925 test packets it beats the degree baseline at k=1 (419/925 vs 327/925) and at k=5 (614/925 vs 533/925; precision@5 0.132757 vs 0.115243). It abstains when the best score is at or below zero. The comparison panel says the on-screen rows are the frequency-bin card.

`P(feature | not this disease) = (k + 1) / (n + 2)` on every disorder in Orphadata Science `en_product4`, including disorders that are not ranked. A missing row contributes a ratio of 1. `CLOSE_DISEASE_COUNT` stays 10 and `CLOSE_FACTOR` stays 2.0. `phenotype.hpoa` is not loaded. The prior counts were not fitted to Phenopacket Store.

Term-overlap-loo full-set top-1 is 3806/4815, with 104/4815 abstentions. It is higher because the catalogue is other packets in the same store release, with only the packet being scored left out. That uses the labels the score is judged against. A held-out packet split does not fix it: the catalogue for a test packet still includes train packets. It is printed, labeled `term-overlap-loo`, and not shipped.

An ancestor climb (depth 8, stop at HP:0000001 and HP:0000118) was measured on the older flat background of 0.05. Full-set top-1 fell from 1292/4815 to 841/4815. On this corpus background the climb was measured on train packets only, with no abstention: top-1 717/3890 against 1172/3890 with no climb. That climb is not shipped. The notebook and `d1_eval store` do not pass a parent map. Thresholds were not refit on a training split or on the held-out split.

## Degree baseline and precision@k

Measured on the shipped frequency-bin 0.0.2 scorer. No parent map. Thresholds were not refit. The held-out split was not used to choose a threshold. Full tables are in [../eval/bars-0.0.2.md](../eval/bars-0.0.2.md).

Packet denominator is the 4815 unique-map packets. Abstentions are misses. The 249-disease rows are the unweighted mean of each disease's packet rate. Every unique-map disease had at least one packet. precision@k uses denominator k, including when the list is shorter than k. Ties take the worst rank.

| cohort | k | frequency-bin hits | degree-baseline hits | frequency percentage@k | degree percentage@k | frequency precision@k | degree precision@k |
| --- | --- | --- | --- | --- | --- | --- | --- |
| all packets | 1 | 1395/4815 | 1647/4815 | 0.289720 | 0.342056 | 0.289720 | 0.342056 |
| all packets | 5 | 1871/4815 | 2665/4815 | 0.388577 | 0.553479 | 0.077715 | 0.110696 |
| train packets | 1 | 1129/3890 | 1320/3890 | 0.290231 | 0.339332 | 0.290231 | 0.339332 |
| train packets | 5 | 1501/3890 | 2132/3890 | 0.385861 | 0.548072 | 0.077172 | 0.109614 |
| test packets | 1 | 266/925 | 327/925 | 0.287568 | 0.353514 | 0.287568 | 0.353514 |
| test packets | 5 | 370/925 | 533/925 | 0.400000 | 0.576216 | 0.080000 | 0.115243 |
| 249 diseases | 1 | mean of packet rates | mean of packet rates | 0.353135 | 0.355850 | 0.353135 | 0.355850 |
| 249 diseases | 5 | mean of packet rates | mean of packet rates | 0.457476 | 0.536436 | 0.091495 | 0.107287 |

Frequency-bin does not beat the degree baseline on percentage@k or precision@k at k = 1 or k = 5, on all packets, on the held-out test packets, or on the 249-disease mean. That pass bar is not met for frequency-bin. Thresholds were not changed after this measurement.

The public-case ranker is a different method. See [../eval/bars-resnik.md](../eval/bars-resnik.md). A decoy gene on each of the 925 held-out packets did not change present HPO ids or Resnik scores.

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
