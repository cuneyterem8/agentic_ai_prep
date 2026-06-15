import asyncio

import pytest

from src.common.errors import (
    AuthorizationError,
    LLMProviderError,
    LLMTimeoutError,
    ValidationError,
)
from src.common.retry import is_retryable, with_retry, with_timeout


@pytest.mark.asyncio
async def test_with_timeout_raises_on_slow_operation():
    async def slow():
        await asyncio.sleep(0.2)
        return "done"

    with pytest.raises(asyncio.TimeoutError):
        await with_timeout(slow(), timeout_seconds=0.05)


@pytest.mark.asyncio
async def test_with_timeout_returns_on_fast_operation():
    async def fast():
        return "ok"

    result = await with_timeout(fast(), timeout_seconds=1.0)
    assert result == "ok"


@pytest.mark.asyncio
async def test_with_retry_succeeds_after_transient_failures():
    attempts = {"count": 0}

    async def flaky():
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise LLMProviderError("transient upstream error")
        return "success"

    result = await with_retry(flaky, max_attempts=3, min_wait_seconds=0.01, max_wait_seconds=0.05)
    assert result == "success"
    assert attempts["count"] == 3


@pytest.mark.asyncio
async def test_with_retry_does_not_retry_validation_error():
    attempts = {"count": 0}

    async def invalid():
        attempts["count"] += 1
        raise ValidationError("bad schema")

    with pytest.raises(ValidationError):
        await with_retry(invalid, max_attempts=3, min_wait_seconds=0.01, max_wait_seconds=0.05)

    assert attempts["count"] == 1


def test_is_retryable_classification():
    assert is_retryable(LLMProviderError("x")) is True
    assert is_retryable(LLMTimeoutError("x")) is True
    assert is_retryable(asyncio.TimeoutError()) is True
    assert is_retryable(ValidationError("x")) is False
    assert is_retryable(AuthorizationError("x")) is False
