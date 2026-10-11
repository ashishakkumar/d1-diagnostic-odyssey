# Finish report

For research use only. Not for use in diagnostic procedures.

This notebook is a synthetic case file. It does not diagnose. `make demo` resets the local database and opens the five cases at <http://127.0.0.1:3000>.

## What a person can run

Sign in with any name, then load one of the five synthetic cases. Each load still goes through `app.apply_decision`. The summary shows a cited catalogue comparison, plain-language wording for the terms, and the India footer (emergency number 112, from `templates/red_flags/default.txt`). One case abstains. The lab-variant page has a warning-sign button. That button posts "Unconsciousness." and the API returns 409 with the stop screen. The draft is not saved. A checkbox on the summary turns on an experimental population-frequency prior from `services/api/app/data/allele_frequencies.json` (`NM_000138.5:c.1A>G`, allele frequency 0.00012). The prior does not change the catalogue comparison, and the limits text says this build did not call gnomAD or ClinVar.

`make e2e` runs that path in Chromium and writes `docs/demo-screenshots/01-cases.png` through `07-stop.png`.

| Case | What the page shows |
| --- | --- |
| Separated rows | ORPHA:9000001 ahead. The next row has a ratio of zero, so the margin is empty, `margin_reason` is `runner_up_ratio_is_zero`, and `margin_fact` names HP:0000272. |
| No separated row | The page abstains (`many_within_factor`). Abstaining does not mean the person is well. |
| Stable at both ends | ORPHA:9000011 stays first. The margin is a finite number. |
| Variant does not move the comparison | Same catalogue rows as Separated rows, plus a typed FBN1 variant. Opting into the prior shows 0.00012 and does not move the comparison. |
| No dose on this page | The page says it does not choose a dose. The warning-sign button on the lab-variant page shows the stop screen. |

## Scorer

The notebook ships frequency-bin 0.0.2. The measurement is [scorer-0.0.2.md](scorer-0.0.2.md). Pull request #8 recorded the same full-set rows; this branch re-ran `d1_eval store` after wiring that background into the scorer the notebook calls. Phenopacket Store 0.1.27 (sha256 `d0c70005bb09b87035087516252b6b539fbc0415be7c664b73c9cde7eedf205a`). 531 diseases are excluded because they are not a unique Orphanet id. `packets_skipped` is 0. 4,815 packets are scored. Abstentions count as misses. `CLOSE_DISEASE_COUNT` stays 10 and `CLOSE_FACTOR` stays 2.0. They were not refit.

`P(feature | not this disease) = (k + 1) / (n + 2)` on every disorder in Orphadata Science `en_product4`, including disorders that are not ranked. A missing row contributes a ratio of 1. Full-set top-1 is 1395/4815 (top-3 1732/4815, top-10 2026/4815, no-confident 1645/4815). The held-out split is SHA-256 of the packet id, modulo 5, remainder 0 is test. It was not used to choose a threshold, a background, or a bin edge. Full top-1 is 1129/3890 on train and 266/925 on test. 1129 + 266 = 1395. The other degradations are in `eval/RESULTS.md`. `d1_eval store` prints those frequency-bin totals and a separate line labeled `term-overlap-loo`.

Frequency-bin 0.0.1, the flat background 0.05, had full-set top-1 1292/4815 and held-out test top-1 246/925. Those rows stay in `eval/RESULTS.md` under the heading Archived frequency-bin 0.0.1. They are not the shipped scorer.

Term-overlap-loo full-set top-1 is 3806/4815, with 104/4815 abstentions, and held-out test top-1 731/925. It reads HPO labels from other packets in the same release. That is label leakage, not an external catalogue. The test catalogue still includes train packets. It is not shipped.

An ancestor climb was measured only on the 0.0.1 flat background. Full-set top-1 fell from 1292/4815 to 841/4815. That climb was not rerun on 0.0.2, so 841/4815 is not a 0.0.2 result. The notebook and `d1_eval store` do not pass a parent map. The function remains for a caller that passes parents.

Not run, so not a pass: the degree baseline, and precision@k at k = 1 and k = 5. `PLAN.md` asks the catalogue to beat that baseline on both percentage@k and precision@k over the 249 unique-map diseases. A unit test checks that one decoy gene does not change a disease rank. A store-scale decoy-gene evaluation was not run.

## Contract, prior, and model client

`contracts/openapi.json` is generated from the FastAPI app. `contracts/ts/src/api.ts` is generated from that document. `tests/test_openapi.py` fails if either file drifts. The report response leaves unset fields out, so a catalogue comparison does not carry a `probability` without a reliability curve. `margin` is still present when it is null, and `margin_reason` says `runner_up_ratio_is_zero` when the runner-up lower ratio is 0.

`services/llm` calls Gemini first through `complete_with_gemini`. That function reads `GEMINI_API_KEY` or `GOOGLE_API_KEY`, follows every `nextPageToken` on `GET https://generativelanguage.googleapis.com/v1beta/models`, and chooses the newest flash-lite id from that list. The chosen id is stored on the completion. OpenRouter is used only after a Gemini 429 or `RESOURCE_EXHAUSTED`, and only for model ids that end in `:free`, with backoff and a SHA-256 replay cache. Text must contain `SYNTHETIC-ONLY` or the client refuses it before any HTTP call. With no Gemini key, no fallback key, or no `OPENROUTER_FREE_MODELS` list of `:free` ids, the client returns pinned wording, records provider `gazetteer`, and does not call OpenRouter. A gazetteer sentence is logged and is not written into the replay cache, so a key added later is not hidden. Keys stay in gitignored `uploads/` and `.env` files. One opt-in smoke (`D4_LLM_LIVE=1`) completed a single `:free` fallback call. The other LLM tests use stubs.

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
