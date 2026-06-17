"""Context assembly for RAG generation."""

from src.rag.documents import RetrievalResult


def build_context(
    results: list[RetrievalResult],
    *,
    max_chars: int = 4000,
) -> str:
    seen_ids: set[str] = set()
    parts: list[str] = []
    total = 0

    for index, item in enumerate(results, start=1):
        if item.chunk.id in seen_ids:
            continue
        seen_ids.add(item.chunk.id)

        title = item.chunk.metadata.get("document_title", item.chunk.document_id)
        section = item.chunk.metadata.get("section", "")
        header = f"[Document {index}] Title: {title}"
        if section:
            header += f"\nSection: {section}"

        block = f"{header}\nContent: {item.chunk.content}"
        if total + len(block) > max_chars:
            break

        parts.append(block)
        total += len(block)

    return "\n\n".join(parts) if parts else "No relevant context found."
