
from pathlib import Path

from app.rag.parsers.base import ParsedDocument


class TXTParser:

    ENCODINGS = ("utf-8-sig", "cp1251", "cp1252")

    def parse(self, file_path: str | Path) -> ParsedDocument:
        path = Path(file_path)

        if not path.is_file():
            raise FileNotFoundError(f"TXT file not found: {path}")

        if path.suffix.lower() != ".txt":
            raise ValueError(
                f"Expected a TXT file, got: {path.name}"
            )

        raw_data = path.read_bytes()
        text = None

        for encoding in self.ENCODINGS:
            try:
                text = raw_data.decode(encoding)
                break
            except UnicodeDecodeError:
                continue

        if text is None:
            raise ValueError(
                f"Could not decode TXT file: {path.name}"
            )

        return ParsedDocument(
            text=text.strip(),
            source_name=path.name,
            file_type="txt",
            metadata={"encoding": encoding},
        )
