# Finish report

For research use only. Not for use in diagnostic procedures.

This notebook is a synthetic case file. It does not diagnose. `make demo` resets the local database and opens the one-step notebook at <http://127.0.0.1:3000>.

Pull request #9 is the finish PR for the whole app. Its base is `main`. It is not a draft. The head branch is `cursor/finish-odyssey-demo-79af`.

The multi-omics slice is the opt-in allele-frequency prior in `services/api/app/data/allele_frequencies.json` (`NM_000138.5:c.1A>G`, 0.00012, source `fixture-allele-frequency`). It is experimental and non-diagnostic. This build did not call gnomAD or ClinVar. The prior does not change the catalogue comparison. No model is used for it.

## What a person can run

The landing is one step. Pick one of the five synthetic cases, or paste or upload a short synthetic note. There is no sign-in wall and no symptom form. The next screen is one pipeline, labeled Read, Map, Match, and Rank. Each stage says what the software did. Extraction is a fixed lexicon. The page says no language model ran, and that the free-tier quota is closed until 2026-10-12 00:00 UTC. Ranks are Resnik best-match average on the ten-row synthetic table. The page says this is not the 249-disease held-out run. The person then confirms or corrects the chips. That click is the only write on this path. It goes through `app.apply_decision`. With no session cookie the reviewer is `synthetic-reader`. A note that matches a warning sign returns 409 with the stop screen and is not saved. The India footer still shows 112.

`POST /demo/cases/{slug}/load` still writes the five frequency-bin stories through the same gate. That summary is the frequency-bin card: Separated rows leads with ORPHA:9000001 and a ratio of zero; No separated row abstains with `many_within_factor`; Stable at both ends keeps a finite margin; the variant case does not move that comparison; the opt-in prior still shows 0.00012 from the fixture and says this build did not call gnomAD or ClinVar. The landing ranker does not retell those margins. On the landing, Separated rows and the variant note lead with ORPHA:9000001. A seizure-only note scores zero because that term is on every synthetic row, so the page says not enough signal. The stable pair shares the best Resnik score, so the page abstains there too. The limits note adds the approved sentence that this page does not choose a dose.

`make e2e` runs the landing path in Chromium and writes `docs/demo-screenshots/01-cases.png` through `07-stop.png`.

| Case on the landing | What the page shows |
| --- | --- |
| Separated rows | Lexicon chips for long fingers and flat cheeks. ORPHA:9000001 has the highest Resnik score on the synthetic table. |
| No separated row | Not enough signal. The seizure term is on every synthetic row, so the best score is zero. |
| Stable at both ends | ORPHA:9000011 and ORPHA:9000012 share the best score, so the page abstains. |
| Variant does not move the comparison | Same chips as Separated rows. The note names FBN1. Resnik did not use it. |
| No dose on this page | Same abstention as the stable pair, plus the sentence that this page does not choose a dose. A pasted "Unconsciousness." shows the stop screen. |

## Scorer

The synthetic notebook card is frequency-bin 0.0.2. The public-case ranker is Resnik best-match average. The measurement for the card is [scorer-0.0.2.md](scorer-0.0.2.md). The one held-out look at the public-case ranker is [../eval/bars-resnik.md](../eval/bars-resnik.md). Pull request #8 recorded the same full-set frequency-bin rows; this branch re-ran `d1_eval store` after wiring that background into the scorer the notebook calls. Phenopacket Store 0.1.27 (sha256 `d0c70005bb09b87035087516252b6b539fbc0415be7c664b73c9cde7eedf205a`). 531 diseases are excluded because they are not a unique Orphanet id. `packets_skipped` is 0. 4,815 packets are scored. Abstentions count as misses. `CLOSE_DISEASE_COUNT` stays 10 and `CLOSE_FACTOR` stays 2.0. They were not refit.

`P(feature | not this disease) = (k + 1) / (n + 2)` on every disorder in Orphadata Science `en_product4`, including disorders that are not ranked. A missing row contributes a ratio of 1. Full-set top-1 is 1395/4815 (top-3 1732/4815, top-10 2026/4815, no-confident 1645/4815). The held-out split is SHA-256 of the packet id, modulo 5, remainder 0 is test. It was not used to choose a threshold, a background, or a bin edge. Full top-1 is 1129/3890 on train and 266/925 on test. 1129 + 266 = 1395. The other degradations are in `eval/RESULTS.md`. `d1_eval store` prints those frequency-bin totals and a separate line labeled `term-overlap-loo`.

Frequency-bin 0.0.1, the flat background 0.05, had full-set top-1 1292/4815 and held-out test top-1 246/925. Those rows stay in `eval/RESULTS.md` under the heading Archived frequency-bin 0.0.1. They are not the shipped scorer.

Term-overlap-loo full-set top-1 is 3806/4815, with 104/4815 abstentions, and held-out test top-1 731/925. It reads HPO labels from other packets in the same release. That is label leakage, not an external catalogue. The test catalogue still includes train packets. It is not shipped.

An ancestor climb was measured on the 0.0.1 flat background. Full-set top-1 fell from 1292/4815 to 841/4815. On the 0.0.2 corpus background the same climb was measured on train packets only, with no abstention: top-1 fell from 1172/3890 to 717/3890. That climb is not shipped. The notebook and `d1_eval store` do not pass a parent map.

Degree baseline and precision@k were measured on this pass for the shipped frequency-bin 0.0.2 scorer. No parent map. `CLOSE_DISEASE_COUNT` and `CLOSE_FACTOR` were not refit. The held-out split was not used to choose a threshold. Packet top-1 stayed 1395/4815, train 1129/3890, test 266/925, which matches the earlier store run. The full table is [../eval/bars-0.0.2.md](../eval/bars-0.0.2.md) and the same section at the top of `eval/RESULTS.md`.

| cohort | k | frequency-bin | degree baseline |
| --- | --- | --- | --- |
| all 4815 packets | 1 | 1395/4815 (0.289720) | 1647/4815 (0.342056) |
| all 4815 packets | 5 | 1871/4815 (0.388577), precision@5 0.077715 | 2665/4815 (0.553479), precision@5 0.110696 |
| test 925 packets | 1 | 266/925 (0.287568) | 327/925 (0.353514) |
| test 925 packets | 5 | 370/925 (0.400000), precision@5 0.080000 | 533/925 (0.576216), precision@5 0.115243 |
| 249 diseases, unweighted mean | 1 | percentage 0.353135, precision 0.353135 | percentage 0.355850, precision 0.355850 |
| 249 diseases, unweighted mean | 5 | percentage 0.457476, precision 0.091495 | percentage 0.536436, precision 0.107287 |

precision@k is the mean of 1/k on a hit and 0 on a miss, so precision@1 equals percentage@1. The denominator stays k when the list is shorter than k. Abstentions are misses. Ties take the worst rank. Frequency-bin does not beat the degree baseline on percentage@k or precision@k at k = 1 or k = 5. That pass bar is not met for frequency-bin.

Train-only diagnosis, 3890 packets, test packets left out: frequency-bin with its catalogue abstention is 1129/3890 at k=1 and 1501/3890 at k=5. Ranking the lower ratios anyway, with no abstention, is 1172/3890 and 1983/3890. Both stay behind the degree baseline on train (1320/3890 and 2132/3890). Truth-disease lower ratio 0, an excluded bin zeroing the product, is 18/3890. Of 33952 train query terms, 11862 are an exact non-excluded annotation of the truth disease, and a further 12650 have an ancestor in that disease's annotation closure. The frequency-bin product does not use that ancestor relation. A parent climb inside the product makes the train top-1 worse, as above. A listed bin can also score below a missing row, because a missing row contributes ratio 1 and a bin lower bound below the corpus background contributes less.

Candidates were scored on fit and validation only. Validation is the train packets whose SHA-256(packet id, newline, "validation") modulo 4 is 0: 993 packets. Fit is the other 2897 train packets. The 925 test packets were skipped. Abstention for each candidate was chosen on fit by higher percentage@1, then percentage@5. Every candidate stayed on `raw` (abstain only when the best score is at or below zero), because extra abstention only removes hits. The degree baseline kept its published rule (best score at or below zero, or at least 10 diseases tied at the best score). A candidate beats that baseline on validation when percentage@k and precision@k at k=1 and k=5 are all strictly greater. Resnik best-match average won: validation k=1 467/993 (0.470292) against degree 328/993 (0.330312), and k=5 627/993 (0.631420), precision 0.126284, against degree 526/993 (0.529708), precision 0.105942. Information-content overlap, the one-way phenomizer mean, and BM25 also beat the degree baseline on validation and were not selected, because Resnik's validation percentage@1 was higher. The degree-prior-corrected frequency scorer did not beat the baseline on validation (k=1 303/993, k=5 498/993). The selection record is `eval/choice.json`. It was not rewritten after the test look except to set `test_scored` true.

The held-out look scored only Resnik best-match average, with the fit-chosen `raw` abstention, against the degree baseline. Degree on that split matches the earlier bar: 327/925 at k=1 and 533/925 at k=5.

| cohort | k | Resnik best-match average | degree baseline |
| --- | --- | --- | --- |
| test 925 packets | 1 | 419/925 (0.452973) | 327/925 (0.353514) |
| test 925 packets | 5 | 614/925 (0.663784), precision@5 0.132757 | 533/925 (0.576216), precision@5 0.115243 |
| 165 of 249 diseases with a test packet | 1 | percentage 0.480944, precision 0.480944 | percentage 0.386210, precision 0.386210 |
| 165 of 249 diseases with a test packet | 5 | percentage 0.665217, precision 0.133043 | percentage 0.553540, precision 0.110708 |

Diseases with no test packet are left out of that mean. 84 of the 249 unique-map diseases have no test packet. Resnik best-match average beats the degree baseline on percentage@k and precision@k at k=1 and k=5, on the test packets and on the diseases that have a test packet. Adding a decoy gene to each of the 925 test packets left the present HPO ids unchanged, recorded the decoy gene, and left the Resnik scores unchanged. Rebuild failures: 0.

The comparison panel states that the rows on the page are the synthetic frequency-bin card, and that the public-case ranker beats the degree baseline at k=1 and k=5. The five synthetic stories stay on the frequency-bin card, including the abstention when many rows sit within a factor of two. The public-case abstention is the fit-chosen rule and is not the rule on that card.

## Measured on this revision

- `make test`: 239 passed, 1 skipped. The skipped test is the opt-in live model smoke. It was not run. The OpenAPI drift tests passed in this run. Gemini-to-OpenRouter `:free` coverage is the stubbed 429 tests only.
- Cold `make e2e`: 1 passed (11.3s). The comparison panel shows the public-case ranker sentence. The abstain page does not show a numeric margin.
- `d1_eval heldout`: exit 0. Resnik best-match average on the 925 test packets beats the degree baseline at k=1 (419/925 vs 327/925) and at k=5 (614/925 vs 533/925). Frequency-bin packet top-1 stays 1395/4815 and does not beat the degree baseline.

## Contract, prior, and model client

`contracts/openapi.json` is generated from the FastAPI app. `contracts/ts/src/api.ts` is generated from that document. `tests/test_openapi.py` fails if either file drifts. The report response leaves unset fields out, so a catalogue comparison does not carry a `probability` without a reliability curve. `margin` is still present when it is null, and `margin_reason` says `runner_up_ratio_is_zero` when the runner-up lower ratio is 0.

`services/llm` calls Gemini first through `complete_with_gemini`. That function reads `GEMINI_API_KEY` or `GOOGLE_API_KEY`, follows every `nextPageToken` on `GET https://generativelanguage.googleapis.com/v1beta/models`, and chooses the newest flash-lite id from that list. The chosen id is stored on the completion. OpenRouter is used only after a Gemini 429 or `RESOURCE_EXHAUSTED`, including a 429 while listing models, and only for model ids that end in `:free`, with backoff and a SHA-256 replay cache. Text must contain `SYNTHETIC-ONLY` or the client refuses it before any HTTP call. When `OPENROUTER_FREE_MODELS` is unset or blank, the client uses the non-empty priced-zero default in `DEFAULT_OPENROUTER_FREE_MODELS`. A set list replaces it. With no Gemini key or no fallback key, the client returns pinned wording, records provider `gazetteer`, and does not call OpenRouter. A gazetteer sentence is logged and is not written into the replay cache, so a key added later is not hidden. Keys stay in gitignored `uploads/` and `.env` files. One opt-in smoke (`D4_LLM_LIVE=1`) completed a single `:free` fallback call. The other LLM tests use stubs.

Synthetic open-band note segmentation, and the replay fixtures for those nine notes, were removed. They came from a paperwork task sent to this repo by mistake. They do not ground catalogue terms.

The implementation review is [code-review.md](code-review.md). `docs/review.md` stays the plan critique.

## Self-review

Fixed while finishing:

- The warning-sign button was in the server HTML before React attached the click handler. A full navigation could drop the click, so the stop screen never appeared. The button stays disabled until the page is mounted, and Playwright waits for that.
- `make e2e` was starting Playwright from the repo root, so it loaded Vitest files. It now runs from `apps/web`.
- Several sentences appear both in the comparison panel and in the summary text. The browser test uses the first match.
- `.gitignore` used `data/`, which hid `services/api/app/data/allele_frequencies.json`. The download directory is `/data/` only, and a test checks the fixture is not ignored.
- Approving several rows in one transaction gives them the same `decided_at`. Ordering by decision id then shuffled the evidence list, so two cases with the same terms could differ. The comparison sorts terms by HPO id. The timeline stays newest-first.
- FastAPI was adding `"probability": null` from the report model default. The report route uses `response_model_exclude_unset`, so an unset probability is absent and a null margin stays.
- The store command was scoring the ancestor climb while the notebook scored exact rows. The command now scores the shipped exact-match scorer. The climb result is recorded above and in the results note.
- An inline import in the held-out test was moved to the top of the file.
- A warning-sign click whose request never reached the API left the page blank. The page now says the notebook cannot reach the API.
- An abstained catalogue comparison showed `Margin 1.000` while the summary already omitted it. The panel now hides the number when the report abstains. The API still returns margin 1 for that tie.
- Playwright starts `.venv/bin/python scripts/demo.py` with working directory `../..` from `apps/web`, which is the repo root. `cwd: ".."` is only the `apps` directory. A cold `make e2e` with nothing listening on ports 3000 and 8000 started the API and passed.
- `d1_eval store` printed the term-overlap-loo top-1 without a label. The summary now names frequency-bin first and labels the stand-in.
- The generated TypeScript client treated OpenAPI `const` as `string`. `margin_reason` is the literal `runner_up_ratio_is_zero` or null.
- A Gemini success did not record the model id, and nothing read `GEMINI_API_KEY`. `complete_with_gemini` lists the models pages, calls the chosen id, and stores it. A missing key degrades without HTTP.

Left as they are:

- The stop paragraph repeats the 112 sentence that is already in the page footer. The stop template and the footer both carry that sentence. The screen still names the matched phrase and does not save the draft.
- The package is still called `d4_llm`. Renaming it would not change the Gemini-then-OpenRouter behavior.
- `eval/RESULTS.md` keeps one calibration row per distinct score. That table is long. It is the existing harness format.
- Term-overlap's held-out row stays in `eval/RESULTS.md` so the leakage is visible. It is not an independent catalogue, and it is not the shipped scorer.
- `FrequencyBinScorer` still accepts an optional parent map. The notebook and `d1_eval store` do not pass one. An empty map does not climb. The measured climb stays rejected.
