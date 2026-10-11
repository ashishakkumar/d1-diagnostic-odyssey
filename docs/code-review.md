# Code review of the finished notebook

For research use only. Not for use in diagnostic procedures.

This review reads the branch `cursor/finish-odyssey-demo-79af` against `cursor/integrate-safe-core-e84c`. It does not replace [review.md](review.md), which is the critique of `PLAN.md`. Thresholds were not refit. Term-overlap-loo was not shipped.

## What holds

- Demo loads still call `app.apply_decision`. The API role does not write observations on its own.
- The five synthetic cases, the stop screen, the India footer, and the opt-in allele prior are covered by `tests/web/test_demo.py` and by Playwright in `apps/web/e2e/demo.spec.ts`. The prior fixture does not change the catalogue report.
- `contracts/openapi.json` and `contracts/ts/src/api.ts` are checked against the app by `tests/test_openapi.py`.
- `complete()` calls the Gemini primary first. A stubbed 429 / `RESOURCE_EXHAUSTED` is the only path to OpenRouter, and that call must use an id ending in `:free`. The returned `Completion.provider` is `gemini`, `openrouter`, or `gazetteer`. A prompt without `SYNTHETIC-ONLY` raises `SyntheticRejected` before either provider is called. No fallback key degrades through `complete_or_degrade` to pinned wording. The notebook routes do not import the client.
- Frequency-bin exact rows are what `d1_eval store` and the notebook score. The ancestor climb lowered full-set top-1 from 1292/4815 to 841/4815 on store 0.1.27, so it is not passed in. Held-out top-1 for the shipped scorer is 1046/3890 train and 246/925 test. Those rows were not used to choose a threshold.
- `PLAN.md` is unchanged by this finish.

## Fixed from this review

- The warning-sign button left the page blank when `fetch` threw. The click is `void save(...)`, so the rejection was unhandled. The page now says the notebook cannot reach the API. A 409 body that is not JSON still shows "Stop. The words were not saved."
- A set `OPENROUTER_API_KEY` with no `:free` id list did not call OpenRouter, and the README read as if the key alone were enough. The client still refuses to invent a model id. The README and finish report say to set `OPENROUTER_FREE_MODELS`. A test locks that an unset list does not call OpenRouter and that the provider recorded is `gazetteer`.
- Playwright resolved `cd ../..` from `apps/web`, which leaves the repo. The web server command is `.venv/bin/python scripts/demo.py` with `cwd: ".."`, so a cold start runs from the repo root.
- `d1_eval store` printed the term-overlap-loo top-1 as an unlabeled `top1=`. The command summary now leads with `frequency-bin` totals and labels the stand-in line `term-overlap-loo`. `eval/RESULTS.md` was not rewritten.
- An abstained comparison still showed `Margin 1.000` when ten diseases tied. The panel hides that number when `abstained` is true. The API still returns margin 1 for the tie.
- `complete_with_gemini` reads `GEMINI_API_KEY` or `GOOGLE_API_KEY`, follows `nextPageToken`, chooses the id, calls Gemini first, and stores that id on `Completion`. OpenRouter stays behind a 429 or `RESOURCE_EXHAUSTED`, and only for an id ending in `:free`. No key returns the pinned gazetteer sentence, does not call HTTP, and does not write the replay cache.
- `is_rate_limited` matches `429` and `RESOURCE_EXHAUSTED` only. The word "quota" on its own does not fall back.
- A lone OpenAPI `const` was rendered as `string`. `margin_reason` in `contracts/ts/src/api.ts` is now `"runner_up_ratio_is_zero" | null`.
- A gazetteer degrade is appended to the jsonl log and is not stored in the replay cache. A pinned sentence must not hide a key that appears later.
- `create_app` is imported at the top of `export_openapi.py`. The API package does not import that module.

## Left as they are

- The stop paragraph repeats the 112 sentence already in the page footer. The stop template and the footer both carry that sentence. The screen still names the matched phrase and does not save the draft.
- The package is still named `d4_llm`. Renaming it does not change Gemini-then-OpenRouter.
- `eval/RESULTS.md` has one calibration row per distinct score. That is the existing harness format.
- Term-overlap's held-out row stays in `eval/RESULTS.md` so the leakage is visible. It is not an independent catalogue, and it is not the shipped scorer.
- `FrequencyBinScorer` still accepts an optional parent map. The notebook and `d1_eval store` do not pass one. An empty map does not climb. The measured climb stays rejected.
