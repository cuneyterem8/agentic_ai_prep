from fastapi import APIRouter, Depends

from src.agents.workflow import CustomerSupportWorkflow
from src.api.dependencies import get_llm_client
from src.api.schemas import WorkflowRequest, WorkflowResponse
from src.data.bootstrap import get_data_stores
from src.llm.base import LLMClient

router = APIRouter(prefix="/v1", tags=["workflow"])


@router.post("/workflow/run", response_model=WorkflowResponse)
async def run_workflow(
    body: WorkflowRequest,
    client: LLMClient = Depends(get_llm_client),
) -> WorkflowResponse:
    stores = get_data_stores()
    if stores.conversation_repo.get(body.conversation_id) is None:
        stores.conversation_repo.create(
            user_id=body.user_id,
            conversation_id=body.conversation_id,
        )
    stores.message_repo.add_message(
        conversation_id=body.conversation_id,
        role="user",
        content=body.message,
    )

    workflow = CustomerSupportWorkflow(
        client,
        tool_execution_service=stores.tool_execution_service,
    )
    result = await workflow.run(
        user_id=body.user_id,
        conversation_id=body.conversation_id,
        customer_message=body.message,
        tenant_id=body.tenant_id,
        user_role=body.user_role,
        approval_granted=body.approval_granted,
        approval_id=body.approval_id,
        run_id=body.run_id,
    )

    return WorkflowResponse(
        run_id=result.run_id,
        conversation_id=result.conversation_id,
        status=result.status.value,
        final_answer=result.final_answer,
        needs_human_approval=result.needs_human_approval,
        approval_id=result.approval_id,
        selected_tool=result.selected_tool,
        steps_completed=result.steps_completed,
        trace_id=result.trace_id,
        trace_summary=(
            result.trace_summary.model_dump() if result.trace_summary else None
        ),
    )
