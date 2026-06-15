def chunk_text(
    text: str,
    *,
    chunk_size: int = 120,
    overlap: int = 30,
) -> list[str]:
    """Fixed-size chunking with overlap — production'da doc yapısına göre ayarlanır."""
    normalized = " ".join(text.split())
    if not normalized:
        return []

    if len(normalized) <= chunk_size:
        return [normalized]

    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        end = start + chunk_size
        chunks.append(normalized[start:end].strip())
        if end >= len(normalized):
            break
        start = max(end - overlap, start + 1)

    return [chunk for chunk in chunks if chunk]
