import hashlib

import pytest

from rag_eval.retrieval import Question, load_questions, summarize


def test_metrics_with_one_labeled_passage():
    rows = [
        {"first_relevant_rank": 2, "search_ms": 3},
        {"first_relevant_rank": None, "search_ms": 1},
    ]
    assert summarize(rows, 2) == pytest.approx({
        "recall_at_k": 0.5, "mrr_at_k": 0.25, "ndcg_at_k": 0.3154648768,
        "median_search_ms": 2,
    })
    assert summarize(rows, 1)["recall_at_k"] == 0


def test_dataset_preserves_evidence_and_excludes_unanswerable_questions():
    dataset = {
        "schema_version": 1,
        "source_name": "guide.docx",
        "parsed_text_sha256": hashlib.sha256(b"abc").hexdigest(),
        "cases": [
            {"id": "first", "question": "First?", "answerable": True,
             "evidence": [{"start_char": 1, "end_char": 3, "text": "bc"}]},
            {"id": "second", "question": "Second?", "answerable": False, "evidence": []},
        ],
    }
    assert load_questions(dataset, "guide.docx", "abc") == [Question("first", "First?", 1, 3)]
    dataset["cases"].pop(0)
    with pytest.raises(ValueError, match="no answerable questions"):
        load_questions(dataset, "guide.docx", "abc")


def test_evaluation_with_fake_embeddings(tmp_path):
    from docx import Document

    from rag_eval.retrieval import evaluate

    class FakeEmbedding:
        def embed(self, texts):
            return [[1.0, 0.0] for _ in texts]

        def embed_text(self, text):
            return self.embed([text])[0]

    path = tmp_path / "guide.docx"
    document = Document()
    document.add_paragraph("The exam is on Tuesday.")
    document.save(path)
    text = "The exam is on Tuesday."
    dataset = {
        "schema_version": 1,
        "source_name": path.name,
        "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "parsed_text_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "cases": [{
            "id": "exam", "question": "When is the exam?", "answerable": True,
            "evidence": [{"start_char": 0, "end_char": len(text), "text": text}],
        }],
    }
    result = evaluate(dataset, path, FakeEmbedding(), dimension=2, k=5, candidate_limit=50)
    assert result["question_count"] == 1
    for mode in ("dense", "hybrid"):
        assert result["modes"][mode]["metrics"]["recall_at_k"] == 1
        row, = result["modes"][mode]["questions"]
        assert row["question_id"] == "exam"
        assert row["first_relevant_rank"] == 1
