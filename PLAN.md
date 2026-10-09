# Plan: a multi-omics correlator for one person over time

Status: plan only. No application code, schema migration, or service is in this repo. Nothing is built until the owner approves this plan.

Owner: Ashish Kumar. This portfolio repo was a longitudinal HPO-to-Orphanet ranker. That concept is replaced. What remains is a research demo, unbuilt until this plan is approved: for one synthetic person, over time, cited comparisons of already-reported facts. The comparisons are the three objects the owner asked for — a risk signal, a rare-disease likelihood, and an alarm or recommendation — and section 2 defines the words on the card so those nouns are not read as a diagnosis, a probability, or an order. The demo does not diagnose, intervene, order, or discover a correlation.

Checked against primary pages in the earlier research pass and against a second pass on 9 October 2026 for the reference layer (gnomAD, ClinPGx/CPIC, NHANES, UK Biobank, All of Us, Synthea, GTEx, OpenSNP, PGP, LOINC/UCUM, UDN, Gemini). Counts are in [docs/search-log.md](docs/search-log.md). They are not 1,500. Anything this file did not re-open is marked unverified or left in section 7.

## 1. Problem and impact

### Who the published record describes

The people in the papers below are not users of this demo. The demo user is one operator with a local session, reading five synthetic charts. The papers are why a cited comparison is a real problem, and why a screen that looks like a diagnosis is a harm. A phenotype is added. A lab report names a variant and a classification. A medication is started. A later ClinVar release uses different words for that same reported variant. A reference file is often missing. The demo can show that last fact. It cannot follow a real chart.

Faye et al., *European Journal of Human Genetics* (2024), surveyed 6,507 people with a confirmed diagnosis, living with 1,675 rare diseases in the abstract and 1,684 in the methods, across 41 European countries ([PMC11369105](https://pmc.ncbi.nlm.nih.gov/articles/PMC11369105/), [doi:10.1038/s41431-024-01604-z](https://doi.org/10.1038/s41431-024-01604-z)).

- Mean total diagnosis time 4.7 years. Median 0.8 years (IQR 0.1–5.0). The mean is the skew, not a typical wait.
- 73% (4,756/6,507) were misdiagnosed at least once. The paper’s definition is wider than a wrong disease name: symptoms attributed to another physical disease, neglected, not taken seriously, or considered psychological.
- The sample is people who already have a diagnosis and who answered a retrospective survey. Undiagnosed people are absent.

Nguengang Wakap et al. counted 6,172 Orphanet diseases, 71.9% genetic, and a conservative point prevalence of 3.5–5.9% ([doi:10.1038/s41431-019-0508-0](https://www.nature.com/articles/s41431-019-0508-0)). That figure excludes rare cancers, infections, and poisonings. It is not a patient count.

Chung et al., *Genetics in Medicine* (2023), report diagnostic rates of 0.38 for exome (126 studies, 38,277 probands) and 0.34 for genome (40 studies, 11,207 probands), inside an eligible set of 50,417 probands ([doi:10.1016/j.gim.2023.100896](https://doi.org/10.1016/j.gim.2023.100896)). Most people remain undiagnosed after the sequencing test. Reanalysis recovers some of the rest, and the yield depends on the denominator. Dai et al. pooled a reanalysis yield of 0.10 (95% CI 0.06–0.13) and wrote that literature updates accounted for most new diagnoses ([doi:10.1016/j.gim.2022.04.021](https://doi.org/10.1016/j.gim.2022.04.021)). The figure of 60% is a companion meeting abstract ([S1098-3600(22)00390-2](https://www.gimjournal.org/article/S1098-3600(22)00390-2/fulltext)), not that paper’s abstract. The Dai full text did not open. Wright et al. moved 1,133 DDD trios from 27% to 40% ([PMC5912505](https://pmc.ncbi.nlm.nih.gov/articles/PMC5912505/)). Liu et al. moved a 250-person cohort from 24.8% to 46.8% and a 2,000-person semi-automated cohort from 25.2% to 36.7% ([PMC6934160](https://pmc.ncbi.nlm.nih.gov/articles/PMC6934160/)). Schobers et al. moved 150 patients from 31% (47/150) to 53% (79/150) ([doi:10.1186/s13073-022-01069-z](https://doi.org/10.1186/s13073-022-01069-z)). Solve-RD systematic reanalysis found 506/6,004 (8.4%), plus 4.1% ad hoc ([doi:10.1038/s41591-024-03420-w](https://www.nature.com/articles/s41591-024-03420-w)). Talos found 241/4,735 (5.1%) ([doi:10.1038/s41591-026-04477-5](https://www.nature.com/articles/s41591-026-04477-5)). One commercial biannual reanalysis moved a lab cohort from 18.3% to 20.4%. ARPA-H’s RAPID page says the odyssey “lasts six years on average.” This plan does not adopt that sentence.

A wrong name at the top of a catalogue comparison is a harm the screen can create. The header says the list is not the probability of a disease. A missing reference file is a different harm. The card says the rank is absent, which means the software abstained. It does not mean the person is well.

### What “correlate” means here

Correlation in this repo is a cited comparison of one accepted fact to a pinned public reference, or of two accepted facts to each other through a published table (a reported gene and a medication, through ClinPGx). It is not a model trained on this repo’s patients. The application database holds synthetic people only. Synthetic people can exercise the plumbing and can carry a known answer the author planted. They cannot be the population a correlation is discovered in. That limit is the point of section 4 and section 5.

Phenotype-to-disease likelihood remains one signal, on the Orphanet frequency table, with the coverage limit measured on Phenopacket Store `0.1.27`: 249 of 780 store diseases have a unique Orphanet id in MONDO `v2026-10-06`. It is no longer the product. A lab percentile, a quoted drug–gene annotation, and a displayed lab classification are separate cards. They are not fused into one rank.

### Companies, and why this is still a public repo

Commercial products sell a test or a lab workstation. GeneDx includes reanalysis in the test price and bought Fabric Genomics for about $33 million cash at closing (agreement 15 April 2025, closed 7 May 2025), with milestones that can take the total toward $51 million ([SEC 8-K](https://www.sec.gov/Archives/edgar/data/1818331/000181833125000057/wgs-20250415.htm)). Fabric, Illumina Emedgene, Geneyx, 3billion, CentoCloud, and SeqOne interpret a VCF inside a lab. SeqOne announced a definitive agreement to acquire Congenica on 2 September 2025; price undisclosed. Face2Gene reads photos. Probably Genetic collects patients. This repo does not call variants and does not read images.

Invitae filed Chapter 11 on 13 February 2024. Labcorp bought selected assets for $239 million; the sale closed 5 August 2024. That is a lab transaction, not a missing correlator.

ARPA-H RAPID, announced 31 August 2026, will invest up to $98.5 million over 4.5 years ([announcement](https://arpa-h.gov/news-and-events/arpa-h-announces-awards-advance-ai-rare-disease-diagnosis-and-treatment)). Performer caps that were opened: UNC/Haendel up to $34.9 million (dataset), Sage/Allaway up to $28.2 million (benchmark platform), FDNA/Bray up to $9.9 million (photos, video, voice), Probably Genetic/Lange up to $9.9 million (patient collection and synthetic data). Those four sum to $82.9 million. The remaining $15.6 million was not itemised on the pages opened. This repository is not a RAPID deliverable.

Investors who write about healthcare AI fund labor that already has a buyer. a16z Bio+Health, General Catalyst, Bessemer (22 January 2026), and Menlo (21 October 2025) would not fund a company from this plan. The plan does not ask them to. Bessemer’s essay says providers are paid for procedures and visits. This screen does not bill a procedure.

The portfolio reason is the engineering problem: a time-ordered chart, a database approval gate, public references with honest licences, and an evaluation that says what it cannot claim. Job ads in an India-skewed sample of 418 postings mention Python (77%), agentic work (59%), RAG (52%), evals (36%; 51% in healthcare), LangChain (26%), LangGraph (17%), MCP (16%), and A2A (3%). Those rates are why section 2 has a table of protocols that are not used. They are not a customer, and they do not choose the comparison functions.

### India

The National Policy for Rare Diseases (2021) pays for treatment. It does not set a prevalence cutoff. The policy text caps central support at Rs 20 lakh for Group 1 under Rashtriya Arogya Nidhi ([policy PDF](https://www.tdb.gov.in/sites/default/files/2025-01/nprd-2021.pdf)). PIB releases state support up to Rs 50 lakh at a Centre of Excellence ([PRID 1846230](https://www.pib.gov.in/Pressreleaseshare.aspx?PRID=1846230), [PRID 2043516](https://www.pib.gov.in/PressReleaseIframePage.aspx?PRID=2043516)): 63 diseases, 1,118 patients, twelve Centres of Excellence as of 9 August 2024. The policy does not procure this screen.

GenomeIndia is a healthy reference of about 10,000 people from 83 populations ([doi:10.1038/s41588-025-02153-x](https://doi.org/10.1038/s41588-025-02153-x)). Pages disagree on the QC denominator (9,648, 9,768, 9,772). Access is controlled (Biotech-PRIDE / FeED). This repo does not request or store those genomes. A frequency prior from GenomeIndia would belong in an approved project, not in git.

ABDM NRCeS FHIR IG v6.5.0 has no rare-disease or Phenopacket profile ([NRCeS](https://nrces.in/ndhm/fhir/r4/)). ICMR NRROID’s live page says the registry started in November 2019, with six categories, 19 centres, and “over 4,000 cases.”

The Digital Personal Data Protection Act, 2023, defines personal data as data about an identifiable person. Health is not a separate class in the text that was opened. A reprint of G.S.R. 843(E) points at operative sections on 13 May 2027. Whether that date and this demo’s synthetic rows are inside the Act is for a lawyer. This plan is not legal advice.

## 2. Solution

### Dimensions in, and dimensions out

Included, because a public reference or a published lookup exists and the fact can be stored as text or a code:

| Dimension | What is stored | Why it is in |
| --- | --- | --- |
| Reported variant | HGVS string, gene symbol, the lab’s own classification words, the quote and character span in the synthetic report, the report date | Rare-disease context and drug–gene lookup need a gene the lab already named. The software displays that classification. It does not assign one. |
| Biomarker or lab | LOINC code, UCUM unit, numeric value, specimen time | NHANES public-use files are an open distribution a percentile can cite. A value with no pinned distribution produces no rank. |
| Phenotype | HPO id, present or excluded, quote and span | Orphanet frequency bins are an open table. The store gives solved cases for a known-answer test. |
| Medication | Drug name as accepted text, optional code if the reviewer types one | ClinPGx/CPIC annotations can be quoted for a reported gene. The card does not choose a dose. |
| Clinical history | Note text, then accepted coded facts with spans | The note is unstructured. A draft with a span is the only machine step. A person accepts it. |
| Social history, family history, exposure, imaging report | Note text, then an accepted fact with a span (relative and condition, tobacco use, a sentence from a report) | These are unstructured, so a gazetteer or a model may propose a draft. Once accepted they are timeline facts. They are not alarms: restating “father, cardiomyopathy” adds no comparison to a pinned distribution. Vitals that already have a LOINC code are labs. |

Excluded, with the reason:

| Left out | Why |
| --- | --- |
| VCF, BAM, FASTQ, variant calling, ACMG/AMP classification | FDA Criterion 1, below. Also the wrong size for a public demo database. |
| Images, DICOM, faces, voice, video | Criterion 1 covers medical-image analysis. FDNA’s RAPID work is that modality. |
| Family-history, exposure, or imaging “alarms” | The accepted fact is already on the timeline. A second card that says a clinician may want to look trains the reader to ignore cards that do compare against a file. |
| Polygenic scores, methylation, episignatures | A new interpretation of a genotype or an assay, and no reference this repo can commit. |
| Proteomics or metabolomics panels that are not already a LOINC result | No open rare-disease reference distribution is pinned here. A LOINC result falls under labs. |
| Raw wearable streams | No committable reference distribution for a rare-disease alarm. |
| GTEx genotypes, and GTEx as a v1 signal | Open median TPM exists, but GTEx is postmortem expression in people who were not assembled as a rare-disease cohort. Individual sequence and full donor metadata are in dbGaP `phs000424`. v1 does not cite TPM as a risk signal. A later signal that needs tissue expression would pin an open median file and say it is expression, not a diagnosis. |
| GenomeIndia, UK Biobank, All of Us, MIMIC, UDN participant files, DECIPHER patient records | Credentialed. They cannot be committed. Section 4. |
| OpenSNP and Harvard Personal Genome Project genomes | The licences are open. The people are real. A public demo database is the wrong place for them. |
| Full gnomAD or ClinVar dumps | Multi-gigabyte. A lookup cites a version and an accession. The dump stays out of git and out of Postgres. |
| Synthea as a validation cohort | It can emit FHIR. It cannot stand in for a correlation discovered in people. Section 4. |
| Matchmaker Exchange | A public token would be a trusted querier. Matching stays off. |
| Orders, enrolments, dose changes, a diagnosis label | Those are interventions or determinations. The card says a clinician may want to look. |

### Cards

After a commit, pure Python recomputes cards from accepted observations and pinned files. The owner’s three names map onto card types, and the card header is the narrower sentence, because “risk signal,” “likelihood,” and “alarm” are what a non-specialist fuses into a diagnosis.

| Owner’s word | Card header the UI uses | Comparison |
| --- | --- | --- |
| Risk signal | Population rank only | A lab value against a pinned NHANES extract |
| Rare-disease likelihood | Catalogue comparison | Accepted HPO terms against Orphanet frequency bins |
| Alarm or recommendation | Copied sentence | A ClinPGx/CPIC quote for an accepted drug and a reported gene |

Each card stores the rule name, the knowledge-base versions, the source ids, and a `not_considered` list. No card multiplies these into one score.

1. Population rank. The pin, written before any case is scored, names the LOINC, the age band, the sex band, and the rule “strictly above the unweighted empirical 97.5 percentile of that extract.” The card states the cycle and that survey weights were not applied. If the extract has no row for that LOINC, the card says the rank is absent. Absence is a missing file, not a normal result. The rank is not the laboratory’s reference interval and not a reason to repeat or treat.
2. Catalogue comparison. Orphanet frequency-bin likelihood ratio at the lower and upper bound of each bin, on diseases with a unique MONDO-to-Orphanet map. The card abstains when at least 10 diseases sit within a factor of 2 of the best lower-bound ratio, or when order 1 flips between the bin bounds. Both numbers are frozen in the eval pin before the store run. Refitting them on the 249, or rewriting the synthetic abstention note so a retuned threshold still passes, fails the eval. A reported variant is not an input. Adding the variant card leaves the likelihood JSON identical, including when HGNC symbols and genomic interpretations are stripped from the packet before scoring. The likelihood reads phenotype frequencies only. It does not read Orphanet `en_product6`.
3. Copied sentence. The drug card quotes ClinPGx or CPIC and says this screen did not choose a dose, a substitute, or a stop. Any “avoid” or “reduce” wording inside the quote belongs to the guideline. CPIC’s own licence text says guidelines can be stale and do not replace judgment. The variant card is a quoted display: the lab’s words, then ClinVar’s words, with the statement that the quotes are not reconciled and that a later ClinVar sentence does not update the lab. v1 shows no gnomAD allele frequency on that card. A frequency next to a class is how a reader applies a rarity criterion without a worksheet. Until the Broad policies page is opened, there is no frequency line at all.

No card says eligible, prescribe, or diagnosed. The words “pathogenic” and similar appear only inside a quote from the lab report or from ClinVar.

### How a non-specialist should read a card

The sentences below are the card text. They are for a reader who does not work in genetics. They are illustrations of wording. They are not a measured NHANES percentile and not a result from a real person.

- Population rank. “Population rank only. This value is above the unweighted 97.5 percentile in the pinned NHANES August 2021–August 2023 extract for the age and sex band named in the pin. Weights were not applied. This is not the laboratory’s reference interval, not the probability of a disease, and not a reason to repeat or treat. No row in the extract means no rank: a missing file, not a normal result.”
- Catalogue comparison. “Catalogue comparison of accepted HPO terms against Orphanet frequency bins. It is not the probability this person has the disease. The reported variant was not an input. The first row ranks ahead of other diseases with a unique MONDO–Orphanet map, at both ends of the published bin. 531 of 780 snapshot diseases have no unique map and cannot appear. ‘No confident likelihood’ means the table could not separate a first row. It does not mean there is no rare disease.”
- Variant. “Quoted display. This software did not classify this variant and did not apply ACMG/AMP. Lab report, with date: the quoted words. ClinVar, with release and accession: the quoted words. The quotes are not reconciled. A later ClinVar sentence does not update the lab. No sequence file was read. No population allele frequency is shown.”
- Drug. “Copied sentence from ClinPGx/CPIC, with version and date. This screen did not choose a dose, a substitute, or a stop. Any avoid, reduce, or switch wording in the quote belongs to the guideline. CPIC says guidelines can be stale and do not replace judgment.”
- History. Timeline only. “Accepted fact, restated: the relative and the condition, or the exposure. No risk was calculated.”
- Every comparison card lists what it did not use: no sequence file, no image, no UK Biobank or All of Us row, no GenomeIndia frequency, no dose, no trial query, and any disease or analyte the pinned file does not contain. The source line is the file name, version or cycle, access date, and the quote the reviewer accepted. The not-considered list is on the card body, not only in a footer.

### Workflow

One case is one synthetic person. Time is `authored_at` on each accepted observation. The order of work:

1. A note or a structured row is proposed. The proposal is inserted as `app.draft` with status `pending`. A trigger stores the canonical JSON and its SHA-256. The client does not supply the hash. This insert does not create an observation.
2. The review screen shows that canonical text. Accept, edit, and reject are form buttons. Edit inserts a new draft and supersedes the old id in one transaction. It does not reuse the old hash.
3. Accept or reject calls `app.apply_decision` inside one database transaction. The function is the only writer of observations, snapshots, and cards.
4. In that same transaction, Python computes the cards from accepted observations and the pinned files, and the function inserts the snapshot. There is no second connection and no second decision for the same click. The scorer does not open a connection as a table owner.

There is no graph pause. A side effect cannot run “before the interrupt” and then run again, because there is no interrupt. Two clicks call the function twice; the second sees a draft that is no longer pending and writes nothing.

### What is code, and what is a model

Deterministic code, with no model in the path:

- Unit normalisation with UCUM.
- Population rank against a pinned NHANES extract.
- Frequency-bin likelihoods against Orphanet.
- Lookup of a reported HGVS or accession in a pinned ClinVar citation, displayed and not scored.
- Lookup of a reported gene plus an accepted drug in a pinned ClinPGx/CPIC file, quoted and not dosed.
- Abstention when the reference row is missing. gnomAD is not consulted in v1.
- The approval function in Postgres.

A model is used in one place, and only when a key is set. Unstructured synthetic note text can be turned into a draft list of coded facts, each with a character span. The span has to match the note or the database trigger rejects the draft. If `GEMINI_API_KEY` is unset, a gazetteer does the same job on the five demo notes. Gemini’s free tier, on the pricing pages opened 9 October 2026, lists eligible input and output as free of charge. The same pages say free-tier content may be used to improve Google products. The demo sends synthetic text only. Grounding with Google Search was described as unavailable on the free tier. A third-party blog named specific model ids; those ids are not treated as official here. The official pages that opened did not give a stable requests-per-minute table. Spend on the free tier is $0 until someone links a billing account, which this plan does not do.

A literature passage is not a card in v1. There is no NCBI key and no second process to hold one.

### Agents not used here, and why

The core is rules and lookups. An agent wrapped around a human click would be a second writer in front of a database that already enforces the write. The integrated-plan exercise reproduced four LangGraph failures: a side effect placed before the pause ran twice; an edited body was committed under the hash of the body the reviewer had approved; two resumes both wrote; renaming the gate node dropped the pending approval. The Postgres function held only after `EXECUTE` was revoked from `PUBLIC`. Those failures are the reason the gate is SQL.

| Component | In this plan | Why |
| --- | --- | --- |
| LangGraph, checkpoints, `interrupt()` | Not used | The only writer of a committed row is `apply_decision`. A node name is not part of the pending key. There is no resume. The four failures in the paragraph above are what a graph pause did when it was the gate. |
| An agent whose job is the human gate | Not used | The gate is a table, a function, and a form. |
| An LLM that ranks diseases, classifies variants, or sets a threshold | Not used | Those are table lookups. A model there cannot be calibrated on synthetic patients. |
| MCP | Not used | The UI calls FastAPI. Tests import the package. No client speaks MCP. An adapter with no caller is ceremony. Lookups stay Python functions. |
| A2A, including a literature container | Not used | v1 has no card that consumes a literature passage. A second container does not isolate a secret the demo does not have. An NCBI key in an environment variable would still be a key on a machine; it would not by itself justify a protocol. If a later card needed a foreign credential, the passage would still enter as a pending draft through this API, and the span trigger would still apply. That card is not in this plan. |
| Google ADK, LiveKit, CrewAI, LlamaIndex, LangSmith, assistant-ui, a vector database | Not used | No voice, no chat gate, no embedding. Quote checks are substring spans. |

The workflow is a draft status (`pending`, `superseded`, `approved`, `rejected`) in FastAPI plus the function. FastAPI does not write observations.

### Approval gate

Committed content is the hash the reviewer saw. One decision produces one effect. A pending row stays pending until the function runs. Reviewer identity comes from the session.

Sketch, not a migration file:

- `app.draft(id, case_id, kind, body jsonb, body_hash, status, created_at)`. Status is `pending`, `approved`, `rejected`, or `superseded`. No column stores a graph node name.
- `app.decision(id, draft_id unique, reviewer, decision, body_hash, decided_at)`. The unique key is what makes a second decision fail.
- `app.observation`, `app.snapshot`, and `app.signal` have no `INSERT`, `UPDATE`, `DELETE`, or `TRUNCATE` for the API role. `app.decision` is insertable only by the function.
- Migrations run as a `NOLOGIN` table owner. The API role is `NOINHERIT`, is not a member of that owner, and owns neither the tables nor the function. A missing grant does not bind the owner. A gate test, connected as the API role, asserts `proowner` and `tableowner` are the other role.
- `app.apply_decision(draft_id, decision, seen_hash)` is `SECURITY DEFINER` with `SET search_path = pg_catalog, app`. Every name inside the function is schema-qualified. `REVOKE ALL ON FUNCTION app.apply_decision FROM PUBLIC`. Grant `EXECUTE` only to the API role. `REVOKE CREATE` on schemas `public` and `app` from the API role.

The function, in one transaction:

1. Reads `current_setting('app.reviewer', true)`. Missing or empty raises. The argument list has no reviewer parameter. The request model has no reviewer field.
2. `SELECT … FROM app.draft WHERE id = draft_id FOR UPDATE`. Status other than `pending` raises. A superseded id raises. Status does not return to `pending`.
3. `seen_hash` must equal `draft.body_hash`. A mismatch raises.
4. Inserts one `app.decision` row (reviewer, decision, hash, time) and exactly one effect: an observation, or, for a rejection, the decision row is the effect. Then sets the draft status. Snapshot and signal rows are inserted only here, from a draft whose body is the pure function of already accepted observations, in this same transaction and under the same reviewer setting. No ORM session, trigger, or rule writes those tables otherwise.
5. A unique violation or a raise rolls the transaction back.

Canonical body: UTF-8, NFC, sorted keys, no whitespace, no duplicate keys. A `BEFORE INSERT` trigger on `app.draft` computes the SHA-256, stores that canonical text, and the review screen shows that text. `body` and `body_hash` are frozen. The API role may update `draft.status` only, and only from `pending` to `superseded`. Edit inserts the new draft and supersedes the old id in that same transaction.

The API sets the reviewer inside that same transaction with `SELECT set_config('app.reviewer', <session user>, true)` and then `apply_decision`. The third argument of `set_config` makes the setting local to the transaction, so a connection returned to a pool does not authorize the next checkout. A missing setting raises, which is what happens if a pooler drops it: the call fails closed. The direct Neon host is still the deployment rule. The session user is the demo login. Tests: permission denied for a role without `EXECUTE`; a second call raises; a hash mismatch raises; a pending row remains when the function is not called; a session-level setting left on a pooled connection does not authorize the next checkout; the decision row’s reviewer equals the server-side session value.

Span rule, carried forward: a `BEFORE INSERT OR UPDATE` trigger on a draft whose body contains a quote reads the note and raises unless `quote = substr(body, span_start, span_end - span_start)` with `span_start` 1-based. A column `CHECK` cannot see the other table.

### Safety and regulatory boundaries

Label on the README and every screen: “For research use only. Not for use in diagnostic procedures.” That sentence is the RUO label in 21 CFR 809.10(c)(2)(i), as quoted in FDA’s RUO guidance. It does not by itself make the software a non-device. Intended use is objective intent. A README that told a clinic to rely on a card would be the use, whatever the banner said.

FDA’s current CDS guidance is the January 2026 final guidance, docket FDA-2017-D-6569, reissued 29 January 2026 ([PDF](https://www.fda.gov/media/109618/download)). The 11 March 2026 town hall repeats the device examples ([slides](https://www.fda.gov/media/191561/download)). A function is non-device CDS only when it meets all four criteria in FD&C Act §520(o)(1)(E):

1. It is not intended to acquire, process, or analyze a medical image, a signal from an in vitro diagnostic device, or a pattern or signal from a signal acquisition system.
2. It is intended to display, analyze, or print medical information about a patient or other medical information, such as peer-reviewed studies and clinical practice guidelines.
3. It is intended to support or provide recommendations to a health care professional about prevention, diagnosis, or treatment.
4. It is intended to enable that professional to independently review the basis for the recommendations, so that they do not rely primarily on the software.

Criterion 1 is the one a genomic correlator is built to fail if the boundary moves. The guidance’s examples say software that processes an NGS sequence or a VCF to identify variants, or to identify the clinical implications of those variants, does not meet Criterion 1. Example 17 in the materials opened with the guidance: software that takes a VCF and returns FDA-approved treatment recommendations is a device function. A geneticist clicking accept does not repair Criterion 1. Time-critical alarms and a single score with no inspectable basis are the Criterion 4 failures. Criterion 3 is the recommendations themselves; it is allowed only together with the other three.

v1 stays on the display side of those examples:

- No sequence, no VCF, no BAM, no caller, no ACMG/AMP worksheet, no new pathogenicity word minted by this software.
- A variant card repeats the classification the synthetic lab report already stated, with the quote, and may place next to it ClinVar’s published words for that accession, with the ClinVar release date. The card computes no class of its own.
- A drug–gene card quotes a ClinPGx/CPIC sentence. It does not name a dose, a substitute drug, or a “do not use” order. Choosing a dose would be a specific directive (Criterion 4) and, if derived from the genotype, the kind of clinical implication Criterion 1 treats as device software when the input is sequence or a VCF. This plan does not take that input. It still does not choose a dose, because a directive is the wrong object even from a quoted guideline.
- Imaging input is report text. Pixels and DICOM are out.
- Every card shows the inputs, the rule, the citation, and the `not_considered` list, which is the Criterion 4 posture. Whether FDA would still call the likelihood list a device is not settled by the pages opened. The NGS examples do not cover a frequency table over HPO terms. They also do not bless it.

What changes if a VCF is in scope. Parsing a VCF, calling variants, annotating clinical implications from the alleles, or recommending a treatment from those alleles fails Criterion 1 on the guidance’s own examples. The rest of the correlator (labs, HPO, notes) would not pull that function back across the line. The honest label would be: this function is a device function if it is intended for clinical use, RUO is a label and not a shield, and the repo would say so in the README before any VCF parser existed. v1 does not add the parser. The evaluation does not ingest VCFs from the Phenopacket Store either; gene symbols in the store are labels for the phenotype test, held out of the function.

HIPAA, on the pages opened, applies to covered entities and business associates. This demo is not one. Real notes, real genomes, and real Matchmaker payloads are not committed. EU IVDR Article 1(3)(a) and the UK MDR 2002 turn on the manufacturer’s intent. Promoting the demo as a diagnostic walks out of the research exclusion.

Matchmaker Exchange service requirements (March 2026) require a real node, manual acceptance, HTTPS, and `X-Auth-Token`. Matching stays off.

### FHIR

No Bundle, no HAPI, no `FHIR_BASE_URL`. Nothing in this correlator reads a Bundle. ABDM is not a target. The previous plan’s disk Bundle was a conditional export for a ranker brief. This brief does not ask for it.

## 3. Tech stack

### Backend

Python 3.12, uv, FastAPI, Pydantic v2, PostgreSQL. Pure modules for the catalogue comparison, the population rank, and the quote lookups. No LangGraph, no MCP server, no A2A service, no LangChain.

Layout, when building is approved:

```
apps/web                 Next.js, TypeScript, Tailwind, shadcn
services/api             FastAPI, draft status, calls apply_decision
packages/correlator      pure functions, imported by tests without FastAPI
eval/                    pins, pytest, a TSV of the catalogue-comparison counts
sql/                     migrations, including the function and the REVOKEs
compose.yaml             api + Postgres
```

### Frontend

Next.js App Router. shadcn `Table`, `Sheet`, `Badge`, `Tabs`, `Button`, `Input`. The timeline is a list of snapshots, not a new component package.

Screens:

- Case list. Empty state: “No synthetic case loaded.” Error state if the API is down.
- Timeline for one case: date, which observation was accepted, which cards appeared or abstained.
- Cards, not one differential as the whole page. Tabs: Labs, Catalogue comparison, Variants, Medications, Timeline. Each comparison card has the sentence from section 2, the source, and the not-considered list in the body. The timeline shows accepted history facts and does not call them alarms.
- Draft review: the body, the hash prefix, the highlighted span, Accept / Edit / Reject. These buttons call the API that calls the function. They are not a chat composer.

assistant-ui, agent-chat-ui, and CopilotKit are not on the accept path. The previous plan kept assistant-ui because an earlier brief asked for a chat. This brief asks for a review UI. The known failure modes stay documented so they are not reintroduced: assistant-ui tutorial part 3 throws `NodeInterrupt`; agent-chat-ui issues #85 and #262 restart a graph when a reply is typed; CopilotKit’s FastAPI pages say `useInterrupt` is unsupported. There is no graph to restart.

Desktop is a timeline beside the cards. Below a narrow width the timeline stacks above the cards. The “not a diagnosis” line remains on that layout.

### Database

Compose Postgres is the demo database. A Neon free project is the same schema behind `DATABASE_URL` when a cloud database is wanted. Neon’s free tier, as cited in the previous pass: $0, 1 GB per project, 100 CU-hours, 10 branches, 6-hour history, scale-to-zero after about 5 minutes, max 2 CU. The pooler is PgBouncer in transaction mode. Use one transaction for `SET LOCAL` and `apply_decision`, on the direct host.

Knowledge-base files stay on disk: Orphanet Science, the MONDO xref extract, HPO, a small NHANES extract, a small ClinPGx extract. They are not loaded into Postgres. No gnomAD extract in v1. `phenotype.hpoa` is not loaded. The annotation guide says IEA rows are parsed from OMIM and that OMIM must be contacted before another product reuses them.

`app.case.synthetic` is checked true in this demo. The decision row is the audit: reviewer, action, time, and hash. There is no second audit table.

### Infra

Default Compose is the API and Postgres. Terraform is a sketch in section 6. It is not applied, and there is no `infra/` tree of HCL.

Already refused: a hosted ranker, Medplum, Langfuse, a vector database, HAPI in the demo, an ECS module checked in as if it had been applied, variant calling, a fused “omics score.”

## 4. Data

### The hard limit

With synthetic patients this repo can test plumbing and known-answer cases. It cannot discover a correlation that was not planted or already published. A green test on five invented charts means the population rank matched a value the author planted. It does not mean the percentile predicts a rare disease. Public case reports and public survey files can support a known-answer test because the answer was established outside this repo. They still cannot support a claim of a new multi-omic association.

Synthetic data only in the application database. Credentialed cohorts are listed so a reader can see the gap. They are not downloaded into this repo.

### What can actually be pinned

| Source | What it is | Size, as opened | Licence and access | Role here |
| --- | --- | --- | --- | --- |
| Phenopacket Store `0.1.27` | 10,377 JSON packets, 700 cohorts, 780 OMIM diseases, 11,454 genomic interpretations, 699 HGNC symbols, 224,863 phenotypic features, onset on 9,280 (4.13%). Released 9 June 2026. Zenodo `10.5281/zenodo.20614899`. Zip 19,431,098 bytes. | 19 MB zip | BSD-3 on the store. Published case reports, not synthetic. Evaluation download only. | Known-answer phenotype test. Gene symbol is a label, held out of the function. Not loaded into the app database. |
| MONDO `v2026-10-06` | 36,055 terms. Unique OMIM-or-OMIMPS to Orphanet map for store diseases: 249/780. At least one Orphanet id: 279/780 (35.8%), 30 of them multi-mapped. | obo about 51 MB | CC BY 4.0 | The coverage denominator. 531 diseases are excluded from the likelihood metric and counted. |
| HPO, ontology file | Version pinned at download (v2026-09-01 was about 10.9 MB). | Small | GitHub pages licence text: use unmodified, cite, show the version. The header IRI `hpo.jax.org/app/license` returned 404. OBO Foundry (17 March 2026) does not treat it as CC BY or CC0. | Ids and labels. No IEA annotations. |
| Orphadata Science `en_product4` and `en_product6` | Phenotypes 4,357 records, dated 23 June 2026 on the page opened. Genes 4,245 records. | 45.67 MB and 21.56 MB | CC BY 4.0. Orphadata Products need a data-transfer agreement and are not used. | Frequency bins: obligate 100%, very frequent 80–99%, frequent 30–79%, occasional 5–29%, very rare 1–4%, excluded 0%. |
| ClinVar | Public archive. E-utilities: 3 requests/second without a key, 10 with a key (NBK25497). | Monthly XML on the order of 6 GB (a 2026-10-01 VCV gzip was about 5.98 GB). Not downloaded. | Attribution if redistributed. Weekly releases are not the archive. | A cited accession and the published classification words. No XML in git. |
| ClinGen | Curated labels. | Not bulk-loaded | CC0, with a requested attribution and access date. Terms page document date 26 January 2018. | Optional citation beside a gene or variant the lab already named. |
| gnomAD | v4 release described on the homepage and downloads page as 730,947 exomes and 76,215 genomes, GRCh38. v4.1.0 all-sites allele-number TSVs were listed at 1.07 GiB (exomes) and 11.19 GiB (genomes). | Do not commit | Summary data described as usable without a restriction pointer, which points at a policies page. That Broad policies page was not fully fetched this pass. A CC0 statement on a regional mirror (`gnomad-sg.org`) is not treated as the Broad policy. UK Biobank samples sit inside v4 exomes. | Listed so the gap is visible. Not shown on a card in v1, and not loaded. Licence UNCLEAR until the Broad policies page is opened. No re-identification use. |
| ClinPGx (successor to PharmGKB, 30 July 2025) and CPIC | `clinicalAnnotations.zip` about 1.2 MB and `guidelineAnnotations.json.zip` about 841 KB, from `api.clinpgx.org`, as listed in a KG-registry page. | Small enough to pin a subset | Blog: annotations CC BY-SA 4.0, attribution, share-alike, no selling the data for others’ private or commercial use. `clinpgx.org` data-use page rendered “Loading…” and is UNCLEAR. CPIC `cpic-data` v1.53.1: curated content CC0, with a request to attribute, and a statement that guidelines are decision support, may be stale, and are not a substitute for judgment. | Quote. Do not auto-dose. Do not vendor the full annotation set into the app database; pin the rows the demo drugs need, with the notice. |
| NHANES August 2021–August 2023 public-use | Interviewed 11,933 (3,073 interview only + 8,860 examined). Screened sample 22,660. Unweighted interview response 34.5%, examined 25.6%. Civilian noninstitutionalized US. This cycle did not oversample by race or income. | Per-analyte files are the pin, not the whole survey in git | Public-use data with a data-user agreement. | Unweighted percentiles for one or two analytes, labeled as not `WTPH2YR`-weighted. Not every person has every analyte. |
| LOINC and UCUM | Codes and units, not a copied terminology database. | None committed beyond codes the demo uses | LOINC: Regenstrief grants use, copy, and distribution, including commercial, with the required copyright notice. The website terms are a narrower site licence. UCUM: royalty-free for software interoperability, attribution, not a fork of a competing unit standard. | Store codes. Show the notice. |
| ClinicalTrials.gov | Not used | — | — | Dropped. A stored query is how the word “eligible” returns. The registry is not a card. |

### Real, credentialed, not in this repo

| Source | Why it is the right population, and why it is absent |
| --- | --- |
| UK Biobank | Large cohort with genetics, labs, and diagnoses. Applications were paused; new applications were described as intended for late 2026. Needs an application, an MTA, and fees. Cannot be committed. |
| All of Us | Genomics in the Controlled Tier inside the Researcher Workbench. Institution agreement, identity, training. No participant-level download into this database. Cannot be committed. |
| MIMIC | Credentialed on PhysioNet. The MIMIC-IV demo is about 100 patients, ODbL, without notes. That demo is not a rare-disease reference. |
| UDN | Participant-level data via dbGaP study `phs001232` under a data-access request. The version string differed across snippets (one said v5.p2; a synthesis said v7.p3). The version is UNCLEAR and is not asserted. Variant classifications that UDN submits to ClinVar are public and can be cited as ClinVar. PhenomeCentral submissions stopped 30 June 2024. Publications are citable. Participant files are not committed. |
| DECIPHER | Terms revised 22 July 2026. No copying of patient data. Bulk access needs an agreement. Out. |
| GenomeIndia | Controlled access, healthy reference, QC denominator not unique across pages. Out. |
| 1000 Genomes / HGDP | 1000 Genomes: no embargo after the final publication; cite the collection. The exact sample count was not re-opened this session and is not stated as a measured number here. HGDP’s licence page was not opened. UNCLEAR. Neither collection is a rare-disease cohort. Not committed. |
| GTEx | V8 public descriptions: on the order of 948 donors and 17,382 RNA-seq samples; V10 release notes that were opened cited 19,788 RNA-seq samples and 946 donors. Open-access expression and eQTL summaries exist. Raw sequence and full donor metadata are dbGaP `phs000424`. Not a v1 signal. |

### Open in licence, still not in the demo database

OpenSNP: donated genotypes under CC0 1.0, software MIT. A preprocessed dump of 5,000 datasets from February 2020 is described on GenomePrep. These are real people who consented to public release, including phenotype files and picture phenotypes. Consent to publication is not a design for a reference population, and faces do not belong in this repo.

Harvard Personal Genome Project: open consent, CC0, and participants are not promised anonymity. Same decision. Cite the project as an example of public genomes. Do not load them.

### Synthetic, and where it is a gimmick

Synthea (Apache-2.0) generates birth-to-death records from modules and public statistics, as FHIR or CSV. An NIH overview says rarer and more complex conditions may be absent, and that modules are not real EHRs. A module can set a genetic flag. It does not model a diagnostic odyssey and it does not validate a correlation. SYNRARE (arXiv `2607.09404v1`, not opened as a peer-reviewed paper) is a Synthea-based rare-disease generator with idealized trajectories. Use, if at all, as a fixture format. Do not report its output as an evaluation result.

The five demo cases are hand-written for this repo. They are not copied from a paper, OMIM, or GeneReviews. They plant a known lab outlier, a reported variant whose display must not move the phenotype likelihood, a phenotype pattern that should abstain, a phenotype pattern that should stay stable at both bin bounds, and a drug–gene quote that must not contain a dose. That is plumbing.

RareBench (Hugging Face `chenxz/RareBench`, card Apache-2.0; upstream case rights unclear; on the order of 150 MB) splits named in the card include RAMEDIS, MME, HMS, LIRICAL, and PUMCH. Published cases in a prompt or a training split are leakage. Off by default.

### PanelApp and Exomiser

PanelApp England software is Apache-2.0. Panel content had no redistribution grant on the pages opened. Australia panels were “research use” without an open redistribution licence. Panels are not committed. Exomiser’s code is AGPL-3.0 and its data bundle includes OMIM and, for some files, a non-commercial clause. It is not vendored. LIRICAL’s licence is Jackson Laboratory, non-commercial, non-transferable, non-sublicensable. Phenotype-only top-3 on 384 reports was 43.7% (Phenomizer 35.3%). Those figures are a citation, not a bar this repo restates as its own result. DeepRare (*Nature* 2026, [doi:10.1038/s41586-025-10097-9](https://www.nature.com/articles/s41586-025-10097-9)) reports HPO Recall@1 57.18% and, on 168 Xinhua cases, 69.1% versus Exomiser 55.9%, with rank judged by GPT-4o. The article is CC BY-NC-ND. The GitHub licence is `NOASSERTION`. Not vendored and not a target.

## 5. Evaluation

### What a pass is allowed to mean

A pass on synthetic cases means the plumbing matched the planted answer. A pass on the Phenopacket Store means the phenotype likelihood, using only HPO terms, put the published disease in the stated rank band on the 249 diseases that have a unique Orphanet map, against a baseline, with the 531 exclusions printed. A pass on NHANES means the percentile function matches a hand-computed percentile on a pinned extract. None of these is a discovered correlation. Calibration here means: when the reference is missing, the card abstains; when the card states a rank, the empirical hit rate on the store is reported beside the claim. It does not mean a probability that a new patient has the disease.

### Cases

| Set | Contents | What it can falsify |
| --- | --- | --- |
| Five synthetic cases | Planted outlier, zero likelihood diff when a variant card is added, abstention, stable likelihood, drug–gene quote with no dose, span trigger, gate tests (hash, double apply, revoked execute, pending row survives when the function is not called) | Plumbing and the safety assertions |
| Store `0.1.27`, unique-map subset | 249 diseases. Input is phenotypic features only. The truth OMIM id is the label. The HGNC symbol is not an input. | Whether the frequency-bin likelihood beats a degree baseline on percentage@k and precision@k |
| ClinVar-dated fixture | Two recorded classification strings for one accession, with dates. No network in the test. | The likelihood is unchanged; the displayed words can change |
| NHANES extract | The pin names the LOINC codes, age bands, and sex bands before any case is scored. Unweighted. | The population rank matches the extract, and a LOINC missing from the extract abstains |
| Published-case spot check | A handful of papers already inside the store, named by id, scored only from HPO | The same metric on a readable example, not a second hidden corpus |

The 200-packet file is a checksum fingerprint so a stranger can see they have the same slice. The full unique-map run is the reported result. “No confident likelihood” is not tuned on the five synthetic cases.

### Metrics

Pass bars are frozen before the store run. A miss fails `python -m eval`. It is not rewritten as “the result is the baseline.”

- Catalogue comparison, k = 1 and k = 5, both required. percentage@k is hits over all 249 labeled diseases, including diseases the list never returns and including abstentions. Abstaining on a likely miss and then quoting a hit rate among only the cards that stated a rank is not the pass. That conditional rate may be printed beside the reason codes. precision@k uses denominator k when the list is shorter than k. Ties take the worst rank. The 531 diseases outside the unique map are a printed exclusion count, not a silent drop. Both percentage@k and precision@k have to beat the degree baseline at each of those two k.
- Variant card: likelihood JSON identical after the variant card is added, and identical when HGNC symbols and genomic interpretations are removed from the packet.
- Population rank: exact match to the pin (LOINC, inequality, age band, sex band, unweighted 97.5 percentile of that extract). A LOINC missing from the extract abstains. A hand check that calls the same function is not a second implementation, so the expected percentile is computed in the test from the pinned rows and then compared. The pin file is written before any synthetic case is scored.
- Drug–gene: the quote is a substring of the pinned annotation. The forbidden-token check (dose units, “prescribe,” “eligible”) runs on every pinned ClinPGx row the demo can show, not only the planted card.
- Abstention is printed by card type. A card that emits a number when its reference row is absent fails. percentage@k is attached only to the catalogue comparison.
- Gate: the SQL tests in section 2.
- The fingerprint is the SHA-256 of the lexicographically first 200 JSON paths in the store zip, listed in a file next to the checksum of the zip. It is not a second metric.

Store cases and Orphanet frequencies may share the same papers. The hit rate is retrieval against that public table. It is not performance on a new patient. A PMID-overlap study is not a pass gate.

PhEval’s published metric names (Bridges et al., BMC Bioinformatics 2025;26:87; that paper used store 0.1.12) may appear as extra columns on the TSV. MRR, MAP, and NDCG are not pass gates. This file is not the Sage RAPID platform.

### Baselines and ablations

- Degree baseline: for each present HPO term, frequency is the fraction of the 249 unique-map diseases whose pinned Orphanet phenotype row lists that term in any bin other than excluded. The baseline score is the sum of the negative log of those frequencies. Terms absent from that file add nothing. The corpus is `en_product4` plus the MONDO unique-map list. `phenotype.hpoa` is not loaded. `en_product6` is not an input. The catalogue comparison has to beat this baseline at k = 1 and k = 5 on both percentage@k and precision@k. If it does not, the eval fails.
- Lab note range: a value outside a range typed on the synthetic report is a different comparison. The population-rank card must not be described as confirming that range.
- Ablation, phenotype: drop frequency bins and keep only the degree score. The delta is the bins.
- Ablation, variant: add the variant card, and separately strip gene symbols. Likelihood JSON identical both times.
- Ablation, medication: remove the drug. The copied-sentence card disappears. Other cards stay.
- Ablation, NHANES file: remove the extract. Population-rank cards abstain.
- Extractor: the gazetteer must propose each planted code on the five notes with a span the trigger accepts. Likelihood invariance is tested only when the accepted facts are the same. A skipped Gemini run is a pass of the key-off path, not evidence the model would have matched the gazetteer.

### Leakage

- The extractor prompt, if a model is on, contains the note and a list of allowed codes. It does not contain a PMID, a filename, a cohort name, an abstract, or the disease label. A test scans the prompt.
- The likelihood function’s inputs are accepted HPO ids and the pinned Orphanet and MONDO files. A test imports the function and asserts the signature has no text and no gene-symbol parameter.
- Store packets are not copied into the five demo notes.
- RareBench and DeepRare case text are not loaded.
- ClinVar and literature text are not concatenated into the likelihood.

### What a stranger can reproduce

Pins: store zip checksum, MONDO version, Orphanet file dates, NHANES cycle and analyte filename, ClinPGx file version, scorer version. `docker compose up`, `pytest` on the five cases and the SQL gate, `python -m eval` printing percentage@k, precision@k, the exclusion count, and the abstention counts. No API key. The Gemini comparison is skipped when the key is absent, and the skip is a pass of the “key off” path, not a hidden failure. The full store run is documented as a local download, not as a CI fetch on every push.

## 6. Terraform, pilot, scaling, cost

### Pilot

One operator, one browser, five synthetic cases. `docker compose up` starts the API and Postgres. No account beyond a local demo session whose user name is fixed in the session cookie and read back with `SET LOCAL`. The walked path the tests follow: reject a draft, accept a draft, see one observation; edit a draft and confirm the old hash cannot approve the new body; click accept twice and see one effect; add a variant card and see the likelihood unchanged; a lab in the pin gets a population rank; a lab missing from the extract abstains; a drug card quotes and does not dose.

That demo does not exist until building is approved. A ten-minute reading after that is Compose, `pytest`, and one `psql` session showing a pending draft that is still pending when the function has not been called.

### Productionization sketch

Compose on one machine is the deployment. Neon’s free project can replace `DATABASE_URL`. AWS is not created for this pilot.

Sketch only, not applied, and not a file in the tree: a later Terraform configuration would declare one Postgres instance and the API’s environment variables (`DATABASE_URL`, no NCBI key on the API). It would not declare a GPU, a VCF bucket, or a public literature service. Applying it is a separate decision. The trigger to write the real HCL is the same as the trigger to leave Compose: the one box is too small, or a covered entity is in the conversation. The second of those stops the project.

### Scaling triggers

- Postgres above about 0.7 GB, or a Neon project near its CU-hour cap: the knowledge base is already on disk. Pay for the database or keep Compose. Do not load ClinVar XML.
- A second organization: a separate database.
- Anyone asks to load a real chart or a VCF: stop.

### Cost, at the pilot described here

| Item | Cost |
| --- | --- |
| Neon free, or local Postgres | $0 |
| GitHub | $0 |
| HPO, Orphanet Science, MONDO, Phenopacket Store, ClinVar E-utilities, NHANES public-use, ClinPGx/CPIC downloads, LOINC codes | $0 |
| Gemini free tier, synthetic text only, key optional | $0. Off when the key is unset. Do not link billing. |
| NCBI key | unset |
| LangSmith, Medplum, AWS, Terraform apply | $0, not used |
| OMIM licence, Exomiser data, UK Biobank, All of Us | $0, not purchased |

The first cost appears only if someone links a paid model, applies the AWS sketch, or pays a cohort access fee. The README says the demo does not need those.

## 7. CLEAR, UNCLEAR, and open questions

### CLEAR

- The product is separate cards (population rank, catalogue comparison, quoted variant display, copied drug–gene sentence). History facts stay on the timeline. A fused score is out. gnomAD is not on the variant card. FHIR, MCP, A2A, and trial links are not in v1.
- Store `0.1.27` census and the 249/780 unique map, measured locally on 9 October 2026.
- FDA January 2026 CDS guidance: all four criteria; sequence or VCF in, variants or their clinical implications out, fails Criterion 1. Town hall 11 March 2026. Accepting a draft does not repair that failure.
- v1 takes already-reported classifications and does not parse a VCF. Putting a VCF in scope makes that function fail Criterion 1 on the guidance’s examples.
- NHANES August 2021–August 2023: 11,933 interviewed, 8,860 examined. v1 percentiles are unweighted and say so.
- gnomAD v4 counts on the homepage and downloads page: 730,947 exomes and 76,215 genomes. The dump is not committed.
- ClinPGx replaced PharmGKB on 30 July 2025. CPIC curated content is CC0 with an attribution request and an explicit “not a substitute for judgment” line. This plan quotes and does not dose.
- Synthea does not validate correlations. Credentialed cohorts cannot be committed.
- The approval gate is a Postgres function whose execute privilege is revoked from the public role. Reviewer identity is a session setting. LangGraph is not the workflow.
- Epidemiology, RAPID caps, GeneDx–Fabric, NPRD, and GenomeIndia access as stated in section 1, from the earlier pass.
- Neon free-tier limits as cited.
- Job-ad rates from the 418-posting sample describe what postings mention. They are not a customer and they do not put a protocol into this repo. A2A was about 3% of that sample. v1 does not use A2A.

### UNCLEAR

- gnomAD’s Broad policies page was not fully fetched. CC0 on a regional mirror is not adopted. v1 does not show a frequency and does not ship a fixture that the card renderer can import.
- ClinPGx data-use page did not render. The blog’s CC BY-SA 4.0 statement is what loaded. Share-alike on a small pinned extract needs a second read of the rendered policy before a public redistribution.
- 1000 Genomes sample count and the HGDP licence page. Not used either way.
- UDN dbGaP version string.
- Dai full text (Cloudflare). The 60% literature share stays a meeting abstract.
- Whether a phenotype likelihood plus a quoted lab classification, with no VCF, is non-device CDS. The guidance settles the VCF case. It does not issue a blessing for the likelihood card.
- HPO canonical licence IRI still 404. Working text is the GitHub pages licence. Counsel on vendoring the unmodified obo is still wise. Nothing is vendored until approval; setup downloads.
- GenomeIndia’s three QC denominators.
- The $15.6 million between RAPID’s $98.5 million and the four performer caps.
- DPDP commencement. Lawyer.
- Gemini free-tier model ids and rate limits. Official pages confirmed a free tier and the training-use clause. They did not confirm a blog’s model names.
- Two DeepLearning.AI lesson titles that did not render in the earlier pass. Section 8 lists titles that did, and marks the ones this design does not use.
- Why 30 MONDO maps are multi-mapped, and why 501 store diseases have no Orphanet xref. The join to the June 2026 Orphanet file was not done.

### NEEDS MORE INFORMATION

1. gnomAD licence. The Broad policies page is still unread. The plan shows no allele frequency. Say if a frequency line should be added after that page is logged. The plan’s answer until then is no.
2. FHIR is dropped. Say if a disk Bundle should come back. The plan’s answer is no.
3. Gemini stays off without a key. Say if the free tier should be on by default. The plan’s answer is no, because free-tier prompts may be used to improve Google products and the gazetteer covers the demo.
4. A clinician is not recruited. Say if someone should read the five synthetic cards before any UI is built.
5. India remains a policy section. An NRCeS mapping is a different project.

### Top open questions

- Publish, at setup, the fraction of the 699 store genes that appear in Orphanet `en_product6`, next to the phenotype metrics. The gene is still not a score input.
- A second dated Orphanet Science file, if one is published, is what would make a knowledge-base diff meaningful. Until then there is no “the frequencies moved” claim.
- Matchmaker Exchange stays unimplemented.
- PanelApp content stays out until a redistribution right is written down.

## 8. DeepLearning.AI course mapping

Lesson titles are ones that rendered on a public course page in the earlier research. This table says which lessons the correlator still uses. Voice and image courses stay listed so the omission is deliberate.

| Course | Lesson titles that were visible | Still used? |
| --- | --- | --- |
| AI Agents in LangGraph | Introduction; Build an Agent from Scratch; LangGraph Components; Agentic Search Tools; Persistence and Streaming; Human in the loop; Essay Writer | Deliberately unused. The filmed human-in-the-loop lesson pauses a graph. This gate is SQL, because a graph pause double-fired a side effect in the integrated-plan exercise. |
| Long-Term Agentic Memory with LangGraph | Introduction to Agent Memory; Baseline Email Assistant; semantic, episodic, and procedural sequels that rendered | Unused as a design. Accepted facts are Postgres rows. The email assistant is not built. |
| LangChain: Chat with Your Data | Introduction; Document Splitting; Vectorstores and Embedding; Retrieval; Question Answering | Deliberately unused. No retrieval card. |
| Evaluating AI Agents | Introduction; Evaluation in the time of LLMs; Decomposing agents; tracing; router and skill evaluations; trajectory evaluations; structure; LLM-as-a-judge; monitoring | The evaluation section is the part that applies, and it is ordinary tests. LLM-as-a-judge does not set a likelihood or an alarm. |
| Agentic AI | What is agentic AI?; Degrees of autonomy; Task decomposition; Evaluating agentic AI; tools and MCP lessons that rendered | Deliberately unused as a runtime. Comparisons are functions with no autonomy. The MCP lessons have no client in this repo. |
| A2A: The Agent2Agent Protocol | Introduction; Why Agent2Agent Protocol?; A2A Architecture; Wrapping the QA Agent into an A2A Server; Advanced A2A Concepts | Deliberately unused. No literature card, no foreign credential. About 3% of the 418-posting sample mentioned A2A. That rate is not a reason to add a container. |
| MCP with Anthropic | Introduction; Chatbot Example; Creating an MCP Server | Deliberately unused. No MCP client. Authorization on the course page was still roadmap text. |
| Governing AI Agents | Introduction; What is AI Agent Governance?; Establishing Governance in Catalogs; Building, Evaluating & Deploying Agents | The decision row and the revoked `EXECUTE` are the part that applies. No Unity Catalog. No NCBI key. |
| Building Adaptive AI Agents | Introduction; Overview of Continual Learning; Behavior Adaptation; Knowledge Adaptation Through Code Graphs | Unused. Drafts are not auto-promoted. A person accepts them. No fine-tune. |
| Agent Memory | Introduction; Why AI Agents Need Memory; Constructing The Memory Manager; semantic tool memory; Memory Aware Agent | Unused. There is no memory manager writing back into a score. |
| Building Live Voice Agents with Google’s ADK | Introduction; Running Voice Agents; Tools; research agent; guardrails; multi-agent orchestration | No rare-disease voice lesson. Out of scope. |
| Building AI Voice Agents for Production | Introduction; Voice Agent Overview; End-to-end architecture; Voice Agent Components; Optimizing Latency | Out of scope. |
| Multimodal Search and RAG | Introduction; Overview of Multimodality; Multimodal Search; Large Multimodal Models; Multimodal RAG | Faces and pixels stay out. Report text is a note, not this course. |

## 9. What changed, and what review still has to do

The previous plan’s product was a phenotype ranker with a next question, a ClinVar row that did not move the score, and a LangGraph accept path. Reviewers of that plan tightened the metric, the abstention rule, the span trigger, and the market language. Those constraints are kept where they still apply: unique-map denominator 249/780, bin bounds, truth gene held out, ties take the worst rank, precision@k beside percentage@k, a degree baseline, span trigger, disk FHIR with no Condition, Compose Postgres, no HCL applied, synthetic rows only, RUO label, Matchmaker off.

Replaced:

- The ranker is one card, headed “catalogue comparison.” A population rank and a copied drug–gene sentence are other cards. They are not multiplied into one score. History is a timeline fact, not an alarm.
- Trial queries are not stored. FHIR is not written. MCP and A2A are not in the layout.
- LangGraph is not the workflow. The gate is `apply_decision`, owned by a `NOLOGIN` role, with execute revoked from the public role and `search_path` fixed. A graph pause had double-applied a side effect, committed an edited body under an old hash, applied two resumes, and could drop a pending approval when the node was renamed.
- The review UI is a form. gnomAD frequency is not shown beside a classification.
- Pass bars: k = 1 and k = 5, abstentions count as misses, a miss fails the eval, the degree baseline’s corpus is the 249’s Orphanet phenotype rows.
- The reference gap is a limit on what a pass means. Credentialed cohorts stay out. Synthea is plumbing.

[docs/review.md](docs/review.md) records what this critic pass changed.
