from dataclasses import asdict
from unittest.mock import Mock

import pytest
from qdrant_client import QdrantClient

from app.rag.chunking import DocumentChunk
from app.rag.integration import RAGApplication, RAGOperationError
from app.rag.llm import LLMRateLimit
from app.rag.vector_store import SearchHit, VectorStore
from rag_eval.reranking import rerank_report
from rag_eval.retrieval import SPACE_ID


@pytest.fixture
def application():
    client = QdrantClient(":memory:")
    try:
        store = VectorStore(client, dimension=2)
        store.ensure_collection()
        embedding = Mock()
        embedding.embed.side_effect = lambda texts: [[1.0, 0.0] for text in texts]
        embedding.embed_text.return_value = [1.0, 0.0]
        provider = Mock()
        yield RAGApplication(embedding, store, provider)
    finally:
        client.close()


def test_sparse_and_ingestion_isolate_spaces(application, tmp_path):
    path = tmp_path / "lecture.txt"
    path.write_text("Quantum physics exam")
    result = application.ingest_document(path, space_id="physics", document_id="exam")
    assert result.source_name == path.name
    assert len(result.point_ids) == 1
    store = application.store
    assert store.search_sparse("quantum", space_id="private") == []
    assert store.search_sparse("quantum", space_id="physics")[0].document_id == "exam"
    assert store.search_sparse("???", space_id="physics") == []
    assert not application.ask("Exam?", space_id="private").found
    application.answers.provider.complete.assert_not_called()
    path.write_text("   ")
    with pytest.raises(RAGOperationError, match="no extractable text"):
        application.ingest_document(path, space_id="physics", document_id="empty")


@pytest.mark.parametrize("space,question", [("", "Q"), ("s", " "), (None, "Q")])
def test_invalid_input_never_calls_dependencies(application, space, question):
    with pytest.raises(RAGOperationError) as error:
        application.ask(question, space_id=space)
    assert error.value.code == "invalid_input"
    application.embedding.embed_text.assert_not_called()


def test_backend_errors_hide_internal_details(application):
    application.embedding.embed_text.side_effect = RuntimeError("private key and filesystem path")
    with pytest.raises(RAGOperationError) as error:
        application.ask("Exam?", space_id="physics")
    assert error.value.code == "embedding_failed"
    assert "private" not in str(error.value)


def test_storage_failure_and_rate_limit(application, monkeypatch):
    monkeypatch.setattr(application.store, "search", Mock(side_effect=RuntimeError("secret URL")))
    with pytest.raises(RAGOperationError) as error:
        application.ask("Exam?", space_id="physics")
    assert error.value.code == "retrieval_failed"
    assert "secret" not in str(error.value)
    application.answers.ask = Mock(side_effect=LLMRateLimit("3"))
    with pytest.raises(RAGOperationError) as error:
        application.ask("Exam?", space_id="physics")
    assert error.value.code == "rate_limited"
    assert error.value.retryable


def test_reranker_changes_ranking_and_rejects_cross_space_candidates():
    def hit(index, text):
        return SearchHit(str(index), 1.0, SPACE_ID, "doc",
                         DocumentChunk(text, "guide.docx", index, start_char=index * 10,
                                       end_char=index * 10 + len(text)))

    report = {
        "k": 1, "source_sha256": "doc", "source_name": "guide.docx",
        "modes": {"hybrid": {"questions": [{
            "question_id": "q", "question": "exam?", "relevant_start": 10,
            "relevant_end": 14, "search_ms": 1,
            "candidates": [asdict(hit(0, "noise")), asdict(hit(1, "exam"))],
        }]}},
    }
    predict = Mock(return_value=[0.0, 1.0])
    result = rerank_report(report, predict)
    assert result["metrics"]["recall_at_k"] == 1
    report["modes"]["hybrid"]["questions"][0]["candidates"][0]["space_id"] = "private"
    predict.reset_mock()
    with pytest.raises(RuntimeError, match="outside"):
        rerank_report(report, predict)
    predict.assert_not_called()


def test_sparse_query_rejects_empty_scope(application):
    with pytest.raises(ValueError):
        application.store.search_sparse("query", space_id="")
    with pytest.raises(ValueError):
        application.store.search_sparse("", space_id="physics")
    with pytest.raises(ValueError):
        application.store.search_sparse("query", space_id="physics", limit=0)


def test_ingestion_retry_is_idempotent(application, tmp_path):
    path = tmp_path / "a.txt"
    path.write_text("One lecture")
    first = application.ingest_document(path, space_id="s", document_id="d")
    second = application.ingest_document(path, space_id="s", document_id="d")
    assert first == second
    assert application.store.client.count(application.store.collection).count == 1


def test_reranking_is_opt_in_and_receives_scoped_candidates(application, tmp_path):
    from app.rag.retrieval import Retriever

    path = tmp_path / "lecture.txt"
    path.write_text("Relevant theory")
    application.ingest_document(path, space_id="physics", document_id="exam")
    scorer = Mock()
    scorer.predict.return_value = [1.0]
    retriever = Retriever(application.embedding, application.store, reranker=scorer)
    assert len(retriever.retrieve("theory", space_id="physics", limit=1)) == 1
    scorer.predict.assert_called_once_with([("theory", "Relevant theory")])


@pytest.mark.parametrize("scores", [[], [float("nan")], [float("inf")]])
def test_reranking_invalid_scores_are_rejected(scores):
    from app.rag.reranking import rerank_hits

    hit = SearchHit("1", 1, SPACE_ID, "doc", DocumentChunk("text", "source", 0))
    with pytest.raises(ValueError):
        rerank_hits("question", [hit], lambda _: scores)


def test_ingestion_failure_does_not_write(application, tmp_path):
    path = tmp_path / "lecture.txt"
    path.write_text("text")
    application.embedding.embed.side_effect = RuntimeError("secret model path")
    with pytest.raises(RAGOperationError) as error:
        application.ingest_document(path, space_id="s", document_id="d")
    assert error.value.code == "embedding_failed"
    assert application.store.client.count(application.store.collection).count == 0


def test_reranker_never_sees_cross_space_hits(application, monkeypatch):
    from app.rag.retrieval import RetrievalError, Retriever

    scorer = Mock()
    private = SearchHit("1", 1, "private", "doc", DocumentChunk("secret", "source", 0))
    monkeypatch.setattr(application.store, "search", Mock(return_value=[private]))
    retriever = Retriever(application.embedding, application.store, reranker=scorer)
    with pytest.raises(RetrievalError):
        retriever.retrieve("question", space_id="physics")
    scorer.predict.assert_not_called()
