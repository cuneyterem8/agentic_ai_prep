import logging
import time

from src.common.errors import LLMTimeoutError
from src.common.logging import get_correlation_id
from src.common.retry import with_retry, with_timeout
from src.llm.base import LLMClient, LLMResponse, Message
from src.observability.metrics import get_metrics
from src.observability.traces import get_trace

logger = logging.getLogger("agenticai")


async def generate_chat_response(
    messages: list[Message],
    client: LLMClient,
    *,
    timeout_seconds: float = 30.0,
    max_attempts: int = 3,
) -> LLMResponse:
    """Provider-agnostic chat completion with timeout, retry, trace and metrics."""

    attempts = 0

    async def _call() -> LLMResponse:
        nonlocal attempts
        attempts += 1
        return await client.complete(messages)

    started = time.perf_counter()
    status = "ok"
    response: LLMResponse | None = None

    try:
        response = await with_timeout(
            with_retry(_call, max_attempts=max_attempts),
            timeout_seconds,
        )
    except TimeoutError as exc:
        status = "timeout"
        raise LLMTimeoutError(f"LLM call timed out after {timeout_seconds}s") from exc
    except Exception:
        status = "error"
        raise
    finally:
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        prompt_tokens = response.usage.prompt_tokens if response else 0
        completion_tokens = response.usage.completion_tokens if response else 0
        model = response.model if response else getattr(client, "model", "unknown")

        get_metrics().record_llm_call(
            model=model,
            latency_ms=latency_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            retry_count=attempts,
            status=status,
        )

        trace = get_trace()
        if trace is not None:
            trace.record_llm_span(
                model=model,
                latency_ms=latency_ms,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                retry_count=attempts,
                status=status,
            )

        trace_id = trace.trace_id if trace else None
        logger.info(
            "llm_completion",
            extra={
                "event": "llm_completion",
                "provider": model,
                "model": model,
                "latency_ms": latency_ms,
                "tokens": prompt_tokens + completion_tokens,
                "retry_count": attempts,
                "status": status,
                "trace_id": trace_id,
            },
        )

        correlation_id = get_correlation_id()
        if correlation_id:
            logger.debug(
                "llm_trace",
                extra={
                    "event": "llm_trace",
                    "correlation_id": correlation_id,
                    "trace_id": trace_id,
                },
            )

    return response  # type: ignore[return-value]
