
from pathlib import Path

import pytest

from app.rag.parsers.base import ParsedDocument
from app.rag.parsers.pdf import PDFParser


FIXTURES_DIR = Path(__file__).parent / "fixtures"
TEST_PDF = FIXTURES_DIR / "nsu_rag_parser_test.pdf"


def test_pdf_parser_extracts_text_and_page_numbers():
    document = PDFParser().parse(TEST_PDF)

    assert isinstance(document, ParsedDocument)
    assert document.source_name == "nsu_rag_parser_test.pdf"
    assert document.file_type == "pdf"
    assert len(document.pages) == 2

    assert document.pages[0].page_number == 1
    assert "This is page one." in document.pages[0].text

    assert document.pages[1].page_number == 2
    assert "This is page two." in document.pages[1].text

    assert "This is page one." in document.text
    assert "This is page two." in document.text


def test_pdf_parser_rejects_missing_file():
    missing_file = FIXTURES_DIR / "missing.pdf"

    with pytest.raises(FileNotFoundError):
        PDFParser().parse(missing_file)


def test_pdf_parser_rejects_non_pdf_file(tmp_path):
    txt_file = tmp_path / "document.txt"
    txt_file.write_text("Some text", encoding="utf-8")

    with pytest.raises(ValueError, match="Expected a PDF file"):
        PDFParser().parse(txt_file)
