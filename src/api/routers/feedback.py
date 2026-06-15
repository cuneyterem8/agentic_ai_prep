from fastapi import APIRouter, Query

from src.api.schemas import FeedbackListResponse, FeedbackRequest, FeedbackResponse
from src.evals.feedback_store import append_feedback, list_feedback

router = APIRouter(prefix="/v1", tags=["feedback"])


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(body: FeedbackRequest) -> FeedbackResponse:
    record = append_feedback(
        user_id=body.user_id,
        conversation_id=body.conversation_id,
        rating=body.rating,
        comment=body.comment,
        trace_id=body.trace_id,
        run_id=body.run_id,
        message_preview=body.message_preview,
    )
    return FeedbackResponse(**record)


@router.get("/feedback/recent", response_model=FeedbackListResponse)
async def get_recent_feedback(
    limit: int = Query(default=20, ge=1, le=100),
) -> FeedbackListResponse:
    return FeedbackListResponse(items=list_feedback(limit=limit))
