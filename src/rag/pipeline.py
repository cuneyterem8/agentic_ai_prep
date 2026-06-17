"""End-to-end RAG pipeline."""

from typing import Any

from src.evals.judge import JudgeRubric, judge_answer
from src.llm.base import LLMClient, Message, MessageRole
from src.llm.service import generate_chat_response
from src.rag.context import build_context
from src.rag.query_rewrite import rewrite_query
from src.rag.reranker import rerank
from src.rag.retriever import VectorRetriever


async def rag_pipeline(
    user_query: str,
    client: LLMClient,
    *,
    retriever: VectorRetriever | None = None,
    top_k: int = 5,
    include_judge: bool = True,
) -> dict[str, Any]:
    retriever = retriever or VectorRetriever()

    normalized_query = rewrite_query(user_query)
    dense_results = await retriever.retrieve(normalized_query, top_k=top_k * 2)
    reranked = rerank(normalized_query, dense_results, top_k=top_k)
    context = build_context(reranked)

    messages = [
        Message(
            role=MessageRole.SYSTEM,
            content=(
                "You are a banking assistant. Answer using only the provided context. "
                "If information is unavailable, say so. Do not provide investment advice."
            ),
        ),
        Message(
            role=MessageRole.USER,
            content=f"User question:\n{normalized_query}\n\nContext:\n{context}\n\nAnswer:",
        ),
    ]
    response = await generate_chat_response(messages, client, timeout_seconds=20.0)

    result: dict[str, Any] = {
        "query": user_query,
        "rewritten_query": normalized_query,
        "context": context,
        "source_chunk_ids": [item.chunk.id for item in reranked],
        "answer": response.content,
        "model": response.model,
    }

    if include_judge:
        rubric: JudgeRubric = await judge_answer(
            question=user_query,
            context=context,
            answer=response.content,
            client=client,
        )
        result["eval"] = rubric.model_dump()

    return result
