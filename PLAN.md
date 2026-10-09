# Plan: a longitudinal rare-disease case file

Status: plan only. No application code, schema migration, or service is in this repo. Nothing is built until the owner approves this plan.

This is one portfolio repo. It is a years-long diagnostic-odyssey case file. It is not a clinic-workflow closer. Prior authorization, medication reconciliation, nodule follow-up, and trial screening end in a packet a person can submit. This repo ends in a new immutable snapshot and a score list a person can compare with the previous snapshot. The screen says it is not a diagnosis. The human accepts every phenotype before a score is stored.

Checked against primary pages and against Phenopacket Store release `0.1.27` and MONDO `v2026-10-06` downloaded on 9 October 2026. Search counts are in [docs/search-log.md](docs/search-log.md). They are not 1,500.

## 1. Problem and impact

### Who has the pain

A person with a rare disease, their family, and the clinician who keeps the chart between visits. The chart is not one note. Phenotype is added, a gene panel comes back negative, a paper names a new gene, ClinVar moves a variant, and someone has to notice.

Faye et al., *European Journal of Human Genetics* (2024), surveyed 6,507 people with a confirmed diagnosis, living with 1,675 rare diseases in the abstract and 1,684 in the methods, across 41 European countries ([PMC11369105](https://pmc.ncbi.nlm.nih.gov/articles/PMC11369105/), [doi:10.1038/s41431-024-01604-z](https://doi.org/10.1038/s41431-024-01604-z)).

- Mean total diagnosis time 4.7 years. Median 0.8 years (IQR 0.1–5.0). The mean is not a typical wait. The distribution is skewed, and about 90% of the mean is time after the first medical contact.
- 73% (4,756/6,507) were misdiagnosed at least once. The paper’s definition is wider than a wrong disease name: symptoms attributed to another physical disease, neglected, not taken seriously, or considered psychological.
- The sample is people who already have a diagnosis and who answered a retrospective survey. Undiagnosed people are absent. Recruitment mixes a Rare Barometer panel and social media. Those limits are in the paper.

Nguengang Wakap et al. counted 6,172 Orphanet diseases, 71.9% genetic, and a conservative point prevalence of 3.5–5.9% ([doi:10.1038/s41431-019-0508-0](https://www.nature.com/articles/s41431-019-0508-0)). That prevalence is of diseases in the catalogue, using the European threshold, and it excludes rare cancers, infections, and poisonings. It is not “6,172 patients.”

The case for keeping a chart after the first test is the undiagnosed fraction, not the survey mean. Chung et al., *Genetics in Medicine* (2023), report diagnostic rates of 0.38 for exome (126 studies, 38,277 probands) and 0.34 for genome (40 studies, 11,207 probands), inside an eligible set of 50,417 probands ([doi:10.1016/j.gim.2023.100896](https://doi.org/10.1016/j.gim.2023.100896)). Most people remain undiagnosed after the test. Faye’s median wait is 0.8 years; the 4.7-year mean is the skew, driven by a long tail. The 73% misdiagnosis figure counts four categories in the paper: symptoms attributed to another physical disease, neglected, not taken seriously, or considered psychological. How many of the 4,756 received a different disease name is not broken out. A wrong name at rank 1 on this screen would be a harm the screen itself can create, which is why the header says the list is not a diagnosis. ARPA-H’s RAPID announcement says the odyssey “lasts six years on average.” This plan does not adopt that sentence. Faye’s median and Chung’s yields are the figures it uses.

Reanalysis finds some of the rest, and the yield depends on the denominator. Dai et al. pooled an overall diagnostic yield of reanalysis of 0.10 (95% CI 0.06–0.13) and wrote that literature updates accounted for most new diagnoses ([doi:10.1016/j.gim.2022.04.021](https://doi.org/10.1016/j.gim.2022.04.021)). The figure of 60% is not in that paper’s abstract. It is in a companion meeting abstract (GiméP338, [S1098-3600(22)00390-2](https://www.gimjournal.org/article/S1098-3600(22)00390-2/fulltext)). Single cohorts are higher because they report cumulative yield, not the yield among only the unsolved: Wright et al. moved 1,133 DDD trios from 27% to 40% ([PMC5912505](https://pmc.ncbi.nlm.nih.gov/articles/PMC5912505/)); Liu et al. (first author Liu, second author Meng) moved a 250-person manual cohort from 24.8% to 46.8% ([PMC6934160](https://pmc.ncbi.nlm.nih.gov/articles/PMC6934160/)); Schobers et al. moved 150 pediatric neurology patients from 31% (47/150) to 53% (79/150) ([doi:10.1186/s13073-022-01069-z](https://doi.org/10.1186/s13073-022-01069-z)). Newer work does not replace Dai or Chung. Solve-RD systematic reanalysis found 506/6,004 families (8.4%), plus 4.1% from ad hoc review ([doi:10.1038/s41591-024-03420-w](https://www.nature.com/articles/s41591-024-03420-w)). An automated Talos reanalysis found 241/4,735 (5.1%) ([doi:10.1038/s41591-026-04477-5](https://www.nature.com/articles/s41591-026-04477-5)). A commercial biannual reanalysis moved one lab cohort only from 18.3% to 20.4%.

### Why a case file, not another ranker

Phenomizer (Köhler et al., *AJHG* 2009, [PMC2756558](https://pmc.ncbi.nlm.nih.gov/articles/PMC2756558/)) ranks diseases from HPO semantic similarity and stops. LIRICAL (Robinson et al., *AJHG* 2020, [PMC7477017](https://pmc.ncbi.nlm.nih.gov/articles/PMC7477017/)) adds a likelihood ratio and, with a VCF, a gene rank. On 384 published case reports, phenotype-only top-3 was 43.7% for LIRICAL and 35.3% for Phenomizer. The 92.9% top-3 figure is gene rank with genotype spiked in, against Exomiser at 92.2%. Phrank (Jagadeesh et al., *Genetics in Medicine* 2019) on 169 solved exomes, after both methods were restricted to diseases explained by the patient’s candidate genes, put the true disease about 3 places ahead of the truth (top-10 recall 64.5%) versus about 32 for Phenomizer. Exomiser’s hiPHIVE path also uses mouse, zebrafish, and protein-interaction data (Smedley et al., [PMC5467691](https://pmc.ncbi.nlm.nih.gov/articles/PMC5467691/)). DeepRare (Zhao et al., *Nature*, 2026, [doi:10.1038/s41586-025-10097-9](https://www.nature.com/articles/s41586-025-10097-9)) is a multi-agent LLM system. The paper reports average HPO Recall@1 of 57.18% and, on 168 Xinhua whole-exome cases, 69.1% versus Exomiser 55.9%. Those numbers are not a bar this repo should chase: correctness of the rank was judged with GPT-4o, the cases are published or private hospital sets, the article is CC BY-NC-ND, and the GitHub license is `NOASSERTION`. An LLM that has read the case report can look accurate.

What a public repo can add, without becoming one of those products, is a record around a score: time-ordered snapshots, a human acceptance of each HPO draft, a score recomputed in code when an accepted phenotype changes, a ClinVar row that does not enter the score, and a trial link that stores the query and does not say “eligible.” An unpublished file is not evidence that a buyer is waiting.

### Companies, and why this slice is still worth a public repo

Commercial products sell a test or a lab workstation. GeneDx sells exome and genome tests and includes reanalysis in the test price; it bought Fabric Genomics for about $33 million cash at closing (agreement 15 April 2025, closed 7 May 2025), with milestones that can take the total toward $51 million ([SEC 8-K](https://www.sec.gov/Archives/edgar/data/1818331/000181833125000057/wgs-20250415.htm), [completion release](https://ir.genedx.com/news-releases/news-release-details/genedx-announces-completion-fabric-genomics-acquisition)). Fabric GEM, Illumina Emedgene, Geneyx, 3billion EVIDENCE, CentoCloud, and SeqOne (which announced a definitive agreement to acquire Congenica on 2 September 2025; GenomeWeb reported the deal as closed that day; price undisclosed) interpret a VCF inside a lab. Face2Gene phenotypes from photos; a 2020 product sheet priced extra next-generation phenotyping at $50 a case. Probably Genetic collects patients and orders tests. SimulConsult reruns a Bayesian dashboard as findings change, on annotated variant tables, in a proprietary session. Phenomizer is the public one-shot ranker. None of them is an append-only Phenopacket history a stranger can re-score.

Invitae filed Chapter 11 on 13 February 2024. Labcorp bought selected assets for $239 million; the sale closed 5 August 2024 ([8-K](https://www.sec.gov/Archives/edgar/data/1501134/000119312524196195/d859163d8k.htm)). That is a lab winding down, not a case-file product leaving the market.

ARPA-H RAPID, announced 31 August 2026, will invest up to $98.5 million over 4.5 years ([announcement](https://arpa-h.gov/news-and-events/arpa-h-announces-awards-advance-ai-rare-disease-diagnosis-and-treatment)). The page says the diagnostic odyssey “lasts six years on average.” Award pages name four performers: UNC up to $34.9 million (dataset; PI Melissa Haendel; start 8 September 2026), Sage Bionetworks up to $28.2 million (benchmarking platform), FDNA up to $9.9 million (photos, video, voice), Probably Genetic up to $9.9 million (patient collection and synthetic data). Those four caps sum to $82.9 million. The announcement also names Lawrence Berkeley, NIH All of Us, the Monarch Initiative, and in-kind compute, without splitting the remaining $15.6 million. RAPID is funding shared data and benchmarks, and patient-facing collection. It is not funding this repository. This repo does not pretend to be that data commons.

Investors who write about healthcare AI are funding labor that already has a buyer. None of the following would fund a company from this plan, and the plan does not ask them to.

- a16z Bio+Health has treated rare disease as a biotech market and exome-scale sequencing as an early use case ([2021](https://a16z.com/its-time-to-heal-16-trends-driving-the-future-of-bio-and-healthcare/)). The 2023 jobs-to-be-done essay is prior-authorization hours. This repo does not upload a VCF and does not take a labor contract.
- General Catalyst’s recent public healthcare notes that were opened are care delivery and trial operations that enroll patients. A trial row that must not say “eligible,” and a FHIR Bundle that stays on disk, are not that business.
- Bessemer’s 22 January 2026 essay describes services-as-software and says providers are paid for procedures and visits, not for an AI-generated diagnosis ([Bessemer](https://www.bvp.com/atlas/state-of-health-ai-2026)). That essay does not mention rare disease or phenotype ranking.
- Menlo’s 21 October 2025 essay does not mention them either. It is about administrative follow-up and scribing.
- Oak HC/FT’s line is end-to-end process ownership rather than a chat wrapper. A score list is not that process.
- RAPID’s money is a dataset, a benchmarking platform, photos and voice, and patient collection. This repo writes a PhEval-shaped TSV and prints denominators. That file is not a RAPID deliverable, and this plan does not claim it will satisfy a benchmark Sage has not published.

A lab session, a reanalysis report, and an ACMG worksheet are different objects. This repo adds three fields those products do not publish as a rerunnable demo: an immutable snapshot, a human accept before a new score is stored, and the query string stored on the trial row. GeneDx and Ambry already fold reanalysis into the price of a test. This demo does not bill and does not own a lab.

The portfolio reason to build it is that the engineering problem is real, the public corpora exist, and the evaluation can be strict. It is not a company. The 418-posting sample and the course list in section 8 decide which protocols are honest to mention. They decide nothing about the scorer, the accept gate, or the tables.

### India

The National Policy for Rare Diseases (2021) does not set a prevalence cutoff. It groups diseases by whether treatment is one-time, long-term and cheaper, or long-term and very expensive. The policy text caps central support at Rs 20 lakh for Group 1, under Rashtriya Arogya Nidhi, for people covered by Pradhan Mantri Jan Arogya Yojana norms, described there as about 40% of the population, at government tertiary hospitals ([policy PDF](https://www.tdb.gov.in/sites/default/files/2025-01/nprd-2021.pdf)). A PIB release of 29 July 2022 states support up to Rs 50 lakh for any category, at a Centre of Excellence, outside that umbrella ([PRID 1846230](https://www.pib.gov.in/Pressreleaseshare.aspx?PRID=1846230)). A PIB release of 9 August 2024 states 63 diseases, up to Rs 50 lakh per patient, 1,118 patients helped, and twelve Centres of Excellence ([PRID 2043516](https://www.pib.gov.in/PressReleaseIframePage.aspx?PRID=2043516)). The policy pays for treatment. It does not procure a phenotype ranker.

GenomeIndia is a healthy reference, not a patient cohort. The *Nature Genetics* comment (8 April 2025, [doi:10.1038/s41588-025-02153-x](https://doi.org/10.1038/s41588-025-02153-x)) describes whole genomes of about 10,000 healthy unrelated people from 83 populations. The author PDF says 10,074 individuals were sequenced and 9,772 were retained after joint-genotyping QC. The project insights page says 9,768 passed QC. The project FAQ says sequencing data for 9,648 samples are archived. A 30 April 2025 PIB says FASTQ and gVCF for 9,772 samples are archived at IBDC and that FASTQ will not be available for download. Access is controlled under Biotech-PRIDE. This repo does not request, store, or simulate those genomes. A frequency prior from GenomeIndia would matter later, inside an approved project. It is not a file in git.

ABDM is the national exchange: a Health Information Provider sends a record to a Health Information User with the person’s consent. The NRCeS FHIR IG v6.5.0 profiles include DiagnosticReport, DischargeSummary, OPConsult, Prescription, Condition, and Patient. No profile in that list is a rare-disease or Phenopacket profile ([NRCeS](https://nrces.in/ndhm/fhir/r4/)). A case file does not sit on ABDM in v1.

The ICMR registry page (NRROID) says it was initiated in November 2019, lists six disease categories, 19 centres, and “over 4,000 cases.” A 2025 preprint snippet with larger counts was not opened. Use the live page.

The Digital Personal Data Protection Act, 2023, defines personal data as data about an identifiable person. Health data is not a separate class in the Act text that was opened. A purely synthetic case is the intended content of this repo. Whether a public GitHub demo is outside the Act, and whether the operative sections are in force before the notified commencement (a reprint of G.S.R. 843(E) points at 13 May 2027), is for a lawyer. This plan is not legal advice.

An India-shaped demo is a documentation section plus global ontologies. The UI can show a synthetic odyssey beside the fact that NPRD pays for treatment at a Centre of Excellence and does not procure this screen. A Centre of Excellence pilot would be a new project with a data agreement. Job ads in the owner’s India-skewed sample ask for Python agents and evaluations. That is a hiring fact. It is not evidence that Indian hospitals are buying this screen, and it does not choose the score function.

## 2. Solution

### Workflow

One case. Many snapshots. The model never writes the rank.

1. A reviewer pastes a synthetic note, or loads the next authored note in a demo case.
2. A drafter proposes HPO terms. Each draft has the term id, the label, present or excluded, and a character span. The span must be a substring of the note. If it is not, the draft is dropped.
3. The graph pauses. The reviewer accepts, edits, or rejects each draft. Nothing is stored as a phenotype before that.
4. On accept, the service appends an immutable Phenopackets v2 snapshot. It does not edit the previous JSON.
5. A Python function scores diseases from the accepted HPO ids and the pinned Orphanet files. The score list is stored inside the new snapshot. The screen orders diseases by that score. Gene scores are computed the same way for the evaluation file. They are not the headline of the page.
6. The Questions tab lists at most five HPO terms. A term qualifies when toggling it present versus excluded changes which disease is score-order 1, under the same function, and the chart has neither accepted nor excluded it. Intellectual disability, global developmental delay, seizure, hypotonia, short stature, failure to thrive, and their direct parents are never suggested. If the case is “no confident score,” the tab is empty. Genes are not on this tab. A separate line under the differential can name Orphanet genes of the top disease that the human has not typed. That line is not an order.
7. A separate fetch records ClinVar for HGVS strings the human typed: classification, review status, accession, date. The score function does not read that row. Reanalysis stores the score list from before the fetch and the score list after it. The test asserts they are identical, including when the classification moves from variant of uncertain significance to pathogenic or the other way. The visible “rank diff” for ClinVar is that recorded zero. A phenotype acceptance is what produces a non-zero diff, and the timeline shows it.
8. Trial links are a ClinicalTrials.gov query stored with the query text, the NCT id, the title, and `overallStatus`. The screen does not say eligible. One synthetic case freezes an off-target hit with the query visible.
9. Similar-patient matching is not implemented. The screen says it stays off until a trusted Matchmaker Exchange node exists. There is no token, no patient JSON, and no outbound match call.
10. After the same approval, a FHIR transaction Bundle is written to disk: `Patient`, plus one `Observation` per accepted HPO term. No `Condition`, so a downstream server cannot read the score order as a diagnosis. `If-None-Exist` is used only when `FHIR_BASE_URL` is set. The default demo does not construct an HTTP client. A test fails if one is constructed while that variable is unset.

No model summary sits beside the differential. A test that feeds the scorer a free-text summary, a disease label, or a PMID asserts the score list does not change.

### What is code, and what is a model

| Step | Implementation |
| --- | --- |
| Disease score, score diff, next question | Python. Orphanet frequency bounds and the HPO graph. No model. |
| HPO draft from a note | Gazetteer of HPO labels and synonyms, with a negation window (`no`, `denies`, `without`). This path needs no API key. An optional LangChain chat model may propose additional drafts. Same span rule. The gazetteer is the committed baseline. |
| Literature sentence | Only inside the literature service. A sentence is kept if it is a substring of the fetched open-access text and the DOI or PMID resolves. It is attached to a disease row as evidence. It does not reorder the row. |
| ClinVar, trials, MONDO crosswalk | HTTP or a pinned file. Pure functions. |
| Diagnosis, ACMG class, “order this test,” “enroll” | Not produced. |

### Scorer v1, and the corpus fact that constrains it

Phenopacket Store `0.1.27` was downloaded on 9 October 2026 (zip 19,431,098 bytes, release 9 June 2026, Zenodo [10.5281/zenodo.20614899](https://zenodo.org/records/20614899)).

- 10,377 phenopacket JSON files, 700 cohort directories.
- 10,377 disease rows, all `OMIM:` ids, 780 distinct diseases.
- 11,454 genomic interpretations, 699 distinct HGNC symbols. Every packet has an interpretation. Genes are at `variantInterpretation.variationDescriptor.geneContext`, not on a top-level gene list.
- 224,863 phenotypic features, of which 9,280 (4.13%) have an onset. Progressive disclosure by onset will be thin. Report the denominator.

MONDO `v2026-10-06` (`mondo.obo`, 51 MB, 36,055 terms) maps a store disease id to at least one Orphanet xref for 279 of 780 diseases (35.8%) if both `OMIM:` and `OMIMPS:` are tried. 30 of those hit more than one Orphanet id, so 249 of 780 have a unique Orphanet id. Noonan syndrome 3 (`OMIM:609942`) and Cornelia de Lange syndrome 3 (`OMIM:610759`) do not appear in that obo file at all. An Orphanet disease score cannot be judged against the other 531. The setup script recomputes the 249 and also prints how many of those ids occur in the pinned Orphanet frequency and gene files. This paragraph is not the fixture.

The screen shows disease score order, with the unmapped and multi-mapped counts in the header when the case has an OMIM id. The public benchmark prints two numbers, each with its denominator:

1. **Disease score, on the unique-map subset only.** Truth is that one Orphanet id. Packets outside the 249 are excluded, and the exclusion count is printed beside the metric. This is what the screen shows.
2. **Gene score, evaluation only, from HPO ids alone.** The packet’s HGNC symbol is the label, never an input. The run fails if adding that symbol changes the reported scores. A gene is the best Orphanet disease that `en_product6` links it to. Every causative symbol in the 11,454 interpretations is a row. A gene missing from `en_product6` stays in the denominator and is treated as not returned. Ties take the worst rank in the tie.

The likelihood ratio follows Robinson et al. in structure. Orphanet bins, as documented on the HPO frequency page: obligate 100%, very frequent 80–99%, frequent 30–79%, occasional 5–29%, very rare 1–4%, excluded 0%. v1 evaluates the ratio at the bin’s lower bound and at its upper bound. The stored score and the PhEval file use the lower bound. The row is marked unstable when score-order 1 differs between the two bounds. A missing frequency contributes LR 1, the row shows “frequency missing,” and the metric table reports what fraction of the top 10 those rows are. LIRICAL’s default of treating a missing frequency as “always present” is not copied. The 1/1000 floor applies only when the patient has a term the disease annotation marks excluded. A patient negation of a nonspecific term is stored and left out of the ratio. A patient term matches an annotated term or an ancestor. When the patient term is more specific than the annotated term, the frequency is divided by the number of direct children, which is LIRICAL’s rule. Taking the maximum frequency among descendants is not used. It inflates the disease that was annotated with a child term the patient did not have.

This loses, relative to Exomiser hiPHIVE: mouse and zebrafish phenotypes, STRING random walks for genes with no human phenotype, variant pathogenicity, and inheritance filtering. It also loses OMIM’s finer disease splits wherever Orphanet lumps genes into one clinical entity. The Exomiser data bundle stays out. The 2602 phenotype release includes OMIM dated 12 February 2026, and the genomic archives are on the order of tens of gigabytes. SpliceAI in that bundle is free for academic and not-for-profit use only. The code is AGPL-3.0. v1 does not vendor it and does not shell out to it.

The runnable baseline ranks each gene by how many Orphanet diseases it is linked to, and ranks each disease by how many genes it is linked to. The likelihood ratio is reported as an improvement only when full-store percentage@k and precision@k both beat that baseline. A random gene that shares one HPO id is a second, weaker baseline. Resnik’s Monte Carlo p-value stays a citation of Phenomizer. It is not on the stranger-run path. Phrank is cited, not reimplemented. Phen2Gene’s code is MIT, and its knowledge base is not committed. PubCaseFinder may be called as an external baseline. Mined case-report text is not stored. LIRICAL is not run. The 43.7% figure stays a citation.

“No confident score” is not a cutoff fit to the five cases. It is fixed here, before any score is inspected: at least 10 diseases lie within a factor of two of the best lower-bound likelihood ratio, or score-order 1 changes between the bin bounds. The Questions tab is then empty. The store’s abstention rate is printed and is not used to edit the rule.

### Agents, and why that protocol

Job ads in the owner’s 418-posting, India-skewed sample ask for MCP far more often than A2A (about 16% versus about 3%). This repo uses A2A in one place because a secret would otherwise sit in the case process, and the README says the ads do not ask for it.

| Piece | Protocol | Why this one |
| --- | --- | --- |
| Case thread | LangGraph, in the FastAPI process | One `thread_id` per case. `interrupt()` pauses for acceptance. The node restarts from the top on resume, so the snapshot insert and the Bundle write sit after `interrupt()` returns. Checkpointer: `AsyncPostgresSaver` on the same Postgres as the cases, via `DATABASE_URL`. Compose provides that database. Neon’s direct host is a drop-in later; its pooler is transaction-mode PgBouncer and is the wrong string for the saver (`prepare_threshold=0` on the direct host). Durability `sync` still checkpoints at super-steps, not mid-node. |
| HPO, Orphanet frequency, MONDO xref, keyless ClinVar `esummary` | MCP, in-process, no credentials | Same API process. Stateless tools over pinned files on disk and public E-utilities (3 requests/second without a key, 10 with a key, [NBK25497](https://www.ncbi.nlm.nih.gov/books/NBK25497/)). A separate MCP container is not required to show the protocol. Tool annotations are hints. The human gate is LangGraph, not an MCP elicitation. MCP elicitation must not collect secrets. |
| Literature | A2A server, Compose profile `literature` | Not in the default `docker compose up`. Started when an NCBI key is present, or in fixture mode with a checked-in open-access paragraph and no key. The key, if any, is only in that container. A quote is kept only as a substring of the fetched or fixture text. A non-substring is dropped. Either way the score list is unchanged. Returning an empty evidence list does not depend on the `INPUT_REQUIRED` edge of the spec. |
| Chat model and open-access loaders | LangChain, inside a node or inside the literature service | The model object only. Not a second graph. Not the ranker. |
| Google ADK | Not used | Tool confirmation is experimental and does not support `DatabaseSessionService` or `VertexAiSessionService`. The case thread needs Postgres. The voice courses have no rare-disease lesson. LiveKit is out of scope. |
| Scorer, diffs, next question | No agent | A function. Calling it an agent would make the rank look like a generation. |

There is no swarm. DeepRare’s “more than 40 tools” is the design this plan declines.

### FHIR

v1 writes, after approval, a transaction Bundle to disk:

- `Patient` from the phenopacket subject. Synthetic identifier only.
- `Observation` per accepted HPO term, including an excluded flag.

No `Condition`. The score order stays in the snapshot, not in a resource a server could treat as a diagnosis. `If-None-Exist` runs only when `FHIR_BASE_URL` is set. Otherwise no HTTP client is constructed. Medplum is out of v1. Genomics Reporting is out of v1. No `ServiceRequest`. No `Claim`.

### Human in the loop

The gate is the accept control, which posts `Command(resume=...)` to FastAPI on the case’s `thread_id`. It is not the chat composer. assistant-ui’s LangGraph tutorial part 3 still throws `NodeInterrupt`. The current interrupts page returns `interrupts` from `load()`. agent-chat-ui issues [#85](https://github.com/langchain-ai/agent-chat-ui/issues/85) and [#262](https://github.com/langchain-ai/agent-chat-ui/issues/262) restart the graph when a reply is typed into the chat box. CopilotKit’s FastAPI pages say `useInterrupt` is unsupported there. The stockbroker example still shows the older `interrupt_before` breakpoint. v1 copies none of those as the gate.

`thread_id` is the case, not the patient and not the browser session. Long-term facts (accepted terms, snapshots, ranks) live in the tables below, not only in the checkpoint. `adelete_thread` must not be the way a case is deleted. An audit table remains. If note text is stored, checkpoints use `EncryptedSerializer`. The demo data is synthetic either way.

Parallel interrupts are not used. One payload lists the drafts. Static `interrupt_before` is not used, because resume would pass `None`.

### Safety and regulatory boundaries

This is a research demo. The README and the UI say: “For research use only. Not for use in diagnostic procedures.” That sentence is the RUO label from 21 CFR 809.10(c)(2)(i), as quoted in FDA’s RUO guidance. It is not a claim that the software is a non-device. FDA’s current Clinical Decision Support guidance is the January 2026 final guidance, docket FDA-2017-D-6569, reissued 29 January 2026 ([PDF](https://www.fda.gov/media/109618/download)). A function is non-device CDS only if it meets all four criteria in FD&C Act §520(o)(1)(E). The guidance states that software which processes an NGS sequence or a VCF to identify variants or their clinical implications does not meet Criterion 1. The 11 March 2026 town hall repeats that example ([slides](https://www.fda.gov/media/191561/download)). A geneticist clicking “accept” helps the recommendation criteria. It does not repair Criterion 1.

v1 stays on the near side of that example by refusing VCF upload, refusing to call variants, refusing to emit an ACMG class, and refusing to recommend a drug or a trial. ClinVar text does not enter the score function. A human-typed HGVS is displayed with NCBI’s classification and date, and the stored score diff for that fetch is zero. The score changes when the human accepts a phenotype. Whether FDA would still call the disease list a device is not settled by the pages that were opened. Intended use is objective intent. The label is not a shield if the README tells a clinic to rely on the list. The README tells a clinic not to. Every differential header, including the narrow layout, reads “Highest phenotype score. Not a diagnosis.” The column is “score order.”

HIPAA, on the pages opened, applies to covered entities and business associates. This demo is not one. Real notes, real VCFs, face photographs, and real Matchmaker Exchange payloads are not committed. The Phenopacket Store is a public, BSD-3 corpus of published case reports. It is an evaluation download. It is not the demo database, and it is not “synthetic.”

Matchmaker Exchange service requirements (March 2026) require a real node to deposit cases, connect to at least two peers, match on test data, notify depositors, and attest to the GA4GH Data Security Infrastructure Policy. The join protocol trusts a sender after manual acceptance, via HTTPS and `X-Auth-Token`. A public demo with a published token would be a trusted querier. That is why matching stays off.

EU IVDR Article 1(3)(a) excludes research-use-only products that the manufacturer does not intend for diagnostic examination. The same intent test is in the UK MDR 2002 definition. Promoting the demo as a diagnostic would walk out of that exclusion. The README does not do that.

Faces, voice, and photos are out. FDNA’s RAPID work is that modality. This repo does not compete with it and does not collect it.

## 3. Tech stack

### Backend

Python 3.12, uv, FastAPI, Pydantic v2, LangGraph, a small MCP server (official Python SDK), one A2A service, LangChain only for the optional chat model and for open-access document loading. PostgreSQL. No second agent framework. No CrewAI, no LlamaIndex, no hosted LangSmith.

Layout, when building is approved:

```
apps/web                 Next.js, TypeScript, Tailwind, shadcn, assistant-ui
services/api             FastAPI, LangGraph, scorer, in-process MCP, Bundle writer
services/literature      A2A, Compose profile, off by default
packages/scorer          pure module, imported by tests without FastAPI
eval/                    pins, PhEval TSV, pytest
sql/                     migrations
compose.yaml             api + Postgres
```

There is no `infra/` tree of HCL in v1. Section 6 is the productionization plan, in prose. A hiring-manager review asked to drop assistant-ui. The brief asks for it, so it stays, and it does not own the accept gate. A review asked to drop A2A. The brief requires it where a credential or a separate deployment is the reason. The literature profile is that deployment. Default Compose does not start it, because the score does not need it.

### Frontend

Next.js App Router. shadcn `Table`, `Sheet`, `Badge`, `Tabs`, `Button`, `Input`. There is no shadcn Timeline component. The timeline is a list of snapshots with a date and a one-line diff, built from those primitives. Do not invent an `EvidencePanel` or `InterruptCard` package.

Screens:

- Case list, empty state (“No synthetic case loaded”), error state if the API is down.
- Timeline of snapshots for one case.
- Differential table. Header: “Highest phenotype score. Not a diagnosis.” Columns: disease, score, score order, delta versus the previous snapshot, unstable flag, frequency-missing flag, knowledge-base version. Gene symbols are not this table.
- Evidence sheet: the quote, the span, the Orphanet frequency bin, the reviewer, the ontology versions.
- Tabs: Differential, Questions, Trials, ClinVar.
- Draft review: each proposed term with the highlighted span, and Accept / Edit / Reject. This is the gate.

The note box can be an assistant-ui `Thread` for the draft conversation. Accept, edit, and reject are ordinary form buttons that post `Command(resume=...)` for that case’s `thread_id`. They do not go through the composer, and v1 does not follow tutorial part 3, does not call `load()` to resume, and does not mount agent-chat-ui or CopilotKit. Desktop is a two-column timeline plus table. Below a narrow width the timeline stacks above the table. The evidence sheet becomes a full-screen sheet. The “not a diagnosis” header remains on that layout.

Buggy options called out so they are not “fixed” by accident: assistant-ui tutorial part 3 `NodeInterrupt`; agent-chat-ui #85 and #262; CopilotKit FastAPI interrupts; AI SDK `needsApproval` deprecation (it does not suspend a LangGraph node); ADK confirmation.

### Database

Compose Postgres is the demo database. A Neon free project (1 GB) is the same schema behind `DATABASE_URL` when a cloud database is wanted. LangGraph checkpoints live in schema `lg`. Application tables live in schema `app`. Use the direct Neon host if Neon is used. The pooler will break the saver.

Outline (names, not a migration). The score list lives in the snapshot. Adjacent snapshots are the diff. Separate rank and evidence tables were cut after review.

- `app.case(id, title, synthetic, created_at)` with a check that `synthetic` is true in this demo.
- `app.note(id, case_id, seq, body, authored_at)` synthetic text only.
- `app.hpo_draft(id, case_id, note_id, hp_id, label, excluded, quote, span_start, span_end, status, reviewer, reviewed_at)`. `span_start` is 1-based. A `BEFORE INSERT OR UPDATE` trigger reads `app.note.body` and raises unless `quote = substr(body, span_start, span_end - span_start)`. A column `CHECK` cannot see the other table. The trigger test inserts a match at character 1, a match later in the note, then a mismatched quote and a 0-based span, and expects errors on the last two.
- `app.snapshot(id, case_id, seq, phenopacket jsonb, scores jsonb, hpo_version, orphanet_version, mondo_version, scorer_version, reviewer, created_at)` unique `(case_id, seq)`.
- `app.clinvar_observation(case_id, hgvs, gene_symbol, significance, review_status, accession, fetched_at)`.
- `app.trial_link(snapshot_id, nct_id, title, overall_status, query, fetched_at)`.
- `app.audit(id, case_id, actor, action, at, detail jsonb)`.

Orphanet, the MONDO xref file, and the HPO graph stay as pinned files the scorer reads. They are not loaded into Postgres. `phenotype.hpoa` is not loaded. The annotation guide says IEA rows are parsed from OMIM and that OMIM must be contacted before another product reuses them ([guide](https://obophenotype.github.io/human-phenotype-ontology/annotations/phenotype_hpoa/)).

### Infra

Default Compose is the API and Postgres. The literature profile is off. A managed Postgres, Neon or otherwise, can replace the database later without a second service. GitHub Actions, if added, runs the scorer tests on the five synthetic cases against Compose Postgres. It does not download the 10,377-packet zip on every push.

Already refused, and still refused after review: a second product ranker, Medplum, Langfuse, a vector database, embeddings as the quote check, HAPI in the demo, an ECS module checked in as if it had been applied.

## 4. Data

Synthetic data only in the application database. Public corpora are downloads for evaluation and for the knowledge base, pinned by version and checksum.

| Resource | License and use | Size | In Postgres? |
| --- | --- | --- | --- |
| Five hand-authored odyssey cases | Written for this repo. Not copied from a paper, OMIM, or GeneReviews. | Negligible | Yes |
| Orphadata Science phenotypes and genes (`en_product4`, `en_product6`, July 2026 files dated 23 Jun 2026 on the pages opened) | CC BY 4.0. Cite the version. Do not add restrictions. | 45.67 MB and 21.56 MB as stated on the download pages | No. Pinned files on disk. |
| MONDO `v2026-10-06` xref extract | CC BY 4.0 | obo 51 MB on disk; the xref extract is smaller | No. File on disk. |
| HPO `hp.obo` release `v2026-09-01` | Custom license, not CC BY. The text on [human-phenotype-ontology.github.io/license.html](https://human-phenotype-ontology.github.io/license.html) allows download and use if the consortium is cited, the version is displayed, and the file is not altered. The obo header’s license IRI `https://hpo.jax.org/app/license` returns 404. OBO Foundry does not treat this as CC BY or CC0 (operations call, 17 March 2026). | 10.9 MB | No. Unmodified download on disk. The file is not rewritten. |
| `phenotype.hpoa` | Same HPO terms, plus the OMIM/IEA restriction. Header on the release that was described in research: 8,478 OMIM, 47 DECIPHER, 4,357 Orphanet. | 35.8 MB | No |
| Phenopacket Store `0.1.27` | BSD-3-Clause | zip 19.4 MB; 10,377 packets | No. Eval disk only. |
| RareBench public splits | HF card `apache-2.0`; upstream case rights not restated. Published cases. | about 150 MB | No |
| ClinVar | Attribution if redistributed. Monthly XML is archived; the latest VCV gzip was about 6.0 GB on 1 Oct 2026. | Do not download the XML in v1 | A few `esummary` rows the demo fetches |
| ClinicalTrials.gov API v2 | NLM asks for attribution and, if you redistribute, a statement that the copy is not the live registry. One call on 9 Oct 2026 returned `totalCount` 606,601. | Not bulk-loaded | A handful of links per snapshot |
| ClinGen gene-disease validity, dosage, actionability | CC0, with a requested access date | Small if a later slice needs labels | Not in v1 |
| Exomiser bundle, LIRICAL, OMIM, GeneReviews, DECIPHER, Orphadata Products (centres, patient organisations), PanelApp panel dumps, GenomeIndia, Matchmaker Exchange records | Not licensed for this public repo | — | No |

PanelApp’s software is Apache-2.0. The live England disclaimer says the lists came from commercial and academic providers and that users must check intellectual property before use. It does not grant a redistribution license. Australia says the panels are open for research use and does not name an open license. v1 does not ship a panel file.

Orphadata Products need a data-transfer agreement. They are not the Science XML.

Postgres holds the five cases, drafts, snapshots, a few ClinVar rows, trial links, audit, and LangGraph checkpoints. The knowledge base is files beside the process. That is far under 1 GB. The store, RareBench, MONDO’s full OWL, AACT, and ClinVar XML do not go in the database. Neon’s free plan, if used later: 1 GB per project, 100 CU-hours, 10 branches, 6-hour history window up to 1 GB of changes, scale-to-zero after 5 minutes.

Gaps: no public corpus is a longitudinal chart with human acceptances and character spans. The five synthetic cases are that golden set, and they are small on purpose. The store supplies cross-sectional solved cases for rank metrics, with the leakage controls in the next section. Synthea does not generate rare-disease odysseys; it is the wrong filler.

## 5. Evaluation

A stranger clones the repo, runs the setup script, and gets the same pins: HPO `v2026-09-01`, Orphadata files dated 23 Jun 2026, MONDO `v2026-10-06`, Phenopacket Store tag `0.1.27`. The script prints checksums. Metrics are written to `eval/expected/` with a tolerance.

### Golden sets

1. **Product set.** Five original odysseys, at least two notes each. They are a smoke set, not a place to fit a cutoff. Unit tests on tiny HPO sets cover the written rules (missing frequency as LR 1, excluded floor, ancestor match, child-count division, bin bounds). The five cases are:
   - Intellectual disability plus seizures only. Expected “no confident score.” Questions empty. An empty note and an all-negated note are assertions on this case.
   - One exam finding a geneticist would recognize, suggested on the earlier note, and one stable disease after it is accepted.
   - One gene linked to two Orphanet diseases. The expected file names the disease a family would be harmed by confusing, and the test fails if that disease is score-order 1.
   - A denied seizure or intellectual disability, plus a missing Orphanet frequency. Score-order 1 unchanged. “Frequency missing” visible.
   - A ClinVar reclassification. Both significances and dates on the ClinVar tab. The two score lists are identical. One trial row is an off-target hit with the query string stored.
   The rank table ships only if case 1 abstains and case 2 does not.
2. **Public set.** Store `0.1.27`. The full 10,377-packet run is the result that counts. A 200-packet draw, stratified by cohort with a fixed seed, is a regression fingerprint stored in `eval/expected/`. It is not a substitute for the full run.

### Metrics

PhEval’s published ranked metrics (Bridges et al., *BMC Bioinformatics* 2025;26:87, [doi:10.1186/s12859-025-06105-4](https://doi.org/10.1186/s12859-025-06105-4)) are the count in the top n, mean reciprocal rank, precision@k, mean average precision@k, f-beta, and NDCG. percentage@k is hits in the top k divided by all known entities, including ones the tool never returned. pytest reports top-1/3/5/10, mean reciprocal rank, percentage@k, and precision@k. Genes missing from `en_product6` stay in the gene-score denominator. Disease scores outside the 249 unique maps stay out of that denominator, and the exclusion count is printed in the same line. A single Recall@1 with a hidden denominator is a failed report. The scorer also writes PhEval TSV (file stem equal to the packet stem) so `pheval-utils benchmark` can be pointed at it later. That command is not required for the smoke test. Wrapping Exomiser or LIRICAL is out of scope.

### Baselines and ablations

- Degree baseline: genes by number of linked Orphanet diseases, diseases by number of linked genes. The likelihood ratio has to beat it on percentage@k and precision@k on the full store.
- Random gene among Orphanet genes that share one HPO id. Weaker. Reported, not the bar.
- Ablation: patient negations omitted versus included. The nonspecific negations are omitted in v1; the ablation measures that choice.
- Ablation: child-count division off.
- Not an ablation that can pass the suite: handing the scorer the truth gene. That run must match the HPO-only scores or the suite fails.
- Optional LLM column, off by default. A positive control injects the disease name and asserts only that column moves. A column that does not move is not called “no leakage.” The screen has no LLM column.
- Not a full-store ablation: “drop onset.” Onset is present on 9,280 of 224,863 features (4.13%). Progressive disclosure is reported only on packets with at least two onset-dated features, with that subset size printed.

External numbers that are not local runs: LIRICAL phenotype-only top-3 43.7% on 384 case reports; Phrank’s filtered top-10 64.5% on 169 exomes; DeepRare’s 57.18% Recall@1. Different corpora. They are not targets.

### Reanalysis simulation

A second dated Orphanet Science file is an open gap. Until one is pinned, the plan claims no knowledge-base rank diff.

ClinVar: the synthetic case stores two classifications and two dates. The score lists before and after the fetch are asserted equal. A literature quote, substring or not, is asserted not to change the score list. A phenotype accept on case 2 is asserted to change score-order 1 to the hand-written expected disease.

### Leakage controls

Store filenames contain PMIDs. The papers are in the pretraining corpus of any current model. Controls:

- The score function’s signature is HPO ids and a knowledge-base object. No gene symbol, no disease label, no text.
- The run fails when an evaluation prompt or loader input contains a PMID, a packet filename, a cohort-directory name, an abstract, or a disease label.
- Eval mode does not call the literature service.
- Synthetic notes are original sentences, not pasted from a source paper.
- Do not score by deleting terms from `phenotype.hpoa`. That file is not loaded. Truth for genes is the packet’s causative symbol. Truth for diseases is the unique MONDO→Orphanet id. Annotations are Orphanet frequencies.

RareBench is optional and off by default. Its public splits are published cases (LIRICAL, MME, HMS, RAMEDIS). The paper’s privacy warning is about PUMCH identifiers, not about pretraining. A 2026 medRxiv meta-analysis snippet said LLM rare-disease evaluations were at high risk of leakage; the PDF was not read, so that sentence stays a pointer, not a result.

### Error analysis

After the first full run, tabulate misses by: nonspecific HPO only, Orphanet frequency missing, gene absent from `en_product6`, and multi-gene Orphanet entity. The first ten misses are written out with the HPO ids and the top three diseases. That file is the error analysis. No LLM-as-judge assigns the cause.

### What a stranger can reproduce

Setup script, pins, checksums, `pytest` on the synthetic cases, and one command that scores the 200-packet sample and diffs `eval/expected/sample200.json`. Full 10,377 is a second command, expected to be CPU-bound and offline. No API key is required for those commands. PhEval’s own corpora (the paper’s 4,916-packet “4K” set was store release 0.1.12; LIRICAL’s 384 or 385; a synthetic phenotype2phenopacket corpus) can be added later as extra runners. v1’s frozen tag is 0.1.27, which is newer than the paper’s 0.1.12 and newer than the 6,668 packets in Danis et al. for 0.1.19 ([PMC11564936](https://pmc.ncbi.nlm.nih.gov/articles/PMC11564936/)).

## 6. Terraform, pilot, scaling, cost

### Pilot

One operator, one browser, five synthetic cases. `docker compose up` starts the API and Postgres. No account. The walked path, also stored as a transcript the tests follow: rejected draft, accepted draft, second note changes score order, ClinVar row leaves the scores identical, trial query visible and off-target. No real patient, no Matchmaker node, no VCF.

A ten-minute reading of the repo, once it is built, is: Compose up, `pytest` (span trigger, ClinVar zero diff, FHIR client absent, literature substring on the fixture), one `psql` session showing a new `lg` checkpoint and a new `app.snapshot` only after accept, and `python -m eval` on the five cases printing percentage@k with the unscored count. That demo does not exist yet.

A geneticist reading the five cases is a later favor, not a launch gate. The demo does not wait on it.

### Productionization sketch

Compose on one machine is the deployment. A managed Postgres, Neon’s free project or a later RDS, replaces `DATABASE_URL` and nothing else. If an NCBI key is ever used, it belongs only on the literature profile, which is not publicly reachable except from the API. AWS, ECS, and a Terraform module are not created for this pilot. Writing them before a second user exists is how a sketch becomes a bill. The trigger to write HCL is the same as the trigger to leave Compose: the one box is actually too small, or a covered entity is in the conversation. The second of those stops the project instead.

### Scaling triggers

- Postgres above about 0.7 GB, or a Neon project using most of its 100 CU-hours: the knowledge base is already on disk. Pay for the database or keep Compose. Do not “scale” by loading ClinVar XML.
- A second organization: a separate database. Do not merge tenants in the free project.
- Anyone asks to load a real chart: stop. That requires a covered-entity agreement, a lawyer, and a different repository. This plan’s answer is no.

Engagement does not trigger a Kubernetes migration. One box is enough until the process is actually too big for it.

### Cost, at the pilot described here

| Item | Cost |
| --- | --- |
| Neon free, or local Postgres | $0 |
| GitHub | $0 |
| HPO, Orphanet Science, MONDO, Phenopacket Store, ClinVar E-utilities, ClinicalTrials.gov | $0 |
| LLM | $0, because the gazetteer path is the demo |
| NCBI key | unset |
| LangSmith, Medplum cloud, AWS, Terraform apply | $0, not used |
| Exomiser data, OMIM license | $0, not purchased |

The first cost appears only if someone switches on a paid model or applies the AWS sketch. The README says the demo does not need either.

## 7. CLEAR, UNCLEAR, and open questions

### CLEAR

Web search, page fetches, and a local census supported these. The search log has the counts.

- Faye 2024: n = 6,507, mean 4.7 years, median 0.8 years, 73% (4,756/6,507) misdiagnosed at least once under the paper’s broad definition. Abstract disease count 1,675 and methods count 1,684 are both in the article.
- Nguengang Wakap: 6,172 diseases, 71.9% genetic, prevalence 3.5–5.9%, with the stated exclusions.
- Chung 2023: exome 0.38 and genome 0.34, with the split denominators above, inside 50,417 probands.
- Dai 2022 abstract: reanalysis yield 0.10 (0.06–0.13); literature updates accounted for most new diagnoses. Wright, Liu, and Schobers cumulative yields as cited.
- Store `0.1.27` exists (9 June 2026) and contains 10,377 packets, 780 OMIM diseases, 699 genes, onset on 4.13% of feature rows. v0.1.19 in Danis et al. remains 6,668 packets and 475 diseases. The zip count is from the release archive, not from the release notes, which do not state a count.
- MONDO `v2026-10-06` maps 279/780 store diseases to at least one Orphanet xref (35.8%). 30 of those are multi-mapped, so 249/780 are unique. Disease metrics use the 249. The other 531 are excluded and counted.
- Exomiser code AGPL-3.0; data bundle includes OMIM and is not committed. LIRICAL is non-commercial and non-sublicensable; phenotype-only top-3 on 384 reports is 43.7%. Phen2Gene code MIT; its knowledge base is not.
- DeepRare *Nature* 2026 abstract figures and CC BY-NC-ND article license. Rank judging used GPT-4o.
- PhEval metrics and the fact that the paper’s store snapshot was release 0.1.12.
- FDA January 2026 CDS guidance: all four criteria required; NGS variant identification or clinical interpretation, including from a VCF, does not meet Criterion 1. Town hall 11 March 2026.
- RAPID announcement date 31 August 2026, “up to $98.5 million over 4.5 years,” four performer caps, and the six-year sentence on that page.
- GeneDx–Fabric: about $33 million cash at close, milestones toward $51 million, closed 7 May 2025.
- Congenica: SeqOne definitive agreement announced 2 September 2025; price undisclosed; not a shutdown.
- NPRD 2021 text Rs 20 lakh for Group 1; PIB 2022 and 2024 Rs 50 lakh; 63 diseases and 1,118 patients as of 9 August 2024.
- GenomeIndia is healthy volunteers, 10,074 sequenced, controlled access. The QC count differs by page (9,648, 9,768, 9,772).
- ABDM NRCeS v6.5.0 has no rare-disease profile.
- Neon free tier limits cited above.
- LangGraph `interrupt()` restarts the node; the write goes after it returns. ADK confirmation does not fit this gate.
- HPO license text on the GitHub pages site: use unmodified, cite, show the version. IEA rows from OMIM are not reusable in another product without contacting OMIM.
- Orphadata Science is CC BY 4.0. Orphadata Products need an agreement. ClinGen curated labels are CC0 with a requested access date. PanelApp software is Apache-2.0 and the panel content has no redistribution grant on the pages opened.

### UNCLEAR

Searched, and the page either disagreed with itself, failed to load, or did not say.

- The 60% literature share. It is in a meeting abstract and in a thesis chapter (62%), not in the Dai 2022 paper abstract. The Dai full text did not open (Cloudflare).
- Phenopacket Store disease-id namespace. All 10,377 rows are `OMIM:`. Whether a later release adds ORPHA ids was not checked beyond 0.1.27.
- Why 501 store diseases have no Orphanet xref in MONDO `v2026-10-06`, and why 30 of the 279 mapped ids hit more than one Orphanet id. Some OMIM ids may be newer than Orphanet’s June 2026 file. That join was not done. How many of Faye’s 4,756 “misdiagnosed” answers were a different disease name is not in the tables that were opened.
- HPO’s canonical license IRI 404s. The GitHub pages text was opened and is the working license. A counsel read of whether vendoring the unmodified obo is allowed is still wise. The plan vendors nothing until approval, and the setup script downloads.
- GeneDx “reanalysis for no extra charge” is on the provider page that was opened. It is not a promise about this software.
- CPT 81417. A claims site stated a commercial average near $332. The CMS schedule did not load. The number is not used above, because it was being asked to stand in for a buyer this repo does not have.
- AMELIE. The 2021 preprint describes a literature alerter. `amelie.stanford.edu` returned HTTP 500. A 2026 portal was not verified.
- Dx29 and the current Phenomizer host. Pages were empty or HTTP 500. Phenomizer as a 2009 method is clear. The 2026 website is not.
- The $15.6 million between RAPID’s $98.5 million and the four performer caps.
- GenomeIndia’s three QC denominators. Do not pick one as the scientific result.
- Whether phenotype-only ranking plus a human-typed gene symbol, with ClinVar displayed and not scored, is non-device CDS. The NGS examples do not cover it. They also do not bless it.
- DPDP commencement and whether synthetic packets are personal data. Lawyer.
- Whether the twelfth NPRD Centre of Excellence and the PMJAY 40% cap survived after August 2024. The 19 May 2022 office memorandum was not available as clean English.
- PubCaseFinder’s license for mined full text. Bibliographic use of the API as a baseline is the only use planned. Case-report storage is out.
- DeepRare code license (`NOASSERTION` on GitHub versus the article’s CC BY-NC-ND). Do not vendor either.
- RareBench row-level rights versus the HF Apache-2.0 card.
- PanelApp Australia “research use” as a redistribution right. Treated as no.
- A2A `INPUT_REQUIRED` resume rules were not re-read in the design pass. The literature service can instead return an empty evidence list. That fallback does not depend on the spec edge case.
- Two lesson titles on several DeepLearning.AI course pages did not render. Section 8 lists only titles that did.
- assistant-ui’s stockbroker example still documents `interrupt_before`. The interrupts article documents `load()`. Both pages exist. v1 uses a form for the gate and does not resume through `load()`.

### NEEDS MORE INFORMATION

These are questions for the owner, not facts a search will settle.

1. OMIM-level disease scores on all 780 store diseases need an OMIM license for a private knowledge base that is never committed. The plan does not buy one. The screen shows Orphanet disease scores, and the benchmark prints the 531 exclusions. Say if that is the wrong public metric.
2. The brief asks for conditional FHIR create. The plan writes a Patient-and-Observation Bundle to disk and does not POST unless `FHIR_BASE_URL` is set. Say if the disk Bundle is enough.
3. The $0 demo uses the gazetteer only. Say if a paid model should be on by default. The plan’s answer is no.
4. India in this repo is the policy section and the global ontologies. An NRCeS mapping is a different project. Say if that spike is actually wanted.
5. A clinician is not recruited. Say if someone specific should read the five synthetic cases before any UI is built.

### Top open questions

- Publish, at setup time, the fraction of the 699 store genes present in Orphanet `en_product6`, next to gene percentage@k.
- Whether a second dated Orphanet Science file is still published. Until it is pinned, there is no knowledge-base rank-diff claim.
- Leave Matchmaker Exchange unimplemented unless the owner later has a node that has passed the March 2026 service review.
- The 1/1000 excluded-term floor is LIRICAL’s heuristic. It is labeled. A better public frequency for “excluded” was not found.

## 8. DeepLearning.AI course mapping

Lesson titles below are ones that rendered on a public course page during this research. Voice and image courses are listed so the omission is deliberate.

| Course | Lesson titles that were visible | What this repo is for |
| --- | --- | --- |
| AI Agents in LangGraph | Introduction; Build an Agent from Scratch; LangGraph Components; Agentic Search Tools; Persistence and Streaming; Human in the loop; Essay Writer | One case thread, persistence, human acceptance. The filmed human-in-the-loop lesson uses `interrupt_before`. The implementation uses `interrupt()`, with the write after it returns. |
| Long-Term Agentic Memory with LangGraph | Introduction to Agent Memory; Baseline Email Assistant; Email Assistant with Semantic Memory; and the episodic and procedural sequels that rendered | Accepted facts live in Postgres. The checkpoint is not the case file. The email assistant is not built. |
| LangChain: Chat with Your Data | Introduction; Document Splitting; Vectorstores and Embedding; Retrieval; Question Answering | Used only inside the literature service, and only to keep a substring quote. Embeddings are optional. The substring test is the requirement. |
| Evaluating AI Agents | Introduction; Evaluation in the time of LLMs; Decomposing agents; tracing labs; router and skill evaluations; trajectory evaluations; structure; LLM-as-a-judge; monitoring | Rank metrics are code. A trajectory test asserts the FHIR client is not called before accept. LLM-as-judge does not set the rank. |
| Agentic AI | What is agentic AI?; Degrees of autonomy; Task decomposition; Evaluating agentic AI; tools and MCP lessons that rendered | Tools are functions. The scorer is not given autonomy. |
| A2A: The Agent2Agent Protocol | Introduction; Why Agent2Agent Protocol?; A2A Architecture; Wrapping the QA Agent into an A2A Server; Advanced A2A Concepts | One server, the literature agent, because it would hold a foreign key. |
| MCP with Anthropic | Introduction; Chatbot Example; Creating an MCP Server | One server for HPO, Orphanet, MONDO, and keyless ClinVar. Authorization on the course page was still described as roadmap text. The spec, not the course, forbids collecting secrets via elicitation. |
| Governing AI Agents | Introduction; What is AI Agent Governance?; Establishing Governance in Catalogs; Building, Evaluating & Deploying Agents | Least privilege for the NCBI key, and an audit row with ontology version, evidence id, and reviewer. No Unity Catalog. |
| Building Adaptive AI Agents | Introduction; Overview of Continual Learning; Behavior Adaptation; Knowledge Adaptation Through Code Graphs | A person approves a draft before it is reused. Traces are not auto-promoted into skills. No fine-tune. |
| Agent Memory | Introduction; Why AI Agents Need Memory; Constructing The Memory Manager; Scaling Agent Tool Use with Semantic Tool Memory; Memory Aware Agent | Memory write-back does not touch the score list inside the snapshot. |
| Building Live Voice Agents with Google’s ADK | Introduction; Running Voice Agents; Tools; Adding a research agent; Instruction tuning and guardrails; Multi-agent orchestration | No rare-disease voice lesson on the page. Out of scope. |
| Building AI Voice Agents for Production | Introduction; Voice Agent Overview; End-to-end architecture; Voice Agent Components; Optimizing Latency | LiveKit and latency. Out of scope. |
| Multimodal Search and RAG | Introduction; Overview of Multimodality; Multimodal Search; Large Multimodal Models; Multimodal RAG | Faces and images stay out. Out of scope. |

## 9. How review changed this plan

Checking the dossier changed the design before anyone reviewed the draft: the 60% reanalysis line is a meeting abstract; Faye’s 73% is four categories, not a wrong-name rate; store `0.1.27` is 10,377 OMIM-labeled packets; only 249 of 780 diseases have a unique Orphanet id in MONDO `v2026-10-06`. Exomiser, LIRICAL, Phen2Gene’s knowledge base, PanelApp dumps, and DeepRare stayed citations.

Four reviews then read the draft. [docs/review.md](docs/review.md) records what was adopted and what was declined.

Adopted:

- The public gene score does not receive the truth symbol. Ties take the worst rank. Missing genes stay in the denominator. precision@k is reported next to percentage@k. A degree baseline has to be beaten. “No confident score” is a fixed rule, not a cutoff fit on the five cases.
- Disease scores use bin bounds, not midpoints. Descendant-max frequency is out. Questions exclude nonspecific terms and are empty when the score abstains. The header says the list is not a diagnosis.
- ClinVar’s stored score diff is zero. A phenotype accept is what moves score order. The user-facing “rank diff” includes that recorded zero, which is the safety property.
- Knowledge-base files stay on disk. Score lists live in the snapshot. The span rule is a trigger, not a cross-table `CHECK`.
- Default Compose is API plus Postgres. MCP is in-process. The literature A2A service is a Compose profile. FHIR does not POST unless a base URL is set, and the Bundle has no Condition.
- Market sentences that implied a buyer, a CPT wedge, or a RAPID deliverable were removed. The six-year RAPID line is not adopted.

Declined, with the reason:

- Dropping assistant-ui. The brief asks for shadcn and assistant-ui. The accept gate is a form so the known interrupt bugs are not the control.
- Dropping A2A entirely. The brief requires it where a credential or a separate process is the reason. It is not on the default path, because the score does not need a key.
- Letting ClinVar or an accepted gene symbol move the disease score. That fights the FDA boundary the rest of the plan is built on. Gene symbols remain an evaluation label and a leakage check.
- Checking in Terraform HCL. Section 6 is the productionization plan. HCL waits until Compose is actually too small.
