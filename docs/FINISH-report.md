# Finish report

For research use only. Not for use in diagnostic procedures.

This notebook is a synthetic case file. It does not diagnose. `make demo` resets the local database and opens the five cases at <http://127.0.0.1:3000>.

## What a person can run

Sign in with any name, then load one of the five synthetic cases. Each load still goes through `app.apply_decision`. The summary shows a cited catalogue comparison, plain-language wording for the terms, and the India footer (emergency number 112, from `templates/red_flags/default.txt`). One case abstains. The lab-variant page has a warning-sign button. That button posts "Unconsciousness." and the API returns 409 with the stop screen. The draft is not saved. A checkbox on the summary turns on an experimental population-frequency prior from `services/api/app/data/allele_frequencies.json` (`NM_000138.5:c.1A>G`, allele frequency 0.00012). The prior does not change the catalogue comparison, and the limits text says this build did not call gnomAD or ClinVar.

`make e2e` runs that path in Chromium and writes `docs/demo-screenshots/01-cases.png` through `07-stop.png`.

| Case | What the page shows |
| --- | --- |
| Separated rows | ORPHA:9000001 ahead. The next row has a ratio of zero, so the margin is empty and `margin_reason` is `runner_up_ratio_is_zero`. |
| No separated row | The page abstains (`many_within_factor`). Abstaining does not mean the person is well. |
| Stable at both ends | ORPHA:9000011 stays first. The margin is a finite number. |
| Variant does not move the comparison | Same catalogue rows as Separated rows, plus a typed FBN1 variant. Opting into the prior shows 0.00012 and does not move the comparison. |
| No dose on this page | The page says it does not choose a dose. The warning-sign button on the lab-variant page shows the stop screen. |

## Scorer

Two scores were compared on Phenopacket Store 0.1.27 (sha256 `d0c70005bb09b87035087516252b6b539fbc0415be7c664b73c9cde7eedf205a`). 531 diseases are excluded because they are not a unique Orphanet id. `packets_skipped` is 0. 4,815 packets are scored. Abstentions count as misses. Thresholds stayed frozen (`CLOSE_DISEASE_COUNT` 10, `CLOSE_FACTOR` 2.0, background 0.05).

Term-overlap-loo is high because it reads HPO labels from other packets in the same release and leaves out only the packet being scored. That is label leakage, not an external catalogue. Its held-out row is still not independent: the catalogue for a test packet includes train packets. It is not shipped.

Frequency-bin is the Orphanet phenotype-frequency catalogue. A missing row uses the flat unannotated ratio 0.01 / 0.05. This is the scorer the notebook ships. Exact-match full-set top-1 is 1292/4815 (top-3 1589/4815, top-10 1953/4815, no-confident 1653/4815). The held-out split is SHA-256 of the packet id, modulo 5, remainder 0 is test. It was not used to choose a threshold, a background, or a bin edge. Full top-1 is 1046/3890 on train and 246/925 on test, so the two cohorts agree. The other degradations are in `eval/RESULTS.md`.

An ancestor climb (depth 8, stop at HP:0000001 and HP:0000118) was measured on the same pin. Full-set top-1 fell from 1292/4815 to 841/4815 (top-3 1082/4815, top-10 1619/4815, no-confident 1634/4815). Held-out test top-1 under the climb was 178/925, below the exact-match test row of 246/925. Climbing replaces a missing specific row with a parent bin, which boosts diseases that annotate a broad parent. That hurt retrieval, so the notebook and `d1_eval store` do not pass a parent map into the scorer. The climb function remains for a caller that passes parents, and a unit test covers that path. Thresholds were not refit on either run.

Term-overlap-loo on the same pin, for comparison only: full-set top-1 3806/4815, held-out test top-1 731/925. The gap is the leaked labels, not a bug in the frequency bins.

## Contract, prior, and model client

`contracts/openapi.json` is generated from the FastAPI app. `contracts/ts/src/api.ts` is generated from that document. `tests/test_openapi.py` fails if either file drifts. The report response leaves unset fields out, so a catalogue comparison does not carry a `probability` without a reliability curve. `margin` is still present when it is null, and `margin_reason` says `runner_up_ratio_is_zero` when the runner-up lower ratio is 0.

`services/llm` calls Gemini first. The model id is the newest flash-lite id returned by `GET https://generativelanguage.googleapis.com/v1beta/models`, not a constant in the client. OpenRouter is used only after a Gemini rate limit, and only for model ids that end in `:free`, with backoff and a SHA-256 replay cache. Text must contain `SYNTHETIC-ONLY` or the client refuses it before any HTTP call. With no fallback key, or no `OPENROUTER_FREE_MODELS` list of `:free` ids, a rate limit degrades to pinned wording and does not call OpenRouter. Keys stay in gitignored `uploads/` and `.env` files. One opt-in smoke (`D4_LLM_LIVE=1`) completed a single `:free` fallback call. The other LLM tests use stubs.

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

Left as they are:

- The stop paragraph repeats the 112 sentence that is already in the page footer. The stop template and the footer both carry that sentence. The screen still names the matched phrase and does not save the draft.
- The package is still called `d4_llm`. Renaming it would not change the Gemini-then-OpenRouter behavior.
- `eval/RESULTS.md` keeps one calibration row per distinct score. That table is long. It is the existing harness format.
- Term-overlap's test cohort is reported so the leakage is visible. It is not an independent catalogue, and it is not the shipped scorer.
