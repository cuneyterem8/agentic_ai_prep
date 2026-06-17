import pytest

from src.rag.preparation import (
    ACRONYM_MAP,
    chunk_by_words,
    chunk_recursive,
    clean_text,
    normalize_text,
    prepare_documents,
)
from src.rag.documents import SourceDocument


def test_clean_text_removes_page_markers():
    text = "Policy text   Page 1 of 10   more content"
    cleaned = clean_text(text)
    assert "Page 1 of 10" not in cleaned
    assert "Policy text" in cleaned


def test_normalize_expands_acronym():
    result = normalize_text("KMH hesabı nedir?")
    assert "Kredili Mevduat Hesabı" in result


def test_chunk_by_words_overlap():
    text = " ".join(["word"] * 50)
    chunks = chunk_by_words(text, chunk_size=20, overlap=5)
    assert len(chunks) > 1


def test_chunk_recursive_preserves_paragraphs():
    text = "Paragraph one about FAST.\n\nParagraph two about EFT."
    chunks = chunk_recursive(text, max_chars=200)
    assert len(chunks) >= 2


def test_prepare_documents_adds_metadata():
    docs = [
        SourceDocument(
            id="doc-test",
            title="Test Policy",
            content="FAST işlemleri 7/24 yapılabilir.",
            metadata={"category": "payments"},
        )
    ]
    prepared = prepare_documents(docs, chunk_size=80, overlap=10)
    assert len(prepared) >= 1
    assert prepared[0].metadata.get("document_title") == "Test Policy"
    assert "FAST" in prepared[0].text
