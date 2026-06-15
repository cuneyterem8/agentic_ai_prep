import time
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError

from src.api.exception_handlers import (
    app_exception_handler,
    llm_timeout_exception_handler,
    validation_exception_handler,
)
from src.api.routers import agent, analyst, chat, classify, observability, rag, security, workflow
from src.common.config import get_settings
from src.common.errors import AppError, AuthorizationError, LLMTimeoutError
from src.common.health import healthcheck
from src.common.logging import set_correlation_id, setup_logging
from src.observability.metrics import get_metrics

settings = get_settings()
logger = setup_logging(settings.log_level)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)

app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(LLMTimeoutError, llm_timeout_exception_handler)
app.add_exception_handler(AppError, app_exception_handler)

app.include_router(chat.router)
app.include_router(agent.router)
app.include_router(classify.router)
app.include_router(workflow.router)
app.include_router(rag.router)
app.include_router(rag.router)
app.include_router(analyst.router)
app.include_router(observability.router)
app.include_router(security.router)


@app.middleware("http")
async def request_metrics_middleware(request: Request, call_next):
    started = time.perf_counter()
    response = await call_next(request)
    latency_ms = round((time.perf_counter() - started) * 1000, 2)
    route = request.url.path
    get_metrics().record_http_request(
        route=route,
        method=request.method,
        status_code=response.status_code,
        latency_ms=latency_ms,
    )
    return response


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    set_correlation_id(correlation_id)
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


@app.get("/health")
async def health_endpoint() -> dict[str, str | bool]:
    result = healthcheck()
    logger.info("healthcheck", extra={"event": "healthcheck", "status": result["status"]})
    return result
