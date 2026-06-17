"""RAG data preparation: clean, normalize, chunk strategies."""

import re

from src.rag.chunking import chunk_text
from src.rag.documents import Chunk, SourceDocument

ACRONYM_MAP = {
    "KMH": "Kredili Mevduat Hesabı",
    "EFT": "Elektronik Fon Transferi",
    "FAST": "Fonların Anlık ve Sürekli Transferi",
    "POS": "Point of Sale",
    "IBAN": "International Bank Account Number",
}


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"Page \d+ of \d+", "", text, flags=re.IGNORECASE)
    text = text.replace("\u00a0", " ")
    return text.strip()


def normalize_text(text: str) -> str:
    normalized = text
    for acronym, expansion in ACRONYM_MAP.items():
        pattern = rf"\b{re.escape(acronym)}\b"
        normalized = re.sub(pattern, f"{acronym} ({expansion})", normalized, flags=re.IGNORECASE)
    return normalized


def chunk_by_words(text: str, *, chunk_size: int = 120, overlap: int = 30) -> list[str]:
    words = text.split()
    if not words:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        if chunk:
            chunks.append(chunk)
        if end >= len(words):
            break
        start += chunk_size - overlap

    return chunks


def chunk_recursive(text: str, *, max_chars: int = 500) -> list[str]:
    """Paragraph → sentence → fixed-size fallback."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []

    for paragraph in paragraphs:
        if len(paragraph) <= max_chars:
            chunks.append(paragraph)
            continue

        sentences = re.split(r"(?<=[.!?])\s+", paragraph)
        buffer = ""
        for sentence in sentences:
            if len(buffer) + len(sentence) + 1 <= max_chars:
                buffer = f"{buffer} {sentence}".strip()
            else:
                if buffer:
                    chunks.append(buffer)
                if len(sentence) <= max_chars:
                    buffer = sentence
                else:
                    chunks.extend(chunk_text(sentence, chunk_size=max_chars, overlap=50))
                    buffer = ""
        if buffer:
            chunks.append(buffer)

    return chunks


class PreparedChunk:
    def __init__(
        self,
        *,
        chunk_id: str,
        document_id: str,
        text: str,
        metadata: dict[str, str],
        chunk_index: int,
    ) -> None:
        self.chunk_id = chunk_id
        self.document_id = document_id
        self.text = text
        self.metadata = metadata
        self.chunk_index = chunk_index


def prepare_documents(
    documents: list[SourceDocument],
    *,
    chunk_size: int = 120,
    overlap: int = 30,
    strategy: str = "fixed",
) -> list[PreparedChunk]:
    prepared: list[PreparedChunk] = []

    for document in documents:
        text = normalize_text(clean_text(document.content))
        if strategy == "words":
            parts = chunk_by_words(text, chunk_size=chunk_size, overlap=overlap)
        elif strategy == "recursive":
            parts = chunk_recursive(text, max_chars=chunk_size * 4)
        else:
            parts = chunk_text(text, chunk_size=chunk_size, overlap=overlap)

        base_metadata = {
            **document.metadata,
            "document_title": document.title,
            "source_type": document.metadata.get("source_type", "text"),
        }

        for index, part in enumerate(parts):
            prepared.append(
                PreparedChunk(
                    chunk_id=f"{document.id}-chunk-{index}",
                    document_id=document.id,
                    text=part,
                    metadata={**base_metadata, "chunk_index": str(index)},
                    chunk_index=index,
                )
            )

    return prepared


def prepared_to_chunks(prepared: list[PreparedChunk]) -> list[Chunk]:
    return [
        Chunk(
            id=item.chunk_id,
            document_id=item.document_id,
            content=item.text,
            metadata=item.metadata,
            chunk_index=item.chunk_index,
        )
        for item in prepared
    ]
