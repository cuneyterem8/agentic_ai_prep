import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.llm.mock_client import MockLLMClient
from src.rag.chunking import chunk_text
from src.rag.documents import default_ing_documents
from src.rag.embeddings import MockEmbeddingProvider, cosine_similarity
from src.rag.evaluation import (
    build_default_eval_dataset,
    precision_at_k,
    run_retrieval_evaluation,
)
from src.rag.retriever import KnowledgeBase, MockRetriever, VectorRetriever
from src.rag.service import answer_with_sources


def test_chunk_text_with_overlap():
    text = "word " * 50
    chunks = chunk_text(text, chunk_size=80, overlap=20)

    assert len(chunks) > 1
    assert all(len(chunk) <= 80 for chunk in chunks)


def test_knowledge_base_ingest_creates_chunks():
    kb = KnowledgeBase()
    count = kb.ingest(default_ing_documents(), chunk_size=80, overlap=10)

    assert count >= len(default_ing_documents())
    assert all(chunk.id for chunk in kb.chunks)


def test_cosine_similarity_identical_vectors():
    provider = MockEmbeddingProvider()
    vector = provider.embed("transfer approval limit")
    assert cosine_similarity(vector, vector) == pytest.approx(1.0, abs=1e-6)


@pytest.mark.asyncio
async def test_vector_retriever_returns_transfer_chunk():
    retriever = VectorRetriever()
    results = await retriever.retrieve("transfer approval limit", top_k=2)

    assert len(results) >= 1
    assert any("transfer" in item.chunk.content.lower() for item in results)
    assert results[0].chunk.id.startswith("doc-")


@pytest.mark.asyncio
async def test_vector_retriever_metadata_filter():
    retriever = VectorRetriever()
    results = await retriever.retrieve(
        "complaint escalation",
        top_k=3,
        metadata_filter={"category": "complaints"},
    )

    assert len(results) >= 1
    assert all(item.chunk.metadata.get("category") == "complaints" for item in results)


def test_precision_at_k_metric():
    retrieved = ["doc-3-chunk-0", "doc-1-chunk-0", "doc-2-chunk-0"]
    relevant = {"doc-3-chunk-0"}

    assert precision_at_k(retrieved, relevant, k=3) == pytest.approx(1 / 3)


@pytest.mark.asyncio
async def test_retrieval_evaluation_dataset():
    report = await run_retrieval_evaluation(build_default_eval_dataset(), top_k=3)

    assert report.mean_precision_at_k > 0
    assert report.mean_recall_at_k > 0
    assert len(report.cases) == 3


@pytest.mark.asyncio
async def test_answer_with_sources_returns_chunk_ids_first():
    client = MockLLMClient()
    result = await answer_with_sources(
        "What is transfer approval limit?",
        client,
        top_k=2,
    )

    assert len(result.source_chunk_ids) >= 1
    assert result.sources
    assert result.answer


@pytest.mark.asyncio
async def test_mock_retriever_backward_compatible():
    retriever = MockRetriever()
    docs = await retriever.retrieve("password reset verification", top_k=2)

    assert len(docs) >= 1
    assert any("password" in doc.content.lower() for doc in docs)


def test_rag_query_endpoint():
    client = TestClient(app)
    response = client.get("/v1/rag/eval")

    assert response.status_code == 200
    body = response.json()
    assert body["mean_precision_at_k"] > 0


def test_rag_query_post_endpoint():
    client = TestClient(app)
    response = client.post(
        "/v1/rag/query",
        json={
            "user_id": "user-1",
            "question": "transfer above 50000 TL approval",
            "top_k": 2,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["source_chunk_ids"]
    assert body["sources"]
    assert body["answer"]
