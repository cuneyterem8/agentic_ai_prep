from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.api.schemas import ErrorDetail, ErrorResponse
from src.common.errors import AppError, AuthorizationError, LLMTimeoutError
from src.common.logging import get_correlation_id


def _error_response(status_code: int, code: str, message: str) -> JSONResponse:
    body = ErrorResponse(
        error=ErrorDetail(
            code=code,
            message=message,
            correlation_id=get_correlation_id(),
        )
    )
    return JSONResponse(status_code=status_code, content=body.model_dump())


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return _error_response(
        422,
        "validation_error",
        "Request validation failed",
    )


async def llm_timeout_exception_handler(
    request: Request,
    exc: LLMTimeoutError,
) -> JSONResponse:
    return _error_response(504, "llm_timeout", str(exc))


async def app_exception_handler(request: Request, exc: AppError) -> JSONResponse:
    status_code = 403 if isinstance(exc, AuthorizationError) else 500
    code = "authorization_error" if isinstance(exc, AuthorizationError) else "app_error"
    return _error_response(status_code, code, str(exc))
