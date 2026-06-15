from pydantic import BaseModel, Field


class SourceDocument(BaseModel):
    id: str
    title: str
    content: str
    metadata: dict[str, str] = Field(default_factory=dict)


class Chunk(BaseModel):
    id: str
    document_id: str
    content: str
    metadata: dict[str, str] = Field(default_factory=dict)
    chunk_index: int = 0


class RetrievalResult(BaseModel):
    chunk: Chunk
    score: float
    rank: int


def default_banking_documents() -> list[SourceDocument]:
    """Örnek bankacılık iç bilgi tabanı."""
    return [
        SourceDocument(
            id="doc-1",
            title="Password Reset Policy",
            content=(
                "Internal banking policy: password reset requires identity verification. "
                "Customer must pass KYC checks before reset is approved."
            ),
            metadata={"category": "security", "department": "ops"},
        ),
        SourceDocument(
            id="doc-2",
            title="Complaint SLA",
            content=(
                "Complaint handling SLA: high-risk complaints escalate within 2 hours. "
                "Medium-risk complaints receive response within 24 hours."
            ),
            metadata={"category": "complaints", "department": "support"},
        ),
        SourceDocument(
            id="doc-3",
            title="Transfer Limits",
            content=(
                "Account transfer limits: transfers above 50000 TL require human approval. "
                "Daily transfer cap for retail customers is 100000 TL."
            ),
            metadata={"category": "transfers", "department": "payments"},
        ),
        SourceDocument(
            id="doc-4",
            title="Card Dispute Process",
            content=(
                "Card dispute process starts with transaction review. "
                "Disputes above 1000 TL need fraud team approval."
            ),
            metadata={"category": "cards", "department": "fraud"},
        ),
    ]
