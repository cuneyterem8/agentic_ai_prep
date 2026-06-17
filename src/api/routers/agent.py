from fastapi import APIRouter, Depends

from src.agents.react_loop import run_react_loop
from src.api.dependencies import get_llm_client
from src.api.schemas import (
    AgentRunRequest,
    AgentRunResponse,
    ReActRequest,
    ReActResponse,
    ReActStepResponse,
)
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


@router.post("/agent/react", response_model=ReActResponse)
async def run_react_agent(
    body: ReActRequest,
    client: LLMClient = Depends(get_llm_client),
) -> ReActResponse:
    result = await run_react_loop(
        user_query=body.query,
        user_id=body.user_id,
        client=client,
    )

    return ReActResponse(
        conversation_id=body.conversation_id,
        query=result.query,
        status=result.status,
        final_answer=result.final_answer,
        steps=[
            ReActStepResponse(
                thought=step.thought,
                action_type=step.action_type,
                tool_name=step.tool_name,
                tool_arguments=step.tool_arguments,
                observation=step.observation,
            )
            for step in result.steps
        ],
    )
