from app.rag.embeddings import EmbeddingBackend, EmbeddingError
from app.rag.reranking import CrossEncoderReranker, rerank_hits
from app.rag.vector_store import SearchHit, VectorStore, lexical_vector


class RetrievalError(RuntimeError):
    """The search results could not be used safely."""


class Retriever:
    def __init__(self, embedding: EmbeddingBackend, store: VectorStore, *,
                 reranker: CrossEncoderReranker | None = None) -> None:
        self.embedding = embedding
        self.store = store
        self.reranker = reranker

    def retrieve(self, question: str, *, space_id: str, limit: int = 5) -> list[SearchHit]:
        if not isinstance(space_id, str) or not space_id.strip():
            raise ValueError("space_id must be a non-empty string")
        if not isinstance(question, str) or not question.strip():
            raise ValueError("question must be a non-empty string")
        if type(limit) is not int or limit <= 0:
            raise ValueError("limit must be a positive integer")

        question = question.strip()
        try:
            vector = self.embedding.embed_text(question)
        except Exception:  # noqa: BLE001 - sanitize errors at the dependency boundary
            raise EmbeddingError("Could not encode the question") from None
        try:
            hits = self.store.search(
                vector,
                space_id=space_id,
                limit=max(50, limit) if self.reranker else limit,
                query_text=question if lexical_vector(question, query=True).indices else None,
                candidate_limit=max(50, limit),
            )
        except Exception:  # noqa: BLE001 - sanitize errors at the dependency boundary
            raise RetrievalError("Could not retrieve materials") from None
        if any(hit.space_id != space_id for hit in hits):
            raise RetrievalError("Search returned a hit outside the requested space")
        if self.reranker:
            try:
                hits = rerank_hits(question, hits, self.reranker.predict)
            except Exception:  # noqa: BLE001 - sanitize optional inference errors
                raise RetrievalError("Could not rerank materials") from None
        return hits[:limit]
