
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol


@dataclass
class ParsedPage:

    page_number: int
    text: str


@dataclass
class ParsedDocument:

    text: str
    source_name: str
    file_type: str
    pages: list[ParsedPage] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)


class DocumentParser(Protocol):

    def parse(self, file_path: str | Path) -> ParsedDocument:
        """Extract text and metadata from a document."""
        ...
