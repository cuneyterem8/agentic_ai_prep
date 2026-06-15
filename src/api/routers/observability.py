from fastapi import APIRouter, HTTPException

from src.api.schemas import MetricsSnapshotResponse, TraceSummaryResponse
from src.observability.metrics import get_metrics
from src.observability.traces import get_trace_store

router = APIRouter(prefix="/v1/observability", tags=["observability"])


@router.get("/metrics", response_model=MetricsSnapshotResponse)
async def get_metrics_snapshot() -> MetricsSnapshotResponse:
    snapshot = get_metrics().snapshot()
    return MetricsSnapshotResponse(**snapshot)


@router.get("/traces/{trace_id}", response_model=TraceSummaryResponse)
async def get_trace_summary(trace_id: str) -> TraceSummaryResponse:
    record = get_trace_store().get(trace_id)
    if record is None or record.summary is None:
        raise HTTPException(status_code=404, detail="Trace not found")

    return TraceSummaryResponse(**record.summary.model_dump())
