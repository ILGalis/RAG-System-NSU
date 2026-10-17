
from dataclasses import dataclass, field

from app.rag.parsers.base import ParsedDocument


@dataclass
class DocumentChunk:
    text: str
    source_name: str
    chunk_index: int
    page_numbers: list[int] = field(default_factory=list)
    start_char: int = 0
    end_char: int = 0
    metadata: dict[str, str] = field(default_factory=dict)


def chunk_document(
    document: ParsedDocument,
    chunk_size: int = 1000,
    overlap: int = 150,
) -> list[DocumentChunk]:
    """Split a parsed document into overlapping text chunks."""

    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError(
            "overlap must be non-negative and smaller than chunk_size"
        )

    text = document.text
    if not text.strip():
        return []

    # Map non-empty page ranges to positions in the combined document text.
    page_ranges: list[tuple[int, int, int]] = []
    position = 0

    for page in document.pages:
        if not page.text:
            continue

        if page_ranges:
            position += 2  # The parser joins pages with "\n\n".

        page_start = position
        position += len(page.text)
        page_ranges.append(
            (page_start, position, page.page_number)
        )

    chunks: list[DocumentChunk] = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))

        if end < len(text):
            search_text = text[start:end]
            paragraph_boundary = search_text.rfind("\n\n")
            sentence_boundary = max(
                search_text.rfind(". "),
                search_text.rfind("? "),
                search_text.rfind("! "),
            )

            boundary = (
                paragraph_boundary + 2
                if paragraph_boundary >= chunk_size // 2
                else sentence_boundary + 1
                if sentence_boundary >= chunk_size // 2
                else -1
            )

            if boundary > 0:
                end = start + boundary

        # Trim whitespace while keeping offsets aligned with the original text.
        chunk_start = start
        chunk_end = end

        while chunk_start < chunk_end and text[chunk_start].isspace():
            chunk_start += 1

        while chunk_end > chunk_start and text[chunk_end - 1].isspace():
            chunk_end -= 1

        chunk_text = text[chunk_start:chunk_end]

        if chunk_text:
            pages = [
                page_number
                for page_start, page_end, page_number in page_ranges
                if chunk_start < page_end and chunk_end > page_start
            ]

            chunks.append(
                DocumentChunk(
                    text=chunk_text,
                    source_name=document.source_name,
                    chunk_index=len(chunks),
                    page_numbers=pages,
                    start_char=chunk_start,
                    end_char=chunk_end,
                    metadata={"file_type": document.file_type},
                )
            )

        if end >= len(text):
            break

        next_start = max(start + 1, end - overlap)

        while next_start < end and not text[next_start - 1].isspace():
            next_start += 1

        start = next_start

    return chunks
