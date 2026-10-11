# What these results can claim

For research use only. Not for use in diagnostic procedures.

## Can claim

- A method result on public Phenopacket Store cases: whether the published disease was in the top 1, top 3, or top 10 among diseases with one Orphanet id.
- How many diseases were excluded because they do not have a unique Orphanet id.
- How often the method returned no confident score on those public cases.
- The tool name and the pinned data versions for that run.

## Cannot claim

- A benefit to a real patient.
- The probability that a person outside this public set has a disease.
- A diagnosis, a test, or a treatment.
- That a reported gene produced the rank. The scorer is never given the true gene. Gene-level metrics are evaluation-only and are not in the disease table.
- That a packet timestamp is a new patient. The time-split note uses the packet created field, which is not a publication date.
