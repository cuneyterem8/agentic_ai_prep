from fastapi import APIRouter, Depends

from src.agents.classifier import classify_customer_message
from src.api.dependencies import get_llm_client
from src.api.schemas import ClassifyRequest, ClassifyResponse
from src.evals.run_evals import run_all_evals, run_classification_eval
from src.llm.base import LLMClient
from src.security.input_guardrails import validate_user_input

router = APIRouter(prefix="/v1", tags=["classify"])


@router.post("/classify", response_model=ClassifyResponse)
async def classify_message(
    body: ClassifyRequest,
    client: LLMClient = Depends(get_llm_client),
) -> ClassifyResponse:
    input_guardrail = validate_user_input(body.message)
    if input_guardrail.blocked:
        return ClassifyResponse(
            conversation_id=body.conversation_id,
            intent="unknown",
            risk_level="high",
            needs_human_approval=True,
            blocked=True,
            block_reasons=input_guardrail.reasons,
            model="input-guardrail",
        )

    result = await classify_customer_message(body.message, client)

    return ClassifyResponse(
        conversation_id=body.conversation_id,
        intent=result.intent.value,
        risk_level=result.risk_level.value,
        needs_human_approval=result.needs_human_approval,
        blocked=False,
        model="classification-chain",
    )


@router.get("/classify/eval")
async def classify_eval_endpoint(
    client: LLMClient = Depends(get_llm_client),
) -> dict:
    return await run_classification_eval(client)


@router.get("/evals/run")
async def run_all_evals_endpoint(
    client: LLMClient = Depends(get_llm_client),
) -> dict:
    return await run_all_evals(client)
