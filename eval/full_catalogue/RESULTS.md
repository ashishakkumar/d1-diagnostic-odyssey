# Full-catalogue ranker on Phenopacket Store 0.1.27

For research use only. Not for use in diagnostic procedures. Script: `eval/full_catalogue/run.py`.

Ranker: Resnik best-match average, information content from phenotype.hpoa (2026-09-02), over all
12,867 diseases (OMIM, Orphanet, DECIPHER). Inputs are the packets' gold HPO codes, excluded
codes are used as absent findings. Truth is the packet's OMIM id. Ties take the worst rank.
Split: SHA-256(packet id) mod 5 == 0 is test.

| split | packets | top-1 | top-5 | top-10 | median rank |
| --- | --- | --- | --- | --- | --- |
| test | 2,106 | 0.338 | 0.568 | 0.661 | 3 |
| all | 10,345 | 0.342 | 0.573 | 0.661 | 3 |

32 packets skipped (no OMIM id in the catalogue or no usable present code).

Absent-finding penalty: subtract ABSENT_WEIGHT x mean IC of absent findings that a disease lists
at >= 80% frequency. On 1,200 train packets: weight 0 gave top-1 0.365 / top-5 0.588, 0.05 gave
0.354 / 0.578, and penalising every listed annotation at 0.5 collapsed to 0.05 / 0.09. The app uses
0.05: the penalty costs about one point on these packets, kept because a clinician's "no X" should
count. Not tuned on the test split.

Caveats: this is not comparable with the earlier 249-disease result (45.3% top-1), which ranked a
much smaller Orphanet-mapped set. phenotype.hpoa is partly curated from the same publications as
the packets, so these numbers are likely optimistic. Inputs are gold codes, not free text; see
eval/extraction/RESULTS.md for the extraction loss.

## Weak-signal flag (2026-10-13)

Flag fires on: fewer than two present findings, top score < 1.5, a tie, top-5 relative spread
(top1 - top5) / top1 < 0.03, or every present term has IC < 4.0 (all common). Thresholds chosen on
train (eval/full_catalogue/abstain.py), reported on test.

| rule | split | packets | flagged | top-1 when flagged | top-1 when not flagged |
| --- | --- | --- | --- | --- | --- |
| old (n<2, top<1.5, tie) | test | 2,106 | 5.9% | 6.5% (124) | 35.5% |
| new | test | 2,106 | 15.6% | 5.2% (328) | 39.1% |
| new | train | 8,239 | 15.1% | 6.1% | 39.3% |
