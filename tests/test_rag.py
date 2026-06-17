import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.llm.mock_client import MockLLMClient
from src.rag.chunking import chunk_text
from src.rag.documents import default_banking_documents
from src.rag.embeddings import MockEmbeddingProvider, cosine_similarity
from src.rag.evaluation import (
    build_default_eval_dataset,
    dcg,
    hit_rate_at_k,
    mrr,
    ndcg_at_k,
    precision_at_k,
    reciprocal_rank,
    run_retrieval_evaluation,
)
from src.rag.query_rewrite import rewrite_query
from src.rag.reranker import rerank
from src.rag.retriever import KnowledgeBase, MockRetriever, VectorRetriever
from src.rag.service import answer_with_sources


def test_chunk_text_with_overlap():
    text = "word " * 50
    chunks = chunk_text(text, chunk_size=80, overlap=20)

    assert len(chunks) > 1
    assert all(len(chunk) <= 80 for chunk in chunks)


def test_knowledge_base_ingest_creates_chunks():
    kb = KnowledgeBase()
    count = kb.ingest(default_banking_documents(), chunk_size=80, overlap=10)

    assert count >= len(default_banking_documents())
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
    assert report.mean_mrr >= 0
    assert report.mean_ndcg_at_k >= 0
    assert len(report.cases) == 5


def test_mrr_and_ndcg_helpers():
    assert reciprocal_rank([0, 1, 0]) == 0.5
    assert mrr([[1, 0, 0], [0, 1, 0]]) == pytest.approx(0.75)
    assert hit_rate_at_k(["a", "b"], {"a"}, k=2) == 1.0
    assert ndcg_at_k([3, 2, 0]) > 0
    assert dcg([3, 2, 0]) > 0


def test_rewrite_query_expands_acronym():
    rewritten = rewrite_query("KMH limiti nedir?")
    assert "Kredili" in rewritten or "KMH" in rewritten


@pytest.mark.asyncio
async def test_reranker_reorders_results():
    retriever = VectorRetriever()
    results = await retriever.retrieve("transfer approval", top_k=3)
    reranked = rerank("transfer approval limit", results, top_k=2)
    assert len(reranked) <= 2
    assert reranked[0].rank == 1


@pytest.mark.asyncio
async def test_rag_pipeline_endpoint(client=None):
    client = TestClient(app)
    response = client.post(
        "/v1/rag/pipeline",
        json={"question": "FAST işlemleri ne zaman yapılır?", "top_k": 3},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["answer"]
    assert body["source_chunk_ids"]
    assert body.get("eval") is not None


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
