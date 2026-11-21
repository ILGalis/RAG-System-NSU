
from dataclasses import dataclass
from pathlib import Path
from threading import Lock

from app.rag.answers import RAGAnswer, RAGService
from app.rag.chunking import chunk_document
from app.rag.embeddings import EmbeddingBackend, EmbeddingError, embed_chunks
from app.rag.llm import LLMError, LLMProvider, LLMRateLimit, LLMTimeout
from app.rag.parsers.docx import DOCXParser
from app.rag.parsers.pdf import PDFParser
from app.rag.parsers.txt import TXTParser
from app.rag.reranking import CrossEncoderReranker
from app.rag.retrieval import RetrievalError, Retriever
from app.rag.vector_store import VectorStore


class RAGOperationError(RuntimeError):
    """Public error suitable for mapping to a Backend response."""

    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable


@dataclass(frozen=True)
class IngestionResult:
    space_id: str
    document_id: str
    source_name: str
    point_ids: tuple[str, ...]


def _identifier(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise RAGOperationError("invalid_input", f"{name} must be a non-empty string")


class RAGApplication:

    def __init__(self, embedding: EmbeddingBackend, store: VectorStore,
                 provider: LLMProvider, *, reranker: CrossEncoderReranker | None = None) -> None:
        self.embedding = embedding
        self.store = store
        self.answers = RAGService(Retriever(embedding, store, reranker=reranker), provider)
        self._lock = Lock()

    def ingest_document(self, path: str | Path, *, space_id: str,
                        document_id: str) -> IngestionResult:
        _identifier(space_id, "space_id")
        _identifier(document_id, "document_id")
        if not isinstance(path, (str, Path)) or not str(path).strip():
            raise RAGOperationError("invalid_input", "Document path is required")
        path = Path(path)
        parsers = {".pdf": PDFParser, ".docx": DOCXParser, ".txt": TXTParser}
        if path.suffix.lower() not in parsers:
            raise RAGOperationError("unsupported_format", "Unsupported document format")
        try:
            document = parsers[path.suffix.lower()]().parse(path)
        except Exception:  # noqa: BLE001 - sanitize errors at the dependency boundary
            raise RAGOperationError("document_read_failed", "Could not read the document") from None
        chunks = chunk_document(document)
        if not chunks:
            raise RAGOperationError("empty_document", "Document contains no extractable text")
        with self._lock:
            try:
                embedded = embed_chunks(chunks, self.embedding)
            except Exception:  # noqa: BLE001 - sanitize errors at the dependency boundary
                raise RAGOperationError("embedding_failed", "Could not encode the document") from None
            try:
                point_ids = self.store.upsert(
                    embedded, space_id=space_id, document_id=document_id,
                )
            except Exception:  # noqa: BLE001 - sanitize errors at the dependency boundary
                raise RAGOperationError(
                    "storage_failed", "Could not store the document", retryable=True,
                ) from None
        return IngestionResult(space_id, document_id, document.source_name, tuple(point_ids))

    def ask(self, question: str, *, space_id: str) -> RAGAnswer:
        _identifier(space_id, "space_id")
        _identifier(question, "question")
        with self._lock:
            try:
                return self.answers.ask(question, space_id=space_id)
            except LLMRateLimit:
                raise RAGOperationError(
                    "rate_limited", "Answer service is busy", retryable=True,
                ) from None
            except LLMTimeout:
                raise RAGOperationError(
                    "generation_timeout", "Answer service timed out", retryable=True,
                ) from None
            except LLMError:
                raise RAGOperationError("generation_failed", "Could not generate an answer") from None
            except EmbeddingError:
                raise RAGOperationError("embedding_failed", "Could not encode the question") from None
            except RetrievalError:
                raise RAGOperationError("retrieval_failed", "Could not retrieve materials") from None
            except Exception:  # noqa: BLE001 - sanitize errors at the dependency boundary
                raise RAGOperationError("rag_failed", "Could not process the question") from None
