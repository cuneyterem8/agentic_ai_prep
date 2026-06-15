from fastapi import APIRouter, Depends

from src.agents.data_analyst import run_data_analyst
from src.api.dependencies import get_llm_client
from src.api.schemas import AnalystRequest, AnalystResponse
from src.evals.run_evals import run_golden_dataset_eval
from src.llm.base import LLMClient

router = APIRouter(prefix="/v1", tags=["analyst"])


@router.post("/analyst/query", response_model=AnalystResponse)
async def analyst_query(
    body: AnalystRequest,
    client: LLMClient = Depends(get_llm_client),
) -> AnalystResponse:
    result = await run_data_analyst(
        question=body.question,
        tenant_id=body.tenant_id,
        client=client,
        approval_granted=body.approval_granted,
    )

    return AnalystResponse(
        question=result.question,
        generated_sql=result.generated_sql,
        final_sql=result.final_sql,
        allowed=result.guardrail.allowed,
        sql_correct=result.correctness.is_correct,
        sql_repaired=result.sql_repaired,
        needs_human_approval=result.needs_human_approval,
        executed=result.executed,
        row_count=len(result.rows),
        analysis_summary=result.analysis_summary,
        confidence=result.confidence,
        guardrail_reasons=result.guardrail.reasons,
        correctness_issues=result.correctness.issues,
    )


@router.get("/analyst/eval")
async def analyst_eval(client: LLMClient = Depends(get_llm_client)) -> dict:
    return await run_golden_dataset_eval(client)
