from src.rag.chunking import chunk_text
from src.rag.documents import Chunk, SourceDocument
from src.rag.embeddings import EmbeddingProvider, MockEmbeddingProvider, cosine_similarity
from src.rag.preparation import prepare_documents, prepared_to_chunks


class KnowledgeBase:
    """Ingestion → chunking → embedding → in-memory index."""

    def __init__(self, embedding_provider: EmbeddingProvider | None = None) -> None:
        self.embedding_provider = embedding_provider or MockEmbeddingProvider()
        self.chunks: list[Chunk] = []
        self.vectors: list[list[float]] = []

    def ingest(
        self,
        documents: list[SourceDocument],
        *,
        chunk_size: int = 120,
        overlap: int = 30,
        strategy: str = "fixed",
    ) -> int:
        self.chunks.clear()
        self.vectors.clear()

        prepared = prepare_documents(
            documents,
            chunk_size=chunk_size,
            overlap=overlap,
            strategy=strategy,
        )
        chunks = prepared_to_chunks(prepared)

        for chunk in chunks:
            self.chunks.append(chunk)
            self.vectors.append(self.embedding_provider.embed(chunk.content))

        return len(self.chunks)


class VectorRetriever:
    """Vector search + keyword hybrid + metadata filter."""

    def __init__(self, knowledge_base: KnowledgeBase | None = None) -> None:
        self.knowledge_base = knowledge_base or _build_default_knowledge_base()

    async def retrieve(
        self,
        query: str,
        *,
        top_k: int = 3,
        metadata_filter: dict[str, str] | None = None,
    ) -> list:
        from src.rag.documents import RetrievalResult

        query_vector = self.knowledge_base.embedding_provider.embed(query)
        query_terms = {term.lower() for term in query.split() if len(term) > 2}

        scored: list[tuple[float, Chunk]] = []
        for chunk, vector in zip(self.knowledge_base.chunks, self.knowledge_base.vectors):
            if metadata_filter and not _matches_metadata(chunk.metadata, metadata_filter):
                continue

            vector_score = cosine_similarity(query_vector, vector)
            chunk_terms = {term.lower() for term in chunk.content.split() if len(term) > 2}
            keyword_score = len(query_terms & chunk_terms) / max(len(query_terms), 1)
            hybrid_score = (0.7 * vector_score) + (0.3 * keyword_score)

            if hybrid_score > 0:
                scored.append((hybrid_score, chunk))

        scored.sort(key=lambda item: item[0], reverse=True)

        results: list[RetrievalResult] = []
        for rank, (score, chunk) in enumerate(scored[:top_k], start=1):
            results.append(RetrievalResult(chunk=chunk, score=round(score, 4), rank=rank))

        return results


class MockRetriever:
    """Backward-compatible retriever used by workflow — vector retriever üstünde."""

    def __init__(self, retriever: VectorRetriever | None = None) -> None:
        self._retriever = retriever or VectorRetriever()

    async def retrieve(self, query: str, *, top_k: int = 3):
        results = await self._retriever.retrieve(query, top_k=top_k)
        return [result.chunk for result in results]


def _matches_metadata(chunk_metadata: dict[str, str], expected: dict[str, str]) -> bool:
    return all(chunk_metadata.get(key) == value for key, value in expected.items())


def _build_default_knowledge_base() -> KnowledgeBase:
    from src.rag.documents import default_banking_documents

    kb = KnowledgeBase()
    kb.ingest(default_banking_documents())
    return kb
