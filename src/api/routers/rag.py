from fastapi import APIRouter, Depends

from src.api.dependencies import get_llm_client
from src.api.schemas import RagEvalCaseResult, RagEvalResponse, RagQueryRequest, RagQueryResponse, RagSource
from src.llm.base import LLMClient
from src.rag.evaluation import build_default_eval_dataset, run_retrieval_evaluation
from src.rag.service import answer_with_sources

router = APIRouter(prefix="/v1", tags=["rag"])


@router.post("/rag/query", response_model=RagQueryResponse)
async def rag_query(
    body: RagQueryRequest,
    client: LLMClient = Depends(get_llm_client),
) -> RagQueryResponse:
    result = await answer_with_sources(body.question, client, top_k=body.top_k)

    return RagQueryResponse(
        question=result.question,
        source_chunk_ids=result.source_chunk_ids,
        sources=[
            RagSource(
                chunk_id=item.chunk.id,
                document_id=item.chunk.document_id,
                content=item.chunk.content,
                score=item.score,
                metadata=item.chunk.metadata,
            )
            for item in result.sources
        ],
        answer=result.answer,
        model=result.model,
    )


@router.get("/rag/eval", response_model=RagEvalResponse)
async def rag_eval() -> RagEvalResponse:
    report = await run_retrieval_evaluation(build_default_eval_dataset(), top_k=3)

    return RagEvalResponse(
        mean_precision_at_k=report.mean_precision_at_k,
        mean_recall_at_k=report.mean_recall_at_k,
        cases=[
            RagEvalCaseResult(
                query=case.query,
                precision_at_k=case.precision_at_k,
                recall_at_k=case.recall_at_k,
                retrieved_chunk_ids=case.retrieved_chunk_ids,
                relevant_chunk_ids=case.relevant_chunk_ids,
            )
            for case in report.cases
        ],
    )
