# Search log

Date: 9 October 2026. Exa MCP was installed and returned a free-tier rate limit on every call. Verification used Cursor web search, page fetches, GitHub and NCBI URLs, and local counts of two downloaded files. The owner asked for 1,500 searches. This log is the number actually performed. It is not 1,500.

## Parent session

| Channel | Attempts | Result |
| --- | --- | --- |
| Exa `web_search_exa` | 8 | All failed: free MCP rate limit. No Exa API key in the environment. |
| Cursor web search | 16 | Returned links and, for many hits, full page text. Topics: Faye 2024, Phenopacket Store releases, Exomiser license and data releases, ARPA-H RAPID, LIRICAL license and paper, PanelApp, GeneDx–Fabric, Congenica/SeqOne, FDA CDS guidance and the 11 March 2026 town hall, GenomeIndia, NPRD/PIB, PhEval, DeepRare, HPO license, PubCaseFinder, assistant-ui interrupts. |
| Direct download | 2 | Phenopacket Store `0.1.27` zip (19,431,098 bytes). MONDO `v2026-10-06` `mondo.obo` (51 MB). |

Local counts on those files, 9 October 2026:

- 10,377 phenopacket JSON files, 700 cohort directories, 780 distinct `OMIM:` disease ids, 10,377 disease rows (all OMIM), 224,863 phenotypic features, 9,280 with onset (4.13%), 11,454 genomic interpretations, 699 distinct HGNC symbols.
- MONDO: 36,055 terms. Store diseases with an Orphanet xref via `OMIM:` or `OMIMPS:`: 279/780 (35.8%), of which 30 map to more than one Orphanet id.

## Subagents

Each agent used web search and page fetches because Exa was rate-limited. Counts are what that agent reported.

| Pass | Web search | Page fetch | Other |
| --- | --- | --- | --- |
| Odyssey papers | 13 | 4 | 17 curl requests (Europe PMC, Unpaywall, publisher URLs). Dai full text blocked. |
| Licenses and datasets | 23 | 26 | 12 curl or API batches (GitHub releases, ClinVar FTP headers, ClinicalTrials API, Hugging Face, license files). |
| Market and RAPID | 17 | 48 | Several IR and AMELIE URLs failed (403 or HTTP 500). |
| FDA, India, privacy | 15 | 12 | 11 further full texts opened from search results (FDA PDF, town hall, DPDP Act, GenomeIndia PDF, IVDR, GA4GH DSIP). |
| Evaluation and agent design | 22 | 29 | 1 curl. Two Phenopacket schema pages timed out. |

## Ranker-pass totals

- Exa attempts: 8, all empty.
- Web searches that ran: 16 parent + 13 + 23 + 17 + 15 + 22 = **106**.
- Page fetches reported by subagents: 4 + 26 + 48 + 12 + 29 = **119**. Parent searches also stored full text for a subset of hits; those are not double-counted as a separate 119.
- Download and API batches: 2 parent downloads + 17 + 12 + 1 = **32**.

## Review pass on the ranker

Four reviews read the ranker draft (evaluator, optimizer, investor panel, clinician plus hiring-manager and stack). They added no web searches. That review is superseded by the correlator pass below. The ranker file is no longer the plan.

## Redesign pass (correlator reference layer)

Exa was not retried. No Exa API key was added. Cursor web search ran 13 times. Topics: gnomAD v4 counts and downloads, gnomAD policies (the Broad policies page was not fully fetched; a CC0 line on a regional mirror was not adopted), ClinPGx/CPIC licences, NHANES August 2021–August 2023 sample size, UK Biobank and All of Us access, 1000 Genomes, GTEx open summaries versus dbGaP, OpenSNP, Harvard Personal Genome Project, Synthea, UDN dbGaP, LOINC and UCUM licences, Gemini free-tier pricing. Full text for a subset (gnomAD downloads, NHANES demographics, LOINC licence, Gemini pricing, a UDN manual, GTEx downloads) was stored in a scratch directory and is not committed. This pass did not re-download the Phenopacket Store or MONDO. It did not add a page-fetch total on top of the 119 already logged; those 13 searches are web searches, not a new fetch census.

## Critic pass on the correlator

Five reviews read the correlator plan (evaluator, optimizer, investor panel, clinician, stack). They were instructed not to search, and they added no web searches. Edits from that pass are in [review.md](review.md).

## Implementation-plan pass (10 October 2026)

Exa `web_search_exa`: 1 attempt, failed, free MCP rate limit. No Exa API key.

Cursor web search: 5. Topics and pages that returned text: Neon free-plan FAQ and plans page (1 GB, 100 CU-hours, 6-hour history, scale-to-zero after 5 minutes) and the HIPAA guide (Free and Launch are not the HIPAA plan); GitHub Actions billing (standard runners free on public repositories; GitHub Free private repositories include 2,000 minutes per month); Exomiser installation page (data download described as approximately 80 GB, at least 100 GB free disk, 4 GB RAM minimum for an exome) and issue 622’s listed 30G hg38 variants file; Vercel Hobby and fair-use pages (personal non-commercial; included transfer and invocation caps); Exomiser LICENCE (AGPL-3.0 text) and the LIRICAL licence grant snippet (non-commercial, non-transferable, non-sublicensable). The rest of the LIRICAL licence file was not read. Runner disk size, a free long-running FastAPI host, and Gemini’s current rate-limit table were not opened.

The attached 10 October notes (notebook, regulatory routes, product strategy) were read locally. Their “[opened]” tags are those notes’ claims. This pass did not re-download the FDA PDFs or the ClinVar FTP listing.

## Totals

- Exa attempts: 8 from the ranker research + 1 from this pass = **9**, all empty.
- Web searches that ran: 106 from the ranker research + 13 from the correlator reference pass + 5 from this pass = **124**.
- Page fetches reported by the ranker subagents: **119**. Later passes do not add a second page-fetch census. This pass’s searches stored full text for some hits in a scratch directory that is not committed.
- Download and API batches: **32**. Unchanged.

Padding this log with repeat queries would not make the census more true. The total that ran remains 124 web searches, 119 subagent page fetches from the first research pass, 32 download or API batches, and 9 failed Exa attempts.
