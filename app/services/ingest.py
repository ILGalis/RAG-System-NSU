import logging
from pathlib import Path

from backend.db.connection import SessionLocal
from backend.models import Document
from app.core.ids import document_id_str, space_id_str

logger = logging.getLogger(__name__)


def ingest_document(document_id: int) -> None:
    db = SessionLocal()
    try:
        doc = db.get(Document, document_id)
        if doc is None:
            logger.warning("ingest_document(%s): not found", document_id)
            return

        doc.status = "processing"
        db.commit()

        try:
            _run_pipeline(doc)
            doc.status = "ready"
            doc.error_message = None
        except Exception as exc:
            logger.exception("ingest_document(%s) failed", document_id)
            doc.status = "failed"
            doc.error_message = str(exc)[:2000]

        db.commit()
    finally:
        db.close()


def _pick_parser(file_type: str):
    if file_type == "pdf":
        from app.rag.parsers.pdf import PDFParser
        return PDFParser()
    if file_type == "docx":
        from app.rag.parsers.docx import DOCXParser
        return DOCXParser()
    if file_type == "txt":
        from app.rag.parsers.txt import TXTParser
        return TXTParser()
    raise ValueError(f"Unsupported file_type: {file_type}")


def _run_pipeline(doc: Document) -> None:
    from qdrant_client import QdrantClient

    from app.rag.chunking import chunk_document
    from app.rag.embeddings import MLXEmbeddingBackend, embed_chunks
    from app.rag.vector_store import VectorStore
    from backend.core.config import settings

    parser = _pick_parser(doc.file_type)
    parsed = parser.parse(Path(doc.file_path))
    chunks = chunk_document(parsed)
    if not chunks:
        raise ValueError("Document produced no chunks")

    backend = MLXEmbeddingBackend()
    embedded = embed_chunks(chunks, backend)

    client = QdrantClient(url=settings.qdrant_url)
    try:
        store = VectorStore(client)
        store.ensure_collection()
        store.upsert(
            embedded,
            space_id=space_id_str(doc.space_id),
            document_id=document_id_str(doc.id),
        )
    finally:
        client.close()