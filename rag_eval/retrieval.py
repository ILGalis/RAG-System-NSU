
import argparse
import hashlib
import json
import statistics
from dataclasses import asdict, dataclass
from math import log2
from pathlib import Path
from time import perf_counter

from qdrant_client import QdrantClient

from app.rag.chunking import chunk_document
from app.rag.embeddings import EmbeddingBackend, MLXEmbeddingBackend, embed_chunks
from app.rag.parsers.docx import DOCXParser
from app.rag.vector_store import SearchHit, VectorStore

SPACE_ID = "week7-evaluation"


@dataclass(frozen=True)
class Question:
    id: str
    text: str
    start: int
    end: int


def load_questions(dataset: dict, source_name: str, text: str) -> list[Question]:
    if dataset["schema_version"] != 1 or dataset["source_name"] != source_name:
        raise ValueError("Unexpected dataset schema or source name")
    if hashlib.sha256(text.encode()).hexdigest() != dataset["parsed_text_sha256"]:
        raise ValueError("Parsed text does not match the dataset")
    questions = []
    seen = set()
    for case in dataset["cases"]:
        case_id, question, evidence = case["id"], case["question"], case["evidence"]
        if (not isinstance(case_id, str) or not case_id.strip() or case_id in seen
                or not isinstance(question, str) or not question.strip()
                or type(case["answerable"]) is not bool):
            raise ValueError("Invalid or duplicate question")
        seen.add(case_id)
        if not case["answerable"]:
            if evidence:
                raise ValueError(f"Unexpected evidence for {case_id}")
            continue
        if len(evidence) != 1:
            raise ValueError(f"Expected one labeled passage for {case_id}")
        span = evidence[0]
        start, end = span["start_char"], span["end_char"]
        if (type(start) is not int or type(end) is not int
                or not 0 <= start < end <= len(text) or text[start:end] != span["text"]):
            raise ValueError(f"Invalid evidence for {case_id}")
        questions.append(Question(case_id, question, start, end))
    if not questions:
        raise ValueError("The dataset has no answerable questions")
    return questions


def relevant_rank(
    hits: list[SearchHit], question: Question, *, document_id: str, source_name: str,
) -> int | None:
    if any(hit.space_id != SPACE_ID for hit in hits):
        raise RuntimeError("Evaluation received a hit outside its space")
    return next((
        rank for rank, hit in enumerate(hits, start=1)
        if hit.document_id == document_id and hit.chunk.source_name == source_name
        and hit.chunk.start_char <= question.start and hit.chunk.end_char >= question.end
    ), None)


def summarize(rows: list[dict], k: int) -> dict:
    ranks = [row["first_relevant_rank"] for row in rows]
    return {
        "recall_at_k": statistics.mean(rank is not None and rank <= k for rank in ranks),
        "mrr_at_k": statistics.mean(1 / rank if rank is not None and rank <= k else 0
                                    for rank in ranks),
        "ndcg_at_k": statistics.mean(1 / log2(rank + 1) if rank is not None and rank <= k
                                     else 0 for rank in ranks),
        "median_search_ms": statistics.median(row["search_ms"] for row in rows),
    }


def evaluate(
    dataset: dict, source: Path, backend: EmbeddingBackend, *,
    dimension: int, k: int, candidate_limit: int,
) -> dict:
    if not 1 <= k <= candidate_limit:
        raise ValueError("Require 1 <= k <= candidate_limit")
    document_id = hashlib.sha256(source.read_bytes()).hexdigest()
    if document_id != dataset["source_sha256"]:
        raise ValueError("DOCX does not match the dataset")
    document = DOCXParser().parse(source)
    questions = load_questions(dataset, document.source_name, document.text)
    chunks = chunk_document(document)
    rows = {"dense": [], "sparse": [], "hybrid": []}
    client = QdrantClient(":memory:")
    try:
        store = VectorStore(client, dimension=dimension)
        store.ensure_collection()
        store.upsert(embed_chunks(chunks, backend), space_id=SPACE_ID, document_id=document_id)
        for question in questions:
            started = perf_counter()
            vector = backend.embed_text(question.text)
            embedding_ms = (perf_counter() - started) * 1000
            for mode, results in rows.items():
                started = perf_counter()
                if mode == "sparse":
                    hits = store.search_sparse(question.text, space_id=SPACE_ID, limit=k)
                else:
                    hits = store.search(
                        vector, space_id=SPACE_ID,
                        limit=candidate_limit if mode == "hybrid" else k,
                        candidate_limit=candidate_limit,
                        query_text=question.text if mode == "hybrid" else None,
                    )
                search_ms = (perf_counter() - started) * 1000
                results.append({
                    "question_id": question.id,
                    "first_relevant_rank": relevant_rank(
                        hits[:k], question, document_id=document_id, source_name=document.source_name,
                    ),
                    "search_ms": search_ms,
                    "embedding_ms": 0 if mode == "sparse" else embedding_ms,
                    "question": question.text,
                    "relevant_start": question.start,
                    "relevant_end": question.end,
                    "candidates": [asdict(hit) for hit in hits] if mode == "hybrid" else [],
                })
    finally:
        client.close()
    return {
        "source_sha256": document_id,
        "source_name": document.source_name,
        "question_count": len(questions),
        "excluded_unanswerable_count": len(dataset["cases"]) - len(questions),
        "chunk_count": len(chunks),
        "k": k,
        "candidate_limit": candidate_limit,
        "median_query_embedding_ms": statistics.median(row["embedding_ms"] for row in rows["dense"]),
        "modes": {
            mode: {"metrics": summarize(results, k), "questions": results}
            for mode, results in rows.items()
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--candidate-limit", type=int, default=50)
    args = parser.parse_args()
    backend = MLXEmbeddingBackend()
    result = evaluate(
        json.loads(args.dataset.read_text()), args.source, backend,
        dimension=backend.config.dimension, k=args.k, candidate_limit=args.candidate_limit,
    )
    result["embedding_model"] = backend.config.model_name
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
