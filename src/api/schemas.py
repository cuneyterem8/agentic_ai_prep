from typing import Any

from pydantic import BaseModel, Field

from src.agents.policies import UserRole
from src.llm.base import TokenUsage


class ChatRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=128)
    conversation_id: str = Field(min_length=1, max_length=128)
    message: str = Field(min_length=1, max_length=8000)
    metadata: dict[str, Any] = Field(default_factory=dict)
    stream: bool = False


class ChatResponse(BaseModel):
    conversation_id: str
    message: str
    model: str
    usage: TokenUsage


class StreamChunk(BaseModel):
    token: str
    done: bool = False


class AgentRunRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=128)
    conversation_id: str = Field(min_length=1, max_length=128)
    task: str = Field(min_length=1, max_length=256)
    input: str = Field(min_length=1, max_length=8000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentRunResponse(BaseModel):
    conversation_id: str
    task: str
    status: str
    result: str
    model: str


class ErrorDetail(BaseModel):
    code: str
    message: str
    correlation_id: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class ClassifyRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=128)
    conversation_id: str = Field(min_length=1, max_length=128)
    message: str = Field(min_length=1, max_length=8000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ClassifyResponse(BaseModel):
    conversation_id: str
    intent: str
    risk_level: str
    needs_human_approval: bool
    blocked: bool = False
    block_reasons: list[str] = Field(default_factory=list)
    model: str


class EvalCaseResult(BaseModel):
    pass_: bool = Field(alias="pass")
    model_config = {"populate_by_name": True}


class EvalSuiteResponse(BaseModel):
    total: int
    passed: int
    failed: int
    score: float
    cases: list[dict[str, Any]] = Field(default_factory=list)


class AllEvalsResponse(BaseModel):
    total: int
    passed: int
    failed: int
    score: float
    suites: dict[str, EvalSuiteResponse]


class WorkflowRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=128)
    conversation_id: str = Field(min_length=1, max_length=128)
    message: str = Field(min_length=1, max_length=8000)
    tenant_id: str = Field(default="default", min_length=1, max_length=64)
    user_role: UserRole = UserRole.CUSTOMER
    approval_granted: bool = False
    approval_id: str | None = None
    run_id: str | None = None


class WorkflowResponse(BaseModel):
    run_id: str
    conversation_id: str
    status: str
    final_answer: str
    needs_human_approval: bool
    approval_id: str | None = None
    selected_tool: str | None = None
    steps_completed: list[str]
    trace_id: str | None = None
    trace_summary: dict[str, Any] | None = None


class AuditLogEntryResponse(BaseModel):
    id: str
    actor: str
    action: str
    risk_level: str
    details: dict[str, Any]
    correlation_id: str | None = None
    created_at: str


class AuditLogListResponse(BaseModel):
    entries: list[AuditLogEntryResponse]


class TraceTimelineItem(BaseModel):
    name: str
    kind: str
    latency_ms: float
    status: str
    model: str | None = None


class TraceSummaryResponse(BaseModel):
    trace_id: str
    correlation_id: str | None = None
    run_id: str | None = None
    status: str
    total_latency_ms: float
    timeline: list[TraceTimelineItem]
    llm_calls: int
    total_tokens: int
    estimated_cost_usd: float
    prompt_version: str


class MetricsSnapshotResponse(BaseModel):
    counters: dict[str, int]
    latencies: dict[str, dict[str, float | int]]
    gauges: dict[str, float]


class RagQueryRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=128)
    question: str = Field(min_length=1, max_length=4000)
    top_k: int = Field(default=3, ge=1, le=10)


class RagSource(BaseModel):
    chunk_id: str
    document_id: str
    content: str
    score: float
    metadata: dict[str, str] = Field(default_factory=dict)


class RagQueryResponse(BaseModel):
    question: str
    source_chunk_ids: list[str]
    sources: list[RagSource]
    answer: str
    model: str


class RagEvalCaseResult(BaseModel):
    query: str
    precision_at_k: float
    recall_at_k: float
    retrieved_chunk_ids: list[str]
    relevant_chunk_ids: list[str]


class RagEvalResponse(BaseModel):
    mean_precision_at_k: float
    mean_recall_at_k: float
    cases: list[RagEvalCaseResult]


class AnalystRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=128)
    tenant_id: str = Field(min_length=1, max_length=64)
    question: str = Field(min_length=1, max_length=4000)
    approval_granted: bool = False


class AnalystResponse(BaseModel):
    question: str
    generated_sql: str
    final_sql: str
    allowed: bool
    sql_correct: bool
    sql_repaired: bool
    needs_human_approval: bool
    executed: bool
    row_count: int
    analysis_summary: str
    confidence: float
    guardrail_reasons: list[str]
    correctness_issues: list[str]


class FeedbackRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=128)
    conversation_id: str = Field(min_length=1, max_length=128)
    rating: str = Field(pattern="^(positive|negative)$")
    comment: str = Field(default="", max_length=2000)
    trace_id: str | None = None
    run_id: str | None = None
    message_preview: str = Field(default="", max_length=500)


class FeedbackResponse(BaseModel):
    feedback_id: str
    timestamp: str
    user_id: str
    conversation_id: str
    rating: str
    comment: str
    trace_id: str | None = None
    run_id: str | None = None
    message_preview: str = ""


class FeedbackListResponse(BaseModel):
    items: list[FeedbackResponse]
