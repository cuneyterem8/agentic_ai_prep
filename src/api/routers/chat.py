import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from src.api.dependencies import get_llm_client
from src.api.schemas import ChatRequest, ChatResponse, StreamChunk
from src.llm.base import LLMClient, Message, MessageRole
from src.llm.service import generate_chat_response

router = APIRouter(prefix="/v1", tags=["chat"])


def _to_messages(body: ChatRequest) -> list[Message]:
    return [Message(role=MessageRole.USER, content=body.message)]


@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    client: LLMClient = Depends(get_llm_client),
) -> ChatResponse | StreamingResponse:
    messages = _to_messages(body)

    if body.stream:
        return StreamingResponse(
            _stream_tokens(client, messages, body.conversation_id),
            media_type="text/event-stream",
        )

    response = await generate_chat_response(messages, client)
    return ChatResponse(
        conversation_id=body.conversation_id,
        message=response.content,
        model=response.model,
        usage=response.usage,
    )


async def _stream_tokens(
    client: LLMClient,
    messages: list[Message],
    conversation_id: str,
):
    async for token in client.stream(messages):
        chunk = StreamChunk(token=token)
        yield f"data: {json.dumps(chunk.model_dump())}\n\n"

    done = StreamChunk(token="", done=True)
    yield f"data: {json.dumps({**done.model_dump(), 'conversation_id': conversation_id})}\n\n"
