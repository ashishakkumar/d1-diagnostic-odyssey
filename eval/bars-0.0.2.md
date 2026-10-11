# Degree baseline and precision@k

For research use only. Not for use in diagnostic procedures.

Shipped scorer: frequency-bin 0.0.2. No parent map. CLOSE_DISEASE_COUNT stays 10 and CLOSE_FACTOR stays 2.0. They were not refit. The degree baseline scores each unique-map disease by the sum of -log(frequency) over present terms that disease lists outside the excluded bin. Frequency is the fraction of unique-map diseases that list the term. A term no unique-map disease lists adds nothing. phenotype.hpoa was not loaded. en_product6 was not loaded.

percentage@k is hits over the stated denominator. Abstentions are misses. precision@k is the mean of 1/k when the truth disease's worst rank is at most k, and 0 otherwise. The denominator stays k when the returned list is shorter than k. Ties take the worst rank. The held-out split is SHA-256 of the packet id, modulo 5, remainder 0 = test. That split was not used to choose a threshold, a background, or a bin edge.

unique_map_diseases: 249
excluded_diseases: 531
en_product4_rows: 116664
store_sha256: d0c70005bb09b87035087516252b6b539fbc0415be7c664b73c9cde7eedf205a

| cohort | tool | k | hits | denominator | percentage@k | precision@k |
| --- | --- | --- | --- | --- | --- | --- |
| all packets | frequency-bin | 1 | 1395 | 4815 | 0.289720 | 0.289720 |
| all packets | frequency-bin | 5 | 1871 | 4815 | 0.388577 | 0.077715 |
| all packets | degree-baseline | 1 | 1647 | 4815 | 0.342056 | 0.342056 |
| all packets | degree-baseline | 5 | 2665 | 4815 | 0.553479 | 0.110696 |
| train packets | frequency-bin | 1 | 1129 | 3890 | 0.290231 | 0.290231 |
| train packets | frequency-bin | 5 | 1501 | 3890 | 0.385861 | 0.077172 |
| train packets | degree-baseline | 1 | 1320 | 3890 | 0.339332 | 0.339332 |
| train packets | degree-baseline | 5 | 2132 | 3890 | 0.548072 | 0.109614 |
| test packets | frequency-bin | 1 | 266 | 925 | 0.287568 | 0.287568 |
| test packets | frequency-bin | 5 | 370 | 925 | 0.400000 | 0.080000 |
| test packets | degree-baseline | 1 | 327 | 925 | 0.353514 | 0.353514 |
| test packets | degree-baseline | 5 | 533 | 925 | 0.576216 | 0.115243 |

Disease rows are the unweighted mean of each disease's packet rate. A unique-map disease with no scored packet is a miss and stays in the denominator.

| tool | k | diseases | diseases_with_no_packet | percentage@k | precision@k |
| --- | --- | --- | --- | --- | --- |
| frequency-bin | 1 | 249 | 0 | 0.353135 | 0.353135 |
| frequency-bin | 5 | 249 | 0 | 0.457476 | 0.091495 |
| degree-baseline | 1 | 249 | 0 | 0.355850 | 0.355850 |
| degree-baseline | 5 | 249 | 0 | 0.536436 | 0.107287 |

## Comparison

On all packets at k=1, frequency-bin percentage@k does not beat the degree baseline (0.289720 vs 0.342056) and precision@k does not beat it (0.289720 vs 0.342056).
On all packets at k=5, frequency-bin percentage@k does not beat the degree baseline (0.388577 vs 0.553479) and precision@k does not beat it (0.077715 vs 0.110696).
On train packets at k=1, frequency-bin percentage@k does not beat the degree baseline (0.290231 vs 0.339332) and precision@k does not beat it (0.290231 vs 0.339332).
On train packets at k=5, frequency-bin percentage@k does not beat the degree baseline (0.385861 vs 0.548072) and precision@k does not beat it (0.077172 vs 0.109614).
On test packets at k=1, frequency-bin percentage@k does not beat the degree baseline (0.287568 vs 0.353514) and precision@k does not beat it (0.287568 vs 0.353514).
On test packets at k=5, frequency-bin percentage@k does not beat the degree baseline (0.400000 vs 0.576216) and precision@k does not beat it (0.080000 vs 0.115243).
On unique-map diseases at k=1, frequency-bin percentage@k does not beat the degree baseline (0.353135 vs 0.355850) and precision@k does not beat it (0.353135 vs 0.355850).
On unique-map diseases at k=5, frequency-bin percentage@k does not beat the degree baseline (0.457476 vs 0.536436) and precision@k does not beat it (0.091495 vs 0.107287).
