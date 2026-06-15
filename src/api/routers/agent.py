from fastapi import APIRouter, Depends

from src.api.dependencies import get_llm_client
from src.api.schemas import AgentRunRequest, AgentRunResponse
from src.llm.base import LLMClient, Message, MessageRole
from src.llm.service import generate_chat_response

router = APIRouter(prefix="/v1", tags=["agent"])


@router.post("/agent/run", response_model=AgentRunResponse)
async def run_agent(
    body: AgentRunRequest,
    client: LLMClient = Depends(get_llm_client),
) -> AgentRunResponse:
    prompt = f"Task: {body.task}\nInput: {body.input}"
    messages = [Message(role=MessageRole.USER, content=prompt)]

    response = await generate_chat_response(messages, client)

    return AgentRunResponse(
        conversation_id=body.conversation_id,
        task=body.task,
        status="completed",
        result=response.content,
        model=response.model,
    )
