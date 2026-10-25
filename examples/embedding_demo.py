
from app.rag.chunking import DocumentChunk
from app.rag.embeddings import MLXEmbeddingBackend, embed_chunks


def main() -> None:
    backend = MLXEmbeddingBackend()
    vector = backend.embed_text("Novosibirsk State University offers educational courses.")
    chunks = [
        DocumentChunk("Linear algebra studies vector spaces.", "course.txt", 0),
        DocumentChunk("Calculus studies derivatives and integrals.", "course.txt", 1),
    ]
    embedded = embed_chunks(chunks, backend)
    assert len(vector) == 2560
    assert len(embedded) == 2
    assert all(len(item.vector) == 2560 for item in embedded)
    assert all(item.chunk is chunk for item, chunk in zip(embedded, chunks))
    print("Single vector dimension:", len(vector))
    print("Chunk vectors:", len(embedded))
    print("Success!")


if __name__ == "__main__":
    main()
