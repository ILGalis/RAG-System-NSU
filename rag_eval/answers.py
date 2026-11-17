"""Run the Week 7 answer evaluation and emit one JSON record per question."""
import argparse
import hashlib
import json
from collections.abc import Iterator
from dataclasses import asdict
from pathlib import Path

import httpx
from qdrant_client import QdrantClient

from app.rag.answers import RAGService
from app.rag.chunking import chunk_document
from app.rag.embeddings import MLXEmbeddingBackend, embed_chunks
from app.rag.llm import LLMError, OpenRouterProvider
from app.rag.parsers.docx import DOCXParser
from app.rag.retrieval import Retriever
from app.rag.vector_store import VectorStore
from rag_eval.retrieval import SPACE_ID, load_questions


def answer_rows(service: RAGService, cases: list[dict]) -> Iterator[dict]:
    for case in cases:
        row = {
            "question_id": case["id"],
            "category": case["category"],
            "question": case["question"],
            "expected_found": case["answerable"],
            "expected_answer": case["expected_answer"],
            "evidence": case["evidence"],
        }
        try:
            answer = service.ask(case["question"], space_id=SPACE_ID)
        except LLMError as error:
            row["error"] = str(error)
        else:
            row["result"] = asdict(answer)
            row["found_matches_expected"] = answer.found == case["answerable"]
        yield row


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--case", action="append", metavar="ID", help="Run only this case (repeatable)")
    args = parser.parse_args()

    dataset = json.loads(args.dataset.read_text())
    source_hash = hashlib.sha256(args.source.read_bytes()).hexdigest()
    if source_hash != dataset["source_sha256"]:
        parser.error("DOCX does not match the dataset")
    document = DOCXParser().parse(args.source)
    load_questions(dataset, document.source_name, document.text)

    cases = dataset["cases"]
    if args.case:
        requested = set(args.case)
        unknown = requested - {case["id"] for case in cases}
        if unknown:
            parser.error(f"Unknown case IDs: {', '.join(sorted(unknown))}")
        cases = [case for case in cases if case["id"] in requested]

    with httpx.Client() as http:
        provider = OpenRouterProvider(http)
        backend = MLXEmbeddingBackend()
        client = QdrantClient(":memory:")
        try:
            store = VectorStore(client, dimension=backend.config.dimension)
            store.ensure_collection()
            store.upsert(
                embed_chunks(chunk_document(document), backend),
                space_id=SPACE_ID,
                document_id=source_hash,
            )
            service = RAGService(Retriever(backend, store), provider)
            for row in answer_rows(service, cases):
                print(json.dumps(row, ensure_ascii=False), flush=True)
        finally:
            client.close()


if __name__ == "__main__":
    main()
