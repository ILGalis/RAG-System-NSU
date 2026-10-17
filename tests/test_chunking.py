
import pytest

from app.rag.chunking import chunk_document
from app.rag.parsers.base import ParsedDocument, ParsedPage


def make_document(
    text: str,
    pages: list[ParsedPage] | None = None,
) -> ParsedDocument:
    return ParsedDocument(
        text=text,
        source_name="test.txt",
        file_type="txt",
        pages=pages or [],
    )


def test_empty_document_returns_no_chunks() -> None:
    document = make_document("   ")

    assert chunk_document(document) == []


def test_short_document_returns_one_chunk() -> None:
    document = make_document("Short document.")

    chunks = chunk_document(document)

    assert len(chunks) == 1
    assert chunks[0].text == "Short document."
    assert chunks[0].chunk_index == 0


def test_long_document_is_split_into_chunks() -> None:
    document = make_document("a" * 2500)

    chunks = chunk_document(
        document,
        chunk_size=1000,
        overlap=150,
    )

    assert len(chunks) > 1
    assert all(len(chunk.text) <= 1000 for chunk in chunks)


def test_invalid_chunk_size_raises_error() -> None:
    document = make_document("Some text.")

    with pytest.raises(ValueError):
        chunk_document(document, chunk_size=0)


def test_invalid_overlap_raises_error() -> None:
    document = make_document("Some text.")

    with pytest.raises(ValueError):
        chunk_document(document, chunk_size=100, overlap=100)


def test_pdf_page_numbers_are_preserved() -> None:
    pages = [
        ParsedPage(page_number=1, text="First page text."),
        ParsedPage(page_number=2, text="Second page text."),
    ]
    document = make_document(
        "First page text.\n\nSecond page text.",
        pages=pages,
    )

    chunks = chunk_document(document)

    assert len(chunks) == 1
    assert chunks[0].page_numbers == [1, 2]

def test_chunk_offsets_match_original_text() -> None:
    text = "First paragraph.\n\nSecond paragraph."
    document = make_document(text)

    chunks = chunk_document(document, chunk_size=20, overlap=5)

    for chunk in chunks:
        assert text[chunk.start_char:chunk.end_char].strip() == chunk.text


def test_chunk_indices_are_sequential() -> None:
    document = make_document("word " * 500)

    chunks = chunk_document(document, chunk_size=100, overlap=20)

    assert [chunk.chunk_index for chunk in chunks] == list(range(len(chunks)))

def test_chunking_does_not_skip_non_whitespace_characters() -> None:
    text = ("alpha beta gamma delta " * 30).strip()
    document = make_document(text)

    chunks = chunk_document(
        document,
        chunk_size=40,
        overlap=10,
    )

    covered_positions = {
        position
        for chunk in chunks
        for position in range(chunk.start_char, chunk.end_char)
    }

    for position, character in enumerate(text):
        if not character.isspace():
            assert position in covered_positions, (
                f"Character at position {position} was skipped: "
                f"{character!r}"
            )

def test_empty_first_pdf_page_does_not_shift_page_numbers() -> None:
    pages = [
        ParsedPage(page_number=1, text=""),
        ParsedPage(page_number=2, text="Second page text."),
    ]
    document = make_document(
        "Second page text.",
        pages=pages,
    )

    chunks = chunk_document(document)

    assert len(chunks) == 1
    assert chunks[0].page_numbers == [2]


def test_chunk_spanning_two_pdf_pages_preserves_both_page_numbers() -> None:
    pages = [
        ParsedPage(page_number=1, text="12345"),
        ParsedPage(page_number=2, text="ABCDEFGHIJKLMNO"),
    ]
    document = make_document(
        "12345\n\nABCDEFGHIJKLMNO",
        pages=pages,
    )

    chunks = chunk_document(
        document,
        chunk_size=20,
        overlap=3,
    )

    assert chunks[0].page_numbers == [1, 2]
