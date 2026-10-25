
import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from app.rag.chunking import DocumentChunk


@dataclass(frozen=True)
class EmbeddingConfig:
    model_name: str = "majentik/Qwen3-Embedding-4B-MLX-4bit"
    dimension: int = 2560
    batch_size: int = 1
    max_length: int = 512

    def __post_init__(self) -> None:
        if not isinstance(self.model_name, str) or not self.model_name.strip():
            raise ValueError("model_name must be a non-empty string")
        for name in ("dimension", "batch_size", "max_length"):
            value = getattr(self, name)
            if type(value) is not int or value <= 0:
                raise ValueError(f"{name} must be a positive integer")


class EmbeddingError(RuntimeError):
    """The embedding backend could not load or produce valid vectors."""


class EmbeddingBackend(Protocol):
    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        ...

    def embed_text(self, text: str) -> list[float]:
        ...


@dataclass
class EmbeddedChunk:
    chunk: DocumentChunk
    vector: list[float]


def embed_chunks(
    chunks: Sequence[DocumentChunk], backend: EmbeddingBackend,
) -> list[EmbeddedChunk]:
    if not isinstance(chunks, Sequence) or isinstance(chunks, (str, bytes)):
        raise TypeError("chunks must be a sequence of DocumentChunk objects")
    items = list(chunks)
    if any(not isinstance(chunk, DocumentChunk) for chunk in items):
        raise TypeError("chunks must contain only DocumentChunk objects")
    if not items:
        return []
    vectors = backend.embed([chunk.text for chunk in items])
    if len(vectors) != len(items):
        raise EmbeddingError("Backend returned an incorrect number of vectors")
    return [EmbeddedChunk(chunk, vector) for chunk, vector in zip(items, vectors)]


class MLXEmbeddingBackend:


    def __init__(self, config: EmbeddingConfig | None = None) -> None:
        self.config = config if config is not None else EmbeddingConfig()
        self._model = None
        self._tokenizer = None
        self._generate = None

    def embed_text(self, text: str) -> list[float]:
        return self.embed([text])[0]

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not isinstance(texts, Sequence) or isinstance(texts, (str, bytes)):
            raise TypeError("texts must be a sequence of strings, not a single string")
        items = list(texts)
        for index, text in enumerate(items):
            if not isinstance(text, str):
                raise TypeError(f"texts[{index}] must be a string")
            if not text.strip():
                raise ValueError(f"texts[{index}] must not be blank")
        if not items:
            return []

        if self._model is None:
            try:
                from mlx_embeddings import generate, load

                model, tokenizer = load(self.config.model_name)
            except Exception as error:
                raise EmbeddingError(
                    f"Could not load MLX embedding model {self.config.model_name}; "
                    "check mlx-embeddings, model access and Apple Metal availability"
                ) from error
            self._model, self._tokenizer = model, tokenizer
            self._generate = generate

        vectors: list[list[float]] = []
        for start in range(0, len(items), self.config.batch_size):
            batch = items[start:start + self.config.batch_size]
            try:
                output = self._generate(
                    self._model, self._tokenizer, texts=batch,
                    max_length=self.config.max_length,
                )
                rows = output.text_embeds.tolist()
                self._validate_vectors(rows, len(batch))
            except Exception as error:
                raise EmbeddingError(
                    f"MLX embedding inference failed for batch starting at index {start}"
                ) from error
            vectors.extend(rows)
        return vectors

    def _validate_vectors(self, rows: list[list[float]], count: int) -> None:
        if len(rows) != count:
            raise ValueError("Incorrect number of embedding vectors")
        for row in rows:
            if len(row) != self.config.dimension:
                raise ValueError(f"Expected embedding dimension {self.config.dimension}")
            if not all(math.isfinite(value) for value in row):
                raise ValueError("Embedding contains non-finite values")
            norm = math.sqrt(sum(value * value for value in row))
            if abs(norm - 1.0) > 0.01:
                raise ValueError("Embedding is not L2-normalized")
