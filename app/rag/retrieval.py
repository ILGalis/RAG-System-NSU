from app.rag.embeddings import EmbeddingBackend
from app.rag.vector_store import SearchHit, VectorStore, lexical_vector


class RetrievalError(RuntimeError):
    """The search results could not be used safely."""


class Retriever:
    def __init__(self, embedding: EmbeddingBackend, store: VectorStore) -> None:
        self.embedding = embedding
        self.store = store

    def retrieve(self, question: str, *, space_id: str, limit: int = 5) -> list[SearchHit]:
        if not isinstance(space_id, str) or not space_id.strip():
            raise ValueError("space_id must be a non-empty string")
        if not isinstance(question, str) or not question.strip():
            raise ValueError("question must be a non-empty string")
        if type(limit) is not int or limit <= 0:
            raise ValueError("limit must be a positive integer")

        question = question.strip()
        hits = self.store.search(
            self.embedding.embed_text(question),
            space_id=space_id,
            limit=limit,
            query_text=question if lexical_vector(question, query=True).indices else None,
            candidate_limit=max(50, limit),
        )
        if any(hit.space_id != space_id for hit in hits):
            raise RetrievalError("Search returned a hit outside the requested space")
        return hits
