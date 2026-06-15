import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

from tenacity import (
    AsyncRetrying,
    RetryError,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.common.errors import AppError, AuthorizationError, TransientError, ValidationError

T = TypeVar("T")

RETRYABLE_EXCEPTIONS = (TransientError, asyncio.TimeoutError)


async def with_timeout(awaitable: Awaitable[T], timeout_seconds: float) -> T:
    return await asyncio.wait_for(awaitable, timeout=timeout_seconds)


async def with_retry(
    operation: Callable[[], Awaitable[T]],
    *,
    max_attempts: int = 3,
    min_wait_seconds: float = 0.1,
    max_wait_seconds: float = 1.0,
    retryable_exceptions: tuple[type[BaseException], ...] = RETRYABLE_EXCEPTIONS,
) -> T:
    if max_attempts < 1:
        raise ValueError("max_attempts must be >= 1")

    try:
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(
                multiplier=min_wait_seconds,
                min=min_wait_seconds,
                max=max_wait_seconds,
            ),
            retry=retry_if_exception_type(retryable_exceptions),
            reraise=True,
        ):
            with attempt:
                return await operation()
    except RetryError as exc:
        raise exc.last_attempt.exception() from exc

    raise RuntimeError("retry loop exited unexpectedly")


def is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, (ValidationError, AuthorizationError)):
        return False
    if isinstance(exc, AppError) and not isinstance(exc, TransientError):
        return False
    return isinstance(exc, RETRYABLE_EXCEPTIONS)
