import pytest
from qdrant_client import QdrantClient, models

from app.rag.chunking import DocumentChunk
from app.rag.embeddings import EmbeddedChunk, embed_chunks
from app.rag.vector_store import VectorStore, lexical_vector


class FakeBackend:
    def embed(self, texts):
        return [[1.0, 0.0, 0.0] for _ in texts]


@pytest.fixture
def store():
    client = QdrantClient(":memory:")
    try:
        result = VectorStore(client, dimension=3)
        result.ensure_collection()
        yield result
    finally:
        client.close()


def chunk(text="Quantum mechanics", index=0):
    return DocumentChunk(text, "lecture.pdf", index, [2, 3], 10, 10 + len(text),
                         {"file_type": "pdf", "space_id": "cannot override scope"})


def test_schema_idempotent_and_mismatch(store):
    store.ensure_collection()
    params = store.client.get_collection(store.collection).config.params
    assert params.vectors["dense"].size == 3
    assert params.sparse_vectors["lexical"].modifier == models.Modifier.IDF
    with pytest.raises(ValueError, match="Incompatible"):
        VectorStore(store.client, dimension=2560).ensure_collection()


def test_fake_embedding_roundtrip_and_update(store):
    original = chunk()
    items = embed_chunks([original], FakeBackend())
    ids = store.upsert(items, space_id="course-a", document_id="doc-1")
    assert store.upsert(items, space_id="course-a", document_id="doc-1") == ids
    assert store.client.count(store.collection).count == 1
    hit = store.search([1, 0, 0], space_id="course-a")[0]
    assert hit.chunk == original
    assert hit.document_id == "doc-1"
    assert hit.space_id == "course-a"
    assert hit.score == pytest.approx(1)
    assert hit.point_id == ids[0]
    updated = chunk("Updated content")
    store.upsert(embed_chunks([updated], FakeBackend()),
                 space_id="course-a", document_id="doc-1")
    assert store.client.count(store.collection).count == 1
    assert store.search([1, 0, 0], space_id="course-a")[0].chunk == updated


@pytest.mark.parametrize("hybrid", [False, True])
def test_space_isolation_and_document_identity(store, hybrid):
    for space in ("course-a", "course-b"):
        for document in ("doc-1", "doc-2"):
            store.upsert(embed_chunks([chunk()], FakeBackend()),
                         space_id=space, document_id=document)
    assert store.client.count(store.collection).count == 4
    kwargs = {"query_text": "Quantum"} if hybrid else {}
    hits = store.search([1, 0, 0], space_id="course-a", **kwargs)
    assert len(hits) == 2
    assert {h.space_id for h in hits} == {"course-a"}
    assert {h.document_id for h in hits} == {"doc-1", "doc-2"}
    assert store.search([1, 0, 0], space_id="missing", **kwargs) == []


def test_lexical_branch_changes_hybrid_ranking(store):
    store.upsert([
        EmbeddedChunk(chunk("ordinary text", 0), [1, 0, 0]),
        EmbeddedChunk(chunk("rareidentifier", 1), [0, 1, 0]),
    ], space_id="a", document_id="d")
    assert store.search([1, 0, 0], space_id="a", limit=1)[0].chunk.chunk_index == 0
    hit = store.search([1, 0, 0], space_id="a", query_text="rareidentifier", limit=1)[0]
    assert hit.chunk.chunk_index == 1


def test_sparse_tokenization():
    assert lexical_vector("МЕХАНИКА механика").indices == lexical_vector("механика").indices
    assert lexical_vector("a a", query=True).values == [1.0]
    assert lexical_vector("!!!").indices == []


@pytest.mark.parametrize("vector", [[1, 0], [0, 0, 0], [float("nan"), 0, 1],
                                   [float("inf"), 0, 1], [True, 0, 1]])
def test_invalid_vectors_do_not_write(store, vector):
    with pytest.raises(ValueError):
        store.upsert([EmbeddedChunk(chunk(), vector)], space_id="a", document_id="d")
    assert store.client.count(store.collection).count == 0
    with pytest.raises(ValueError):
        store.search(vector, space_id="a")


@pytest.mark.parametrize("space", [None, "", " ", 1])
def test_invalid_scope(store, space):
    with pytest.raises(ValueError):
        store.search([1, 0, 0], space_id=space)
    with pytest.raises(ValueError):
        store.upsert([], space_id=space, document_id="d")


def test_validation_before_batch_write(store):
    with pytest.raises(ValueError, match="Duplicate"):
        store.upsert(embed_chunks([chunk(), chunk()], FakeBackend()),
                     space_id="a", document_id="d")
    assert store.client.count(store.collection).count == 0
    assert store.upsert([], space_id="a", document_id="d") == []
    for kwargs in ({"limit": 0}, {"query_text": "!!!"},
                   {"query_text": "x", "candidate_limit": 1}):
        with pytest.raises(ValueError):
            store.search([1, 0, 0], space_id="a", **kwargs)


def test_default_2560_dimension():
    client = QdrantClient(":memory:")
    try:
        store = VectorStore(client)
        store.ensure_collection()
        vector = [1.0] + [0.0] * 2559
        store.upsert([EmbeddedChunk(chunk(), vector)], space_id="a", document_id="d")
        assert store.search(vector, space_id="a")[0].chunk.text == "Quantum mechanics"
    finally:
        client.close()


def test_reject_missing_sparse_schema():
    client = QdrantClient(":memory:")
    try:
        client.create_collection("old", vectors_config={"dense": models.VectorParams(
            size=3, distance=models.Distance.COSINE)})
        with pytest.raises(ValueError, match="Incompatible"):
            VectorStore(client, collection="old", dimension=3).ensure_collection()
    finally:
        client.close()
