"""Mock cross-encoder reranker."""

from src.rag.documents import Chunk, RetrievalResult


def rerank(
    query: str,
    candidates: list[RetrievalResult],
    *,
    top_k: int = 5,
) -> list[RetrievalResult]:
    """Re-score candidates using query+chunk joint relevance (mock heuristic)."""
    query_terms = {term.lower() for term in query.split() if len(term) > 2}
    rescored: list[tuple[float, RetrievalResult]] = []

    for item in candidates:
        chunk_terms = {term.lower() for term in item.chunk.content.split() if len(term) > 2}
        overlap = len(query_terms & chunk_terms) / max(len(query_terms), 1)
        joint_score = (0.6 * item.score) + (0.4 * overlap)
        rescored.append((joint_score, item))

    rescored.sort(key=lambda pair: pair[0], reverse=True)

    results: list[RetrievalResult] = []
    for rank, (score, item) in enumerate(rescored[:top_k], start=1):
        results.append(
            RetrievalResult(chunk=item.chunk, score=round(score, 4), rank=rank)
        )

    return results
