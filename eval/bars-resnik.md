# Resnik best-match average, held-out once

For research use only. Not for use in diagnostic procedures.

The public-case ranker was chosen on fit and validation before this file was written. The winner is resnik_bma. Abstention is raw: a best score at or below zero abstains, and a positive tie does not. That mode was the fit-split choice. The degree baseline keeps its published rule: best score at or below zero, or at least 10 diseases tied at the best score. Other candidates were not scored on this split. phenotype.hpoa was not loaded. en_product6 was not loaded.

The synthetic notebook card stays the frequency-bin comparison. These rows do not replace that card. The five synthetic stories stay on that card.

store_sha256: d0c70005bb09b87035087516252b6b539fbc0415be7c664b73c9cde7eedf205a
unique_map_diseases: 249
test_packets: 925
diseases_with_a_test_packet: 165

## Why frequency-bin loses to the degree baseline

Measured on train packets only. Test packets were not in this loop. The shipped frequency-bin scorer does not receive a parent map. A missing row contributes a ratio of 1. A listed bin whose lower bound sits below the corpus background scores below a missing row. Abstentions are misses. Climbing to a parent inside that product was measured here on the train split and is not shipped.

| train check | k | hits | denominator | percentage@k |
| --- | --- | --- | --- | --- |
| frequency_with_abstention | 1 | 1129 | 3890 | 0.290231 |
| frequency_with_abstention | 5 | 1501 | 3890 | 0.385861 |
| frequency_ranked_anyway | 1 | 1172 | 3890 | 0.301285 |
| frequency_ranked_anyway | 5 | 1983 | 3890 | 0.509769 |
| frequency_parent_climb_ranked_anyway | 1 | 717 | 3890 | 0.184319 |
| frequency_parent_climb_ranked_anyway | 5 | 1374 | 3890 | 0.353213 |

Train packets whose truth disease has lower ratio 0: 18 / 3890.
Train query terms: 33952. Exact annotation on the truth disease: 11862. Additional ancestor relation: 12650.

## Held-out packets

percentage@k is hits over the test-packet denominator. Abstentions are misses. precision@k is the mean of 1/k on a hit and 0 on a miss. Ties take the worst rank.

| tool | k | hits | denominator | percentage@k | precision@k |
| --- | --- | --- | --- | --- | --- |
| resnik_bma | 1 | 419 | 925 | 0.452973 | 0.452973 |
| resnik_bma | 5 | 614 | 925 | 0.663784 | 0.132757 |
| degree | 1 | 327 | 925 | 0.353514 | 0.353514 |
| degree | 5 | 533 | 925 | 0.576216 | 0.115243 |

Disease rows are the unweighted mean of each disease's test-packet rate. A unique-map disease with no test packet is left out of this mean. 165 of 249 unique-map diseases have a test packet.

| tool | k | diseases_in_mean | percentage@k | precision@k |
| --- | --- | --- | --- | --- |
| resnik_bma | 1 | 165 | 0.480944 | 0.480944 |
| resnik_bma | 5 | 165 | 0.665217 | 0.133043 |
| degree | 1 | 165 | 0.386210 | 0.386210 |
| degree | 5 | 165 | 0.553540 | 0.110708 |

## Comparison

On test packets at k=1, resnik_bma percentage@k beats the degree baseline (0.452973 vs 0.353514) and precision@k beats it (0.452973 vs 0.353514).
On unique-map diseases with a test packet at k=1, resnik_bma percentage@k beats the degree baseline (0.480944 vs 0.386210) and precision@k beats it (0.480944 vs 0.386210).
On test packets at k=5, resnik_bma percentage@k beats the degree baseline (0.663784 vs 0.576216) and precision@k beats it (0.132757 vs 0.115243).
On unique-map diseases with a test packet at k=5, resnik_bma percentage@k beats the degree baseline (0.665217 vs 0.553540) and precision@k beats it (0.133043 vs 0.110708).

The held-out packet bar beats the degree baseline at both k=1 and k=5 on percentage@k and precision@k.

## Decoy gene

A gene symbol was added to each test packet and the case was rebuilt. The ranker is called with present HPO ids only.

packets: 925
hpo_unchanged: 925
decoy_gene_recorded: 925
scores_unchanged: 925
rebuild_failures: 0
