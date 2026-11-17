from unittest.mock import create_autospec

from app.rag.answers import INSUFFICIENT_CONTEXT, RAGAnswer, RAGService
from app.rag.llm import LLMError
from rag_eval.answers import answer_rows
from rag_eval.retrieval import SPACE_ID


def test_answer_report_distinguishes_abstention_from_provider_failure():
    service = create_autospec(RAGService, instance=True)
    service.ask.side_effect = [RAGAnswer(INSUFFICIENT_CONTEXT, False), LLMError("HTTP 429")]
    cases = [
        {"id": case_id, "category": "out_of_scope", "question": question,
         "answerable": False, "expected_answer": None, "evidence": []}
        for case_id, question in (("first", "First?"), ("second", "Second?"))
    ]

    first, second = answer_rows(service, cases)

    assert first["question_id"] == "first"
    assert first["found_matches_expected"] is True
    assert first["result"]["found"] is False
    assert second["question_id"] == "second"
    assert second["error"] == "HTTP 429"
    assert "found_matches_expected" not in second
    service.ask.assert_called_with("Second?", space_id=SPACE_ID)
