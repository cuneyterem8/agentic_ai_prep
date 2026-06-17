import math

from pydantic import BaseModel, Field

from src.rag.retriever import VectorRetriever


class RetrievalEvalCase(BaseModel):
    query: str
    relevant_chunk_ids: list[str] = Field(min_length=1)
    relevance_grades: list[int] | None = None


class RetrievalEvalResult(BaseModel):
    query: str
    precision_at_k: float
    recall_at_k: float
    hit_rate_at_k: float
    reciprocal_rank: float
    ndcg_at_k: float
    retrieved_chunk_ids: list[str]
    relevant_chunk_ids: list[str]


class RetrievalEvalReport(BaseModel):
    cases: list[RetrievalEvalResult]
    mean_precision_at_k: float
    mean_recall_at_k: float
    mean_hit_rate_at_k: float
    mean_mrr: float
    mean_ndcg_at_k: float


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


def hit_rate_at_k(
    retrieved_ids: list[str],
    relevant_ids: set[str],
    *,
    k: int,
) -> float:
    top = retrieved_ids[:k]
    return 1.0 if any(chunk_id in relevant_ids for chunk_id in top) else 0.0


def reciprocal_rank(relevance_list: list[int]) -> float:
    for idx, rel in enumerate(relevance_list, start=1):
        if rel >= 1:
            return 1 / idx
    return 0.0


def mrr(relevance_lists: list[list[int]]) -> float:
    if not relevance_lists:
        return 0.0
    return sum(reciprocal_rank(rlist) for rlist in relevance_lists) / len(relevance_lists)


def dcg(relevances: list[float]) -> float:
    return sum(rel / math.log2(idx + 2) for idx, rel in enumerate(relevances))


def ndcg_at_k(relevances: list[float]) -> float:
    if not relevances:
        return 0.0
    ideal = sorted(relevances, reverse=True)
    ideal_dcg = dcg(ideal)
    if ideal_dcg == 0:
        return 0.0
    return dcg(relevances) / ideal_dcg


def build_default_eval_dataset() -> list[RetrievalEvalCase]:
    return [
        RetrievalEvalCase(
            query="transfer limit human approval",
            relevant_chunk_ids=["doc-3-chunk-0"],
            relevance_grades=[3],
        ),
        RetrievalEvalCase(
            query="password reset identity verification",
            relevant_chunk_ids=["doc-1-chunk-0"],
            relevance_grades=[3],
        ),
        RetrievalEvalCase(
            query="complaint escalation SLA",
            relevant_chunk_ids=["doc-2-chunk-0"],
            relevance_grades=[3],
        ),
        RetrievalEvalCase(
            query="FAST 7/24 transfer",
            relevant_chunk_ids=["doc-5-chunk-0"],
            relevance_grades=[3],
        ),
        RetrievalEvalCase(
            query="EFT business hours weekday",
            relevant_chunk_ids=["doc-5-chunk-1"],
            relevance_grades=[2],
        ),
    ]


def _relevance_list(retrieved_ids: list[str], relevant_ids: set[str], *, k: int) -> list[int]:
    return [1 if chunk_id in relevant_ids else 0 for chunk_id in retrieved_ids[:k]]


def _graded_relevance_list(
    retrieved_ids: list[str],
    relevant_ids: set[str],
    grades: dict[str, int] | None,
    *,
    k: int,
) -> list[float]:
    result: list[float] = []
    for chunk_id in retrieved_ids[:k]:
        if chunk_id in relevant_ids:
            result.append(float((grades or {}).get(chunk_id, 3)))
        else:
            result.append(0.0)
    return result


async def run_retrieval_evaluation(
    dataset: list[RetrievalEvalCase],
    retriever: VectorRetriever | None = None,
    *,
    top_k: int = 3,
) -> RetrievalEvalReport:
    retriever = retriever or VectorRetriever()
    results: list[RetrievalEvalResult] = []
    rr_lists: list[list[int]] = []

    for case in dataset:
        retrieved = await retriever.retrieve(case.query, top_k=top_k)
        retrieved_ids = [item.chunk.id for item in retrieved]
        relevant = set(case.relevant_chunk_ids)
        grade_map = (
            dict(zip(case.relevant_chunk_ids, case.relevance_grades))
            if case.relevance_grades
            else None
        )

        rel_list = _relevance_list(retrieved_ids, relevant, k=top_k)
        rr_lists.append(rel_list)
        graded = _graded_relevance_list(retrieved_ids, relevant, grade_map, k=top_k)

        results.append(
            RetrievalEvalResult(
                query=case.query,
                precision_at_k=precision_at_k(retrieved_ids, relevant, k=top_k),
                recall_at_k=recall_at_k(retrieved_ids, relevant, k=top_k),
                hit_rate_at_k=hit_rate_at_k(retrieved_ids, relevant, k=top_k),
                reciprocal_rank=reciprocal_rank(rel_list),
                ndcg_at_k=round(ndcg_at_k(graded), 4),
                retrieved_chunk_ids=retrieved_ids,
                relevant_chunk_ids=case.relevant_chunk_ids,
            )
        )

    n = len(results)
    return RetrievalEvalReport(
        cases=results,
        mean_precision_at_k=round(sum(item.precision_at_k for item in results) / n, 4),
        mean_recall_at_k=round(sum(item.recall_at_k for item in results) / n, 4),
        mean_hit_rate_at_k=round(sum(item.hit_rate_at_k for item in results) / n, 4),
        mean_mrr=round(mrr(rr_lists), 4),
        mean_ndcg_at_k=round(sum(item.ndcg_at_k for item in results) / n, 4),
    )
