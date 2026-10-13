
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


from docx import Document


def test_corrupted_docx_raises_value_error(tmp_path):
    """A corrupted DOCX file should raise a clear ValueError."""
    file_path = tmp_path / "corrupted.docx"
    file_path.write_text("This is not a valid DOCX file", encoding="utf-8")

    parser = DOCXParser()

    with pytest.raises(ValueError, match="Could not read DOCX file"):
        parser.parse(file_path)


def test_empty_docx_returns_empty_text(tmp_path):
    """An empty DOCX should be parsed without errors."""
    file_path = tmp_path / "empty.docx"
    Document().save(file_path)

    parser = DOCXParser()
    result = parser.parse(file_path)

    assert result.text == ""
    assert result.source_name == "empty.docx"
    assert result.file_type == "docx"
    assert result.metadata["paragraph_count"] == "0"
    assert result.metadata["table_count"] == "0"
