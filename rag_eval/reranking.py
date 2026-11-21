
import argparse
import json
from importlib.metadata import version
from pathlib import Path
from time import perf_counter

from app.rag.chunking import DocumentChunk
from app.rag.reranking import CrossEncoderReranker, rerank_hits
from app.rag.vector_store import SearchHit
from rag_eval.retrieval import Question, relevant_rank, summarize

MODEL = CrossEncoderReranker.model_name


def rerank_report(report: dict, predict) -> dict:
    rows = []
    for record in report["modes"]["hybrid"]["questions"]:
        hits = [
            SearchHit(**{**item, "chunk": DocumentChunk(**item["chunk"])})
            for item in record["candidates"]
        ]
        question = Question(
            record["question_id"], record["question"],
            record["relevant_start"], record["relevant_end"],
        )
        # Reject cross-space candidates before passing their text to a model.
        relevant_rank(hits, question, document_id=report["source_sha256"],
                      source_name=report["source_name"])
        started = perf_counter()
        ranked = rerank_hits(question.text, hits, predict)
        rerank_ms = (perf_counter() - started) * 1000
        rows.append({
            "question_id": question.id,
            "first_relevant_rank": relevant_rank(
                ranked[:report["k"]], question,
                document_id=report["source_sha256"], source_name=report["source_name"],
            ),
            "search_ms": record["search_ms"] + rerank_ms,
            "rerank_ms": rerank_ms,
        })
    if not rows:
        raise ValueError("No hybrid candidates in report")
    return {"metrics": summarize(rows, report["k"]), "questions": rows}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--model", default=MODEL)
    args = parser.parse_args()
    model = CrossEncoderReranker(args.model)
    report = json.loads(args.input.read_text())
    report["modes"]["hybrid_reranked"] = rerank_report(
        report, model.predict,
    )
    report["reranker"] = {
        "model": args.model, "device": "cpu", "max_length": 512, "batch_size": 4,
        "sentence_transformers_version": version("sentence-transformers"),
        "timing": "Includes first-call model loading in the first question",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
