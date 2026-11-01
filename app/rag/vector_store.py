import hashlib
import json
import math
import re
from collections import Counter
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from uuid import NAMESPACE_URL, uuid5

from qdrant_client import QdrantClient, models

from app.rag.chunking import DocumentChunk
from app.rag.embeddings import EmbeddedChunk


def _identifier(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Identifiers must be non-empty strings")
    return value


def lexical_vector(text: str, *, query: bool = False) -> models.SparseVector:
    counts = Counter(re.findall(r"\w+", text.casefold()))
    weights: dict[int, float] = {}
    length = sum(counts.values())
    for token, count in counts.items():
        index = int.from_bytes(hashlib.sha256(token.encode()).digest()[:4], "big")
        weight = 1.0 if query else count * 2.2 / (count + 1.2 * (0.25 + 0.75 * length / 200))
        weights[index] = weights.get(index, 0.0) + weight
    indices = sorted(weights)
    return models.SparseVector(indices=indices, values=[weights[i] for i in indices])


@dataclass(frozen=True)
class SearchHit:
    point_id: str
    score: float
    space_id: str
    document_id: str
    chunk: DocumentChunk


class VectorStore:

    def __init__(self, client: QdrantClient, *, collection: str = "rag_chunks_v1",
                 dimension: int = 2560) -> None:
        if type(dimension) is not int or dimension <= 0:
            raise ValueError("dimension must be a positive integer")
        self.client = client
        self.collection = _identifier(collection)
        self.dimension = dimension

    def ensure_collection(self) -> None:
        if not self.client.collection_exists(self.collection):
            self.client.create_collection(
                self.collection,
                vectors_config={"dense": models.VectorParams(
                    size=self.dimension, distance=models.Distance.COSINE)},
                sparse_vectors_config={"lexical": models.SparseVectorParams(
                    modifier=models.Modifier.IDF)},
            )
        params = self.client.get_collection(self.collection).config.params
        dense = params.vectors
        sparse = params.sparse_vectors or {}
        if (not isinstance(dense, dict) or "dense" not in dense
                or dense["dense"].size != self.dimension
                or dense["dense"].distance != models.Distance.COSINE
                or "lexical" not in sparse
                or sparse["lexical"].modifier != models.Modifier.IDF):
            raise ValueError("Incompatible collection schema; use a new collection and reindex")

    def _vector(self, vector: Sequence[float]) -> list[float]:
        values = list(vector)
        if (len(values) != self.dimension
                or any(isinstance(v, bool) or not isinstance(v, (int, float))
                       or not math.isfinite(v) for v in values)
                or not any(values)):
            raise ValueError("Dense vector must have the configured dimension and finite nonzero values")
        return [float(v) for v in values]

    def upsert(self, chunks: Sequence[EmbeddedChunk], *, space_id: str,
               document_id: str) -> list[str]:
        space_id, document_id = _identifier(space_id), _identifier(document_id)
        points = []
        seen = set()
        for item in chunks:
            chunk = item.chunk
            if type(chunk.chunk_index) is not int or chunk.chunk_index < 0:
                raise ValueError("chunk_index must be a non-negative integer")
            if chunk.chunk_index in seen:
                raise ValueError("Duplicate chunk_index in batch")
            seen.add(chunk.chunk_index)
            if not chunk.text.strip():
                raise ValueError("Chunk text must not be blank")
            point_id = str(uuid5(NAMESPACE_URL, json.dumps(
                [space_id, document_id, chunk.chunk_index], ensure_ascii=False)))
            points.append(models.PointStruct(
                id=point_id,
                vector={"dense": self._vector(item.vector),
                        "lexical": lexical_vector(chunk.text)},
                payload={"schema_version": 1, "space_id": space_id,
                         "document_id": document_id, **asdict(chunk)},
            ))
        if points:
            self.client.upsert(self.collection, points=points, wait=True)
        return [str(point.id) for point in points]

    def search(self, vector: Sequence[float], *, space_id: str, limit: int = 10,
               query_text: str | None = None, candidate_limit: int = 50) -> list[SearchHit]:
        scope = models.Filter(must=[models.FieldCondition(
            key="space_id", match=models.MatchValue(value=_identifier(space_id)))])
        dense = self._vector(vector)
        if type(limit) is not int or limit <= 0:
            raise ValueError("limit must be a positive integer")
        kwargs = {"query": dense, "using": "dense"}
        if query_text is not None:
            if not isinstance(query_text, str) or not lexical_vector(query_text).indices:
                raise ValueError("Hybrid query must contain word tokens")
            if type(candidate_limit) is not int or candidate_limit < limit:
                raise ValueError("candidate_limit must be at least limit")
            kwargs = {
                "prefetch": [
                    models.Prefetch(query=dense, using="dense", filter=scope,
                                    limit=candidate_limit),
                    models.Prefetch(query=lexical_vector(query_text, query=True),
                                    using="lexical", filter=scope, limit=candidate_limit),
                ],
                "query": models.FusionQuery(fusion=models.Fusion.RRF),
            }
        response = self.client.query_points(
            self.collection, query_filter=scope, limit=limit,
            with_payload=True, with_vectors=False, **kwargs,
        )
        hits = []
        for point in response.points:
            payload = point.payload
            hits.append(SearchHit(
                point_id=str(point.id), score=point.score,
                space_id=payload["space_id"], document_id=payload["document_id"],
                chunk=DocumentChunk(**{key: payload[key] for key in (
                    "text", "source_name", "chunk_index", "page_numbers",
                    "start_char", "end_char", "metadata")}),
            ))
        return hits
