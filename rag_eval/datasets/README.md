# Study guide evaluation dataset

This initial dataset contains 30 Russian questions about the five chapters of
the NSU higher mathematics study guide. There are 25 answerable cases and five
out-of-scope cases. Answerable cases cover definitions, theory, paraphrases,
worked examples, and hints for exercises. The reference answers use the
provided theory and avoid requiring an unpublished worked solution.

## Evidence and scoring

Each answerable case includes a manually selected reference passage and its
half-open Unicode character offsets in the output of the project DOCX parser.
The file and the parsed text have separate SHA-256 fingerprints. All 25
reference passages fit in at least one of the 53 chunks produced by the
default chunker (1,000 characters, 150-character overlap).

Use a binary passage judgment for the initial retrieval comparison. A chunk
matches a labeled passage when its offsets fully cover the passage in the
same source document. A matching chunk counts only once per passage, including
when overlaps produce multiple copies. The labels are a set of verified
reference passages. Other passages may also be relevant, so review apparent
false negatives before using these scores for optimization.

Use answerable cases for Recall@K, MRR, and nDCG@K. Use out-of-scope cases to
check grounded abstention. Review answer correctness and whether each cited
passage supports the claim, even when application-level citation validation
passes.

## Parser limitation

Some mathematical formulas in the DOCX are missing from the parsed text.
The dataset uses questions supported by the text the pipeline can index.
Treat formula extraction as a separate coverage issue when interpreting the
benchmark.

No retrieval or generation metrics have been measured with this dataset yet.

## Run the retrieval baseline

From the repository root on an Apple Silicon Mac with the project environment
and the MLX embedding backend installed:

```sh
.venv/bin/python -m rag_eval.retrieval --source storage/eval/методичка_рец.docx --dataset rag_eval/datasets/week7_study_guide.json > storage/eval/retrieval-baseline.json
```

The runner compares dense and hybrid RRF search with in-memory Qdrant at
K=5 and 50 candidates per hybrid branch. With one labeled passage per
question, Recall@K is the fraction of questions with a matching chunk in
the first K results. MRR@K averages the reciprocal rank of the first match.
nDCG@K averages its logarithmic discount. Missing matches score zero.
The report includes each question's first relevant rank and search time.
Query embedding latency is measured separately from Qdrant search.
In-memory timings describe this benchmark environment. Dedicated sparse
search and a reranker are outside the current comparison. The benchmark
uses no LLM calls.

## Run the answer baseline

With `OPENROUTER_API_KEY` exported in the current terminal, run this from the
repository root:

```sh
.venv/bin/python -m rag_eval.answers --source storage/eval/методичка_рец.docx --dataset rag_eval/datasets/week7_study_guide.json > storage/eval/answer-baseline.jsonl
```

The runner indexes the guide locally and evaluates all 30 cases with the
standard hybrid retrieval and answer service. It sends up to 30 requests to
OpenRouter using excerpts from the guide. Each JSON line is written as soon as
the case finishes, preserving partial results if the run is interrupted.
Provider and response-validation failures appear as errors in the report.
The recorded `found` comparison measures answer availability. Manually review
correctness, evidence relevance, and whether the sources support each claim.
