# Text-to-HPO extraction results

For research use only. Not for use in diagnostic procedures. Run 2026-10-13 on HPO v2026-09-01.

Corpora: GSC+ test split (206 abstracts, `PhenoTagger/data/corpus/GSC/GSCplus_test_gold.tsv`) and
ID-68 (68 clinical notes, `PhenoBERT/phenobert/data/ID-68`). Script: `eval/extraction/run.py`.
Metric: document-level HPO-id sets, micro-averaged. "Relaxed" also credits an id that is an ancestor
or descendant of a gold id in the same document. Negated mentions are kept as predictions,
because the gold sets annotate mentions regardless of negation.

| corpus | path | docs | exact P | exact R | exact F1 | relaxed F1 | invalid ids | gold top-1 = extracted top-1 | gold top-1 in extracted top-5 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GSC+ | rules | 206/206 | 0.891 | 0.512 | 0.650 | 0.832 | 0 | 0.523 | 0.673 |
| GSC+ | LLM + grounding | 206/206 | 0.801 | 0.397 | 0.531 | 0.744 | 0 | 0.342 | 0.457 |
| GSC+ | hybrid (shipped) | 206/206 | 0.818 | 0.609 | **0.698** | **0.879** | 0 | **0.598** | **0.759** |
| ID-68 | rules | 68/68 | 0.894 | 0.641 | 0.747 | 0.829 | 0 | 0.515 | 0.559 |
| ID-68 | rules, same 43 docs | 43/68 | 0.908 | 0.649 | **0.757** | 0.828 | 0 | 0.512 | 0.581 |
| ID-68 | LLM + grounding | 43/68 | 0.694 | 0.603 | 0.645 | 0.771 | 0 | 0.372 | 0.535 |
| ID-68 | hybrid (shipped) | 43/68 | 0.714 | 0.723 | 0.718 | 0.829 | 0 | **0.581** | **0.721** |

LLM: gemini-3.5-flash-lite (Gemini free tier). gemini-2.5-flash returned 429 for the whole run.
Grounding: exact HPO labels and synonyms, fuzzy match, potion-base-8M embeddings; a term is used
only at score >= 0.8. The model never supplies ids, so invalid predicted ids are 0 by construction.
Gold ids absent from this HPO release (obsolete or alternate ids): GSC+ 2, ID-68 14 (8 in the 43-doc subset).

## Published comparison (from the papers, not re-run here)

| method | GSC+ doc-level F1 | ID-68 F1 |
| --- | --- | --- |
| PhenoTagger (Luo et al. 2021, 206-doc test split) | 0.757 | 0.826 (as reported by PhenoBERT, macro) |
| PhenoBERT (Feng et al. 2022; GSC+ on all 228 docs) | 0.747 (macro) | 0.854 (micro) / 0.854 (macro) |

RAG-HPO (github.com/PoseyPod/RAG-HPO) was not run: it needs its own LLM and vector store setup
and the free Gemini quota was already the bottleneck here.

## Honest reading

- Shipped hybrid is below PhenoTagger and PhenoBERT on exact F1 (0.698 vs 0.757 on GSC+).
- The LLM alone did worse than the dictionary matcher: it merges or paraphrases findings and the
  0.8 grounding threshold drops unsure ones (those go to the user to confirm in the app).
- Adding the dictionary hits the model missed is what lifted recall; on ID-68 it cost precision,
  so exact F1 there is lower than rules alone, while downstream agreement rose.
- Quota limited the run: 25 of 68 ID-68 notes were not processed (Gemini 429/503 and slow responses).
  Rows marked 43/68 are that subset; compare them only with each other.
- Downstream columns are agreement with ranking on the gold codes, not diagnostic accuracy:
  these corpora have no diagnosis labels.
