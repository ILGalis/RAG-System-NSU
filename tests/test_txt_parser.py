
from pathlib import Path

import pytest

from app.rag.parsers.base import ParsedDocument
from app.rag.parsers.txt import TXTParser


FIXTURES_DIR = Path(__file__).parent / "fixtures"
TEST_TXT = FIXTURES_DIR / "nsu_rag_parser_test.txt"


def test_txt_parser_extracts_utf8_text():
    document = TXTParser().parse(TEST_TXT)

    assert isinstance(document, ParsedDocument)
    assert document.source_name == "nsu_rag_parser_test.txt"
    assert document.file_type == "txt"
    assert "NSU RAG TXT parser test." in document.text
    assert "Привет, мир" in document.text
    assert document.metadata["encoding"] == "utf-8-sig"


def test_txt_parser_supports_cp1251(tmp_path):
    txt_file = tmp_path / "russian.txt"
    txt_file.write_bytes("Привет, мир!".encode("cp1251"))

    document = TXTParser().parse(txt_file)

    assert "Привет, мир!" in document.text
    assert document.metadata["encoding"] == "cp1251"


def test_txt_parser_rejects_missing_file():
    with pytest.raises(FileNotFoundError):
        TXTParser().parse(FIXTURES_DIR / "missing.txt")


def test_txt_parser_rejects_non_txt_file(tmp_path):
    pdf_file = tmp_path / "document.pdf"
    pdf_file.write_text("Not a real PDF", encoding="utf-8")

    with pytest.raises(ValueError, match="Expected a TXT file"):
        TXTParser().parse(pdf_file)
