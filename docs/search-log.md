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

## Totals

- Exa attempts: 8, all empty.
- Web searches that ran: 16 parent + 13 + 23 + 17 + 15 + 22 = **106**.
- Page fetches reported by subagents: 4 + 26 + 48 + 12 + 29 = **119**. Parent searches also stored full text for a subset of hits; those are not double-counted as a separate 119.
- Download and API batches: 2 parent downloads + 17 + 12 + 1 = **32**.

## Review pass

Four reviews read the draft plan (evaluator, optimizer, investor panel, clinician plus hiring-manager and stack). They added no web searches. Plan edits from that pass are in [review.md](review.md).

Padding this log with repeat queries would not make the census more true. The total that ran remains 106 web searches, 119 subagent page fetches, 32 download or API batches, and 8 failed Exa attempts.
