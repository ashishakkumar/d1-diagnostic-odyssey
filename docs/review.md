# Review of the correlator plan

Five reviews read `PLAN.md` after it had been rewritten from the HPO-to-Orphanet ranker into a multi-omics correlator. They did not run web searches. The ranker review that used to live in this file is superseded. What it had already forced, and this plan still uses, is listed at the end.

## Evaluator

Verdict was revise. Synthetic patients still cannot validate a correlation, and that sentence was already tight enough. A pass could still be tuned: k was unnamed, a miss could be reported as “the result is the baseline,” abstentions could be dropped before the hit rate, the degree baseline had no corpus, the NHANES pin did not name its analyte, and a signature check did not prove the gene was held out.

Adopted in section 5:

- k is 1 and 5. Both percentage@k and precision@k must beat the degree baseline at each k. A miss fails the eval.
- The pass denominator is all 249 unique-map diseases. Abstentions are misses. A conditional hit rate among cards that stated a rank may be printed and is not the pass.
- “At least 10 diseases” and “a factor of 2” are frozen in the pin before the store run. Refitting them fails the eval.
- The degree baseline’s frequency is the fraction of those 249 diseases whose pinned Orphanet phenotype row lists the term in any bin other than excluded. `phenotype.hpoa` is not the corpus. `en_product6` is not an input.
- The NHANES pin names LOINC, age band, sex band, and the unweighted 97.5-percentile rule before any case is scored. The expected percentile is computed from the pinned rows in the test.
- Holdout is an execution check: stripping HGNC symbols and genomic interpretations leaves the likelihood JSON identical.
- The gazetteer must propose each planted code with a span the trigger accepts. Likelihood invariance is only claimed when the accepted facts are the same.
- Abstention is printed by card type. The dose-token check covers every pinned ClinPGx row the demo can show.
- One sentence states that store cases and Orphanet frequencies may share papers, so the hit rate is not performance on a new patient.

Declined: a fused calibration score (ECE or Brier) across percentile, quote, and likelihood; Synthea, RareBench, or a credentialed cohort as the way to discover a correlation; putting the store gene into the score; MRR, MAP, and NDCG as pass gates; fetching the store on every CI run.

## Optimizer

The LangGraph refusal was judged honest. MCP and A2A were judged ceremonial. The disk FHIR Bundle and the trial-link sentence had no reader.

Adopted:

- MCP is not in the layout. No adapter, no client.
- A2A and the literature container are not in the layout. v1 has no literature card and no NCBI key. A second process does not isolate a secret the demo does not have.
- FHIR is dropped. No Bundle, no `FHIR_BASE_URL`.
- Trial queries are not stored.
- Family history, exposures, imaging text, and social history are timeline facts after acceptance. They are not alarm cards. Vitals with a LOINC code are labs.
- No separate `app.audit` table. The decision row is the record.
- gnomAD is not loaded and is not on the variant card. ClinGen is not a v1 citation on the card.

Declined, because this brief asks for them:

- Deleting the agents-not-used table, the DeepLearning.AI mapping, the Terraform sketch, and the cost table. The table is shorter than the ranker plan’s agent design. The course rows say which lessons are unused. The Terraform sketch stays prose and is not applied.
- Deleting the 418-posting rates entirely. They stay as a description of what postings mention, next to the sentence that they are not a customer.
- Deleting Gemini as an optional key-off extractor. The gazetteer is the demo. The model stays off without a key.
- Deleting the PhEval-shaped columns. They are not pass gates. The TSV can still carry the names.

## Investors

a16z Bio+Health, General Catalyst, Bessemer, Menlo, an ARPA-H RAPID reading, and a diagnostics-lab investor each said they would not fund a company from this plan. That was also their answer to the ranker. The objection moved. The ranker was a score with no buyer. The correlator states that synthetic patients cannot discover a correlation and that UK Biobank, All of Us, MIMIC, and GenomeIndia cannot be committed. A written gap is still not a visit, a dataset award, or a lab test.

Adopted in the opening and in section 1: the demo user is one operator on five synthetic charts; the people in Faye and Chung are the published record, not users of this repo; the title’s first paragraph says research demo; job-ad rates are not a customer; the RAPID six-year sentence remains only as a sentence this plan does not adopt. The hemoglobin wording example no longer pretends to be a computed NHANES result.

Declined: renaming the plan away from the owner’s correlator. The card headers in section 2 are the narrower words (“population rank,” “catalogue comparison,” “copied sentence”). The owner’s three nouns are defined there so they are not the chrome.

## Clinician

A non-geneticist will fuse four cards. “Risk signal,” “likelihood,” and “a clinician may want to look” do that fusion. A gnomAD frequency beside a lab class is read as a rarity criterion. A family-history alarm that repeats an accepted fact is noise. A ClinVar quote can be read as an update of the lab. A CPIC sentence can be read as an order.

Adopted as the card text in section 2: population rank is not a reference interval and not a reason to repeat or treat; a missing row is a missing file, not a normal result; the catalogue comparison is not the probability of the disease and does not take the variant as input; the two variant quotes are not reconciled; the drug card says any avoid/reduce wording belongs to the guideline; history is “accepted fact, restated,” with no risk calculated; no allele frequency on the variant card while the Broad licence page is unread.

Declined: dropping the catalogue comparison. It is one card, with the 531 exclusions printed. The clinician’s risk was the header, not the existence of the frequency table.

## Stack

The four LangGraph failures were already the reason for the function. Holes remained: the API role could own the function, `search_path` was unset, the client could supply the hash, edit and supersede could split, a pooler could carry a session setting, and a second call could write the snapshot outside the decision.

Adopted in the gate sketch: `NOLOGIN` table owner; API role `NOINHERIT` and not a member of the owner; `SECURITY DEFINER` with `SET search_path = pg_catalog, app`; `REVOKE CREATE` on `public` and `app`; `set_config(..., true)` in the same transaction as the call; canonical JSON and the hash computed by a trigger; `body` frozen; status updates only from `pending` to `superseded`; edit and supersede in one transaction; snapshot rows only inside `apply_decision` in that same transaction; tests for owner, privileges, pooled settings, and hash mismatch.

There is no MCP tool list and no literature database role to bypass the function, because those processes are not in the plan.

## What the ranker review had already changed, still in force

The earlier pass on the ranker (evaluator, optimizer, the same investor panel, clinician, hiring manager) fixed the phenotype metric and the market tone. This plan keeps: unique-map denominator 249 of 780; bin bounds; truth gene held out of the function; ties take the worst rank; precision@k beside percentage@k; span trigger rather than a cross-table `CHECK`; Compose Postgres; knowledge-base files on disk; synthetic rows only; RUO label; Matchmaker off; no applied HCL.

That pass had kept assistant-ui, a literature A2A profile, and a disk FHIR Bundle because the ranker brief asked for them. This brief’s critics cut all three. The accept gate is a form. The only writer is the Postgres function.
