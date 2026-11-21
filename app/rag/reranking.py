import math
from collections.abc import Callable

from app.rag.vector_store import SearchHit


def rerank_hits(
    question: str, hits: list[SearchHit],
    predict: Callable[[list[tuple[str, str]]], object],
) -> list[SearchHit]:
    if not hits:
        return []
    scores = list(predict([(question, hit.chunk.text) for hit in hits]))
    if len(scores) != len(hits) or any(not math.isfinite(float(v)) for v in scores):
        raise ValueError("Reranker returned invalid scores")
    ranked = sorted(zip(hits, scores), key=lambda pair: float(pair[1]), reverse=True)
    return [hit for hit, _ in ranked]


class CrossEncoderReranker:


    model_name = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"

    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name or self.model_name
        self._model = None

    def predict(self, pairs: list[tuple[str, str]]):
        if self._model is None:
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder(self.model_name, device="cpu", max_length=512)
        return self._model.predict(pairs, batch_size=4, show_progress_bar=False)
