import logging

from backend.db.connection import SessionLocal
from backend.models import Document
from app.core.ids import document_id_str, space_id_str

logger = logging.getLogger(__name__)


def ingest_document(document_id: int) -> None:
    """Фоновая обработка документа. Вызывает RAG-пайплайн B.

    Вызывается через FastAPI BackgroundTasks после успешного сохранения файла
    и создания Document. Открывает собственную сессию — к этому моменту
    оригинальный request уже завершён.
    """
    db = SessionLocal()
    try:
        doc = db.get(Document, document_id)
        if doc is None:
            logger.warning("ingest_document: document %s not found", document_id)
            return

        doc.status = "processing"
        db.commit()

        try:
            from app.rag.ingest import ingest_document as rag_ingest
            rag_ingest(
                space_id=space_id_str(doc.space_id),
                document_id=document_id_str(doc.id),
                file_path=doc.file_path,
            )
            # B ожидает str для space_id/document_id (см. контракт collection).
            raise NotImplementedError("RAG ingest not wired yet (week 7-8)")

            doc.status = "ready"
            doc.error_message = None
        except Exception as exc:
            logger.exception("ingest failed for document %s", document_id)
            doc.status = "failed"
            doc.error_message = str(exc)[:2000]

        db.commit()
    finally:
        db.close()