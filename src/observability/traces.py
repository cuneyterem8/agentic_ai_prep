import time
from contextlib import contextmanager
from contextvars import ContextVar
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from src.common.logging import get_correlation_id

trace_session_var: ContextVar["TraceSession | None"] = ContextVar("trace_session", default=None)

_trace_store: dict[str, "TraceRecord"] = {}


class SpanStatus(str, Enum):
    OK = "ok"
    ERROR = "error"


class TraceSpan(BaseModel):
    span_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    kind: str
    latency_ms: float = 0.0
    status: SpanStatus = SpanStatus.OK
    attributes: dict[str, Any] = Field(default_factory=dict)


class TraceSummary(BaseModel):
    trace_id: str
    correlation_id: str | None = None
    run_id: str | None = None
    status: str
    total_latency_ms: float
    timeline: list[dict[str, Any]] = Field(default_factory=list)
    llm_calls: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    prompt_version: str = "v1"


class TraceRecord(BaseModel):
    trace_id: str
    correlation_id: str | None = None
    run_id: str | None = None
    spans: list[TraceSpan] = Field(default_factory=list)
    summary: TraceSummary | None = None


class TraceSession:
    """OpenTelemetry/LangSmith benzeri in-memory trace context."""

    def __init__(
        self,
        *,
        trace_id: str | None = None,
        run_id: str | None = None,
        prompt_version: str = "v1",
    ) -> None:
        self.trace_id = trace_id or str(uuid4())
        self.run_id = run_id
        self.prompt_version = prompt_version
        self.spans: list[TraceSpan] = []
        self._started = time.perf_counter()
        self._token = trace_session_var.set(self)

    def close(self) -> None:
        trace_session_var.reset(self._token)

    @contextmanager
    def span(self, name: str, kind: str, **attributes: Any):
        started = time.perf_counter()
        status = SpanStatus.OK
        try:
            yield
        except Exception:
            status = SpanStatus.ERROR
            raise
        finally:
            latency_ms = round((time.perf_counter() - started) * 1000, 2)
            self.spans.append(
                TraceSpan(
                    name=name,
                    kind=kind,
                    latency_ms=latency_ms,
                    status=status,
                    attributes=attributes,
                )
            )

    def record_llm_span(
        self,
        *,
        model: str,
        latency_ms: float,
        prompt_tokens: int,
        completion_tokens: int,
        retry_count: int,
        status: str = "ok",
    ) -> None:
        self.spans.append(
            TraceSpan(
                name="llm_completion",
                kind="llm",
                latency_ms=latency_ms,
                status=SpanStatus.OK if status == "ok" else SpanStatus.ERROR,
                attributes={
                    "model": model,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": prompt_tokens + completion_tokens,
                    "retry_count": retry_count,
                    "status": status,
                },
            )
        )

    def finish(self, status: str) -> TraceSummary:
        total_latency_ms = round((time.perf_counter() - self._started) * 1000, 2)
        llm_spans = [span for span in self.spans if span.kind == "llm"]
        total_tokens = sum(span.attributes.get("total_tokens", 0) for span in llm_spans)

        from src.observability.metrics import estimate_llm_cost_usd

        estimated_cost_usd = sum(
            estimate_llm_cost_usd(
                prompt_tokens=span.attributes.get("prompt_tokens", 0),
                completion_tokens=span.attributes.get("completion_tokens", 0),
            )
            for span in llm_spans
        )

        timeline = [
            {
                "name": span.name,
                "kind": span.kind,
                "latency_ms": span.latency_ms,
                "status": span.status.value,
                **(
                    {"model": span.attributes["model"]}
                    if span.kind == "llm" and "model" in span.attributes
                    else {}
                ),
            }
            for span in self.spans
        ]

        summary = TraceSummary(
            trace_id=self.trace_id,
            correlation_id=get_correlation_id(),
            run_id=self.run_id,
            status=status,
            total_latency_ms=total_latency_ms,
            timeline=timeline,
            llm_calls=len(llm_spans),
            total_tokens=total_tokens,
            estimated_cost_usd=round(estimated_cost_usd, 6),
            prompt_version=self.prompt_version,
        )

        record = TraceRecord(
            trace_id=self.trace_id,
            correlation_id=summary.correlation_id,
            run_id=self.run_id,
            spans=self.spans,
            summary=summary,
        )
        _trace_store[self.trace_id] = record
        return summary


def start_trace(
    *,
    run_id: str | None = None,
    prompt_version: str = "v1",
) -> TraceSession:
    return TraceSession(run_id=run_id, prompt_version=prompt_version)


def get_trace() -> TraceSession | None:
    return trace_session_var.get()


def get_trace_store() -> dict[str, TraceRecord]:
    return _trace_store


def clear_trace_store() -> None:
    _trace_store.clear()
