import logging

from qdrant_client import QdrantClient, models

from backend.core.config import settings

logger = logging.getLogger(__name__)

COLLECTION = "rag_chunks_v1"


def _client() -> QdrantClient:
    return QdrantClient(url=settings.qdrant_url)


def delete_document_points(space_id: str, document_id: str) -> None:
    """Удаляет все точки документа из Qdrant по payload (space_id, document_id).
    Сейчас — прямой вызов Qdrant по схеме payload из vector_store.py.
    РЕВЬЮЕР ПРОВЕРЬ НЕ НУЖНО ЛИ В(участнику) РАСШИРЯТЬ КОНТРАКТ СО МНОЙ????
    """
    client = _client()
    try:
        if not client.collection_exists(COLLECTION):
            return
        client.delete(
            collection_name=COLLECTION,
            points_selector=models.FilterSelector(
                filter=models.Filter(must=[
                    models.FieldCondition(key="space_id", match=models.MatchValue(value=space_id)),
                    models.FieldCondition(key="document_id", match=models.MatchValue(value=document_id)),
                ])
            ),
            wait=True,
        )
    except Exception:
        logger.exception("qdrant cleanup failed space=%s document=%s", space_id, document_id)
    finally:
        client.close()


def delete_space_points(space_id: str) -> None:
    """Удаляет все точки пространства из Qdrant."""
    client = _client()
    try:
        if not client.collection_exists(COLLECTION):
            return
        client.delete(
            collection_name=COLLECTION,
            points_selector=models.FilterSelector(
                filter=models.Filter(must=[
                    models.FieldCondition(key="space_id", match=models.MatchValue(value=space_id)),
                ])
            ),
            wait=True,
        )
    except Exception:
        logger.exception("qdrant cleanup failed space=%s", space_id)
    finally:
        client.close()