from pydantic import BaseModel, Field

from src.rag.retriever import VectorRetriever


class RetrievalEvalCase(BaseModel):
    query: str
    relevant_chunk_ids: list[str] = Field(min_length=1)


class RetrievalEvalResult(BaseModel):
    query: str
    precision_at_k: float
    recall_at_k: float
    retrieved_chunk_ids: list[str]
    relevant_chunk_ids: list[str]


class RetrievalEvalReport(BaseModel):
    cases: list[RetrievalEvalResult]
    mean_precision_at_k: float
    mean_recall_at_k: float


def precision_at_k(
    retrieved_ids: list[str],
    relevant_ids: set[str],
    *,
    k: int,
) -> float:
    if k <= 0:
        return 0.0
    top = retrieved_ids[:k]
    if not top:
        return 0.0
    hits = sum(1 for chunk_id in top if chunk_id in relevant_ids)
    return hits / len(top)


def recall_at_k(
    retrieved_ids: list[str],
    relevant_ids: set[str],
    *,
    k: int,
) -> float:
    if not relevant_ids:
        return 0.0
    top = retrieved_ids[:k]
    hits = sum(1 for chunk_id in top if chunk_id in relevant_ids)
    return hits / len(relevant_ids)


def build_default_eval_dataset() -> list[RetrievalEvalCase]:
    return [
        RetrievalEvalCase(
            query="transfer limit human approval",
            relevant_chunk_ids=["doc-3-chunk-0"],
        ),
        RetrievalEvalCase(
            query="password reset identity verification",
            relevant_chunk_ids=["doc-1-chunk-0"],
        ),
        RetrievalEvalCase(
            query="complaint escalation SLA",
            relevant_chunk_ids=["doc-2-chunk-0"],
        ),
    ]


async def run_retrieval_evaluation(
    dataset: list[RetrievalEvalCase],
    retriever: VectorRetriever | None = None,
    *,
    top_k: int = 3,
) -> RetrievalEvalReport:
    retriever = retriever or VectorRetriever()
    results: list[RetrievalEvalResult] = []

    for case in dataset:
        retrieved = await retriever.retrieve(case.query, top_k=top_k)
        retrieved_ids = [item.chunk.id for item in retrieved]
        relevant = set(case.relevant_chunk_ids)

        results.append(
            RetrievalEvalResult(
                query=case.query,
                precision_at_k=precision_at_k(retrieved_ids, relevant, k=top_k),
                recall_at_k=recall_at_k(retrieved_ids, relevant, k=top_k),
                retrieved_chunk_ids=retrieved_ids,
                relevant_chunk_ids=case.relevant_chunk_ids,
            )
        )

    mean_precision = sum(item.precision_at_k for item in results) / len(results)
    mean_recall = sum(item.recall_at_k for item in results) / len(results)

    return RetrievalEvalReport(
        cases=results,
        mean_precision_at_k=round(mean_precision, 4),
        mean_recall_at_k=round(mean_recall, 4),
    )
