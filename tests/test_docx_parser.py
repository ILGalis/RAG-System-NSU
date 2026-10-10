
from pathlib import Path

import pytest

from app.rag.parsers.base import ParsedDocument
from app.rag.parsers.docx import DOCXParser


FIXTURES_DIR = Path(__file__).parent / "fixtures"
TEST_DOCX = FIXTURES_DIR / "nsu_rag_parser_test.docx"


def test_docx_parser_extracts_paragraphs_and_tables():
    document = DOCXParser().parse(TEST_DOCX)

    assert isinstance(document, ParsedDocument)
    assert document.source_name == "nsu_rag_parser_test.docx"
    assert document.file_type == "docx"

    assert "NSU RAG DOCX Test" in document.text
    assert "This is a test paragraph." in document.text
    assert "Term | Definition" in document.text
    assert "RAG | Retrieval-Augmented Generation" in document.text

    assert document.metadata["table_count"] == "1"


def test_docx_parser_rejects_missing_file():
    with pytest.raises(FileNotFoundError):
        DOCXParser().parse(FIXTURES_DIR / "missing.docx")


def test_docx_parser_rejects_non_docx_file(tmp_path):
    txt_file = tmp_path / "document.txt"
    txt_file.write_text("Some text", encoding="utf-8")

    with pytest.raises(ValueError, match="Expected a DOCX file"):
        DOCXParser().parse(txt_file)
