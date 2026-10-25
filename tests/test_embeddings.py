import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.rag.chunking import DocumentChunk
from app.rag.embeddings import (
    EmbeddingConfig,
    EmbeddingError,
    MLXEmbeddingBackend,
    embed_chunks,
)


@pytest.fixture
def mlx(monkeypatch):
    def generate_vectors(model, tokenizer, texts, max_length):
        vectors = [[0.0] * 2560 for _ in texts]
        for text, vector in zip(texts, vectors):
            vector[0 if text == "first" else 1] = 1.0
        return SimpleNamespace(text_embeds=SimpleNamespace(tolist=lambda: vectors))

    module = SimpleNamespace(
        load=Mock(return_value=(object(), object())),
        generate=Mock(side_effect=generate_vectors),
    )
    monkeypatch.setitem(sys.modules, "mlx_embeddings", module)
    return module


def test_single_text_and_model_reuse(mlx):
    backend = MLXEmbeddingBackend()
    vector = backend.embed_text("first")
    assert len(vector) == 2560
    assert vector[0] == 1.0
    assert backend.embed_text("second")[1] == 1.0
    mlx.load.assert_called_once_with(EmbeddingConfig().model_name)


def test_batch_order_and_bounded_inference(mlx):
    backend = MLXEmbeddingBackend(EmbeddingConfig(batch_size=2))
    vectors = backend.embed(["second", "first", "second"])
    assert [vector[:2] for vector in vectors] == [[0, 1], [1, 0], [0, 1]]
    assert [call.kwargs["texts"] for call in mlx.generate.call_args_list] == [
        ["second", "first"], ["second"],
    ]
    mlx.load.assert_called_once()


def test_empty_batch_does_not_load_model(mlx):
    assert MLXEmbeddingBackend().embed([]) == []
    mlx.load.assert_not_called()


@pytest.mark.parametrize("texts, error", [
    ("first", TypeError), (None, TypeError), ([1], TypeError),
    ([""], ValueError), (["first", "  "], ValueError),
])
def test_invalid_input_before_loading(mlx, texts, error):
    with pytest.raises(error):
        MLXEmbeddingBackend().embed(texts)
    mlx.load.assert_not_called()


@pytest.mark.parametrize("field, value", [
    ("batch_size", 0), ("max_length", -1), ("dimension", True),
    ("model_name", ""),
])
def test_invalid_configuration(field, value):
    with pytest.raises(ValueError):
        EmbeddingConfig(**{field: value})


def test_loading_failure_can_be_retried(mlx):
    failure = ImportError("Metal unavailable")
    mlx.load.side_effect = failure
    backend = MLXEmbeddingBackend()
    with pytest.raises(EmbeddingError, match="Could not load") as caught:
        backend.embed_text("first")
    assert caught.value.__cause__ is failure
    mlx.load.side_effect = None
    assert len(backend.embed_text("first")) == 2560


def test_inference_failure(mlx):
    failure = RuntimeError("Out of memory")
    mlx.generate.side_effect = failure
    with pytest.raises(EmbeddingError, match="index 0") as caught:
        MLXEmbeddingBackend().embed_text("first")
    assert caught.value.__cause__ is failure


@pytest.mark.parametrize("rows", [
    [], [[1.0]], [[float("nan")] * 2560], [[float("inf")] * 2560],
    [[0.0] * 2560], [[1.0] * 2560],
])
def test_invalid_model_output(mlx, rows):
    mlx.generate.side_effect = None
    mlx.generate.return_value = SimpleNamespace(
        text_embeds=SimpleNamespace(tolist=lambda: rows)
    )
    with pytest.raises(EmbeddingError):
        MLXEmbeddingBackend().embed_text("first")


def test_chunks_keep_metadata_with_replaceable_backend():
    class FakeBackend:
        def embed(self, texts):
            return [[float(index)] for index, _ in enumerate(texts)]

        def embed_text(self, text):
            return self.embed([text])[0]

    chunks = [
        DocumentChunk("first", "course.pdf", 0, page_numbers=[1]),
        DocumentChunk("second", "course.pdf", 1, metadata={"file_type": "pdf"}),
    ]
    result = embed_chunks(chunks, FakeBackend())
    assert [item.vector for item in result] == [[0.0], [1.0]]
    assert all(item.chunk is chunk for item, chunk in zip(result, chunks))
    assert result[0].chunk.page_numbers == [1]
    assert result[1].chunk.metadata == {"file_type": "pdf"}
    assert embed_chunks([], FakeBackend()) == []


def test_chunk_backend_count_mismatch():
    backend = SimpleNamespace(embed=lambda texts: [])
    with pytest.raises(EmbeddingError, match="number"):
        embed_chunks([DocumentChunk("first", "test.txt", 0)], backend)


@pytest.mark.parametrize("chunks", ["text", None, ["text"]])
def test_invalid_chunks(chunks):
    with pytest.raises(TypeError):
        embed_chunks(chunks, SimpleNamespace())
