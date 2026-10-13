
from pathlib import Path

import pymupdf

from app.rag.parsers.base import ParsedDocument, ParsedPage


class PDFParser:
    
    def parse(self, file_path: str | Path) -> ParsedDocument:
        path = Path(file_path)

        if not path.is_file():
            raise FileNotFoundError(f"PDF file not found: {path}")

        if path.suffix.lower() != ".pdf":
            raise ValueError(f"Expected a PDF file, got: {path.name}")

        pages: list[ParsedPage] = []

        with pymupdf.open(path) as pdf:
            if pdf.is_encrypted:
                raise ValueError(f"Encrypted PDF is not supported: {path.name}")

            for page_number, page in enumerate(pdf, start=1):
                text = page.get_text().strip()
                pages.append(
                    ParsedPage(
                        page_number=page_number,
                        text=text,
                    )
                )

        full_text = "\n\n".join(
            page.text for page in pages if page.text
        )

        return ParsedDocument(
            text=full_text,
            source_name=path.name,
            file_type="pdf",
            pages=pages,
            metadata={"page_count": str(len(pages))},
        )
