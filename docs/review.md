# Review of the plan

Four reviews read `PLAN.md` after the dossier had already been checked against primary pages. They did not run new web searches. The search log is unchanged by this pass.

## Evaluator

Verdict was revise. A scorer that received the truth gene, tied every gene for rank 1, or fit “no confident score” on the same five notes could have stayed green.

Adopted in section 5: HPO-only inputs on the public gene score; truth symbol is a label; ties take the worst rank; genes missing from Orphanet stay in the denominator; precision@k beside percentage@k; a degree baseline that has to be beaten; the abstention rule fixed before any score is inspected; prompts that contain a PMID, filename, cohort name, abstract, or disease label fail the run; a phenotype accept has a hand-written expected disease; ClinVar and a literature quote leave the score list unchanged. The 200-packet file is a fingerprint. The full 10,377-packet run is the result.

The unique-map count is 249 of 780, not a 35.8% ceiling used as the metric denominator. 279 map to at least one Orphanet id, and 30 of those map to more than one.

## Optimizer

Adopted: score list inside the snapshot; knowledge-base files on disk; MCP in-process; literature container off the default Compose path; Resnik’s Monte Carlo p-value off the stranger-run path; no Terraform HCL in the tree.

Kept, because the brief requires them: a FHIR Bundle written after accept, with the HTTP call off unless a base URL is set; an A2A literature service for the credential boundary, behind a Compose profile.

## Investors

a16z Bio+Health, General Catalyst, Bessemer, Menlo, an ARPA-H RAPID reading, and a diagnostics-lab investor each said they would not fund a company from this plan. The plan already said it was not a company. Sentences that still sounded like demand were removed: a geneticist’s unasked question, a counselor who must notice a lab reanalysis, a CPT 81417 dollar figure, “the slice worth building,” “if Sage publishes a benchmark, this repo should emit it,” and the claim that job ads choose the scorer. The RAPID six-year average is quoted only to say this plan does not adopt it.

## Clinician

Adopted: questions are at most five terms that flip score-order 1, nonspecific terms are ineligible, the tab is empty when the score abstains, bin bounds replace midpoints, descendant-max frequency is out, the header says the list is not a diagnosis, and the five synthetic cases are specified so a nonspecific chart abstains and a recognizable finding does not.

Declined: removing any ClinVar diff at all. The brief asks for a reanalysis diff. The diff is stored and asserted to be zero. Also declined: making disease rank the only public number. Gene percentage@k is printed with its denominator because 531 of 780 store diseases have no unique Orphanet id. The screen still orders diseases.

## Hiring manager and stack

Adopted: one API process; the span rule as a trigger; Compose Postgres as the demo database; no HAPI; no ECS module; the ten-minute demo described as tests that do not exist yet.

Declined: removing assistant-ui. The brief asks for it. The composer is not the accept gate, which is the part those libraries get wrong. Declined: deleting A2A. The brief requires it for a credentialed separate process. It is not required to compute a score.
