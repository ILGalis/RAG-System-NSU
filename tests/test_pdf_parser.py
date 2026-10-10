
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


import pymupdf



def test_pdf_preserves_russian_text_and_page_structure(tmp_path):
    """Russian text and page boundaries should be preserved."""
    file_path = tmp_path / "russian.pdf"
    font_path = "/System/Library/Fonts/Supplemental/Arial.ttf"

    with pymupdf.open() as pdf:
        first_page = pdf.new_page()
        first_page.insert_font(fontname="Arial", fontfile=font_path)
        first_page.insert_text(
            (72, 72),
            "Привет, студент!",
            fontname="Arial",
        )

        second_page = pdf.new_page()
        second_page.insert_font(fontname="Arial", fontfile=font_path)
        second_page.insert_text(
            (72, 72),
            "Вторая страница",
            fontname="Arial",
        )

        pdf.save(file_path)

    parser = PDFParser()
    result = parser.parse(file_path)

    assert len(result.pages) == 2
    assert [page.page_number for page in result.pages] == [1, 2]
    assert " ".join(result.pages[0].text.split()) == "Привет, студент!"
    assert " ".join(result.pages[1].text.split()) == "Вторая страница"
    assert result.metadata["page_count"] == "2"
    assert result.text == "\n\n".join(
        page.text for page in result.pages if page.text
    )
