from src.llm.base import LLMClient, Message, MessageRole
from src.llm.service import generate_chat_response
from src.rag.documents import RetrievalResult
from src.rag.retriever import VectorRetriever


class GroundedAnswer:
    def __init__(
        self,
        *,
        question: str,
        source_chunk_ids: list[str],
        sources: list[RetrievalResult],
        answer: str,
        model: str,
    ) -> None:
        self.question = question
        self.source_chunk_ids = source_chunk_ids
        self.sources = sources
        self.answer = answer
        self.model = model


async def answer_with_sources(
    question: str,
    client: LLMClient,
    *,
    retriever: VectorRetriever | None = None,
    top_k: int = 3,
) -> GroundedAnswer:
    """Önce retrieval yapar, kaynak chunk id'lerini döner, sonra grounded cevap üretir."""
    retriever = retriever or VectorRetriever()
    retrieved = await retriever.retrieve(question, top_k=top_k)

    source_chunk_ids = [item.chunk.id for item in retrieved]
    context = "\n".join(
        f"[{item.chunk.id}] {item.chunk.content}" for item in retrieved
    ) or "No relevant context found."

    messages = [
        Message(
            role=MessageRole.SYSTEM,
            content=(
                "You are an internal banking assistant. "
                "Answer only using provided context. "
                "If context is insufficient, say you do not know. "
                "Always mention source chunk ids in the answer."
            ),
        ),
        Message(
            role=MessageRole.USER,
            content=(
                f"Question: {question}\n\n"
                f"Context:\n{context}\n\n"
                f"Source chunk ids: {', '.join(source_chunk_ids) if source_chunk_ids else 'none'}"
            ),
        ),
    ]

    response = await generate_chat_response(messages, client, timeout_seconds=20.0)

    return GroundedAnswer(
        question=question,
        source_chunk_ids=source_chunk_ids,
        sources=retrieved,
        answer=response.content,
        model=response.model,
    )
