
from pathlib import Path

from app.rag.parsers.base import ParsedDocument
from app.rag.parsers.pdf import PDFParser
from app.rag.parsers.docx import DOCXParser
from app.rag.parsers.txt import TXTParser


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_all_parsers_return_unified_document_format():
    test_cases = [
        (PDFParser(), FIXTURES_DIR / "nsu_rag_parser_test.pdf", "pdf"),
        (DOCXParser(), FIXTURES_DIR / "nsu_rag_parser_test.docx", "docx"),
        (TXTParser(), FIXTURES_DIR / "nsu_rag_parser_test.txt", "txt"),
    ]

    for parser, file_path, expected_type in test_cases:
        document = parser.parse(file_path)

        assert isinstance(document, ParsedDocument)
        assert document.file_type == expected_type
        assert document.source_name == file_path.name
        assert isinstance(document.text, str)
        assert isinstance(document.metadata, dict)
